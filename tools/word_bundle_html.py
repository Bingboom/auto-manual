#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import html
import re
from pathlib import Path

from tools.config_pages import CoverPdfPage, CsvPage, PdfInsertPage, RstIncludePage, parse_config_pages_or_raise
from tools.phase1.renderers import rst_escape
from tools.word_bundle_common import (
    apply_rst_substitutions,
    derive_word_title,
    ensure_csv_page_rsts,
    fill_product_name_from_spec_master,
    load_rst_substitutions,
    load_word_context,
    paths,
    pick_vars_map,
    resolve_config_path,
    resolve_csv_include_rst_path,
    resolve_reference_doc,
)


def _render_cover_html(title: str) -> str:
    title_html = html.escape(rst_escape(title))
    return "".join(
        [
            '<section class="manual-cover">',
            f'<div class="cover-title">{title_html}</div>',
            "</section>",
        ]
    )


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


def render_spec_word_html(data: dict[str, object]) -> str:
    parts = [
        '<section class="manual-section spec-section">',
        f"<h1>{html.escape(rst_escape(str(data['title_main'])))}</h1>",
    ]

    for section in data["sections"]:
        title = html.escape(rst_escape(str(section["title"])))
        parts.append(f"<h2>{title}</h2>")
        parts.append('<table class="manual-table">')
        parts.append("<tbody>")
        for left, right in section["rows"]:
            parts.append("<tr>")
            parts.append(f"<td>{_render_table_cell_html(str(left))}</td>")
            parts.append(f"<td>{_render_table_cell_html(str(right))}</td>")
            parts.append("</tr>")
        parts.append("</tbody>")
        parts.append("</table>")

    for note in data["notes"]:
        parts.append(f"<p>{_render_table_cell_html(str(note))}</p>")
    for footnote in data["footnotes"]:
        parts.append(f"<p>{_render_table_cell_html(str(footnote))}</p>")

    parts.append("</section>")
    return "".join(parts)


_IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_STYLE_ATTR_RE = re.compile(r'style="([^"]*)"', re.IGNORECASE)
_WIDTH_ATTR_RE = re.compile(r"\bwidth\s*=", re.IGNORECASE)
_HEIGHT_ATTR_RE = re.compile(r"\bheight\s*=", re.IGNORECASE)
_STYLE_WIDTH_RE = re.compile(r"\bwidth\s*:\s*([^;]+)", re.IGNORECASE)
_STYLE_HEIGHT_RE = re.compile(r"\bheight\s*:\s*([^;]+)", re.IGNORECASE)
_RST_HEADING_CHARS = set("=-~^\"`:+*#")


def _normalize_css_size(value: str) -> str | None:
    token = value.strip()
    if not token:
        return None

    px_match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)px", token, re.IGNORECASE)
    if px_match:
        return str(int(round(float(px_match.group(1)))))

    pct_match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)%", token, re.IGNORECASE)
    if pct_match:
        number = float(pct_match.group(1))
        if number.is_integer():
            return f"{int(number)}%"
        return f"{number}%"

    return None


def _inject_img_dimensions(html_doc: str) -> str:
    def replace_tag(match: re.Match[str]) -> str:
        tag = match.group(0)
        style_match = _STYLE_ATTR_RE.search(tag)
        if not style_match:
            return tag

        style = style_match.group(1)
        additions: list[str] = []

        width_match = _STYLE_WIDTH_RE.search(style)
        if width_match and not _WIDTH_ATTR_RE.search(tag):
            width_value = _normalize_css_size(width_match.group(1))
            if width_value:
                additions.append(f'width="{width_value}"')

        height_match = _STYLE_HEIGHT_RE.search(style)
        if height_match and not _HEIGHT_ATTR_RE.search(tag):
            height_value = _normalize_css_size(height_match.group(1))
            if height_value:
                additions.append(f'height="{height_value}"')

        if not additions:
            return tag

        return tag[:-1] + " " + " ".join(additions) + ">"

    return _IMG_TAG_RE.sub(replace_tag, html_doc)


