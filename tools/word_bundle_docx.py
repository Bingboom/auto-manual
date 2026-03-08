#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from tools.word_bundle_common import paths
from tools.word_bundle_html import build_word_bundle_html

_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_W_VAL = f"{{{_W_NS}}}val"


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

