from __future__ import annotations

from typing import Optional

from ..models import Listing
from .autotempest import AutoTempestClient


def fetch_cars_com_s2000(
    *,
    zip_code: str = "",
    radius_miles: Optional[int] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    max_price: Optional[int] = None,
    max_pages: int = 3,
) -> list[Listing]:
    """Fetch Honda S2000 listings from Cars.com via AutoTempest.

    Direct cars.com requests are Cloudflare-blocked from most cloud IPs.
    AutoTempest's Cars.com feed (`sites=cm`) returns the same inventory.
    Pass radius_miles=None (or 0) for nationwide.
    """
    client = AutoTempestClient()
    radius = radius_miles
    if radius is None:
        radius = 0
    return client.fetch_site_listings(
        site_code="cm",
        source_name="cars.com",
        zip_code=zip_code or "10001",
        radius_miles=radius,
        year_min=year_min,
        year_max=year_max,
        max_price=max_price,
        max_pages=max_pages,
    )
