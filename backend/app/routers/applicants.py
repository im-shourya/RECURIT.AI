"""
RECRUIT.AI — Applicants Router (Public Endpoints)
GET  /apply/{link_token}        — Fetch drive details for the apply form
POST /apply/{link_token}        — Submit application → triggers email
POST /submit/{applicant_id}     — Submit task/GitHub → triggers RepoLens + interview email
"""

import secrets
from datetime import date, datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
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
)
from app.services.email_service import send_application_email, send_interview_email
from app.services.qr_service import generate_apply_link
from app.config import get_settings

settings = get_settings()
router = APIRouter(tags=["Applicants (Public)"])


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
@router.post("/apply/{link_token}", response_model=ApplicantResponse, status_code=status.HTTP_201_CREATED)
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
    )
    db.add(applicant)
    db.commit()
    db.refresh(applicant)

    # ── Determine next steps based on task_type ──
    org_name = drive.organisation.name

    if drive.task_type == TaskType.TASK:
        # Task path: send email with task link + submission link
        applicant.status = ApplicantStatus.TASK_SENT
        db.commit()

        task_link = f"{settings.FRONTEND_URL}/task/{drive.link_token}"
        submission_link = f"{settings.FRONTEND_URL}/submit/{applicant.id}"

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
@router.post("/submit/{applicant_id}", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_task(
    applicant_id: UUID,
    body: SubmissionCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    applicant = db.query(Applicant).filter(Applicant.id == applicant_id).first()
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")

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
