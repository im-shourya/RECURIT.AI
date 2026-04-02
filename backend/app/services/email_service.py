"""
RECRUIT.AI — Email Service
Sends transactional emails via EmailJS REST API.

Two separate EmailJS services:
  - Service 1: Applied + Task emails
  - Service 2: Interview + Result emails
"""

import httpx
from app.config import get_settings

settings = get_settings()

EMAILJS_API_URL = "https://api.emailjs.com/api/v1.0/email/send"

# ── Map templates to their service credentials ──
SERVICE_MAP = {
    settings.EMAILJS_TEMPLATE_APPLIED: {
        "service_id": settings.EMAILJS_SERVICE_1_ID,
        "public_key": settings.EMAILJS_SERVICE_1_PUBLIC_KEY,
        "private_key": settings.EMAILJS_SERVICE_1_PRIVATE_KEY,
    },
    settings.EMAILJS_TEMPLATE_TASK: {
        "service_id": settings.EMAILJS_SERVICE_1_ID,
        "public_key": settings.EMAILJS_SERVICE_1_PUBLIC_KEY,
        "private_key": settings.EMAILJS_SERVICE_1_PRIVATE_KEY,
    },
    settings.EMAILJS_TEMPLATE_INTERVIEW: {
        "service_id": settings.EMAILJS_SERVICE_2_ID,
        "public_key": settings.EMAILJS_SERVICE_2_PUBLIC_KEY,
        "private_key": settings.EMAILJS_SERVICE_2_PRIVATE_KEY,
    },
    settings.EMAILJS_TEMPLATE_RESULT: {
        "service_id": settings.EMAILJS_SERVICE_2_ID,
        "public_key": settings.EMAILJS_SERVICE_2_PUBLIC_KEY,
        "private_key": settings.EMAILJS_SERVICE_2_PRIVATE_KEY,
    },
}


async def send_email(template_id: str, template_params: dict) -> str:
    """
    Send an email using the correct EmailJS service based on the template.
    Routes applied/task → Service 1, interview/result → Service 2.
    """
    creds = SERVICE_MAP.get(template_id)
    if not creds or not creds["service_id"]:
        print(f"[EMAIL SKIP] template={template_id}, params={template_params}")
        return "skipped-no-config"

    payload = {
        "service_id": creds["service_id"],
        "template_id": template_id,
        "user_id": creds["public_key"],
        "template_params": template_params,
        "accessToken": creds["private_key"],
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(EMAILJS_API_URL, json=payload)
        response.raise_for_status()
        return response.text


async def send_application_email(
    to_email: str,
    to_name: str,
    drive_name: str,
    org_name: str,
    task_link: str = "",
    submission_link: str = "",
):
    """Send the 'You have applied' confirmation email via Service 1."""
    params = {
        "to_email": to_email,
        "to_name": to_name,
        "drive_name": drive_name,
        "org_name": org_name,
        "task_link": task_link,
        "submission_link": submission_link,
    }
    return await send_email(settings.EMAILJS_TEMPLATE_APPLIED, params)


async def send_task_email(
    to_email: str,
    to_name: str,
    drive_name: str,
    task_description: str,
    task_link: str,
    submission_link: str,
    deadline: str,
):
    """Send the task assignment email via Service 1."""
    params = {
        "to_email": to_email,
        "to_name": to_name,
        "drive_name": drive_name,
        "task_description": task_description,
        "task_link": task_link,
        "submission_link": submission_link,
        "deadline": deadline,
    }
    return await send_email(settings.EMAILJS_TEMPLATE_TASK, params)


async def send_interview_email(
    to_email: str,
    to_name: str,
    drive_name: str,
    interview_link: str,
):
    """Send the interview invitation email via Service 2."""
    params = {
        "to_email": to_email,
        "to_name": to_name,
        "drive_name": drive_name,
        "interview_link": interview_link,
    }
    return await send_email(settings.EMAILJS_TEMPLATE_INTERVIEW, params)


async def send_result_email(
    to_email: str,
    to_name: str,
    drive_name: str,
    result_status: str,
    score: int,
):
    """Send the result notification email via Service 2."""
    params = {
        "to_email": to_email,
        "to_name": to_name,
        "drive_name": drive_name,
        "result_status": result_status,
        "score": str(score),
    }
    return await send_email(settings.EMAILJS_TEMPLATE_RESULT, params)
