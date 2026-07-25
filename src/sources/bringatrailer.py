from __future__ import annotations

import json
import re
from typing import Optional
from urllib import request

from bs4 import BeautifulSoup

from ..models import Listing

BAT_S2000_URL = "https://bringatrailer.com/honda/s2000/"
USER_AGENT = "Auto_Trader/1.0 (+https://github.com/KarmicFuture/Auto_Trader)"


def _http_get(url: str) -> str:
    req = request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    with request.urlopen(req, timeout=45) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _parse_price(text: Optional[str]) -> Optional[int]:
    if not text:
        return None
    m = re.search(r"([\d,]+)", text.replace("USD", ""))
    if not m:
        return None
    return int(m.group(1).replace(",", ""))


def _parse_year(title: str) -> Optional[int]:
    m = re.search(r"\b(19\d{2}|20\d{2})\b", title)
    return int(m.group(1)) if m else None


def _parse_mileage(title: str, excerpt: str = "") -> Optional[int]:
    for blob in (title, excerpt):
        m = re.search(r"(\d+)\s*k[- ]?mile", blob, re.I)
        if m:
            return int(m.group(1)) * 1000
        m = re.search(r"([\d,]+)\s*miles", blob, re.I)
        if m:
            return int(m.group(1).replace(",", ""))
    return None


def _listings_from_completed_json(html: str) -> list[Listing]:
    m = re.search(r"var auctionsCompletedInitialData\s*=\s*(\{.*?\});\s*", html, re.S)
    if not m:
        return []
    data = json.loads(m.group(1))
    out: list[Listing] = []
    for item in data.get("items") or []:
        url = item.get("url") or item.get("permalink")
        title = (item.get("title") or "").strip()
        listing_id = str(item.get("id") or item.get("post_id") or url or title)
        if not url or not title:
            continue
        if "s2000" not in title.lower() and "s2000" not in (item.get("excerpt") or "").lower():
            continue
        price = item.get("current_bid")
        if price is None:
            price = _parse_price(item.get("current_bid_formatted"))
        out.append(
            Listing(
                id=listing_id,
                source="bringatrailer",
                title=title,
                url=url,
                price=int(price) if price is not None else None,
                year=_parse_year(title),
                mileage=_parse_mileage(title, item.get("excerpt") or ""),
                location=item.get("location") or item.get("country_code"),
                status="completed" if not item.get("active") else "live",
                thumbnail=item.get("thumbnail") or item.get("image"),
                notes=(item.get("excerpt") or None),
            )
        )
    return out


def _listings_from_live_cards(html: str) -> list[Listing]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[Listing] = []
    for card in soup.select("div.listing-card[data-listing_id]"):
        listing_id = card.get("data-listing_id")
        link = card.select_one('a[href*="/listing/"]')
        if not listing_id or not link:
            continue
        url = link.get("href")
        title = link.get_text(" ", strip=True)
        if not url or not title:
            # Sometimes the visible title is in a nested heading
            heading = card.select_one(".listing-card-title, h3, h2")
            title = heading.get_text(" ", strip=True) if heading else ""
        if not title or "s2000" not in title.lower():
            # Fall back to any S2000 text in the card
            text = card.get_text(" ", strip=True)
            m = re.search(r"([^.]{0,80}S2000[^.]{0,40})", text, re.I)
            title = m.group(1).strip() if m else title
        if not title:
            continue

        money = re.findall(r"\$[\d,]+", card.get_text(" ", strip=True))
        price = _parse_price(money[0]) if money else None
        img = card.select_one("img")
        thumb = img.get("src") if img else None
        excerpt_el = card.select_one(".listing-card-excerpt, p")
        excerpt = excerpt_el.get_text(" ", strip=True) if excerpt_el else ""

        out.append(
            Listing(
                id=str(listing_id),
                source="bringatrailer",
                title=title,
                url=url,
                price=price,
                year=_parse_year(title),
                mileage=_parse_mileage(title, excerpt),
                location=None,
                status="live",
                thumbnail=thumb,
                notes=excerpt or None,
            )
        )
    return out


def fetch_bringatrailer_s2000(
    *,
    include_completed: bool = False,
    year_min: int | None = None,
    year_max: int | None = None,
    max_price: int | None = None,
) -> list[Listing]:
    """Fetch Honda S2000 auctions from Bring a Trailer.

    By default only live/current auctions are returned (what you want for 'for sale').
    Set include_completed=True to also ingest recently completed auctions.
    """
    html = _http_get(BAT_S2000_URL)
    live = _listings_from_live_cards(html)
    completed = _listings_from_completed_json(html) if include_completed else []

    # Prefer live cards; completed may overlap after an auction ends.
    by_key: dict[str, Listing] = {}
    for listing in completed + live:
        by_key[listing.key] = listing

    filtered: list[Listing] = []
    for listing in by_key.values():
        if year_min is not None and listing.year is not None and listing.year < year_min:
            continue
        if year_max is not None and listing.year is not None and listing.year > year_max:
            continue
        if max_price is not None and listing.price is not None and listing.price > max_price:
            continue
        filtered.append(listing)

    filtered.sort(key=lambda x: (0 if x.status == "live" else 1, x.title))
    return filtered
