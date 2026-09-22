"""
One-off data migration: PostgreSQL (Supabase) -> MongoDB.

The code switch in this branch moves where *new* data is written. This moves
the data that already exists.

Not a dump/restore: submissions, interviews and email_logs were separate
tables and are now embedded inside the applicant document, so rows have to be
joined and nested on the way across.

Reads PostgreSQL with raw SQL rather than the old SQLAlchemy models, which no
longer exist on this branch — and which would otherwise have to be resurrected
and kept in step just to run this once.

Usage:

    # Look, change nothing
    DATABASE_URL=postgresql://...  MONGODB_URL=mongodb://...  \
        python scripts/migrate_postgres_to_mongo.py --dry-run

    # Do it
    DATABASE_URL=postgresql://...  MONGODB_URL=mongodb://...  \
        python scripts/migrate_postgres_to_mongo.py

Safe to re-run: every document is upserted by its existing id, so a migration
interrupted half way can simply be run again. Ids are preserved, which is what
keeps links already emailed to candidates — and audit entries pointing at
them — resolving afterwards.

Requires psycopg2, which this branch no longer depends on:

    pip install psycopg2-binary
"""

import argparse
import asyncio
import os
import sys
from collections import defaultdict

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    sys.exit(
        "psycopg2 is needed to read the old database:\n"
        "    pip install psycopg2-binary"
    )

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

# Path setup so this runs as `python scripts/...` from backend/.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models.documents import (  # noqa: E402
    ALL_DOCUMENTS,
    Applicant,
    AuditLog,
    Drive,
    EmailLogEntry,
    EmailOutbox,
    Interview,
    Organisation,
    PasswordResetToken,
    Submission,
    User,
)


def fetch(cursor, table: str) -> list[dict]:
    """Read a whole table, tolerating one that does not exist."""
    try:
        cursor.execute(f"SELECT * FROM {table}")
        return [dict(row) for row in cursor.fetchall()]
    except psycopg2.errors.UndefinedTable:
        cursor.connection.rollback()
        print(f"  ! {table} does not exist, skipping")
        return []


async def upsert(document) -> None:
    """
    Insert or replace by id.

    Keeping the original id is the point: links already emailed to candidates
    and audit entries referencing them must keep resolving.
    """
    await document.get_motor_collection().replace_one(
        {"_id": document.id},
        document.model_dump(by_alias=True, exclude={"revision_id"}),
        upsert=True,
    )


