"""
RECRUIT.AI — Deletion Cascades

PostgreSQL enforced these with ON DELETE CASCADE. MongoDB has no equivalent,
so every cascade the schema used to guarantee now lives here.

This is the main thing the move to MongoDB gives away, so it is deliberately
in one file rather than scattered through the routers: if a delete is added
elsewhere and forgets to come through here, orphaned documents are the result,
and the database will not object.

Embedded documents — submission, interview, email logs — need no handling.
They are part of the applicant document and go with it.

Ordering is children-first throughout. Deleting a parent first would leave
orphans behind if a later step fails, and an orphan is harder to find than a
parent that is still there.
"""

import logging
from uuid import UUID

from app.models.documents import (
    Applicant,
    AuditLog,
    Drive,
    Organisation,
    PasswordResetToken,
    User,
)

log = logging.getLogger("recruit.cascade")


async def delete_drive(drive: Drive) -> int:
    """
    Delete a drive and every applicant under it.

    Returns how many applicants went with it, so the caller can record that in
    the audit entry.
    """
    result = await Applicant.find(Applicant.drive_id == drive.id).delete()
    removed = getattr(result, "deleted_count", 0) or 0

    await drive.delete()
    log.info(
        "drive deleted",
        extra={"drive_id": str(drive.id), "applicants_deleted": removed},
    )
    return removed


async def delete_organisation(org: Organisation) -> dict[str, int]:
    """
    Delete an organisation and everything beneath it.

    The audit log goes too. It outlives individual applicants on purpose, but
    not the organisation itself: once the account is gone there is nobody left
    with the standing to read it, and keeping it would mean retaining records
    about people after the controller has been removed.
    """
    counts: dict[str, int] = {}

    for label, query in (
        ("applicants", Applicant.find(Applicant.org_id == org.id)),
        ("drives", Drive.find(Drive.org_id == org.id)),
        ("reset_tokens", PasswordResetToken.find(PasswordResetToken.org_id == org.id)),
        ("audit_entries", AuditLog.find(AuditLog.org_id == org.id)),
        ("users", User.find(User.org_id == org.id)),
    ):
        result = await query.delete()
        counts[label] = getattr(result, "deleted_count", 0) or 0

    await org.delete()
    log.info("organisation deleted", extra={"org_id": str(org.id), **counts})
    return counts


async def delete_user(user: User) -> None:
    """
    Remove a member.

    Their outstanding reset tokens go with them: an invitation or reset link
    still sitting in an inbox must stop working the moment access is revoked,
    otherwise removal is reversible by whoever holds the link.
    """
    await PasswordResetToken.find(PasswordResetToken.user_id == user.id).delete()
    await user.delete()
    log.info("user deleted", extra={"user_id": str(user.id)})


async def count_orphans() -> dict[str, int]:
    """
    Count documents whose parent no longer exists.

    Diagnostic only. The database cannot enforce these relationships any more,
    so this is how a bug that skips the cascades above becomes visible instead
    of silently accumulating.
    """
    org_ids = {o.id async for o in Organisation.find_all().project(Organisation)}
    drive_ids = {d.id async for d in Drive.find_all().project(Drive)}

    orphans = {
        "drives": 0,
        "applicants": 0,
        "users": 0,
    }

    async for drive in Drive.find_all():
        if drive.org_id not in org_ids:
            orphans["drives"] += 1

    async for applicant in Applicant.find_all():
        if applicant.drive_id not in drive_ids:
            orphans["applicants"] += 1

    async for user in User.find_all():
        if user.org_id not in org_ids:
            orphans["users"] += 1

    return orphans
