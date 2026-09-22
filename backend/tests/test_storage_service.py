"""
Tests for the submission upload policy.

Uploaded files are untrusted input, so the rules that matter here are the
extension allowlist, the size cap, and the fact that no part of the object key
comes from the client. None of that needs a live S3 bucket.
"""

import io
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import storage_service
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
class _StubApplicant:
    """Minimal stand-in so the route can be exercised without a database."""
    id = APPLICANT_ID
    submission = None


class _StubQuery:
    def filter(self, *a, **k):
        return self

    def first(self):
        return _StubApplicant()


class _StubSession:
    def query(self, *a, **k):
        return _StubQuery()


@pytest.fixture
def stub_db():
    """
    Override get_db so these tests never open a socket.

    DATABASE_URL points at a hosted Postgres that is unreachable from a
    developer machine or CI without network access; letting a test fall through
    to it turns a fast unit test into a multi-minute timeout.
    """
    from app.db import get_db

    app.dependency_overrides[get_db] = lambda: _StubSession()
    yield
    app.dependency_overrides.pop(get_db, None)


def test_upload_returns_503_when_storage_unconfigured(monkeypatch, stub_db):
    """A developer without AWS credentials gets a clear, actionable error."""
    monkeypatch.setattr(storage_service, "is_configured", lambda: False)
    response = client.post(
        f"/api/submit/{APPLICANT_ID}/upload",
        files={"file": ("cv.pdf", b"data", "application/pdf")},
    )
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]


def test_upload_rejects_bad_extension_through_the_endpoint(monkeypatch, stub_db):
    """The allowlist must be enforced at the HTTP boundary, not only in the service."""
    monkeypatch.setattr(storage_service, "is_configured", lambda: True)
    monkeypatch.setattr(
        storage_service, "_client", lambda: pytest.fail("must not reach storage")
    )
    response = client.post(
        f"/api/submit/{APPLICANT_ID}/upload",
        files={"file": ("payload.exe", b"data", "application/octet-stream")},
    )
    assert response.status_code == 400


def test_upload_rejects_oversized_file_through_the_endpoint(monkeypatch, stub_db):
    monkeypatch.setattr(storage_service, "is_configured", lambda: True)
    response = client.post(
        f"/api/submit/{APPLICANT_ID}/upload",
        files={"file": ("big.pdf", b"x" * (MAX_UPLOAD_BYTES + 1), "application/pdf")},
    )
    assert response.status_code == 413


def test_submission_file_link_requires_authentication():
    response = client.get(f"/api/applicants/{APPLICANT_ID}/submission-file")
    assert response.status_code == 401
