from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .config import load_config
from .models import Listing
from .notify import dispatch_notifications, format_digest
from .sources import (
    fetch_autotrader_s2000,
    fetch_bringatrailer_s2000,
    fetch_cars_com_s2000,
    fetch_marketcheck_s2000,
)
from .store import SeenStore


def _radius_for_marketplace(watch: dict) -> int | None:
    """Radius for Cars.com / Autotrader. None/blank zip => nationwide."""
    zip_code = str(watch.get("zip") or "").strip()
    if not zip_code:
        return None
    return int(watch.get("radius_miles") or 100)


def collect_listings(cfg: dict) -> list[Listing]:
    watch = cfg.get("watch") or {}
    sources = cfg.get("sources") or {}
    year_min = watch.get("year_min")
    year_max = watch.get("year_max")
    max_price = watch.get("max_price")
    zip_code = str(watch.get("zip") or "").strip()
    radius = _radius_for_marketplace(watch)

    found: list[Listing] = []
    errors: list[str] = []

    if sources.get("bringatrailer", True):
        try:
            found.extend(
                fetch_bringatrailer_s2000(
                    include_completed=False,
                    year_min=year_min,
                    year_max=year_max,
                    max_price=max_price,
                )
            )
        except Exception as exc:  # noqa: BLE001 - keep other sources running
            errors.append(f"bringatrailer: {exc}")

    if sources.get("cars_com", True):
        try:
            found.extend(
                fetch_cars_com_s2000(
                    zip_code=zip_code,
                    radius_miles=radius,
                    year_min=year_min,
                    year_max=year_max,
                    max_price=max_price,
                )
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"cars.com: {exc}")

    if sources.get("autotrader", True):
        try:
            found.extend(
                fetch_autotrader_s2000(
                    zip_code=zip_code,
                    radius_miles=radius,
                    year_min=year_min,
                    year_max=year_max,
                    max_price=max_price,
                )
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"autotrader: {exc}")

    if sources.get("marketcheck"):
        try:
            found.extend(
                fetch_marketcheck_s2000(
                    zip_code=zip_code,
                    radius_miles=int(watch.get("radius_miles") or 100),
                    year_min=int(year_min or 1999),
                    year_max=int(year_max or 2009),
                    max_price=max_price,
                )
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"marketcheck: {exc}")

    for err in errors:
        print(f"Source warning: {err}", file=sys.stderr)

    # De-dupe by URL as a secondary key
    by_url: dict[str, Listing] = {}
    for listing in found:
        by_url[listing.url] = listing
    return list(by_url.values())


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
