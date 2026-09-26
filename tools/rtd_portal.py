"""Root-only Sphinx portal over frozen publications; no live data or writes."""
from __future__ import annotations

import json
import re
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from tools.utils.path_utils import PathSegments, repo_root, static_dir_of
from tools.rtd_publication_catalog import group_publications, publication_identity
from tools.rtd_analytics import BEACON_SRC, beacon_attributes, beacon_markup, normalize_beacon_token
from tools.rtd_alias_entry import alias_head_markup, alias_targets, delayed_forward_body
from tools.rtd_deliverables import DELIVERABLES_PAGE, DELIVERABLES_TEMPLATE, deliverables_page_context
from tools.rtd_feedback import context_text, manual_feedback_markup, normalize_channels
from tools.rtd_product_voc import normalize_endpoint, page_markup
from tools.rtd_page_metadata import (
    head_markup, normalize_site_base_url, page_description, page_title, portal_head_markup,
)
from tools.rtd_system_workspace import SYSTEM_PAGE, SYSTEM_TEMPLATE, system_page_context
from tools.safe_copy import copytree_replace_no_symlinks

ASSETS = Path(__file__).with_name("rtd_portal_assets")
_LINK = re.compile(r"^- \[([^\n]+)\]\(([^\s]+\.md)\)\s*$", re.MULTILINE)


def local_file(root: Path, relative: str) -> Path | None:
    """Refuse external, absolute, fragment and escaping catalog/asset paths."""
    parts = urlsplit(relative)
    if parts.scheme or parts.netloc or parts.query or parts.fragment:
        return None
    path = Path(unquote(parts.path))
    if path.is_absolute():
        return None
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
        return None
    return resolved


