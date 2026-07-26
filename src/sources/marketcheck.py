from __future__ import annotations

import os
from typing import Any, Optional
from urllib.parse import urlencode
from urllib import request
import json

from ..models import Listing

API_URL = "https://api.marketcheck.com/v2/search/car/active"


def _get_json(url: str) -> dict[str, Any]:
    req = request.Request(
        url,
        headers={
            "User-Agent": "Auto_Trader/1.0",
            "Accept": "application/json",
        },
    )
    with request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_marketcheck_s2000(
    *,
    zip_code: str,
    radius_miles: int = 100,
    year_min: int = 1999,
    year_max: int = 2009,
    max_price: Optional[int] = None,
    api_key: Optional[str] = None,
    rows: int = 50,
) -> list[Listing]:
    """Fetch nearby dealer S2000 inventory via MarketCheck (requires API key)."""
    key = api_key or os.getenv("MARKETCHECK_API_KEY")
    if not key:
        raise RuntimeError(
            "MARKETCHECK_API_KEY is required when sources.marketcheck is enabled"
        )
    if not zip_code:
        raise RuntimeError("watch.zip is required for MarketCheck nearby search")

    params: dict[str, Any] = {
        "api_key": key,
        "make": "Honda",
        "model": "S2000",
        "car_type": "used",
        "zip": zip_code,
        "radius": radius_miles,
        "year_range": f"{year_min}-{year_max}",
        "rows": min(rows, 50),
        "start": 0,
    }
    if max_price is not None:
        params["price_range"] = f"0-{max_price}"

    url = f"{API_URL}?{urlencode(params)}"
    data = _get_json(url)
    listings_raw = data.get("listings") or []
    out: list[Listing] = []
    for item in listings_raw:
        build = item.get("build") or {}
        dealer = item.get("dealer") or {}
        media = item.get("media") or {}
        listing_id = str(item.get("id") or item.get("vin") or item.get("heading"))
        heading = item.get("heading") or (
            f"{build.get('year', '')} Honda S2000".strip()
        )
        link = item.get("vdp_url") or item.get("inventory_url") or ""
        if not link:
            continue
        city = dealer.get("city")
        state = dealer.get("state")
        location = ", ".join(p for p in (city, state) if p) or None
        photos = media.get("photo_links") or []
        out.append(
            Listing(
                id=listing_id,
                source="marketcheck",
                title=heading,
                url=link,
                price=item.get("price"),
                year=build.get("year") or item.get("year"),
                mileage=item.get("miles") or item.get("odometer"),
                location=location,
                status="active",
                thumbnail=photos[0] if photos else None,
                notes=dealer.get("name"),
            )
        )
    return out
