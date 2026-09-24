"""
RECRUIT.AI — Auth Router
POST /auth/register          — Organisation + owner registration
POST /auth/login             — Returns JWT
GET  /auth/me                — Current org profile
PATCH /auth/me               — Update org profile
POST /auth/me/logo           — Upload the organisation logo
DELETE /auth/me/logo         — Remove the organisation logo
POST /auth/change-password   — Change the signed-in user's password
POST /auth/forgot-password   — Request a reset link
POST /auth/reset-password    — Consume a reset token, set a new password
"""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import (
    APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status,
)

from app.config import get_settings
from app.models.documents import (
    AuditAction,
    Organisation,
    PasswordResetToken,
    User,
    UserRole,
)
from app.services.auth_service import require_role
from app.models.schemas import (
    AccountDeleteRequest,
    ForgotPasswordRequest,
    OrgLoginRequest,
    OrgProfileResponse,
    OrgProfileUpdate,
    OrgRegisterRequest,
    PasswordChangeRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.services import audit, cascade, storage_service
from app.services.auth_service import (
    create_access_token,
    generate_reset_token,
    get_current_org,
    get_current_user,
    hash_password,
    hash_reset_token,
    verify_password,
)
from app.services.email_service import send_password_reset_email
from app.services.rate_limit import RateLimit

settings = get_settings()
log = logging.getLogger("recruit.auth")
router = APIRouter(prefix="/auth", tags=["Authentication"])


# ──────────────────────────────────────────────
# REGISTER
# ──────────────────────────────────────────────
@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimit("register", limit=5, window_seconds=3600))],
)
async def register(body: OrgRegisterRequest):
    # Checked against users: that is where the unique index governing sign-in
    # lives. The index is the real guard; this check is for the error message.
    if await User.find_one(User.email == body.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    org = Organisation(
        name=body.name,
        email=body.email,
        description=body.description,
        domain_tags=body.domain_tags,
        logo_url=body.logo_url,
    )
    await org.insert()

    owner = User(
        org_id=org.id,
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
        role=UserRole.OWNER,
    )
    await owner.insert()

    return TokenResponse(access_token=create_access_token(data={"sub": str(owner.id)}))


# ──────────────────────────────────────────────
# LOGIN
# ──────────────────────────────────────────────
@router.post(
    "/login",
    response_model=TokenResponse,
    # Sign-in is the brute-force target; keep this tight.
    dependencies=[Depends(RateLimit("login", limit=10, window_seconds=300))],
)
async def login(body: OrgLoginRequest):
    user = await User.find_one(User.email == body.email)

    # An invited member who has not set a password has no hash. Treated
    # exactly like a wrong password, so the response cannot be used to work
    # out which addresses have an invitation pending.
    if not user or not user.password_hash or not verify_password(
        body.password, user.password_hash
    ):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="This account is disabled")

    user.last_login_at = datetime.now(timezone.utc)
    await user.save()

    return TokenResponse(access_token=create_access_token(data={"sub": str(user.id)}))


# ──────────────────────────────────────────────
# PROFILE
# ──────────────────────────────────────────────
def _profile(org: Organisation, user: User) -> OrgProfileResponse:
    """The organisation, plus who is looking at it."""
    return OrgProfileResponse(
        id=org.id,
        name=org.name,
        email=org.email,
        description=org.description,
        domain_tags=org.domain_tags,
        # An uploaded logo is a private object key, so it is signed for display
        # here rather than handed over raw. A directly supplied URL passes
        # through untouched.
        logo_url=storage_service.resolve_logo_url(org.logo_url),
        created_at=org.created_at,
        user_id=user.id,
        user_name=user.name,
        user_email=user.email,
        role=user.role.value,
    )


@router.get("/me", response_model=OrgProfileResponse)
async def get_me(
    org: Organisation = Depends(get_current_org),
    user: User = Depends(get_current_user),
):
    return _profile(org, user)


@router.patch("/me", response_model=OrgProfileResponse)
async def update_me(
    body: OrgProfileUpdate,
    org: Organisation = Depends(get_current_org),
    user: User = Depends(get_current_user),
):
    if body.name is not None:
        org.name = body.name
    if body.description is not None:
        org.description = body.description
    if body.domain_tags is not None:
        org.domain_tags = body.domain_tags
    if body.logo_url is not None:
        org.logo_url = body.logo_url

    await org.save()
    return _profile(org, user)


