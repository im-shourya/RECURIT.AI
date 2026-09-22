"""
RECRUIT.AI — Applicants Router (Public Endpoints)
GET  /apply/{link_token}        — Fetch drive details for the apply form
POST /apply/{link_token}        — Submit application → triggers email
POST /submit/{applicant_id}        — Submit task/GitHub → triggers RepoLens + interview email
POST /submit/{applicant_id}/upload — Upload a submission file to object storage
"""

import logging
import secrets
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile, File
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.database import (
    Drive, Applicant, Submission, Interview, EmailLog,
    DriveStatus, ApplicantStatus, TaskType, EmailType,
)
from app.models.schemas import (
    ApplyRequest,
    ApplicantResponse,
    DrivePublicResponse,
    SubmissionCreateRequest,
    SubmissionResponse,
    FileUploadResponse,
)
from app.services.email_service import send_application_email, send_interview_email
from app.services import storage_service
from app.services.rate_limit import RateLimit
from app.services.qr_service import generate_apply_link
from app.config import get_settings

settings = get_settings()
log = logging.getLogger("recruit.applicants")
router = APIRouter(tags=["Applicants (Public)"])


def _applicant_by_submit_token(submit_token: str, db: Session) -> Applicant:
    """
    Resolve the submission capability token.

    An unknown token returns 404 with the same wording as a missing applicant,
    so the endpoint cannot be used to probe which tokens exist.
    """
    applicant = (
        db.query(Applicant).filter(Applicant.submit_token == submit_token).first()
    )
    if not applicant:
        raise HTTPException(status_code=404, detail="Submission link is invalid")
    return applicant


# ──────────────────────────────────────────────
# FETCH DRIVE INFO FOR APPLY FORM
# ──────────────────────────────────────────────
@router.get("/apply/{link_token}", response_model=DrivePublicResponse)
def get_drive_for_apply(link_token: str, db: Session = Depends(get_db)):
    drive = db.query(Drive).filter(Drive.link_token == link_token).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Recruitment drive not found")
    if drive.status != DriveStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="This recruitment drive is no longer accepting applications")
    if drive.apply_deadline < date.today():
        raise HTTPException(status_code=400, detail="Application deadline has passed")

    return DrivePublicResponse(
        id=drive.id,
        name=drive.name,
        domain=drive.domain,
        task_type=drive.task_type.value,
        task_description=drive.task_description,
        question_level=drive.question_level.value,
        apply_deadline=drive.apply_deadline,
        task_deadline=drive.task_deadline,
        organisation_name=drive.organisation.name,
        organisation_logo=drive.organisation.logo_url or "",
        status=drive.status.value,
    )