def _normalize_sphinx_only_blocks_for_docutils(rst_text: str) -> str:
    """
    Convert Sphinx-only blocks for docutils parsing:
    - keep `.. only:: html` content
    - drop non-html `.. only:: ...` content (e.g. latex)
    """
    lines = rst_text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if stripped.startswith(".. only::"):
            expr = stripped.split("::", 1)[1].strip().lower()
            i += 1
            block: list[str] = []
            while i < len(lines):
                cur = lines[i]
                cur_stripped = cur.lstrip()
                cur_indent = len(cur) - len(cur_stripped)
                if cur_stripped and cur_indent <= indent:
                    break
                block.append(cur)
                i += 1

            if expr == "html":
                base = indent + 3
                for b in block:
                    if not b.strip():
                        out.append("")
                    elif len(b) > base:
                        out.append(b[base:])
                    else:
                        out.append(b.lstrip())
            continue

        out.append(line)
        i += 1

    return "\n".join(out)


def _extract_rst_first_heading(text: str) -> tuple[str | None, str | None]:
    lines = text.splitlines()
    for idx in range(len(lines) - 1):
        title = lines[idx].strip()
        underline = lines[idx + 1].strip()
        if not title or title.startswith(".. "):
            continue
        if not underline:
            continue
        if len(set(underline)) != 1:
            continue
        ch = underline[0]
        if ch not in _RST_HEADING_CHARS:
            continue
        if len(underline) < len(title):
            continue
        return title, ch
    return None, None


def _convert_rst_fragment_to_html(rst_text: str) -> str:
    from docutils.core import publish_parts

    normalized_rst = _normalize_sphinx_only_blocks_for_docutils(rst_text)
    parts = publish_parts(
        source=normalized_rst,
        writer_name="html5",
        settings_overrides={
            "report_level": 5,
            "halt_level": 6,
            "file_insertion_enabled": False,
            "raw_enabled": True,
            "syntax_highlight": "none",
        },
    )
    fragment = parts.get("fragment") or parts.get("body") or parts.get("html_body")
    if not fragment:
        raise RuntimeError("docutils did not return an HTML fragment for the RST input")
    html_fragment = fragment.strip()

    # docutils treats top "=" headings as document titles and drops them from fragment output.
    # Restore them as h1 so Word navigation keeps chapter hierarchy aligned with the manual TOC.
    title, adorn = _extract_rst_first_heading(normalized_rst)
    if title and adorn == "=":
        title_html = html.escape(rst_escape(title))
        return f"<h1>{title_html}</h1>{html_fragment}"
    return html_fragment


