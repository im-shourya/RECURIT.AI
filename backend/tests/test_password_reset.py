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
# ──────────────────────────────────────────────
# Endpoint behaviour
#
# These run against a real in-process database, so the enumeration guarantee
# is exercised rather than mocked: a registered address and an unknown one go
# down genuinely different code paths and must still look identical.
# ──────────────────────────────────────────────
async def test_forgot_password_looks_identical_for_known_and_unknown_addresses(owner):
    """
    An unknown address must produce exactly the same response as a registered
    one. Anything else turns this endpoint into an account enumeration oracle.
    """
    known = client.post(
        "/api/auth/forgot-password", json={"email": owner.email}
    )
    unknown = client.post(
        "/api/auth/forgot-password", json={"email": "nobody@example.com"}
    )

    assert known.status_code == unknown.status_code == 204
    assert known.content == unknown.content == b""


async def test_forgot_password_issues_a_token_for_a_real_user(owner):
    """The registered address must actually get a usable token behind it."""
    from app.models.documents import PasswordResetToken

    client.post("/api/auth/forgot-password", json={"email": owner.email})

    tokens = await PasswordResetToken.find(
        PasswordResetToken.user_id == owner.id
    ).to_list()
    assert len(tokens) == 1
    # Only the hash is stored; the plaintext exists solely in the email.
    assert len(tokens[0].token_hash) == 64


async def test_forgot_password_issues_nothing_for_an_unknown_address(db):
    from app.models.documents import PasswordResetToken

    client.post(
        "/api/auth/forgot-password", json={"email": "nobody@example.com"}
    )
    assert await PasswordResetToken.find_all().count() == 0


async def test_reset_with_unknown_token_is_rejected(db):
    plaintext, _ = generate_reset_token()
    response = client.post(
        "/api/auth/reset-password",
        json={"token": plaintext, "new_password": "a-new-password"},
    )
    assert response.status_code == 400
    # The same wording is used for unknown, expired and already-used tokens so
    # the response cannot be used to distinguish them.
    assert response.json()["detail"] == "This reset link is invalid or has expired"


async def test_reset_sets_the_password_and_burns_the_token(owner):
    """A replayed link must not be able to set the password a second time."""
    from app.models.documents import PasswordResetToken, User
    from app.services.auth_service import verify_password

    client.post("/api/auth/forgot-password", json={"email": owner.email})
    record = await PasswordResetToken.find_one(
        PasswordResetToken.user_id == owner.id
    )

    # Re-derive the plaintext the same way the endpoint verifies it: the stored
    # value is a hash, so drive this through a token we mint ourselves.
    plaintext, token_hash = generate_reset_token()
    record.token_hash = token_hash
    await record.save()

    first = client.post(
        "/api/auth/reset-password",
        json={"token": plaintext, "new_password": "brand-new-password"},
    )
    assert first.status_code == 204

    updated = await User.get(owner.id)
    assert verify_password("brand-new-password", updated.password_hash)

    replay = client.post(
        "/api/auth/reset-password",
        json={"token": plaintext, "new_password": "attacker-password"},
    )
    assert replay.status_code == 400
    still = await User.get(owner.id)
    assert verify_password("brand-new-password", still.password_hash)


async def test_expired_token_is_rejected(owner):
    from datetime import datetime, timedelta, timezone
    from app.models.documents import PasswordResetToken

    plaintext, token_hash = generate_reset_token()
    await PasswordResetToken(
        org_id=owner.org_id,
        user_id=owner.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    ).insert()

    response = client.post(
        "/api/auth/reset-password",
        json={"token": plaintext, "new_password": "a-new-password"},
    )
    assert response.status_code == 400


def test_routes_are_registered():
    paths = app.openapi()["paths"]
    assert "/api/auth/forgot-password" in paths
    assert "/api/auth/reset-password" in paths
