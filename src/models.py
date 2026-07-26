from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any, Optional


@dataclass(frozen=True)
class Listing:
    """Normalized car listing from any source."""

    id: str
    source: str
    title: str
    url: str
    price: Optional[int] = None
    year: Optional[int] = None
    mileage: Optional[int] = None
    location: Optional[str] = None
    status: Optional[str] = None  # e.g. live, completed, active
    thumbnail: Optional[str] = None
    notes: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    watch_id: Optional[str] = None
    # Independent value model (not relative to other current listings)
    fair_value: Optional[int] = None
    value_score: Optional[float] = None
    value_label: Optional[str] = None
    value_delta: Optional[int] = None  # ask - fair (negative = under fair)

    @property
    def key(self) -> str:
        return f"{self.source}:{self.id}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def with_updates(self, **kwargs: Any) -> "Listing":
        return replace(self, **kwargs)

    def price_label(self) -> str:
        if self.price is None:
            return "Price n/a"
        return f"${self.price:,}"

    def summary_line(self) -> str:
        bits = [self.title, self.price_label()]
        if self.value_score is not None:
            bits.append(f"value {self.value_score:.0f}")
        if self.mileage is not None:
            bits.append(f"{self.mileage:,} mi")
        if self.location:
            bits.append(self.location)
        if self.status:
            bits.append(self.status)
        bits.append(f"[{self.source}]")
        return " · ".join(bits)
