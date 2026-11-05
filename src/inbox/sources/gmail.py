from __future__ import annotations

import email
import email.header
import email.utils
import imaplib
from datetime import datetime, timedelta, timezone
from email.message import Message as EmailMessage
from typing import Any

from ..models import Message

MAX_BODY_CHARS = 800


def _decode_header(raw: str | None) -> str:
    if not raw:
        return ""
    parts = []
    for chunk, charset in email.header.decode_header(raw):
        if isinstance(chunk, bytes):
            parts.append(chunk.decode(charset or "utf-8", errors="replace"))
        else:
            parts.append(chunk)
    return "".join(parts).strip()


def _extract_body(msg: EmailMessage) -> str:
    """Prefer the text/plain part; fall back to stripped-down HTML."""
    candidates: list[tuple[str, str]] = []
    for part in msg.walk():
        if part.get_content_maintype() != "text":
            continue
        if "attachment" in (part.get("Content-Disposition") or ""):
            continue
        payload = part.get_payload(decode=True)
        if payload is None:
            continue
        charset = part.get_content_charset() or "utf-8"
        try:
            text = payload.decode(charset, errors="replace")
        except LookupError:
            text = payload.decode("utf-8", errors="replace")
        candidates.append((part.get_content_subtype(), text))

    for subtype, text in candidates:
        if subtype == "plain":
            return text.strip()[:MAX_BODY_CHARS]
    for _, text in candidates:
        # Crude HTML strip — good enough for importance scoring.
        import re

        stripped = re.sub(r"<[^>]+>", " ", text)
        stripped = re.sub(r"\s+", " ", stripped)
        return stripped.strip()[:MAX_BODY_CHARS]
    return ""


def parse_email_message(raw_bytes: bytes, *, folder: str = "INBOX") -> Message:
    """Turn a raw RFC822 message into our normalized Message."""
    msg = email.message_from_bytes(raw_bytes)
    subject = _decode_header(msg.get("Subject")) or "(no subject)"
    sender = _decode_header(msg.get("From"))
    message_id = (msg.get("Message-ID") or "").strip()

    ts = datetime.now(timezone.utc)
    date_raw = msg.get("Date")
    if date_raw:
        parsed = email.utils.parsedate_to_datetime(date_raw)
        if parsed is not None:
            ts = parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

    extra: dict[str, Any] = {"folder": folder}
    if msg.get("List-Unsubscribe"):
        extra["list_mail"] = True

    return Message(
        source="gmail",
        conversation=subject,
        sender=sender,
        text=_extract_body(msg),
        timestamp=ts,
        message_id=message_id or "",
        url="https://mail.google.com/mail/u/0/#search/"
        + (message_id.strip("<>").replace("@", "%40") if message_id else ""),
        extra=extra,
    )


def fetch_messages(cfg: dict[str, Any], *, lookback_hours: int = 24) -> list[Message]:
    """Fetch recent messages over IMAP (works with a Gmail app password)."""
    user = cfg.get("user") or ""
    password = cfg.get("app_password") or ""
    if not user or not password:
        raise RuntimeError("Gmail source needs user + app_password (GMAIL_APP_PASSWORD)")

    host = cfg.get("imap_host") or "imap.gmail.com"
    folders = cfg.get("folders") or ["INBOX"]
    unread_only = bool(cfg.get("unread_only", True))

    since = (datetime.now(timezone.utc) - timedelta(hours=lookback_hours)).strftime(
        "%d-%b-%Y"
    )
    criteria = f'(SINCE "{since}")'
    if unread_only:
        criteria = f'(UNSEEN SINCE "{since}")'

    messages: list[Message] = []
    with imaplib.IMAP4_SSL(host) as imap:
        imap.login(user, password)
        for folder in folders:
            status, _ = imap.select(f'"{folder}"', readonly=True)
            if status != "OK":
                continue
            status, data = imap.search(None, criteria)
            if status != "OK" or not data or not data[0]:
                continue
            ids = data[0].split()
            # Newest last; cap per folder to keep runs fast.
            for num in ids[-100:]:
                # BODY.PEEK keeps the message unread in the mailbox.
                status, fetched = imap.fetch(num, "(BODY.PEEK[])")
                if status != "OK" or not fetched or fetched[0] is None:
                    continue
                payload = fetched[0]
                if isinstance(payload, tuple) and len(payload) > 1:
                    messages.append(parse_email_message(payload[1], folder=folder))
    return messages
