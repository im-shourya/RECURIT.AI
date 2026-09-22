"""
Tests for the deletion cascades.

PostgreSQL enforced these with ON DELETE CASCADE. MongoDB has none, so they
are application code now — which makes them the single biggest thing the move
gives away, and the part most worth testing for real.

Every test here deletes something and then asserts what survived, rather than
inspecting source.
"""

from datetime import date, timedelta

import pytest

from app.models.documents import (
    Applicant,
    AuditAction,
    AuditLog,
    Drive,
    Organisation,
    PasswordResetToken,
    TaskType,
    User,
    UserRole,
)
from app.services import cascade


async def _drive_for(org: Organisation, token: str) -> Drive:
    record = Drive(
        org_id=org.id,
        name=f"Drive {token}",
        domain="Web",
        task_type=TaskType.GITHUB,
        apply_deadline=date.today() + timedelta(days=7),
        link_token=token,
    )
    await record.insert()
    return record


async def _applicant_for(drive: Drive, email: str) -> Applicant:
    record = Applicant(
        drive_id=drive.id,
        org_id=drive.org_id,
        name=email,
        email=email,
        submit_token=f"token-{email}",
    )
    await record.insert()
    return record


# ──────────────────────────────────────────────
# Drive deletion
# ──────────────────────────────────────────────
async def test_deleting_a_drive_removes_its_applicants(drive, applicant):
    removed = await cascade.delete_drive(drive)

    assert removed == 1
    assert await Drive.get(drive.id) is None
    assert await Applicant.get(applicant.id) is None


async def test_deleting_a_drive_leaves_other_drives_alone(org, drive, applicant):
    """The cascade must be scoped, or one deletion takes the account with it."""
    other = await _drive_for(org, "other-drive")
    survivor = await _applicant_for(other, "survivor@example.com")

    await cascade.delete_drive(drive)

    assert await Drive.get(other.id) is not None
    assert await Applicant.get(survivor.id) is not None


async def test_deleting_an_empty_drive_reports_zero(org):
    empty = await _drive_for(org, "empty-drive")
    assert await cascade.delete_drive(empty) == 0


# ──────────────────────────────────────────────
# Organisation deletion
# ──────────────────────────────────────────────
async def test_deleting_an_organisation_removes_everything_beneath_it(
    org, owner, drive, applicant
):
    await PasswordResetToken(
        org_id=org.id, user_id=owner.id, token_hash="h" * 64,
        expires_at=date.today() + timedelta(days=1),
    ).insert()
    await AuditLog(
        org_id=org.id, action=AuditAction.DRIVE_CREATED,
        entity_type="drive", entity_id=drive.id, entity_label=drive.name,
    ).insert()

    counts = await cascade.delete_organisation(org)

    assert await Organisation.get(org.id) is None
    assert await User.get(owner.id) is None
    assert await Drive.get(drive.id) is None
    assert await Applicant.get(applicant.id) is None
    assert await PasswordResetToken.find_all().count() == 0
    # The audit log outlives individual applicants, but not the organisation:
    # once the account is gone nobody is left with standing to read it.
    assert await AuditLog.find_all().count() == 0

    assert counts["users"] == 1
    assert counts["drives"] == 1
    assert counts["applicants"] == 1


async def test_deleting_an_organisation_spares_another(org, other_org, applicant):
    """
    The most damaging possible bug in this file: a cascade that is not scoped
    would wipe every other customer's data.
    """
    their_drive = await _drive_for(other_org, "their-drive")
    theirs = await _applicant_for(their_drive, "theirs@example.com")
    their_user = User(
        org_id=other_org.id, email="them@example.com", role=UserRole.OWNER
    )
    await their_user.insert()

    await cascade.delete_organisation(org)

    assert await Organisation.get(other_org.id) is not None
    assert await Drive.get(their_drive.id) is not None
    assert await Applicant.get(theirs.id) is not None
    assert await User.get(their_user.id) is not None


# ──────────────────────────────────────────────
# User deletion
# ──────────────────────────────────────────────
async def test_removing_a_member_revokes_their_pending_links(org, owner):
    """
    An invitation or reset link still sitting in an inbox must stop working
    the moment access is revoked, or removal is reversible by whoever holds
    the link.
    """
    member = User(org_id=org.id, email="member@example.com", role=UserRole.MEMBER)
    await member.insert()
    await PasswordResetToken(
        org_id=org.id, user_id=member.id, token_hash="m" * 64,
        expires_at=date.today() + timedelta(days=1),
    ).insert()

    await cascade.delete_user(member)

    assert await User.get(member.id) is None
    assert await PasswordResetToken.find_all().count() == 0


async def test_removing_a_member_leaves_other_members_tokens(org, owner):
    member = User(org_id=org.id, email="member@example.com", role=UserRole.MEMBER)
    await member.insert()

    owner_token = PasswordResetToken(
        org_id=org.id, user_id=owner.id, token_hash="o" * 64,
        expires_at=date.today() + timedelta(days=1),
    )
    await owner_token.insert()

    await cascade.delete_user(member)

    assert await PasswordResetToken.get(owner_token.id) is not None
    assert await User.get(owner.id) is not None


# ──────────────────────────────────────────────
# Orphan detection
# ──────────────────────────────────────────────
async def test_orphan_check_is_clean_after_a_correct_cascade(org, drive, applicant):
    await cascade.delete_drive(drive)
    assert await cascade.count_orphans() == {
        "drives": 0, "applicants": 0, "users": 0,
    }


async def test_orphan_check_notices_a_skipped_cascade(org, drive, applicant):
    """
    The database can no longer object to a dangling reference, so this is how
    a bug that bypasses the cascades becomes visible instead of silently
    accumulating.
    """
    # Delete the drive directly, the way a future careless change might.
    await drive.delete()

    orphans = await cascade.count_orphans()
    assert orphans["applicants"] == 1
