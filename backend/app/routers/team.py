"""
RECRUIT.AI — Team Router
GET    /team           — list members
POST   /team           — invite a member
PATCH  /team/{user_id} — change a member's role
DELETE /team/{user_id} — remove a member

Managing members is owner-only. Everything here is scoped to the caller's
organisation, so one org can never see or change another's people.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models.database import AuditAction, PasswordResetToken, User, UserRole
from app.models.schemas import (
    TeamMemberResponse,
    TeamInviteRequest,
    TeamRoleUpdate,
)
from app.services import audit
from app.services.auth_service import (
    generate_reset_token,
    get_current_user,
    require_role,
)
from app.services.email_service import send_password_reset_email

settings = get_settings()
router = APIRouter(prefix="/team", tags=["Team"])


def _to_response(user: User) -> TeamMemberResponse:
    return TeamMemberResponse(
        id=user.id,
        name=user.name or "",
        email=user.email,
        role=user.role.value,
        is_active=user.is_active,
        # No password hash means an invitation that has not been accepted.
        has_accepted_invite=user.password_hash is not None,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


def _owned_member(user_id: UUID, actor: User, db: Session) -> User:
    member = (
        db.query(User)
        .filter(User.id == user_id, User.org_id == actor.org_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


# ──────────────────────────────────────────────
# LIST
# ──────────────────────────────────────────────
@router.get("", response_model=list[TeamMemberResponse])
def list_members(
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Any member may see who else is on the team."""
    members = (
        db.query(User)
        .filter(User.org_id == actor.org_id)
        .order_by(User.created_at)
        .all()
    )
    return [_to_response(m) for m in members]


# ──────────────────────────────────────────────
# INVITE
# ──────────────────────────────────────────────
@router.post("", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
def invite_member(
    body: TeamInviteRequest,
    background_tasks: BackgroundTasks,
    actor: User = Depends(require_role(UserRole.OWNER)),
    db: Session = Depends(get_db),
):
    """
    Invite someone to the organisation.

    The member is created without a password and receives a reset link, so a
    password is never transmitted or chosen on their behalf. They cannot sign
    in until they set one.

    Only OWNER may invite, and an invitation cannot grant OWNER: promoting
    someone to owner is a separate, deliberate act.
    """
    if body.role == UserRole.OWNER.value:
        raise HTTPException(
            status_code=400,
            detail="An invitation cannot grant the owner role. Invite, then promote.",
        )

    # Email uniqueness is global, because it is the sign-in identifier.
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="That email is already in use")

    member = User(
        org_id=actor.org_id,
        name=body.name,
        email=body.email,
        password_hash=None,
        role=UserRole(body.role),
        is_active=True,
    )
    db.add(member)
    db.flush()

    plaintext, token_hash = generate_reset_token()
    db.add(
        PasswordResetToken(
            org_id=actor.org_id,
            user_id=member.id,
            token_hash=token_hash,
            # Longer than an ordinary reset: an invitation may sit unread for
            # a day or two, and an expired one means re-inviting.
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=settings.INVITE_TOKEN_TTL_MINUTES),
        )
    )

    audit.record(
        db,
        org_id=actor.org_id,
        action=AuditAction.MEMBER_INVITED,
        entity_type="user",
        entity_id=member.id,
        entity_label=member.email,
        detail={"role": member.role.value, "invited_by": actor.email},
    )
    db.commit()
    db.refresh(member)

    background_tasks.add_task(
        send_password_reset_email,
        to_email=member.email,
        to_name=member.name or member.email,
        reset_link=f"{settings.FRONTEND_URL}/auth/reset-password?token={plaintext}",
    )

    return _to_response(member)


# ──────────────────────────────────────────────
# CHANGE ROLE
# ──────────────────────────────────────────────
@router.patch("/{user_id}", response_model=TeamMemberResponse)
def update_member_role(
    user_id: UUID,
    body: TeamRoleUpdate,
    actor: User = Depends(require_role(UserRole.OWNER)),
    db: Session = Depends(get_db),
):
    """
    Change a member's role.

    An organisation must always have exactly one owner, so the current owner
    cannot demote themselves — doing so would leave nobody able to manage
    members, including nobody able to undo it. Transfer happens by promoting
    someone else, which demotes the previous owner in the same operation.
    """
    member = _owned_member(user_id, actor, db)
    new_role = UserRole(body.role)
    previous = member.role

    if member.id == actor.id and new_role != UserRole.OWNER:
        raise HTTPException(
            status_code=400,
            detail="Promote another member to owner instead; that transfers ownership.",
        )

    if new_role == UserRole.OWNER:
        # Ownership transfers rather than duplicates.
        actor.role = UserRole.ADMIN

    member.role = new_role

    audit.record(
        db,
        org_id=actor.org_id,
        action=AuditAction.MEMBER_ROLE_CHANGED,
        entity_type="user",
        entity_id=member.id,
        entity_label=member.email,
        detail={"from": previous.value, "to": new_role.value, "changed_by": actor.email},
    )
    db.commit()
    db.refresh(member)
    return _to_response(member)


# ──────────────────────────────────────────────
# REMOVE
# ──────────────────────────────────────────────
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    user_id: UUID,
    actor: User = Depends(require_role(UserRole.OWNER)),
    db: Session = Depends(get_db),
):
    """
    Remove a member's access.

    The owner cannot be removed: that would leave the organisation with no one
    able to manage it. Delete the organisation instead, or transfer ownership
    first.
    """
    member = _owned_member(user_id, actor, db)

    if member.role == UserRole.OWNER:
        raise HTTPException(
            status_code=400,
            detail="The owner cannot be removed. Transfer ownership first.",
        )

    audit.record(
        db,
        org_id=actor.org_id,
        action=AuditAction.MEMBER_REMOVED,
        entity_type="user",
        entity_id=member.id,
        entity_label=member.email,
        detail={"role": member.role.value, "removed_by": actor.email},
    )
    db.delete(member)
    db.commit()
    return None
