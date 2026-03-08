#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import glob
import html
import os
import re
import shutil
import subprocess
import sys
import zipfile
from xml.etree import ElementTree as ET
from pathlib import Path

# Ensure repo root is importable when running "python tools/xxx.py"
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.phase1.builder import BuildPaths, BuildSelector, Phase1Builder
from tools.phase1.renderers import (
    apply_vars,
    rst_escape,
)
from tools.utils.path_utils import get_paths
from tools.utils.targets import (
    config_uses_token,
    format_tokenized,
    resolve_build_model,
    resolve_sku_from_inputs,
)

paths = get_paths()


def _format_tokenized(text: str, sku: str | None, model: str | None) -> str:
    return format_tokenized(text, sku, model)


def _resolve_config_path(base_dir: Path, value: str, sku: str | None, model: str | None) -> Path:
    rendered = _format_tokenized(value, sku, model)
    path = Path(rendered)
    if path.is_absolute():
        return path
    return base_dir / path


def _resolve_optional_config_path(
    base_dir: Path,
    value: str | None,
    sku: str | None,
    model: str | None,
) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return _resolve_config_path(base_dir, value.strip(), sku, model)


def _resolve_csv_include_rst_path(page: dict, lang: str, sku: str | None, model: str | None) -> Path:
    page_name = (page.get("page") or "").strip()
    if not page_name:
        raise RuntimeError("csv_page requires non-empty 'page'")
    include_dir = page.get("include_dir")
    if include_dir is None:
        rel = f"{page_name}_{lang}.rst"
    else:
        if not isinstance(include_dir, str) or not include_dir.strip():
            raise RuntimeError("csv_page.include_dir must be a non-empty string")
        rel = str(Path(_format_tokenized(include_dir.strip(), sku, model)) / f"{page_name}_{lang}.rst")
    return paths.docs_dir / rel


def _load_rst_substitutions(conf_base_path: Path) -> dict[str, str]:
    substitutions: dict[str, str] = {}
    if not conf_base_path.exists():
        return substitutions

    for line in conf_base_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith(".. |") or "| replace::" not in line:
            continue
        head, value = line.split("| replace::", 1)
        key = head.removeprefix(".. |").strip()
        substitutions[key] = value.strip()
    return substitutions


def _apply_rst_substitutions(
    text: str,
    substitutions: dict[str, str],
    vars_map: dict[str, str],
) -> str:
    out = apply_vars(text, vars_map)
    for key, value in substitutions.items():
        out = out.replace(f"|{key}|", value)
    return out


def resolve_reference_doc(reference_value: str | None, *, root: Path | None = None) -> Path | None:
    if not reference_value:
        return None

    candidate = reference_value.strip()
    if not candidate:
        return None

    root_dir = root or paths.root
    has_glob = any(ch in candidate for ch in "*?[")
    if has_glob:
        pattern = candidate
        if not Path(pattern).is_absolute():
            pattern = str(root_dir / pattern)
        matches = sorted(glob.glob(pattern))
        if not matches:
            raise RuntimeError(f"Word reference doc did not match any files: {candidate}")
        return Path(matches[0])

    path = Path(candidate)
    if not path.is_absolute():
        path = root_dir / path
    if not path.exists():
        raise RuntimeError(f"Word reference doc not found: {path}")
    return path


def derive_word_title(
    build_cfg: dict,
    reference_doc: Path | None,
    substitutions: dict[str, str],
    vars_map: dict[str, str],
) -> str:
    configured = (build_cfg.get("word_title") or "").strip()
    if configured:
        return _apply_rst_substitutions(configured, substitutions, vars_map).replace("\xa0", " ")

    if reference_doc is not None:
        return reference_doc.stem.replace("\xa0", " ")

    product_name = substitutions.get("PRODUCT_NAME") or vars_map.get("product_name")
    if product_name:
        return f"{product_name} User Manual"
    return "User Manual"


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


_IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_STYLE_ATTR_RE = re.compile(r'style="([^"]*)"', re.IGNORECASE)
_WIDTH_ATTR_RE = re.compile(r"\bwidth\s*=", re.IGNORECASE)
_HEIGHT_ATTR_RE = re.compile(r"\bheight\s*=", re.IGNORECASE)
_STYLE_WIDTH_RE = re.compile(r"\bwidth\s*:\s*([^;]+)", re.IGNORECASE)
_STYLE_HEIGHT_RE = re.compile(r"\bheight\s*:\s*([^;]+)", re.IGNORECASE)
_RST_HEADING_CHARS = set("=-~^\"`:+*#")
_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_W_VAL = f"{{{_W_NS}}}val"


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


