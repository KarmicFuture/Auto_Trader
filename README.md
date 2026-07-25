# Auto_Trader — Honda S2000 sale alerts

Get notified when a **Honda S2000** shows up for sale.

Out of the box this watches [Bring a Trailer](https://bringatrailer.com/honda/s2000/) live auctions (the main place clean S2000s trade). Optionally add nearby dealer inventory via [MarketCheck](https://www.marketcheck.com/) if you set an API key and ZIP.

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

## Get told when a new one appears

### Option A — GitHub Actions (recommended)

1. Merge this repo’s alert workflow.
2. In the GitHub repo: **Settings → Secrets and variables → Actions**, optionally add:
   - `NOTIFY_EMAIL_TO` — e.g. `vk00345@gmail.com`
   - `SMTP_USER` / `SMTP_PASSWORD` / `SMTP_HOST` / `SMTP_PORT` / `NOTIFY_EMAIL_FROM` — for Gmail use an [App Password](https://myaccount.google.com/apppasswords) and host `smtp.gmail.com` port `587`
   - `DISCORD_WEBHOOK_URL` — Discord channel webhook
   - `WATCH_ZIP` — your ZIP for nearby dealer search
   - `MARKETCHECK_API_KEY` — enables nearby dealer inventory
3. Run **Actions → S2000 sale alerts → Run workflow**.
4. The job runs hourly. New cars open a GitHub issue labeled `s2000-alert` (GitHub will email you if issue notifications are on). Discord/email fire when those secrets are set.

First Actions run only baselines current auctions. To also get a digest of what’s already listed, run the workflow with **notify_existing = true**.

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

- BaT auctions are nationwide (shipping/transport is normal for these cars), so “near me” mainly applies once MarketCheck + ZIP are configured.
- `data/seen.json` remembers listings already alerted so you don’t get duplicates.
- Be a good citizen: the default schedule is once per hour.
