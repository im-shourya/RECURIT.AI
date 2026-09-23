"""
RECRUIT.AI — Applicants Router (Public Endpoints)
GET  /apply/{link_token}           — Drive details for the apply form
POST /apply/{link_token}           — Submit an application
POST /submit/{submit_token}        — Submit task/GitHub work
POST /submit/{submit_token}/upload — Upload a submission file
GET  /status/{submit_token}        — Candidate's own application status

Every route here is reached by an unguessable token, never by a database id.
"""

import logging
import secrets
from datetime import date, datetime, timedelta, timezone

from fastapi import (
    APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status,
)
from pymongo.errors import DuplicateKeyError

from app.config import get_settings
from app.models.documents import (
    Applicant,
    ApplicantStatus,
    Drive,
    DriveStatus,
    EmailLogEntry,
    EmailType,
    Interview,
    Organisation,
    Submission,
    TaskType,
)
from app.models.schemas import (
    ApplicantResponse,
    ApplicantStatusView,
    ApplyRequest,
    DrivePublicResponse,
    FileUploadResponse,
    SubmissionCreateRequest,
    SubmissionResponse,
)
from app.services import storage_service
from app.services.email_service import send_application_email, send_interview_email
from app.services.rate_limit import RateLimit

settings = get_settings()
log = logging.getLogger("recruit.applicants")
router = APIRouter(tags=["Applicants (Public)"])


async def _applicant_by_submit_token(submit_token: str) -> Applicant:
    """
    Resolve the submission capability token.

    An unknown token returns the same 404 as a missing applicant, so the
    endpoint cannot be used to probe which tokens exist.
    """
    applicant = await Applicant.find_one(Applicant.submit_token == submit_token)
    if not applicant:
        raise HTTPException(status_code=404, detail="Submission link is invalid")
    return applicant


def _new_interview() -> Interview:
    return Interview(
        token=secrets.token_urlsafe(32),
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.INTERVIEW_TOKEN_TTL_DAYS),
    )


# ──────────────────────────────────────────────
# DRIVE INFO FOR THE APPLY FORM
# ──────────────────────────────────────────────
@router.get(
    "/apply/{link_token}",
    response_model=DrivePublicResponse,
    # Generous: this is a page load, and a drive link is shared widely.
    dependencies=[Depends(RateLimit("apply_view", limit=120, window_seconds=3600,
                                    key_param="link_token"))],
)
async def get_drive_for_apply(link_token: str):
    drive = await Drive.find_one(Drive.link_token == link_token)
    if not drive:
        raise HTTPException(status_code=404, detail="Recruitment drive not found")
    if drive.status != DriveStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail="This recruitment drive is no longer accepting applications",
        )
    if drive.apply_deadline < date.today():
        raise HTTPException(status_code=400, detail="Application deadline has passed")

    org = await Organisation.get(drive.org_id)

    return DrivePublicResponse(
        id=drive.id,
        name=drive.name,
        domain=drive.domain,
        task_type=drive.task_type.value,
        task_description=drive.task_description,
        question_level=drive.question_level.value,
        apply_deadline=drive.apply_deadline,
        task_deadline=drive.task_deadline,
        organisation_name=org.name if org else "",
        organisation_logo=(org.logo_url if org else "") or "",
        status=drive.status.value,
    )


