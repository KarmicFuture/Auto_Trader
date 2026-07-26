# Auto_Trader — S2K Board

Browse every **Honda S2000 for sale in the United States**, and optionally get alerted when new ones appear.

## Website (S2K Board)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# http://localhost:8000
python3 -m uvicorn src.web.app:app --host 0.0.0.0 --port 8000 --reload
# or: bash scripts/dev-web.sh
```

The site loads live US inventory from:
- [Cars.com](https://www.cars.com/)
- [Bring a Trailer](https://bringatrailer.com/honda/s2000/)
- [Autotrader](https://www.autotrader.com/) (when not IP-blocked)

API: `GET /api/listings` · force refresh with `?refresh=true`

## Alerts (optional)

Hourly GitHub Action + Discord / email / GitHub issues. See below.

```bash
python -m src.main --list   # CLI snapshot
python -m src.main          # seed / notify watcher
```

Set `WATCH_ZIP` (and optionally `WATCH_RADIUS_MILES`) for nearby-only alert filtering. Leave ZIP blank for nationwide alerts.

### GitHub Actions

1. Merge the alert workflow.
2. Add secrets as needed: `WATCH_ZIP`, `NOTIFY_EMAIL_TO`, `SMTP_*`, `DISCORD_WEBHOOK_URL`, `MARKETCHECK_API_KEY`
3. **Actions → S2000 sale alerts → Run workflow**

### Config

| Setting | Env var | Meaning |
|---|---|---|
| `watch.zip` | `WATCH_ZIP` | ZIP for nearby alert filtering |
| `watch.radius_miles` | `WATCH_RADIUS_MILES` | Search radius (default 100) |
| `watch.max_price` | `WATCH_MAX_PRICE` | Optional price cap |
| `sources.cars_com` | `SOURCE_CARS_COM` | Cars.com (default on) |
| `sources.autotrader` | `SOURCE_AUTOTRADER` | Autotrader (default on) |
| `sources.bringatrailer` | `SOURCE_BRINGATRAILER` | BaT (default on) |

See `config.example.yaml` for the full template.

## Notes

- Cars.com is fetched through AutoTempest’s Cars.com inventory feed.
- Autotrader blocks many datacenter IPs and soft-fails when blocked.
- Website responses are cached for 10 minutes; use **Refresh now** or `?refresh=true`.
