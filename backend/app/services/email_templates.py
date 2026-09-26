"""
RECRUIT.AI — Transactional Email Templates

One shared layout, one builder per email. Each builder returns
(subject, html, text).

Email HTML is not web HTML. The constraints driving the markup here:
  - table-based layout; Outlook ignores flex and grid
  - inline styles on every element; Gmail strips <head><style> in some views,
    so the <style> block only carries progressive extras (dark mode, mobile)
  - 600px content width, the long-standing safe maximum
  - the logo is an absolute URL; relative paths cannot resolve in a mail client
  - a plain-text alternative accompanies every message, because text/html-only
    mail is a strong spam signal

Colours mirror the product's Apple-leaning palette from globals.css so mail and
app look like one product.
"""

from __future__ import annotations

from html import escape

from app.config import get_settings

settings = get_settings()

# ── Palette (kept in step with frontend/app/globals.css) ──
BG = "#F5F5F7"
CARD = "#FFFFFF"
TEXT = "#1d1d1f"
MUTED = "#86868b"
PRIMARY = "#007AFF"
BORDER = "#d1d1d6"
SUCCESS = "#34c759"

FONT = (
    "-apple-system,BlinkMacSystemFont,'SF Pro Text','Segoe UI',Roboto,"
    "Helvetica,Arial,sans-serif"
)


def _brand() -> dict:
    app_url = settings.APP_URL.rstrip("/")
    return {
        "name": "RECRUIT.AI",
        "app_url": app_url,
        "logo_url": settings.EMAIL_LOGO_URL or f"{app_url}/icon.png",
        "support_email": settings.SUPPORT_EMAIL,
    }


def _button(label: str, href: str) -> str:
    """
    A bulletproof-ish CTA.

    Rendered as a table rather than a styled <a>, because Outlook collapses
    padding on inline anchors and the button loses its shape.
    """
    return f"""
    <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:28px 0;">
      <tr>
        <td align="center" bgcolor="{PRIMARY}" style="border-radius:980px;">
          <a href="{escape(href, quote=True)}"
             style="display:inline-block;padding:14px 30px;font-family:{FONT};
                    font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;
                    border-radius:980px;">{escape(label)}</a>
        </td>
      </tr>
    </table>"""


def _detail_rows(details: list[tuple[str, str]]) -> str:
    """A small label/value block for facts like deadlines and scores."""
    if not details:
        return ""
    rows = "".join(
        f"""
        <tr>
          <td style="padding:10px 0;border-bottom:1px solid {BORDER};
                     font-family:{FONT};font-size:13px;color:{MUTED};
                     width:40%;vertical-align:top;">{escape(label)}</td>
          <td style="padding:10px 0;border-bottom:1px solid {BORDER};
                     font-family:{FONT};font-size:14px;color:{TEXT};
                     font-weight:600;vertical-align:top;">{escape(value)}</td>
        </tr>"""
        for label, value in details
    )
    return f"""
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
           style="margin:8px 0 4px;border-collapse:collapse;">{rows}</table>"""


