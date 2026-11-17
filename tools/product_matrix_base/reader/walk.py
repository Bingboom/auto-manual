"""Walk one published manual and return every row of its specification and specification-like tables.

The manual is Markdown with embedded HTML. Markdown headings and HTML headings build one heading path. A heading that
names the specifications opens a specification region at its level; a later heading at the same or a higher level
keeps the region open only when the next table is a specification-class table (specification groups printed as
sibling headings), and closes it otherwise. Tables are classified by ``markup.classify_table``; ``spec-row`` lists
(label and value paragraphs) count as specification rows.
"""
from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Any

from bs4 import BeautifulSoup, Tag

from tools.product_matrix_base.reader.markup import (
    LINE_SEP, SPEC_CLASS, SPEC_HEADING, classify_table, clean_text, described_product, direct_rows, parse_table,
    sup_markers, text_without_markers,
)

_STYLE_OPEN, _STYLE_CLOSE = re.compile(r"<style", re.I), re.compile(r"</style>", re.I)
_MD_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_MD_ANCHOR = re.compile(r"\s*\{#([^}]+)\}\s*$")
_SPAN_ID = re.compile(r'^\s*<span id="([^"]+)"></span>\s*$')
_MYST_LABEL = re.compile(r"^\(([^)]+)\)=\s*$")


def _heading_text(raw: str) -> tuple[str, str]:
    """A Markdown heading's words and its anchor ({#id} suffix or an inner element id)."""
    anchor = ""
    match = _MD_ANCHOR.search(raw)
    if match:
        anchor, raw = match.group(1), raw[: match.start()]
    soup = BeautifulSoup(raw, "html.parser")
    inner = soup.find(id=True)
    if inner is not None and not anchor:
        anchor = inner.get("id", "")
    text = clean_text(soup).replace(LINE_SEP, " ")
    return re.sub(r"\\(['\"])", r"\1", text).strip(), anchor


def chunks(text: str) -> Iterator[tuple]:
    """('heading', level, text, anchor) for Markdown headings and ('html', fragment) for what lies between."""
    buffer: list[str] = []
    in_style = False
    pending_anchor = ""
    for line in text.split("\n"):
        if in_style:
            in_style = not _STYLE_CLOSE.search(line)
            continue
        if _STYLE_OPEN.search(line) and not _STYLE_CLOSE.search(line):
            in_style = True
            continue
        heading = _MD_HEADING.match(line)
        if heading:
            if buffer:
                yield ("html", "\n".join(buffer))
                buffer = []
            words, anchor = _heading_text(heading.group(2))
            yield ("heading", len(heading.group(1)), words, anchor or pending_anchor)
            pending_anchor = ""
            continue
        label = _SPAN_ID.match(line) or _MYST_LABEL.match(line)
        if label:
            pending_anchor = label.group(1)
        elif line.strip():
            pending_anchor = ""
        buffer.append(line)
    if buffer:
        yield ("html", "\n".join(buffer))


def _items(soup: BeautifulSoup) -> Iterator[tuple[str, Tag]]:
    """HTML headings, spec-title and spec-row blocks, and outermost tables, in document order."""
    for node in soup.descendants:
        if not isinstance(node, Tag) or node.find_parent("table") is not None:
            continue
        if node.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            yield ("heading", node)
        elif node.name == "table":
            yield ("table", node)
        elif node.get("data-source-layout") in ("spec-title", "spec-row"):
            yield (node.get("data-source-layout"), node)


