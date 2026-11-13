import json
from datetime import datetime, timezone

from src.inbox.sources.discord import parse_discord_message
from src.inbox.sources.gmail import parse_email_message
from src.inbox.sources.whatsapp import (
    fetch_messages as whatsapp_fetch,
    normalize_cloud_api_value,
    record_to_message,
)


RAW_EMAIL = b"""\
From: Big Boss <boss@company.com>
To: me@example.com
Subject: Need the report today
Date: Mon, 03 Aug 2026 09:15:00 +0000
Message-ID: <abc123@mail.example.com>
Content-Type: text/plain; charset=utf-8

Can you send the Q3 report by end of day? It's urgent.
"""


def test_parse_email_message():
    msg = parse_email_message(RAW_EMAIL)
    assert msg.source == "gmail"
    assert msg.conversation == "Need the report today"
    assert "boss@company.com" in msg.sender
    assert "Q3 report" in msg.text
    assert msg.message_id == "<abc123@mail.example.com>"
    assert msg.timestamp == datetime(2026, 8, 3, 9, 15, tzinfo=timezone.utc)


def test_parse_email_html_fallback():
    raw = (
        b"From: a@b.com\r\nSubject: Hi\r\n"
        b"Content-Type: text/html; charset=utf-8\r\n\r\n"
        b"<html><body><p>Hello <b>there</b></p></body></html>"
    )
    msg = parse_email_message(raw)
    assert "Hello" in msg.text
    assert "<b>" not in msg.text


def test_parse_discord_message_mentions():
    raw = {
        "id": "111222333",
        "content": "hey @you can you check the deploy?",
        "timestamp": "2026-08-03T10:00:00+00:00",
        "author": {"username": "teammate", "global_name": "Team Mate"},
        "mentions": [{"id": "42"}],
        "mention_everyone": False,
    }
    msg = parse_discord_message(
        raw,
        channel_name="ops",
        channel_id="999",
        guild_id="888",
        my_user_id="42",
    )
    assert msg.source == "discord"
    assert msg.conversation == "#ops"
    assert msg.sender == "Team Mate"
    assert msg.extra["mentions_me"] is True
    assert msg.extra["is_dm"] is False
    assert msg.url == "https://discord.com/channels/888/999/111222333"


def test_parse_discord_dm():
    raw = {
        "id": "5",
        "content": "yo",
        "timestamp": "2026-08-03T10:00:00+00:00",
        "author": {"username": "friend"},
    }
    msg = parse_discord_message(raw, channel_name="friend", channel_id="7", guild_id=None)
    assert msg.extra["is_dm"] is True
    assert msg.conversation == "friend"


def test_whatsapp_cloud_api_normalization_and_fetch(tmp_path):
    value = {
        "contacts": [{"wa_id": "15551234567", "profile": {"name": "Alice"}}],
        "messages": [
            {
                "id": "wamid.XYZ",
                "from": "15551234567",
                "timestamp": str(int(datetime.now(timezone.utc).timestamp())),
                "type": "text",
                "text": {"body": "Call me ASAP, it's urgent"},
            }
        ],
    }
    records = normalize_cloud_api_value(value)
    assert len(records) == 1
    assert records[0]["sender"] == "Alice"

    msg = record_to_message(records[0])
    assert msg.source == "whatsapp"
    assert msg.extra["is_dm"] is True
    assert msg.url == "https://wa.me/15551234567"

    inbox_file = tmp_path / "whatsapp.jsonl"
    inbox_file.write_text(json.dumps(records[0]) + "\n")
    fetched = whatsapp_fetch({"inbox_file": str(inbox_file)}, lookback_hours=24)
    assert len(fetched) == 1
    assert fetched[0].text == "Call me ASAP, it's urgent"


def test_whatsapp_fetch_missing_file(tmp_path):
    assert whatsapp_fetch({"inbox_file": str(tmp_path / "nope.jsonl")}) == []
