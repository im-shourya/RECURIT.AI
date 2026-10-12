"""
Tests for URLs that candidates and organisations supply.

These are rendered as links and images on pages other people open, so a
`javascript:` URL stored here would run in a recruiter's session.
"""

import pytest
from pydantic import ValidationError

from app.models.schemas import (
    ApplyRequest,
    OrgProfileUpdate,
    OrgRegisterRequest,
    SubmissionCreateRequest,
)

HOSTILE = [
    "javascript:alert(document.cookie)",
    "JavaScript:alert(1)",
    "data:text/html,<script>alert(1)</script>",
    "vbscript:msgbox(1)",
    "ftp://github.com/name",
]


def _apply(github_url: str) -> ApplyRequest:
    return ApplyRequest(name="Alex", email="alex@example.com", github_url=github_url)


@pytest.mark.parametrize("url", HOSTILE)
def test_application_rejects_non_web_urls(url):
    with pytest.raises(ValidationError):
        _apply(url)


@pytest.mark.parametrize("url", HOSTILE)
def test_submission_rejects_non_web_urls(url):
    with pytest.raises(ValidationError):
        SubmissionCreateRequest(github_url=url)


@pytest.mark.parametrize("url", HOSTILE)
def test_logo_rejects_non_web_urls(url):
    with pytest.raises(ValidationError):
        OrgProfileUpdate(logo_url=url)
    with pytest.raises(ValidationError):
        OrgRegisterRequest(
            name="Club", email="club@example.com", password="long-enough", logo_url=url
        )


def test_github_urls_must_point_at_github():
    with pytest.raises(ValidationError):
        _apply("https://github.com.evil.example/name")
    with pytest.raises(ValidationError):
        SubmissionCreateRequest(github_url="https://gitlab.com/name/repo")


@pytest.mark.parametrize(
    "typed, stored",
    [
        ("https://github.com/alex", "https://github.com/alex"),
        ("http://www.github.com/alex/repo", "http://www.github.com/alex/repo"),
        ("github.com/alex", "https://github.com/alex"),
        ("  https://github.com/alex  ", "https://github.com/alex"),
    ],
)
def test_ordinary_github_links_are_accepted(typed, stored):
    assert _apply(typed).github_url == stored


def test_empty_values_still_mean_none():
    assert _apply("").github_url == ""
    assert SubmissionCreateRequest().github_url == ""
    assert OrgProfileUpdate(logo_url="").logo_url == ""
    # Absent from a partial update means "leave it alone", not "clear it".
    assert OrgProfileUpdate().logo_url is None


def test_logo_accepts_any_web_host():
    assert (
        OrgProfileUpdate(logo_url="https://cdn.example.com/logo.png").logo_url
        == "https://cdn.example.com/logo.png"
    )


def test_urls_are_bounded():
    with pytest.raises(ValidationError):
        _apply("https://github.com/" + "a" * 2048)