def _layout(
    *,
    preheader: str,
    heading: str,
    intro: str,
    body_html: str = "",
    cta_label: str | None = None,
    cta_url: str | None = None,
    fallback_note: str | None = None,
) -> str:
    b = _brand()
    cta = _button(cta_label, cta_url) if cta_label and cta_url else ""

    # Shown under the CTA so the message still works if the button does not
    # render, which is common in stripped-down or text-first clients.
    fallback = ""
    if cta_url and fallback_note:
        fallback = f"""
        <p style="margin:0 0 4px;font-family:{FONT};font-size:12px;color:{MUTED};line-height:1.6;">
          {escape(fallback_note)}
        </p>
        <p style="margin:0 0 8px;font-family:{FONT};font-size:12px;line-height:1.6;word-break:break-all;">
          <a href="{escape(cta_url, quote=True)}" style="color:{PRIMARY};text-decoration:underline;">{escape(cta_url)}</a>
        </p>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="x-apple-disable-message-reformatting">
<meta name="color-scheme" content="light dark">
<title>{escape(heading)}</title>
<style>
  @media (max-width:620px) {{
    .container {{ width:100% !important; }}
    .pad {{ padding-left:22px !important; padding-right:22px !important; }}
    .h1 {{ font-size:23px !important; }}
  }}
  @media (prefers-color-scheme: dark) {{
    .bg {{ background:#000000 !important; }}
    .card {{ background:#1c1c1e !important; border-color:#38383a !important; }}
    .t {{ color:#F5F5F7 !important; }}
    .m {{ color:#98989d !important; }}
  }}
</style>
</head>
<body class="bg" style="margin:0;padding:0;background:{BG};">
  <!-- Preview line: shown in the inbox list, hidden in the message body. -->
  <div style="display:none;max-height:0;overflow:hidden;opacity:0;">
    {escape(preheader)}&#8199;&#65279;&#8199;&#65279;&#8199;&#65279;&#8199;&#65279;&#8199;&#65279;&#8199;&#65279;
  </div>

  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
         class="bg" style="background:{BG};">
    <tr>
      <td align="center" style="padding:32px 12px;">

        <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"
               class="container" style="width:600px;max-width:600px;">

          <!-- Logo -->
          <tr>
            <td align="center" style="padding:0 0 22px;">
              <a href="{escape(b['app_url'], quote=True)}" style="text-decoration:none;">
                <img src="{escape(b['logo_url'], quote=True)}" width="40" height="40" alt="RECRUIT.AI"
                     style="display:block;border:0;border-radius:9px;margin:0 auto 10px;">
                <span class="t" style="font-family:{FONT};font-size:15px;font-weight:700;
                             letter-spacing:-0.2px;color:{TEXT};">RECRUIT<span style="color:{PRIMARY};">.</span>AI</span>
              </a>
            </td>
          </tr>

          <!-- Card -->
          <tr>
            <td class="card" style="background:{CARD};border:1px solid {BORDER};border-radius:14px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td class="pad" style="padding:38px 40px 34px;">
                    <h1 class="h1 t" style="margin:0 0 14px;font-family:{FONT};font-size:26px;
                               line-height:1.25;font-weight:700;letter-spacing:-0.5px;color:{TEXT};">
                      {escape(heading)}
                    </h1>
                    <p class="m" style="margin:0 0 6px;font-family:{FONT};font-size:15px;
                              line-height:1.65;color:{MUTED};">{intro}</p>
                    {body_html}
                    {cta}
                    {fallback}
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td class="pad" style="padding:26px 24px 8px;" align="center">
              <p class="m" style="margin:0 0 10px;font-family:{FONT};font-size:12px;
                        line-height:1.7;color:{MUTED};">
                Sent by <a href="{escape(b['app_url'], quote=True)}" style="color:{MUTED};text-decoration:underline;">RECRUIT.AI</a>,
                an AI-powered recruitment platform.<br>
                Questions? Reach us at
                <a href="mailto:{escape(b['support_email'], quote=True)}" style="color:{PRIMARY};text-decoration:none;">{escape(b['support_email'])}</a>.
              </p>
              <p class="m" style="margin:0 0 10px;font-family:{FONT};font-size:12px;color:{MUTED};">
                <a href="{escape(b['app_url'], quote=True)}/privacy" style="color:{MUTED};text-decoration:underline;">Privacy</a>
                &nbsp;·&nbsp;
                <a href="{escape(b['app_url'], quote=True)}/terms" style="color:{MUTED};text-decoration:underline;">Terms</a>
                &nbsp;·&nbsp;
                <a href="{escape(b['app_url'], quote=True)}/cookies" style="color:{MUTED};text-decoration:underline;">Cookies</a>
              </p>
              <p class="m" style="margin:0;font-family:{FONT};font-size:11px;line-height:1.7;color:{MUTED};">
                This is a transactional message about an application you submitted,
                so there is no subscription to cancel.<br>
                &copy; RECRUIT.AI. All rights reserved.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _text(lines: list[str]) -> str:
    """Plain-text alternative, with the same footer on every message."""
    b = _brand()
    footer = [
        "",
        "—",
        "Sent by RECRUIT.AI, an AI-powered recruitment platform.",
        f"Questions? {b['support_email']}",
        f"Privacy: {b['app_url']}/privacy | Terms: {b['app_url']}/terms",
        "This is a transactional message about an application you submitted.",
    ]
    return "\n".join([ln for ln in lines] + footer)


def _p(text: str) -> str:
    return (
        f'<p class="m" style="margin:0 0 6px;font-family:{FONT};font-size:15px;'
        f'line-height:1.65;color:{MUTED};">{escape(text)}</p>'
    )


# ══════════════════════════════════════════════
# Templates
# ══════════════════════════════════════════════
def application_received(
    *, to_name: str, drive_name: str, org_name: str,
    task_link: str = "", submission_link: str = "",
) -> tuple[str, str, str]:
    heading = "Application received"
    intro = (
        f"Hi {escape(to_name)}, thanks for applying to "
        f"<strong style='color:{TEXT};'>{escape(drive_name)}</strong> at "
        f"<strong style='color:{TEXT};'>{escape(org_name)}</strong>."
    )
    body = _detail_rows([("Role", drive_name), ("Organisation", org_name)])
    body += _p("We will email you the moment there is an update. No action is needed right now.")

    cta_label = cta_url = fallback = None
    if submission_link:
        body = _detail_rows([("Role", drive_name), ("Organisation", org_name)])
        body += _p("Your next step is to complete the assigned task and submit your work.")
        cta_label, cta_url = "Submit your work", submission_link
        fallback = "If the button does not work, paste this link into your browser:"

    html = _layout(
        preheader=f"Your application to {drive_name} was received.",
        heading=heading, intro=intro, body_html=body,
        cta_label=cta_label, cta_url=cta_url, fallback_note=fallback,
    )
    text = _text([
        heading, "",
        f"Hi {to_name}, thanks for applying to {drive_name} at {org_name}.",
        "", f"Role: {drive_name}", f"Organisation: {org_name}",
        *( ["", f"Submit your work: {submission_link}"] if submission_link else
           ["", "We will email you the moment there is an update."] ),
        *( [f"Task details: {task_link}"] if task_link else [] ),
    ])
    return f"Application received — {drive_name}", html, text


def task_assigned(
    *, to_name: str, drive_name: str, task_description: str,
    task_link: str, submission_link: str, deadline: str,
) -> tuple[str, str, str]:
    heading = "Your task is ready"
    intro = (
        f"Hi {escape(to_name)}, here is the task for "
        f"<strong style='color:{TEXT};'>{escape(drive_name)}</strong>."
    )
    body = _detail_rows([("Role", drive_name), ("Submit by", deadline)])
    if task_description:
        body += (
            f'<div style="margin:18px 0 4px;padding:16px 18px;background:{BG};'
            f'border:1px solid {BORDER};border-radius:10px;font-family:{FONT};'
            f'font-size:14px;line-height:1.65;color:{TEXT};white-space:pre-wrap;">'
            f"{escape(task_description)}</div>"
        )
    body += _p("Submit before the deadline to stay in the process.")

    html = _layout(
        preheader=f"Task for {drive_name}. Due {deadline}.",
        heading=heading, intro=intro, body_html=body,
        cta_label="Submit your work", cta_url=submission_link,
        fallback_note="If the button does not work, paste this link into your browser:",
    )
    text = _text([
        heading, "",
        f"Hi {to_name}, here is the task for {drive_name}.",
        "", f"Submit by: {deadline}",
        *( ["", "Task:", task_description] if task_description else [] ),
        "", f"Submit your work: {submission_link}",
        f"Task details: {task_link}",
    ])
    return f"Your task for {drive_name} — due {deadline}", html, text


def interview_invitation(
    *, to_name: str, drive_name: str, interview_link: str,
) -> tuple[str, str, str]:
    heading = "You're invited to interview"
    intro = (
        f"Hi {escape(to_name)}, you have advanced to the AI interview for "
        f"<strong style='color:{TEXT};'>{escape(drive_name)}</strong>."
    )
    body = _detail_rows([
        ("Role", drive_name),
        ("Format", "AI-led, structured"),
        ("Takes about", "5 minutes"),
    ])
    body += _p(
        "Find a quiet spot with a working camera and microphone. "
        "The interview runs in your browser — nothing to install."
    )

    html = _layout(
        preheader=f"Start your interview for {drive_name}.",
        heading=heading, intro=intro, body_html=body,
        cta_label="Start interview", cta_url=interview_link,
        fallback_note="If the button does not work, paste this link into your browser:",
    )
    text = _text([
        heading, "",
        f"Hi {to_name}, you have advanced to the AI interview for {drive_name}.",
        "", "Format: AI-led, structured. Takes about 5 minutes.",
        "Find a quiet spot with a working camera and microphone.",
        "", f"Start your interview: {interview_link}",
    ])
    return f"Your interview for {drive_name}", html, text


def decision_result(
    *, to_name: str, drive_name: str, result_status: str, score: int,
) -> tuple[str, str, str]:
    selected = result_status == "selected"
    heading = "You're moving forward" if selected else "Update on your application"

    if selected:
        intro = (
            f"Congratulations {escape(to_name)} — you have been selected for "
            f"<strong style='color:{TEXT};'>{escape(drive_name)}</strong>."
        )
        closing = "The team will be in touch shortly with next steps."
        badge = (
            f'<div style="display:inline-block;margin:0 0 6px;padding:6px 14px;'
            f'background:rgba(52,199,89,0.12);border:1px solid rgba(52,199,89,0.3);'
            f'border-radius:980px;font-family:{FONT};font-size:12px;font-weight:600;'
            f'color:{SUCCESS};">Selected</div>'
        )
    else:
        intro = (
            f"Hi {escape(to_name)}, thank you for interviewing for "
            f"<strong style='color:{TEXT};'>{escape(drive_name)}</strong>."
        )
        closing = (
            "We are not moving forward with your application this time. "
            "We genuinely appreciate the time you invested, and we hope you apply again."
        )
        badge = ""

    details = [("Role", drive_name)]
    if score:
        details.append(("Interview score", f"{score}/100"))

    body = badge + _detail_rows(details) + _p(closing)

    html = _layout(
        preheader=f"Your result for {drive_name}.",
        heading=heading, intro=intro, body_html=body,
    )
    text = _text([
        heading, "",
        (f"Congratulations {to_name} — you have been selected for {drive_name}."
         if selected else
         f"Hi {to_name}, thank you for interviewing for {drive_name}."),
        "", f"Role: {drive_name}",
        *( [f"Interview score: {score}/100"] if score else [] ),
        "", closing,
    ])
    subject = (
        f"You're moving forward — {drive_name}" if selected
        else f"Update on your application — {drive_name}"
    )
    return subject, html, text


def password_reset(*, to_name: str, reset_link: str, ttl_minutes: int) -> tuple[str, str, str]:
    heading = "Reset your password"
    intro = (
        f"Hi {escape(to_name)}, we received a request to reset the password for "
        "your RECRUIT.AI organisation account."
    )
    body = _detail_rows([("Link expires in", f"{ttl_minutes} minutes")])
    body += _p(
        "If you did not request this, you can ignore this email — "
        "your password stays unchanged and the link will expire on its own."
    )

    html = _layout(
        preheader="Reset your RECRUIT.AI password.",
        heading=heading, intro=intro, body_html=body,
        cta_label="Choose a new password", cta_url=reset_link,
        fallback_note="If the button does not work, paste this link into your browser:",
    )
    text = _text([
        heading, "",
        f"Hi {to_name}, we received a request to reset your RECRUIT.AI password.",
        "", f"Choose a new password: {reset_link}",
        f"This link expires in {ttl_minutes} minutes.",
        "",
        "If you did not request this, you can ignore this email — your password "
        "stays unchanged.",
    ])
    return "Reset your RECRUIT.AI password", html, text


def interview_completed_for_recruiter(
    *, to_name: str, applicant_name: str, drive_name: str,
    total_score: int, review_url: str,
) -> tuple[str, str, str]:
    """
    Sent to the recruiting organisation, not the candidate.

    Every other template here talks to applicants; without this one a
    recruiter only learns an interview finished by opening the dashboard and
    looking.
    """
    heading = "Interview completed"
    intro = (
        f"Hi {escape(to_name)}, "
        f"<strong style='color:{TEXT};'>{escape(applicant_name)}</strong> has finished "
        f"their interview for <strong style='color:{TEXT};'>{escape(drive_name)}</strong>."
    )
    body = _detail_rows([
        ("Candidate", applicant_name),
        ("Role", drive_name),
        ("Score", f"{total_score}/100"),
    ])
    body += _p("Review the transcript and evidence before making a decision.")

    html = _layout(
        preheader=f"{applicant_name} finished their interview for {drive_name}.",
        heading=heading, intro=intro, body_html=body,
        cta_label="Review candidate", cta_url=review_url,
        fallback_note="If the button does not work, paste this link into your browser:",
    )
    text = _text([
        heading, "",
        f"{applicant_name} has finished their interview for {drive_name}.",
        "", f"Score: {total_score}/100",
        "", f"Review the candidate: {review_url}",
    ])
    return f"{applicant_name} completed their interview — {drive_name}", html, text
