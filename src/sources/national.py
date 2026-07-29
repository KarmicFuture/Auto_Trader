from __future__ import annotations

from typing import Optional

from ..models import Listing
from ..watches import Watch, get_watch
from .autotempest import NATIONAL_SITE_CODES, AutoTempestClient


def fetch_national_watch(
    watch: Watch,
    *,
    zip_code: str = "",
    radius_miles: Optional[int] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    max_price: Optional[int] = None,
    max_pages: int = 5,
    site_codes: tuple[str, ...] | list[str] | None = None,
    exclude_site_codes: set[str] | None = None,
) -> list[Listing]:
    """Pull nationwide listings from popular AutoTempest-backed marketplaces.

    Includes Cars.com, eBay, Hemmings, CarGurus, TrueCar, Cars & Bids, Carvana,
    and other AutoTempest mash codes when they return inventory.
    """
    client = AutoTempestClient()
    radius = 0 if radius_miles is None else radius_miles
    listings = client.fetch_national_listings(
        make=watch.make_slug,
        model=watch.model_slug,
        zip_code=zip_code or "10001",
        radius_miles=radius,
        year_min=year_min if year_min is not None else watch.year_min,
        year_max=year_max if year_max is not None else watch.year_max,
        max_price=max_price,
        max_pages=max_pages,
        site_codes=site_codes or NATIONAL_SITE_CODES,
        exclude_site_codes=exclude_site_codes,
    )
    return [
        listing.with_updates(make=watch.make, model=watch.model, watch_id=watch.id)
        for listing in listings
    ]


def fetch_national_s2000(**kwargs) -> list[Listing]:
    watch = get_watch("honda-s2000")
    assert watch is not None
    return fetch_national_watch(watch, **kwargs)
