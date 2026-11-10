"""Optional, local-only feedback affordances for frozen Web publications."""
from __future__ import annotations

import re
from html import escape
from urllib.parse import urlsplit

_MAILTO_ADDRESS = re.compile(r"^[A-Za-z0-9._+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$")


def normalize_channels(raw: object) -> list[dict[str, str]]:
    """Return fixed HTTPS or plain-mailto destinations; never attach publication data."""
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
        if url.lower().startswith("mailto:"):
            # A single plain address; the shape excludes ?, #, %, commas and
            # spaces, so no headers or extra recipients can be smuggled in.
            if not _MAILTO_ADDRESS.fullmatch(url[len("mailto:"):]):
                raise ValueError("feedback mailto channel must be a single plain address")
            if url in seen:
                raise ValueError("duplicate feedback channel URL")
            seen.add(url)
            channels.append({"label": label, "url": url})
            continue
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


def channel_label(channel: dict[str, str], words: dict[str, str]) -> str:
    """A mailto channel reads as the frame's email phrase in the page's language; an HTTPS one keeps its label."""
    url = channel["url"]
    if url.lower().startswith("mailto:"):
        return words["email"].replace("{address}", url[len("mailto:"):])
    return channel["label"]


def manual_feedback_markup(*, channels: list[dict[str, str]], context: str,
                           text: tuple[str, dict[str, str]]) -> str:
    """Render safe markup only when an operator configured at least one channel.

    ``text`` is the reading frame's words and the language they are in (tools/rtd/manual_reader.frame_text).
    """
    if not channels or not context:
        return ""
    lang, words = text
    links = " ".join(
        f'<a href="{escape(item["url"], quote=True)}" rel="noreferrer">'
        f'{escape(channel_label(item, words))}</a>'
        for item in channels
    )
    # The card sits under the manual, outside its main region (manual_reader.html). The context stays readable
    # without JavaScript: it is folded, not hidden, and opens when copying is unavailable. The script's two
    # messages ride on the card, in its language.
    return (
        f'<aside class="manual-feedback" aria-label="{escape(words["feedback"], quote=True)}" '
        f'lang="{escape(lang, quote=True)}" data-copied="{escape(words["feedback_copied"], quote=True)}" '
        f'data-copy-failed="{escape(words["feedback_failed"], quote=True)}">'
        f'<div class="manual-feedback-text"><b>{escape(words["feedback_title"])}</b>'
        f'<span>{escape(words["feedback_text"])}</span></div>'
        '<div class="manual-feedback-actions">'
        f'<button type="button" data-copy-feedback>{escape(words["feedback_copy"])}</button>'
        f'<span class="manual-feedback-channels">{links}</span></div>'
        f'<details class="manual-feedback-details"><summary>{escape(words["feedback_show"])}</summary>'
        f'<pre class="manual-feedback-context" lang="en">{escape(context)}</pre></details>'
        '<span class="manual-feedback-status" aria-live="polite"></span>'
        '</aside>'
    )
