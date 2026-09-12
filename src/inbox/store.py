from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

from .models import ScoredMessage

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "inbox_seen.json"
RETENTION_DAYS = 30


class InboxSeenStore:
    """Persists alerted message keys so each conversation only alerts once."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path(os.getenv("INBOX_SEEN_PATH", str(DEFAULT_PATH)))
        self._seen: dict[str, str] = {}  # key -> ISO timestamp when alerted
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        raw = json.loads(self.path.read_text())
        if isinstance(raw, dict):
            self._seen = dict(raw.get("seen", {}))

    def save(self) -> None:
        self._prune()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"seen": self._seen}, indent=2, sort_keys=True) + "\n"
        )

    def _prune(self) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
        kept: dict[str, str] = {}
        for key, ts in self._seen.items():
            try:
                if datetime.fromisoformat(ts) >= cutoff:
                    kept[key] = ts
            except ValueError:
                continue
        self._seen = kept

    def is_new(self, scored: ScoredMessage) -> bool:
        return scored.key not in self._seen

    def mark_seen(self, items: Iterable[ScoredMessage]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        for item in items:
            self._seen[item.key] = now

    @property
    def count(self) -> int:
        return len(self._seen)
