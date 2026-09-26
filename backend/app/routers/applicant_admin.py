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

import csv
import io
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from app.models.database import (
    Drive, Applicant, EmailLog, Organisation,
    ApplicantStatus, EmailType, TaskType,
)
from app.models.schemas import (
    ApplicantResponse,
    ApplicantDecisionRequest,
    ApplicantDecisionResponse,
    SubmissionFileLinkResponse,
    BulkDecisionRequest,
    BulkDecisionResponse,
    ResendEmailRequest,
)
from app.services.auth_service import get_current_org
from app.services.email_service import (
    send_result_email,
    send_application_email,
    send_task_email,
    send_interview_email,
)
from app.services import storage_service
from app.config import get_settings

settings = get_settings()
log = logging.getLogger("recruit.applicants")

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


def _filtered_query(db: Session, org: Organisation, *, drive_id=None, status=None, q=None):
    """
    Build the organisation-scoped applicant query shared by list and export.

    Both endpoints must apply identical scoping and filters; keeping this in
    one place means an export can never widen what a list would have shown.
    """
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

    return query


# ──────────────────────────────────────────────
# LIST APPLICANTS
# ──────────────────────────────────────────────
@router.get("", response_model=list[ApplicantResponse])
def list_applicants(
    response: Response,
    drive_id: Optional[UUID] = Query(None, description="Restrict to one drive"),
    status: Optional[str] = Query(None, description="Filter by applicant status"),
    q: Optional[str] = Query(None, max_length=255, description="Search name, email or reg no"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    org: Organisation = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    query = _filtered_query(db, org, drive_id=drive_id, status=status, q=q)

    # Pagination metadata travels in headers rather than wrapping the body in
    # {items, total}: the response stays a plain array, so existing callers
    # keep working while a UI can now render "showing 50 of 214" and page
    # counts. The count is of the filtered set, not the whole table.
    total = query.order_by(None).count()
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Limit"] = str(limit)
    response.headers["X-Offset"] = str(offset)
    response.headers["Access-Control-Expose-Headers"] = (
        "X-Total-Count, X-Limit, X-Offset"
    )

    applicants = (
        query.order_by(Applicant.applied_at.desc()).offset(offset).limit(limit).all()
    )
    return [_to_response(a) for a in applicants]


# ──────────────────────────────────────────────
# CSV EXPORT
#
# Declared before /{applicant_id}: FastAPI matches in definition order, so a
# later /export would be captured by the UUID route and rejected as invalid.
# ──────────────────────────────────────────────
@router.get("/export")
def export_applicants(
    drive_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None, max_length=255),
    org: Organisation = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    """
    Export the org's applicants as CSV, honouring the same filters as the list.

    Every cell is passed through _csv_safe: applicant names and skills are
    supplied by candidates, and a value beginning with =, +, - or @ is treated
    as a formula by Excel and Sheets when the file is opened.
    """
    applicants = (
        _filtered_query(db, org, drive_id=drive_id, status=status, q=q)
        .order_by(Applicant.applied_at.desc())
        .all()
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "Name", "Email", "Reg No", "Primary Domain", "Skills", "GitHub",
        "Status", "Applied At", "Submitted At", "Total Score",
        "Intro", "Project", "Domain",
    ])

    for a in applicants:
        interview = a.interview
        submission = a.submission
        writer.writerow([
            _csv_safe(a.name),
            _csv_safe(a.email),
            _csv_safe(a.reg_no or ""),
            _csv_safe(a.primary_domain or ""),
            _csv_safe(", ".join(a.skills or [])),
            _csv_safe(a.github_url or ""),
            _csv_safe(a.status.value),
            a.applied_at.isoformat() if a.applied_at else "",
            submission.submitted_at.isoformat() if submission and submission.submitted_at else "",
            interview.total_score if interview else "",
            interview.score_intro if interview else "",
            interview.score_project if interview else "",
            interview.score_domain if interview else "",
        ])

    buffer.seek(0)
    filename = f"applicants-{datetime.now(timezone.utc):%Y%m%d}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
        log.error(
            "could not sign submission download",
            extra={"applicant_id": str(applicant_id), "error": str(exc)},
        )
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


# ──────────────────────────────────────────────
# CSV safety
# ──────────────────────────────────────────────
# Excel and Google Sheets evaluate a cell that starts with one of these as a
# formula. Applicant names and skills come from a public form, so an exported
# sheet is a delivery vector unless each cell is neutralised.
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _csv_safe(value) -> str:
    """Neutralise spreadsheet formula injection in a single cell."""
    text = "" if value is None else str(value)
    if text.startswith(_FORMULA_PREFIXES):
        return "'" + text
    return text


# ──────────────────────────────────────────────
# RESEND AN EMAIL
# ──────────────────────────────────────────────
@router.post("/{applicant_id}/resend-email", status_code=204)
def resend_email(
    applicant_id: UUID,
    body: ResendEmailRequest,
    background_tasks: BackgroundTasks,
    org: Organisation = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    """
    Re-send one of the transactional emails for an applicant.

    Useful when a candidate deletes a link or the original bounced. Each resend
    is written to email_logs, so the audit trail shows the message really was
    sent more than once rather than appearing to be a single send.
    """
    applicant = _owned_applicant(applicant_id, org, db)
    drive = applicant.drive
    kind = body.type

    if kind == "task":
        if not drive.task_deadline or drive.task_type != TaskType.TASK:
            raise HTTPException(status_code=400, detail="This is not a task-based drive")
        background_tasks.add_task(
            send_task_email,
            to_email=applicant.email,
            to_name=applicant.name,
            drive_name=drive.name,
            task_description=drive.task_description or "",
            task_link=f"{settings.FRONTEND_URL}/task/{drive.link_token}",
            submission_link=f"{settings.FRONTEND_URL}/submit/{applicant.id}",
            deadline=str(drive.task_deadline),
        )
    elif kind == "interview":
        if not applicant.interview:
            raise HTTPException(
                status_code=400, detail="This applicant has no interview yet"
            )
        background_tasks.add_task(
            send_interview_email,
            to_email=applicant.email,
            to_name=applicant.name,
            drive_name=drive.name,
            interview_link=f"{settings.FRONTEND_URL}/interview/{applicant.interview.token}",
        )
    elif kind == "result":
        if applicant.status not in (ApplicantStatus.SELECTED, ApplicantStatus.REJECTED):
            raise HTTPException(
                status_code=400,
                detail="No decision has been recorded for this applicant yet",
            )
        background_tasks.add_task(
            send_result_email,
            to_email=applicant.email,
            to_name=applicant.name,
            drive_name=drive.name,
            result_status=applicant.status.value,
            score=(applicant.interview.total_score if applicant.interview else 0) or 0,
        )
    else:  # "applied"
        background_tasks.add_task(
            send_application_email,
            to_email=applicant.email,
            to_name=applicant.name,
            drive_name=drive.name,
            org_name=org.name,
        )

    db.add(EmailLog(applicant_id=applicant.id, type=EmailType(kind)))
    db.commit()
    return None


# ──────────────────────────────────────────────
# BULK DECISION
# ──────────────────────────────────────────────
@router.post("/bulk-decision", response_model=BulkDecisionResponse)
def bulk_decision(
    body: BulkDecisionRequest,
    background_tasks: BackgroundTasks,
    org: Organisation = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    """
    Record the same decision for several applicants at once.

    Each id is re-checked against the calling organisation rather than trusted
    from the request, so a caller cannot slip another org's applicant into the
    list. Ids that are not owned, or already decided, are reported in `skipped`
    instead of failing the whole batch — one stale row should not discard the
    rest of a recruiter's selection.
    """
    target = (
        ApplicantStatus.SELECTED if body.decision == "selected" else ApplicantStatus.REJECTED
    )

    owned = {
        a.id: a
        for a in (
            db.query(Applicant)
            .join(Drive, Applicant.drive_id == Drive.id)
            .filter(Drive.org_id == org.id, Applicant.id.in_(body.applicant_ids))
            .options(joinedload(Applicant.interview))
            .all()
        )
    }

    updated: list[UUID] = []
    skipped: list[str] = []

    for applicant_id in body.applicant_ids:
        applicant = owned.get(applicant_id)
        if applicant is None:
            skipped.append(f"{applicant_id}: not found")
            continue
        if applicant.status in (ApplicantStatus.SELECTED, ApplicantStatus.REJECTED):
            skipped.append(f"{applicant_id}: already {applicant.status.value}")
            continue

        applicant.status = target
        db.add(EmailLog(applicant_id=applicant.id, type=EmailType.RESULT))
        updated.append(applicant.id)

    db.commit()

    # Queue mail only after the batch has committed, so a failed write never
    # results in a candidate being told an outcome that was not saved.
    for applicant_id in updated:
        applicant = owned[applicant_id]
        background_tasks.add_task(
            send_result_email,
            to_email=applicant.email,
            to_name=applicant.name,
            drive_name=applicant.drive.name,
            result_status=target.value,
            score=(applicant.interview.total_score if applicant.interview else 0) or 0,
        )

    return BulkDecisionResponse(
        updated=len(updated),
        skipped=skipped,
        status=target.value,
    )
