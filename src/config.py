from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = ROOT / "config.yaml"
EXAMPLE_CONFIG_PATH = ROOT / "config.example.yaml"


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def _env_bool(name: str, default: bool | None = None) -> bool | None:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int | None = None) -> int | None:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load YAML config, then apply environment overrides."""
    cfg_path = path or Path(os.getenv("CONFIG_PATH", DEFAULT_CONFIG_PATH))
    if cfg_path.exists():
        with cfg_path.open() as fh:
            cfg = yaml.safe_load(fh) or {}
    elif EXAMPLE_CONFIG_PATH.exists():
        with EXAMPLE_CONFIG_PATH.open() as fh:
            cfg = yaml.safe_load(fh) or {}
    else:
        cfg = {}

    env_overlay: dict[str, Any] = {
        "watch": {},
        "sources": {},
        "notifications": {
            "email": {},
            "discord": {},
            "github_issues": {},
        },
    }

    if os.getenv("WATCH_ZIP"):
        env_overlay["watch"]["zip"] = os.getenv("WATCH_ZIP")
    if os.getenv("WATCH_RADIUS_MILES"):
        env_overlay["watch"]["radius_miles"] = _env_int("WATCH_RADIUS_MILES")
    if os.getenv("WATCH_MAX_PRICE"):
        env_overlay["watch"]["max_price"] = _env_int("WATCH_MAX_PRICE")
    if os.getenv("WATCH_YEAR_MIN"):
        env_overlay["watch"]["year_min"] = _env_int("WATCH_YEAR_MIN")
    if os.getenv("WATCH_YEAR_MAX"):
        env_overlay["watch"]["year_max"] = _env_int("WATCH_YEAR_MAX")

    if _env_bool("SOURCE_BRINGATRAILER") is not None:
        env_overlay["sources"]["bringatrailer"] = _env_bool("SOURCE_BRINGATRAILER")
    if _env_bool("SOURCE_CARS_COM") is not None:
        env_overlay["sources"]["cars_com"] = _env_bool("SOURCE_CARS_COM")
    if _env_bool("SOURCE_AUTOTRADER") is not None:
        env_overlay["sources"]["autotrader"] = _env_bool("SOURCE_AUTOTRADER")
    if _env_bool("SOURCE_MARKETCHECK") is not None:
        env_overlay["sources"]["marketcheck"] = _env_bool("SOURCE_MARKETCHECK")
    elif os.getenv("MARKETCHECK_API_KEY"):
        env_overlay["sources"]["marketcheck"] = True

    if _env_bool("NOTIFY_EXISTING") is not None:
        env_overlay["notify_existing"] = _env_bool("NOTIFY_EXISTING")

    email = env_overlay["notifications"]["email"]
    if _env_bool("NOTIFY_EMAIL") is not None:
        email["enabled"] = _env_bool("NOTIFY_EMAIL")
    if os.getenv("NOTIFY_EMAIL_TO"):
        email["to"] = os.getenv("NOTIFY_EMAIL_TO")
    if os.getenv("NOTIFY_EMAIL_FROM"):
        email["from"] = os.getenv("NOTIFY_EMAIL_FROM")
    if os.getenv("SMTP_HOST"):
        email["smtp_host"] = os.getenv("SMTP_HOST")
    if os.getenv("SMTP_PORT"):
        email["smtp_port"] = _env_int("SMTP_PORT")
    if os.getenv("SMTP_USER"):
        email["smtp_user"] = os.getenv("SMTP_USER")
    if os.getenv("SMTP_PASSWORD"):
        email["smtp_password"] = os.getenv("SMTP_PASSWORD")

    discord = env_overlay["notifications"]["discord"]
    if os.getenv("DISCORD_WEBHOOK_URL"):
        discord["webhook_url"] = os.getenv("DISCORD_WEBHOOK_URL")
    if _env_bool("NOTIFY_DISCORD") is not None:
        discord["enabled"] = _env_bool("NOTIFY_DISCORD")
    elif os.getenv("DISCORD_WEBHOOK_URL"):
        discord["enabled"] = True

    gh = env_overlay["notifications"]["github_issues"]
    if _env_bool("NOTIFY_GITHUB_ISSUES") is not None:
        gh["enabled"] = _env_bool("NOTIFY_GITHUB_ISSUES")
    elif os.getenv("GITHUB_ACTIONS") == "true":
        # In Actions, open an issue per new listing so GitHub emails you.
        gh["enabled"] = True

    # Auto-enable email when SMTP password is present unless explicitly disabled.
    if _env_bool("NOTIFY_EMAIL") is None and os.getenv("SMTP_PASSWORD"):
        email["enabled"] = True

    # Drop empty overlay branches so merge doesn't wipe defaults with {}.
    def prune(d: dict[str, Any]) -> dict[str, Any]:
        cleaned: dict[str, Any] = {}
        for k, v in d.items():
            if isinstance(v, dict):
                nested = prune(v)
                if nested:
                    cleaned[k] = nested
            elif v is not None:
                cleaned[k] = v
        return cleaned

    return _deep_merge(cfg, prune(env_overlay))
