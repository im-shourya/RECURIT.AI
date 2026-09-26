"""
RECRUIT.AI — Audit Log

Records consequential actions so a hiring decision can be traced back to who
made it and when.

Writes are best-effort: an audit failure must never roll back or block the
action it describes. A missing audit row is bad; a rejected candidate whose
rejection failed to save because the log was unavailable is worse.
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.database import AuditAction, AuditLog

log = logging.getLogger("recruit.audit")


def record(
    db: Session,
    *,
    org_id: UUID,
    action: AuditAction,
    entity_type: str,
    entity_id: Optional[UUID] = None,
    entity_label: str = "",
    detail: Optional[dict] = None,
) -> None:
    """
    Append an audit entry to the caller's session.

    Added but not committed: it rides the same transaction as the action it
    describes, so the two land together or not at all.
    """
    try:
        db.add(
            AuditLog(
                org_id=org_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                # Captured now so the entry stays readable after the subject
                # is deleted.
                entity_label=(entity_label or "")[:255],
                detail=detail or {},
            )
        )
    except Exception as exc:
        log.error(
            "could not record audit entry",
            extra={"action": getattr(action, "value", str(action)), "error": type(exc).__name__},
        )
