#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import hashlib
import html
import re
import shutil
from pathlib import Path

from tools.gen_index_bundle import MaterializedBundle, materialize_bundle
from tools.word_bundle_common import paths
from tools.word_bundle_html_images import _IMG_SRC_RE, _inject_img_dimensions
from tools.word_bundle_html_models import WordBundlePageMeta
from tools.word_bundle_html_only import (
    _build_word_only_tags,
    _dedent_only_block_lines,
    _evaluate_only_expression,
)
from tools.word_bundle_html_render import (
    _extract_word_anchor_text,
    _render_page_break_html,
    render_safety_word_html,
    render_spec_word_html,
)
from tools.word_bundle_html_rewrite import (
    _extract_spec_word_data,
    _rewrite_word_friendly_fragment,
)

_RST_HEADING_CHARS = set("=-~^\"`:+*#")


def _normalize_sphinx_only_blocks_for_docutils(rst_text: str, *, active_tags: set[str] | None = None) -> str:
    """
    Convert Sphinx-only blocks for docutils parsing:
    - keep `.. only:: ...` content whose expression matches the active tags
    - drop non-matching `.. only:: ...` content
    """
    tags = {"html"}
    if active_tags:
        tags.update(tag.strip().lower() for tag in active_tags if tag.strip())

    lines = rst_text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if stripped.startswith(".. only::"):
            expr = stripped.split("::", 1)[1].strip()
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

            if _evaluate_only_expression(expr, tags):
                dedented = _dedent_only_block_lines(block, indent)
                normalized = _normalize_sphinx_only_blocks_for_docutils(
                    "\n".join(dedented),
                    active_tags=tags,
                )
                if normalized:
                    out.extend(normalized.split("\n"))
                else:
                    out.append("")
            continue

        out.append(line)
        i += 1

    return "\n".join(out)


def _extract_raw_html_blocks(rst_text: str, *, active_tags: set[str] | None = None) -> str | None:
    normalized_rst = _normalize_sphinx_only_blocks_for_docutils(rst_text, active_tags=active_tags)
    lines = normalized_rst.splitlines()
    fragments: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if stripped != ".. raw:: html":
            i += 1
            continue

        i += 1
        if i < len(lines) and not lines[i].strip():
            i += 1

        block: list[str] = []
        while i < len(lines):
            cur = lines[i]
            cur_stripped = cur.lstrip()
            cur_indent = len(cur) - len(cur_stripped)
            if cur_stripped and cur_indent <= indent:
                break
            if not cur_stripped:
                block.append("")
            else:
                block.append(cur[indent + 3 :] if len(cur) > indent + 3 else cur_stripped)
            i += 1
        fragment = "\n".join(block).strip()
        if fragment:
            fragments.append(fragment)

    joined = "\n".join(fragments).strip()
    return joined or None


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


def _resolve_fragment_asset_path(src: str, source_path: Path) -> Path | None:
    candidate = src.strip()
    if not candidate or candidate.startswith(("http://", "https://", "data:", "file:", "#")):
        return None

    raw_path = Path(candidate)
    probe_paths: list[Path] = []
    if raw_path.is_absolute():
        probe_paths.append(raw_path)
    else:
        probe_paths.extend(
            [
                source_path.parent / raw_path,
                source_path.parent.parent / raw_path,
                paths.docs_dir / raw_path,
                paths.root / raw_path,
            ]
        )

    for probe in probe_paths:
        if probe.exists() and probe.is_file():
            return probe.resolve()
    return None


def _stage_fragment_assets(fragment: str, source_path: Path, bundle_dir: Path) -> str:
    assets_dir = bundle_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    staged: dict[str, str] = {}

    def replace_src(match: re.Match[str]) -> str:
        prefix, src, suffix = match.groups()
        resolved = _resolve_fragment_asset_path(src, source_path)
        if resolved is None:
            return match.group(0)

        key = str(resolved)
        staged_name = staged.get(key)
        if staged_name is None:
            digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:10]
            staged_name = f"{resolved.stem}_{digest}{resolved.suffix}"
            shutil.copy2(resolved, assets_dir / staged_name)
            staged[key] = staged_name

        return f"{prefix}{(assets_dir / staged_name).resolve().as_uri()}{suffix}"

    return _IMG_SRC_RE.sub(replace_src, fragment)


