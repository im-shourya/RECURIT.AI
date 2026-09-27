"""
RECRUIT.AI — Team Router
GET    /team           — list members
POST   /team           — invite a member
PATCH  /team/{user_id} — change a member's role
DELETE /team/{user_id} — remove a member

Managing members is owner-only; everything is scoped to the caller's
organisation.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.config import get_settings
from app.models.documents import AuditAction, PasswordResetToken, User, UserRole
from app.models.schemas import TeamInviteRequest, TeamMemberResponse, TeamRoleUpdate
from app.services import audit, cascade
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


async def _owned_member(user_id: UUID, actor: User) -> User:
    member = await User.find_one(User.id == user_id, User.org_id == actor.org_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


# ──────────────────────────────────────────────
# LIST
# ──────────────────────────────────────────────
@router.get("", response_model=list[TeamMemberResponse])
async def list_members(actor: User = Depends(get_current_user)):
    """Any member may see who else is on the team."""
    members = (
        await User.find(User.org_id == actor.org_id).sort(User.created_at).to_list()
    )
    return [_to_response(m) for m in members]


# ──────────────────────────────────────────────
# INVITE
# ──────────────────────────────────────────────
@router.post("", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
async def invite_member(
    body: TeamInviteRequest,
    background_tasks: BackgroundTasks,
    actor: User = Depends(require_role(UserRole.OWNER)),
):
    """
    The member is created without a password and receives a reset link, so a
    password is never transmitted or chosen on their behalf.

    An invitation cannot grant OWNER: promoting someone is a separate,
    deliberate act.
    """
    if body.role == UserRole.OWNER.value:
        raise HTTPException(
            status_code=400,
            detail="An invitation cannot grant the owner role. Invite, then promote.",
        )

    if await User.find_one(User.email == body.email):
        raise HTTPException(status_code=400, detail="That email is already in use")

    member = User(
        org_id=actor.org_id,
        name=body.name,
        email=body.email,
        password_hash=None,
        role=UserRole(body.role),
        is_active=True,
    )
    await member.insert()

    plaintext, token_hash = generate_reset_token()
    await PasswordResetToken(
        org_id=actor.org_id,
        user_id=member.id,
        token_hash=token_hash,
        # Longer than an ordinary reset: an invitation may sit unread for a
        # day or two, and expiry means re-inviting.
        expires_at=datetime.now(timezone.utc)
        + timedelta(minutes=settings.INVITE_TOKEN_TTL_MINUTES),
    ).insert()

    await audit.record(
        org_id=actor.org_id,
        action=AuditAction.MEMBER_INVITED,
        entity_type="user",
        entity_id=member.id,
        entity_label=member.email,
        detail={"role": member.role.value, "invited_by": actor.email},
    )

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
async def update_member_role(
    user_id: UUID,
    body: TeamRoleUpdate,
    actor: User = Depends(require_role(UserRole.OWNER)),
):
    """
    An organisation always has exactly one owner, so the current owner cannot
    demote themselves — that would leave nobody able to manage members,
    including nobody able to undo it. Ownership transfers by promoting someone
    else, which demotes the previous owner in the same operation.
    """
    member = await _owned_member(user_id, actor)
    new_role = UserRole(body.role)
    previous = member.role

    if member.id == actor.id and new_role != UserRole.OWNER:
        raise HTTPException(
            status_code=400,
            detail="Promote another member to owner instead; that transfers ownership.",
        )

    if new_role == UserRole.OWNER:
        # Ownership transfers rather than duplicates: two owners would mean
        # either could remove the other.
        actor.role = UserRole.ADMIN
        await actor.save()

    member.role = new_role
    await member.save()

    await audit.record(
        org_id=actor.org_id,
        action=AuditAction.MEMBER_ROLE_CHANGED,
        entity_type="user",
        entity_id=member.id,
        entity_label=member.email,
        detail={"from": previous.value, "to": new_role.value, "changed_by": actor.email},
    )
    return _to_response(member)


# ──────────────────────────────────────────────
# REMOVE
# ──────────────────────────────────────────────
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    user_id: UUID,
    actor: User = Depends(require_role(UserRole.OWNER)),
):
    """
    The owner cannot be removed: that would leave the organisation with nobody
    able to manage it. Transfer ownership first.
    """
    member = await _owned_member(user_id, actor)

    if member.role == UserRole.OWNER:
        raise HTTPException(
            status_code=400,
            detail="The owner cannot be removed. Transfer ownership first.",
        )

    await audit.record(
        org_id=actor.org_id,
        action=AuditAction.MEMBER_REMOVED,
        entity_type="user",
        entity_id=member.id,
        entity_label=member.email,
        detail={"role": member.role.value, "removed_by": actor.email},
    )

    # Their outstanding reset tokens go too: an invitation still sitting in an
    # inbox must stop working the moment access is revoked.
    await cascade.delete_user(member)
    return None
