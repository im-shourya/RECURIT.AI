"""
Tests for signing in with Google and GitHub.

The provider calls themselves are stubbed: what is under test is what the
platform does with a verified identity, and that a callback cannot be
completed without the state this browser was given.
"""

from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.models.documents import Organisation, User, UserRole
from app.services import oauth, rate_limit
from app.services.auth_service import decode_token, verify_password

settings = get_settings()


@pytest.fixture(autouse=True)
def _configured(monkeypatch):
    rate_limit.reset()
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "google-id")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "google-secret")
    monkeypatch.setattr(settings, "GITHUB_CLIENT_ID", "")
    monkeypatch.setattr(settings, "GITHUB_CLIENT_SECRET", "")
    monkeypatch.setattr(settings, "FRONTEND_URL", "http://testserver")
    yield
    rate_limit.reset()


@pytest.fixture
def identity(monkeypatch):
    """The identity the stubbed provider will report. Mutate to change it."""
    who = oauth.Identity("google", "owner@example.com", "Owner Person")

    async def _fetch(provider, code, verifier):
        assert code == "the-code"
        assert verifier, "the PKCE verifier must survive the round trip"
        return who

    monkeypatch.setattr(oauth, "fetch_identity", _fetch)
    return who


def _client() -> TestClient:
    return TestClient(app, follow_redirects=False)


def _start(client: TestClient) -> str:
    """Begin a Google sign-in and return the state sent to the provider."""
    response = client.get("/api/auth/oauth/google/start")
    assert response.status_code == 302
    location = urlsplit(response.headers["location"])
    assert location.netloc == "accounts.google.com"
    query = parse_qs(location.query)
    assert query["redirect_uri"] == ["http://testserver/api/auth/oauth/google/callback"]
    assert query["code_challenge_method"] == ["S256"]
    return query["state"][0]


def _callback(client: TestClient, state: str, **extra):
    params = {"code": "the-code", "state": state, **extra}
    return client.get("/api/auth/oauth/google/callback", params=params)


def _session_user_id(client: TestClient) -> str:
    return decode_token(client.cookies[settings.SESSION_COOKIE_NAME])["sub"]


# ──────────────────────────────────────────────
# Which providers are offered
# ──────────────────────────────────────────────
def test_only_configured_providers_are_listed(db):
    assert _client().get("/api/auth/oauth/providers").json() == {"providers": ["google"]}


def test_an_unconfigured_provider_returns_to_sign_in(db):
    response = _client().get("/api/auth/oauth/github/start")
    assert response.status_code == 302
    assert response.headers["location"].endswith("/auth/login?oauth_error=unavailable")


def test_an_unknown_provider_is_not_found(db):
    assert _client().get("/api/auth/oauth/myspace/start").status_code == 404


# ──────────────────────────────────────────────
# State
# ──────────────────────────────────────────────
async def test_a_callback_without_this_browsers_state_is_refused(owner, identity):
    attacker = _client()
    state = _start(attacker)

    # The victim's browser has no flow cookie, so a link carrying the
    # attacker's code and state must not sign them in to anything.
    victim = _client()
    response = _callback(victim, state)
    assert response.headers["location"].endswith("oauth_error=expired")
    assert settings.SESSION_COOKIE_NAME not in victim.cookies


async def test_a_mismatched_state_is_refused(owner, identity):
    client = _client()
    _start(client)
    response = _callback(client, "not-the-state")
    assert response.headers["location"].endswith("oauth_error=expired")


async def test_cancelling_at_the_provider_is_reported(owner, identity):
    client = _client()
    state = _start(client)
    response = client.get(
        "/api/auth/oauth/google/callback", params={"state": state, "error": "access_denied"}
    )
    assert response.headers["location"].endswith("oauth_error=cancelled")


async def test_an_unverified_email_is_refused(owner, monkeypatch):
    async def _unverified(*_args):
        raise oauth.OAuthError("no verified email")

    monkeypatch.setattr(oauth, "fetch_identity", _unverified)
    client = _client()
    response = _callback(client, _start(client))
    assert response.headers["location"].endswith("oauth_error=no_email")


# ──────────────────────────────────────────────
# What a verified identity leads to
# ──────────────────────────────────────────────
async def test_an_existing_account_is_signed_in(owner, identity):
    client = _client()
    response = _callback(client, _start(client))

    assert response.headers["location"] == "http://testserver/dashboard"
    assert _session_user_id(client) == str(owner.id)
    # Signing in with a provider leaves the password alone.
    assert verify_password("correct-horse", (await User.get(owner.id)).password_hash)


async def test_the_address_is_matched_regardless_of_case(owner, identity):
    owner.email = "Owner@Example.com"
    await owner.save()

    client = _client()
    _callback(client, _start(client))
    assert _session_user_id(client) == str(owner.id)


async def test_a_disabled_account_is_not_signed_in(owner, identity):
    owner.is_active = False
    await owner.save()

    client = _client()
    response = _callback(client, _start(client))
    assert response.headers["location"].endswith("oauth_error=disabled")
    assert settings.SESSION_COOKIE_NAME not in client.cookies