def _publish_rst_fragment_to_html(
    rst_text: str,
    source_path: Path,
    *,
    active_tags: set[str] | None = None,
) -> str:
    from docutils.core import publish_parts

    normalized_rst = _normalize_sphinx_only_blocks_for_docutils(rst_text, active_tags=active_tags)
    parts = publish_parts(
        source=normalized_rst,
        source_path=str(source_path),
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

    title, adorn = _extract_rst_first_heading(normalized_rst)
    if title and adorn == "=":
        html_fragment = f"<h1>{html.escape(title)}</h1>{html_fragment}"

    return html_fragment


def _convert_rst_fragment_to_html(
    rst_text: str,
    source_path: Path,
    bundle_dir: Path,
    *,
    active_tags: set[str] | None = None,
) -> str:
    source_name = source_path.name.lower()
    if source_name.startswith("safety_"):
        raw_html = _extract_raw_html_blocks(rst_text, active_tags=active_tags)
        if raw_html:
            rewritten_fragment = _rewrite_word_friendly_fragment(raw_html)
            return _stage_fragment_assets(rewritten_fragment, source_path, bundle_dir)

    published_fragment = _publish_rst_fragment_to_html(rst_text, source_path, active_tags=active_tags)

    if source_name.startswith("spec_"):
        spec_data = _extract_spec_word_data(published_fragment)
        if spec_data is not None:
            published_fragment = render_spec_word_html(spec_data)

    rewritten_fragment = _rewrite_word_friendly_fragment(published_fragment)
    return _stage_fragment_assets(rewritten_fragment, source_path, bundle_dir)


def build_word_bundle_html(
    cfg: dict,
    model: str | None,
    region: str | None,
    *,
    materialized_bundle: MaterializedBundle | None = None,
    output_dir: Path | None = None,
) -> tuple[Path, Path | None, tuple[WordBundlePageMeta, ...]]:
    materialized = materialized_bundle or materialize_bundle(cfg, model, region)
    title = materialized.title
    reference_doc = materialized.reference_doc
    active_tags = _build_word_only_tags(model=materialized.model, region=materialized.region, lang=materialized.lang)

    bundle_output_dir = output_dir or (paths.docs_build_dir / "word")
    bundle_output_dir.mkdir(parents=True, exist_ok=True)
    bundle_html = bundle_output_dir / "manual_bundle.html"

    body_parts: list[str] = []
    page_metas: list[WordBundlePageMeta] = []
    previous_was_cover = False
    for idx, rst_path in enumerate(materialized.page_paths):
        if idx > 0 and not previous_was_cover:
            body_parts.append(_render_page_break_html())
        rst_text = rst_path.read_text(encoding="utf-8")
        html_fragment = _convert_rst_fragment_to_html(
            rst_text,
            rst_path,
            bundle_output_dir,
            active_tags=active_tags,
        )
        body_parts.append(html_fragment or "<div></div>")
        page_metas.append(
            WordBundlePageMeta(
                source_path=rst_path,
                anchor_text=_extract_word_anchor_text(html_fragment),
            )
        )
        previous_was_cover = rst_path.name.startswith("cover")

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
            ".manual-two-col-table { width: 100%; border-collapse: separate; border-spacing: 12px 0; margin: 0 0 16px 0; }",
            ".manual-two-col-table td { width: 50%; border: none; padding: 0; vertical-align: top; }",
            ".manual-callout-table { width: 100%; border-collapse: collapse; margin: 0 0 16px 0; }",
            ".manual-callout-table td { border: 1px solid #888; padding: 6px 8px; vertical-align: top; }",
            ".manual-callout-table td:first-child { width: 16%; }",
            ".manual-spec-note, .manual-spec-footnote { margin: 8px 0 0 0; }",
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
    return bundle_html, reference_doc, tuple(page_metas)


__all__ = [
    "WordBundlePageMeta",
    "_build_word_only_tags",
    "_convert_rst_fragment_to_html",
    "_inject_img_dimensions",
    "_rewrite_word_friendly_fragment",
    "build_word_bundle_html",
    "render_safety_word_html",
    "render_spec_word_html",
]
