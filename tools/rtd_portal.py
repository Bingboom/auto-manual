"""Root-only Sphinx portal over frozen publications; no live data or writes."""
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from tools.utils.path_utils import PathSegments, static_dir_of

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


def catalog(root: Path, settings: dict) -> list[dict[str, str]]:
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
        })
    order = list(settings["categories"])
    return sorted(records, key=lambda p: (order.index(p["category"]), p["model"], p["region"]))


def configure(app, config) -> None:
    # Absolute engineering assets are independent of the frozen source config.
    config.templates_path = [str(ASSETS), *config.templates_path]
    config.html_static_path = [*config.html_static_path, str(ASSETS / PathSegments.STATIC)]


def page_context(app, pagename, templatename, context, doctree):
    if pagename != app.config.root_doc:
        return None
    settings = json.loads((ASSETS / "settings.json").read_text(encoding="utf-8"))
    products = catalog(Path(app.srcdir).resolve(), settings)
    if not products:
        return None
    context["portal"] = settings
    context["products"] = products
    return "manual_portal.html"


def setup(app):
    app.connect("config-inited", configure)
    app.connect("html-page-context", page_context)
    return {"version": "1", "parallel_read_safe": True, "parallel_write_safe": True}
