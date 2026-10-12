"""
RECRUIT.AI — Sign in with Google / GitHub
GET  /auth/oauth/providers             — Which providers are configured
GET  /auth/oauth/{provider}/start      — Redirect to the provider
GET  /auth/oauth/{provider}/callback   — Provider redirects back here
GET  /auth/oauth/signup                — The identity waiting to become an organisation
POST /auth/oauth/signup                — Name the organisation and finish signing up

The browser reaches all of these through the frontend's /api rewrite, so the
session cookie set at the end is first-party, exactly as with a password
sign-in.

A verified provider email is treated the same as the address on an account:
  - accepted memberships → sign in to the most recently used one
  - only pending invitations → accept them and sign in; the provider has
    proved control of the address, which is all the invitation link proves
  - nothing → ask for an organisation name, then create it with this person
    as owner

Someone who signs up this way has no password. Their memberships get an
unusable random hash, so they count as accepted everywhere else, and a
password can be set later through "forgot password".
"""

import logging
import re
import secrets
from datetime import datetime, timezone
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.config import get_settings
from app.models.documents import Organisation, User, UserRole
from app.models.schemas import OrgProfileResponse
from app.routers.auth import _aware, _profile
from app.services import oauth
from app.services.auth_service import CSRF_HEADER, hash_password, set_session_cookie
from app.services.rate_limit import RateLimit

settings = get_settings()
log = logging.getLogger("recruit.oauth")
router = APIRouter(prefix="/auth/oauth", tags=["Authentication"])

FLOW_COOKIE = "recruit_oauth"
SIGNUP_COOKIE = "recruit_oauth_signup"
COOKIE_PATH = "/api/auth/oauth"


class ProvidersResponse(BaseModel):
    providers: list[str]


class PendingSignupResponse(BaseModel):
    provider: str
    email: str
    name: str


class OAuthSignupRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)


# ── Helpers ──
def _set_cookie(response: Response, key: str, value: str, max_age: int) -> None:
    response.set_cookie(
        key=key,
        value=value,
        max_age=max_age,
        path=COOKIE_PATH,
        httponly=True,
        secure=settings.session_cookie_secure,
        # Lax, not Strict: the callback is a top-level navigation from the
        # provider's site, and a Strict cookie would not be sent with it.
        samesite="lax",
    )


def _clear_cookie(response: Response, key: str) -> None:
    response.delete_cookie(
        key=key, path=COOKIE_PATH, httponly=True,
        secure=settings.session_cookie_secure, samesite="lax",
    )


def _frontend(path: str, **query) -> str:
    url = f"{settings.FRONTEND_URL.rstrip('/')}{path}"
    return f"{url}?{urlencode(query)}" if query else url


def _fail(code: str) -> RedirectResponse:
    """Back to the sign-in page with a reason the page can explain."""
    response = RedirectResponse(_frontend("/auth/login", oauth_error=code), status_code=302)
    _clear_cookie(response, FLOW_COOKIE)
    return response


def _known_provider(provider: str) -> str:
    if provider not in oauth.PROVIDERS:
        raise HTTPException(status_code=404, detail="Unknown sign-in provider")
    return provider


async def _memberships(email: str) -> list[User]:
    """
    Every membership for this address, ignoring case.

    Providers report addresses lower-cased, while an account may have been
    registered as "Name@Example.com"; an exact match would treat that person
    as new and start a second, empty organisation for them.
    """
    pattern = f"^{re.escape(email)}$"
    return await User.find({"email": {"$regex": pattern, "$options": "i"}}).to_list()


def _unusable_password() -> str:
    """A hash nobody knows the password to. Marks a membership as accepted."""
    return hash_password(secrets.token_urlsafe(32))


# ── Routes ──
@router.get(
    "/providers",
    response_model=ProvidersResponse,
    dependencies=[Depends(RateLimit("oauth_providers", limit=60, window_seconds=60))],
)
async def list_providers():
    """Lets the sign-in page offer only the buttons that will work."""
    return ProvidersResponse(providers=oauth.enabled_providers())


@router.get(
    "/{provider}/start",
    dependencies=[Depends(RateLimit("oauth_start", limit=30, window_seconds=300))],
)
async def start(provider: str):
    _known_provider(provider)
    if not oauth.is_enabled(provider):
        return _fail("unavailable")

    url, flow = oauth.new_flow(provider)
    response = RedirectResponse(url, status_code=302)
    _set_cookie(response, FLOW_COOKIE, flow, int(oauth.FLOW_TTL.total_seconds()))
    return response


