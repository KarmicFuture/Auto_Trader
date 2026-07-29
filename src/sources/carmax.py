from __future__ import annotations

import sys
from typing import Any, Optional
from urllib import parse

from ..models import Listing
from ..watches import Watch, get_watch

SEARCH_URL = "https://www.carmax.com/cars/api/search/run"
HOME_URL = "https://www.carmax.com/cars"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# Extra CarMax path segments when a watch spans multiple catalog models.
# Cayman inventory is split between classic "cayman" and modern "718-cayman".
MODEL_PATH_ALIASES: dict[str, tuple[str, ...]] = {
    "cayman": ("cayman", "718-cayman"),
}


def _model_paths(model_slug: str) -> tuple[str, ...]:
    return MODEL_PATH_ALIASES.get(model_slug, (model_slug,))


def _normalize(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _model_matches(item_model: str | None, *, wanted: str) -> bool:
    """True when CarMax model text matches the watched model (e.g. 718 Cayman)."""
    if not item_model:
        return False
    got = _normalize(item_model)
    needle = _normalize(wanted)
    if not needle:
        return False
    return needle in got or got in needle


def _facet_has_model(facets: list[dict[str, Any]], *, model_slug: str) -> bool:
    """CarMax broadens to make-only when a model has no inventory; detect that."""
    wanted = {_normalize(p) for p in _model_paths(model_slug)}
    wanted.add(_normalize(model_slug))
    for facet in facets:
        if (facet.get("name") or "").lower() != "model":
            continue
        value = _normalize(str(facet.get("value") or ""))
        display = _normalize(str(facet.get("display") or ""))
        if value in wanted or display in wanted:
            return True
        if any(w and (w in value or w in display or value in w) for w in wanted):
            return True
    return False


def _to_listing(item: dict[str, Any], *, watch: Watch) -> Listing | None:
    stock = item.get("stockNumber")
    if stock is None:
        return None
    listing_id = str(stock)
    year = item.get("year")
    make = item.get("make") or watch.make
    model = item.get("model") or watch.model
    trim = (item.get("trim") or "").strip()
    title = f"{year or ''} {make} {model}".strip()
    if trim:
        title = f"{title} {trim}"

    price = item.get("basePrice")
    try:
        price_i = int(price) if price is not None else None
    except (TypeError, ValueError):
        price_i = None

    mileage = item.get("mileage")
    try:
        mileage_i = int(mileage) if mileage is not None else None
    except (TypeError, ValueError):
        mileage_i = None

    city = item.get("storeCity")
    state = item.get("stateAbbreviation") or item.get("state")
    location = ", ".join(p for p in (city, state) if p) or None

    thumb = item.get("heroImageUrl") or item.get("heroThumbnailImageUrl")
    store = item.get("storeName")

    return Listing(
        id=listing_id,
        source="carmax",
        title=title,
        url=f"https://www.carmax.com/car/{listing_id}",
        price=price_i,
        year=int(year) if year is not None else None,
        mileage=mileage_i,
        location=location,
        status="active",
        thumbnail=thumb,
        notes=store,
        make=make,
        model=model,
        watch_id=watch.id,
    )


def _fetch_page(session: Any, *, uri: str, zip_code: str, skip: int, take: int) -> dict[str, Any]:
    params = {
        "uri": uri,
        "skip": str(skip),
        "take": str(take),
        "zipCode": zip_code,
        "radius": "radius-nationwide",
        "shipping": "-1",
        "sort": "bestmatch",
    }
    url = f"{SEARCH_URL}?{parse.urlencode(params)}"
    resp = session.get(
        url,
        headers={
            "Accept": "application/json, text/plain, */*",
            "Referer": f"https://www.carmax.com{uri}",
            "User-Agent": USER_AGENT,
        },
        timeout=60,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"CarMax HTTP {resp.status_code}")
    ctype = resp.headers.get("content-type", "")
    if "json" not in ctype and not resp.text.strip().startswith("{"):
        raise RuntimeError("CarMax returned a non-JSON response (likely blocked)")
    return resp.json()


def fetch_carmax_watch(
    watch: Watch,
    *,
    zip_code: str = "",
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    max_price: Optional[int] = None,
    max_pages: int = 5,
    page_size: int = 24,
) -> list[Listing]:
    """Fetch nationwide CarMax inventory for a watch via the site search API."""
    from curl_cffi import requests as crequests

    zip_code = zip_code or "10001"
    y_min = year_min if year_min is not None else watch.year_min
    y_max = year_max if year_max is not None else watch.year_max

    session = crequests.Session(impersonate="chrome131")
    try:
        warm = session.get(
            HOME_URL,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
            timeout=45,
        )
        if warm.status_code >= 400:
            print(
                f"CarMax ({watch.id}) skipped (warm HTTP {warm.status_code})",
                file=sys.stderr,
            )
            return []
    except Exception as exc:  # noqa: BLE001
        print(f"CarMax ({watch.id}) skipped: {exc}", file=sys.stderr)
        return []

    out: list[Listing] = []
    seen_ids: set[str] = set()

    for model_path in _model_paths(watch.model_slug):
        uri = f"/cars/{watch.make_slug}/{model_path}"
        try:
            first = _fetch_page(
                session, uri=uri, zip_code=zip_code, skip=0, take=page_size
            )
        except Exception as exc:  # noqa: BLE001
            print(f"CarMax ({watch.id}/{model_path}) skipped: {exc}", file=sys.stderr)
            continue

        facets = first.get("selectedFacets") or []
        if not _facet_has_model(facets, model_slug=watch.model_slug):
            # No inventory for this model — CarMax falls back to make-wide results.
            continue

        pages = [first]
        total = int(first.get("totalCount") or 0)
        for page_idx in range(1, max_pages):
            skip = page_idx * page_size
            if skip >= total:
                break
            try:
                pages.append(
                    _fetch_page(
                        session,
                        uri=uri,
                        zip_code=zip_code,
                        skip=skip,
                        take=page_size,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                print(
                    f"CarMax ({watch.id}/{model_path}) page {page_idx} skipped: {exc}",
                    file=sys.stderr,
                )
                break

        for data in pages:
            for item in data.get("items") or []:
                item_model = item.get("model")
                if not (
                    _model_matches(item_model, wanted=watch.model)
                    or any(
                        _model_matches(item_model, wanted=p.replace("-", " "))
                        for p in _model_paths(watch.model_slug)
                    )
                ):
                    continue
                listing = _to_listing(item, watch=watch)
                if listing is None or listing.id in seen_ids:
                    continue
                if y_min is not None and listing.year is not None and listing.year < y_min:
                    continue
                if y_max is not None and listing.year is not None and listing.year > y_max:
                    continue
                if (
                    max_price is not None
                    and listing.price is not None
                    and listing.price > max_price
                ):
                    continue
                seen_ids.add(listing.id)
                out.append(
                    listing.with_updates(
                        make=watch.make, model=watch.model, watch_id=watch.id
                    )
                )

    return out


def fetch_carmax_s2000(**kwargs) -> list[Listing]:
    watch = get_watch("honda-s2000")
    assert watch is not None
    return fetch_carmax_watch(watch, **kwargs)
