#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import glob
import html
import subprocess
import sys
from pathlib import Path

from tools.phase1.builder import BuildPaths, Phase1Builder, _normalize_content_blocks, _read_csv
from tools.phase1.renderers import (
    apply_vars,
    collect_safety_content,
    collect_spec_content,
    rst_escape,
)
from tools.utils.path_utils import get_paths

paths = get_paths()


def _format_tokenized(text: str, sku: str | None) -> str:
    if "{sku}" in text and not sku:
        raise RuntimeError("config uses '{sku}' but no --sku was provided")
    return text.format(sku=sku or "")


def _resolve_config_path(base_dir: Path, value: str, sku: str | None) -> Path:
    rendered = _format_tokenized(value, sku)
    path = Path(rendered)
    if path.is_absolute():
        return path
    return base_dir / path


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
            f"<h1>{title_html}</h1>",
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


def _convert_rst_fragment_to_html(rst_text: str) -> str:
    from docutils.core import publish_parts

    parts = publish_parts(
        source=rst_text,
        writer_name="html5",
        settings_overrides={
            "report_level": 5,
            "halt_level": 6,
            "file_insertion_enabled": False,
            "raw_enabled": False,
            "syntax_highlight": "none",
        },
    )
    fragment = parts.get("fragment") or parts.get("body") or parts.get("html_body")
    if not fragment:
        raise RuntimeError("docutils did not return an HTML fragment for the RST input")
    return fragment.strip()


def _load_word_context() -> tuple[Phase1Builder, list[dict[str, str]], dict[str, dict[str, str]]]:
    build_paths = BuildPaths.from_root(paths.root)
    builder = Phase1Builder(build_paths)
    default_blocks = _normalize_content_blocks(_read_csv(build_paths.content_blocks))
    vars_by_sku = builder._load_vars_by_sku()
    return builder, default_blocks, vars_by_sku


def build_word_bundle_html(cfg: dict, sku: str | None) -> tuple[Path, Path | None]:
    build_cfg = cfg.get("build", {})
    pages_cfg = cfg.get("pages", [])
    build_langs = list(build_cfg.get("languages", ["en"]))

    builder, default_blocks, vars_by_sku = _load_word_context()
    vars_map = vars_by_sku.get(sku or "", {}) if sku else {}
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
            page_name = (page.get("page") or "").strip()
            page_blocks = builder._load_page_blocks(page_name, default_blocks)
            langs = list(page.get("langs", build_langs))
            for idx, lang in enumerate(langs):
                if idx > 0:
                    body_parts.append(_render_page_break_html())
                if page_name == "safety":
                    data = collect_safety_content(page_blocks, sku or "", str(lang), vars_map)
                    body_parts.append(render_safety_word_html(data))
                    continue
                if page_name == "spec":
                    data = collect_spec_content(page_blocks, sku or "", str(lang), vars_map)
                    body_parts.append(render_spec_word_html(data))
                    continue
                raise RuntimeError(f"word bundle does not support csv_page '{page_name}' yet")
            continue

        if ptype == "rst_include":
            file_name = page.get("file")
            if not isinstance(file_name, str) or not file_name.strip():
                raise RuntimeError("rst_include requires non-empty 'file'")
            rst_path = _resolve_config_path(paths.docs_dir, file_name.strip(), sku)
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
            ".manual-cover h1 { font-size: 24pt; }",
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
    bundle_html.write_text(html_doc, encoding="utf-8")
    return bundle_html, reference_doc


def _ps_quote(value: str) -> str:
    return value.replace("'", "''")


def _export_docx_via_word(bundle_html: Path, out_path: Path, reference_doc: Path | None) -> None:
    if not sys.platform.startswith("win"):
        raise RuntimeError("word bundle export currently requires Windows")

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


def export_word_from_bundle(cfg: dict, sku: str | None, word_output: str) -> Path:
    bundle_html, reference_doc = build_word_bundle_html(cfg, sku)

    out_path = Path(word_output)
    if not out_path.is_absolute():
        out_path = paths.docs_build_dir / "word" / out_path

    _export_docx_via_word(bundle_html, out_path, reference_doc)
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml", help="Path to config yaml")
    ap.add_argument("--sku", default=None, help="Optional SKU for word bundle")
    ap.add_argument("--output", default="manual_bundle.docx", help="Output docx path")
    args = ap.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = paths.root / cfg_path

    import yaml  # type: ignore

    with cfg_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    docx_path = export_word_from_bundle(cfg, args.sku, args.output)
    print(f"[word_bundle] Done. DOCX: {docx_path}")


if __name__ == "__main__":
    main()
