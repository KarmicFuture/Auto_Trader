from __future__ import annotations

from typing import Optional

from ..models import Listing
from ..watches import Watch, get_watch
from .autotempest import AutoTempestClient


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
    client = AutoTempestClient()
    radius = 0 if radius_miles is None else radius_miles
    listings = client.fetch_site_listings(
        site_code="cm",
        source_name="cars.com",
        make=watch.make_slug,
        model=watch.model_slug,
        zip_code=zip_code or "10001",
        radius_miles=radius,
        year_min=year_min if year_min is not None else watch.year_min,
        year_max=year_max if year_max is not None else watch.year_max,
        max_price=max_price,
        max_pages=max_pages,
    )
    return [
        listing.with_updates(make=watch.make, model=watch.model, watch_id=watch.id)
        for listing in listings
    ]


def fetch_cars_com_s2000(**kwargs) -> list[Listing]:
    watch = get_watch("honda-s2000")
    assert watch is not None
    return fetch_cars_com_watch(watch, **kwargs)