@router.get(
    "/{provider}/callback",
    dependencies=[Depends(RateLimit("oauth_callback", limit=30, window_seconds=300))],
)
async def callback(
    provider: str,
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    _known_provider(provider)

    flow = oauth.verify(request.cookies.get(FLOW_COOKIE), oauth.FLOW_PURPOSE)
    if error:
        # The person pressed Cancel at the provider.
        return _fail("cancelled")
    if (
        not flow
        or flow.get("provider") != provider
        or not state
        or not secrets.compare_digest(state, flow.get("state", ""))
    ):
        return _fail("expired")
    if not code:
        return _fail("failed")

    try:
        identity = await oauth.fetch_identity(provider, code, flow.get("verifier", ""))
    except oauth.OAuthError as exc:
        return _fail("no_email" if "verified email" in str(exc) else "failed")

    memberships = await _memberships(identity.email)
    accepted = [m for m in memberships if m.password_hash is not None]

    if not accepted and memberships:
        # Only invitations. Accept them: the provider has just shown this
        # person controls the address the invitations were sent to.
        password_hash = _unusable_password()
        for invite in memberships:
            invite.password_hash = password_hash
            invite.is_active = True
            if not invite.name and identity.name:
                invite.name = identity.name
            await invite.save()
        accepted = memberships

    if accepted:
        return await _sign_in(accepted)

    # A new person. Hold the verified identity in a signed cookie while they
    # name their organisation.
    response = RedirectResponse(_frontend("/auth/oauth/complete"), status_code=302)
    _clear_cookie(response, FLOW_COOKIE)
    _set_cookie(
        response,
        SIGNUP_COOKIE,
        oauth.sign(
            oauth.SIGNUP_PURPOSE, oauth.SIGNUP_TTL,
            provider=identity.provider, email=identity.email, name=identity.name,
        ),
        int(oauth.SIGNUP_TTL.total_seconds()),
    )
    return response


async def _sign_in(memberships: list[User]) -> RedirectResponse:
    """Sign in to the most recently used active membership, as password sign-in does."""
    active = [m for m in memberships if m.is_active]
    if not active:
        return _fail("disabled")

    oldest = datetime.min.replace(tzinfo=timezone.utc)
    active.sort(key=lambda m: _aware(m.last_login_at) or oldest, reverse=True)
    for user in active:
        if await Organisation.get(user.org_id) is not None:
            break
    else:
        return _fail("failed")

    user.last_login_at = datetime.now(timezone.utc)
    await user.save()

    response = RedirectResponse(_frontend("/dashboard"), status_code=302)
    _clear_cookie(response, FLOW_COOKIE)
    set_session_cookie(response, user)
    return response


def _pending(request: Request) -> dict:
    claims = oauth.verify(request.cookies.get(SIGNUP_COOKIE), oauth.SIGNUP_PURPOSE)
    if not claims or not claims.get("email"):
        raise HTTPException(
            status_code=401, detail="Sign-up has expired. Please sign in again."
        )
    return claims


@router.get(
    "/signup",
    response_model=PendingSignupResponse,
    dependencies=[Depends(RateLimit("oauth_signup_read", limit=30, window_seconds=300))],
)
async def pending_signup(request: Request):
    """Who is about to create an organisation, so the page can say so."""
    claims = _pending(request)
    return PendingSignupResponse(
        provider=claims.get("provider", ""),
        email=claims["email"],
        name=claims.get("name", ""),
    )


@router.post(
    "/signup",
    response_model=OrgProfileResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimit("register", limit=5, window_seconds=3600))],
)
async def complete_signup(body: OAuthSignupRequest, request: Request, response: Response):
    """Create the organisation, with the provider's verified address as owner."""
    # The pending identity is an ambient cookie, so this needs the same CSRF
    # header every other cookie-authenticated write does.
    if not request.headers.get(CSRF_HEADER):
        raise HTTPException(status_code=403, detail="Missing CSRF header")

    claims = _pending(request)
    email = claims["email"]

    # Someone may have created an account for this address since the
    # callback. Creating a second, password-less owner beside it would split
    # their organisations across two credentials.
    if [m for m in await _memberships(email) if m.password_hash is not None]:
        _clear_cookie(response, SIGNUP_COOKIE)
        raise HTTPException(
            status_code=409,
            detail="This email already has an account. Sign in instead.",
        )

    org = Organisation(name=body.name, email=email)
    await org.insert()

    owner = User(
        org_id=org.id,
        name=claims.get("name") or body.name,
        email=email,
        password_hash=_unusable_password(),
        role=UserRole.OWNER,
        last_login_at=datetime.now(timezone.utc),
    )
    await owner.insert()

    _clear_cookie(response, SIGNUP_COOKIE)
    set_session_cookie(response, owner)
    return await _profile(org, owner)
