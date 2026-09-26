"""
RECRUIT.AI — Authentication Service
Password hashing, JWT creation/verification, and the request dependencies.

Ported from SQLAlchemy to Beanie. The dependencies keep their names and return
types so routes are unchanged by the move, but they are now async.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.config import get_settings
from app.models.documents import ROLE_RANK, Organisation, User, UserRole

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ── Password utilities ──
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    if not hashed:
        return False
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ── JWT utilities ──
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Password reset tokens ──
def generate_reset_token() -> tuple[str, str]:
    """
    Mint a reset token.

    Returns (plaintext, sha256_hash). Only the hash is persisted; the
    plaintext exists solely in the emailed link, so a database leak cannot be
    replayed to seize accounts.
    """
    plaintext = secrets.token_urlsafe(32)
    return plaintext, hash_reset_token(plaintext)


def hash_reset_token(plaintext: str) -> str:
    """
    SHA-256 rather than bcrypt: the token is 32 random bytes with no guessable
    structure to slow down, and lookup must be an indexed equality match.
    """
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


# ── Request dependencies ──
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Resolve the signed-in user.

    Tokens carry a user id. One minted before users existed carried an
    organisation id and will not resolve here, so those holders must sign in
    again — accepting it would mean an old token kept full access with no role
    attached.
    """
    payload = decode_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = await User.get(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Session is no longer valid")

    if not user.is_active:
        # Deactivation takes effect on the next request, not when the token
        # happens to expire.
        raise HTTPException(status_code=401, detail="This account is disabled")

    return user


async def get_current_org(user: User = Depends(get_current_user)) -> Organisation:
    """
    The organisation the signed-in user belongs to.

    Keeps its original name and return type so every route that depends on it
    is unchanged. Routes that need to know *who* acted use get_current_user.
    """
    org = await Organisation.get(user.org_id)
    if org is None:
        # The user document outlived its organisation, which the cascades are
        # meant to prevent. Refuse rather than serve a half-resolved session.
        raise HTTPException(status_code=401, detail="Organisation no longer exists")
    return org


def require_role(minimum: UserRole):
    """
    Dependency factory enforcing a minimum role.

    Compared by rank rather than equality, so OWNER satisfies an ADMIN
    requirement without every call site listing both.
    """

    async def _guard(user: User = Depends(get_current_user)) -> User:
        if ROLE_RANK[user.role] < ROLE_RANK[minimum]:
            raise HTTPException(
                status_code=403,
                detail=f"This action requires the {minimum.value} role",
            )
        return user

    return _guard
