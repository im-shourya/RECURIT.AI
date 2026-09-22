"""
RECRUIT.AI — Audit Log

Records consequential actions so a hiring decision can be traced to who made
it and when.

Under PostgreSQL an entry joined the caller's transaction, so the action and
its record landed together or not at all. MongoDB has no ambient transaction
here, so the entry is written immediately and independently.

That changes the failure mode rather than the intent: previously an audit
failure would roll the action back, now the action can succeed with no entry
behind it. Writes are best-effort and never raise, because the alternative —
a rejection that fails to save because the log was unavailable — is worse
than a missing log line.
"""

import logging
from typing import Optional
from uuid import UUID

from app.models.documents import AuditAction, AuditLog

log = logging.getLogger("recruit.audit")


async def record(
    *,
    org_id: UUID,
    action: AuditAction,
    entity_type: str,
    entity_id: Optional[UUID] = None,
    entity_label: str = "",
    detail: Optional[dict] = None,
) -> None:
    """Append an audit entry. Never raises."""
    try:
        await AuditLog(
            org_id=org_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            # Captured now so the entry stays readable after the subject is
            # deleted — the id resolves to nothing afterwards.
            entity_label=(entity_label or "")[:255],
            detail=detail or {},
        ).insert()
    except Exception as exc:
        log.error(
            "could not record audit entry",
            extra={
                "action": getattr(action, "value", str(action)),
                "error": type(exc).__name__,
            },
        )
