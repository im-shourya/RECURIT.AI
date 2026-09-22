"""
RECRUIT.AI — Applicant Admin Router (Organisation-only)
GET  /applicants                       — List applicants across the org's drives
GET  /applicants/{id}                  — Full applicant profile (submission + interview)
GET  /applicants/{id}/submission-file  — Short-lived link to the uploaded file
POST /applicants/{id}/decision         — Record hire / reject decision, email the result

Every endpoint here is authenticated and scoped to the calling organisation.
Applicants are reached only by joining through Drive.org_id, so one
organisation can never read or decide on another organisation's candidates.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from app.models.database import (
    Drive, Applicant, EmailLog, Organisation,
    ApplicantStatus, EmailType,
)
from app.models.schemas import (
    ApplicantResponse,
    ApplicantDecisionRequest,
    ApplicantDecisionResponse,
    SubmissionFileLinkResponse,
)
from app.services.auth_service import get_current_org
from app.services.email_service import send_result_email
from app.services import storage_service

router = APIRouter(prefix="/applicants", tags=["Applicants (Organisation)"])


# ──────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────
def _owned_applicant(applicant_id: UUID, org: Organisation, db: Session) -> Applicant:
    """
    Fetch an applicant that belongs to one of the calling org's drives.

    The Drive.org_id filter is the authorization boundary. A missing row and a
    row owned by another organisation both raise 404 — never 403 — so this does
    not leak whether a given applicant id exists.
    """
    applicant = (
        db.query(Applicant)
        .join(Drive, Applicant.drive_id == Drive.id)
        .filter(Applicant.id == applicant_id, Drive.org_id == org.id)
        .options(joinedload(Applicant.submission), joinedload(Applicant.interview))
        .first()
    )
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    return applicant


# ──────────────────────────────────────────────
# LIST APPLICANTS
# ──────────────────────────────────────────────
@router.get("", response_model=list[ApplicantResponse])
def list_applicants(
    drive_id: Optional[UUID] = Query(None, description="Restrict to one drive"),
    status: Optional[str] = Query(None, description="Filter by applicant status"),
    q: Optional[str] = Query(None, max_length=255, description="Search name, email or reg no"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    org: Organisation = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Applicant)
        .join(Drive, Applicant.drive_id == Drive.id)
        .filter(Drive.org_id == org.id)
        .options(joinedload(Applicant.submission), joinedload(Applicant.interview))
    )

    if drive_id:
        query = query.filter(Applicant.drive_id == drive_id)

    if status:
        valid = {s.value for s in ApplicantStatus}
        if status not in valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Expected one of: {', '.join(sorted(valid))}",
            )
        query = query.filter(Applicant.status == ApplicantStatus(status))

    if q:
        # ilike through the ORM stays parameterised; the % wrapping is on the
        # bound value, not the SQL string.
        term = f"%{q}%"
        query = query.filter(
            or_(
                Applicant.name.ilike(term),
                Applicant.email.ilike(term),
                Applicant.reg_no.ilike(term),
            )
        )

    applicants = (
        query.order_by(Applicant.applied_at.desc()).offset(offset).limit(limit).all()
    )
    return [_to_response(a) for a in applicants]


# ──────────────────────────────────────────────
# APPLICANT PROFILE
# ──────────────────────────────────────────────
@router.get("/{applicant_id}", response_model=ApplicantResponse)
def get_applicant(
    applicant_id: UUID,
    org: Organisation = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    return _to_response(_owned_applicant(applicant_id, org, db))


# ──────────────────────────────────────────────
# SUBMISSION FILE LINK
# ──────────────────────────────────────────────
@router.get("/{applicant_id}/submission-file", response_model=SubmissionFileLinkResponse)
def get_submission_file_link(
    applicant_id: UUID,
    org: Organisation = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    """
    Return a short-lived presigned URL for the candidate's uploaded file.

    Submission objects are private, so this is the only way to read one. The
    link is minted per request and expires in minutes, which keeps the bucket
    closed and means a copied URL does not grant lasting access.
    """
    applicant = _owned_applicant(applicant_id, org, db)

    if not applicant.submission or not applicant.submission.file_url:
        raise HTTPException(status_code=404, detail="This applicant has no uploaded file")

    stored = applicant.submission.file_url
    try:
        url = storage_service.presigned_get_url(stored)
    except storage_service.StorageError as exc:
        print(f"[STORAGE ERROR] applicant={applicant_id}: {exc}")
        raise HTTPException(status_code=502, detail="Could not generate a download link")

    if not url:
        # Either storage is unconfigured, or this row predates uploads and
        # holds a plain URL the candidate supplied. Hand it back unchanged
        # rather than pretending the file is missing.
        if stored.startswith(("http://", "https://")):
            return SubmissionFileLinkResponse(url=stored, expires_in_seconds=0)
        raise HTTPException(
            status_code=503,
            detail="File downloads are not available: object storage is not configured",
        )

    return SubmissionFileLinkResponse(
        url=url,
        expires_in_seconds=storage_service.PRESIGNED_URL_TTL_SECONDS,
    )


# ──────────────────────────────────────────────
# HIRE / REJECT DECISION
# ──────────────────────────────────────────────
@router.post("/{applicant_id}/decision", response_model=ApplicantDecisionResponse)
def decide_applicant(
    applicant_id: UUID,
    body: ApplicantDecisionRequest,
    background_tasks: BackgroundTasks,
    org: Organisation = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    """
    Record the recruiter's final decision and email the candidate.

    This is the step that closes the hiring loop: until now nothing could move
    an applicant into `selected` or `rejected`, and the result email template
    was never sent.
    """
    applicant = _owned_applicant(applicant_id, org, db)

    decided = {ApplicantStatus.SELECTED, ApplicantStatus.REJECTED}
    if applicant.status in decided:
        raise HTTPException(
            status_code=400,
            detail=f"A decision has already been recorded for this applicant ({applicant.status.value})",
        )

    applicant.status = (
        ApplicantStatus.SELECTED if body.decision == "selected" else ApplicantStatus.REJECTED
    )

    db.add(EmailLog(applicant_id=applicant.id, type=EmailType.RESULT))
    db.commit()
    db.refresh(applicant)

    # The result template renders the outcome and the interview score; an
    # applicant rejected before interviewing simply scores 0.
    score = applicant.interview.total_score if applicant.interview else 0

    background_tasks.add_task(
        send_result_email,
        to_email=applicant.email,
        to_name=applicant.name,
        drive_name=applicant.drive.name,
        result_status=applicant.status.value,
        score=score or 0,
    )

    return ApplicantDecisionResponse(
        id=applicant.id,
        name=applicant.name,
        email=applicant.email,
        status=applicant.status.value,
        result_email_sent=True,
    )


# ──────────────────────────────────────────────
# Serialisation
# ──────────────────────────────────────────────
def _to_response(a: Applicant) -> ApplicantResponse:
    return ApplicantResponse(
        id=a.id,
        drive_id=a.drive_id,
        name=a.name,
        email=a.email,
        reg_no=a.reg_no or "",
        skills=a.skills or [],
        primary_domain=a.primary_domain or "",
        github_url=a.github_url or "",
        status=a.status.value,
        applied_at=a.applied_at,
        submission=a.submission,
        interview=a.interview,
    )
