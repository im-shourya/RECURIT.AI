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

Stored files are the exception: their keys are collected first, but the
objects are removed only after the documents are gone. A storage error must
not leave a record in place, and an orphaned object is recoverable where a
half-deleted candidate is not.
"""

import logging
from typing import Any, Iterable, Optional
from uuid import UUID

from anyio import to_thread
from pydantic import BaseModel

from app.models.documents import (
    Applicant,
    AuditLog,
    Drive,
    Organisation,
    PasswordResetToken,
    User,
)
from app.services import storage_service

log = logging.getLogger("recruit.cascade")


class _StoredFiles(BaseModel):
    """Only the fields that hold object keys, so transcripts are never loaded."""

    submission: Optional[dict[str, Any]] = None
    interview: Optional[dict[str, Any]] = None

    class Settings:
        projection = {"submission.file_url": 1, "interview.recording_url": 1}


def stored_file_keys(applicant: Applicant | _StoredFiles) -> list[str]:
    """Every object key an applicant's document points at."""
    submission, interview = applicant.submission, applicant.interview
    if isinstance(submission, BaseModel):
        submission = submission.model_dump()
    if isinstance(interview, BaseModel):
        interview = interview.model_dump()

    keys = [
        (submission or {}).get("file_url") or "",
        (interview or {}).get("recording_url") or "",
    ]
    return [key for key in keys if key]


async def _keys_for(query) -> list[str]:
    keys: list[str] = []
    async for record in query.project(_StoredFiles):
        keys.extend(stored_file_keys(record))
    return keys


def _delete_all(keys: list[str]) -> int:
    """Blocking; run in a worker thread. Returns how many were left behind."""
    failed = 0
    for key in keys:
        try:
            storage_service.delete_object(key)
        except Exception as exc:
            failed += 1
            log.error(
                "stored file left behind after deletion",
                extra={"key": key, "error": type(exc).__name__},
            )
    return failed


async def delete_stored_files(keys: Iterable[str]) -> int:
    """
    Best-effort removal of stored objects. Never raises.

    boto3 is synchronous, so the deletes run in a worker thread rather than
    stalling the event loop for every other request. Returns the number that
    could not be removed.
    """
    keys = list(keys)
    if not keys:
        return 0
    return await to_thread.run_sync(_delete_all, keys)


async def delete_drive(drive: Drive) -> int:
    """
    Delete a drive and every applicant under it.

    Returns how many applicants went with it, so the caller can record that in
    the audit entry.
    """
    keys = await _keys_for(Applicant.find(Applicant.drive_id == drive.id))

    result = await Applicant.find(Applicant.drive_id == drive.id).delete()
    removed = getattr(result, "deleted_count", 0) or 0

    await drive.delete()
    await delete_stored_files(keys)
    log.info(
        "drive deleted",
        extra={
            "drive_id": str(drive.id),
            "applicants_deleted": removed,
            "stored_files": len(keys),
        },
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

    keys = await _keys_for(Applicant.find(Applicant.org_id == org.id))
    if org.logo_url:
        # delete_object ignores anything that is not one of our keys, so a
        # logo supplied as a plain URL is left alone.
        keys.append(org.logo_url)

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
    await delete_stored_files(keys)
    counts["stored_files"] = len(keys)
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

    Each count is one aggregation that joins every child to its parent by id
    inside MongoDB and returns a single number. Nothing is loaded into this
    process, so it stays usable on a large deployment. The earlier version
    built id sets from whole collections in memory.
    """
    return {
        "drives": await _count_missing_parent(Drive, "org_id", Organisation),
        "applicants": await _count_missing_parent(Applicant, "drive_id", Drive),
        "users": await _count_missing_parent(User, "org_id", Organisation),
    }


async def _count_missing_parent(child, field: str, parent) -> int:
    """How many `child` documents point, through `field`, at no `parent`."""
    rows = await child.find_all().aggregate([
        # Only the reference travels through the rest of the pipeline.
        {"$project": {field: 1}},
        {"$lookup": {
            "from": parent.get_settings().name,
            "localField": field,
            "foreignField": "_id",
            "as": "parent",
        }},
        {"$match": {"parent": {"$size": 0}}},
        {"$count": "n"},
    ]).to_list()
    return rows[0]["n"] if rows else 0
