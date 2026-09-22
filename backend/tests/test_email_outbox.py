"""
Tests for durable email delivery.

The failure being closed here is specific: an email handed to BackgroundTasks
vanished if the process restarted before it sent, leaving no record it had
ever been attempted.
"""

import asyncio
import uuid

import pytest

from app.config import get_settings
from app.models.documents import EmailOutbox, EmailStatus
from app.services import email_outbox

settings = get_settings()


# ──────────────────────────────────────────────
# Model
# ──────────────────────────────────────────────
def test_outbox_stores_everything_needed_to_resend():
    """
    A retry happens in a later process, so the document must carry the
    rendered message — re-rendering needs context that is gone by then.
    """
    fields = set(EmailOutbox.model_fields)
    assert {"to_email", "subject", "html", "text"} <= fields
    assert {"status", "attempts", "last_error", "sent_at"} <= fields


def test_status_is_indexed():
    """The sweeper scans by status; without an index it walks the whole collection."""
    declared = [
        index.document for index in EmailOutbox.Settings.indexes
        if hasattr(index, "document")
    ]
    assert any("status" in d["key"] for d in declared)


def test_pending_is_the_default_status():
    assert EmailOutbox.model_fields["status"].default is EmailStatus.PENDING


# ──────────────────────────────────────────────
# Delivery outcomes
#
# These now run against a real (in-process) database, so the row is written,
# read back and asserted rather than mocked through a fake session.
# ──────────────────────────────────────────────
async def _queued() -> EmailOutbox:
    return await email_outbox.enqueue(
        to_email="a@example.com", subject="s", html="<p>h</p>", text="t"
    )


async def test_enqueue_persists_the_message(db):
    """
    The row must land before delivery is attempted, so a crash between the two
    leaves something the sweeper can retry.
    """
    row = await _queued()

    stored = await EmailOutbox.get(row.id)
    assert stored is not None
    assert stored.status == EmailStatus.PENDING
    assert stored.subject == "s"
    # The rendered message is stored, not the context to re-render it: a retry
    # happens in a later process where that context is gone.
    assert stored.html == "<p>h</p>"


async def test_successful_send_marks_the_row_sent(db, monkeypatch):
    row = await _queued()

    async def _send(**_kwargs):
        return "msg_123"

    monkeypatch.setattr("app.services.email_service.send_email", _send)
    assert await email_outbox.deliver(row.id) is True

    stored = await EmailOutbox.get(row.id)
    assert stored.status == EmailStatus.SENT
    assert stored.provider_message_id == "msg_123"
    assert stored.sent_at is not None


async def test_failure_leaves_the_row_pending_for_retry(db, monkeypatch):
    row = await _queued()

    async def _send(**_kwargs):
        return "failed"

    monkeypatch.setattr("app.services.email_service.send_email", _send)
    assert await email_outbox.deliver(row.id) is False

    stored = await EmailOutbox.get(row.id)
    assert stored.status == EmailStatus.PENDING, "must stay retryable"
    assert stored.attempts == 1


async def test_gives_up_after_the_attempt_cap(db, monkeypatch):
    """
    A permanently bad address must not be retried forever; the row is left as
    failed so it can be inspected rather than silently dropped.
    """
    row = await _queued()
    row.attempts = email_outbox.MAX_ATTEMPTS - 1
    await row.save()

    async def _send(**_kwargs):
        return "failed"

    monkeypatch.setattr("app.services.email_service.send_email", _send)
    await email_outbox.deliver(row.id)

    assert (await EmailOutbox.get(row.id)).status == EmailStatus.FAILED


async def test_unconfigured_transport_counts_as_delivered(db, monkeypatch):
    """
    With no provider there is nothing to retry against, so leaving these
    pending would accumulate documents forever on a machine without email.
    """
    row = await _queued()

    async def _send(**_kwargs):
        return "skipped-no-config"

    monkeypatch.setattr("app.services.email_service.send_email", _send)
    await email_outbox.deliver(row.id)

    assert (await EmailOutbox.get(row.id)).status == EmailStatus.SENT


async def test_already_sent_row_is_not_sent_again(db, monkeypatch):
    """Guards against the sweeper racing an inline delivery."""
    row = await _queued()
    row.status = EmailStatus.SENT
    await row.save()

    async def _send(**_kwargs):
        raise AssertionError("must not resend an already-sent email")

    monkeypatch.setattr("app.services.email_service.send_email", _send)
    assert await email_outbox.deliver(row.id) is True


async def test_delivery_never_raises(db, monkeypatch):
    """
    Callers are background tasks reporting on work that already happened; an
    exception here must not surface as a failure of that work.
    """
    row = await _queued()

    async def _send(**_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("app.services.email_service.send_email", _send)
    assert await email_outbox.deliver(row.id) is False


async def test_missing_row_is_treated_as_done(db):
    """A row deleted between sweep and delivery must not crash the sweeper."""
    import uuid

    assert await email_outbox.deliver(uuid.uuid4()) is True


# ──────────────────────────────────────────────
# Sweeper
# ──────────────────────────────────────────────
async def test_sweep_retries_only_old_pending_rows(db, monkeypatch):
    """
    enqueue() is followed immediately by an inline delivery, so the sweeper
    must not pick the same row up before that has had a chance to finish.
    """
    from datetime import datetime, timedelta, timezone

    fresh = await _queued()

    stale = await _queued()
    stale.created_at = datetime.now(timezone.utc) - timedelta(
        seconds=settings.OUTBOX_RETRY_DELAY_SECONDS + 60
    )
    await stale.save()

    attempted = []

    async def _send(**kwargs):
        attempted.append(kwargs["subject"])
        return "msg"

    monkeypatch.setattr("app.services.email_service.send_email", _send)
    count = await email_outbox.sweep_once()

    assert count == 1, "only the stale row should be retried"
    assert (await EmailOutbox.get(stale.id)).status == EmailStatus.SENT
    assert (await EmailOutbox.get(fresh.id)).status == EmailStatus.PENDING


async def test_sweep_survives_a_broken_query(monkeypatch):
    """A sweeper that dies on one bad query stops retrying everything behind it."""
    async def _boom(*a, **k):
        raise RuntimeError("db gone")

    monkeypatch.setattr(EmailOutbox, "find", _boom)
    assert await email_outbox.sweep_once() == 0


async def test_sweeper_stops_promptly_when_asked(monkeypatch):
    """Shutdown must not block on the sweep interval."""
    monkeypatch.setattr(settings, "OUTBOX_SWEEP_INTERVAL_SECONDS", 3600)

    async def _noop(*a, **k):
        return 0

    monkeypatch.setattr(email_outbox, "sweep_once", _noop)

    stop = asyncio.Event()
    task = asyncio.create_task(email_outbox.run_sweeper(stop))
    await asyncio.sleep(0)
    stop.set()
    await asyncio.wait_for(task, timeout=2)


def test_retry_delay_is_configured():
    assert settings.OUTBOX_RETRY_DELAY_SECONDS > 0
