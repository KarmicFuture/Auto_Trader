#!/usr/bin/env python3
"""Build a static Auto Board site into docs/ for GitHub Pages."""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.catalog import fetch_us_board_listings, listings_payload  # noqa: E402

OUT = ROOT / "docs"
WEB = ROOT / "src" / "web"
EMPTY_TACO = ROOT / "empty-taco"


def _copy_empty_taco_site() -> None:
    """Keep the Empty Taco promo site on Pages after docs/ is rebuilt."""
    if not EMPTY_TACO.is_dir():
        return
    dest = OUT / "empty-taco"
    shutil.copytree(EMPTY_TACO, dest, dirs_exist_ok=True)


def build() -> None:
    listings, errors = fetch_us_board_listings()
    payload = listings_payload(
        listings,
        errors=errors,
        refreshed_at=datetime.now(timezone.utc).isoformat(),
    )

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    static_out = OUT / "static"
    shutil.copytree(WEB / "static", static_out)

    template = (WEB / "templates" / "index.html").read_text()
    html = (
        template.replace("{{ asset_prefix }}", "./static")
        .replace("{{ api_url|tojson }}", json.dumps("./listings.json"))
        .replace("{{ brand }}", "Auto Board")
    )
    (OUT / "index.html").write_text(html)
    (OUT / "listings.json").write_text(json.dumps(payload, indent=2) + "\n")
    (OUT / ".nojekyll").write_text("")
    for name in ("listings", "board", "s2k"):
        (OUT / f"{name}.html").write_text(html)

    _copy_empty_taco_site()

    print(f"Built {OUT} with {payload['count']} listings")
    if errors:
        print("Source warnings:", "; ".join(errors))


if __name__ == "__main__":
    build()
