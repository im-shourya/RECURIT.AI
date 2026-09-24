"""
Tests for the submission upload policy.

Uploaded files are untrusted input, so the rules that matter here are the
extension allowlist, the size cap, and the fact that no part of the object key
comes from the client. None of that needs a live S3 bucket.
"""

import io
import uuid

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.main import app
from app.models.documents import Applicant, Interview
from app.services import storage_service
from app.services.auth_service import get_current_org
from app.services.storage_service import (
    MAX_UPLOAD_BYTES,
    UnsupportedFileType,
    UploadTooLarge,
    build_key,
    extension_of,
    presigned_get_url,
    upload_submission_file,
)

client = TestClient(app)
APPLICANT_ID = uuid.UUID("3f7c1a52-1d44-4a5e-9c3b-9f2a7e6d5c41")
ORG_ID = uuid.UUID("b21c9e70-5d3a-4f18-8a6c-2e4d7b1f9a03")


# ──────────────────────────────────────────────
# Extension allowlist
# ──────────────────────────────────────────────
@pytest.mark.parametrize("name", ["cv.pdf", "Project.ZIP", "notes.md", "shot.JPEG"])
def test_allowlisted_extensions_are_accepted(name):
    assert extension_of(name) in storage_service.ALLOWED_EXTENSIONS


@pytest.mark.parametrize(
    "name",
    [
        "payload.exe",
        "script.sh",
        "shell.php",
        "resume.pdf.exe",      # double extension: only the final suffix counts
        "noextension",
        "",
        ".bashrc",
        "evil.svg",            # SVG can carry script; deliberately excluded
    ],
)
def test_dangerous_or_unknown_extensions_are_rejected(name):
    with pytest.raises(UnsupportedFileType):
        extension_of(name)


# ──────────────────────────────────────────────
# Object key construction
# ──────────────────────────────────────────────
def test_key_is_built_only_from_server_controlled_values():
    key = build_key(APPLICANT_ID, ".pdf")
    assert key.startswith(f"submissions/{APPLICANT_ID}/")
    assert key.endswith(".pdf")
    assert ".." not in key


def test_two_uploads_never_collide():
    a = build_key(APPLICANT_ID, ".pdf")
    b = build_key(APPLICANT_ID, ".pdf")
    assert a != b, "each upload must get a unique key or files overwrite each other"


@pytest.mark.parametrize(
    "filename",
    ["../../../etc/passwd.pdf", "..\\..\\windows\\system.pdf", "a/b/c.pdf"],
)
def test_traversal_attempts_cannot_reach_the_key(filename):
    """
    A traversing filename must never influence the key. The extension is the
    only thing taken from the client, and the rest is a UUID.
    """
    key = build_key(APPLICANT_ID, extension_of(filename))
    assert ".." not in key
    assert key.count("/") == 2, "key must stay at submissions/<applicant>/<file>"
    assert "etc" not in key and "windows" not in key


# ──────────────────────────────────────────────
# Size cap
# ──────────────────────────────────────────────
def test_oversized_upload_is_rejected(monkeypatch):
    """The cap must be enforced from the stream, not a client-supplied header."""
    monkeypatch.setattr(storage_service, "is_configured", lambda: True)
    oversized = io.BytesIO(b"x" * (MAX_UPLOAD_BYTES + 1))

    with pytest.raises(UploadTooLarge):
        upload_submission_file(APPLICANT_ID, "big.pdf", oversized)


def test_empty_upload_is_rejected(monkeypatch):
    monkeypatch.setattr(storage_service, "is_configured", lambda: True)
    with pytest.raises(ValueError):
        upload_submission_file(APPLICANT_ID, "empty.pdf", io.BytesIO(b""))


def test_extension_is_checked_before_any_network_call(monkeypatch):
    """A bad extension must fail without ever reaching the storage backend."""
    monkeypatch.setattr(storage_service, "is_configured", lambda: True)

    def explode():
        raise AssertionError("storage client must not be constructed")

    monkeypatch.setattr(storage_service, "_client", explode)

    with pytest.raises(UnsupportedFileType):
        upload_submission_file(APPLICANT_ID, "payload.exe", io.BytesIO(b"data"))


# ──────────────────────────────────────────────
# Presigned reads
# ──────────────────────────────────────────────
def test_presigning_refuses_values_that_are_not_our_keys(monkeypatch):
    """
    Guards against signing an arbitrary attacker-supplied key. Legacy rows hold
    plain URLs, which must not be signed as if they were bucket objects.
    """
    monkeypatch.setattr(storage_service, "is_configured", lambda: True)
    assert presigned_get_url("https://example.com/whatever.pdf") is None
    assert presigned_get_url("../../secrets") is None
    assert presigned_get_url("") is None


def test_presigning_returns_none_when_storage_unconfigured(monkeypatch):
    monkeypatch.setattr(storage_service, "is_configured", lambda: False)
    assert presigned_get_url("submissions/x/y.pdf") is None


