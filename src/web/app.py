from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..catalog import fetch_us_s2000_listings, listings_payload

WEB_DIR = Path(__file__).resolve().parent
CACHE_TTL_SECONDS = 10 * 60

app = FastAPI(title="S2K Board", description="Honda S2000s for sale across the United States")
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))

_cache: dict[str, Any] = {"expires": 0.0, "payload": None}


def _get_catalog(*, force: bool = False, max_price: int | None = None) -> dict[str, Any]:
    now = time.time()
    cache_key = f"us:{max_price}"
    cached = _cache.get("payload")
    if (
        not force
        and cached
        and _cache.get("key") == cache_key
        and now < float(_cache.get("expires") or 0)
    ):
        return cached

    listings, errors = fetch_us_s2000_listings(max_price=max_price)
    payload = listings_payload(
        listings,
        errors=errors,
        refreshed_at=datetime.now(timezone.utc).isoformat(),
    )
    _cache["payload"] = payload
    _cache["key"] = cache_key
    _cache["expires"] = now + CACHE_TTL_SECONDS
    return payload


def _render_index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "brand": "S2K Board",
            "api_url": "/api/listings",
            "asset_prefix": "/static",
        },
    )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return _render_index(request)


@app.get("/index.html", response_class=HTMLResponse)
async def index_html(request: Request) -> HTMLResponse:
    return _render_index(request)


@app.get("/listings", response_class=HTMLResponse)
@app.get("/board", response_class=HTMLResponse)
@app.get("/s2k", response_class=HTMLResponse)
async def listings_page(request: Request) -> HTMLResponse:
    """Aliases people often hit; same board as home."""
    return _render_index(request)


@app.get("/api")
async def api_root() -> RedirectResponse:
    return RedirectResponse(url="/api/listings", status_code=307)


@app.get("/api/listings")
async def api_listings(
    refresh: bool = Query(False),
    max_price: int | None = Query(None, ge=1000, le=500000),
) -> dict[str, Any]:
    return _get_catalog(force=refresh, max_price=max_price)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# Mount static last so it doesn't swallow API/page routes.
app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")
