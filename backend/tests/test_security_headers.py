"""
Every API response carries the security headers, and the docs pages are
exempt only from the policy that would break them.
"""

from fastapi.testclient import TestClient

from app.main import app
from app.security_headers import API_CSP, headers_for

client = TestClient(app)


def test_api_responses_carry_the_headers():
    response = client.get("/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["Content-Security-Policy"] == API_CSP
    assert "camera=()" in response.headers["Permissions-Policy"]


def test_error_responses_carry_them_too():
    """A 404 is still a response a browser might render."""
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_cors_preflight_carries_them():
    response = client.options(
        "/api/drives",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers["X-Frame-Options"] == "DENY"


def test_docs_are_not_given_the_api_policy():
    """Swagger UI is an HTML page with CDN scripts; the API policy blanks it."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "Content-Security-Policy" not in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"


def test_hsts_only_in_production():
    assert "Strict-Transport-Security" not in headers_for("/api/drives", production=False)
    assert "max-age=" in headers_for("/api/drives", production=True)["Strict-Transport-Security"]
