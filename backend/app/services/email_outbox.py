"""
RECRUIT.AI — Email Outbox

Durability layer in front of the Resend transport.

Every outbound message is written to `email_outbox` before delivery is
attempted, so the *intent* to send survives a process restart even when the
send itself does not. A sweeper retries anything still pending.

This is not a full job queue — there is one sweeper per process and no
distributed lock — but it closes the failure that actually mattered: an email
silently vanishing with no record it was ever attempted. For a result
notification or a password-reset link that is the worst possible outcome.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from app.config import get_settings
from app.models.documents import Applicant, EmailOutbox, EmailStatus

settings = get_settings()
log = logging.getLogger("recruit.outbox")

# Give up after this many tries and leave the row as `failed` for inspection,
# rather than retrying a permanently bad address forever.
MAX_ATTEMPTS = 5


async def enqueue(
    *,
    to_email: str,
    subject: str,
    html: str,
    text: str,
    outbox_id: Optional[UUID] = None,
) -> EmailOutbox:
    """
    Record an outbound email as pending.

    Written immediately and independently of anything else in flight: the
    decision it notifies the candidate about has usually already been saved,
    so the record of intent must not depend on the rest of the request.

    `outbox_id` is supplied when an applicant's email log already names this
    message, so the outcome can be written back to that entry.
    """
    row = EmailOutbox(
        to_email=to_email, subject=subject, html=html, text=text,
        status=EmailStatus.PENDING,
    )
    if outbox_id is not None:
        row.id = outbox_id
    await row.insert()
    return row


async def _record_outcome_on_applicant(row: EmailOutbox) -> None:
    """
    Copy a delivery outcome onto the applicant email-log entry that names it.

    Only mail to candidates has such an entry; for anything else this matches
    nothing. A targeted positional update rather than load-and-save, so it
    cannot overwrite a concurrent change to the rest of the applicant.
    """
    try:
        await Applicant.find({"email_logs.outbox_id": row.id}).update(
            {
                "$set": {
                    "email_logs.$.status": row.status.value,
                    "email_logs.$.sent_at": row.sent_at,
                    "email_logs.$.provider_message_id": row.provider_message_id,
                }
            }
        )
    except Exception as exc:
        log.error(
            "could not record delivery on the email log",
            extra={"outbox_id": str(row.id), "error": type(exc).__name__},
        )


async def deliver(row_id) -> bool:
    """Attempt one delivery and record the outcome. Never raises."""
    # Imported here rather than at module scope: email_service imports this
    # module, so a top-level import would be circular.
    from app.services.email_service import send_email

    try:
        row = await EmailOutbox.get(row_id)
        if row is None or row.status == EmailStatus.SENT:
            return True

        row.attempts += 1
        result = await send_email(
            to_email=row.to_email, subject=row.subject, html=row.html, text=row.text
        )

        if result == "failed":
            row.last_error = "transport reported failure"
            if row.attempts >= MAX_ATTEMPTS:
                row.status = EmailStatus.FAILED
                log.error(
                    "giving up on email after repeated failures",
                    extra={"outbox_id": str(row.id), "attempts": row.attempts},
                )
            await row.save()
            if row.status == EmailStatus.FAILED:
                await _record_outcome_on_applicant(row)
            return False

        # "skipped-no-config" counts as delivered: there is no provider to
        # retry against, so leaving it pending would accumulate documents
        # forever on a machine that simply has no email configured.
        row.status = EmailStatus.SENT
        row.sent_at = datetime.now(timezone.utc)
        row.provider_message_id = result
        await row.save()
        await _record_outcome_on_applicant(row)
        return True
    except Exception as exc:
        log.error("outbox delivery raised", extra={"error": type(exc).__name__})
        return False


async def sweep_once(limit: int = 20) -> int:
    """Retry pending documents. Returns how many were attempted."""
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(
            seconds=settings.OUTBOX_RETRY_DELAY_SECONDS
        )
        rows = (
            await EmailOutbox.find(
                EmailOutbox.status == EmailStatus.PENDING,
                EmailOutbox.attempts < MAX_ATTEMPTS,
                EmailOutbox.created_at < cutoff,
            )
            .sort(EmailOutbox.created_at)
            .limit(limit)
            .to_list()
        )
        ids = [r.id for r in rows]
    except Exception as exc:
        log.error("outbox sweep query failed", extra={"error": type(exc).__name__})
        return 0

    for row_id in ids:
        await deliver(row_id)

    if ids:
        log.info("outbox sweep completed", extra={"attempted": len(ids)})
    return len(ids)


async def run_sweeper(stop: asyncio.Event) -> None:
    """
    Periodically retry pending mail until asked to stop.

    Failures are swallowed and the loop continues: a sweeper that dies on one
    bad row would silently stop retrying everything behind it.
    """
    while not stop.is_set():
        try:
            await sweep_once()
        except Exception as exc:
            log.error("outbox sweeper iteration failed", extra={"error": type(exc).__name__})

        try:
            await asyncio.wait_for(
                stop.wait(), timeout=settings.OUTBOX_SWEEP_INTERVAL_SECONDS
            )
        except asyncio.TimeoutError:
            continue
