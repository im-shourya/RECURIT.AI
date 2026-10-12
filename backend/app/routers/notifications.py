"""
RECRUIT.AI — Notifications Router
GET  /notifications             — Newest first, with this user's unread count
POST /notifications/{id}/read   — Mark one as read for the caller
POST /notifications/read-all    — Mark every one as read for the caller

Open to every member: they announce applications, submissions and finished
interviews, all of which a member can already see in the dashboard. Read
state is per person, so marking something read never hides it from a
colleague.
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.models.documents import Notification, User
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class NotificationResponse(BaseModel):
    id: UUID
    kind: str
    title: str
    body: str
    link: str
    created_at: datetime
    read: bool


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    unread_count: int


def _unread_by(user: User) -> dict:
    return {"org_id": user.org_id, "read_by": {"$ne": user.id}}


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
):
    items = (
        await Notification.find(Notification.org_id == user.org_id)
        .sort(-Notification.created_at)
        .limit(limit)
        .to_list()
    )
    return NotificationListResponse(
        items=[
            NotificationResponse(
                id=n.id,
                kind=n.kind.value,
                title=n.title,
                body=n.body,
                link=n.link,
                # MongoDB returns naive UTC. Without the zone the browser reads
                # it as local time and "2 minutes ago" is off by the offset.
                created_at=n.created_at.replace(tzinfo=n.created_at.tzinfo or timezone.utc),
                read=user.id in n.read_by,
            )
            for n in items
        ],
        unread_count=await Notification.find(_unread_by(user)).count(),
    )


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_read(user: User = Depends(get_current_user)):
    await Notification.find(_unread_by(user)).update({"$addToSet": {"read_by": user.id}})
    return None


@router.post("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_read(notification_id: UUID, user: User = Depends(get_current_user)):
    # Scoped to the caller's organisation: another organisation's id is a 404,
    # the same as one that does not exist.
    notification = await Notification.find_one(
        Notification.id == notification_id, Notification.org_id == user.org_id
    )
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")

    await Notification.find(Notification.id == notification.id).update(
        {"$addToSet": {"read_by": user.id}}
    )
    return None
