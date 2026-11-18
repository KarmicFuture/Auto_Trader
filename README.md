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

## Empty Taco

Promotional site for the Tampa mobile hot dog cart lives in `empty-taco/`. Local preview:

```bash
python3 -m http.server 8080 --directory empty-taco
```

The Pages rebuild copies it to `docs/empty-taco/`.

## Alerts

```bash
python -m src.main --list
python -m src.main
```

Optional secrets: `WATCH_ZIP`, `NOTIFY_EMAIL_TO`, `SMTP_*`, `DISCORD_WEBHOOK_URL`
