"""
RECRUIT.AI — Drives Router (Organisation-only)
POST   /drives                — Create a drive
GET    /drives                — List the org's drives
GET    /drives/{id}           — Drive detail with applicants
PATCH  /drives/{id}           — Edit a drive
PATCH  /drives/{id}/status    — Open / close
DELETE /drives/{id}           — Delete, guarded
"""

import secrets
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.documents import (
    Applicant,
    AuditAction,
    Drive,
    DriveStatus,
    Organisation,
    QuestionLevel,
    TaskType,
)
from app.models.schemas import (
    DriveCreateRequest,
    DriveDetailResponse,
    DriveResponse,
    DriveStatusUpdate,
    DriveUpdateRequest,
)
from app.services import audit
from app.services import cascade
from app.services.auth_service import get_current_org
from app.services.qr_service import generate_qr_for_drive

router = APIRouter(prefix="/drives", tags=["Drives"])


def _to_response(drive: Drive, applicant_count: int = 0) -> DriveResponse:
    return DriveResponse(
        id=drive.id,
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


async def _owned_drive(drive_id: UUID, org: Organisation) -> Drive:
    drive = await Drive.find_one(Drive.id == drive_id, Drive.org_id == org.id)
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")
    return drive


async def _close_if_past_deadline(drive: Drive) -> Drive:
    """
    Close a drive whose apply deadline has passed.

    There is no scheduler, so rather than leave expired drives at "active" —
    which made closed drives look open in the dashboard and counted them as
    active in analytics — the transition happens lazily on read. Idempotent,
    only ever active -> closed, and does not write when nothing changes.
    """
    if drive.status == DriveStatus.ACTIVE and drive.apply_deadline < date.today():
        drive.status = DriveStatus.CLOSED
        await drive.save()
    return drive


# ──────────────────────────────────────────────
# CREATE
# ──────────────────────────────────────────────
@router.post("", response_model=DriveResponse, status_code=status.HTTP_201_CREATED)
async def create_drive(
    body: DriveCreateRequest,
    org: Organisation = Depends(get_current_org),
):
    if body.task_type == "task" and not body.task_deadline:
        raise HTTPException(
            status_code=400, detail="task_deadline is required when task_type is 'task'"
        )

    link_token = secrets.token_urlsafe(32)
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
        qr_code_url=generate_qr_for_drive(link_token),
    )
    await drive.insert()

    await audit.record(
        org_id=org.id,
        action=AuditAction.DRIVE_CREATED,
        entity_type="drive",
        entity_id=drive.id,
        entity_label=drive.name,
    )
    return _to_response(drive)


# ──────────────────────────────────────────────
# LIST
# ──────────────────────────────────────────────
@router.get("", response_model=list[DriveResponse])
async def list_drives(org: Organisation = Depends(get_current_org)):
    drives = await Drive.find(Drive.org_id == org.id).sort(-Drive.created_at).to_list()

    out = []
    for drive in drives:
        await _close_if_past_deadline(drive)
        count = await Applicant.find(Applicant.drive_id == drive.id).count()
        out.append(_to_response(drive, applicant_count=count))
    return out


# ──────────────────────────────────────────────
# DETAIL
# ──────────────────────────────────────────────
@router.get("/{drive_id}", response_model=DriveDetailResponse)
async def get_drive(
    drive_id: UUID,
    org: Organisation = Depends(get_current_org),
):
    drive = await _owned_drive(drive_id, org)
    await _close_if_past_deadline(drive)

    applicants = await Applicant.find(Applicant.drive_id == drive.id).to_list()

    # Imported here to avoid a circular import at module load: the applicant
    # router imports from this one for the shared serialiser.
    from app.routers.applicant_admin import applicant_to_response

    base = _to_response(drive, applicant_count=len(applicants))
    return DriveDetailResponse(
        **base.model_dump(),
        organisation_name=org.name,
        applicants=[applicant_to_response(a) for a in applicants],
    )


# ──────────────────────────────────────────────
# UPDATE
# ──────────────────────────────────────────────
@router.patch("/{drive_id}", response_model=DriveResponse)
async def update_drive(
    drive_id: UUID,
    body: DriveUpdateRequest,
    org: Organisation = Depends(get_current_org),
):
    """
    task_type is not editable: switching a drive between the task and GitHub
    flows mid-round would strand applicants who already went down the other
    branch.
    """
    drive = await _owned_drive(drive_id, org)

    fields = body.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

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

    await drive.save()

    await audit.record(
        org_id=org.id,
        action=AuditAction.DRIVE_UPDATED,
        entity_type="drive",
        entity_id=drive.id,
        entity_label=drive.name,
        detail={"fields": sorted(fields)},
    )

    count = await Applicant.find(Applicant.drive_id == drive.id).count()
    return _to_response(drive, applicant_count=count)


# ──────────────────────────────────────────────
# STATUS
# ──────────────────────────────────────────────
@router.patch("/{drive_id}/status", response_model=DriveResponse)
async def update_drive_status(
    drive_id: UUID,
    body: DriveStatusUpdate,
    org: Organisation = Depends(get_current_org),
):
    drive = await _owned_drive(drive_id, org)
    drive.status = DriveStatus(body.status)
    await drive.save()

    count = await Applicant.find(Applicant.drive_id == drive.id).count()
    return _to_response(drive, applicant_count=count)


# ──────────────────────────────────────────────
# DELETE
# ──────────────────────────────────────────────
@router.delete("/{drive_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_drive(
    drive_id: UUID,
    confirm: bool = Query(
        False, description="Required to delete a drive that already has applicants"
    ),
    org: Organisation = Depends(get_current_org),
):
    """
    Deleting a drive also deletes every applicant under it — candidate data
    that cannot be recovered. A drive with applicants therefore refuses unless
    ?confirm=true, so a stray click cannot wipe a live round; closing the
    drive remains the non-destructive alternative.

    MongoDB has no ON DELETE CASCADE, so the applicants are removed explicitly
    by cascade.delete_drive.
    """
    drive = await _owned_drive(drive_id, org)

    applicant_count = await Applicant.find(Applicant.drive_id == drive.id).count()
    if applicant_count and not confirm:
        raise HTTPException(
            status_code=409,
            detail=(
                f"This drive has {applicant_count} applicant(s). Deleting it also "
                f"deletes their submissions and interviews. Re-send with "
                f"?confirm=true to proceed, or close the drive instead."
            ),
        )

    await audit.record(
        org_id=org.id,
        action=AuditAction.DRIVE_DELETED,
        entity_type="drive",
        entity_id=drive.id,
        entity_label=drive.name,
        detail={"applicants_deleted": applicant_count},
    )

    await cascade.delete_drive(drive)
    return None
