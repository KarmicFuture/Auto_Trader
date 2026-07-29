from __future__ import annotations

import re
import sys
from typing import Any, Iterable

from .models import Listing
from .sources import (
    fetch_autotrader_watch,
    fetch_bringatrailer_watch,
    fetch_carmax_watch,
    fetch_marketcheck_s2000,
    fetch_national_watch,
)
from .value_score import apply_value_score, rank_key
from .watches import WATCHES, Watch, get_watch

_DISTANCE_SUFFIX = re.compile(r"\s*\([^)]*\bmi\b[^)]*\)\s*$", re.I)


def _us_location(listing: Listing) -> Listing:
    """Drop ZIP-relative distances for nationwide board display."""
    if not listing.location:
        return listing
    cleaned = _DISTANCE_SUFFIX.sub("", listing.location).strip() or None
    if cleaned == listing.location:
        return listing
    return listing.with_updates(location=cleaned)


def _fetch_watch(
    watch: Watch,
    *,
    max_price: int | None,
    include_bringatrailer: bool,
    include_cars_com: bool,
    include_autotrader: bool,
) -> tuple[list[Listing], list[str]]:
    found: list[Listing] = []
    errors: list[str] = []

    if include_bringatrailer:
        try:
            found.extend(
                fetch_bringatrailer_watch(
                    watch,
                    include_completed=watch.bat_include_completed,
                    year_min=watch.year_min,
                    year_max=watch.year_max,
                    max_price=max_price,
                )
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{watch.id}/bringatrailer: {exc}")

    # AutoTempest national mash: Cars.com, eBay, Hemmings, CarGurus, TrueCar,
    # Cars & Bids, Carvana, and other AT codes when they return inventory.
    # Flag name remains include_cars_com for config compatibility.
    if include_cars_com and watch.include_dealer_sources:
        try:
            found.extend(
                fetch_national_watch(
                    watch,
                    zip_code="10001",
                    radius_miles=0,
                    year_min=watch.year_min,
                    year_max=watch.year_max,
                    max_price=max_price,
                    max_pages=5,
                )
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{watch.id}/national: {exc}")

        try:
            found.extend(
                fetch_carmax_watch(
                    watch,
                    zip_code="10001",
                    year_min=watch.year_min,
                    year_max=watch.year_max,
                    max_price=max_price,
                )
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{watch.id}/carmax: {exc}")

    if include_autotrader and watch.include_dealer_sources:
        try:
            found.extend(
                fetch_autotrader_watch(
                    watch,
                    zip_code="10001",
                    radius_miles=0,
                    year_min=watch.year_min,
                    year_max=watch.year_max,
                    max_price=max_price,
                )
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{watch.id}/autotrader: {exc}")

    scored = [
        apply_value_score(_us_location(listing), watch.id) for listing in found
    ]
    return scored, errors


def fetch_us_board_listings(
    *,
    watch_ids: Iterable[str] | None = None,
    max_price: int | None = None,
    include_bringatrailer: bool = True,
    include_cars_com: bool = True,
    include_autotrader: bool = True,
    include_marketcheck: bool = False,
    marketcheck_zip: str = "90210",
    marketcheck_radius: int = 100,
) -> tuple[list[Listing], list[str]]:
    """Fetch nationwide US listings for configured watches and score each car."""
    selected = []
    wanted = set(watch_ids) if watch_ids is not None else None
    for watch in WATCHES:
        if wanted is None or watch.id in wanted:
            selected.append(watch)

    found: list[Listing] = []
    errors: list[str] = []

    for watch in selected:
        batch, batch_errors = _fetch_watch(
            watch,
            max_price=max_price,
            include_bringatrailer=include_bringatrailer,
            include_cars_com=include_cars_com,
            include_autotrader=include_autotrader,
        )
        found.extend(batch)
        errors.extend(batch_errors)

    if include_marketcheck and (wanted is None or "honda-s2000" in wanted):
        try:
            s2k = get_watch("honda-s2000")
            assert s2k is not None
            market = fetch_marketcheck_s2000(
                zip_code=marketcheck_zip,
                radius_miles=marketcheck_radius,
                year_min=s2k.year_min,
                year_max=s2k.year_max,
                max_price=max_price,
            )
            found.extend(
                apply_value_score(_us_location(item.with_updates(watch_id=s2k.id)), s2k.id)
                for item in market
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"marketcheck: {exc}")

    for err in errors:
        print(f"Source warning: {err}", file=sys.stderr)

    by_url: dict[str, Listing] = {}
    for listing in found:
        by_url[listing.url] = listing

    listings = list(by_url.values())
    listings.sort(key=rank_key)
    return listings, errors


def fetch_us_s2000_listings(**kwargs) -> tuple[list[Listing], list[str]]:
    """Backward-compatible S2000-only fetch."""
    return fetch_us_board_listings(watch_ids=["honda-s2000"], **kwargs)


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
        "watches": [
            {"id": w.id, "label": w.label, "make": w.make, "model": w.model}
            for w in WATCHES
        ],
        "listings": [listing.to_dict() for listing in listings],
    }
