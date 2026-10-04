"""Semantic reading view of rendered manuals; no OCR or CSS execution."""
from __future__ import annotations

import hashlib
import re

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

from tools.manual_knowledge.identity import callout_severity
from tools.manual_knowledge.tables import content_text, list_entries, table_block

_DECORATIVE = (
    "script", "style", "nav", "form", "button", "select", "input", "svg",
    ".headerlink", ".manual-callout-label-sizer", ".hb-signal-icon",
    ".hb-composite-stage", ".hb-leader-layer", ".hb-operation-step-marker",
    ".manual-feedback", ".product-voc", "[hidden]",
)
_HEADINGS = {f"h{level}" for level in range(1, 7)}


def identity(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def _clean(main: Tag) -> None:
    for element in list(main.select(",".join(_DECORATIVE))):
        if element.parent is not None:
            element.decompose()
    # aria-hidden does not mean visually hidden. For example, an authored
    # button-hold duration can be aria-hidden but is essential product data.
    # Remove only explicit hidden style and known decorative components above.
    for element in list(main.find_all(style=True)):
        if element.parent is None:
            continue
        style = str(element.get("style", ""))
        if re.search(r"(?:^|;)\s*(?:display\s*:\s*none|visibility\s*:\s*hidden)\b", style, re.I):
            element.decompose()


def _list_block(node: Tag) -> dict:
    items = []
    ordered = node.name == "ol"
    reversed_order = node.has_attr("reversed")
    start = str(node.get("start", len(node.find_all("li", recursive=False)) if reversed_order else 1))
    for number, item in list_entries(node):
        copy = BeautifulSoup(str(item), "html.parser").li
        nested = [_list_block(child) for child in item.find_all(["ol", "ul"])
                  if child.find_parent(["ol", "ul"]) is node]
        for child in copy.find_all(["ol", "ul"]):
            child.decompose()
        items.append({"text": content_text(copy), "children": nested, "number": number if ordered else None})
    text = "\n".join((f"{item['number']}. " if ordered else "• ") + item["text"]
                     + "".join("\n" + child["text"] for child in item["children"]) for item in items)
    return {"type": "list", "ordered": ordered, "start": start,
            "reversed": reversed_order, "items": items, "text": text}


def _callout(node: Tag) -> dict | None:
    label = node.select_one(".manual-callout-label, .hb-inbox-tip-label, .admonition-title")
    if label is None:
        return None
    body = node.select_one(".manual-callout-body, .hb-inbox-tip-body")
    if body is None:
        copy = BeautifulSoup(str(node), "html.parser").find()
        title = copy.select_one(".admonition-title")
        if title is not None:
            title.decompose()
        body = copy
    return {"type": "callout", "label": content_text(label), "body": content_text(body),
            "severity": callout_severity(content_text(label)),
            "text": content_text(label) + ": " + content_text(body)}


def _anchor(heading: Tag) -> str:
    if heading.get("id"):
        return str(heading["id"])
    parent = heading.find_parent("section", id=True)
    return str(parent["id"]) if parent else ""


class _Sections:
    def __init__(self, url: str, heading_level: int):
        self.url = url
        self.heading_level = heading_level
        self.sections: list[dict] = []
        self.current = {"title": "Manual introduction", "anchor": "", "blocks": []}

    def flush(self) -> None:
        if self.current["blocks"]:
            self.current["id"] = identity(self.url + "#" + self.current["anchor"])
            for index, block in enumerate(self.current["blocks"]):
                block["block_id"] = f"{self.current['id']}:{index}"
                block["source_ref"] = f"{self.url}#{block.get('anchor') or self.current['anchor']}"
            self.sections.append(self.current)

    def image(self, node: Tag) -> None:
        # Empty decorative images are still counted honestly as untranscribed;
        # alt text is source-authored evidence, not proof of full image coverage.
        alt = str(node.get("alt") or "").strip()
        self.current["blocks"].append({"type": "image", "text": alt,
                                       "evidence_kind": "image_alt", "transcribed": False})

    def walk(self, node: Tag | NavigableString) -> None:
        if isinstance(node, Comment):
            return
        if isinstance(node, NavigableString):
            if value := str(node).strip():
                self.current["blocks"].append({"type": "paragraph", "text": value})
            return
        if node.name in _HEADINGS:
            if int(node.name[1]) == self.heading_level:
                self.flush()
                self.current = {"title": content_text(node), "anchor": _anchor(node), "blocks": []}
            else:
                self.current["blocks"].append({"type": "heading", "level": int(node.name[1]),
                                              "text": content_text(node), "anchor": _anchor(node)})
            return
        is_callout = bool({"manual-callout-table", "admonition", "hb-inbox-tip"}
                          .intersection(node.get("class", [])))
        callout = _callout(node) if is_callout else None
        if callout is not None:
            self.current["blocks"].append(callout)
            return
        if node.name == "table":
            self.current["blocks"].append(table_block(node))
            return
        if node.name in {"ul", "ol"}:
            self.current["blocks"].append(_list_block(node))
            for image in node.find_all("img"):
                self.image(image)
            return
        if node.name == "img":
            self.image(node)
            return
        if node.name in {"p", "pre", "dt", "dd", "figcaption"} or "line-block" in node.get("class", []):
            if value := content_text(node):
                self.current["blocks"].append({"type": "paragraph", "text": value})
            for image in node.find_all("img"):
                self.image(image)
            return
        for child in node.children:
            if isinstance(child, (Tag, NavigableString)):
                self.walk(child)


def extract_sections(html: str, *, url: str) -> tuple[list[dict], dict]:
    soup = BeautifulSoup(html, "html.parser")
    main = soup.select_one("main, [role='main']")
    if main is None:
        raise ValueError(f"Published manual has no main content: {url}")
    _clean(main)
    headings = main.find_all(list(_HEADINGS))
    level = min((int(h.name[1]) for h in headings), default=1)
    parser = _Sections(url, level)
    parser.walk(main)
    parser.flush()
    if not parser.sections:
        raise ValueError(f"Published manual has no queryable content: {url}")
    ids = [section["id"] for section in parser.sections]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Ambiguous chapter anchors in published manual: {url}")
    images = main.find_all("img")
    return parser.sections, {"images": len(images), "images_with_alt": sum(bool(str(i.get("alt") or "").strip()) for i in images),
                             "image_text_coverage": "alt_only_no_ocr"}
