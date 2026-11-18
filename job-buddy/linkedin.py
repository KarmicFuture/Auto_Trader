"""Sign In with LinkedIn using OpenID Connect."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlencode

import requests

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
SCOPES = "openid profile email"


def configured() -> bool:
    return bool(client_id() and client_secret())


def client_id() -> str:
    return os.environ.get("LINKEDIN_CLIENT_ID", "").strip()


def client_secret() -> str:
    return os.environ.get("LINKEDIN_CLIENT_SECRET", "").strip()


def redirect_uri() -> str:
    return os.environ.get(
        "LINKEDIN_REDIRECT_URI",
        "http://localhost:3040/api/auth/linkedin/callback",
    ).strip()


def authorization_url(state: str) -> str:
    params = {
        "response_type": "code",
        "client_id": client_id(),
        "redirect_uri": redirect_uri(),
        "state": state,
        "scope": SCOPES,
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def exchange_code(code: str) -> dict[str, Any]:
    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri(),
            "client_id": client_id(),
            "client_secret": client_secret(),
        },
        headers={"Accept": "application/json"},
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    if "access_token" not in payload:
        raise RuntimeError(payload.get("error_description") or "LinkedIn did not return an access token.")
    return payload


def fetch_userinfo(access_token: str) -> dict[str, Any]:
    response = requests.get(
        USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()
