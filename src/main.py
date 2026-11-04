from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .config import load_config
from .catalog import fetch_us_board_listings
from .models import Listing
from .notify import dispatch_notifications, format_digest
from .store import SeenStore


def collect_listings(cfg: dict) -> list[Listing]:
    watch = cfg.get("watch") or {}
    sources = cfg.get("sources") or {}
    max_price = watch.get("max_price")
    watch_ids = cfg.get("watch_ids")  # optional list override

    listings, errors = fetch_us_board_listings(
        watch_ids=watch_ids,
        max_price=max_price,
        include_bringatrailer=sources.get("bringatrailer", True),
        include_cars_com=sources.get("cars_com", True),
        include_autotrader=sources.get("autotrader", True),
        include_marketcheck=bool(sources.get("marketcheck")),
        marketcheck_zip=str(watch.get("zip") or "90210"),
        marketcheck_radius=int(watch.get("radius_miles") or 100),
    )
    for err in errors:
        print(f"Source warning: {err}", file=sys.stderr)
    return listings


def run_watch(
    *,
    notify_existing: bool | None = None,
    dry_run: bool = False,
    config_path
