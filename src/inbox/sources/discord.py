from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from ..models import Message

API_BASE = "https://discord.com/api/v10"
MAX_MESSAGES_PER_CHANNEL = 100


def parse_discord_message(
    raw: dict[str, Any],
    *,
    channel_name: str,
    channel_id: str,
    guild_id: str | None = None,
    my_user_id: str = "",
) -> Message:
    """Normalize one message object from the Discord REST API."""
    author = raw.get("author") or {}
    sender = author.get("global_name") or author.get("username") or "unknown"

    ts = datetime.now(timezone.utc)
    if raw.get("timestamp"):
        ts = datetime.fromisoformat(raw["timestamp"])

    mentions_me = False
    if my_user_id:
        mentions_me = any(
            str(m.get("id")) == str(my_user_id) for m in raw.get("mentions") or []
        )
        if raw.get("mention_everyone"):
            mentions_me = True

    path = f"{guild_id or '@me'}/{channel_id}/{raw.get('id', '')}"
    return Message(
        source="discord",
        conversation=f"#{channel_name}" if guild_id else channel_name,
        sender=sender,
        text=(raw.get("content") or "")[:800],
        timestamp=ts,
        message_id=str(raw.get("id") or ""),
        url=f"https://discord.com/channels/{path}",
        extra={
            "mentions_me": mentions_me,
            "is_dm": guild_id is None,
            "channel_id": channel_id,
        },
    )


def _get(session: requests.Session, path: str, token: str) -> Any:
    resp = session.get(
        f"{API_BASE}{path}",
        headers={
            "Authorization": f"Bot {token}",
            "User-Agent": "Auto_Trader-InboxAgent/1.0",
        },
        timeout=30,
    )
    if resp.status_code == 403:
        return None  # bot lacks access to this channel; skip quietly
    resp.raise_for_status()
    return resp.json()


def fetch_messages(cfg: dict[str, Any], *, lookback_hours: int = 24) -> list[Message]:
    """Poll recent messages from the configured channels with a bot token.

    Note: Discord bots can only read channels they've been invited to (plus DMs
    sent to the bot itself). They cannot read your personal DMs — that would
    require a user token, which Discord's ToS forbids automating.
    """
    token = cfg.get("bot_token") or ""
    if not token:
        raise RuntimeError("Discord source needs bot_token (DISCORD_BOT_TOKEN)")

    channel_ids = [str(c) for c in (cfg.get("channel_ids") or []) if c]
    my_user_id = str(cfg.get("my_user_id") or "")
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)

    session = requests.Session()
    messages: list[Message] = []
    for channel_id in channel_ids:
        channel = _get(session, f"/channels/{channel_id}", token)
        if channel is None:
            continue
        guild_id = channel.get("guild_id")
        name = channel.get("name") or ", ".join(
            r.get("global_name") or r.get("username") or "?"
            for r in channel.get("recipients") or []
        ) or channel_id

        raw_messages = _get(
            session,
            f"/channels/{channel_id}/messages?limit={MAX_MESSAGES_PER_CHANNEL}",
            token,
        )
        if not raw_messages:
            continue
        for raw in raw_messages:
            msg = parse_discord_message(
                raw,
                channel_name=name,
                channel_id=channel_id,
                guild_id=guild_id,
                my_user_id=my_user_id,
            )
            if msg.timestamp >= cutoff and msg.text:
                messages.append(msg)
    return messages
