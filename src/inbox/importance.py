from __future__ import annotations

import re
from typing import Any, Iterable

from .models import Message, ScoredMessage

# Words that almost always mean "read this now".
URGENT_WORDS = re.compile(
    r"\b(urgent|urgently|asap|emergency|immediately|critical|time.sensitive|"
    r"right away|call me|need you|please respond|please reply|action required|"
    r"final notice|last chance|overdue|expiring|expires)\b",
    re.IGNORECASE,
)

# Softer time pressure: deadlines and near-term scheduling.
TIME_WORDS = re.compile(
    r"\b(today|tonight|tomorrow|by (eod|end of day|noon|friday|monday)|"
    r"deadline|due (today|tomorrow|by)|this (morning|afternoon|evening))\b",
    re.IGNORECASE,
)

MONEY_PATTERN = re.compile(
    r"([$£€]\s?\d[\d,]*(\.\d+)?)|\b(\d[\d,]*\s?(usd|dollars|eur|gbp))\b|"
    r"\b(invoice|payment|paid|refund|wire|transfer|owe|owed)\b",
    re.IGNORECASE,
)

QUESTION_PATTERN = re.compile(
    r"\?|\b(can you|could you|will you|would you|are you able|let me know|"
    r"what do you think|please confirm|any update|did you)\b",
    re.IGNORECASE,
)

MEETING_WORDS = re.compile(
    r"\b(meeting|meet up|call at|zoom|appointment|interview|reschedul|"
    r"cancel+ed|confirm(ed)? (for|at)|flight|reservation)\b",
    re.IGNORECASE,
)

# Bulk mail markers — these push a message towards "ignore".
BULK_SENDER = re.compile(
    r"(no.?reply|do.?not.?reply|newsletter|notifications?@|marketing@|"
    r"updates@|info@|noreply)",
    re.IGNORECASE,
)
BULK_BODY = re.compile(
    r"\b(unsubscribe|view (this email )?in (your )?browser|manage preferences|"
    r"promotional|% off|flash sale)\b",
    re.IGNORECASE,
)


def _matches_any(value: str, needles: Iterable[str]) -> bool:
    lowered = value.lower()
    return any(needle.lower() in lowered for needle in needles if needle)


def score_message(message: Message, cfg: dict[str, Any] | None = None) -> ScoredMessage:
    """Score 0-10. Rule-based so it runs anywhere with zero extra dependencies."""
    cfg = cfg or {}
    vip_senders: list[str] = cfg.get("vip_senders") or []
    keywords: list[str] = cfg.get("keywords") or []
    muted_senders: list[str] = cfg.get("muted_senders") or []
    muted_conversations: list[str] = cfg.get("muted_conversations") or []

    text = message.text or ""
    haystack = f"{message.conversation}\n{text}"

    score = 0
    reasons: list[str] = []

    if _matches_any(message.sender, muted_senders) or _matches_any(
        message.conversation, muted_conversations
    ):
        return ScoredMessage(message, 0, ["muted"])

    if _matches_any(message.sender, vip_senders):
        score += 4
        reasons.append("VIP sender")

    if _matches_any(haystack, keywords):
        score += 3
        reasons.append("watched keyword")

    if URGENT_WORDS.search(haystack):
        score += 3
        reasons.append("urgent language")

    if TIME_WORDS.search(haystack):
        score += 1
        reasons.append("time-sensitive")

    if MONEY_PATTERN.search(haystack):
        score += 1
        reasons.append("money/payment")

    if QUESTION_PATTERN.search(text):
        score += 1
        reasons.append("asks a question")

    if MEETING_WORDS.search(haystack):
        score += 1
        reasons.append("meeting/scheduling")

    if message.extra.get("mentions_me"):
        score += 3
        reasons.append("you were mentioned")

    if message.extra.get("is_dm"):
        score += 2
        reasons.append("direct message")

    # Bulk mail penalty applies mostly to email but is harmless elsewhere.
    if BULK_SENDER.search(message.sender) or BULK_BODY.search(text):
        score -= 4
        reasons.append("looks like bulk mail")

    score = max(0, min(10, score))
    return ScoredMessage(message, score, reasons)


def filter_important(
    messages: Iterable[Message],
    cfg: dict[str, Any] | None = None,
    *,
    min_score: int | None = None,
) -> list[ScoredMessage]:
    cfg = cfg or {}
    threshold = min_score if min_score is not None else int(cfg.get("min_importance") or 3)
    scored = [score_message(msg, cfg) for msg in messages]
    important = [s for s in scored if s.score >= threshold]
    important.sort(key=lambda s: (-s.score, s.message.timestamp))
    return important
