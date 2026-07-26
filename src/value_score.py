"""Independent fair-value / value-score model.

Each car is scored from its own attributes (year, mileage, trim cues, ask price)
against a static market anchor curve — not against other listings currently online.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Optional

from .models import Listing


@dataclass(frozen=True)
class ValueResult:
    fair_value: Optional[int]
    value_score: Optional[float]
    value_label: Optional[str]
    value_delta: Optional[int]


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _detect_s2000_anchor(title: str, year: Optional[int]) -> tuple[int, str]:
    text = title.lower()
    if " cr" in f" {text}" or "club racer" in text:
        return 95_000, "S2000 CR"
    if year is not None and year >= 2004:
        return 34_000, "S2000 AP2"
    return 29_000, "S2000 AP1"


def _detect_cayman_anchor(title: str, year: Optional[int]) -> tuple[int, str]:
    text = title.lower()
    if "gt4 rs" in text:
        return 175_000, "Cayman GT4 RS"
    if "gt4" in text:
        return 105_000, "Cayman GT4"
    if "gts 4.0" in text or "gts4.0" in text:
        return 95_000, "Cayman GTS 4.0"
    if "gts" in text:
        premium = 12_000
    elif re.search(r"\bs\b", text) or "cayman s" in text:
        premium = 6_000
    else:
        premium = 0

    if year is None:
        return 38_000 + premium, "Cayman"
    if year >= 2017:  # 718
        return 52_000 + premium, "718 Cayman"
    if year >= 2013:  # 981
        return 42_000 + premium, "981 Cayman"
    if year >= 2009:  # 987.2
        return 33_000 + premium, "987.2 Cayman"
    return 27_000 + premium, "987.1 Cayman"


def estimate_fair_value(
    *,
    watch_id: str,
    title: str,
    year: Optional[int],
    mileage: Optional[int],
) -> tuple[Optional[int], str]:
    """Return (fair_value_usd, trim_label) from independent anchors."""
    if watch_id == "honda-s2000":
        base, label = _detect_s2000_anchor(title, year)
        # ~$180 / 1k miles around a 60k-mile clean reference
        miles = mileage if mileage is not None else 60_000
        fair = base - ((miles - 60_000) / 1000.0) * 180.0
        if year is not None:
            # Mild year preference within generation
            if year >= 2004:
                fair += (year - 2004) * 400
            else:
                fair += (year - 1999) * 250
        return max(12_000, int(round(fair / 100.0) * 100)), label

    if watch_id == "porsche-cayman":
        base, label = _detect_cayman_anchor(title, year)
        miles = mileage if mileage is not None else 45_000
        # Newer cars depreciate faster per mile
        per_k = 220.0 if (year or 0) >= 2017 else 160.0
        fair = base - ((miles - 45_000) / 1000.0) * per_k
        if year is not None:
            # Cap model-year drift so brand-new cars don't runaway vs ask noise
            fair += max(-6_000, min(6_000, (year - 2012) * 700))
        return max(14_000, int(round(fair / 100.0) * 100)), label

    return None, "Unknown"


def score_value(ask: Optional[int], fair: Optional[int]) -> ValueResult:
    if ask is None or fair is None or fair <= 0:
        return ValueResult(fair_value=fair, value_score=None, value_label=None, value_delta=None)

    delta = ask - fair
    # 0% delta => 50. ±30% of fair maps roughly to 0..100.
    pct = delta / fair
    score = _clamp(50.0 - (pct / 0.30) * 50.0, 0.0, 100.0)
    score = round(score, 1)

    if score >= 80:
        label = "Great value"
    elif score >= 65:
        label = "Good value"
    elif score >= 45:
        label = "Fair value"
    elif score >= 30:
        label = "Soft value"
    else:
        label = "Stretched"

    return ValueResult(
        fair_value=fair,
        value_score=score,
        value_label=label,
        value_delta=int(delta),
    )


def apply_value_score(listing: Listing, watch_id: str) -> Listing:
    fair, _trim = estimate_fair_value(
        watch_id=watch_id,
        title=listing.title,
        year=listing.year,
        mileage=listing.mileage,
    )
    result = score_value(listing.price, fair)
    return listing.with_updates(
        watch_id=watch_id,
        fair_value=result.fair_value,
        value_score=result.value_score,
        value_label=result.value_label,
        value_delta=result.value_delta,
    )


def rank_key(listing: Listing) -> tuple:
    """Sort best independent value first, then cheaper asks."""
    score = listing.value_score
    return (
        score is None,
        -(score if score is not None else -1.0),
        listing.price is None,
        listing.price if listing.price is not None else 10**9,
        listing.title,
    )
