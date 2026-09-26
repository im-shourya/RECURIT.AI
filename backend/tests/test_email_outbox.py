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
from app.models.database import EmailOutbox, EmailStatus
from app.services import email_outbox

settings = get_settings()


# ──────────────────────────────────────────────
# Model
# ──────────────────────────────────────────────
def test_outbox_stores_everything_needed_to_resend():
    """
    A retry happens in a later process, so the row must carry the rendered
    message — re-rendering it would need the original context, which is gone.
    """
    columns = set(EmailOutbox.__table__.c.keys())
    assert {"to_email", "subject", "html", "text"} <= columns
    assert {"status", "attempts", "last_error", "sent_at"} <= columns


def test_status_is_indexed():
    """The sweeper scans by status; without an index it walks the whole table."""
    assert EmailOutbox.__table__.c.status.index is True


def test_pending_is_the_default_status():
    assert EmailOutbox.__table__.c.status.default.arg is EmailStatus.PENDING


# ──────────────────────────────────────────────
# Delivery outcomes
# ──────────────────────────────────────────────
class _Row:
    def __init__(self, status=EmailStatus.PENDING, attempts=0):
        self.id = uuid.uuid4()
        self.to_email = "a@b.test"
        self.subject = "s"
        self.html = "<p>h</p>"
        self.text = "t"
        self.status = status
        self.attempts = attempts
        self.last_error = ""
        self.provider_message_id = ""
        self.sent_at = None


class _Session:
    def __init__(self, row):
        self.row = row
        self.committed = False

    def get(self, _model, _id):
        return self.row

    def commit(self):
        self.committed = True

    def rollback(self):
        pass

    def close(self):
        pass


def _run(coro):
    return asyncio.run(coro)


def test_successful_send_marks_the_row_sent(monkeypatch):
    row = _Row()
    monkeypatch.setattr(email_outbox, "SessionLocal", lambda: _Session(row))

    async def _send(**_kwargs):
        return "msg_123"

    monkeypatch.setattr("app.services.email_service.send_email", _send)
    assert _run(email_outbox.deliver(row.id)) is True
    assert row.status == EmailStatus.SENT
    assert row.provider_message_id == "msg_123"
    assert row.sent_at is not None


def test_failure_leaves_the_row_pending_for_retry(monkeypatch):
    row = _Row()
    monkeypatch.setattr(email_outbox, "SessionLocal", lambda: _Session(row))

    async def _send(**_kwargs):
        return "failed"

    monkeypatch.setattr("app.services.email_service.send_email", _send)
    assert _run(email_outbox.deliver(row.id)) is False
    assert row.status == EmailStatus.PENDING, "must stay retryable"
    assert row.attempts == 1


def test_gives_up_after_the_attempt_cap(monkeypatch):
    """
    A permanently bad address must not be retried forever; the row is left as
    failed so it can be inspected rather than silently dropped.
    """
    row = _Row(attempts=email_outbox.MAX_ATTEMPTS - 1)
    monkeypatch.setattr(email_outbox, "SessionLocal", lambda: _Session(row))

    async def _send(**_kwargs):
        return "failed"

    monkeypatch.setattr("app.services.email_service.send_email", _send)
    _run(email_outbox.deliver(row.id))
    assert row.status == EmailStatus.FAILED


def test_unconfigured_transport_counts_as_delivered(monkeypatch):
    """
    With no provider there is nothing to retry against, so leaving these
    pending would accumulate rows forever on a machine without email set up.
    """
    row = _Row()
    monkeypatch.setattr(email_outbox, "SessionLocal", lambda: _Session(row))

    async def _send(**_kwargs):
        return "skipped-no-config"

    monkeypatch.setattr("app.services.email_service.send_email", _send)
    _run(email_outbox.deliver(row.id))
    assert row.status == EmailStatus.SENT


def test_already_sent_row_is_not_sent_again(monkeypatch):
    """Guards against the sweeper racing an inline delivery."""
    row = _Row(status=EmailStatus.SENT)
    monkeypatch.setattr(email_outbox, "SessionLocal", lambda: _Session(row))

    async def _send(**_kwargs):
        raise AssertionError("must not resend an already-sent email")

    monkeypatch.setattr("app.services.email_service.send_email", _send)
    assert _run(email_outbox.deliver(row.id)) is True


def test_delivery_never_raises(monkeypatch):
    """
    Callers are background tasks reporting on work that already committed; an
    exception here must not surface as a failure of that work.
    """
    row = _Row()
    monkeypatch.setattr(email_outbox, "SessionLocal", lambda: _Session(row))

    async def _send(**_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("app.services.email_service.send_email", _send)
    assert _run(email_outbox.deliver(row.id)) is False


# ──────────────────────────────────────────────
# Sweeper
# ──────────────────────────────────────────────
def test_sweep_survives_a_broken_query(monkeypatch):
    """A sweeper that dies on one bad query stops retrying everything behind it."""
    class _Broken:
        def scalars(self, *a, **k):
            raise RuntimeError("db gone")

        def close(self):
            pass

    monkeypatch.setattr(email_outbox, "SessionLocal", lambda: _Broken())
    assert _run(email_outbox.sweep_once()) == 0


def test_sweeper_stops_promptly_when_asked(monkeypatch):
    """Shutdown must not block on the sweep interval."""
    monkeypatch.setattr(settings, "OUTBOX_SWEEP_INTERVAL_SECONDS", 3600)

    async def _noop(*a, **k):
        return 0

    monkeypatch.setattr(email_outbox, "sweep_once", _noop)

    async def _drive():
        stop = asyncio.Event()
        task = asyncio.create_task(email_outbox.run_sweeper(stop))
        await asyncio.sleep(0)
        stop.set()
        await asyncio.wait_for(task, timeout=2)

    _run(_drive())


def test_retry_delay_avoids_duplicating_the_inline_attempt():
    """
    enqueue() is followed immediately by an inline delivery, so the sweeper
    must not pick the same row up before that has had a chance to finish.
    """
    assert settings.OUTBOX_RETRY_DELAY_SECONDS > 0
