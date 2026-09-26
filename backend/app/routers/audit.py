"""
RECRUIT.AI — Audit Router
GET /audit — the calling organisation's audit trail
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from app.models.documents import AuditAction, AuditLog, Organisation
from app.models.schemas import AuditEntryResponse
from app.services.auth_service import get_current_org

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("", response_model=list[AuditEntryResponse])
async def list_audit_entries(
    response: Response,
    action: Optional[str] = Query(None, description="Filter by action"),
    entity_id: Optional[UUID] = Query(None, description="Filter to one subject"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    org: Organisation = Depends(get_current_org),
):
    """
    Newest first, scoped to the calling organisation.

    Read-only by design: there is no endpoint to edit or delete an entry,
    because a trail that can be rewritten answers nothing.
    """
    conditions = [AuditLog.org_id == org.id]

    if action:
        valid = {a.value for a in AuditAction}
        if action not in valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action. Expected one of: {', '.join(sorted(valid))}",
            )
        conditions.append(AuditLog.action == AuditAction(action))

    if entity_id:
        conditions.append(AuditLog.entity_id == entity_id)

    query = AuditLog.find(*conditions)

    total = await query.count()
    response.headers["X-Total-Count"] = str(total)
    response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"

    entries = (
        await query.sort(-AuditLog.created_at).skip(offset).limit(limit).to_list()
    )

    return [
        AuditEntryResponse(
            id=e.id,
            action=e.action.value,
            entity_type=e.entity_type,
            entity_id=e.entity_id,
            entity_label=e.entity_label or "",
            detail=e.detail or {},
            created_at=e.created_at,
        )
        for e in entries
    ]
