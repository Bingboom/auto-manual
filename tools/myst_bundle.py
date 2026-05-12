#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import html
import os
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

from tools.gen_index_bundle import MaterializedBundle, materialize_bundle
from tools.word_bundle_common import paths
from tools.word_bundle_docx_pandoc import resolve_pandoc_binary
from tools.word_bundle_html import _build_word_only_tags, _convert_rst_fragment_to_html

_FILE_URI_ATTR_RE = re.compile(r"""(\b(?:src|href)=)(["'])(file:[^"']+)(\2)""", re.IGNORECASE)
_LINE_DIV_RE = re.compile(r"""<div\s+class=(["'])line\1>\s*(.*?)\s*</div>""", re.IGNORECASE | re.DOTALL)


def _file_uri_to_relative(uri: str, *, output_dir: Path) -> str | None:
    parsed = urlparse(uri)
    if parsed.scheme.lower() != "file":
        return None
    raw_path = unquote(parsed.path or "")
    if os.name == "nt" and re.match(r"^/[A-Za-z]:", raw_path):
        raw_path = raw_path[1:]
    file_path = Path(raw_path)
    try:
        relative = file_path.resolve(strict=False).relative_to(output_dir.resolve(strict=False))
    except ValueError:
        return None
    return relative.as_posix()


def _rewrite_local_file_uri_attrs(html_text: str, *, output_dir: Path) -> str:
    def replace(match: re.Match[str]) -> str:
        prefix, quote, uri, closing_quote = match.groups()
        relative = _file_uri_to_relative(uri, output_dir=output_dir)
        if relative is None:
            return match.group(0)
        return f"{prefix}{quote}{relative}{closing_quote}"

    return _FILE_URI_ATTR_RE.sub(replace, html_text)


def _normalize_fragment_html_for_myst(html_text: str) -> str:
    return _LINE_DIV_RE.sub(r"<p>\2</p>", html_text)


