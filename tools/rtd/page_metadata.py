"""Page head metadata derived from frozen publication identity; nothing hand-written."""
from __future__ import annotations

from html import escape
from urllib.parse import urlsplit


def normalize_site_base_url(raw: object) -> str:
    """Return the HTTPS site root for absolute URLs, or '' to omit them.

    The root is an origin plus an optional serving prefix such as
    ``/en/latest`` (Read the Docs for Business serves under one); the
    trailing slash is dropped so callers can append ``/<page>``.
    """
    if raw is None:
        return ""
    if not isinstance(raw, str):
        raise ValueError("site_base_url must be a string")
    base = raw.strip()
    if not base:
        return ""
    try:
        parsed = urlsplit(base)
        hostname = parsed.hostname
    except ValueError as exc:
        raise ValueError("invalid site_base_url") from exc
    if (
        parsed.scheme != "https" or not parsed.netloc or not hostname
        or parsed.username is not None or parsed.password is not None
        or parsed.query or parsed.fragment
        or any(part in {".", ".."} for part in parsed.path.split("/"))
        or "//" in parsed.path.rstrip("/")
    ):
        raise ValueError("site_base_url must be an HTTPS origin with an optional path prefix")
    return f"https://{parsed.netloc}{parsed.path.rstrip('/')}"


def page_title(*, name: str, model: str, region: str, lang_label: str) -> str:
    """Search-legible title: product identity first, market and language explicit."""
    subject = " ".join(part.strip() for part in (name, model) if part and part.strip())
    return f"{subject} User Manual ({region} · {lang_label}) · Jackery"


def page_description(*, name: str, model: str, region: str, lang_label: str, version: str) -> str:
    subject = " ".join(part.strip() for part in (name, model) if part and part.strip())
    tail = f" Version {version}." if version.strip() else ""
    return (
        f"Official Jackery user manual for the {subject}, {region} edition, {lang_label}."
        f"{tail} Safety information, operation guide, specifications and troubleshooting."
    )


def head_markup(*, title: str, description: str, page_url: str,
                alternates: list[tuple[str, str]], site_base_url: str) -> str:
    """Meta/link tags for one verified single-language page; absolute URLs only
    when a site origin is configured. Every value is escaped; alternates are
    (hreflang code, site-root-relative url) pairs and include the page itself."""
    lines = [f'<meta name="description" content="{escape(description, quote=True)}" />']
    lines.append(f'<meta property="og:title" content="{escape(title, quote=True)}" />')
    lines.append(f'<meta property="og:description" content="{escape(description, quote=True)}" />')
    lines.append('<meta property="og:site_name" content="Jackery Manual Center" />')
    if site_base_url:
        canonical = f"{site_base_url}/{page_url}"
        lines.append(f'<link rel="canonical" href="{escape(canonical, quote=True)}" />')
        lines.append(f'<meta property="og:url" content="{escape(canonical, quote=True)}" />')
        for code, url in alternates:
            lines.append(
                f'<link rel="alternate" hreflang="{escape(code, quote=True)}"'
                f' href="{escape(f"{site_base_url}/{url}", quote=True)}" />'
            )
    return "\n" + "\n".join(lines)


def portal_head_markup(*, site_base_url: str) -> str:
    """Canonical and share metadata for the portal home page."""
    lines = ['<meta property="og:title" content="Jackery Manual Center" />',
             '<meta property="og:site_name" content="Jackery Manual Center" />']
    if site_base_url:
        lines.append(f'<link rel="canonical" href="{escape(site_base_url, quote=True)}/" />')
        lines.append(f'<meta property="og:url" content="{escape(site_base_url, quote=True)}/" />')
    return "\n".join(lines)
