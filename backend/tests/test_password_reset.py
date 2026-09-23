"""
Tests for the password reset flow.

The properties that matter here are cryptographic and behavioural rather than
DB-bound: tokens must be unguessable, stored only as hashes, and the request
endpoint must not reveal whether an account exists.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.models.schemas import ForgotPasswordRequest, ResetPasswordRequest
from app.services.auth_service import generate_reset_token, hash_reset_token

client = TestClient(app)


# ──────────────────────────────────────────────
# Token generation
# ──────────────────────────────────────────────
def test_tokens_are_unique():
    tokens = {generate_reset_token()[0] for _ in range(200)}
    assert len(tokens) == 200, "reset tokens must never repeat"


def test_token_has_enough_entropy():
    """32 random bytes, urlsafe-encoded, is not brute-forceable."""
    plaintext, _ = generate_reset_token()
    assert len(plaintext) >= 32


def test_only_the_hash_is_suitable_for_storage():
    """
    The stored value must not be the token itself. If these were equal, a
    database leak would hand over working reset links for every account.
    """
    plaintext, stored = generate_reset_token()
    assert stored != plaintext
    assert len(stored) == 64  # sha256 hex


def test_hashing_is_deterministic():
    """Lookup is by hash equality, so the same token must always hash alike."""
    plaintext, stored = generate_reset_token()
    assert hash_reset_token(plaintext) == stored


def test_different_tokens_hash_differently():
    a, _ = generate_reset_token()
    b, _ = generate_reset_token()
    assert hash_reset_token(a) != hash_reset_token(b)


# ──────────────────────────────────────────────
# Request validation
# ──────────────────────────────────────────────
def test_forgot_password_requires_a_valid_email():
    with pytest.raises(ValidationError):
        ForgotPasswordRequest(email="not-an-email")


def test_reset_enforces_password_minimum_length():
    plaintext, _ = generate_reset_token()
    with pytest.raises(ValidationError):
        ResetPasswordRequest(token=plaintext, new_password="short")

    assert ResetPasswordRequest(token=plaintext, new_password="longenough1")


def test_reset_rejects_an_implausibly_short_token():
    """Blocks trivially short guesses before they ever reach a DB lookup."""
    with pytest.raises(ValidationError):
        ResetPasswordRequest(token="abc", new_password="longenough1")


# ──────────────────────────────────────────────
# Endpoint behaviour
# ──────────────────────────────────────────────
class _StubQuery:
    """Behaves like an org/token lookup that finds nothing."""

    def filter(self, *a, **k):
        return self

    def first(self):
        return None

    def update(self, *a, **k):
        return 0


class _StubSession:
    def query(self, *a, **k):
        return _StubQuery()

    def add(self, *a, **k):
        pass

    def commit(self):
        pass


@pytest.fixture
def stub_db():
    """Keeps these tests off the network; DATABASE_URL is a hosted Postgres."""
    from app.db import get_db

    app.dependency_overrides[get_db] = lambda: _StubSession()
    yield
    app.dependency_overrides.pop(get_db, None)


def test_forgot_password_does_not_leak_whether_an_account_exists(stub_db):
    """
    An unknown address must produce exactly the same 204 as a known one.
    Anything else turns this endpoint into an account enumeration oracle.
    """
    response = client.post(
        "/api/auth/forgot-password", json={"email": "nobody@example.com"}
    )
    assert response.status_code == 204
    assert response.content == b""


def test_reset_with_unknown_token_is_rejected(stub_db):
    plaintext, _ = generate_reset_token()
    response = client.post(
        "/api/auth/reset-password",
        json={"token": plaintext, "new_password": "a-new-password"},
    )
    assert response.status_code == 400
    # The same wording is used for unknown, expired and already-used tokens so
    # the response cannot be used to distinguish them.
    assert response.json()["detail"] == "This reset link is invalid or has expired"


def test_reset_endpoints_are_public(stub_db):
    """Both must work without a token — the user cannot sign in."""
    for path, payload in [
        ("/api/auth/forgot-password", {"email": "a@b.com"}),
        (
            "/api/auth/reset-password",
            {"token": generate_reset_token()[0], "new_password": "a-new-password"},
        ),
    ]:
        assert client.post(path, json=payload).status_code != 401


def test_routes_are_registered():
    paths = app.openapi()["paths"]
    assert "/api/auth/forgot-password" in paths
    assert "/api/auth/reset-password" in paths
