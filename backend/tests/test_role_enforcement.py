"""
Tests that roles are actually enforced.

The role system existed — owner/admin/member, ranked, with a require_role
dependency — but it was applied only to team management and account deletion.
Everywhere else any signed-in user could act, so a "member" the UI describes
as read-only could create drives, decide on candidates and erase a person's
data.

A permission model the UI advertises and the backend does not enforce is
worse than no model, because people rely on it.
"""

import pytest
from fastapi.routing import APIRoute

from app.main import app
from app.models.documents import ROLE_RANK, UserRole


def _dep_names(dependant) -> set[str]:
    out = set()
    for d in dependant.dependencies:
        call = getattr(d, "call", None)
        if call is not None:
            out.add(getattr(call, "__name__", type(call).__name__))
        out |= _dep_names(d)
    return out


def _route(method: str, path: str) -> APIRoute:
    for r in app.routes:
        if isinstance(r, APIRoute) and r.path == path and method in r.methods:
            return r
    raise AssertionError(f"no route {method} {path}")


def _is_guarded(method: str, path: str) -> bool:
    return "_guard" in _dep_names(_route(method, path).dependant)


# ──────────────────────────────────────────────
# Every organisation-facing write needs a role
# ──────────────────────────────────────────────
@pytest.mark.parametrize(
    "method,path",
    [
        ("POST", "/api/drives"),
        ("PATCH", "/api/drives/{drive_id}"),
        ("PATCH", "/api/drives/{drive_id}/status"),
        ("DELETE", "/api/drives/{drive_id}"),
        ("POST", "/api/applicants/{applicant_id}/decision"),
        ("POST", "/api/applicants/{applicant_id}/resend-email"),
        ("POST", "/api/applicants/bulk-decision"),
        ("DELETE", "/api/applicants/{applicant_id}"),
        ("POST", "/api/team"),
        ("PATCH", "/api/team/{user_id}"),
        ("DELETE", "/api/team/{user_id}"),
    ],
)
def test_write_endpoints_require_a_role(method, path):
    assert _is_guarded(method, path), f"{method} {path} is open to any signed-in user"


def test_no_organisation_write_is_left_unguarded():
    """
    Catches a write endpoint added later without a role check, rather than
    relying on the list above being kept up to date.
    """
    public_prefixes = ("/api/apply", "/api/submit", "/api/interview", "/api/auth")
    unguarded = []

    for r in app.routes:
        if not isinstance(r, APIRoute) or not r.path.startswith("/api"):
            continue
        if r.path.startswith(public_prefixes):
            continue
        if not (r.methods & {"POST", "PATCH", "PUT", "DELETE"}):
            continue
        if "_guard" not in _dep_names(r.dependant):
            unguarded.append(f"{sorted(r.methods)[0]} {r.path}")

    assert not unguarded, f"writes with no role check: {unguarded}"


# ──────────────────────────────────────────────
# Reads stay open to every member
# ──────────────────────────────────────────────
@pytest.mark.parametrize(
    "path",
    [
        "/api/applicants",
        "/api/applicants/{applicant_id}",
        "/api/drives",
        "/api/drives/{drive_id}",
        "/api/audit",
        "/api/team",
        "/api/analytics/dashboard",
    ],
)
def test_reads_are_open_to_any_member(path):
    """
    A member is read-only, not locked out. Over-restricting reads would make
    the role useless — reviewing candidates is the whole point of it.
    """
    assert not _is_guarded("GET", path), f"GET {path} should not require a role"


# ──────────────────────────────────────────────
# Which role each action needs
# ──────────────────────────────────────────────
def _required_role(method: str, path: str) -> UserRole:
    for d in _route(method, path).dependant.dependencies:
        call = getattr(d, "call", None)
        if call is not None and getattr(call, "__name__", "") == "_guard":
            # The minimum is captured in the closure of require_role().
            return call.__closure__[0].cell_contents
    raise AssertionError(f"{method} {path} has no role guard")


@pytest.mark.parametrize(
    "method,path",
    [
        ("DELETE", "/api/drives/{drive_id}"),
        ("DELETE", "/api/applicants/{applicant_id}"),
    ],
)
def test_irreversible_deletions_are_owner_only(method, path):
    """
    Deleting a drive takes every candidate with it, and deleting an applicant
    erases a person's transcript. Neither is recoverable, so admin is not
    enough.
    """
    assert _required_role(method, path) is UserRole.OWNER


