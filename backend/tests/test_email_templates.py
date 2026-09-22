"""
Tests for the transactional email templates and the Resend transport.

Applicant names, drive names and task descriptions all arrive from public
forms and are interpolated straight into HTML that lands in someone's inbox,
so escaping is the property that matters most here.
"""

import asyncio

import pytest

from app.config import get_settings
from app.services import email_service, email_templates

settings = get_settings()

ALL_TEMPLATES = [
    lambda: email_templates.application_received(
        to_name="Alex", drive_name="Frontend Engineer", org_name="Sparkles Ltd"
    ),
    lambda: email_templates.application_received(
        to_name="Alex", drive_name="Frontend Engineer", org_name="Sparkles Ltd",
        task_link="https://x.test/t", submission_link="https://x.test/s",
    ),
    lambda: email_templates.task_assigned(
        to_name="Alex", drive_name="Frontend Engineer", task_description="Build a thing",
        task_link="https://x.test/t", submission_link="https://x.test/s", deadline="2026-10-05",
    ),
    lambda: email_templates.interview_invitation(
        to_name="Alex", drive_name="Frontend Engineer", interview_link="https://x.test/i"
    ),
    lambda: email_templates.decision_result(
        to_name="Alex", drive_name="Frontend Engineer", result_status="selected", score=87
    ),
    lambda: email_templates.decision_result(
        to_name="Alex", drive_name="Frontend Engineer", result_status="rejected", score=40
    ),
    lambda: email_templates.password_reset(
        to_name="Sparkles Ltd", reset_link="https://x.test/r", ttl_minutes=60
    ),
]


# ──────────────────────────────────────────────
# Shape
# ──────────────────────────────────────────────
@pytest.mark.parametrize("build", ALL_TEMPLATES)
def test_every_template_returns_subject_html_and_text(build):
    subject, html, text = build()
    assert subject and not subject.startswith(" ")
    assert html.lstrip().startswith("<!DOCTYPE html>")
    # A plain-text part must accompany the HTML; html-only mail is a strong
    # spam signal and some clients render text by preference.
    assert text.strip()


@pytest.mark.parametrize("build", ALL_TEMPLATES)
def test_every_template_carries_the_footer(build):
    _, html, text = build()
    for fragment in ("Privacy", "Terms", settings.SUPPORT_EMAIL):
        assert fragment in html, f"footer missing {fragment!r} from HTML"
    assert settings.SUPPORT_EMAIL in text


@pytest.mark.parametrize("build", ALL_TEMPLATES)
def test_logo_and_footer_links_are_absolute(build):
    """Mail clients cannot resolve relative paths, so every URL must be absolute."""
    _, html, _ = build()
    assert 'src="https://' in html or 'src="http://' in html
    assert 'href="https://' in html


@pytest.mark.parametrize("build", ALL_TEMPLATES)
def test_preheader_is_present(build):
    """The inbox preview line; without it clients show raw markup."""
    _, html, _ = build()
    assert "display:none" in html


# ──────────────────────────────────────────────
# Escaping — untrusted input reaches these templates
# ──────────────────────────────────────────────
XSS = '<script>alert("xss")</script>'
IMG = '"><img src=x onerror=alert(1)>'


def test_applicant_name_is_escaped():
    _, html, _ = email_templates.application_received(
        to_name=XSS, drive_name="Role", org_name="Org"
    )
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_drive_name_is_escaped():
    """
    The layout legitimately contains a logo <img>, so assert on the injected
    payload rather than the tag: no attacker-supplied handler may survive.
    """
    _, html, _ = email_templates.interview_invitation(
        to_name="Alex", drive_name=IMG, interview_link="https://x.test/i"
    )
    # The payload must survive only as inert text. "onerror" appearing as
    # escaped characters is harmless; what must not exist is a live tag or an
    # unescaped quote that could break out of the surrounding attribute.
    assert "<img src=x" not in html.lower()
    assert "&lt;img src=x" in html.lower()
    assert '"><img' not in html


def test_task_description_is_escaped():
    """The longest free-text field, and fully attacker-controlled."""
    _, html, _ = email_templates.task_assigned(
        to_name="Alex", drive_name="Role", task_description=XSS,
        task_link="https://x.test/t", submission_link="https://x.test/s",
        deadline="2026-10-05",
    )
    assert "<script>" not in html


def test_links_are_attribute_escaped():
    _, html, _ = email_templates.password_reset(
        to_name="Org", reset_link='https://x.test/r?a="onmouseover="alert(1)', ttl_minutes=60
    )
    assert '"onmouseover="' not in html


# ──────────────────────────────────────────────
# Tone — the rejection must not read as a congratulation
# ──────────────────────────────────────────────
def test_rejection_does_not_congratulate():
    subject, html, text = email_templates.decision_result(
        to_name="Alex", drive_name="Role", result_status="rejected", score=40
    )
    for blob in (subject, html, text):
        assert "congratulations" not in blob.lower()
    assert "Selected" not in subject


def test_selection_is_unambiguous():
    subject, html, _ = email_templates.decision_result(
        to_name="Alex", drive_name="Role", result_status="selected", score=87
    )
    assert "moving forward" in subject.lower()
    assert "Selected" in html


def test_score_is_omitted_when_zero():
    """An applicant rejected before interviewing should not be shown 0/100."""
    _, html, _ = email_templates.decision_result(
        to_name="Alex", drive_name="Role", result_status="rejected", score=0
    )
    assert "0/100" not in html


# ──────────────────────────────────────────────
# Transport
# ──────────────────────────────────────────────
def test_send_is_skipped_cleanly_when_unconfigured(monkeypatch):
    """
    Without an API key, sending must no-op rather than raise. Callers are
    fire-and-forget background tasks, and a mail failure must never appear to
    undo work that already committed.
    """
    monkeypatch.setattr(email_service, "is_configured", lambda: False)
    result = asyncio.run(
        email_service.send_email(
            to_email="a@b.test", subject="s", html="<p>h</p>", text="t"
        )
    )
    assert result == "skipped-no-config"


def test_from_header_combines_name_and_address(monkeypatch):
    monkeypatch.setattr(settings, "RESEND_FROM_NAME", "RECRUIT.AI")
    monkeypatch.setattr(settings, "RESEND_FROM_EMAIL", "no-reply@example.test")
    assert email_service._from_header() == "RECRUIT.AI <no-reply@example.test>"


def test_from_header_falls_back_to_bare_address(monkeypatch):
    monkeypatch.setattr(settings, "RESEND_FROM_NAME", "")
    monkeypatch.setattr(settings, "RESEND_FROM_EMAIL", "no-reply@example.test")
    assert email_service._from_header() == "no-reply@example.test"


def test_is_configured_requires_both_key_and_sender(monkeypatch):
    monkeypatch.setattr(settings, "RESEND_API_KEY", "re_test")
    monkeypatch.setattr(settings, "RESEND_FROM_EMAIL", "")
    assert email_service.is_configured() is False

    monkeypatch.setattr(settings, "RESEND_FROM_EMAIL", "no-reply@example.test")
    assert email_service.is_configured() is True
