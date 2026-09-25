"""
RECRUIT.AI — Email Service
Sends transactional email through the Resend API.

Replaces EmailJS. EmailJS is a browser-oriented service whose templates lived
in a third-party dashboard, which meant the message content was neither in
version control nor reviewable, and its "private key" had to be shipped
server-side to send at all. Templates now live in email_templates.py and ship
with the code.

The public helpers keep the signatures the routers already call, so changing
transport required no edits at any call site.

httpx rather than the official `resend` SDK: the SDK is synchronous, and these
run inside FastAPI background tasks on the event loop, where a blocking HTTP
call would stall the worker. httpx is already a dependency.
"""

import logging
from typing import Optional

import httpx

from app.config import get_settings
from app.services import email_templates

settings = get_settings()
log = logging.getLogger("recruit.email")

RESEND_API_URL = "https://api.resend.com/emails"
REQUEST_TIMEOUT_SECONDS = 15.0


def is_configured() -> bool:
    """True when Resend has enough configuration to actually send."""
    return bool(settings.RESEND_API_KEY and settings.RESEND_FROM_EMAIL)


def _from_header() -> str:
    name = settings.RESEND_FROM_NAME.strip()
    email = settings.RESEND_FROM_EMAIL.strip()
    return f"{name} <{email}>" if name else email


async def send_email(
    *,
    to_email: str,
    subject: str,
    html: str,
    text: str,
    reply_to: Optional[str] = None,
) -> str:
    """
    Deliver one message.

    Returns the Resend message id, or a marker string when sending is skipped
    or fails. This never raises: every caller is a fire-and-forget background
    task, and a mail problem must not take down the request that queued it or
    appear to undo work that already committed.
    """
    if not is_configured():
        log.warning(
            "email skipped: Resend is not configured",
            extra={"to": to_email, "subject": subject},
        )
        return "skipped-no-config"

    payload = {
        "from": _from_header(),
        "to": [to_email],
        "subject": subject,
        "html": html,
        # A plain-text part alongside the HTML: html-only mail is a strong spam
        # signal, and some clients render text by preference.
        "text": text,
    }
    reply = reply_to or settings.SUPPORT_EMAIL
    if reply:
        payload["reply_to"] = reply

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(
                RESEND_API_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            return response.json().get("id", "sent")
    except httpx.HTTPStatusError as exc:
        # Log the status and Resend's message, never the payload or the key.
        log.error(
            "email rejected by Resend",
            extra={
                "to": to_email,
                "subject": subject,
                "status": exc.response.status_code,
                # Resend's message, truncated. Never the payload or the key.
                "response": exc.response.text[:300],
            },
        )
        return "failed"
    except (httpx.HTTPError, ValueError) as exc:
        log.error(
            "email transport failed",
            extra={"to": to_email, "subject": subject, "error": type(exc).__name__},
        )
        return "failed"


# ══════════════════════════════════════════════
# Templated senders
#
# Signatures are unchanged from the EmailJS implementation, so no router needed
# touching during the switch.
# ══════════════════════════════════════════════
async def send_application_email(
    to_email: str,
    to_name: str,
    drive_name: str,
    org_name: str,
    task_link: str = "",
    submission_link: str = "",
):
    """Confirm that an application was received."""
    subject, html, text = email_templates.application_received(
        to_name=to_name,
        drive_name=drive_name,
        org_name=org_name,
        task_link=task_link,
        submission_link=submission_link,
    )
    return await send_email(to_email=to_email, subject=subject, html=html, text=text)


async def send_task_email(
    to_email: str,
    to_name: str,
    drive_name: str,
    task_description: str,
    task_link: str,
    submission_link: str,
    deadline: str,
):
    """Send the assigned task and the submission link."""
    subject, html, text = email_templates.task_assigned(
        to_name=to_name,
        drive_name=drive_name,
        task_description=task_description,
        task_link=task_link,
        submission_link=submission_link,
        deadline=deadline,
    )
    return await send_email(to_email=to_email, subject=subject, html=html, text=text)


async def send_interview_email(
    to_email: str,
    to_name: str,
    drive_name: str,
    interview_link: str,
):
    """Invite a candidate to the AI interview."""
    subject, html, text = email_templates.interview_invitation(
        to_name=to_name,
        drive_name=drive_name,
        interview_link=interview_link,
    )
    return await send_email(to_email=to_email, subject=subject, html=html, text=text)


async def send_result_email(
    to_email: str,
    to_name: str,
    drive_name: str,
    result_status: str,
    score: int,
):
    """Tell a candidate the outcome of their application."""
    subject, html, text = email_templates.decision_result(
        to_name=to_name,
        drive_name=drive_name,
        result_status=result_status,
        score=score,
    )
    return await send_email(to_email=to_email, subject=subject, html=html, text=text)


async def send_password_reset_email(to_email: str, to_name: str, reset_link: str):
    """Send an organisation's password reset link."""
    subject, html, text = email_templates.password_reset(
        to_name=to_name,
        reset_link=reset_link,
        ttl_minutes=settings.PASSWORD_RESET_TOKEN_TTL_MINUTES,
    )
    return await send_email(to_email=to_email, subject=subject, html=html, text=text)
