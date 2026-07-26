from __future__ import annotations

import re
import sys
from typing import Any

from .models import Listing
from .sources import (
    fetch_autotrader_s2000,
    fetch_bringatrailer_s2000,
    fetch_cars_com_s2000,
    fetch_marketcheck_s2000,
)

_DISTANCE_SUFFIX = re.compile(r"\s*\([^)]*\bmi\b[^)]*\)\s*$", re.I)


def _us_location(listing: Listing) -> Listing:
    """Drop ZIP-relative distances for nationwide board display."""
    if not listing.location:
        return listing
    cleaned = _DISTANCE_SUFFIX.sub("", listing.location).strip() or None
    if cleaned == listing.location:
        return listing
    return Listing(
        id=listing.id,
        source=listing.source,
        title=listing.title,
        url=listing.url,
        price=listing.price,
        year=listing.year,
        mileage=listing.mileage,
        location=cleaned,
        status=listing.status,
        thumbnail=listing.thumbnail,
        notes=listing.notes,
    )


def fetch_us_s2000_listings(
    *,
    year_min: int = 1999,
    year_max: int = 2009,
    max_price: int | None = None,
    include_bringatrailer: bool = True,
    include_cars_com: bool = True,
    include_autotrader: bool = True,
    include_marketcheck: bool = False,
    marketcheck_zip: str = "90210",
    marketcheck_radius: int = 100,
) -> tuple[list[Listing], list[str]]:
    """Fetch Honda S2000s for sale across the United States.

    Cars.com / Autotrader use nationwide search (no ZIP radius).
    Bring a Trailer is included as live US auction inventory.
    """
    found: list[Listing] = []
    errors: list[str] = []

    if include_bringatrailer:
        try:
            found.extend(
                fetch_bringatrailer_s2000(
                    include_completed=False,
                    year_min=year_min,
                    year_max=year_max,
                    max_price=max_price,
                )
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"bringatrailer: {exc}")

    if include_cars_com:
        try:
            found.extend(
                fetch_cars_com_s2000(
                    zip_code="10001",
                    radius_miles=0,  # AutoTempest nationwide
                    year_min=year_min,
                    year_max=year_max,
                    max_price=max_price,
                    max_pages=5,
                )
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"cars.com: {exc}")

    if include_autotrader:
        try:
            found.extend(
                fetch_autotrader_s2000(
                    zip_code="10001",
                    radius_miles=0,
                    year_min=year_min,
                    year_max=year_max,
                    max_price=max_price,
                )
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"autotrader: {exc}")

    if include_marketcheck:
        try:
            found.extend(
                fetch_marketcheck_s2000(
                    zip_code=marketcheck_zip,
                    radius_miles=marketcheck_radius,
                    year_min=year_min,
                    year_max=year_max,
                    max_price=max_price,
                )
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"marketcheck: {exc}")

    for err in errors:
        print(f"Source warning: {err}", file=sys.stderr)

    by_url: dict[str, Listing] = {}
    for listing in found:
        by_url[listing.url] = _us_location(listing)

    listings = list(by_url.values())
    listings.sort(
        key=lambda item: (
            item.price is None,
            item.price if item.price is not None else 10**9,
            item.title,
        )
    )
    return listings, errors


def listings_payload(
    listings: list[Listing],
    *,
    errors: list[str] | None = None,
    refreshed_at: str | None = None,
) -> dict[str, Any]:
    return {
        "count": len(listings),
        "refreshed_at": refreshed_at,
        "errors": errors or [],
        "listings": [listing.to_dict() for listing in listings],
    }