@pytest.mark.parametrize(
    "method,path",
    [
        ("POST", "/api/drives"),
        ("POST", "/api/applicants/{applicant_id}/decision"),
        ("POST", "/api/applicants/bulk-decision"),
    ],
)
def test_running_recruitment_is_admin(method, path):
    assert ROLE_RANK[_required_role(method, path)] >= ROLE_RANK[UserRole.ADMIN]


def test_owner_satisfies_an_admin_requirement():
    """
    Ranked comparison, so an owner is not locked out of admin actions — which
    would be the obvious way to get this wrong.
    """
    assert ROLE_RANK[UserRole.OWNER] > ROLE_RANK[UserRole.ADMIN] > ROLE_RANK[UserRole.MEMBER]


# ──────────────────────────────────────────────
# End to end: a member is actually refused
# ──────────────────────────────────────────────
import uuid  # noqa: E402
from datetime import date, timedelta  # noqa: E402

import pytest_asyncio  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.models.documents import Organisation, User  # noqa: E402
from app.services.auth_service import get_current_user  # noqa: E402

client = TestClient(app)


@pytest_asyncio.fixture
async def as_role(org: Organisation):
    """Sign in as a user with a given role, for the duration of one test."""

    def _sign_in(role: UserRole) -> User:
        user = User(
            org_id=org.id,
            name=f"{role.value.title()} User",
            email=f"{role.value}@example.com",
            role=role,
        )
        app.dependency_overrides[get_current_user] = lambda: user
        return user

    yield _sign_in
    app.dependency_overrides.clear()


def _create_drive_body() -> dict:
    return {
        "name": "Backend Engineer",
        "domain": "Backend",
        "task_type": "task",
        "task_description": "Build a small service.",
        "question_level": "intermediate",
        "apply_deadline": str(date.today() + timedelta(days=14)),
        "task_deadline": str(date.today() + timedelta(days=28)),
    }


async def test_member_cannot_create_a_drive(as_role):
    as_role(UserRole.MEMBER)
    response = client.post("/api/drives", json=_create_drive_body())
    assert response.status_code == 403
    assert "admin" in response.json()["detail"]


async def test_admin_can_create_a_drive(as_role):
    """
    The guard has to let the right people through, not just block the wrong
    ones — a check that refuses everybody would pass the test above.
    """
    as_role(UserRole.ADMIN)
    response = client.post("/api/drives", json=_create_drive_body())
    assert response.status_code == 201


async def test_admin_cannot_delete_a_drive(as_role, drive):
    as_role(UserRole.ADMIN)
    response = client.delete(f"/api/drives/{drive.id}?confirm=true")
    assert response.status_code == 403
    assert "owner" in response.json()["detail"]


async def test_owner_can_delete_a_drive(as_role, drive):
    as_role(UserRole.OWNER)
    response = client.delete(f"/api/drives/{drive.id}?confirm=true")
    assert response.status_code == 204


async def test_member_can_still_read(as_role, drive):
    """A member who cannot read candidates has no reason to have an account."""
    as_role(UserRole.MEMBER)
    assert client.get("/api/drives").status_code == 200
    assert client.get("/api/applicants").status_code == 200


async def test_member_cannot_decide(as_role, applicant):
    as_role(UserRole.MEMBER)
    response = client.post(
        f"/api/applicants/{applicant.id}/decision", json={"decision": "selected"}
    )
    assert response.status_code == 403


async def test_member_cannot_delete_an_applicant(as_role, applicant):
    as_role(UserRole.MEMBER)
    assert client.delete(f"/api/applicants/{applicant.id}").status_code == 403


# ──────────────────────────────────────────────
# The client has to be able to tell which role it has
# ──────────────────────────────────────────────
@pytest.mark.parametrize("role", list(UserRole))
async def test_me_reports_the_signed_in_role(as_role, role):
    """
    Without this the interface cannot distinguish a member from an owner, so
    it would offer every action to everyone and let the API answer with 403s.
    """
    user = as_role(role)
    body = client.get("/api/auth/me").json()

    assert body["role"] == role.value
    assert body["user_email"] == user.email
    # Still the organisation's own profile, not the user's, for the rest.
    assert body["email"] == "org@example.com"