async def run(dry_run: bool) -> int:
    pg_url = os.environ.get("DATABASE_URL")
    mongo_url = os.environ.get("MONGODB_URL")
    mongo_db = os.environ.get("MONGODB_DB", "recruit_ai")

    if not pg_url or not mongo_url:
        sys.exit("Set both DATABASE_URL and MONGODB_URL")

    connection = psycopg2.connect(pg_url)
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    print(f"Reading PostgreSQL: {pg_url.split('@')[-1]}")
    orgs = fetch(cursor, "organisations")
    users = fetch(cursor, "users")
    drives = fetch(cursor, "drives")
    applicants = fetch(cursor, "applicants")
    submissions = fetch(cursor, "submissions")
    interviews = fetch(cursor, "interviews")
    email_logs = fetch(cursor, "email_logs")
    reset_tokens = fetch(cursor, "password_reset_tokens")
    audit_entries = fetch(cursor, "audit_log")
    outbox = fetch(cursor, "email_outbox")

    # Index the child rows so each applicant can be assembled in one pass.
    submission_by_applicant = {s["applicant_id"]: s for s in submissions}
    interview_by_applicant = {i["applicant_id"]: i for i in interviews}
    logs_by_applicant = defaultdict(list)
    for entry in email_logs:
        logs_by_applicant[entry["applicant_id"]].append(entry)

    drive_org = {d["id"]: d["org_id"] for d in drives}

    counts = {
        "organisations": len(orgs),
        "users": len(users),
        "drives": len(drives),
        "applicants": len(applicants),
        "  ├ submissions embedded": len(submissions),
        "  ├ interviews embedded": len(interviews),
        "  └ email logs embedded": len(email_logs),
        "password_reset_tokens": len(reset_tokens),
        "audit_log": len(audit_entries),
        "email_outbox": len(outbox),
    }
    print("\nFound:")
    for label, count in counts.items():
        print(f"  {label:26} {count}")

    if dry_run:
        orphans = [a for a in applicants if a["drive_id"] not in drive_org]
        if orphans:
            print(f"\n  ! {len(orphans)} applicant(s) reference a missing drive")
            print("    They would be skipped; resolve before the real run.")
        print("\nDry run: nothing written.")
        return 0

    client = AsyncIOMotorClient(mongo_url, uuidRepresentation="standard")
    await init_beanie(database=client[mongo_db], document_models=ALL_DOCUMENTS)
    print(f"\nWriting MongoDB: {mongo_db}")

    for row in orgs:
        await upsert(Organisation(
            id=row["id"], name=row["name"], email=row["email"],
            description=row.get("description") or "",
            domain_tags=list(row.get("domain_tags") or []),
            logo_url=row.get("logo_url") or "",
            # Column added late; default to on for rows that predate it.
            notify_on_interview=row.get("notify_on_interview", True),
            created_at=row["created_at"],
        ))

    for row in users:
        await upsert(User(
            id=row["id"], org_id=row["org_id"], name=row.get("name") or "",
            email=row["email"], password_hash=row.get("password_hash"),
            role=row["role"], is_active=row.get("is_active", True),
            created_at=row["created_at"], last_login_at=row.get("last_login_at"),
        ))

    for row in drives:
        await upsert(Drive(
            id=row["id"], org_id=row["org_id"], name=row["name"],
            domain=row["domain"], task_type=row["task_type"],
            task_description=row.get("task_description") or "",
            question_level=row.get("question_level") or "beginner",
            apply_deadline=row["apply_deadline"],
            task_deadline=row.get("task_deadline"),
            link_token=row["link_token"],
            qr_code_url=row.get("qr_code_url") or "",
            status=row.get("status") or "active",
            created_at=row["created_at"],
        ))

    skipped = 0
    for row in applicants:
        org_id = drive_org.get(row["drive_id"])
        if org_id is None:
            # org_id is denormalised onto the applicant and there is nowhere to
            # read it from without the drive. Skipped rather than guessed.
            skipped += 1
            continue

        sub = submission_by_applicant.get(row["id"])
        itv = interview_by_applicant.get(row["id"])

        await upsert(Applicant(
            id=row["id"], drive_id=row["drive_id"], org_id=org_id,
            name=row["name"], email=row["email"],
            reg_no=row.get("reg_no") or "",
            skills=list(row.get("skills") or []),
            primary_domain=row.get("primary_domain") or "",
            github_url=row.get("github_url") or "",
            submit_token=row.get("submit_token"),
            status=row["status"], applied_at=row["applied_at"],
            submission=Submission(
                file_url=sub.get("file_url") or "",
                github_url=sub.get("github_url") or "",
                description=sub.get("description") or "",
                repolens_analysis=sub.get("repolens_analysis") or {},
                submitted_at=sub["submitted_at"],
            ) if sub else None,
            interview=Interview(
                token=itv["token"], expires_at=itv.get("expires_at"),
                started_at=itv.get("started_at"), ended_at=itv.get("ended_at"),
                recording_url=itv.get("recording_url") or "",
                transcript=itv.get("transcript") or [],
                score_intro=itv.get("score_intro") or 0,
                score_project=itv.get("score_project") or 0,
                score_domain=itv.get("score_domain") or 0,
                total_score=itv.get("total_score") or 0,
                malpractice_flags=itv.get("malpractice_flags") or [],
            ) if itv else None,
            email_logs=[
                EmailLogEntry(
                    type=e["type"], sent_at=e["sent_at"],
                    provider_message_id=e.get("emailjs_msg_id") or "",
                )
                for e in logs_by_applicant.get(row["id"], [])
            ],
        ))

    for row in reset_tokens:
        await upsert(PasswordResetToken(
            id=row["id"], org_id=row["org_id"], user_id=row.get("user_id"),
            token_hash=row["token_hash"], expires_at=row["expires_at"],
            used_at=row.get("used_at"), created_at=row["created_at"],
        ))

    for row in audit_entries:
        await upsert(AuditLog(
            id=row["id"], org_id=row["org_id"], action=row["action"],
            entity_type=row["entity_type"], entity_id=row.get("entity_id"),
            entity_label=row.get("entity_label") or "",
            detail=row.get("detail") or {}, created_at=row["created_at"],
        ))

    for row in outbox:
        await upsert(EmailOutbox(
            id=row["id"], to_email=row["to_email"], subject=row["subject"],
            html=row["html"], text=row.get("text") or "",
            status=row["status"], attempts=row.get("attempts") or 0,
            last_error=row.get("last_error") or "",
            provider_message_id=row.get("provider_message_id") or "",
            created_at=row["created_at"], sent_at=row.get("sent_at"),
        ))

    # Read back rather than trusting the write loop.
    print("\nVerifying:")
    for model, expected in (
        (Organisation, len(orgs)),
        (User, len(users)),
        (Drive, len(drives)),
        (Applicant, len(applicants) - skipped),
        (PasswordResetToken, len(reset_tokens)),
        (AuditLog, len(audit_entries)),
        (EmailOutbox, len(outbox)),
    ):
        actual = await model.find_all().count()
        mark = "ok" if actual == expected else "MISMATCH"
        print(f"  {model.Settings.name:24} {actual}/{expected}  {mark}")

    with_submission = await Applicant.find(
        {"submission": {"$ne": None}}
    ).count()
    with_interview = await Applicant.find({"interview": {"$ne": None}}).count()
    print(f"  {'embedded submissions':24} {with_submission}/{len(submissions)}")
    print(f"  {'embedded interviews':24} {with_interview}/{len(interviews)}")

    if skipped:
        print(f"\n  ! skipped {skipped} applicant(s) whose drive was missing")

    cursor.close()
    connection.close()
    print("\nDone.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true", help="Report what would move, write nothing"
    )
    args = parser.parse_args()
    sys.exit(asyncio.run(run(args.dry_run)))
