#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import fnmatch
import html
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Mapping

from bs4 import BeautifulSoup, NavigableString, Tag

from tools.component_specs.fcc import COMPONENT_ID
from tools.component_specs.fcc_adapters import word_fcc_projection
from tools.component_specs.fcc_html import parse_fcc_html
from tools.component_specs.spec_table import (
    spec_table_component_spec,
    word_spec_table_projection,
)
from tools.csv_pages.renderers import rst_escape


def _render_cover_html(title: str) -> str:
    title_html = html.escape(rst_escape(title))
    return "".join(
        [
            '<section class="manual-cover">',
            f'<div class="cover-title">{title_html}</div>',
            "</section>",
        ]
    )


class _AnchorTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._texts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split()).strip()
        if text:
            self._texts.append(text)

    @property
    def first_text(self) -> str:
        return self._texts[0] if self._texts else ""


def _extract_word_anchor_text(fragment: str) -> str:
    parser = _AnchorTextParser()
    parser.feed(fragment)
    return parser.first_text


def _render_page_break_html() -> str:
    return '<div class="manual-page-break"></div>'


def _render_safety_item_html(text: str) -> str:
    raw = rst_escape(text)
    parts = [part.strip() for part in raw.split("\\n") if part.strip()]
    if not parts:
        return ""

    head = html.escape(parts[0])
    extra_lines: list[str] = []
    sub_items: list[str] = []
    for part in parts[1:]:
        if part.startswith("- "):
            sub_items.append(f"<li>{html.escape(part[2:].strip())}</li>")
        else:
            extra_lines.append(html.escape(part))

    body = head
    if extra_lines:
        body += "<br/>" + "<br/>".join(extra_lines)
    if sub_items:
        body += '<ul>' + "".join(sub_items) + "</ul>"
    return f"<li>{body}</li>"


def render_safety_word_html(data: dict[str, object]) -> str:
    top_items = [str(item) for item in data["top_items"]]
    bottom_items = [str(item) for item in data["bottom_items"]]
    return "".join(
        [
            '<section class="manual-section safety-section">',
            f"<h1>{html.escape(rst_escape(str(data['title_main'])))}</h1>",
            f"<p><strong>{html.escape(rst_escape(str(data['warning_title'])))}</strong></p>",
            f"<p>{html.escape(rst_escape(str(data['lead_top'])))}</p>",
            "<ul>",
            "".join(_render_safety_item_html(item) for item in top_items),
            "</ul>",
            f"<h2>{html.escape(rst_escape(str(data['title_operating'])))}</h2>",
            f"<p><strong>{html.escape(rst_escape(str(data['save_title'])))}</strong></p>",
            "<ul>",
            "".join(_render_safety_item_html(item) for item in bottom_items),
            "</ul>",
            "</section>",
        ]
    )


