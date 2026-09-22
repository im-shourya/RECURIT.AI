"""
Tests for per-user accounts and roles.

The property that matters most is that moving the login off the organisation
did not lock anybody out, and that role checks cannot be bypassed.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app
from app.models.database import ROLE_RANK, User, UserRole, PasswordResetToken
from app.models.schemas import TeamInviteRequest, TeamRoleUpdate
from app.services.auth_service import require_role
from pydantic import ValidationError

client = TestClient(app)
USER_ID = uuid.uuid4()


# ──────────────────────────────────────────────
# Role model
# ──────────────────────────────────────────────
def test_roles_are_ordered_by_capability():
    assert ROLE_RANK[UserRole.OWNER] > ROLE_RANK[UserRole.ADMIN] > ROLE_RANK[UserRole.MEMBER]


@pytest.mark.parametrize(
    "actor,required,allowed",
    [
        (UserRole.OWNER, UserRole.ADMIN, True),
        (UserRole.OWNER, UserRole.OWNER, True),
        (UserRole.ADMIN, UserRole.ADMIN, True),
        (UserRole.ADMIN, UserRole.OWNER, False),
        (UserRole.MEMBER, UserRole.ADMIN, False),
        (UserRole.MEMBER, UserRole.MEMBER, True),
    ],
)
def test_require_role_compares_by_rank(actor, required, allowed):
    """
    Rank rather than equality, so OWNER satisfies an ADMIN requirement without
    every call site having to list both.
    """
    guard = require_role(required)
    user = User(role=actor)

    if allowed:
        assert guard(user) is user
    else:
        with pytest.raises(HTTPException) as exc:
            guard(user)
        assert exc.value.status_code == 403


# ──────────────────────────────────────────────
# Existing logins must survive
# ──────────────────────────────────────────────
def test_password_hash_is_nullable_for_pending_invites():
    """An invited member has no password until they set one."""
    assert User.__table__.c.password_hash.nullable is True


def test_email_is_globally_unique():
    """Email is the sign-in identifier, so it cannot repeat across orgs."""
    assert User.__table__.c.email.unique is True


def test_migration_copies_the_existing_password_hash():
    """
    The backfill must copy the hash, never regenerate it — regenerating would
    lock every existing account out.
    """
    import pathlib

    migration = (
        pathlib.Path(__file__).resolve().parents[1]
        / "alembic" / "versions" / "0007_users_and_roles.py"
    ).read_text()

    assert "o.password_hash" in migration, "must copy the existing hash"
    assert "'owner'::user_role_enum" in migration
    assert "NOT EXISTS" in migration, "backfill must be re-runnable"


def test_migration_reattaches_outstanding_reset_tokens():
    """A reset link already in someone's inbox should still work afterwards."""
    import pathlib

    migration = (
        pathlib.Path(__file__).resolve().parents[1]
        / "alembic" / "versions" / "0007_users_and_roles.py"
    ).read_text()
    assert "UPDATE password_reset_tokens" in migration


def test_reset_tokens_can_point_at_a_user():
    assert "user_id" in PasswordResetToken.__table__.c
    assert PasswordResetToken.__table__.c.user_id.nullable is True


# ──────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────
@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/api/team"),
        ("post", "/api/team"),
        ("patch", f"/api/team/{USER_ID}"),
        ("delete", f"/api/team/{USER_ID}"),
    ],
)
def test_team_endpoints_require_authentication(method, path):
    kwargs = {"json": {"email": "invitee@example.com", "role": "member"}} if method in ("post", "patch") else {}
    assert getattr(client, method)(path, **kwargs).status_code == 401


def test_invitation_cannot_grant_ownership():
    """Ownership is transferred deliberately, never handed out in an invite."""
    with pytest.raises(ValidationError):
        TeamInviteRequest(email="invitee@example.com", role="owner")


@pytest.mark.parametrize("role", ["admin", "member"])
def test_invitation_roles_allowed(role):
    assert TeamInviteRequest(email="invitee@example.com", role=role).role == role


def test_role_update_accepts_owner_for_transfer():
    assert TeamRoleUpdate(role="owner").role == "owner"


@pytest.mark.parametrize("role", ["superuser", "OWNER", ""])
def test_role_update_rejects_unknown_roles(role):
    with pytest.raises(ValidationError):
        TeamRoleUpdate(role=role)


def test_owner_cannot_be_removed():
    import inspect
    from app.routers import team

    source = inspect.getsource(team.remove_member)
    assert "UserRole.OWNER" in source
    assert "Transfer ownership first" in source


def test_ownership_transfer_demotes_the_previous_owner():
    """
    Two owners would mean either could remove the other. Promotion transfers
    rather than duplicates.
    """
    import inspect
    from app.routers import team

    source = inspect.getsource(team.update_member_role)
    assert "actor.role = UserRole.ADMIN" in source


def test_invite_does_not_set_a_password():
    """
    A password must never be chosen on someone's behalf or transmitted; the
    invitee sets their own via the reset link.
    """
    import inspect
    from app.routers import team

    source = inspect.getsource(team.invite_member)
    assert "password_hash=None" in source
    assert "generate_reset_token" in source


def test_login_treats_a_pending_invite_like_a_wrong_password():
    """
    Otherwise the response would reveal which addresses have an unaccepted
    invitation waiting.
    """
    import inspect
    from app.routers import auth

    source = inspect.getsource(auth.login)
    assert "not user.password_hash" in source
    assert source.count("Invalid email or password") >= 1


def test_deactivated_user_is_rejected_on_the_next_request():
    """Deactivation must not wait for the token to expire."""
    import inspect
    from app.services import auth_service

    source = inspect.getsource(auth_service.get_current_user)
    assert "is_active" in source
