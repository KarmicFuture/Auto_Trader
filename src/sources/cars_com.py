from __future__ import annotations

from typing import Optional

from ..models import Listing
from ..watches import Watch, get_watch
from .national import fetch_national_watch


def fetch_cars_com_watch(
    watch: Watch,
    *,
    zip_code: str = "",
    radius_miles: Optional[int] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    max_price: Optional[int] = None,
    max_pages: int = 3,
) -> list[Listing]:
    """Fetch Cars.com via AutoTempest (kept for backward-compatible callers)."""
    return [
        listing
        for listing in fetch_national_watch(
            watch,
            zip_code=zip_code,
            radius_miles=radius_miles,
            year_min=year_min,
            year_max=year_max,
            max_price=max_price,
            max_pages=max_pages,
            site_codes=("cm",),
        )
        if listing.source == "cars.com"
    ]


def fetch_cars_com_s2000(**kwargs) -> list[Listing]:
    watch = get_watch("honda-s2000")
    assert watch is not None
    return fetch_cars_com_watch(watch, **kwargs)
