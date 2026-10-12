"""
RECRUIT.AI — Sign in with Google and GitHub

The provider half of the OAuth flow: building the authorisation URL,
exchanging the code, and reading back a verified email address. What to do
with that address (sign in, accept an invitation, or start a new
organisation) is the router's job.

Only a *verified* address is ever returned. An account is found by email, so
trusting an unverified one would let anyone who can create a provider
account with your address sign in as you.

The short-lived values the flow needs between redirects (state, PKCE
verifier, a pending signup) travel in signed, httpOnly cookies rather than
server-side storage. Each carries a `purpose` claim, so none can be replayed
as a session token or as one of the others.
"""

import base64
import hashlib
import logging
import secrets
from dataclasses import dataclass
from datetime import timedelta
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException

from app.config import get_settings
from app.services.auth_service import create_access_token, decode_token

settings = get_settings()
log = logging.getLogger("recruit.oauth")

PROVIDERS = ("google", "github")
HTTP_TIMEOUT_SECONDS = 10

# Long enough to pick an account at the provider; short enough that a state
# cookie left behind by an abandoned attempt is useless soon after.
FLOW_TTL = timedelta(minutes=10)
# Time to name the organisation after coming back from the provider.
SIGNUP_TTL = timedelta(minutes=30)

FLOW_PURPOSE = "oauth_flow"
SIGNUP_PURPOSE = "oauth_signup"


class OAuthError(Exception):
    """The provider refused, or answered with something unusable."""


@dataclass
class Identity:
    provider: str
    email: str
    name: str


def is_enabled(provider: str) -> bool:
    if provider == "google":
        return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)
    if provider == "github":
        return bool(settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET)
    return False


def enabled_providers() -> list[str]:
    return [p for p in PROVIDERS if is_enabled(p)]


def redirect_uri(provider: str) -> str:
    return f"{settings.FRONTEND_URL.rstrip('/')}/api/auth/oauth/{provider}/callback"


# ── Signed cookie values ──
def sign(purpose: str, ttl: timedelta, **claims) -> str:
    return create_access_token({"purpose": purpose, **claims}, expires_delta=ttl)


def verify(token: str | None, purpose: str) -> dict | None:
    """The claims, or None if the value is missing, expired, forged or for another purpose."""
    if not token:
        return None
    try:
        claims = decode_token(token)
    except HTTPException:
        return None
    return claims if claims.get("purpose") == purpose else None


# ── Authorisation ──
def new_flow(provider: str) -> tuple[str, str]:
    """
    Start a sign-in. Returns (authorisation URL, signed flow cookie value).

    `state` ties the callback to the browser that started it, which is what
    stops an attacker completing a sign-in into their own account in your
    browser. Google also gets PKCE, so a leaked code cannot be redeemed.
    """
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(48)

    if provider == "google":
        challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
            .rstrip(b"=")
            .decode()
        )
        url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": redirect_uri(provider),
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "prompt": "select_account",
        })
    else:
        url = "https://github.com/login/oauth/authorize?" + urlencode({
            "client_id": settings.GITHUB_CLIENT_ID,
            "redirect_uri": redirect_uri(provider),
            "scope": "read:user user:email",
            "state": state,
            "allow_signup": "true",
        })

    cookie = sign(FLOW_PURPOSE, FLOW_TTL, provider=provider, state=state, verifier=verifier)
    return url, cookie


# ── Code exchange ──
async def fetch_identity(provider: str, code: str, verifier: str) -> Identity:
    """Exchange the code and return the verified identity. Raises OAuthError."""
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            if provider == "google":
                return await _google(client, code, verifier)
            return await _github(client, code)
    except httpx.HTTPError as exc:
        # The message can echo request details; only the type is logged.
        log.warning("oauth provider request failed", extra={
            "provider": provider, "error": type(exc).__name__,
        })
        raise OAuthError("provider request failed") from exc


async def _google(client: httpx.AsyncClient, code: str, verifier: str) -> Identity:
    token = await client.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri("google"),
            "grant_type": "authorization_code",
            "code_verifier": verifier,
        },
    )
    access_token = token.json().get("access_token") if token.is_success else None
    if not access_token:
        raise OAuthError("google refused the code")

    info = await client.get(
        "https://openidconnect.googleapis.com/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if not info.is_success:
        raise OAuthError("google userinfo failed")
    profile = info.json()

    email = (profile.get("email") or "").strip().lower()
    if not email or profile.get("email_verified") is not True:
        raise OAuthError("no verified email")
    return Identity("google", email, profile.get("name") or "")


async def _github(client: httpx.AsyncClient, code: str) -> Identity:
    token = await client.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "code": code,
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "redirect_uri": redirect_uri("github"),
        },
    )
    # GitHub answers 200 with an "error" field when it refuses a code.
    access_token = token.json().get("access_token") if token.is_success else None
    if not access_token:
        raise OAuthError("github refused the code")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
    }
    user = await client.get("https://api.github.com/user", headers=headers)
    emails = await client.get("https://api.github.com/user/emails", headers=headers)
    if not user.is_success or not emails.is_success:
        raise OAuthError("github profile failed")

    # The profile email is whatever the user chose to make public, verified
    # or not; only the emails endpoint says which addresses GitHub verified.
    primary = next(
        (e for e in emails.json() if e.get("primary") and e.get("verified")), None
    )
    if not primary or not primary.get("email"):
        raise OAuthError("no verified email")

    profile = user.json()
    return Identity(
        "github",
        primary["email"].strip().lower(),
        profile.get("name") or profile.get("login") or "",
    )