def _load_word_context(
    cfg: dict,
    sku: str | None,
    model: str | None,
) -> tuple[Phase1Builder, dict[str, dict[str, str]]]:
    base_paths = BuildPaths.from_root(paths.root)
    cfg_paths_raw = cfg.get("paths", {})
    cfg_paths = cfg_paths_raw if isinstance(cfg_paths_raw, dict) else {}
    spec_master_cfg = cfg_paths.get("spec_master_csv")
    spec_footnotes_cfg = cfg_paths.get("spec_footnotes_csv")
    spec_master_csv = (
        _resolve_config_path(paths.root, spec_master_cfg.strip(), sku, model)
        if isinstance(spec_master_cfg, str) and spec_master_cfg.strip()
        else base_paths.spec_master_csv
    )
    spec_footnotes_csv = (
        _resolve_optional_config_path(paths.root, spec_footnotes_cfg, sku, model)
        if isinstance(spec_footnotes_cfg, str)
        else base_paths.spec_footnotes_csv
    )

    build_paths = BuildPaths(
        root=base_paths.root,
        page_registry=base_paths.page_registry,
        content_blocks=base_paths.content_blocks,
        product_variables=base_paths.product_variables,
        template_dir=base_paths.template_dir,
        output_dir=base_paths.output_dir,
        spec_master_csv=spec_master_csv,
        spec_footnotes_csv=spec_footnotes_csv,
    )
    builder = Phase1Builder(build_paths)
    vars_by_sku = builder._load_vars_by_sku()
    return builder, vars_by_sku


def _ensure_csv_page_rsts(cfg: dict, builder: Phase1Builder, sku: str | None, model: str | None) -> None:
    pages_cfg = cfg.get("pages", [])
    build_cfg = cfg.get("build", {})
    build_langs = list(build_cfg.get("languages", ["en"]))

    page_ids: set[str] = set()
    langs: set[str] = set()
    for page in pages_cfg:
        if not isinstance(page, dict):
            continue
        if (page.get("type") or "").strip() != "csv_page":
            continue
        page_name = (page.get("page") or "").strip()
        if not page_name:
            raise RuntimeError("csv_page requires non-empty 'page'")
        page_ids.add(page_name)
        for lang in page.get("langs", build_langs):
            langs.add(str(lang))

    if not page_ids:
        return

    selector = BuildSelector(
        skus={sku} if sku else None,
        models={model} if model else None,
        pages=page_ids,
        langs=langs or None,
    )
    builder.build(selector, strict_renderer=True)


def _pick_model_from_vars(vars_map: dict[str, str]) -> str:
    for key in ("model", "product_model", "model_no", "model_number", "Model"):
        value = (vars_map.get(key) or "").strip()
        if value:
            return value
    return ""


def _pick_vars_map(
    vars_by_sku: dict[str, dict[str, str]],
    sku: str | None,
    model: str | None,
) -> dict[str, str]:
    if sku:
        return vars_by_sku.get(sku, {})
    if model:
        matched = [
            vars_map
            for vars_map in vars_by_sku.values()
            if _pick_model_from_vars(vars_map) == model
        ]
        if len(matched) == 1:
            return matched[0]
    return {}


def _config_uses_sku_token(cfg: dict) -> bool:
    return config_uses_token(
        cfg,
        "sku",
        include_rst_include=True,
        paths_keys=("spec_master_csv", "spec_footnotes_csv"),
        build_keys=("word_reference_doc",),
    )


def resolve_bundle_targets(cfg: dict, sku: str | None, model: str | None) -> tuple[str | None, str | None]:
    picked_model = resolve_build_model(cfg, model)
    if sku and sku.strip():
        return sku.strip(), picked_model

    if not _config_uses_sku_token(cfg):
        return None, picked_model

    picked_sku = resolve_sku_from_inputs(
        cfg,
        arg_sku=None,
        arg_model=picked_model,
        root=paths.root,
        requires_sku_token=True,
        log_prefix=None,
    )
    return picked_sku, picked_model