class ManualWalk:
    """The heading path and specification region while one manual is read."""

    def __init__(self, identity: dict[str, Any]) -> None:
        self.identity = identity
        self.stack: list[tuple[int, str, str]] = []
        self.region: dict[str, Any] | None = None
        self.base_level = 0
        self.subtitle = ("", "")
        self.spec_seen = False
        self.table_index = 0
        self.spec_row_index = 0
        self.rows: list[dict[str, Any]] = []

    def heading(self, level: int, words: str, anchor: str) -> None:
        while self.stack and self.stack[-1][0] >= level:
            self.stack.pop()
        self.stack.append((level, words, anchor))
        self.subtitle = ("", "")
        if SPEC_HEADING.search(words):
            self.spec_seen = True
            self.region = {"level": level, "heading": words, "candidate": False}
        elif self.region is not None:
            if self.region["candidate"]:
                self.region = None
            elif level <= self.region["level"]:
                self.region["candidate"] = True

    def html(self, fragment: str) -> None:
        for kind, node in _items(BeautifulSoup(fragment, "html.parser")):
            if kind == "heading":
                inner = node.find(id=True)
                anchor = node.get("id", "") or (inner.get("id", "") if inner is not None else "")
                self.heading(self.base_level + int(node.name[1]), clean_text(node).replace(LINE_SEP, " "), anchor)
            elif kind == "spec-title":
                self.subtitle = (clean_text(node).replace(LINE_SEP, " "), node.get("id", ""))
            else:
                self._block(kind, node)

    def _settle_candidate(self, kind: str, node: Tag) -> None:
        """A region left open after a sibling heading stays only if this block is specification-class."""
        if self.region is not None and self.region["candidate"]:
            if kind == "spec-row" or SPEC_CLASS.search(" ".join(node.get("class") or [])):
                self.region["candidate"] = False
            else:
                self.region = None

    def _context(self) -> dict[str, Any]:
        path = " > ".join(words for _level, words, _anchor in self.stack)
        anchor = next((a for _level, _words, a in reversed(self.stack) if a), "")
        section = path + (f" > {self.subtitle[0]}" if self.subtitle[0] else "")
        return {**self.identity, "section_path": section,
                "spec_section_heading": self.region["heading"] if self.region else "",
                "anchor_id": self.subtitle[1] or anchor, "html_subheading": self.subtitle[0],
                "described_product": described_product(section)}

    def _block(self, kind: str, node: Tag) -> None:
        self._settle_candidate(kind, node)
        in_spec = self.region is not None and not self.region["candidate"]
        base = self._context()
        if kind == "spec-row":
            self._spec_row(node, base, in_spec)
            return
        self.table_index += 1
        table_kind = classify_table(node, in_spec, base["section_path"])
        if table_kind.startswith("skip"):
            return
        classes = " ".join(node.get("class") or [])
        for row in parse_table(node):
            self.rows.append({**base, "table_kind": table_kind, "table_index": self.table_index,
                              "table_class": classes, "row_index": row["row_index"], "row_type": row["row_type"],
                              "col_index": row["col_index"], "col_header": row["col_header"],
                              "table_subheading": row["subheading"], "row_label": row["label"],
                              "row_label_clean": row["label_clean"].rstrip(":：").strip(), "value_text": row["value"],
                              "footnote_markers": " ".join(row["markers"]),
                              "rowspan_continuation": "yes" if row["rowspan_cont"] else "no"})

    def _spec_row(self, node: Tag, base: dict[str, Any], in_spec: bool) -> None:
        paragraphs = node.find_all("p", recursive=False) or node.find_all("p")
        if len(paragraphs) < 2:
            return
        self.spec_row_index += 1
        self.rows.append({**base, "table_kind": "spec_section" if in_spec else "spec_class_elsewhere",
                          "table_index": "specrow-list", "table_class": "data-source-layout=spec-row",
                          "row_index": self.spec_row_index, "row_type": "pair", "col_index": 1, "col_header": "",
                          "table_subheading": "", "row_label": clean_text(paragraphs[0]),
                          "row_label_clean": text_without_markers(paragraphs[0]).rstrip(":：").strip(),
                          "value_text": LINE_SEP.join(clean_text(p) for p in paragraphs[1:]),
                          "footnote_markers": " ".join(sup_markers(node)), "rowspan_continuation": "no"})


def read_manual(text: str, identity: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    """Every captured row of one manual, and whether it has a specification heading at all."""
    walk = ManualWalk(identity)
    for chunk in chunks(text):
        if chunk[0] == "heading":
            walk.base_level = chunk[1]
            walk.heading(chunk[1], chunk[2], chunk[3])
        else:
            walk.html(chunk[1])
    return walk.rows, walk.spec_seen


__all__ = ["ManualWalk", "chunks", "direct_rows", "read_manual"]
