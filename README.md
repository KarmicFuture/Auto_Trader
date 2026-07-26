# Auto_Trader — Honda S2000 sale alerts

Get notified when a **Honda S2000** shows up for sale.

**Sources (on by default):**
- [Bring a Trailer](https://bringatrailer.com/honda/s2000/) live auctions
- [Cars.com](https://www.cars.com/) dealer/private listings
- [Autotrader](https://www.autotrader.com/) (when the network isn’t blocked)

Optional: [MarketCheck](https://www.marketcheck.com/) with an API key + ZIP.

## Quick start (local)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# See what's listed right now
python -m src.main --list

# Seed a baseline (no spam). Later runs only alert on *new* cars.
python -m src.main
```

Set `WATCH_ZIP` (and optionally `WATCH_RADIUS_MILES`) for “near me” Cars.com / Autotrader results. Leave ZIP blank for nationwide.

## Get told when a new one appears

### Option A — GitHub Actions (recommended)

1. Merge this repo’s alert workflow.
2. In the GitHub repo: **Settings → Secrets and variables → Actions**, optionally add:
   - `WATCH_ZIP` — your ZIP for nearby Cars.com / Autotrader search
   - `WATCH_RADIUS_MILES` — e.g. `100`
   - `NOTIFY_EMAIL_TO` — e.g. `vk00345@gmail.com`
   - `SMTP_USER` / `SMTP_PASSWORD` / `SMTP_HOST` / `SMTP_PORT` / `NOTIFY_EMAIL_FROM` — for Gmail use an [App Password](https://myaccount.google.com/apppasswords) and host `smtp.gmail.com` port `587`
   - `DISCORD_WEBHOOK_URL` — Discord channel webhook
   - `MARKETCHECK_API_KEY` — enables MarketCheck nearby inventory
3. Run **Actions → S2000 sale alerts → Run workflow**.
4. The job runs hourly. New cars open a GitHub issue labeled `s2000-alert` (GitHub will email you if issue notifications are on). Discord/email fire when those secrets are set.

First Actions run only baselines current listings. To also get a digest of what’s already listed, run the workflow with **notify_existing = true**.

### Option B — Local cron + Discord/email

```bash
cp config.example.yaml config.yaml
# edit zip / notification settings

export DISCORD_WEBHOOK_URL='https://discord.com/api/webhooks/...'
# or SMTP_* + NOTIFY_EMAIL_TO

python -m src.main
```

## Config

| Setting | Env var | Meaning |
|---|---|---|
| `watch.zip` | `WATCH_ZIP` | Your ZIP for nearby inventory |
| `watch.radius_miles` | `WATCH_RADIUS_MILES` | Search radius (default 100) |
| `watch.max_price` | `WATCH_MAX_PRICE` | Optional price cap |
| `sources.cars_com` | `SOURCE_CARS_COM` | Cars.com (default on) |
| `sources.autotrader` | `SOURCE_AUTOTRADER` | Autotrader (default on) |
| `sources.bringatrailer` | `SOURCE_BRINGATRAILER` | BaT (default on) |
| `sources.marketcheck` | `SOURCE_MARKETCHECK` | Enable MarketCheck |
| `notifications.discord.webhook_url` | `DISCORD_WEBHOOK_URL` | Discord alerts |
| email SMTP fields | `SMTP_*`, `NOTIFY_EMAIL_TO` | Email alerts |

See `config.example.yaml` for the full template.

## CLI

```bash
python -m src.main --list              # JSON dump of current matches
python -m src.main --dry-run           # fetch + diff, no save/notify
python -m src.main --notify-existing   # alert on current listings too
```

## Notes

- Cars.com is fetched through AutoTempest’s Cars.com inventory feed (direct cars.com is Cloudflare-blocked from most cloud IPs).
- Autotrader blocks many datacenter IPs. The source soft-fails when blocked; it works from residential / unblocked networks (including some GitHub-hosted runners).
- BaT auctions are nationwide. “Near me” applies to Cars.com / Autotrader / MarketCheck once `WATCH_ZIP` is set.
- `data/seen.json` remembers listings already alerted so you don’t get duplicates.
- Default schedule is once per hour.
