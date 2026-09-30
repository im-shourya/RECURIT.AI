"""
Tests for belonging to more than one organisation.

Email used to be unique across the whole deployment, so someone who ran one
club could not be invited to help with another, or register a second one.
A User is now one membership: unique per (email, organisation), with one
shared password across the memberships a person has accepted.
"""

import pytest
from fastapi import BackgroundTasks, HTTPException, Response
from mongomock_motor import AsyncMongoMockClient

from app.config import get_settings
from app.db import drop_superseded_indexes
from app.models.documents import Organisation, User, UserRole
from app.models.schemas import (
    OrgLoginRequest,
    OrgRegisterRequest,
    SwitchOrganisationRequest,
    TeamInviteRequest,
)
from app.routers.auth import login, register, switch_organisation
from app.routers.team import invite_member
from app.services.auth_service import (
    decode_token,
    hash_password,
    set_password,
    verify_password,
)

settings = get_settings()
PASSWORD = "correct-horse"


def _session(response: Response) -> dict:
    """The claims in the session cookie a handler just set."""
    header = response.headers["set-cookie"]
    token = header.split(f"{settings.SESSION_COOKIE_NAME}=", 1)[1].split(";", 1)[0]
    return decode_token(token)


@pytest.fixture
async def second_membership(owner, other_org) -> User:
    """The owner of the first organisation, also an accepted admin of a second."""
    member = User(
        org_id=other_org.id,
        name="Owner",
        email=owner.email,
        password_hash=owner.password_hash,
        role=UserRole.ADMIN,
    )
    await member.insert()
    return member


# ──────────────────────────────────────────────
# Joining a second organisation
# ──────────────────────────────────────────────
async def test_someone_in_one_organisation_can_be_invited_to_another(owner, other_org):
    rival_owner = User(
        org_id=other_org.id, email="rival-owner@example.com",
        password_hash=hash_password("rival-pass"), role=UserRole.OWNER,
    )
    await rival_owner.insert()

    invited = await invite_member(
        TeamInviteRequest(email=owner.email, name="Owner", role="member"),
        BackgroundTasks(),
        actor=rival_owner,
    )

    assert invited.has_accepted_invite is False
    assert await User.find(User.email == owner.email).count() == 2


async def test_inviting_an_existing_member_of_the_same_organisation_is_refused(owner):
    with pytest.raises(HTTPException) as exc:
        await invite_member(
            TeamInviteRequest(email=owner.email, name="Owner", role="member"),
            BackgroundTasks(),
            actor=owner,
        )
    assert exc.value.status_code == 400


async def test_registering_a_second_organisation_needs_the_existing_password(owner):
    with pytest.raises(HTTPException) as exc:
        await register(
            OrgRegisterRequest(name="Second Club", email=owner.email, password="not-it"),
            Response(),
        )
    assert exc.value.status_code == 400
    assert await Organisation.find(Organisation.name == "Second Club").count() == 0

    profile = await register(
        OrgRegisterRequest(name="Second Club", email=owner.email, password=PASSWORD),
        Response(),
    )
    assert profile.name == "Second Club"
    assert profile.role == "owner"
    assert {o.name for o in profile.organisations} == {"Sparkles Ltd", "Second Club"}


# ──────────────────────────────────────────────
# Signing in and switching
# ──────────────────────────────────────────────
async def test_login_lands_in_the_most_recently_used_organisation(
    owner, second_membership, other_org
):
    from datetime import datetime, timedelta, timezone

    second_membership.last_login_at = datetime.now(timezone.utc)
    owner.last_login_at = datetime.now(timezone.utc) - timedelta(days=1)
    await second_membership.save()
    await owner.save()

    response = Response()
    profile = await login(OrgLoginRequest(email=owner.email, password=PASSWORD), response)

    assert profile.id == other_org.id
    assert _session(response)["sub"] == str(second_membership.id)
    assert len(profile.organisations) == 2


async def test_switch_moves_the_session_to_the_other_membership(
    owner, second_membership, other_org
):
    response = Response()
    profile = await switch_organisation(
        SwitchOrganisationRequest(org_id=other_org.id), response, user=owner
    )

    assert profile.id == other_org.id
    assert profile.role == "admin"
    assert _session(response)["sub"] == str(second_membership.id)


async def test_switch_refuses_an_organisation_you_do_not_belong_to(owner, other_org):
    with pytest.raises(HTTPException) as exc:
        await switch_organisation(
            SwitchOrganisationRequest(org_id=other_org.id), Response(), user=owner
        )
    assert exc.value.status_code == 404


async def test_switch_refuses_a_pending_invitation(owner, other_org):
    """Being invited must not by itself grant a way in."""
    await User(org_id=other_org.id, email=owner.email, password_hash=None).insert()

    with pytest.raises(HTTPException) as exc:
        await switch_organisation(
            SwitchOrganisationRequest(org_id=other_org.id), Response(), user=owner
        )
    assert exc.value.status_code == 404


# ──────────────────────────────────────────────
# One password per person
# ──────────────────────────────────────────────
async def test_setting_a_password_applies_to_every_accepted_membership(
    owner, second_membership
):
    before = second_membership.token_version

    await set_password(owner, "a-brand-new-password")

    other = await User.get(second_membership.id)
    assert verify_password("a-brand-new-password", other.password_hash)
    assert other.token_version == before + 1, "its sessions must be signed out too"


async def test_setting_a_password_leaves_pending_invitations_pending(owner, other_org):
    pending = User(org_id=other_org.id, email=owner.email, password_hash=None)
    await pending.insert()

    await set_password(owner, "a-brand-new-password")

    assert (await User.get(pending.id)).password_hash is None


# ──────────────────────────────────────────────
# Migration
# ──────────────────────────────────────────────
async def test_the_old_deployment_wide_unique_index_is_dropped():
    database = AsyncMongoMockClient()["migration_test"]
    await database["users"].create_index("email", unique=True)
    assert "email_1" in await database["users"].index_information()

    await drop_superseded_indexes(database)
    await drop_superseded_indexes(database)  # and again, as on every boot

    assert "email_1" not in await database["users"].index_information()
