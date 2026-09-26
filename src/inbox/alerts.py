from __future__ import annotations

import json
import smtplib
import textwrap
from email.message import EmailMessage
from typing import Any, Sequence
from urllib import request

from .models import ScoredMessage

SOURCE_LABELS = {"gmail": "Gmail", "discord": "Discord", "whatsapp": "WhatsApp"}
SOURCE_COLORS = {"gmail": 0xEA4335, "discord": 0x5865F2, "whatsapp": 0x25D366}


def format_digest(items: Sequence[ScoredMessage], heading: str) -> str:
    lines = [heading, ""]
    for scored in items:
        msg = scored.message
        label = SOURCE_LABELS.get(msg.source, msg.source)
        why = ", ".join(scored.reasons) or "important"
        lines.append(
            f"- [{label}] {msg.conversation} — from {msg.sender} "
            f"(score {scored.score}/10: {why})"
        )
        snippet = textwrap.shorten(msg.text.replace("\n", " "), width=200, placeholder="…")
        if snippet:
            lines.append(f"  \"{snippet}\"")
        if msg.url:
            lines.append(f"  {msg.url}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def alert_console(items: Sequence[ScoredMessage]) -> None:
    print(format_digest(items, f"Important conversations ({len(items)}):"))


def alert_discord(items: Sequence[ScoredMessage], webhook_url: str) -> None:
    if not webhook_url:
        raise ValueError("Discord webhook URL is empty")

    for scored in items:
        msg = scored.message
        label = SOURCE_LABELS.get(msg.source, msg.source)
        embed: dict[str, Any] = {
            "title": f"[{label}] {msg.conversation}"[:256],
            "description": textwrap.shorten(msg.text, width=400, placeholder="…"),
            "fields": [
                {"name": "From", "value": msg.sender[:1024] or "?", "inline": True},
                {
                    "name": "Importance",
                    "value": f"{scored.score}/10 — {', '.join(scored.reasons)[:900]}",
                    "inline": True,
                },
            ],
            "color": SOURCE_COLORS.get(msg.source, 0x999999),
            "timestamp": msg.timestamp.isoformat(),
        }
        if msg.url:
            embed["url"] = msg.url

        payload = {"content": "Important conversation needs your attention", "embeds": [embed]}
        req = request.Request(
            webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "Auto_Trader/1.0"},
            method="POST",
        )
        with request.urlopen(req, timeout=30) as resp:
            if resp.status >= 400:
                raise RuntimeError(f"Discord webhook failed: HTTP {resp.status}")


def alert_email(
    items: Sequence[ScoredMessage],
    *,
    to_addr: str,
    from_addr: str,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
) -> None:
    if not to_addr:
        raise ValueError("Email 'to' address is empty")
    sender = from_addr or smtp_user or to_addr
    body = format_digest(items, f"Important conversations ({len(items)}):")
    msg = EmailMessage()
    msg["Subject"] = f"[Inbox Agent] {len(items)} important conversation(s)"
    msg["From"] = sender
    msg["To"] = to_addr
    msg.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port, timeout=45) as smtp:
        smtp.starttls()
        if smtp_user and smtp_password:
            smtp.login(smtp_user, smtp_password)
        smtp.send_message(msg)


def dispatch_alerts(items: Sequence[ScoredMessage], cfg: dict[str, Any]) -> list[str]:
    """Send alerts through every enabled channel. Returns channel names used."""
    if not items:
        return []

    used: list[str] = []
    alert_console(items)
    used.append("console")

    alerts_cfg = (cfg.get("inbox") or {}).get("alerts") or {}
    notif = cfg.get("notifications") or {}

    webhook = alerts_cfg.get("discord_webhook_url") or (
        (notif.get("discord") or {}).get("webhook_url")
        if (notif.get("discord") or {}).get("enabled")
        else ""
    )
    if webhook:
        alert_discord(items, webhook)
        used.append("discord")

    email_cfg = notif.get("email") or {}
    email_enabled = alerts_cfg.get("email")
    if email_enabled is None:
        email_enabled = email_cfg.get("enabled")
    if email_enabled:
        alert_email(
            items,
            to_addr=email_cfg.get("to") or "",
            from_addr=email_cfg.get("from") or "",
            smtp_host=email_cfg.get("smtp_host") or "smtp.gmail.com",
            smtp_port=int(email_cfg.get("smtp_port") or 587),
            smtp_user=email_cfg.get("smtp_user") or "",
            smtp_password=email_cfg.get("smtp_password") or "",
        )
        used.append("email")

    return used