def _run_pandoc_html_to_markdown(html_text: str, *, output_dir: Path) -> str:
    pandoc = resolve_pandoc_binary(None)
    resource_path = os.pathsep.join(
        [
            str(output_dir),
            str(paths.docs_dir),
            str(paths.root),
        ]
    )
    proc = subprocess.run(
        [
            pandoc,
            "--from=html",
            "--to=gfm",
            "--wrap=none",
            "--markdown-headings=atx",
            "--resource-path",
            resource_path,
        ],
        cwd=str(paths.root),
        input=html_text,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return proc.stdout


class _BasicHtmlToMarkdown(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[str] = []
        self.current: list[str] = []
        self.heading_level: int | None = None
        self.list_stack: list[str] = []
        self.link_stack: list[str] = []
        self.in_pre = False
        self.in_code = False
        self.table_rows: list[list[str]] | None = None
        self.table_row: list[str] | None = None
        self.table_cell: list[str] | None = None

    def _append(self, text: str) -> None:
        if self.table_cell is not None:
            self.table_cell.append(text)
            return
        self.current.append(text)

    def _rstrip_current(self) -> None:
        target = self.table_cell if self.table_cell is not None else self.current
        if target:
            target[-1] = target[-1].rstrip()

    def _flush_current(self) -> None:
        text = "".join(self.current).strip()
        self.current = []
        if text:
            self.blocks.append(re.sub(r"[ \t]+\n", "\n", text))

    def _start_block(self) -> None:
        if self.current:
            self._flush_current()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {name.lower(): value or "" for name, value in attrs}
        lower = tag.lower()
        if lower in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._start_block()
            self.heading_level = int(lower[1])
            self.current.append("#" * self.heading_level + " ")
        elif lower in {"p", "div", "section", "article"}:
            self._start_block()
        elif lower == "br":
            self._append("\n")
        elif lower in {"ul", "ol"}:
            self._start_block()
            self.list_stack.append(lower)
        elif lower == "li":
            self._start_block()
            indent = "  " * max(0, len(self.list_stack) - 1)
            bullet = "1. " if (self.list_stack[-1:] == ["ol"]) else "- "
            self.current.append(indent + bullet)
        elif lower in {"strong", "b"}:
            self._append("**")
        elif lower in {"em", "i"}:
            self._append("*")
        elif lower == "pre":
            self._start_block()
            self.in_pre = True
            self.current.append("```\n")
        elif lower == "code" and not self.in_pre:
            self.in_code = True
            self._append("`")
        elif lower == "a":
            href = attr_map.get("href", "")
            self.link_stack.append(href)
            self._append("[")
        elif lower == "img":
            alt = attr_map.get("alt", "")
            src = attr_map.get("src", "")
            if src:
                self._append(f"![{alt}]({src})")
        elif lower == "table":
            self._start_block()
            self.table_rows = []
        elif lower == "tr" and self.table_rows is not None:
            self.table_row = []
        elif lower in {"td", "th"} and self.table_row is not None:
            self.table_cell = []

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if lower in {"h1", "h2", "h3", "h4", "h5", "h6", "p", "div", "section", "article", "li"}:
            self.heading_level = None
            self._flush_current()
        elif lower in {"ul", "ol"}:
            self._flush_current()
            if self.list_stack:
                self.list_stack.pop()
        elif lower in {"strong", "b"}:
            self._rstrip_current()
            self._append("**")
        elif lower in {"em", "i"}:
            self._rstrip_current()
            self._append("*")
        elif lower == "code" and self.in_code and not self.in_pre:
            self._rstrip_current()
            self._append("`")
            self.in_code = False
        elif lower == "pre":
            self.current.append("\n```")
            self.in_pre = False
            self._flush_current()
        elif lower == "a":
            href = self.link_stack.pop() if self.link_stack else ""
            self._append(f"]({href})" if href else "]")
        elif lower in {"td", "th"} and self.table_row is not None and self.table_cell is not None:
            cell = " ".join("".join(self.table_cell).split())
            self.table_row.append(cell)
            self.table_cell = None
        elif lower == "tr" and self.table_rows is not None and self.table_row is not None:
            self.table_rows.append(self.table_row)
            self.table_row = None
        elif lower == "table":
            self._flush_table()

    def handle_data(self, data: str) -> None:
        if self.in_pre:
            self._append(data)
            return
        text = " ".join(data.split())
        if text:
            self._append(html.unescape(text) + " ")

    def _flush_table(self) -> None:
        rows = self.table_rows or []
        self.table_rows = None
        self.table_row = None
        self.table_cell = None
        if not rows:
            return
        max_cols = max(len(row) for row in rows)
        normalized = [row + [""] * (max_cols - len(row)) for row in rows]
        header = normalized[0]
        table_lines = [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join("---" for _ in header) + " |",
        ]
        for row in normalized[1:]:
            table_lines.append("| " + " | ".join(row) + " |")
        self.blocks.append("\n".join(table_lines))

    def markdown(self) -> str:
        self._flush_current()
        return "\n\n".join(block.strip() for block in self.blocks if block.strip())


def _fallback_html_to_markdown(html_text: str) -> str:
    parser = _BasicHtmlToMarkdown()
    parser.feed(html_text)
    parser.close()
    return parser.markdown()


def _normalize_markdown(markdown_text: str) -> str:
    text = markdown_text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _dedupe_leading_title(markdown_text: str, title: str) -> str:
    clean_title = title.strip()
    if not clean_title:
        return markdown_text
    duplicate_prefix = f"# {clean_title}\n\n# {clean_title}\n"
    if markdown_text.startswith(duplicate_prefix):
        return f"# {clean_title}\n" + markdown_text[len(duplicate_prefix) :]
    return markdown_text


def html_fragment_to_markdown(
    html_fragment: str,
    *,
    output_dir: Path,
    prefer_pandoc: bool = True,
) -> str:
    normalized_html = _normalize_fragment_html_for_myst(
        _rewrite_local_file_uri_attrs(html_fragment, output_dir=output_dir)
    )
    if prefer_pandoc:
        try:
            markdown_text = _run_pandoc_html_to_markdown(normalized_html, output_dir=output_dir)
        except (OSError, RuntimeError, subprocess.SubprocessError):
            markdown_text = _fallback_html_to_markdown(normalized_html)
    else:
        markdown_text = _fallback_html_to_markdown(normalized_html)
    return _normalize_markdown(markdown_text)


def export_myst_from_bundle(
    cfg: dict,
    model: str | None,
    region: str | None,
    myst_output: str,
    *,
    materialized_bundle: MaterializedBundle | None = None,
    output_dir: Path | None = None,
) -> Path:
    materialized = materialized_bundle or materialize_bundle(cfg, model, region)
    bundle_output_dir = output_dir or (paths.docs_build_dir / "myst")
    bundle_output_dir.mkdir(parents=True, exist_ok=True)

    out_path = Path(myst_output)
    if not out_path.is_absolute():
        out_path = bundle_output_dir / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    active_tags = _build_word_only_tags(model=materialized.model, region=materialized.region, lang=materialized.lang)
    markdown_parts: list[str] = []
    title = (materialized.title or "").strip()
    if title:
        markdown_parts.append(f"# {title}")

    for rst_path in materialized.page_paths:
        rst_text = rst_path.read_text(encoding="utf-8")
        html_fragment = _convert_rst_fragment_to_html(
            rst_text,
            rst_path,
            bundle_output_dir,
            active_tags=active_tags,
        )
        markdown_fragment = html_fragment_to_markdown(html_fragment or "<div></div>", output_dir=bundle_output_dir)
        if markdown_fragment:
            markdown_parts.append(markdown_fragment)

    markdown_text = _dedupe_leading_title(_normalize_markdown("\n\n".join(markdown_parts)), title)
    out_path.write_text(markdown_text + "\n", encoding="utf-8")
    return out_path


__all__ = [
    "export_myst_from_bundle",
    "html_fragment_to_markdown",
]
