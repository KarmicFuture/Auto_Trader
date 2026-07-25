from __future__ import annotations

import json
import os
import smtplib
import subprocess
import textwrap
from email.message import EmailMessage
from typing import Any, Sequence
from urllib import error, request

from .models import Listing


def format_digest(listings: Sequence[Listing], heading: str) -> str:
    lines = [heading, ""]
    for listing in listings:
        lines.append(f"- {listing.summary_line()}")
        lines.append(f"  {listing.url}")
        if listing.notes:
            note = textwrap.shorten(listing.notes, width=180, placeholder="…")
            lines.append(f"  {note}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def notify_console(listings: Sequence[Listing]) -> None:
    print(format_digest(listings, f"New Honda S2000 listings ({len(listings)}):"))


def notify_discord(listings: Sequence[Listing], webhook_url: str) -> None:
    if not webhook_url:
        raise ValueError("Discord webhook URL is empty")

    # Discord embeds: keep under size limits; batch if needed.
    for listing in listings:
        embed = {
            "title": listing.title[:256],
            "url": listing.url,
            "description": (listing.notes or "")[:400] or listing.price_label(),
            "fields": [
                {"name": "Price", "value": listing.price_label(), "inline": True},
                {
                    "name": "Source",
                    "value": listing.source,
                    "inline": True,
                },
            ],
            "color": 0xC8102E,  # Honda-ish red
        }
        if listing.location:
            embed["fields"].append(
                {"name": "Location", "value": listing.location[:1024], "inline": True}
            )
        if listing.mileage is not None:
            embed["fields"].append(
                {
                    "name": "Mileage",
                    "value": f"{listing.mileage:,} mi",
                    "inline": True,
                }
            )
        if listing.thumbnail:
            embed["thumbnail"] = {"url": listing.thumbnail}

        payload = {
            "content": "New Honda S2000 for sale",
            "embeds": [embed],
        }
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            webhook_url,
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": "Auto_Trader/1.0"},
            method="POST",
        )
        with request.urlopen(req, timeout=30) as resp:
            if resp.status >= 400:
                raise RuntimeError(f"Discord webhook failed: HTTP {resp.status}")


def notify_email(
    listings: Sequence[Listing],
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
    body = format_digest(listings, f"New Honda S2000 listings ({len(listings)})")
    msg = EmailMessage()
    msg["Subject"] = f"[Auto_Trader] {len(listings)} new Honda S2000 listing(s)"
    msg["From"] = sender
    msg["To"] = to_addr
    msg.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port, timeout=45) as smtp:
        smtp.starttls()
        if smtp_user and smtp_password:
            smtp.login(smtp_user, smtp_password)
        smtp.send_message(msg)


def notify_github_issues(
    listings: Sequence[Listing],
    *,
    labels: Sequence[str] | None = None,
) -> None:
    """Create one GitHub issue per listing using the `gh` CLI when available."""
    repo = os.getenv("GITHUB_REPOSITORY")
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required for GitHub issue notifications")

    label_args: list[str] = []
    for label in labels or ["s2000-alert"]:
        label_args.extend(["--label", label])

    for listing in listings:
        body = format_digest([listing], "New Honda S2000 listing detected by Auto_Trader.")
        title = f"S2000 alert: {listing.title}"[:200]
        cmd = [
            "gh",
            "issue",
            "create",
            "--title",
            title,
            "--body",
            body,
            *label_args,
        ]
        if repo:
            cmd.extend(["--repo", repo])
        env = os.environ.copy()
        env["GH_TOKEN"] = token
        subprocess.run(cmd, check=True, env=env)


def dispatch_notifications(
    listings: Sequence[Listing],
    cfg: dict[str, Any],
) -> list[str]:
    """Send notifications through every enabled channel. Returns channel names used."""
    if not listings:
        return []

    used: list[str] = []
    notify_console(listings)
    used.append("console")

    notif = cfg.get("notifications") or {}

    email_cfg = notif.get("email") or {}
    if email_cfg.get("enabled"):
        notify_email(
            listings,
            to_addr=email_cfg.get("to") or "",
            from_addr=email_cfg.get("from") or "",
            smtp_host=email_cfg.get("smtp_host") or "smtp.gmail.com",
            smtp_port=int(email_cfg.get("smtp_port") or 587),
            smtp_user=email_cfg.get("smtp_user") or "",
            smtp_password=email_cfg.get("smtp_password") or "",
        )
        used.append("email")

    discord_cfg = notif.get("discord") or {}
    if discord_cfg.get("enabled"):
        notify_discord(listings, discord_cfg.get("webhook_url") or "")
        used.append("discord")

    gh_cfg = notif.get("github_issues") or {}
    if gh_cfg.get("enabled") and (
        os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN") or os.getenv("GITHUB_ACTIONS")
    ):
        try:
            notify_github_issues(listings, labels=gh_cfg.get("labels") or ["s2000-alert"])
            used.append("github_issues")
        except (FileNotFoundError, subprocess.CalledProcessError, RuntimeError) as exc:
            # Don't fail the whole run if issue creation isn't available locally.
            print(f"GitHub issue notification skipped: {exc}")

    return used


def safe_request_json(url: str, headers: dict[str, str] | None = None) -> Any:
    req = request.Request(
        url,
        headers=headers
        or {"User-Agent": "Auto_Trader/1.0 (+https://github.com/KarmicFuture/Auto_Trader)"},
    )
    try:
        with request.urlopen(req, timeout=45) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} for {url}") from exc
