"""
RECRUIT.AI — Authentication Service
Handles password hashing and JWT token creation / verification.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models.database import Organisation, ROLE_RANK, User, UserRole

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ── Password utilities ──
def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ── JWT utilities ──
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── FastAPI dependencies ──
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Resolve the signed-in user.

    Tokens now carry a user id. A token issued before users existed carried an
    organisation id, which will not resolve here — those holders must sign in
    again. Tokens are short-lived, so the window is small, and silently
    accepting an organisation id as a user id would mean a token minted under
    the old model kept full access with no role attached.
    """
    payload = decode_token(token)
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Session is no longer valid")

    if not user.is_active:
        # Deactivation must take effect on the next request, not when the
        # token happens to expire.
        raise HTTPException(status_code=401, detail="This account is disabled")

    return user


def get_current_org(user: User = Depends(get_current_user)) -> Organisation:
    """
    The organisation the signed-in user belongs to.

    Kept with its original name and return type so every existing route that
    depends on it is unchanged by the move to per-user accounts. Routes that
    need to know *who* acted depend on get_current_user instead.
    """
    return user.organisation


def require_role(minimum: UserRole):
    """
    Dependency factory enforcing a minimum role.

        dependencies=[Depends(require_role(UserRole.ADMIN))]

    Compared by rank rather than equality, so OWNER satisfies an ADMIN
    requirement without every call site listing both.
    """

    def _guard(user: User = Depends(get_current_user)) -> User:
        if ROLE_RANK[user.role] < ROLE_RANK[minimum]:
            raise HTTPException(
                status_code=403,
                detail=f"This action requires the {minimum.value} role",
            )
        return user

    return _guard


# ── Password reset tokens ──
def generate_reset_token() -> tuple[str, str]:
    """
    Mint a reset token.

    Returns (plaintext, sha256_hash). Only the hash is ever persisted; the
    plaintext exists solely inside the emailed link, so a database leak cannot
    be replayed to seize accounts.
    """
    plaintext = secrets.token_urlsafe(32)
    return plaintext, hash_reset_token(plaintext)


def hash_reset_token(plaintext: str) -> str:
    """
    Hash a reset token for storage and lookup.

    SHA-256 rather than bcrypt on purpose: the token is 32 random bytes, so it
    has no guessable structure to slow down, and lookup must be an indexed
    equality match rather than a scan over every row.
    """
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()
