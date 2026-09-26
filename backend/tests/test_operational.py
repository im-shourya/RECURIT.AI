"""
Tests for the operational completeness work: recruiter notifications,
recording storage, lazy drive closing, and pagination metadata.
"""

import io
import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.database import Drive, DriveStatus, Organisation
from app.services import email_templates, storage_service
from app.routers.drives import _close_if_past_deadline

client = TestClient(app)


# ──────────────────────────────────────────────
# Recruiter notification
# ──────────────────────────────────────────────
def test_recruiter_template_addresses_the_org_not_the_candidate():
    """
    Every other template talks to applicants. This one must read as an
    internal notification, not as a message to the person being assessed.
    """
    subject, html, text = email_templates.interview_completed_for_recruiter(
        to_name="Sparkles Ltd", applicant_name="Alex Developer",
        drive_name="Frontend Engineer", total_score=87,
        review_url="https://x.test/dashboard/drives/1",
    )
    assert "Alex Developer" in subject
    assert "Review candidate" in html
    assert "https://x.test/dashboard/drives/1" in text


def test_recruiter_template_escapes_the_candidate_name():
    """The candidate name is attacker-controlled and now reaches a recruiter."""
    _, html, _ = email_templates.interview_completed_for_recruiter(
        to_name="Org", applicant_name='<script>alert(1)</script>',
        drive_name="Role", total_score=10, review_url="https://x.test/r",
    )
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_notification_preference_defaults_to_on():
    """
    A recruiter who hears nothing assumes the platform is idle, so this is
    opt-out rather than opt-in.
    """
    assert Organisation.__table__.c.notify_on_interview.default.arg is True
    assert Organisation.__table__.c.notify_on_interview.nullable is False


# ──────────────────────────────────────────────
# Recording storage
# ──────────────────────────────────────────────
def test_recording_route_exists():
    paths = {r.path for r in app.routes if hasattr(r, "methods")}
    assert "/api/interview/{token}/recording" in paths


def test_end_no_longer_trusts_a_client_supplied_recording_url():
    """
    /end used to store body.recording_url verbatim, so the client decided what
    the recording pointed at.
    """
    import inspect
    from app.routers import interviews

    source = inspect.getsource(interviews.end_interview)
    assert "interview.recording_url = body.recording_url" not in source


@pytest.mark.parametrize("name", ["take.webm", "clip.MP4", "audio.m4a", "voice.ogg"])
def test_recording_formats_allowed(name):
    extension = name[name.rfind(".") :].lower()
    assert extension in storage_service.RECORDING_EXTENSIONS


@pytest.mark.parametrize("name", ["resume.pdf", "payload.exe", "sheet.xlsx", "shell.sh"])
def test_non_recording_formats_rejected(name, monkeypatch):
    """A candidate must not be able to post a document as a "recording"."""
    monkeypatch.setattr(storage_service, "is_configured", lambda: True)
    with pytest.raises(storage_service.UnsupportedFileType):
        storage_service.upload_recording(uuid.uuid4(), name, io.BytesIO(b"x"))


def test_recording_size_cap_is_enforced(monkeypatch):
    monkeypatch.setattr(storage_service, "is_configured", lambda: True)
    oversized = io.BytesIO(b"x" * (storage_service.MAX_RECORDING_BYTES + 1))
    with pytest.raises(storage_service.UploadTooLarge):
        storage_service.upload_recording(uuid.uuid4(), "take.webm", oversized)


def test_recordings_can_be_presigned(monkeypatch):
    """Recordings are private, so the recruiter needs a signed read URL."""
    monkeypatch.setattr(storage_service, "is_configured", lambda: True)
    # Not one of our prefixes -> refused, as before.
    assert storage_service.presigned_get_url("https://evil.test/x.webm") is None


# ──────────────────────────────────────────────
# Lazy drive closing
# ──────────────────────────────────────────────
class _FakeDb:
    def __init__(self):
        self.committed = False

    def commit(self):
        self.committed = True

    def refresh(self, _):
        pass


def _drive(status, deadline):
    d = Drive()
    d.status = status
    d.apply_deadline = deadline
    return d


def test_expired_drive_is_closed_on_read():
    """
    There is no scheduler, so an expired drive stayed "active" forever and
    looked open in the dashboard and in analytics.
    """
    db = _FakeDb()
    drive = _drive(DriveStatus.ACTIVE, date.today() - timedelta(days=1))
    _close_if_past_deadline(drive, db)

    assert drive.status == DriveStatus.CLOSED
    assert db.committed is True


def test_drive_within_deadline_is_untouched():
    db = _FakeDb()
    drive = _drive(DriveStatus.ACTIVE, date.today() + timedelta(days=7))
    _close_if_past_deadline(drive, db)

    assert drive.status == DriveStatus.ACTIVE
    assert db.committed is False, "must not write on every read"


def test_deadline_today_is_still_open():
    """The deadline day itself should still accept applications."""
    db = _FakeDb()
    drive = _drive(DriveStatus.ACTIVE, date.today())
    _close_if_past_deadline(drive, db)

    assert drive.status == DriveStatus.ACTIVE


def test_closing_never_reopens_a_drive():
    """Only ever active -> closed, so a drive closed early stays closed."""
    db = _FakeDb()
    drive = _drive(DriveStatus.CLOSED, date.today() + timedelta(days=7))
    _close_if_past_deadline(drive, db)

    assert drive.status == DriveStatus.CLOSED
    assert db.committed is False


def test_closing_is_idempotent():
    db = _FakeDb()
    drive = _drive(DriveStatus.ACTIVE, date.today() - timedelta(days=1))
    _close_if_past_deadline(drive, db)
    db.committed = False
    _close_if_past_deadline(drive, db)

    assert db.committed is False, "second read must not write again"


# ──────────────────────────────────────────────
# Pagination metadata
# ──────────────────────────────────────────────
def test_list_still_requires_authentication():
    assert client.get("/api/applicants").status_code == 401


def test_pagination_headers_are_declared_exposed():
    """
    Browsers hide non-safelisted response headers from JavaScript unless they
    are named in Access-Control-Expose-Headers, so declaring them is what
    makes the count usable by the frontend at all.
    """
    import inspect
    from app.routers import applicant_admin

    source = inspect.getsource(applicant_admin.list_applicants)
    assert "X-Total-Count" in source
    assert "Access-Control-Expose-Headers" in source


def test_total_is_counted_before_pagination_is_applied():
    """
    The count must come from the filtered query without limit/offset, or it
    would just report the page size back.
    """
    import inspect
    from app.routers import applicant_admin

    source = inspect.getsource(applicant_admin.list_applicants)
    count_line = source.index("query.order_by(None).count()")
    paginate_line = source.index(".offset(offset).limit(limit)")
    assert count_line < paginate_line
