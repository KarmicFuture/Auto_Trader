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
    config_path: Path | None = None,
) -> int:
    cfg = load_config(config_path)
    if notify_existing is not None:
        cfg["notify_existing"] = notify_existing

    store = SeenStore()
    listings = collect_listings(cfg)
    new_listings = [listing for listing in listings if store.is_new(listing)]

    first_run = store.count == 0
    should_notify_existing = bool(cfg.get("notify_existing"))

    if first_run and not should_notify_existing:
        # Seed baseline so the next run only alerts on truly new cars.
        if dry_run:
            print(
                f"Dry run — would seed baseline with {len(listings)} listing(s) "
                "(no alerts)."
            )
            print(format_digest(listings, "Current Honda S2000 listings:"))
            return 0
        store.mark_seen(listings)
        store.save()
        print(
            f"Baseline seeded with {len(listings)} listing(s). "
            "Future runs will notify on new S2000s only."
        )
        print(format_digest(listings, "Current Honda S2000 listings (no alert sent):"))
        return 0

    to_notify = listings if (first_run and should_notify_existing) else new_listings

    print(f"Fetched {len(listings)} listing(s); {len(to_notify)} new.")
    if dry_run:
        if to_notify:
            print(format_digest(to_notify, "Dry run — would notify:"))
        else:
            print("Dry run — no new listings to notify.")
        return 0

    if to_notify:
        channels = dispatch_notifications(to_notify, cfg)
        print(f"Notified via: {', '.join(channels)}")
    else:
        print("No new Honda S2000 listings.")

    store.mark_seen(listings)
    store.save()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Watch for Honda S2000 cars for sale and notify you."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to config.yaml (defaults to ./config.yaml or config.example.yaml)",
    )
    parser.add_argument(
        "--notify-existing",
        action="store_true",
        help="On an empty seen-store, send alerts for currently listed cars.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and diff without saving state or sending notifications.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print current listings as JSON and exit.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.list:
        cfg = load_config(args.config)
        listings = collect_listings(cfg)
        print(json.dumps([listing.to_dict() for listing in listings], indent=2))
        return 0
    return run_watch(
        notify_existing=True if args.notify_existing else None,
        dry_run=args.dry_run,
        config_path=args.config,
    )


if __name__ == "__main__":
    sys.exit(main())