def _render_table_cell_html(text: str) -> str:
    lines = [html.escape(rst_escape(x)) for x in rst_escape(text).replace("\\n", "\n").splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        return ""
    return "<br/>".join(lines)


def _split_spec_value_lines(text: str) -> list[str]:
    lines = [line for line in str(text).replace("\\n", "\n").splitlines()]
    return [line for line in lines if line.strip()]


def render_spec_word_html(data: dict[str, object]) -> str:
    parts = [
        '<section class="manual-section spec-section">',
        f"<h1>{html.escape(rst_escape(str(data['title_main'])))}</h1>",
    ]

    for section_index, section in enumerate(data["sections"]):
        raw_title = str(section["title"])
        spec = spec_table_component_spec(
            section_title=raw_title,
            rows=section["rows"],
            source_ref=f"word:spec:{section_index}:{raw_title}",
            language=str(data.get("language") or "und"),
        )
        projection = word_spec_table_projection(spec)
        title = html.escape(rst_escape(str(projection["title"]))).upper()
        parts.append(
            '<h2 class="hb-spec-section">'
            '<span class="hb-spec-bullet" aria-hidden="true">&#9679;</span>'
            f'<span class="hb-spec-section-text">{title}</span>'
            "</h2>"
        )
        parts.append('<table class="manual-table manual-spec-table">')
        parts.append("<tbody>")
        for group in projection["groups"]:
            left = str(group["label"])
            right_lines = [
                line
                for value in group["values"]
                for line in _split_spec_value_lines(str(value["text"]))
            ]
            if not right_lines:
                right_lines = [""]
            if len(right_lines) == 1:
                parts.append("<tr>")
                parts.append(f'<td class="manual-spec-label">{_render_table_cell_html(str(left))}</td>')
                parts.append(f'<td class="manual-spec-value">{_render_table_cell_html(right_lines[0])}</td>')
                parts.append("</tr>")
                continue

            parts.append("<tr>")
            parts.append(
                f'<td class="manual-spec-label" rowspan="{len(right_lines)}">{_render_table_cell_html(str(left))}</td>'
            )
            parts.append(f'<td class="manual-spec-value">{_render_table_cell_html(right_lines[0])}</td>')
            parts.append("</tr>")
            for line in right_lines[1:]:
                parts.append("<tr>")
                parts.append(f'<td class="manual-spec-value">{_render_table_cell_html(line)}</td>')
                parts.append("</tr>")
        parts.append("</tbody>")
        parts.append("</table>")

    trailers: list[tuple[str, str]] = []
    raw_trailers = data.get("trailers")
    if isinstance(raw_trailers, list):
        for item in raw_trailers:
            if not isinstance(item, (tuple, list)) or len(item) != 2:
                continue
            kind = str(item[0]).strip().lower()
            text = str(item[1])
            if kind not in {"note", "footnote"} or not text:
                continue
            trailers.append((kind, text))

    if not trailers:
        notes = [str(note) for note in data.get("notes", [])]
        footnotes = [str(footnote) for footnote in data.get("footnotes", [])]
        if notes and footnotes:
            raise ValueError(
                "spec trailer order must come from the upstream HTML fragment; "
                "do not reconstruct note/footnote order inside Word rendering"
            )
        trailers = [("note", note) for note in notes]
        trailers.extend(("footnote", footnote) for footnote in footnotes)
    if trailers:
        parts.append('<p class="manual-spec-trailer-spacer" aria-hidden="true">&#160;</p>')
    for kind, text in trailers:
        class_name = "manual-spec-note" if kind == "note" else "manual-spec-footnote"
        parts.append(f'<p class="{class_name}">{_render_table_cell_html(text)}</p>')

    parts.append("</section>")
    return "".join(parts)


def _append_word_fcc_paragraph_content(
    soup: BeautifulSoup,
    paragraph: Tag,
    block: Mapping[str, Any],
    *,
    continuation: bool,
) -> None:
    if continuation:
        paragraph.append(NavigableString(" "))
    label_text = str(block.get("label") or "").strip()
    if label_text:
        label = soup.new_tag("strong")
        label.string = label_text
        paragraph.append(label)
    body = str(block.get("text") or "").strip()
    if body:
        paragraph.append(NavigableString(f" {body}" if label_text else body))


def _append_word_fcc_blocks(
    soup: BeautifulSoup,
    parent: Tag,
    blocks: list[Mapping[str, Any]],
) -> None:
    paragraph: Tag | None = None
    for block in blocks:
        if block["kind"] != "list":
            if paragraph is None:
                paragraph = soup.new_tag("p")
                parent.append(paragraph)
            _append_word_fcc_paragraph_content(
                soup,
                paragraph,
                block,
                continuation=bool(paragraph.contents),
            )
            continue

        paragraph = None
        list_node = soup.new_tag("ul")
        for text in block["items"]:
            item = soup.new_tag("li")
            item.string = str(text)
            list_node.append(item)
        parent.append(list_node)


def transform_word_fcc_html(
    html_fragment: str,
    *,
    source_path: Path,
    config: Mapping[str, Any],
) -> str:
    patterns = [str(pattern).lower() for pattern in config["source_patterns"]]
    if not any(fnmatch.fnmatch(source_path.stem.lower(), pattern) for pattern in patterns):
        return html_fragment
    soup = BeautifulSoup(html_fragment, "html.parser")
    source = parse_fcc_html(
        soup,
        source_path=source_path,
        config=config,
        error_type=RuntimeError,
    )
    projection = word_fcc_projection(source.spec)
    table = soup.new_tag(
        "table",
        attrs={
            "class": ["manual-table", projection["table_class"]],
            "aria-label": projection["accessibility_label"],
            "data-component-id": COMPONENT_ID,
            "style": "width:100%;border-collapse:separate;background:#f2f2f2;",
        },
    )
    body = soup.new_tag("tbody")
    row = soup.new_tag("tr")
    left = soup.new_tag(
        "td",
        attrs={
            "class": projection["left_class"],
            "style": "width:50%;padding:10px;vertical-align:top;background:#f2f2f2;",
        },
    )
    right = soup.new_tag(
        "td",
        attrs={
            "class": projection["right_class"],
            "style": "width:50%;padding:10px;vertical-align:top;background:#f2f2f2;",
        },
    )
    mark = soup.new_tag(
        "img",
        attrs={
            "src": str(config["mark_path"]),
            "alt": projection["accessibility_label"],
            "style": "width:88px;height:auto;float:left;margin:0 10px 6px 0;",
        },
    )
    left.append(mark)
    for line in projection["opening_copy"]:
        paragraph = soup.new_tag("p")
        paragraph.string = str(line)
        left.append(paragraph)
    _append_word_fcc_blocks(soup, left, projection["left_blocks"])
    _append_word_fcc_blocks(soup, right, projection["right_blocks"])
    row.append(left)
    row.append(right)
    body.append(row)
    table.append(body)
    for node in source.consumed_nodes:
        node.decompose()
    source.heading.insert_after(table)
    return str(soup)
