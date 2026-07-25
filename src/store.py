from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .models import Listing

DEFAULT_SEEN_PATH = Path(__file__).resolve().parents[1] / "data" / "seen.json"


class SeenStore:
    """Persists listing keys so we only alert once per listing."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path(
            __import__("os").getenv("SEEN_PATH", str(DEFAULT_SEEN_PATH))
        )
        self._seen: set[str] = set()
        self._listings: dict[str, dict] = {}
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        raw = json.loads(self.path.read_text())
        if isinstance(raw, list):
            self._seen = set(raw)
            return
        self._seen = set(raw.get("seen", []))
        self._listings = dict(raw.get("listings", {}))

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "seen": sorted(self._seen),
            "listings": self._listings,
        }
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    def is_new(self, listing: Listing) -> bool:
        return listing.key not in self._seen

    def mark_seen(self, listings: Iterable[Listing]) -> None:
        for listing in listings:
            self._seen.add(listing.key)
            self._listings[listing.key] = listing.to_dict()

    @property
    def count(self) -> int:
        return len(self._seen)