class ProductImage(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.sources: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "img" and "hb-inbox-art" in (values.get("class") or "").split():
            if src := values.get("src"):
                self.sources.append(src)


def product_image(source: Path, root: Path) -> str:
    parser = ProductImage()
    parser.feed(source.read_text(encoding="utf-8"))
    if not parser.sources:
        return ""
    src = parser.sources[0]
    # Resolve from the manual, then constrain to the frozen static subtree.
    if urlsplit(src).scheme or urlsplit(src).netloc:
        return ""
    candidate = source.parent / unquote(urlsplit(src).path)
    try:
        relative = candidate.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return ""
    asset = local_file(root, relative)
    if asset and asset.is_relative_to(static_dir_of(root).resolve()):
        return relative
    return ""


def catalog(root: Path, settings: dict) -> list[dict]:
    """Project only explicit existing index links; never synthesize locales."""
    records = []
    index = root / "index.md"
    if not index.is_file():
        return records
    for label, target in _LINK.findall(index.read_text(encoding="utf-8")):
        source = local_file(root, target)
        if source is None:
            raise ValueError(f"Missing or unsafe portal manual link: {target}")
        parts = source.relative_to(root.resolve()).parts
        if len(parts) < 4:
            continue
        model, region = parts[:2]
        name = label.split(" - ", 1)[-1]
        name = re.sub(r"^Jackery\s+|\s+User Manual$", "", name)
        category = next(
            (name for prefix, name in settings["category_prefixes"].items() if model.startswith(prefix)),
            "Accessories",
        )
        records.append({
            "model": model, "region": region, "name": name, "category": category,
            "edition": "EUUK" if region == "EU" else region,
            "url": source.relative_to(root.resolve()).with_suffix(".html").as_posix(),
            "image": product_image(source, root), "label": label,
            **publication_identity(root, source, model=model, region=region),
        })
    order = list(settings["categories"])
    records = group_publications(records, settings["language_labels"])
    return sorted(records, key=lambda p: (order.index(p["category"]), p["model"], p["region"]))


def without_leading_language_label(body: str, label: str) -> str:
    """Omit only a plain leading locale paragraph duplicated by the switcher."""
    match = re.match(r"\s*<p>([^<>]*)</p>\s*", body)
    if match and unescape(match.group(1)).strip() == label:
        return body[match.end():]
    return body


def configure(app, config) -> None:
    config.html_title = "Manual Center"
    # Absolute engineering assets are independent of the frozen source config.
    config.templates_path = [str(ASSETS), *config.templates_path]
    config.html_static_path = [*config.html_static_path, str(ASSETS / PathSegments.STATIC)]


def portal_data(app) -> tuple[dict, list[dict]]:
    """Validate frozen publications once per build, not once per output page."""
    cached = getattr(app, "_rtd_portal_data", None)
    if cached is None:
        settings = json.loads((ASSETS / "settings.json").read_text(encoding="utf-8"))
        cached = (settings, catalog(Path(app.srcdir).resolve(), settings))
        app._rtd_portal_data = cached
    return cached


def prepare_catalog(app) -> None:
    # Populate before parallel page writers fork; a failed validation is never cached.
    portal_data(app)


def clear_catalog_cache(app, exception) -> None:
    # A later build in the same process must validate its own frozen inputs again.
    app._rtd_portal_data = None


def page_context(app, pagename, templatename, context, doctree):
    settings, products = portal_data(app)
    feedback_channels = normalize_channels(settings.get("feedback_channels", []))
    beacon_token = normalize_beacon_token(settings.get("analytics_beacon_token", ""))
    site_base_url = normalize_site_base_url(settings.get("site_base_url", ""))
    voc_markup = page_markup(
        endpoint=normalize_endpoint(settings.get("product_voc_endpoint", "")),
        publications=[item for product in products for item in product["publications"]],
        pagename=pagename, root=app.config.root_doc,
    )
    if voc_markup and pagename != app.config.root_doc:
        context["body"] = context.get("body", "") + voc_markup
        app.add_js_file("product-voc.js")
        app.add_css_file("product-voc.css")
    if beacon_token:
        app.add_js_file(BEACON_SRC, loading_method="defer", **beacon_attributes(beacon_token))
    if pagename == "search":
        app.add_css_file("manual-search.css")
        return None
    if pagename != app.config.root_doc:
        if "/" not in pagename:
            alias_target = alias_targets(products).get(pagename)
            if alias_target:
                context["metatags"] = context.get("metatags", "") + alias_head_markup(
                    target_url=alias_target, site_base_url=site_base_url,
                )
                if beacon_token:
                    context["body"] = delayed_forward_body(
                        context.get("body", ""), target_url=alias_target,
                    )
                return None
        for product in products:
            active = next((p for p in product["publications"]
                           if p["url"] == f"{pagename}.html" and p["language_scope"] == "single"), None)
            if active is None:
                continue
            context["language"] = active["lang"]
            direction = "rtl" if active["lang"] in settings.get("rtl_languages", []) else "ltr"
            options = []
            for item in product["language_options"]:
                url = context["pathto"](item["url"][:-5]) if item["url"] else ""
                if url == "#":
                    url = Path(item["url"]).name
                state = ' selected' if item["url"] == active["url"] else ''
                if not url:
                    state += ' disabled'
                label = item["label"] + (f' — {item["unavailable_reason"]}' if not url else "")
                options.append(f'<option value="{escape(url, quote=True)}"{state}>{escape(label)}</option>')
            feedback_context = context_text(
                model=active["model"], region=active["region"],
                lang=active["lang"], version=active.get("version") or "",
                page=active["url"],
            )
            lang_label = settings.get("language_labels", {}).get(active["lang"], active["lang"])
            derived_title = page_title(
                name=product.get("name") or "", model=active["model"],
                region=active["region"], lang_label=lang_label,
            )
            context["manual_page_title"] = derived_title
            context["metatags"] = context.get("metatags", "") + head_markup(
                title=derived_title,
                description=page_description(
                    name=product.get("name") or "", model=active["model"],
                    region=active["region"], lang_label=lang_label,
                    version=active.get("version") or "",
                ),
                page_url=active["url"],
                alternates=[(item["code"], item["url"]) for item in product["language_options"]
                            if item.get("url") and item["code"] != "current"],
                site_base_url=site_base_url,
            )
            context["body"] = (
                '<nav class="manual-locale-nav" aria-label="Manual language">'
                f'<span>{escape(product["model"])} · {escape(product["edition"])}</span> '
                '<label for="manual-locale-select">Language </label>'
                '<select id="manual-locale-select">' + ''.join(options) + '</select></nav>'
                + f'<div lang="{escape(active["lang"], quote=True)}" dir="{direction}">'
                + without_leading_language_label(context.get("body", ""), lang_label) + '</div>'
                + manual_feedback_markup(channels=feedback_channels, context=feedback_context)
            )
            app.add_js_file("manual-locales.js")
            if feedback_channels and feedback_context:
                app.add_js_file("manual-feedback.js")
            app.add_css_file("manual-locales.css")
            break
        return None
    if not products:
        return None
    context["portal"] = settings
    context["products"] = products
    context["analytics_beacon"] = beacon_markup(beacon_token)
    context["portal_head_meta"] = portal_head_markup(site_base_url=site_base_url)
    context["product_voc"] = voc_markup
    return "manual_portal.html"


def workspace_content(app) -> Path:
    """Read business-owned content from Hello-Docs, outside mirrored tools."""
    configured = app.config.rtd_knowledge_dir
    return Path(configured) if configured else repo_root() / PathSegments.DOCS / "knowledge"


def collect_workspace_pages(app):
    """Add the workspace entry, its system page and its deliverables page, leaving the manual-center root alone.

    The workspace always exists: the manual center links to it, and the system
    and deliverables pages live inside it. The deliverables page always renders
    (a missing input shows as 无数据); the system page drops out on an authoring
    error. The AI sharing package is an optional entry, so moving or withdrawing
    it hides only its own links.
    """
    has_share = (workspace_content(app) / "ai-share" / "00_打开分享.html").is_file()
    system = system_page_context(app, ASSETS)
    settings, products = portal_data(app)
    names = {(product["model"], product["region"]): product.get("name") or "" for product in products}
    deliverables = deliverables_page_context(app, ASSETS, names, list(settings.get("language_labels") or {}))
    yield "workspace/index", {
        "share_entry": "../ai-share/00_打开分享.html" if has_share else "",
        "system_entry": system is not None,
        "deliverables_entry": True,
    }, "workspace_portal.html"
    if system is not None:
        yield SYSTEM_PAGE, {**system, "has_share": has_share, "deliverables_entry": True}, SYSTEM_TEMPLATE
    yield DELIVERABLES_PAGE, {**deliverables, "has_share": has_share, "system_entry": system is not None}, \
        DELIVERABLES_TEMPLATE


def copy_workspace_content(app, exception) -> None:
    """Copy the reviewed personal reading package into the built static site."""
    if exception is not None:
        return
    source = workspace_content(app) / "ai-share"
    if not source.is_dir():
        return
    output_root = Path(app.outdir)
    copytree_replace_no_symlinks(
        source,
        output_root / "ai-share",
        destination_root=output_root,
        label="personal AI sharing package",
    )


def setup(app):
    from tools.rtd_deployment_receipt import write_deployment_receipt
    from tools.rtd_portal_search import write_search_index

    app.add_config_value("rtd_knowledge_dir", "", "html")
    # ISO date for the system and deliverables pages' staleness rules; empty means the build date (UTC).
    app.add_config_value("rtd_system_workspace_date", "", "html")
    app.connect("config-inited", configure)
    app.connect("builder-inited", prepare_catalog)
    app.connect("html-page-context", page_context)
    app.connect("html-collect-pages", collect_workspace_pages)
    # Generated conf.py copies manual assets at the default priority (500).
    app.connect("build-finished", copy_workspace_content, priority=800)
    app.connect("build-finished", write_search_index, priority=900)
    app.connect("build-finished", write_deployment_receipt, priority=1000)
    app.connect("build-finished", clear_catalog_cache, priority=1100)
    return {"version": "1", "parallel_read_safe": True, "parallel_write_safe": True}
