"""
RECRUIT.AI — Drives Router
POST   /drives              — Create new drive (returns link + QR)
GET    /drives              — List all drives for the authenticated org
GET    /drives/{id}         — Drive detail + applicant list
PATCH  /drives/{id}/status  — Open / close drive
"""

import secrets
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.database import Drive, Organisation, TaskType, QuestionLevel, DriveStatus, AuditAction
from app.models.schemas import (
    DriveCreateRequest,
    DriveResponse,
    DriveDetailResponse,
    DriveStatusUpdate,
    DriveUpdateRequest,
    ApplicantResponse,
)
from app.services.auth_service import get_current_org
from app.services import audit
from app.services.qr_service import generate_qr_for_drive, generate_apply_link

def _close_if_past_deadline(drive: Drive, db: Session) -> Drive:
    """
    Close a drive whose apply deadline has passed.

    There is no scheduler in this project, so rather than leave every expired
    drive sitting at "active" — which made closed drives look open in the
    dashboard and counted them as active in analytics — the transition happens
    lazily the next time the drive is read. It is idempotent and only ever
    moves active -> closed, never the reverse, so a drive the recruiter closed
    early stays closed.
    """
    if drive.status == DriveStatus.ACTIVE and drive.apply_deadline < date.today():
        drive.status = DriveStatus.CLOSED
        db.commit()
        db.refresh(drive)
    return drive


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
    db.flush()
    audit.record(
        db, org_id=org.id, action=AuditAction.DRIVE_CREATED,
        entity_type="drive", entity_id=drive.id, entity_label=drive.name,
    )
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
    for drive in drives:
        _close_if_past_deadline(drive, db)
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


# ──────────────────────────────────────────────
# UPDATE DRIVE
# ──────────────────────────────────────────────
@router.patch("/{drive_id}", response_model=DriveResponse)
def update_drive(
    drive_id: UUID,
    body: DriveUpdateRequest,
    org: Organisation = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    """
    Edit a drive's details.

    `task_type` is not editable. Switching between a task drive and a GitHub
    drive mid-flight would strand applicants who already progressed down the
    other branch, so that needs a new drive rather than an edit.
    """
    drive = db.query(Drive).filter(Drive.id == drive_id, Drive.org_id == org.id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")

    fields = body.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    # A task drive still needs a task deadline after the edit.
    if "task_deadline" in fields and fields["task_deadline"] is None:
        if drive.task_type == TaskType.TASK:
            raise HTTPException(
                status_code=400,
                detail="task_deadline is required while task_type is 'task'",
            )

    for key, value in fields.items():
        if key == "question_level":
            drive.question_level = QuestionLevel(value)
        elif key == "status":
            drive.status = DriveStatus(value)
        else:
            setattr(drive, key, value)

    db.commit()
    db.refresh(drive)
    return _drive_to_response(drive, applicant_count=len(drive.applicants))


# ──────────────────────────────────────────────
# DELETE DRIVE
# ──────────────────────────────────────────────
@router.delete("/{drive_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_drive(
    drive_id: UUID,
    confirm: bool = Query(
        False,
        description="Required to delete a drive that already has applicants",
    ),
    org: Organisation = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    """
    Permanently delete a drive.

    This cascades to every applicant, submission, interview and email log under
    it — candidate data that cannot be recovered. A drive with applicants
    therefore refuses to delete unless ?confirm=true is passed, so a stray
    click cannot wipe a live recruitment round. Closing a drive
    (PATCH status=closed) is the non-destructive alternative.
    """
    drive = db.query(Drive).filter(Drive.id == drive_id, Drive.org_id == org.id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")

    applicant_count = len(drive.applicants)
    if applicant_count and not confirm:
        raise HTTPException(
            status_code=409,
            detail=(
                f"This drive has {applicant_count} applicant(s). Deleting it also "
                f"deletes their submissions and interviews. Re-send with "
                f"?confirm=true to proceed, or close the drive instead."
            ),
        )

    audit.record(
        db, org_id=org.id, action=AuditAction.DRIVE_DELETED,
        entity_type="drive", entity_id=drive.id, entity_label=drive.name,
        detail={"applicants_deleted": applicant_count},
    )
    db.delete(drive)
    db.commit()
    return None
