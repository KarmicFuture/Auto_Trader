from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ..models import Message

DEFAULT_INBOX_FILE = (
    Path(__file__).resolve().parents[3] / "data" / "inbox" / "whatsapp.jsonl"
)


def normalize_cloud_api_value(value: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten one WhatsApp Cloud API webhook `value` into simple records.

    Meta's webhook nests messages under entry[].changes[].value; the receiver
    in `src.inbox.whatsapp_webhook` calls this and appends the result to the
    JSONL inbox file that `fetch_messages` reads.
    """
    contacts = {
        c.get("wa_id"): (c.get("profile") or {}).get("name")
        for c in value.get("contacts") or []
    }
    records: list[dict[str, Any]] = []
    for msg in value.get("messages") or []:
        if msg.get("type") != "text":
            body = f"[{msg.get('type', 'media')} message]"
        else:
            body = (msg.get("text") or {}).get("body") or ""
        wa_id = msg.get("from") or ""
        sender = contacts.get(wa_id) or wa_id
        ts_raw = msg.get("timestamp")
        ts = (
            datetime.fromtimestamp(int(ts_raw), tz=timezone.utc)
            if ts_raw
            else datetime.now(timezone.utc)
        )
        records.append(
            {
                "message_id": msg.get("id") or "",
                "sender": sender,
                "wa_id": wa_id,
                "text": body,
                "timestamp": ts.isoformat(),
            }
        )
    return records


def record_to_message(record: dict[str, Any]) -> Message:
    ts_raw = record.get("timestamp")
    ts = datetime.fromisoformat(ts_raw) if ts_raw else datetime.now(timezone.utc)
    sender = record.get("sender") or record.get("wa_id") or "unknown"
    wa_id = record.get("wa_id") or ""
    return Message(
        source="whatsapp",
        conversation=sender,
        sender=sender,
        text=(record.get("text") or "")[:800],
        timestamp=ts,
        message_id=str(record.get("message_id") or ""),
        url=f"https://wa.me/{wa_id}" if wa_id else "",
        extra={"is_dm": True, "wa_id": wa_id},
    )


def fetch_messages(cfg: dict[str, Any], *, lookback_hours: int = 24) -> list[Message]:
    """Read messages captured by the WhatsApp webhook receiver.

    WhatsApp has no polling API for personal accounts, so incoming messages are
    delivered by the Business Cloud API to `src.inbox.whatsapp_webhook`, which
    appends them to a JSONL file this source reads.
    """
    inbox_file = Path(cfg.get("inbox_file") or DEFAULT_INBOX_FILE)
    if not inbox_file.exists():
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    messages: list[Message] = []
    for line in inbox_file.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = record_to_message(record)
        if msg.timestamp >= cutoff and msg.text:
            messages.append(msg)
    return messages