# ──────────────────────────────────────────────
# Endpoint behaviour
# ──────────────────────────────────────────────
# These use the real applicant fixture, so the route resolves its capability
# token against an actual document rather than a stubbed session.
async def test_upload_returns_503_when_storage_unconfigured(applicant, monkeypatch):
    """A developer without AWS credentials gets a clear, actionable error."""
    monkeypatch.setattr(storage_service, "is_configured", lambda: False)
    response = client.post(
        f"/api/submit/{applicant.submit_token}/upload",
        files={"file": ("cv.pdf", b"data", "application/pdf")},
    )
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]


async def test_upload_rejects_bad_extension_through_the_endpoint(applicant, monkeypatch):
    """The allowlist must be enforced at the HTTP boundary, not only in the service."""
    monkeypatch.setattr(storage_service, "is_configured", lambda: True)
    monkeypatch.setattr(
        storage_service, "_client", lambda: pytest.fail("must not reach storage")
    )
    response = client.post(
        f"/api/submit/{applicant.submit_token}/upload",
        files={"file": ("payload.exe", b"data", "application/octet-stream")},
    )
    assert response.status_code == 400


async def test_upload_rejects_oversized_file_through_the_endpoint(applicant, monkeypatch):
    monkeypatch.setattr(storage_service, "is_configured", lambda: True)
    response = client.post(
        f"/api/submit/{applicant.submit_token}/upload",
        files={"file": ("big.pdf", b"x" * (MAX_UPLOAD_BYTES + 1), "application/pdf")},
    )
    assert response.status_code == 413


async def test_upload_rejects_an_unknown_token(db, monkeypatch):
    """
    The route is keyed on an unguessable token; an unknown one must not reveal
    whether it exists.
    """
    monkeypatch.setattr(storage_service, "is_configured", lambda: True)
    response = client.post(
        "/api/submit/not-a-real-token/upload",
        files={"file": ("cv.pdf", b"data", "application/pdf")},
    )
    assert response.status_code == 404


def test_submission_file_link_requires_authentication():
    import uuid

    response = client.get(f"/api/applicants/{uuid.uuid4()}/submission-file")
    assert response.status_code == 401


# ──────────────────────────────────────────────
# Interview recording playback link
#
# recording_url holds a server-generated object key, and recordings are stored
# private. These cover turning that key back into something a recruiter can
# actually play, and the scoping that stops it signing another organisation's
# video.
# ──────────────────────────────────────────────
def test_recording_file_link_requires_authentication():
    response = client.get(f"/api/applicants/{uuid.uuid4()}/recording-file")
    assert response.status_code == 401


@pytest_asyncio.fixture
async def as_org(org):
    """Sign in as the fixture organisation for the duration of one test."""
    app.dependency_overrides[get_current_org] = lambda: org
    yield org
    app.dependency_overrides.clear()


async def test_recording_link_is_signed_from_the_stored_key(
    as_org, applicant, monkeypatch
):
    applicant.interview = Interview(
        token="interview-token", recording_url="recordings/abc/def.webm"
    )
    await applicant.save()

    monkeypatch.setattr(storage_service, "is_configured", lambda: True)
    monkeypatch.setattr(
        storage_service,
        "presigned_get_url",
        lambda key, **kw: f"https://signed.test/{key}",
    )

    response = client.get(f"/api/applicants/{applicant.id}/recording-file")

    assert response.status_code == 200
    body = response.json()
    assert body["url"] == "https://signed.test/recordings/abc/def.webm"
    assert body["expires_in_seconds"] == storage_service.PRESIGNED_URL_TTL_SECONDS


async def test_recording_link_is_404_when_nothing_was_recorded(as_org, applicant):
    """
    The common case today: the interview page never uploads, so recording_url
    is empty. That must read as "no recording", not as a server error.
    """
    applicant.interview = Interview(token="interview-token", recording_url="")
    await applicant.save()

    response = client.get(f"/api/applicants/{applicant.id}/recording-file")
    assert response.status_code == 404


async def test_recording_link_is_404_for_another_organisations_applicant(
    as_org, other_org, db
):
    """Scoping is the point: a signed link to a rival's candidate video is the
    worst possible leak from this endpoint."""
    theirs = Applicant(
        drive_id=uuid.uuid4(),
        org_id=other_org.id,
        name="Someone Else",
        email="else@example.com",
        interview=Interview(token="other-token", recording_url="recordings/x/y.webm"),
    )
    await theirs.insert()

    response = client.get(f"/api/applicants/{theirs.id}/recording-file")
    assert response.status_code == 404


async def test_legacy_plain_url_recording_is_passed_through(as_org, applicant, monkeypatch):
    """
    /end used to accept recording_url from the client and store it verbatim.
    Those rows hold a URL rather than a key, so presigning returns None and the
    stored value is handed back unsigned with no expiry.
    """
    applicant.interview = Interview(
        token="interview-token", recording_url="https://legacy.test/clip.webm"
    )
    await applicant.save()

    monkeypatch.setattr(storage_service, "presigned_get_url", lambda key, **kw: None)

    response = client.get(f"/api/applicants/{applicant.id}/recording-file")

    assert response.status_code == 200
    assert response.json() == {
        "url": "https://legacy.test/clip.webm",
        "expires_in_seconds": 0,
    }


