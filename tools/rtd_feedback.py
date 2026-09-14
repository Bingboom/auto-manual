"""Optional, local-only feedback affordances for frozen Web publications."""
from __future__ import annotations

from html import escape
from urllib.parse import urlsplit


def normalize_channels(raw: object) -> list[dict[str, str]]:
    """Return fixed HTTPS destinations; never attach publication data to URLs."""
    if not isinstance(raw, list):
        raise ValueError("feedback_channels must be a list")
    channels: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("feedback channel must be an object")
        raw_label = str(item.get("label") or "")
        raw_url = str(item.get("url") or "")
        if any(ord(char) < 0x20 or ord(char) == 0x7F for char in f"{raw_label}{raw_url}"):
            raise ValueError("feedback channel contains a control character")
        label = raw_label.strip()
        url = raw_url.strip()
        if not label or not url:
            raise ValueError("feedback channel needs label and url")
        try:
            parsed = urlsplit(url)
            hostname = parsed.hostname
            parsed.port
        except ValueError as exc:
            raise ValueError("invalid feedback channel URL") from exc
        if (
            parsed.scheme != "https" or not parsed.netloc or not hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.query or parsed.fragment or any(char.isspace() for char in hostname)
            or "\\" in url or "%" in hostname
        ):
            raise ValueError("feedback channel URL must be HTTPS without credentials, query, or fragment")
        if url in seen:
            raise ValueError("duplicate feedback channel URL")
        seen.add(url)
        channels.append({"label": label, "url": url})
    return channels


def context_text(*, model: str, region: str, lang: str, version: str, page: str) -> str:
    """Plain context the user may intentionally copy into an existing channel."""
    fields = (model, region, lang, version, page)
    if not all(isinstance(value, str) and value.strip() for value in fields):
        return ""
    return (
        f"Manual feedback context\n"
        f"Model: {model}\nRegion: {region}\nLanguage: {lang}\nVersion: {version}\nPage: {page}"
    )


def manual_feedback_markup(*, channels: list[dict[str, str]], context: str) -> str:
    """Render safe markup only when an operator configured at least one channel."""
    if not channels or not context:
        return ""
    links = " ".join(
        f'<a href="{escape(item["url"], quote=True)}" rel="noreferrer">'
        f'{escape(item["label"])}</a>'
        for item in channels
    )
    return (
        '<aside class="manual-feedback" aria-label="Manual feedback">'
        '<span>Found an issue?</span> '
        '<button type="button" data-copy-feedback>Copy context</button> '
        f'<pre class="manual-feedback-context">{escape(context)}</pre> '
        f'<span class="manual-feedback-channels">{links}</span>'
        '<span class="manual-feedback-status" aria-live="polite"></span>'
        '</aside>'
    )
