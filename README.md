# Auto_Trader — S2K Board

Browse every **Honda S2000 for sale in the United States**, and optionally get alerted when new ones appear.

## Website (S2K Board)

### 1) Make the repo public (required on free GitHub)

Your repo is currently **private**. Free GitHub only publishes Pages from **public** repos, which is why the Pages “Source” control may be missing.

1. Open https://github.com/KarmicFuture/Auto_Trader/settings  
2. Scroll to **Danger Zone** → **Change repository visibility** → **Make public**

### 2) Turn on Pages from the `docs` folder

1. Open https://github.com/KarmicFuture/Auto_Trader/settings/pages  
2. Under **Build and deployment**, find the dropdown that currently says **None** (or similar)  
3. Choose branch **`main`**  
4. Choose folder **`/docs`**  
5. Click **Save**

You do **not** need “GitHub Actions” as the source for this setup.

Site URL: **https://karmicfuture.github.io/Auto_Trader/**

### Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn src.web.app:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000

### Refresh listings

`docs/` is rebuilt by the **Refresh S2K Board site** Action on push to `main` and every 6 hours.

```bash
python scripts/build_static_site.py
```

## Alerts (optional)

Hourly GitHub Action + Discord / email / GitHub issues.

```bash
python -m src.main --list
python -m src.main
```

Set `WATCH_ZIP` for nearby-only alerts. Leave blank for nationwide.

### GitHub Actions secrets (optional)

`WATCH_ZIP`, `NOTIFY_EMAIL_TO`, `SMTP_*`, `DISCORD_WEBHOOK_URL`, `MARKETCHECK_API_KEY`

## Notes

- Cars.com is fetched through AutoTempest’s Cars.com inventory feed.
- Autotrader blocks many datacenter IPs and soft-fails when blocked.
