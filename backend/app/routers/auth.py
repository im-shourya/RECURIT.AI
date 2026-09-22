"""
RECRUIT.AI — Auth Router
POST /auth/register          — Organisation + owner registration
POST /auth/login             — Returns JWT
GET  /auth/me                — Current org profile
PATCH /auth/me               — Update org profile
POST /auth/change-password   — Change the signed-in user's password
POST /auth/forgot-password   — Request a reset link
POST /auth/reset-password    — Consume a reset token, set a new password
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.config import get_settings
from app.models.documents import (
    AuditAction,
    Organisation,
    PasswordResetToken,
    User,
    UserRole,
)
from app.models.schemas import (
    ForgotPasswordRequest,
    OrgLoginRequest,
    OrgProfileResponse,
    OrgProfileUpdate,
    OrgRegisterRequest,
    PasswordChangeRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.services import audit
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
@router.get("/me", response_model=OrgProfileResponse)
async def get_me(org: Organisation = Depends(get_current_org)):
    return org


@router.patch("/me", response_model=OrgProfileResponse)
async def update_me(
    body: OrgProfileUpdate,
    org: Organisation = Depends(get_current_org),
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
    return org


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
