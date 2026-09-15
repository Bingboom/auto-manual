"""Optional, cookieless Cloudflare Web Analytics beacon for frozen Web pages."""
from __future__ import annotations

import json
import re
from html import escape

BEACON_SRC = "https://static.cloudflareinsights.com/beacon.min.js"
_TOKEN = re.compile(r"^[0-9a-f]{32}$")


def normalize_beacon_token(raw: object) -> str:
    """Return the configured beacon token, or '' when analytics stays off."""
    if raw is None:
        return ""
    if not isinstance(raw, str):
        raise ValueError("analytics_beacon_token must be a string")
    token = raw.strip()
    if not token:
        return ""
    if not _TOKEN.fullmatch(token):
        raise ValueError("analytics_beacon_token must be 32 lowercase hex characters")
    return token


def beacon_attributes(token: str) -> dict[str, str]:
    """Attributes for the beacon script tag; the token is the only payload."""
    return {"data-cf-beacon": json.dumps({"token": token})}


def beacon_markup(token: str) -> str:
    """Beacon script tag for templates that render their own head; '' when off."""
    if not token:
        return ""
    payload = escape(json.dumps({"token": token}), quote=True)
    return f'<script defer src="{BEACON_SRC}" data-cf-beacon="{payload}"></script>'
