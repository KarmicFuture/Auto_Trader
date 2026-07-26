from __future__ import annotations

import json
import re
import sys
from typing import Any, Optional
from urllib import parse, request

from ..models import Listing
from ..watches import Watch, get_watch

SEARCH_URL = "https://www.autotrader.com/rest/searchresults/base"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


def _parse_mileage(listing: dict[str, Any]) -> Optional[int]:
    specs = listing.get("specifications") or {}
    mileage = specs.get("mileage") or {}
    raw = mileage.get("value") if isinstance(mileage, dict) else mileage
    if raw is None:
        return listing.get("mileage")
    text = str(raw).replace(",", "")
    m = re.search(r"(\d+)", text)
    return int(m.group(1)) if m else None


def _to_listing(item: dict[str, Any], *, watch: Watch) -> Listing | None:
    listing_id = str(item.get("id") or item.get("listingId") or "")
    year = item.get("year")
    make = item.get("make") or watch.make
    model = item.get("model") or watch.model
    title = (item.get("title") or f"{year or ''} {make} {model}").strip()
    if not listing_id:
        return None

    url = item.get("websiteHybridDetailUrl") or item.get("vdpUrl") or item.get("url")
    if not url:
        url = (
            "https://www.autotrader.com/cars-for-sale/vehicledetails.xhtml"
            f"?listingId={listing_id}"
        )
    if url.startswith("/"):
        url = "https://www.autotrader.com" + url
    if "listingId=" not in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}listingId={listing_id}"

    pricing = item.get("pricingDetail") or {}
    price = (
        pricing.get("primary")
        or pricing.get("salePrice")
        or pricing.get("askPrice")
        or item.get("price")
    )
    try:
        price_i = int(price) if price is not None else None
    except (TypeError, ValueError):
        price_i = None

    owner = item.get("owner") or {}
    city = owner.get("city")
    state = owner.get("state")
    location = ", ".join(p for p in (city, state) if p) or None

    images = item.get("images") or []
    thumb = None
    if images:
        first = images[0]
        thumb = first.get("src") if isinstance(first, dict) else str(first)

    return Listing(
        id=listing_id,
        source="autotrader",
        title=title,
        url=url,
        price=price_i,
        year=int(year) if year is not None else None,
        mileage=_parse_mileage(item),
        location=location,
        status="active",
        thumbnail=thumb,
        notes=owner.get("name"),
        make=make,
        model=model,
        watch_id=watch.id,
    )


def _http_get_json(url: str, headers: dict[str, str]) -> dict[str, Any]:
    req = request.Request(url, headers=headers)
    with request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _fetch_via_curl_cffi(url: str, headers: dict[str, str]) -> dict[str, Any]:
    from curl_cffi import requests as crequests

    resp = crequests.get(url, headers=headers, impersonate="chrome131", timeout=60)
    if resp.status_code >= 400:
        raise RuntimeError(f"Autotrader HTTP {resp.status_code}")
    ctype = resp.headers.get("content-type", "")
    if "json" not in ctype and not resp.text.strip().startswith("{"):
        raise RuntimeError(
            "Autotrader returned a non-JSON response (likely IP/geo blocked)"
        )
    return resp.json()


def fetch_autotrader_watch(
    watch: Watch,
    *,
    zip_code: str = "",
    radius_miles: Optional[int] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    max_price: Optional[int] = None,
    max_records: int = 100,
) -> list[Listing]:
    zip_code = zip_code or "10001"
    if radius_miles is None or radius_miles == 0:
        search_radius = 0
        market_extension = "include"
    else:
        search_radius = int(radius_miles)
        market_extension = "include"

    y_min = year_min if year_min is not None else watch.year_min
    y_max = year_max if year_max is not None else watch.year_max

    params = {
        "zip": zip_code,
        "makeCodeList": watch.autotrader_make,
        "modelCodeList": watch.autotrader_model,
        "marketExtension": market_extension,
        "searchRadius": str(search_radius),
        "sortBy": "relevance",
        "numRecords": str(min(max_records, 100)),
        "firstRecord": "0",
        "startYear": str(y_min),
        "endYear": str(y_max),
        "channel": "ATC",
    }
    if max_price is not None:
        params["maxPrice"] = str(max_price)

    url = f"{SEARCH_URL}?{parse.urlencode(params)}"
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": (
            f"https://www.autotrader.com/cars-for-sale/all-cars/"
            f"{watch.make_slug}/{watch.model_slug}"
            f"?zip={zip_code}&searchRadius={search_radius}"
        ),
        "Cache-Control": "no-cache",
    }

    data: dict[str, Any] | None = None
    errors: list[str] = []

    try:
        data = _fetch_via_curl_cffi(url, headers)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"curl_cffi: {exc}")

    if data is None:
        try:
            data = _http_get_json(url, headers)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"urllib: {exc}")

    if data is None:
        print(
            f"Autotrader ({watch.id}) skipped (blocked or unavailable): "
            + "; ".join(errors),
            file=sys.stderr,
        )
        return []

    raw = data.get("listings") or data.get("results") or []
    out: list[Listing] = []
    for item in raw:
        listing = _to_listing(item, watch=watch)
        if listing is None:
            continue
        if y_min is not None and listing.year is not None and listing.year < y_min:
            continue
        if y_max is not None and listing.year is not None and listing.year > y_max:
            continue
        if max_price is not None and listing.price is not None and listing.price > max_price:
            continue
        out.append(listing)
    return out


def fetch_autotrader_s2000(**kwargs) -> list[Listing]:
    watch = get_watch("honda-s2000")
    assert watch is not None
    return fetch_autotrader_watch(watch, **kwargs)
