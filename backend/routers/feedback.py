"""Player feedback endpoint — collects bug reports / feature requests / etc.
and emails them to the configured recipient via Resend.

Free tier (testing mode) of Resend only delivers to the account owner's
verified address; since FEEDBACK_RECIPIENT_EMAIL is also the address used
to sign up at Resend, this works without needing a custom domain.

Sender = `onboarding@resend.dev` (Resend's shared sandbox sender).
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Literal, Optional

import resend
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


class ContextSnapshot(BaseModel):
    """Optional debugging context auto-attached by the frontend."""

    campaignId: Optional[str] = None
    characterId: Optional[str] = None
    characterName: Optional[str] = None
    characterClass: Optional[str] = None
    characterRace: Optional[str] = None
    realmName: Optional[str] = None
    currentLocation: Optional[str] = None
    currentUrl: Optional[str] = None
    userAgent: Optional[str] = None


class FeedbackRequest(BaseModel):
    type: Literal["bug", "feature", "other"]
    title: str = Field(min_length=3, max_length=140)
    description: str = Field(min_length=5, max_length=4000)
    fromEmail: Optional[EmailStr] = None  # optional — only if user fills it
    context: Optional[ContextSnapshot] = None


def _esc(value: Optional[str]) -> str:
    """Minimal HTML escape for snippet rendering."""
    if not value:
        return ""
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _render_email_html(payload: FeedbackRequest, received_at: str) -> str:
    """Build a clean inline-styled HTML body for the inbox view."""
    type_label = {"bug": "🐛 Bug", "feature": "✨ Feature Request", "other": "💬 Other"}.get(
        payload.type, payload.type
    )
    type_color = {"bug": "#dc2626", "feature": "#7c3aed", "other": "#475569"}.get(
        payload.type, "#475569"
    )
    ctx = payload.context.model_dump() if payload.context else {}

    ctx_rows = ""
    for label, key in [
        ("Campaign ID", "campaignId"),
        ("Character ID", "characterId"),
        ("Character", "characterName"),
        ("Class / Race", None),
        ("Realm", "realmName"),
        ("Location", "currentLocation"),
        ("Current URL", "currentUrl"),
        ("User Agent", "userAgent"),
    ]:
        if label == "Class / Race":
            klass = ctx.get("characterClass") or ""
            race = ctx.get("characterRace") or ""
            joined = " ".join([s for s in [race, klass] if s])
            if not joined:
                continue
            value = joined
        else:
            value = ctx.get(key) or ""
            if not value:
                continue
        ctx_rows += (
            f'<tr><td style="padding:4px 12px 4px 0;color:#64748b;'
            f'font-size:12px;vertical-align:top;white-space:nowrap;">'
            f'{_esc(label)}</td>'
            f'<td style="padding:4px 0;color:#1e293b;font-size:12px;'
            f'font-family:Menlo,Consolas,monospace;word-break:break-all;">'
            f'{_esc(value)}</td></tr>'
        )

    ctx_block = (
        f'<table style="border-collapse:collapse;margin-top:16px;'
        f'background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;'
        f'padding:12px 16px;width:100%;">{ctx_rows}</table>'
        if ctx_rows
        else ""
    )

    description_html = _esc(payload.description).replace("\n", "<br/>")
    from_line = (
        f'<div style="font-size:13px;color:#64748b;margin-top:4px;">'
        f'From: <a href="mailto:{_esc(payload.fromEmail)}" '
        f'style="color:#0ea5e9;">{_esc(payload.fromEmail)}</a></div>'
        if payload.fromEmail
        else '<div style="font-size:13px;color:#94a3b8;margin-top:4px;">'
        '(player did not provide email)</div>'
    )

    return f"""<!DOCTYPE html>
<html><body style="margin:0;padding:24px;background:#f1f5f9;
font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;">
  <table style="max-width:640px;margin:0 auto;background:#ffffff;
border-radius:8px;border:1px solid #e2e8f0;overflow:hidden;">
    <tr><td style="padding:24px;">
      <div style="display:inline-block;padding:4px 12px;border-radius:999px;
background:{type_color};color:#ffffff;font-size:12px;
font-weight:600;letter-spacing:0.5px;text-transform:uppercase;">
        {_esc(type_label)}
      </div>
      <h2 style="margin:12px 0 0;color:#0f172a;font-size:20px;">
        {_esc(payload.title)}
      </h2>
      {from_line}
      <div style="margin-top:20px;padding:16px;background:#fafaf9;
border-left:3px solid {type_color};border-radius:4px;color:#1e293b;
font-size:14px;line-height:1.6;">
        {description_html}
      </div>
      {ctx_block}
      <div style="margin-top:20px;font-size:11px;color:#94a3b8;">
        Received {_esc(received_at)} · RPG Forge feedback channel
      </div>
    </td></tr>
  </table>
</body></html>"""


@router.post("/")
async def submit_feedback(payload: FeedbackRequest):
    api_key = os.getenv("RESEND_API_KEY")
    recipient = os.getenv("FEEDBACK_RECIPIENT_EMAIL")
    sender = os.getenv("RESEND_SENDER_EMAIL", "onboarding@resend.dev")

    if not api_key or not recipient:
        # Fail loudly — the dev needs to know the env wasn't picked up.
        logger.error("Feedback submit attempted but RESEND_API_KEY / "
                     "FEEDBACK_RECIPIENT_EMAIL not configured")
        raise HTTPException(
            status_code=503,
            detail="Feedback channel not configured — please contact the developer.",
        )

    resend.api_key = api_key
    received_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    subject = f"[RPG Forge · {payload.type.upper()}] {payload.title}"

    params = {
        "from": sender,
        "to": [recipient],
        "subject": subject,
        "html": _render_email_html(payload, received_at),
    }
    # Player's email -> reply_to so you can answer in one click.
    if payload.fromEmail:
        params["reply_to"] = payload.fromEmail

    try:
        sent = await asyncio.to_thread(resend.Emails.send, params)
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Resend send failed: {exc}")
        raise HTTPException(
            status_code=502,
            detail=f"Email delivery failed: {exc}",
        )

    return {
        "ok": True,
        "email_id": sent.get("id") if isinstance(sent, dict) else None,
        "received_at": received_at,
    }
