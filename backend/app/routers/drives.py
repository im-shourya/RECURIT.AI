"""
RECRUIT.AI — Drives Router
POST   /drives              — Create new drive (returns link + QR)
GET    /drives              — List all drives for the authenticated org
GET    /drives/{id}         — Drive detail + applicant list
PATCH  /drives/{id}/status  — Open / close drive
"""

import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.database import Drive, Organisation, TaskType, QuestionLevel, DriveStatus
from app.models.schemas import (
    DriveCreateRequest,
    DriveResponse,
    DriveDetailResponse,
    DriveStatusUpdate,
    ApplicantResponse,
)
from app.services.auth_service import get_current_org
from app.services.qr_service import generate_qr_for_drive, generate_apply_link

router = APIRouter(prefix="/drives", tags=["Drives"])


def _drive_to_response(drive: Drive, applicant_count: int = 0) -> DriveResponse:
    return DriveResponse(
        id=drive.id,
        org_id=drive.org_id,
        name=drive.name,
        domain=drive.domain,
        task_type=drive.task_type.value,
        task_description=drive.task_description,
        question_level=drive.question_level.value,
        apply_deadline=drive.apply_deadline,
        task_deadline=drive.task_deadline,
        link_token=drive.link_token,
        qr_code_url=drive.qr_code_url,
        status=drive.status.value,
        created_at=drive.created_at,
        applicant_count=applicant_count,
    )


# ──────────────────────────────────────────────
# CREATE DRIVE
# ──────────────────────────────────────────────
@router.post("", response_model=DriveResponse, status_code=status.HTTP_201_CREATED)
def create_drive(
    body: DriveCreateRequest,
    org: Organisation = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    # Validate task_deadline is present when task_type is "task"
    if body.task_type == "task" and not body.task_deadline:
        raise HTTPException(status_code=400, detail="task_deadline is required when task_type is 'task'")

    link_token = secrets.token_urlsafe(32)
    qr_code_url = generate_qr_for_drive(link_token)

    drive = Drive(
        org_id=org.id,
        name=body.name,
        domain=body.domain,
        task_type=TaskType(body.task_type),
        task_description=body.task_description,
        question_level=QuestionLevel(body.question_level),
        apply_deadline=body.apply_deadline,
        task_deadline=body.task_deadline,
        link_token=link_token,
        qr_code_url=qr_code_url,
    )
    db.add(drive)
    db.commit()
    db.refresh(drive)

    return _drive_to_response(drive)


# ──────────────────────────────────────────────
# LIST DRIVES
# ──────────────────────────────────────────────
@router.get("", response_model=list[DriveResponse])
def list_drives(
    org: Organisation = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    drives = db.query(Drive).filter(Drive.org_id == org.id).order_by(Drive.created_at.desc()).all()
    return [
        _drive_to_response(d, applicant_count=len(d.applicants))
        for d in drives
    ]


# ──────────────────────────────────────────────
# DRIVE DETAIL
# ──────────────────────────────────────────────
@router.get("/{drive_id}", response_model=DriveDetailResponse)
def get_drive(
    drive_id: UUID,
    org: Organisation = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    drive = db.query(Drive).filter(Drive.id == drive_id, Drive.org_id == org.id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")

    applicants_data = []
    for a in drive.applicants:
        applicants_data.append(
            ApplicantResponse(
                id=a.id,
                drive_id=a.drive_id,
                name=a.name,
                email=a.email,
                reg_no=a.reg_no,
                skills=a.skills or [],
                primary_domain=a.primary_domain,
                github_url=a.github_url,
                status=a.status.value,
                applied_at=a.applied_at,
                submission=a.submission,
                interview=a.interview,
            )
        )

    return DriveDetailResponse(
        id=drive.id,
        org_id=drive.org_id,
        name=drive.name,
        domain=drive.domain,
        task_type=drive.task_type.value,
        task_description=drive.task_description,
        question_level=drive.question_level.value,
        apply_deadline=drive.apply_deadline,
        task_deadline=drive.task_deadline,
        link_token=drive.link_token,
        qr_code_url=drive.qr_code_url,
        status=drive.status.value,
        created_at=drive.created_at,
        applicant_count=len(drive.applicants),
        organisation_name=drive.organisation.name,
        applicants=applicants_data,
    )


# ──────────────────────────────────────────────
# UPDATE DRIVE STATUS
# ──────────────────────────────────────────────
@router.patch("/{drive_id}/status", response_model=DriveResponse)
def update_drive_status(
    drive_id: UUID,
    body: DriveStatusUpdate,
    org: Organisation = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    drive = db.query(Drive).filter(Drive.id == drive_id, Drive.org_id == org.id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")

    drive.status = DriveStatus(body.status)
    db.commit()
    db.refresh(drive)
    return _drive_to_response(drive, applicant_count=len(drive.applicants))