# ──────────────────────────────────────────────
# SUBMIT AN APPLICATION
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
):
    drive = await Drive.find_one(Drive.link_token == link_token)
    if not drive:
        raise HTTPException(status_code=404, detail="Recruitment drive not found")
    if drive.status != DriveStatus.ACTIVE:
        raise HTTPException(
            status_code=400, detail="This drive is no longer accepting applications"
        )
    if drive.apply_deadline < date.today():
        raise HTTPException(status_code=400, detail="Application deadline has passed")

    org = await Organisation.get(drive.org_id)
    org_name = org.name if org else ""

    applicant = Applicant(
        drive_id=drive.id,
        org_id=drive.org_id,
        name=body.name,
        email=body.email,
        reg_no=body.reg_no,
        skills=body.skills,
        primary_domain=body.primary_domain,
        github_url=body.github_url,
        status=ApplicantStatus.APPLIED,
        # Capability token for the submission endpoint, so that route never
        # keys off a bare id.
        submit_token=secrets.token_urlsafe(32),
    )

    try:
        await applicant.insert()
    except DuplicateKeyError:
        # The pre-check is a read before a write, so two concurrent requests
        # could both pass it. The unique index on (drive_id, email) is what
        # actually closes that window; a double-click reads the same as
        # applying twice.
        raise HTTPException(
            status_code=400, detail="You have already applied to this drive"
        )

    submission_link = f"{settings.FRONTEND_URL}/submit/{applicant.submit_token}"

    if drive.task_type == TaskType.TASK:
        applicant.status = ApplicantStatus.TASK_SENT
        background_tasks.add_task(
            send_application_email,
            to_email=applicant.email,
            to_name=applicant.name,
            drive_name=drive.name,
            org_name=org_name,
            task_link=f"{settings.FRONTEND_URL}/task/{drive.link_token}",
            submission_link=submission_link,
        )

    elif drive.task_type == TaskType.GITHUB:
        if body.github_url:
            applicant.interview = _new_interview()
            applicant.status = ApplicantStatus.INTERVIEW_SENT

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
                interview_link=f"{settings.FRONTEND_URL}/interview/{applicant.interview.token}",
            )
            # TODO: trigger RepoLens analysis once the GitAnalyser service is wired in
        else:
            background_tasks.add_task(
                send_application_email,
                to_email=applicant.email,
                to_name=applicant.name,
                drive_name=drive.name,
                org_name=org_name,
            )

    applicant.email_logs.append(EmailLogEntry(type=EmailType.APPLIED))
    await applicant.save()

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
@router.post(
    "/submit/{submit_token}",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    # One submission is expected; the rest is retries after an error.
    dependencies=[Depends(RateLimit("submit", limit=10, window_seconds=3600,
                                    key_param="submit_token"))],
)
async def submit_task(
    submit_token: str,
    body: SubmissionCreateRequest,
    background_tasks: BackgroundTasks,
):
    """
    Keyed on an unguessable token rather than the applicant's id. The old
    route accepted a bare id, so anyone holding or guessing one could submit
    on another candidate's behalf.
    """
    applicant = await _applicant_by_submit_token(submit_token)

    if applicant.submission:
        raise HTTPException(status_code=400, detail="You have already submitted")

    drive = await Drive.get(applicant.drive_id)
    if drive and drive.task_deadline and drive.task_deadline < date.today():
        raise HTTPException(status_code=400, detail="Submission deadline has passed")

    applicant.submission = Submission(
        file_url=body.file_url,
        github_url=body.github_url,
        description=body.description,
    )
    applicant.status = ApplicantStatus.SUBMITTED

    applicant.interview = _new_interview()
    applicant.status = ApplicantStatus.INTERVIEW_SENT
    applicant.email_logs.append(EmailLogEntry(type=EmailType.INTERVIEW))
    await applicant.save()

    background_tasks.add_task(
        send_interview_email,
        to_email=applicant.email,
        to_name=applicant.name,
        drive_name=drive.name if drive else "",
        interview_link=f"{settings.FRONTEND_URL}/interview/{applicant.interview.token}",
    )
    # TODO: trigger RepoLens analysis once the GitAnalyser service is wired in

    return SubmissionResponse(
        id=applicant.id,
        applicant_id=applicant.id,
        file_url=applicant.submission.file_url,
        github_url=applicant.submission.github_url,
        description=applicant.submission.description,
        repolens_analysis=applicant.submission.repolens_analysis or {},
        submitted_at=applicant.submission.submitted_at,
    )


# ──────────────────────────────────────────────
# UPLOAD A SUBMISSION FILE
# ──────────────────────────────────────────────
@router.post(
    "/submit/{submit_token}/upload",
    response_model=FileUploadResponse,
    # Each accepted upload is up to 10MB of object storage, so this is a
    # spend limit as much as an abuse limit.
    dependencies=[Depends(RateLimit("submit_upload", limit=10, window_seconds=3600,
                                    key_param="submit_token"))],
)
async def upload_submission_file(
    submit_token: str,
    file: UploadFile = File(...),
):
    """
    Upload is a separate step from creating the submission, so an interrupted
    upload leaves no half-finished application behind.
    """
    applicant = await _applicant_by_submit_token(submit_token)

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
        # Not surfaced verbatim: it can carry bucket names and credential detail.
        log.error(
            "submission upload failed",
            extra={"applicant_id": str(applicant.id), "error": str(exc)},
        )
        raise HTTPException(status_code=502, detail="Upload failed, please try again")

    return FileUploadResponse(file_url=key, filename=file.filename or "")


# ──────────────────────────────────────────────
# CANDIDATE SELF-SERVICE STATUS
# ──────────────────────────────────────────────
@router.get(
    "/status/{submit_token}",
    response_model=ApplicantStatusView,
    # Candidates refresh this while they wait, so it is deliberately loose.
    dependencies=[Depends(RateLimit("status", limit=120, window_seconds=3600,
                                    key_param="submit_token"))],
)
async def get_own_status(submit_token: str):
    """
    Reuses the token the candidate already holds, so no new credential is
    introduced.

    Deliberately narrow: progress, deadlines and the final outcome, but never
    the interview score, transcript or malpractice flags. Those are the
    recruiter's evidence, and showing them mid-process would tell a candidate
    how they are being graded while they are still being graded.
    """
    applicant = await _applicant_by_submit_token(submit_token)
    drive = await Drive.get(applicant.drive_id)
    org = await Organisation.get(applicant.org_id)

    decided = applicant.status in (ApplicantStatus.SELECTED, ApplicantStatus.REJECTED)

    return ApplicantStatusView(
        name=applicant.name,
        drive_name=drive.name if drive else "",
        organisation_name=org.name if org else "",
        status=applicant.status.value,
        applied_at=applicant.applied_at,
        task_deadline=drive.task_deadline if drive else None,
        has_submitted=applicant.submission is not None,
        interview_completed=bool(applicant.interview and applicant.interview.ended_at),
        decision=applicant.status.value if decided else None,
    )
