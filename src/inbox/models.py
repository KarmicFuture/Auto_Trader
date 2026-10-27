from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Message:
    """A single message pulled from any monitored channel."""

    source: str  # "gmail" | "discord" | "whatsapp"
    conversation: str  # thread subject, channel name, or chat name
    sender: str
    text: str
    timestamp: datetime
    message_id: str = ""  # provider id; falls back to a content hash
    url: str = ""  # deep link to open the conversation, when available
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)
        if not self.message_id:
            digest = hashlib.sha256(
                f"{self.source}|{self.conversation}|{self.sender}|{self.text}".encode()
            ).hexdigest()[:20]
            self.message_id = digest

    @property
    def key(self) -> str:
        return f"{self.source}:{self.message_id}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "conversation": self.conversation,
            "sender": self.sender,
            "text": self.text,
            "timestamp": self.timestamp.isoformat(),
            "message_id": self.message_id,
            "url": self.url,
        }


@dataclass
class ScoredMessage:
    """A message with its importance verdict attached."""

    message: Message
    score: int
    reasons: list[str] = field(default_factory=list)

    @property
    def key(self) -> str:
        return self.message.key