# ──────────────────────────────────────────────
# SUBMIT APPLICATION
# ──────────────────────────────────────────────
@router.post(
    "/apply/{link_token}",
    response_model=ApplicantResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimit("apply", limit=10, window_seconds=3600))],
)
async def submit_application(
    link_token: str,
    body: ApplyRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    drive = db.query(Drive).filter(Drive.link_token == link_token).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Recruitment drive not found")
    if drive.status != DriveStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="This drive is no longer accepting applications")
    if drive.apply_deadline < date.today():
        raise HTTPException(status_code=400, detail="Application deadline has passed")

    # Check for duplicate application
    existing = db.query(Applicant).filter(
        Applicant.drive_id == drive.id,
        Applicant.email == body.email,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already applied to this drive")

    # Create applicant
    applicant = Applicant(
        drive_id=drive.id,
        name=body.name,
        email=body.email,
        reg_no=body.reg_no,
        skills=body.skills,
        primary_domain=body.primary_domain,
        github_url=body.github_url,
        status=ApplicantStatus.APPLIED,
        # Capability token for the submission endpoint. Issued to every
        # applicant so the public route never keys off a bare UUID.
        submit_token=secrets.token_urlsafe(32),
    )
    db.add(applicant)
    try:
        db.commit()
    except IntegrityError:
        # Lost the race against a concurrent duplicate submit. The unique
        # constraint did its job; report it the same way the pre-check does so
        # a double-click is indistinguishable from applying twice.
        db.rollback()
        raise HTTPException(
            status_code=400, detail="You have already applied to this drive"
        )
    db.refresh(applicant)

    # ── Determine next steps based on task_type ──
    org_name = drive.organisation.name

    if drive.task_type == TaskType.TASK:
        # Task path: send email with task link + submission link
        applicant.status = ApplicantStatus.TASK_SENT
        db.commit()

        task_link = f"{settings.FRONTEND_URL}/task/{drive.link_token}"
        submission_link = f"{settings.FRONTEND_URL}/submit/{applicant.submit_token}"

        background_tasks.add_task(
            send_application_email,
            to_email=applicant.email,
            to_name=applicant.name,
            drive_name=drive.name,
            org_name=org_name,
            task_link=task_link,
            submission_link=submission_link,
        )

    elif drive.task_type == TaskType.GITHUB:
        # GitHub path: if they provided a GitHub URL, send interview link directly
        if body.github_url:
            interview_token = secrets.token_urlsafe(32)
            interview = Interview(
                applicant_id=applicant.id,
                token=interview_token,
                expires_at=datetime.now(timezone.utc)
                + timedelta(days=settings.INTERVIEW_TOKEN_TTL_DAYS),
            )
            db.add(interview)
            applicant.status = ApplicantStatus.INTERVIEW_SENT
            db.commit()

            interview_link = f"{settings.FRONTEND_URL}/interview/{interview_token}"

            background_tasks.add_task(
                send_application_email,
                to_email=applicant.email,
                to_name=applicant.name,
                drive_name=drive.name,
                org_name=org_name,
            )
            background_tasks.add_task(
                send_interview_email,
                to_email=applicant.email,
                to_name=applicant.name,
                drive_name=drive.name,
                interview_link=interview_link,
            )

            # TODO: trigger RepoLens analysis as async Celery job here
        else:
            # No GitHub URL provided — just confirm application
            background_tasks.add_task(
                send_application_email,
                to_email=applicant.email,
                to_name=applicant.name,
                drive_name=drive.name,
                org_name=org_name,
            )

    # Log the email
    email_log = EmailLog(
        applicant_id=applicant.id,
        type=EmailType.APPLIED,
    )
    db.add(email_log)
    db.commit()
    db.refresh(applicant)

    return ApplicantResponse(
        id=applicant.id,
        drive_id=applicant.drive_id,
        name=applicant.name,
        email=applicant.email,
        reg_no=applicant.reg_no,
        skills=applicant.skills or [],
        primary_domain=applicant.primary_domain,
        github_url=applicant.github_url,
        status=applicant.status.value,
        applied_at=applicant.applied_at,
    )


# ──────────────────────────────────────────────
# SUBMIT TASK / GITHUB PROJECT
# ──────────────────────────────────────────────
@router.post("/submit/{submit_token}", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_task(
    submit_token: str,
    body: SubmissionCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Submit a task or project.

    Keyed on an unguessable token rather than the applicant's UUID. The old
    route accepted a bare id, so anyone holding or guessing one could submit
    on another candidate's behalf.
    """
    applicant = _applicant_by_submit_token(submit_token, db)

    # Check applicant hasn't already submitted
    if applicant.submission:
        raise HTTPException(status_code=400, detail="You have already submitted")

    drive = applicant.drive

    # Check deadline
    if drive.task_deadline and drive.task_deadline < date.today():
        raise HTTPException(status_code=400, detail="Submission deadline has passed")

    # Create submission record
    submission = Submission(
        applicant_id=applicant.id,
        file_url=body.file_url,
        github_url=body.github_url,
        description=body.description,
    )
    db.add(submission)

    # Update applicant status
    applicant.status = ApplicantStatus.SUBMITTED
    db.commit()
    db.refresh(submission)

    # ── Create interview and send link ──
    interview_token = secrets.token_urlsafe(32)
    interview = Interview(
        applicant_id=applicant.id,
        token=interview_token,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.INTERVIEW_TOKEN_TTL_DAYS),
    )
    db.add(interview)
    applicant.status = ApplicantStatus.INTERVIEW_SENT
    db.commit()

    interview_link = f"{settings.FRONTEND_URL}/interview/{interview_token}"
    background_tasks.add_task(
        send_interview_email,
        to_email=applicant.email,
        to_name=applicant.name,
        drive_name=drive.name,
        interview_link=interview_link,
    )

    # Log interview email
    email_log = EmailLog(
        applicant_id=applicant.id,
        type=EmailType.INTERVIEW,
    )
    db.add(email_log)
    db.commit()
    db.refresh(submission)

    # TODO: Trigger RepoLens analysis as async Celery job if github_url is present

    return SubmissionResponse(
        id=submission.id,
        applicant_id=submission.applicant_id,
        file_url=submission.file_url,
        github_url=submission.github_url,
        description=submission.description,
        repolens_analysis=submission.repolens_analysis or {},
        submitted_at=submission.submitted_at,
    )


# ──────────────────────────────────────────────
# UPLOAD A SUBMISSION FILE
# ──────────────────────────────────────────────
@router.post("/submit/{submit_token}/upload", response_model=FileUploadResponse)
async def upload_submission_file(
    submit_token: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a candidate's submission file and return the stored object key.

    The key is what the caller then passes as `file_url` to POST /submit/{id}.
    Uploading does not itself create a submission, so an interrupted upload
    leaves no half-finished application behind.

    The file is untrusted: the extension is allowlisted, the size cap is
    enforced while streaming, the object key is built only from server-side
    values, and the stored object is private.
    """
    applicant = _applicant_by_submit_token(submit_token, db)

    if applicant.submission:
        raise HTTPException(status_code=400, detail="You have already submitted")

    if not storage_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="File uploads are not available: object storage is not configured",
        )

    try:
        key = storage_service.upload_submission_file(
            applicant_id=applicant.id,
            filename=file.filename or "",
            stream=file.file,
        )
    except storage_service.UnsupportedFileType as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except storage_service.UploadTooLarge as exc:
        raise HTTPException(status_code=413, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except storage_service.StorageError as exc:
        # Do not surface the backend error verbatim; it can carry bucket names
        # and credentials detail.
        log.error(
            "submission upload failed",
            extra={"applicant_id": str(applicant.id), "error": str(exc)},
        )
        raise HTTPException(status_code=502, detail="Upload failed, please try again")

    return FileUploadResponse(file_url=key, filename=file.filename or "")
