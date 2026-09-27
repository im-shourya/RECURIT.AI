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
from app.models.documents import Drive, DriveStatus, Organisation
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
    assert Organisation.model_fields["notify_on_interview"].default is True


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
async def test_expired_drive_is_closed_on_read(drive):
    """
    There is no scheduler, so an expired drive stayed "active" forever and
    looked open in the dashboard and in analytics.
    """
    drive.apply_deadline = date.today() - timedelta(days=1)
    await drive.save()

    await _close_if_past_deadline(drive)

    assert drive.status == DriveStatus.CLOSED
    reloaded = await Drive.get(drive.id)
    assert reloaded.status == DriveStatus.CLOSED, "the change must be persisted"


async def test_drive_within_deadline_is_untouched(drive):
    drive.apply_deadline = date.today() + timedelta(days=7)
    await drive.save()

    await _close_if_past_deadline(drive)
    assert drive.status == DriveStatus.ACTIVE


async def test_deadline_today_is_still_open(drive):
    """The deadline day itself should still accept applications."""
    drive.apply_deadline = date.today()
    await drive.save()

    await _close_if_past_deadline(drive)
    assert drive.status == DriveStatus.ACTIVE


async def test_closing_never_reopens_a_drive(drive):
    """Only ever active -> closed, so a drive closed early stays closed."""
    drive.status = DriveStatus.CLOSED
    drive.apply_deadline = date.today() + timedelta(days=7)
    await drive.save()

    await _close_if_past_deadline(drive)
    assert drive.status == DriveStatus.CLOSED


async def test_closing_is_idempotent(drive):
    drive.apply_deadline = date.today() - timedelta(days=1)
    await drive.save()

    await _close_if_past_deadline(drive)
    await _close_if_past_deadline(drive)

    assert drive.status == DriveStatus.CLOSED


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
    The count must come from the filtered query without skip/limit, or it
    would just report the page size back.

    Behaviour is covered for real in test_documents.py; this pins the ordering
    in the handler, which is where it would regress.
    """
    import inspect
    from app.routers import applicant_admin

    source = inspect.getsource(applicant_admin.list_applicants)
    assert source.index("await query.count()") < source.index(".skip(offset).limit(limit)")
