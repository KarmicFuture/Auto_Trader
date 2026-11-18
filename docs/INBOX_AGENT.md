# Inbox agent — important conversation alerts

Scans **Gmail**, **Discord**, and **WhatsApp**, scores each recent message for
importance (0–10), and alerts you — via console, a Discord webhook, and/or
email — only for conversations that matter and haven't been alerted before.

```bash
python -m src.inbox.main --dry-run   # scan + score, no alerts, no state change
python -m src.inbox.main --list      # dump all fetched messages with scores as JSON
python -m src.inbox.main             # scan and send alerts
```

Configuration lives in the `inbox:` section of `config.yaml` (copy from
`config.example.yaml`); every setting can also come from env vars / GitHub
Actions secrets, which is how the scheduled workflow
(`.github/workflows/inbox-alerts.yml`, every 30 minutes) runs it.

## What counts as "important"

Rule-based scoring, tunable in config:

| Signal | Points |
| --- | --- |
| Sender matches `vip_senders` | +4 |
| Message matches one of your `keywords` | +3 |
| Urgent language (urgent, ASAP, action required, call me, …) | +3 |
| You were @mentioned (Discord) | +3 |
| Direct message (Discord DM / WhatsApp) | +2 |
| Deadline / near-term scheduling language | +1 |
| Money, invoices, payments | +1 |
| Asks you a question | +1 |
| Meetings, appointments, flights, reservations | +1 |
| Looks like bulk mail / newsletter | −4 |
| Sender or conversation is muted | never alerts |

Anything scoring at or above `min_importance` (default **3**) triggers an
alert, once per message (state is kept in `data/inbox_seen.json`).

## Gmail setup

Uses IMAP with a Google **app password** — no OAuth app registration needed.

1. Enable 2-Step Verification on your Google account.
2. Create an app password: <https://myaccount.google.com/apppasswords>
3. Set secrets/env: `GMAIL_USER` (your address) and `GMAIL_APP_PASSWORD`.

By default only **unread** mail from the last `lookback_hours` is scanned, and
messages are fetched with `BODY.PEEK` so they stay unread. Newsletters and
no-reply senders are penalized automatically.

## Discord setup

Uses a **bot token** (the only ToS-compliant way to read Discord programmatically).

1. Create an application + bot at <https://discord.com/developers/applications>.
2. Enable the **Message Content Intent** on the Bot page.
3. Invite the bot to your server(s) with the *View Channels* and *Read Message
   History* permissions.
4. Set secrets/env: `DISCORD_BOT_TOKEN`, `DISCORD_CHANNEL_IDS` (comma-separated
   channel IDs — enable Developer Mode in Discord, right-click a channel, Copy ID),
   and `DISCORD_MY_USER_ID` so @mentions of you score higher.

> Limitation: bots can only see channels they're invited to. Discord forbids
> automating a *user* account, so your personal DMs can't be scanned — but any
> server channel you add the bot to is covered, and @mentions of you rank high.

## WhatsApp setup

WhatsApp has no polling API, so messages are received via the **WhatsApp
Business Cloud API** webhook and buffered to `data/inbox/whatsapp.jsonl`
(gitignored), which the scanner reads.

1. Create a Meta app with the WhatsApp product (free tier is fine):
   <https://developers.facebook.com/docs/whatsapp/cloud-api/get-started>
2. Run the receiver somewhere Meta can reach (a small VPS, or ngrok/Cloudflare
   tunnel while testing):

   ```bash
   WHATSAPP_VERIFY_TOKEN=pick-a-secret \
   python -m uvicorn src.inbox.whatsapp_webhook:app --host 0.0.0.0 --port 8080
   ```

3. In the Meta app dashboard, set the webhook URL to
   `https://<your-host>/whatsapp/webhook` with the same verify token, and
   subscribe to the `messages` field.
4. Enable `inbox.whatsapp` in config (and set `WHATSAPP_INBOX_FILE` if the
   receiver and scanner run on different paths).

> Note: the Cloud API delivers messages sent **to your WhatsApp Business
> number**. Personal-account scraping isn't supported by WhatsApp; if you need
> that, forward the chats you care about to your business number.

## Alert channels

- **Console** — always on.
- **Discord webhook** — set `INBOX_DISCORD_WEBHOOK_URL` (or reuse the existing
  `DISCORD_WEBHOOK_URL` used for S2000 alerts). One embed per conversation,
  color-coded by source, with score and reasons.
- **Email** — reuses the `notifications.email` SMTP settings (Gmail app
  password works). Force on/off with `INBOX_ALERT_EMAIL=true|false`.

## Tuning

Env vars (all optional): `INBOX_LOOKBACK_HOURS`, `INBOX_MIN_IMPORTANCE`,
`INBOX_VIP_SENDERS` (comma-separated), `INBOX_KEYWORDS` (comma-separated),
`INBOX_GMAIL_ENABLED`, `INBOX_DISCORD_ENABLED`, `INBOX_WHATSAPP_ENABLED`,
`INBOX_ENABLED`.