def build_word_bundle_html(cfg: dict, sku: str | None, model: str | None) -> tuple[Path, Path | None]:
    build_cfg = cfg.get("build", {})
    pages_cfg = cfg.get("pages", [])
    build_langs = list(build_cfg.get("languages", ["en"]))

    builder, vars_by_sku = _load_word_context(cfg, sku, model)
    _ensure_csv_page_rsts(cfg, builder, sku, model)
    vars_map = _pick_vars_map(vars_by_sku, sku, model)
    substitutions = _load_rst_substitutions(paths.docs_dir / "conf_base.py")
    reference_doc = resolve_reference_doc(build_cfg.get("word_reference_doc"), root=paths.root)
    title = derive_word_title(build_cfg, reference_doc, substitutions, vars_map)

    bundle_dir = paths.docs_build_dir / "word"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    bundle_html = bundle_dir / "manual_bundle.html"

    body_parts: list[str] = []
    started = False
    cover_added = False

    for page in pages_cfg:
        ptype = (page.get("type") or "").strip()
        if ptype == "cover_pdf":
            if cover_added:
                continue
            body_parts.append(_render_cover_html(title))
            cover_added = True
            started = True
            continue

        if started:
            body_parts.append(_render_page_break_html())
        started = True

        if ptype == "csv_page":
            langs = list(page.get("langs", build_langs))
            for idx, lang in enumerate(langs):
                if idx > 0:
                    body_parts.append(_render_page_break_html())
                rst_path = _resolve_csv_include_rst_path(page, str(lang), sku, model)
                if not rst_path.exists():
                    raise RuntimeError(
                        f"Missing generated RST for csv_page: {rst_path}. "
                        "Run tools/phase1_build.py (or tools/build_docs.py) first."
                    )
                rst_text = rst_path.read_text(encoding="utf-8")
                rst_text = _apply_rst_substitutions(rst_text, substitutions, vars_map)
                body_parts.append(_convert_rst_fragment_to_html(rst_text))
            continue

        if ptype == "rst_include":
            file_name = page.get("file")
            if not isinstance(file_name, str) or not file_name.strip():
                raise RuntimeError("rst_include requires non-empty 'file'")
            rst_path = _resolve_config_path(paths.docs_dir, file_name.strip(), sku, model)
            rst_text = rst_path.read_text(encoding="utf-8")
            rst_text = _apply_rst_substitutions(rst_text, substitutions, vars_map)
            body_parts.append(_convert_rst_fragment_to_html(rst_text))
            continue

        if ptype == "pdf_insert":
            raise RuntimeError("word bundle does not support pdf_insert pages")

        raise RuntimeError(f"Unsupported page type for word bundle: {ptype}")

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


def _ps_quote(value: str) -> str:
    return value.replace("'", "''")


def _collect_word_heading_style_ids(styles_xml: bytes) -> tuple[set[str], set[str]]:
    ns = {"w": _W_NS}
    root = ET.fromstring(styles_xml)
    h1_ids: set[str] = set()
    h2_ids: set[str] = set()

    for style in root.findall(".//w:style", ns):
        if style.attrib.get(f"{{{_W_NS}}}type") != "paragraph":
            continue
        style_id = style.attrib.get(f"{{{_W_NS}}}styleId", "").strip()
        if not style_id:
            continue
        name_el = style.find("w:name", ns)
        name = (name_el.attrib.get(_W_VAL, "") if name_el is not None else "").strip().lower()

        if name in {"heading 1", "heading1", "标题 1", "标题1"}:
            h1_ids.add(style_id)
        elif name in {"heading 2", "heading2", "标题 2", "标题2"}:
            h2_ids.add(style_id)

    # Fallback for common built-in IDs when the style name lookup is unavailable.
    if not h1_ids:
        h1_ids.update({"Heading1", "1"})
    if not h2_ids:
        h2_ids.update({"Heading2", "2"})
    return h1_ids, h2_ids


