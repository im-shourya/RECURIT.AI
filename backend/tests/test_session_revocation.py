"""
Tests for session revocation (#58).

Changing or resetting a password must sign out every token issued before it.
Someone resetting because they believe an attacker has their session gets no
protection otherwise.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.models.documents import PasswordResetToken
from app.models.schemas import PasswordChangeRequest, ResetPasswordRequest
from app.routers.auth import change_password, reset_password
from app.services.auth_service import (
    create_access_token,
    decode_token,
    generate_reset_token,
    get_current_user,
    issue_token,
)


@pytest.mark.asyncio
async def test_issued_token_carries_the_token_version(owner):
    assert decode_token(issue_token(owner))["ver"] == owner.token_version


@pytest.mark.asyncio
async def test_a_fresh_token_resolves(owner):
    user = await get_current_user(issue_token(owner))
    assert user.id == owner.id


@pytest.mark.asyncio
async def test_token_without_a_version_still_works_until_the_first_revocation(owner):
    """Tokens minted before this change carry no "ver"; deploying must not sign everyone out."""
    legacy = create_access_token(data={"sub": str(owner.id)})
    assert (await get_current_user(legacy)).id == owner.id


@pytest.mark.asyncio
async def test_changing_the_password_revokes_existing_tokens(owner):
    stolen = issue_token(owner)

    response = await change_password(
        PasswordChangeRequest(current_password="correct-horse", new_password="battery-staple"),
        user=owner,
    )

    with pytest.raises(HTTPException) as exc:
        await get_current_user(stolen)
    assert exc.value.status_code == 401

    # The tab the change was made from gets a working token back.
    assert (await get_current_user(response.access_token)).id == owner.id


@pytest.mark.asyncio
async def test_changing_the_password_revokes_legacy_tokens_too(owner):
    legacy = create_access_token(data={"sub": str(owner.id)})

    await change_password(
        PasswordChangeRequest(current_password="correct-horse", new_password="battery-staple"),
        user=owner,
    )

    with pytest.raises(HTTPException):
        await get_current_user(legacy)


@pytest.mark.asyncio
async def test_a_failed_password_change_revokes_nothing(owner):
    token = issue_token(owner)

    with pytest.raises(HTTPException):
        await change_password(
            PasswordChangeRequest(current_password="wrong-password", new_password="battery-staple"),
            user=owner,
        )

    assert (await get_current_user(token)).id == owner.id


@pytest.mark.asyncio
async def test_resetting_the_password_revokes_existing_tokens(owner):
    stolen = issue_token(owner)
    plaintext, token_hash = generate_reset_token()
    await PasswordResetToken(
        org_id=owner.org_id,
        user_id=owner.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    ).insert()

    await reset_password(ResetPasswordRequest(token=plaintext, new_password="battery-staple"))

    with pytest.raises(HTTPException) as exc:
        await get_current_user(stolen)
    assert exc.value.status_code == 401