async def test_a_pending_invitation_is_accepted(org, identity):
    invited = User(org_id=org.id, email="owner@example.com", role=UserRole.MEMBER)
    await invited.insert()

    client = _client()
    response = _callback(client, _start(client))

    assert response.headers["location"] == "http://testserver/dashboard"
    stored = await User.get(invited.id)
    assert stored.password_hash is not None
    assert stored.name == "Owner Person"
    assert _session_user_id(client) == str(invited.id)


async def test_a_new_person_names_their_organisation(db, identity):
    identity.email = "founder@example.com"
    identity.name = "Founder"

    client = _client()
    response = _callback(client, _start(client))
    assert response.headers["location"] == "http://testserver/auth/oauth/complete"
    assert await User.find(User.email == "founder@example.com").count() == 0

    pending = client.get("/api/auth/oauth/signup").json()
    assert pending == {"provider": "google", "email": "founder@example.com", "name": "Founder"}

    created = client.post(
        "/api/auth/oauth/signup",
        json={"name": "Founder's Club"},
        headers={"X-Requested-With": "fetch"},
    )
    assert created.status_code == 201
    assert created.json()["role"] == "owner"

    owner = await User.find_one(User.email == "founder@example.com")
    assert owner.password_hash is not None, "must count as an accepted membership"
    assert (await Organisation.get(owner.org_id)).name == "Founder's Club"
    assert _session_user_id(client) == str(owner.id)

    # The pending identity is spent.
    assert client.get("/api/auth/oauth/signup").status_code == 401


async def test_finishing_signup_needs_the_csrf_header(db, identity):
    identity.email = "founder@example.com"
    client = _client()
    _callback(client, _start(client))

    response = client.post("/api/auth/oauth/signup", json={"name": "Club"})
    assert response.status_code == 403


async def test_finishing_signup_without_a_pending_identity_is_refused(db):
    response = _client().post(
        "/api/auth/oauth/signup", json={"name": "Club"}, headers={"X-Requested-With": "fetch"}
    )
    assert response.status_code == 401


def test_a_flow_cookie_is_not_a_session():
    """Each signed value names its purpose, so none can stand in for another."""
    _, flow = oauth.new_flow("google")
    assert oauth.verify(flow, oauth.FLOW_PURPOSE) is not None
    assert oauth.verify(flow, oauth.SIGNUP_PURPOSE) is None
    assert "sub" not in decode_token(flow)


# ──────────────────────────────────────────────
# Reading the provider's answer
# ──────────────────────────────────────────────
_RealAsyncClient = httpx.AsyncClient


def _provider(monkeypatch, routes: dict):
    """Answer provider HTTP calls from `routes`, keyed by URL."""

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url).split("?")[0]
        return httpx.Response(200, json=routes[url])

    monkeypatch.setattr(
        oauth.httpx, "AsyncClient",
        lambda **kw: _RealAsyncClient(transport=httpx.MockTransport(handler), **kw),
    )


GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"
GOOGLE_INFO = "https://openidconnect.googleapis.com/v1/userinfo"
GITHUB_TOKEN = "https://github.com/login/oauth/access_token"
GITHUB_USER = "https://api.github.com/user"
GITHUB_EMAILS = "https://api.github.com/user/emails"


async def test_google_identity_requires_a_verified_email(monkeypatch):
    _provider(monkeypatch, {
        GOOGLE_TOKEN: {"access_token": "t"},
        GOOGLE_INFO: {"email": "A@Example.com", "email_verified": True, "name": "A"},
    })
    who = await oauth.fetch_identity("google", "code", "verifier")
    assert (who.email, who.name) == ("a@example.com", "A")

    _provider(monkeypatch, {
        GOOGLE_TOKEN: {"access_token": "t"},
        GOOGLE_INFO: {"email": "a@example.com", "email_verified": False},
    })
    with pytest.raises(oauth.OAuthError):
        await oauth.fetch_identity("google", "code", "verifier")


async def test_github_uses_the_primary_verified_address(monkeypatch):
    _provider(monkeypatch, {
        GITHUB_TOKEN: {"access_token": "t"},
        # The public profile email is unverified and must not be used.
        GITHUB_USER: {"login": "octo", "name": None, "email": "public@example.com"},
        GITHUB_EMAILS: [
            {"email": "old@example.com", "primary": False, "verified": True},
            {"email": "Main@Example.com", "primary": True, "verified": True},
        ],
    })
    who = await oauth.fetch_identity("github", "code", "")
    assert (who.email, who.name) == ("main@example.com", "octo")


async def test_github_without_a_verified_primary_is_refused(monkeypatch):
    _provider(monkeypatch, {
        GITHUB_TOKEN: {"access_token": "t"},
        GITHUB_USER: {"login": "octo"},
        GITHUB_EMAILS: [{"email": "a@example.com", "primary": True, "verified": False}],
    })
    with pytest.raises(oauth.OAuthError):
        await oauth.fetch_identity("github", "code", "")


async def test_a_refused_code_is_an_error(monkeypatch):
    _provider(monkeypatch, {GITHUB_TOKEN: {"error": "bad_verification_code"}})
    with pytest.raises(oauth.OAuthError):
        await oauth.fetch_identity("github", "code", "")
