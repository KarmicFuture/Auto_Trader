from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Optional
from urllib import error, parse, request

from ..models import Listing

# Client-side token salt extracted from AutoTempest's frontend bundle.
# Token = sha256(decodeURIComponent(jQuery.param(params)) + TOKEN_SALT)
TOKEN_SALT = "d8007486d73c168684860aae427ea1f9d74e502b06d94609691f5f4f2704a07f"
QUEUE_URL = "https://www.autotempest.com/queue-results"
WARM_URL = "https://www.autotempest.com/results"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

SITE_CODES = {
    "cars.com": "cm",
    "autotrader": "at",
}


def _jquery_param(params: dict[str, Any]) -> str:
    """Match jQuery.param encoding used by AutoTempest."""
    parts: list[str] = []
    for key, value in params.items():
        ek = parse.quote(str(key), safe="-_.!~*()")
        ev = parse.quote("" if value is None else str(value), safe="-_.!~*()").replace(
            "%20", "+"
        )
        parts.append(f"{ek}={ev}")
    return "&".join(parts)


def _token_for(params: dict[str, Any]) -> str:
    serialized = _jquery_param(params)
    decoded = parse.unquote(serialized.replace("+", "%20"))
    return hashlib.sha256((decoded + TOKEN_SALT).encode("utf-8")).hexdigest()


def _parse_price(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value)
    m = re.search(r"([\d,]+)", text.replace("$", ""))
    if not m:
        return None
    return int(m.group(1).replace(",", ""))


def _parse_mileage(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    text = str(value).replace(",", "")
    m = re.search(r"(\d+)", text)
    return int(m.group(1)) if m else None


def _parse_year(value: Any, title: str = "") -> Optional[int]:
    if value is not None:
        try:
            return int(value)
        except (TypeError, ValueError):
            pass
    m = re.search(r"\b(19\d{2}|20\d{2})\b", title)
    return int(m.group(1)) if m else None


def _clean_url(url: str) -> str:
    """Strip AutoTempest affiliate tracking for a stable listing identity."""
    if not url:
        return url
    parts = parse.urlsplit(url)
    return parse.urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


class AutoTempestClient:
    """Minimal AutoTempest search client (Cars.com + other mash sources)."""

    def __init__(self) -> None:
        self._cookie_processor = request.HTTPCookieProcessor()
        self._opener = request.build_opener(self._cookie_processor)
        self._warmed = False

    def warm(self, *, make: str, model: str, zip_code: str, radius: int) -> None:
        if self._warmed:
            return
        query = parse.urlencode(
            {"make": make, "model": model, "zip": zip_code, "radius": radius}
        )
        req = request.Request(
            f"{WARM_URL}?{query}",
            headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
        )
        with self._opener.open(req, timeout=45) as resp:
            resp.read(2048)
        self._warmed = True

    def queue_results(
        self,
        *,
        make: str,
        model: str,
        zip_code: str,
        radius: int,
        sites: str,
        rpp: int = 50,
        search_after: list[Any] | None = None,
    ) -> dict[str, Any]:
        self.warm(make=make, model=model, zip_code=zip_code, radius=radius)
        params: dict[str, Any] = {
            "make": make.lower(),
            "model": model.lower(),
            "radius": str(radius),
            "originalradius": str(radius),
            "zip": zip_code,
            "sort": "best_match",
            "sites": sites,
            "deduplicationSites": sites,
            "rpp": str(rpp),
        }
        if search_after:
            params["searchAfter"] = json.dumps(search_after, separators=(",", ":"))
        params["token"] = _token_for(params)
        url = f"{QUEUE_URL}?{_jquery_param(params)}"
        req = request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"{WARM_URL}?make={make}&model={model}&zip={zip_code}",
            },
        )
        try:
            with self._opener.open(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            raise RuntimeError(f"AutoTempest HTTP {exc.code} for sites={sites}") from exc

    def fetch_site_listings(
        self,
        *,
        site_code: str,
        source_name: str,
        make: str = "honda",
        model: str = "s2000",
        zip_code: str = "10001",
        radius_miles: int | None = None,
        year_min: int | None = None,
        year_max: int | None = None,
        max_price: int | None = None,
        max_pages: int = 3,
    ) -> list[Listing]:
        """Fetch listings for one AutoTempest site code (e.g. cm=Cars.com)."""
        # AutoTempest: radius 0 ≈ nationwide. Positive radius = miles from ZIP.
        radius = 0 if radius_miles is None else int(radius_miles)
        zip_code = zip_code or "10001"

        out: list[Listing] = []
        seen_ids: set[str] = set()
        search_after: list[Any] | None = None

        for _ in range(max_pages):
            data = self.queue_results(
                make=make,
                model=model,
                zip_code=zip_code,
                radius=radius,
                sites=site_code,
                rpp=50,
                search_after=search_after,
            )
            if data.get("errors"):
                raise RuntimeError(f"AutoTempest errors: {data['errors']}")

            batch = data.get("results") or []
            if not batch:
                break

            for item in batch:
                listing = self._to_listing(item, source_name=source_name)
                if listing is None or listing.id in seen_ids:
                    continue
                if year_min is not None and listing.year is not None and listing.year < year_min:
                    continue
                if year_max is not None and listing.year is not None and listing.year > year_max:
                    continue
                if (
                    max_price is not None
                    and listing.price is not None
                    and listing.price > max_price
                ):
                    continue
                seen_ids.add(listing.id)
                out.append(listing)

            next_after = data.get("searchAfter")
            # status 1 => last page for this radius bucket; status 0 may continue
            if not next_after or data.get("status") == 1 or next_after == search_after:
                break
            search_after = next_after

        return out

    @staticmethod
    def _to_listing(item: dict[str, Any], *, source_name: str) -> Listing | None:
        url = item.get("url") or ""
        title = (item.get("title") or "").strip()
        listing_id = str(item.get("id") or item.get("externalId") or "")
        if not url or not title or not listing_id:
            return None
        # Prefer canonical marketplace URL without affiliate junk.
        clean = _clean_url(url)
        distance = item.get("distance")
        location = item.get("location")
        if distance is not None and location:
            location = f"{location} ({distance} mi)"
        notes_parts = [
            p
            for p in (
                item.get("dealerName"),
                item.get("detailsShort"),
                item.get("detailsMid"),
                item.get("detailsLong"),
            )
            if p
        ]
        return Listing(
            id=listing_id,
            source=source_name,
            title=title,
            url=clean,
            price=_parse_price(item.get("price")),
            year=_parse_year(item.get("year"), title),
            mileage=_parse_mileage(item.get("mileage")),
            location=location,
            status="active",
            thumbnail=item.get("imgSource") or item.get("img"),
            notes=" ".join(notes_parts)[:240] or None,
        )