def build_word_bundle_html(
    cfg: dict,
    model: str | None,
    region: str | None,
) -> tuple[Path, Path | None]:
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    build_langs = list(build_cfg.get("languages", ["en"]))
    pages_cfg = parse_config_pages_or_raise(
        cfg.get("pages"),
        default_languages=build_langs,
        error_prefix="config.pages",
    )

    builder = load_word_context(cfg, model, region)
    ensure_csv_page_rsts(cfg, builder, model, region)
    base_vars_map = pick_vars_map(model, region)
    primary_lang = str(build_langs[0]) if build_langs else "en"
    title_vars = fill_product_name_from_spec_master(
        base_vars_map,
        spec_master_csv=builder.paths.spec_master_csv,
        model=model,
        region=region,
        lang=primary_lang,
    )
    base_substitutions = load_rst_substitutions(paths.docs_dir / "conf_base.py")
    title_substitutions = dict(base_substitutions)
    if title_vars.get("product_name"):
        resolved_name = str(title_vars["product_name"])
        title_substitutions["PRODUCT_NAME"] = resolved_name
        title_substitutions["PRODUCT_NAME_BOLD"] = f"**{resolved_name}**"
    reference_doc = resolve_reference_doc(build_cfg.get("word_reference_doc"), root=paths.root)
    title = derive_word_title(build_cfg, reference_doc, title_substitutions, title_vars)

    bundle_dir = paths.docs_build_dir / "word"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    bundle_html = bundle_dir / "manual_bundle.html"

    body_parts: list[str] = []
    started = False
    cover_added = False

    for page in pages_cfg:
        if isinstance(page, CoverPdfPage):
            if cover_added:
                continue
            body_parts.append(_render_cover_html(title))
            cover_added = True
            started = True
            continue

        if started:
            body_parts.append(_render_page_break_html())
        started = True

        if isinstance(page, CsvPage):
            langs = list(page.langs) or build_langs
            for idx, lang in enumerate(langs):
                if idx > 0:
                    body_parts.append(_render_page_break_html())
                rst_path = resolve_csv_include_rst_path(page, str(lang), model, region)
                if not rst_path.exists():
                    raise RuntimeError(
                        f"Missing generated RST for csv_page: {rst_path}. "
                        "Run tools/phase1_build.py (or tools/build_docs.py) first."
                    )
                rst_text = rst_path.read_text(encoding="utf-8")
                page_vars = fill_product_name_from_spec_master(
                    base_vars_map,
                    spec_master_csv=builder.paths.spec_master_csv,
                    model=model,
                    region=region,
                    lang=str(lang),
                )
                page_substitutions = dict(base_substitutions)
                if page_vars.get("product_name"):
                    resolved_name = str(page_vars["product_name"])
                    page_substitutions["PRODUCT_NAME"] = resolved_name
                    page_substitutions["PRODUCT_NAME_BOLD"] = f"**{resolved_name}**"
                rst_text = apply_rst_substitutions(rst_text, page_substitutions, page_vars)
                body_parts.append(_convert_rst_fragment_to_html(rst_text))
            continue

        if isinstance(page, RstIncludePage):
            rst_path = resolve_config_path(paths.docs_dir, page.file, model, region)
            rst_text = rst_path.read_text(encoding="utf-8")
            page_lang = page.lang or primary_lang
            page_vars = fill_product_name_from_spec_master(
                base_vars_map,
                spec_master_csv=builder.paths.spec_master_csv,
                model=model,
                region=region,
                lang=page_lang,
            )
            page_substitutions = dict(base_substitutions)
            if page_vars.get("product_name"):
                resolved_name = str(page_vars["product_name"])
                page_substitutions["PRODUCT_NAME"] = resolved_name
                page_substitutions["PRODUCT_NAME_BOLD"] = f"**{resolved_name}**"
            rst_text = apply_rst_substitutions(rst_text, page_substitutions, page_vars)
            body_parts.append(_convert_rst_fragment_to_html(rst_text))
            continue

        if isinstance(page, PdfInsertPage):
            raise RuntimeError("word bundle does not support pdf_insert pages")

        raise RuntimeError(f"Unsupported page type for word bundle: {type(page).__name__}")

    html_doc = "".join(
        [
            "<!DOCTYPE html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8"/>',
            f"<title>{html.escape(title)}</title>",
            "<style>",
            "body { font-family: Calibri, Arial, sans-serif; line-height: 1.45; margin: 0; }",
            "h1, h2 { page-break-after: avoid; }",
            ".hb-h1-pill { margin: 10px 0 12px 0; font-size: 20pt; }",
            ".hb-subbar { margin: 10px 0 12px 0; font-size: 14pt; }",
            ".hb-spec-section { margin: 8px 0 6px 0; font-size: 12pt; }",
            ".manual-cover { min-height: 85vh; display: flex; align-items: center; justify-content: center; text-align: center; }",
            ".manual-cover .cover-title { font-size: 24pt; font-weight: 700; }",
            ".manual-page-break { page-break-after: always; }",
            ".manual-table { width: 100%; border-collapse: collapse; margin: 0 0 16px 0; }",
            ".manual-table td { border: 1px solid #888; padding: 6px 8px; vertical-align: top; }",
            ".manual-table td:first-child { width: 34%; }",
            "p, li { font-size: 10.5pt; }",
            "</style>",
            "</head>",
            "<body>",
            "".join(body_parts),
            "</body>",
            "</html>",
        ]
    )
    bundle_html.write_text(_inject_img_dimensions(html_doc), encoding="utf-8")
    return bundle_html, reference_doc
