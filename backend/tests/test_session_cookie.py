"""
Tests for the httpOnly session cookie (#57).

The JWT used to be returned in the login body and kept in localStorage, where
any script on the origin could read it, so a single XSS was a full account
takeover. It now lives in a cookie JavaScript cannot see.
"""

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app
from app.services.auth_service import issue_token

NAME = get_settings().SESSION_COOKIE_NAME
CSRF = {"X-Requested-With": "fetch"}


@pytest.fixture
def browser():
    # A fresh cookie jar per test, so one test's session never leaks into
    # the next.
    return TestClient(app)


def _sign_in(browser):
    return browser.post(
        "/api/auth/login", json={"email": "owner@example.com", "password": "correct-horse"}
    )


async def test_login_sets_an_httponly_cookie_and_returns_no_token(browser, owner):
    response = _sign_in(browser)

    assert response.status_code == 200
    assert "access_token" not in response.json()
    assert response.json()["user_email"] == "owner@example.com"

    cookie = response.headers["set-cookie"].lower()
    assert cookie.startswith(f"{NAME}=")
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert "path=/api" in cookie


async def test_the_cookie_authenticates_reads(browser, owner):
    _sign_in(browser)
    assert browser.get("/api/auth/me").status_code == 200


async def test_a_cookie_write_without_the_csrf_header_is_refused(browser, owner):
    _sign_in(browser)

    response = browser.post(
        "/api/auth/change-password",
        json={"current_password": "wrong-password", "new_password": "battery-staple"},
    )

    assert response.status_code == 403


async def test_a_cookie_write_with_the_csrf_header_goes_through(browser, owner):
    _sign_in(browser)

    response = browser.post(
        "/api/auth/change-password",
        json={"current_password": "wrong-password", "new_password": "battery-staple"},
        headers=CSRF,
    )

    # Reached the handler, which then rejected the wrong password.
    assert response.status_code == 400


async def test_a_bearer_header_still_works_without_the_csrf_header(browser, owner):
    """Non-browser clients attach the header deliberately; it cannot be forged cross-site."""
    response = browser.post(
        "/api/auth/change-password",
        json={"current_password": "wrong-password", "new_password": "battery-staple"},
        headers={"Authorization": f"Bearer {issue_token(owner)}"},
    )
    assert response.status_code == 400


async def test_no_cookie_and_no_header_is_unauthenticated(browser, db):
    assert browser.get("/api/auth/me").status_code == 401


async def test_logout_clears_the_cookie(browser, owner):
    _sign_in(browser)

    response = browser.post("/api/auth/logout", headers=CSRF)

    assert response.status_code == 204
    assert f'{NAME}=""' in response.headers["set-cookie"] or "max-age=0" in (
        response.headers["set-cookie"].lower()
    )
    assert browser.get("/api/auth/me").status_code == 401


async def test_register_signs_the_new_owner_in(browser, db):
    response = browser.post(
        "/api/auth/register",
        json={"name": "New Org", "email": "new@example.com", "password": "battery-staple"},
    )

    assert response.status_code == 201
    assert "access_token" not in response.json()
    assert browser.get("/api/auth/me").json()["role"] == "owner"


@pytest.mark.parametrize(
    "environment,override,expected",
    [
        ("production", None, True),
        ("development", None, False),
        ("development", True, True),
        ("production", False, False),
    ],
)
def test_the_cookie_is_secure_in_production_unless_overridden(environment, override, expected):
    settings = Settings(
        ENVIRONMENT=environment,
        SECRET_KEY="x" * 64,
        SESSION_COOKIE_SECURE=override,
    )
    assert settings.session_cookie_secure is expected
