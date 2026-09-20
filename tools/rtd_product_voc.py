"""Opt-in product suggestions; no credentials or live requests during a build."""
from __future__ import annotations

from html import escape

from tools.rtd_feedback import normalize_channels


def normalize_endpoint(raw: object) -> str:
    if raw in (None, ""):
        return ""
    if not isinstance(raw, str) or not raw.startswith("https://"):
        raise ValueError("product_voc_endpoint must be a fixed HTTPS URL")
    return normalize_channels([{"label": "Product suggestions", "url": raw}])[0]["url"]


def suggestion_markup(*, endpoint: str, model: str = "", context: str = "") -> str:
    """The caller supplies frozen context, never window.location or visitor identity."""
    if not endpoint:
        return ""
    return (
        '<details class="product-voc" id="product-suggestions" lang="en" dir="ltr">'
        '<summary>Suggest a product improvement</summary>'
        '<form data-product-voc method="post" data-endpoint="'
        + escape(endpoint, quote=True) + '">'
        '<p>What would make your Jackery product better? No Feishu account is needed.</p>'
        '<p>Your suggestion and the manual context below will be stored in Feishu '
        'for product research. Do not include names, contact details, order numbers '
        'or other personal information. For service requests, use the support '
        'contact in your manual.</p>'
        '<fieldset disabled><legend>Product improvement suggestion</legend>'
        '<label>Product model <input name="model" required maxlength="100" value="'
        + escape(model, quote=True) + '" autocomplete="off"></label>'
        '<label>Your suggestion <textarea name="suggestion" required minlength="5" '
        'maxlength="3000" rows="5" placeholder="What would you change, and how would '
        'it help you?"></textarea></label>'
        '<label>Use case (optional) <textarea name="use_case" maxlength="1000" '
        'rows="2" placeholder="When or where would this improvement help?"></textarea></label>'
        '<input type="hidden" name="context" value="' + escape(context, quote=True) + '">'
        '<div class="product-voc-trap" aria-hidden="true"><label>Leave blank '
        '<input name="website" tabindex="-1" autocomplete="off"></label></div>'
        '<p>Included manual context:</p><pre>' + escape(context or "Manual Center home")
        + '</pre><button type="submit">Send suggestion</button></fieldset>'
        '<p class="product-voc-status" role="status" aria-live="polite"></p>'
        '<noscript>Enable JavaScript to send a suggestion. Nothing has been submitted.</noscript>'
        '</form></details>'
    )


def page_markup(*, endpoint: str, publications: list[dict], pagename: str, root: str) -> str:
    if pagename == root:
        return suggestion_markup(endpoint=endpoint, context="Manual Center home")
    active = next((item for item in publications if item["url"] == f"{pagename}.html"), None)
    if not active:
        return ""
    # Legacy pages can collect suggestions without claiming a verified locale/version.
    context = "\n".join(f"{label}: {value}" for label, value in (
        ("Model", active["model"]), ("Region", active["region"]),
        ("Language", active.get("lang") if active.get("language_scope") == "single" else "unverified"),
        ("Version", active.get("version") or "unverified"), ("Page", active["url"]),
    ))
    return suggestion_markup(endpoint=endpoint, model=active["model"], context=context)