def _enforce_docx_outline_levels(docx_path: Path) -> None:
    with zipfile.ZipFile(docx_path, "r") as zin:
        infos = zin.infolist()
        blobs = {info.filename: zin.read(info.filename) for info in infos}

    styles_xml = blobs.get("word/styles.xml")
    doc_xml = blobs.get("word/document.xml")
    if not styles_xml or not doc_xml:
        return

    h1_ids, h2_ids = _collect_word_heading_style_ids(styles_xml)
    ns = {"w": _W_NS}
    root = ET.fromstring(doc_xml)
    changed = False

    for para in root.findall(".//w:body//w:p", ns):
        ppr = para.find("w:pPr", ns)
        if ppr is None:
            continue
        pstyle = ppr.find("w:pStyle", ns)
        if pstyle is None:
            continue
        style_id = pstyle.attrib.get(_W_VAL, "").strip()
        if style_id in h1_ids:
            target_lvl = "0"
        elif style_id in h2_ids:
            target_lvl = "1"
        else:
            continue

        outline = ppr.find("w:outlineLvl", ns)
        if outline is None:
            outline = ET.SubElement(ppr, f"{{{_W_NS}}}outlineLvl")
        prev = outline.attrib.get(_W_VAL)
        if prev != target_lvl:
            outline.attrib[_W_VAL] = target_lvl
            changed = True

    if not changed:
        return

    ET.register_namespace("w", _W_NS)
    blobs["word/document.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    tmp_path = docx_path.with_suffix(".tmp.docx")
    with zipfile.ZipFile(tmp_path, "w") as zout:
        for info in infos:
            zout.writestr(info, blobs[info.filename])
    tmp_path.replace(docx_path)


def _export_docx_via_pandoc(bundle_html: Path, out_path: Path, reference_doc: Path | None) -> None:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise RuntimeError("pandoc is required for non-Windows word bundle export")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    resource_path = os.pathsep.join(
        [
            str(bundle_html.parent),
            str(paths.docs_dir),
            str(paths.root),
        ]
    )

    cmd = [
        pandoc,
        str(bundle_html),
        "--from=html",
        "--to=docx",
        "--resource-path",
        resource_path,
        "-o",
        str(out_path),
    ]
    if reference_doc is not None:
        cmd += ["--reference-doc", str(reference_doc)]

    subprocess.run(cmd, check=True, cwd=str(paths.root))


def _export_docx_via_word(bundle_html: Path, out_path: Path, reference_doc: Path | None) -> None:
    if not sys.platform.startswith("win"):
        _export_docx_via_pandoc(bundle_html, out_path, reference_doc)
        return

    out_path.parent.mkdir(parents=True, exist_ok=True)
    ref_literal = _ps_quote(str(reference_doc)) if reference_doc else ""
    html_literal = _ps_quote(str(bundle_html))
    out_literal = _ps_quote(str(out_path))

    script = f"""
$ErrorActionPreference = 'Stop'
$referencePath = '{ref_literal}'
$htmlPath = '{html_literal}'
$outPath = '{out_literal}'
$word = $null
$doc = $null
$wdAlertsNone = 0
$wdFormatXMLDocument = 12
try {{
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = $wdAlertsNone

    if ($referencePath) {{
        Copy-Item -LiteralPath $referencePath -Destination $outPath -Force
        $doc = $word.Documents.Open($outPath)
        $deleteEnd = [Math]::Max(0, $doc.Content.End - 1)
        if ($deleteEnd -gt 0) {{
            $doc.Range(0, $deleteEnd).Delete()
        }}
    }} else {{
        $doc = $word.Documents.Add()
    }}

    $range = $doc.Range(0, 0)
    $range.InsertFile($htmlPath)

    foreach ($table in @($doc.Tables)) {{
        try {{
            $table.Style = 'Table Grid'
        }} catch {{
        }}
    }}

    if ($referencePath) {{
        $doc.Save()
    }} else {{
        $doc.SaveAs([ref]$outPath, [ref]$wdFormatXMLDocument)
    }}
}} finally {{
    if ($doc) {{
        $doc.Close([ref]$false)
    }}
    if ($word) {{
        $word.Quit()
    }}
}}
"""
    subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        check=True,
        cwd=str(paths.root),
    )


def export_word_from_bundle(cfg: dict, sku: str | None, model: str | None, word_output: str) -> Path:
    bundle_html, reference_doc = build_word_bundle_html(cfg, sku, model)

    out_path = Path(word_output)
    if not out_path.is_absolute():
        out_path = paths.docs_build_dir / "word" / out_path

    _export_docx_via_word(bundle_html, out_path, reference_doc)
    _enforce_docx_outline_levels(out_path)
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml", help="Path to config yaml")
    ap.add_argument("--sku", default=None, help="Optional SKU for word bundle")
    ap.add_argument("--model", default=None, help="Optional model for spec filtering / SKU resolving")
    ap.add_argument("--output", default="manual_bundle.docx", help="Output docx path")
    args = ap.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = paths.root / cfg_path

    import yaml  # type: ignore

    with cfg_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    target_sku, target_model = resolve_bundle_targets(cfg, args.sku, args.model)
    docx_path = export_word_from_bundle(cfg, target_sku, target_model, args.output)
    print(f"[word_bundle] Done. DOCX: {docx_path}")


if __name__ == "__main__":
    main()
