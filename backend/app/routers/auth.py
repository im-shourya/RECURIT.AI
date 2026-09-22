"""
RECRUIT.AI — Auth Router
POST /auth/register          — Organisation registration
POST /auth/login             — Returns JWT
GET  /auth/me                — Current org profile
PATCH /auth/me               — Update org profile
POST /auth/change-password   — Change the organisation password
POST /auth/forgot-password   — Request a reset link
POST /auth/reset-password    — Consume a reset token, set a new password
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models.database import Organisation, PasswordResetToken, AuditAction, User, UserRole
from app.models.schemas import (
    OrgRegisterRequest,
    OrgLoginRequest,
    TokenResponse,
    OrgProfileResponse,
    OrgProfileUpdate,
    PasswordChangeRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_org,
    get_current_user,
    generate_reset_token,
    hash_reset_token,
)
from app.services.email_service import send_password_reset_email
from app.services.rate_limit import RateLimit
from app.services import audit

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
def register(body: OrgRegisterRequest, db: Session = Depends(get_db)):
    # Check if email already exists
    # Checked against users, not organisations: the user table holds the
    # unique constraint that actually governs sign-in.
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # The organisation still carries an email for display and contact, but the
    # credential now lives on the owner user created alongside it.
    org = Organisation(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
        description=body.description,
        domain_tags=body.domain_tags,
        logo_url=body.logo_url,
    )
    db.add(org)
    db.flush()

    owner = User(
        org_id=org.id,
        name=body.name,
        email=body.email,
        password_hash=org.password_hash,
        role=UserRole.OWNER,
    )
    db.add(owner)
    db.commit()
    db.refresh(owner)

    token = create_access_token(data={"sub": str(owner.id)})
    return TokenResponse(access_token=token)


# ──────────────────────────────────────────────
# LOGIN
# ──────────────────────────────────────────────
@router.post(
    "/login",
    response_model=TokenResponse,
    # Sign-in is the brute-force target; keep this tight.
    dependencies=[Depends(RateLimit("login", limit=10, window_seconds=300))],
)
def login(body: OrgLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()

    # An invited member who has not set a password yet has no hash. Treated
    # exactly like a wrong password so the response cannot be used to work out
    # which addresses have pending invitations.
    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="This account is disabled")

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=token)


# ──────────────────────────────────────────────
# ME (current profile)
# ──────────────────────────────────────────────
@router.get("/me", response_model=OrgProfileResponse)
def get_me(org: Organisation = Depends(get_current_org)):
    return org


@router.patch("/me", response_model=OrgProfileResponse)
def update_me(
    body: OrgProfileUpdate,
    org: Organisation = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    if body.name is not None:
        org.name = body.name
    if body.description is not None:
        org.description = body.description
    if body.domain_tags is not None:
        org.domain_tags = body.domain_tags
    if body.logo_url is not None:
        org.logo_url = body.logo_url

    db.commit()
    db.refresh(org)
    return org


# ──────────────────────────────────────────────
# CHANGE PASSWORD
# ──────────────────────────────────────────────
@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    body: PasswordChangeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Change the calling organisation's password.

    Requires the current password even though the caller is already
    authenticated, so a leaked or borrowed token alone cannot lock the owner
    out of their account.
    """
    if not verify_password(body.current_password, user.password_hash or ""):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password must differ from the current password"
        )

    user.password_hash = hash_password(body.new_password)
    audit.record(
        db, org_id=user.org_id, action=AuditAction.PASSWORD_CHANGED,
        entity_type="user", entity_id=user.id, entity_label=user.email,
    )
    db.commit()

    # Returns 204. Existing JWTs stay valid: tokens carry no password state and
    # there is no revocation list yet, which is noted in the PR.
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
def forgot_password(
    body: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Start a password reset.

    Always returns 204, whether or not the email is registered. Reporting
    "no such account" here would turn this endpoint into an account
    enumeration oracle for anyone probing addresses.
    """
    user = db.query(User).filter(User.email == body.email).first()

    if user:
        org_id = user.org_id
        # Invalidate any outstanding tokens so only the newest link works.
        now = datetime.now(timezone.utc)
        (
            db.query(PasswordResetToken)
            .filter(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.used_at.is_(None),
            )
            .update({PasswordResetToken.used_at: now}, synchronize_session=False)
        )

        plaintext, token_hash = generate_reset_token()
        db.add(
            PasswordResetToken(
                org_id=org_id,
                user_id=user.id,
                token_hash=token_hash,
                expires_at=now + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_TTL_MINUTES),
            )
        )
        db.commit()

        reset_link = f"{settings.FRONTEND_URL}/auth/reset-password?token={plaintext}"
        background_tasks.add_task(
            send_password_reset_email,
            to_email=user.email,
            to_name=user.name or user.email,
            reset_link=reset_link,
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
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Consume a reset token and set a new password.

    The token is looked up by hash, so the plaintext is never compared against
    anything stored. Expired, already-used and unknown tokens are all reported
    identically, so this cannot be used to probe which tokens exist.
    """
    record = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == hash_reset_token(body.token))
        .first()
    )

    now = datetime.now(timezone.utc)
    if not record or record.used_at is not None or record.expires_at <= now:
        raise HTTPException(
            status_code=400, detail="This reset link is invalid or has expired"
        )

    user = db.query(User).filter(User.id == record.user_id).first()
    if not user:
        raise HTTPException(
            status_code=400, detail="This reset link is invalid or has expired"
        )

    user.password_hash = hash_password(body.new_password)
    # Setting a password is also how an invited member activates, so this is
    # the point at which the invitation is accepted.
    user.is_active = True
    # Burn the token before returning, so a replayed link cannot set the
    # password a second time.
    record.used_at = now
    db.commit()

    return None