async def test_recording_link_is_503_when_storage_unconfigured(
    as_org, applicant, monkeypatch
):
    applicant.interview = Interview(
        token="interview-token", recording_url="recordings/abc/def.webm"
    )
    await applicant.save()

    monkeypatch.setattr(storage_service, "presigned_get_url", lambda key, **kw: None)

    response = client.get(f"/api/applicants/{applicant.id}/recording-file")
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]


# ──────────────────────────────────────────────
# Organisation logos
#
# The logo renders in the dashboard avatar and at the top of the public apply
# page, so it needs an upload path and a way to resolve a stored key back into
# something a browser can load.
# ──────────────────────────────────────────────
@pytest.mark.parametrize("name", ["mark.png", "Logo.SVG", "brand.webp", "photo.JPEG"])
def test_logo_extensions_are_accepted(name, monkeypatch):
    monkeypatch.setattr(storage_service, "is_configured", lambda: True)
    captured = {}

    class _FakeClient:
        def put_object(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(storage_service, "_client", lambda: _FakeClient())

    key = storage_service.upload_org_logo(ORG_ID, name, io.BytesIO(b"image-bytes"))

    assert key.startswith(f"logos/{ORG_ID}/")
    # The content type comes from our table, never from the client.
    assert captured["ContentType"] in storage_service.LOGO_EXTENSIONS.values()
    assert captured["ACL"] == "private"


@pytest.mark.parametrize("name", ["resume.pdf", "archive.zip", "clip.webm", "script.js"])
def test_logo_upload_rejects_non_images(name, monkeypatch):
    """The submission allowlist is wider; a logo must not accept a .pdf or a .zip."""
    monkeypatch.setattr(storage_service, "is_configured", lambda: True)
    monkeypatch.setattr(
        storage_service, "_client", lambda: pytest.fail("must not reach storage")
    )
    with pytest.raises(UnsupportedFileType):
        storage_service.upload_org_logo(ORG_ID, name, io.BytesIO(b"x"))


def test_logo_upload_enforces_its_own_smaller_cap(monkeypatch):
    monkeypatch.setattr(storage_service, "is_configured", lambda: True)
    oversized = io.BytesIO(b"x" * (storage_service.MAX_LOGO_BYTES + 1))
    with pytest.raises(UploadTooLarge):
        storage_service.upload_org_logo(ORG_ID, "mark.png", oversized)


def test_logo_cap_is_tighter_than_the_submission_cap():
    """A logo is decoration on a public page, not a deliverable."""
    assert storage_service.MAX_LOGO_BYTES < MAX_UPLOAD_BYTES


def test_logo_key_is_built_only_from_server_values(monkeypatch):
    monkeypatch.setattr(storage_service, "is_configured", lambda: True)
    monkeypatch.setattr(storage_service, "_client", lambda: type("C", (), {"put_object": lambda self, **k: None})())

    key = storage_service.upload_org_logo(
        ORG_ID, "../../../etc/passwd.png", io.BytesIO(b"x")
    )
    assert ".." not in key
    assert "passwd" not in key
    assert key.startswith(f"logos/{ORG_ID}/")


def test_resolve_logo_url_signs_a_stored_key(monkeypatch):
    monkeypatch.setattr(
        storage_service, "presigned_get_url", lambda key, **kw: f"https://signed.test/{key}"
    )
    assert (
        storage_service.resolve_logo_url("logos/x/y.png")
        == "https://signed.test/logos/x/y.png"
    )


def test_resolve_logo_url_passes_a_supplied_url_through():
    """logo_url predates uploads and may hold a URL the organisation supplied."""
    assert (
        storage_service.resolve_logo_url("https://cdn.example.com/logo.png")
        == "https://cdn.example.com/logo.png"
    )
    assert storage_service.resolve_logo_url("") == ""


def test_resolve_logo_url_never_raises(monkeypatch):
    """
    A blank avatar is an acceptable outcome; failing the profile request or the
    public apply page over a logo is not.
    """
    def _boom(key, **kw):
        raise storage_service.StorageError("bucket on fire")

    monkeypatch.setattr(storage_service, "presigned_get_url", _boom)
    assert storage_service.resolve_logo_url("logos/x/y.png") == ""


def test_logo_keys_are_signable_and_deletable():
    """
    Both guards are prefix-based, so adding a new prefix means updating them —
    otherwise an uploaded logo can never be displayed or cleaned up.
    """
    assert "logos/" in storage_service.MANAGED_PREFIXES
    # Refuses anything outside the managed prefixes, as before.
    assert storage_service.delete_object("../../secrets") is False
    assert storage_service.delete_object("https://evil.test/x.png") is False
