#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import html
from html.parser import HTMLParser

from tools.phase1.renderers import rst_escape


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

    for section in data["sections"]:
        title = html.escape(rst_escape(str(section["title"]))).upper()
        parts.append(
            '<h2 class="hb-spec-section">'
            '<span class="hb-spec-bullet" aria-hidden="true">&#9679;</span>'
            f'<span class="hb-spec-section-text">{title}</span>'
            "</h2>"
        )
        parts.append('<table class="manual-table manual-spec-table">')
        parts.append("<tbody>")
        for left, right in section["rows"]:
            right_lines = _split_spec_value_lines(str(right))
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
