"""
RECRUIT.AI — In-app notifications

Writes the events shown under the dashboard bell. Like the audit log, a write
is best-effort and never raises: a candidate's application must not fail
because the notification about it could not be stored.
"""

import logging
from typing import Optional
from uuid import UUID

from app.models.documents import Applicant, Notification, NotificationKind

log = logging.getLogger("recruit.notifications")


async def notify(
    *,
    org_id: UUID,
    kind: NotificationKind,
    title: str,
    body: str = "",
    link: str = "",
    drive_id: Optional[UUID] = None,
    applicant_id: Optional[UUID] = None,
) -> None:
    """Record one notification for the organisation. Never raises."""
    try:
        await Notification(
            org_id=org_id,
            kind=kind,
            title=title[:255],
            body=body[:500],
            link=link,
            drive_id=drive_id,
            applicant_id=applicant_id,
        ).insert()
    except Exception as exc:
        log.error(
            "could not record notification",
            extra={"kind": kind.value, "error": type(exc).__name__},
        )


async def about_applicant(
    applicant: Applicant, kind: NotificationKind, title: str, body: str
) -> None:
    """A notification that opens this applicant's profile."""
    await notify(
        org_id=applicant.org_id,
        kind=kind,
        title=title,
        body=body,
        link=f"/dashboard/applicants/{applicant.id}",
        drive_id=applicant.drive_id,
        applicant_id=applicant.id,
    )
