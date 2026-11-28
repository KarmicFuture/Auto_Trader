# Auto_Trader — Auto Board

Browse **Honda S2000**, **Porsche Cayman**, and **dune buggy** listings for sale in the United States, each with an **independent value score**.

Sources: Cars.com, CarGurus, eBay, TrueCar, Carvana, CarMax, Hemmings, Cars & Bids, Bring a Trailer, and Autotrader (when reachable).

## Value score

Every listing is scored from its own year, mileage, trim cues, and ask price against a fixed fair-value curve for that model — not against other cars currently listed. Higher score = better buy vs that car’s own expected market value.

## Website

### Local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn src.web.app:app --host 0.0.0.0 --port 8000
```

### GitHub Pages

1. Make the repo **public** (free GitHub requirement)
2. Settings → Pages → branch **main** / folder **/docs** → Save
3. https://karmicfuture.github.io/Auto_Trader/

Rebuild static docs:

```bash
python scripts/build_static_site.py
```

## Alerts

```bash
python -m src.main --list
python -m src.main
```

Optional secrets: `WATCH_ZIP`, `NOTIFY_EMAIL_TO`, `SMTP_*`, `DISCORD_WEBHOOK_URL`

## Inbox agent

Scans **Gmail**, **Discord**, and **WhatsApp** for important conversations and
alerts you (console / Discord webhook / email). Runs on a 30-minute schedule in
GitHub Actions. Full setup guide: [docs/INBOX_AGENT.md](docs/INBOX_AGENT.md).

```bash
python -m src.inbox.main --dry-run   # scan + score without alerting
python -m src.inbox.main             # scan and alert on important conversations
```

Secrets: `GMAIL_USER` + `GMAIL_APP_PASSWORD`, `DISCORD_BOT_TOKEN` +
`DISCORD_CHANNEL_IDS`, WhatsApp Cloud API webhook (see guide), plus
`INBOX_VIP_SENDERS` / `INBOX_KEYWORDS` to tune what counts as important.
