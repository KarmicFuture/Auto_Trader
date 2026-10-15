from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ..config import _deep_merge, _env_bool, load_config


def load_inbox_config(path: Path | None = None) -> dict[str, Any]:
    """Base config plus inbox-specific environment overrides."""
    cfg = load_config(path)

    overlay: dict[str, Any] = {}
    inbox: dict[str, Any] = {}

    if _env_bool("INBOX_ENABLED") is not None:
        inbox["enabled"] = _env_bool("INBOX_ENABLED")
    if os.getenv("INBOX_LOOKBACK_HOURS"):
        inbox["lookback_hours"] = int(os.getenv("INBOX_LOOKBACK_HOURS", "24"))
    if os.getenv("INBOX_MIN_IMPORTANCE"):
        inbox["min_importance"] = int(os.getenv("INBOX_MIN_IMPORTANCE", "3"))
    if os.getenv("INBOX_VIP_SENDERS"):
        inbox["vip_senders"] = [
            s.strip() for s in os.getenv("INBOX_VIP_SENDERS", "").split(",") if s.strip()
        ]
    if os.getenv("INBOX_KEYWORDS"):
        inbox["keywords"] = [
            s.strip() for s in os.getenv("INBOX_KEYWORDS", "").split(",") if s.strip()
        ]

    gmail: dict[str, Any] = {}
    if os.getenv("GMAIL_USER"):
        gmail["user"] = os.getenv("GMAIL_USER")
    if os.getenv("GMAIL_APP_PASSWORD"):
        gmail["app_password"] = os.getenv("GMAIL_APP_PASSWORD")
        gmail.setdefault("enabled", True)
    if _env_bool("INBOX_GMAIL_ENABLED") is not None:
        gmail["enabled"] = _env_bool("INBOX_GMAIL_ENABLED")
    if gmail:
        inbox["gmail"] = gmail

    discord: dict[str, Any] = {}
    if os.getenv("DISCORD_BOT_TOKEN"):
        discord["bot_token"] = os.getenv("DISCORD_BOT_TOKEN")
        discord.setdefault("enabled", True)
    if os.getenv("DISCORD_CHANNEL_IDS"):
        discord["channel_ids"] = [
            s.strip()
            for s in os.getenv("DISCORD_CHANNEL_IDS", "").split(",")
            if s.strip()
        ]
    if os.getenv("DISCORD_MY_USER_ID"):
        discord["my_user_id"] = os.getenv("DISCORD_MY_USER_ID")
    if _env_bool("INBOX_DISCORD_ENABLED") is not None:
        discord["enabled"] = _env_bool("INBOX_DISCORD_ENABLED")
    if discord:
        inbox["discord"] = discord

    whatsapp: dict[str, Any] = {}
    if os.getenv("WHATSAPP_INBOX_FILE"):
        whatsapp["inbox_file"] = os.getenv("WHATSAPP_INBOX_FILE")
    if _env_bool("INBOX_WHATSAPP_ENABLED") is not None:
        whatsapp["enabled"] = _env_bool("INBOX_WHATSAPP_ENABLED")
    if whatsapp:
        inbox["whatsapp"] = whatsapp

    alerts: dict[str, Any] = {}
    if os.getenv("INBOX_DISCORD_WEBHOOK_URL"):
        alerts["discord_webhook_url"] = os.getenv("INBOX_DISCORD_WEBHOOK_URL")
    if _env_bool("INBOX_ALERT_EMAIL") is not None:
        alerts["email"] = _env_bool("INBOX_ALERT_EMAIL")
    if alerts:
        inbox["alerts"] = alerts

    if inbox:
        overlay["inbox"] = inbox
    return _deep_merge(cfg, overlay)