# ──────────────────────────────────────────────
# LOGO
# ──────────────────────────────────────────────
@router.post(
    "/me/logo",
    response_model=OrgProfileResponse,
    # The logo appears at the top of every public apply page, so replacing it
    # is a change to how the organisation presents itself to candidates.
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def upload_logo(
    file: UploadFile = File(...),
    org: Organisation = Depends(get_current_org),
    user: User = Depends(get_current_user),
):
    """
    Replace the organisation's logo.

    There was no upload path at any layer before this: `logo_url` could only
    be set by sending a URL string to PATCH /auth/me, so the settings page's
    "Upload new" button had nothing to call.
    """
    if not storage_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Logo uploads are not available: object storage is not configured",
        )

    try:
        key = storage_service.upload_org_logo(
            org_id=org.id, filename=file.filename or "", stream=file.file
        )
    except storage_service.UnsupportedFileType as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except storage_service.UploadTooLarge as exc:
        raise HTTPException(status_code=413, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except storage_service.StorageError as exc:
        # Not surfaced verbatim: it can carry bucket names and credential detail.
        log.error("logo upload failed", extra={"org_id": str(org.id), "error": str(exc)})
        raise HTTPException(status_code=502, detail="Upload failed, please try again")

    previous = org.logo_url
    org.logo_url = key
    await org.save()

    # After the document is saved: a storage error here must not lose the new
    # logo, and an orphaned object is cheaper than a broken avatar.
    _discard_old_logo(previous)

    return _profile(org, user)


@router.delete(
    "/me/logo",
    response_model=OrgProfileResponse,
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def remove_logo(
    org: Organisation = Depends(get_current_org),
    user: User = Depends(get_current_user),
):
    """Clear the logo and remove the stored object, if we own one."""
    previous = org.logo_url
    org.logo_url = ""
    await org.save()

    _discard_old_logo(previous)
    return _profile(org, user)


def _discard_old_logo(stored: str) -> None:
    """
    Best-effort cleanup of a replaced logo.

    Only ever deletes a key this service wrote — delete_object refuses
    anything outside its own prefixes, so a directly supplied URL is left
    alone. Never raises: losing the old object is not worth failing the
    request that already succeeded.
    """
    if not stored:
        return
    try:
        storage_service.delete_object(stored)
    except Exception as exc:
        log.error(
            "previous logo left behind in storage",
            extra={"key": stored, "error": type(exc).__name__},
        )


# ──────────────────────────────────────────────
# CHANGE PASSWORD
# ──────────────────────────────────────────────
@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: PasswordChangeRequest,
    user: User = Depends(get_current_user),
):
    """
    Requires the current password even though the caller is authenticated, so
    a leaked or borrowed token alone cannot lock the owner out.
    """
    if not verify_password(body.current_password, user.password_hash or ""):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password must differ from the current password"
        )

    user.password_hash = hash_password(body.new_password)
    await user.save()

    await audit.record(
        org_id=user.org_id,
        action=AuditAction.PASSWORD_CHANGED,
        entity_type="user",
        entity_id=user.id,
        entity_label=user.email,
    )

    # Existing JWTs stay valid: tokens carry no password state and there is no
    # revocation list yet.
    return None


# ──────────────────────────────────────────────
# FORGOT PASSWORD
# ──────────────────────────────────────────────
@router.post(
    "/forgot-password",
    status_code=status.HTTP_204_NO_CONTENT,
    # Each call sends mail to a third party, so this doubles as abuse control.
    dependencies=[Depends(RateLimit("forgot_password", limit=5, window_seconds=3600))],
)
async def forgot_password(body: ForgotPasswordRequest, background_tasks: BackgroundTasks):
    """
    Always returns 204, whether or not the email is registered. Reporting "no
    such account" would turn this into an enumeration oracle.
    """
    user = await User.find_one(User.email == body.email)

    if user:
        now = datetime.now(timezone.utc)

        # Invalidate outstanding tokens so only the newest link works.
        await PasswordResetToken.find(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at == None,  # noqa: E711 — Beanie needs ==
        ).set({PasswordResetToken.used_at: now})

        plaintext, token_hash = generate_reset_token()
        await PasswordResetToken(
            org_id=user.org_id,
            user_id=user.id,
            token_hash=token_hash,
            expires_at=now
            + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_TTL_MINUTES),
        ).insert()

        background_tasks.add_task(
            send_password_reset_email,
            to_email=user.email,
            to_name=user.name or user.email,
            reset_link=f"{settings.FRONTEND_URL}/auth/reset-password?token={plaintext}",
        )

    return None


# ──────────────────────────────────────────────
# RESET PASSWORD
# ──────────────────────────────────────────────
@router.post(
    "/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RateLimit("reset_password", limit=10, window_seconds=3600))],
)
async def reset_password(body: ResetPasswordRequest):
    """
    Looked up by hash, so the plaintext is never compared against anything
    stored. Unknown, expired and already-used tokens all report identically,
    so this cannot be used to probe token state.
    """
    record = await PasswordResetToken.find_one(
        PasswordResetToken.token_hash == hash_reset_token(body.token)
    )

    now = datetime.now(timezone.utc)
    invalid = HTTPException(
        status_code=400, detail="This reset link is invalid or has expired"
    )

    if not record or record.used_at is not None:
        raise invalid

    # Stored datetimes come back from MongoDB without a timezone, so compare
    # against a naive UTC value rather than crashing on the mismatch.
    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
        raise invalid

    user = await User.get(record.user_id) if record.user_id else None
    if not user:
        raise invalid

    user.password_hash = hash_password(body.new_password)
    # Setting a password is also how an invited member activates.
    user.is_active = True
    await user.save()

    # Burn the token before returning, so a replayed link cannot set the
    # password a second time.
    record.used_at = now
    await record.save()

    return None


# ──────────────────────────────────────────────
# DELETE ACCOUNT
# ──────────────────────────────────────────────
@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    body: AccountDeleteRequest,
    user: User = Depends(require_role(UserRole.OWNER)),
):
    """
    Permanently delete the organisation and everything under it.

    Owner only, and the password is required even though the caller is signed
    in: this erases every drive, candidate, transcript and audit entry, so a
    borrowed session should not be enough to trigger it.

    MongoDB has no cascading delete, so the removal runs through
    services/cascade.py. The audit log goes too — once the account is gone
    nobody is left with standing to read it, and keeping it would mean
    retaining records about candidates after the controller has been removed.
    """
    if not body.confirm:
        raise HTTPException(status_code=400, detail="Confirmation is required")

    if not verify_password(body.current_password, user.password_hash or ""):
        raise HTTPException(status_code=400, detail="Password is incorrect")

    org = await Organisation.get(user.org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    await cascade.delete_organisation(org)
    return None
