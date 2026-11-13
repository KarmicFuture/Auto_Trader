from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .alerts import dispatch_alerts, format_digest
from .config import load_inbox_config
from .importance import filter_important
from .models import Message
from .sources import discord as discord_source
from .sources import gmail as gmail_source
from .sources import whatsapp as whatsapp_source
from .store import InboxSeenStore


def collect_messages(cfg: dict) -> list[Message]:
    inbox = cfg.get("inbox") or {}
    lookback = int(inbox.get("lookback_hours") or 24)
    messages: list[Message] = []

    fetchers = [
        ("gmail", gmail_source.fetch_messages),
        ("discord", discord_source.fetch_messages),
        ("whatsapp", whatsapp_source.fetch_messages),
    ]
    for name, fetch in fetchers:
        source_cfg = inbox.get(name) or {}
        if not source_cfg.get("enabled"):
            continue
        try:
            fetched = fetch(source_cfg, lookback_hours=lookback)
            messages.extend(fetched)
            print(f"{name}: fetched {len(fetched)} message(s)", file=sys.stderr)
        except Exception as exc:  # one broken source must not kill the run
            print(f"Source warning ({name}): {exc}", file=sys.stderr)

    return messages


def run_scan(*, dry_run: bool = False, config_path: Path | None = None) -> int:
    cfg = load_inbox_config(config_path)
    inbox = cfg.get("inbox") or {}
    if inbox.get("enabled") is False:
        print("Inbox agent disabled in config.")
        return 0

    enabled = [k for k in ("gmail", "discord", "whatsapp") if (inbox.get(k) or {}).get("enabled")]
    if not enabled:
        print(
            "No inbox sources enabled. Configure inbox.gmail / inbox.discord / "
            "inbox.whatsapp in config.yaml or via env vars (see docs/INBOX_AGENT.md)."
        )
        return 1

    store = InboxSeenStore()
    messages = collect_messages(cfg)
    important = filter_important(messages, inbox)
    new_important = [s for s in important if store.is_new(s)]

    print(
        f"Scanned {len(messages)} message(s) from {', '.join(enabled)}; "
        f"{len(important)} important, {len(new_important)} not yet alerted."
    )

    if dry_run:
        if new_important:
            print(format_digest(new_important, "Dry run — would alert:"))
        else:
            print("Dry run — nothing new to alert.")
        return 0

    if new_important:
        channels = dispatch_alerts(new_important, cfg)
        print(f"Alerted via: {', '.join(channels)}")
        store.mark_seen(new_important)
        store.save()
    else:
        print("No new important conversations.")
        # Still save so pruning keeps the store small.
        if store.count:
            store.save()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scan Discord, WhatsApp, and Gmail and alert on important conversations."
    )
    parser.add_argument("--config", type=Path, default=None, help="Path to config.yaml")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan and score without saving state or sending alerts.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print all fetched messages with scores as JSON and exit.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.list:
        cfg = load_inbox_config(args.config)
        inbox = cfg.get("inbox") or {}
        from .importance import score_message

        messages = collect_messages(cfg)
        out = []
        for msg in messages:
            scored = score_message(msg, inbox)
            record = msg.to_dict()
            record["score"] = scored.score
            record["reasons"] = scored.reasons
            out.append(record)
        out.sort(key=lambda r: -r["score"])
        print(json.dumps(out, indent=2))
        return 0
    return run_scan(dry_run=args.dry_run, config_path=args.config)


if __name__ == "__main__":
    sys.exit(main())
