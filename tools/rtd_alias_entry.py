"""Root alias pages as the countable print/QR entry layer over canonical routes."""
from __future__ import annotations

import json
from html import escape
from pathlib import PurePosixPath


def alias_targets(products: list[dict]) -> dict[str, str]:
    """Map each root alias page name to its nested canonical page URL."""
    targets: dict[str, str] = {}
    for product in products:
        for publication in product["publications"]:
            url = publication["url"]
            targets[PurePosixPath(url).stem] = url
    return targets


def alias_head_markup(*, target_url: str, site_base_url: str) -> str:
    """Forwarding pages stay out of search indexes and declare their canonical."""
    lines = ['<meta name="robots" content="noindex" />']
    if site_base_url:
        canonical = f"{site_base_url}/{target_url}"
        lines.append(f'<link rel="canonical" href="{escape(canonical, quote=True)}" />')
    return "\n" + "\n".join(lines)


def forward_markers(target_url: str, *, delayed: bool) -> tuple[str, str]:
    """The generated (meta refresh, script) pair, instant or with a send window."""
    escaped = escape(target_url, quote=True)
    replace = json.dumps(target_url)
    if not delayed:
        return (
            f'<meta http-equiv="refresh" content="0; url={escaped}">',
            f"<script>window.location.replace({replace});</script>",
        )
    return (
        f'<meta http-equiv="refresh" content="4; url={escaped}">',
        "<script>(function () {"
        f" var go = function () {{ window.location.replace({replace}); }};"
        ' window.addEventListener("load", function () { window.setTimeout(go, 200); });'
        " window.setTimeout(go, 2500);"
        " })();</script>",
    )


def delayed_forward_body(body: str, *, target_url: str) -> str:
    """Give the analytics beacon a send window before the alias forwards.

    The alias pageview is the print/QR entry signal, so the instant forward is
    slowed only when both generated markers are present: the JS path navigates
    shortly after the load event (beacon dispatched), the no-JS meta refresh
    becomes the delayed fallback. An unknown alias shape is left unchanged.
    """
    instant_meta, instant_script = forward_markers(target_url, delayed=False)
    if instant_meta not in body or instant_script not in body:
        return body
    delayed_meta, delayed_script = forward_markers(target_url, delayed=True)
    return body.replace(instant_meta, delayed_meta, 1).replace(instant_script, delayed_script, 1)
