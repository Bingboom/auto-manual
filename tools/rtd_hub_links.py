"""Validate and project link metadata without copying document bodies."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit


def read_practices(path: Path, audience: str) -> list[dict]:
    entries = json.loads(path.read_text(encoding="utf-8"))["practices"]
    result = []
    for item in entries:
        if audience == "public" and item.get("visibility") != "public":
            continue
        url = urlsplit(item["url"])
        if url.scheme != "https" or url.hostname != "alidocs.dingtalk.com" or url.username or url.password or url.port not in (None, 443):
            raise ValueError("Practice links must use https://alidocs.dingtalk.com")
        if not item.get("title", "").strip() or not isinstance(item.get("tags", []), list):
            raise ValueError("Practice title and tag list are required")
        date = item.get("updated_at", "")
        if date:
            datetime.fromisoformat(date)
        result.append({"title": item["title"], "summary": item.get("summary", ""),
                       "tags": item.get("tags", []), "url": item["url"], "updated_at": date})
    return result

