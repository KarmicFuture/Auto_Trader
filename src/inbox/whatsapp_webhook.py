"""WhatsApp Business Cloud API webhook receiver.

WhatsApp offers no polling API, so Meta pushes incoming messages to a webhook.
This tiny app verifies Meta's challenge handshake and appends every incoming
message to the JSONL inbox file that `src.inbox.sources.whatsapp` reads.

Run it somewhere reachable by Meta (or behind an ngrok/Cloudflare tunnel):

    WHATSAPP_VERIFY_TOKEN=pick-a-secret \
    python -m uvicorn src.inbox.whatsapp_webhook:app --host 0.0.0.0 --port 8080

Then point your Meta app's webhook at https://<host>/whatsapp/webhook with the
same verify token, subscribed to the `messages` field.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from .sources.whatsapp import DEFAULT_INBOX_FILE, normalize_cloud_api_value

app = FastAPI(title="Inbox Agent — WhatsApp webhook")


def _inbox_file() -> Path:
    return Path(os.getenv("WHATSAPP_INBOX_FILE", str(DEFAULT_INBOX_FILE)))


@app.get("/whatsapp/webhook")
def verify(
    hub_mode: str = Query("", alias="hub.mode"),
    hub_verify_token: str = Query("", alias="hub.verify_token"),
    hub_challenge: str = Query("", alias="hub.challenge"),
) -> PlainTextResponse:
    expected = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
    if hub_mode == "subscribe" and expected and hub_verify_token == expected:
        return PlainTextResponse(hub_challenge)
    raise HTTPException(status_code=403, detail="verify token mismatch")


@app.post("/whatsapp/webhook")
async def receive(request: Request) -> dict[str, Any]:
    payload = await request.json()
    records: list[dict[str, Any]] = []
    for entry in payload.get("entry") or []:
        for change in entry.get("changes") or []:
            if change.get("field") != "messages":
                continue
            records.extend(normalize_cloud_api_value(change.get("value") or {}))

    if records:
        inbox = _inbox_file()
        inbox.parent.mkdir(parents=True, exist_ok=True)
        with inbox.open("a") as fh:
            for record in records:
                fh.write(json.dumps(record) + "\n")

    return {"stored": len(records)}
