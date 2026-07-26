# Auto_Trader — Auto Board

Browse **Honda S2000** and **Porsche Cayman** cars for sale in the United States, each with an **independent value score**.

## Value score

Every listing is scored from its own year, mileage, trim cues, and ask price against a fixed fair-value curve for that model — not against other cars currently listed. Higher score = better buy vs that car’s own expected market value.

## App

Auto Board is an installable progressive web app: browse inventory, filter by value, and star cars to a local Saved list.

### Local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn src.web.app:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000 — on a phone or Chromium, use **Install** when prompted (or the browser “Add to Home Screen” action).

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
