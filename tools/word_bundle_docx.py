#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote
from xml.etree import ElementTree as ET

from tools.gen_index_bundle import MaterializedBundle
from tools.word_bundle_common import paths
from tools.word_bundle_html import WordBundlePageMeta, build_word_bundle_html

_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_W_VAL = f"{{{_W_NS}}}val"
_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
_CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
_IMAGE_CONTENT_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".svg": "image/svg+xml",
}
_REFERENCE_H1_STYLE_ID = "dingding-heading1"
_REFERENCE_H2_STYLE_ID = "dingding-heading2"
_REFERENCE_TABLE_STYLE_ID = "tableHeader"
_REFERENCE_GRID_TABLE_STYLE_ID = "TableGrid"
_PANDOC_MAJOR_HEADING_STYLE_IDS = {"Title", "Heading1"}
_PANDOC_SUBHEADING_STYLE_IDS = {"Heading2"}
_PANDOC_BODY_STYLE_IDS = {"BodyText", "FirstParagraph", "Compact"}
_PRESERVED_SOURCE_PREFIXES = ("safety_", "spec_")


@dataclass(frozen=True)
class _DocBlock:
    index: int
    kind: str
    text: str
    element: ET.Element


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


def _set_paragraph_style_and_outline(
    para: ET.Element,
    ns: dict[str, str],
    *,
    style_id: str,
    outline_level: str,
) -> bool:
    changed = False
    ppr = para.find("w:pPr", ns)
    if ppr is None:
        ppr = ET.SubElement(para, f"{{{_W_NS}}}pPr")
        changed = True

    pstyle = ppr.find("w:pStyle", ns)
    if pstyle is None:
        pstyle = ET.SubElement(ppr, f"{{{_W_NS}}}pStyle")
        changed = True
    prev_style = pstyle.attrib.get(_W_VAL)
    if prev_style != style_id:
        pstyle.attrib[_W_VAL] = style_id
        changed = True

    outline = ppr.find("w:outlineLvl", ns)
    if outline is None:
        outline = ET.SubElement(ppr, f"{{{_W_NS}}}outlineLvl")
        changed = True
    prev_outline = outline.attrib.get(_W_VAL)
    if prev_outline != outline_level:
        outline.attrib[_W_VAL] = outline_level
        changed = True

    return changed


def _clear_paragraph_style_and_outline(para: ET.Element, ns: dict[str, str]) -> bool:
    ppr = para.find("w:pPr", ns)
    if ppr is None:
        return False

    changed = False
    pstyle = ppr.find("w:pStyle", ns)
    if pstyle is not None:
        ppr.remove(pstyle)
        changed = True

    outline = ppr.find("w:outlineLvl", ns)
    if outline is not None:
        ppr.remove(outline)
        changed = True

    if changed and len(ppr) == 0 and not ppr.attrib:
        para.remove(ppr)
    return changed


def _normalize_docx_text(text: str) -> str:
    return " ".join((text or "").split()).strip()


def _paragraph_style_id(para: ET.Element, ns: dict[str, str]) -> str:
    pstyle = para.find("w:pPr/w:pStyle", ns)
    return pstyle.attrib.get(_W_VAL, "").strip() if pstyle is not None else ""


def _table_style_id(tbl: ET.Element, ns: dict[str, str]) -> str:
    tbl_style = tbl.find("w:tblPr/w:tblStyle", ns)
    return tbl_style.attrib.get(_W_VAL, "").strip() if tbl_style is not None else ""


def _set_table_style(tbl: ET.Element, ns: dict[str, str], style_id: str) -> bool:
    changed = False
    tbl_pr = tbl.find("w:tblPr", ns)
    if tbl_pr is None:
        tbl_pr = ET.SubElement(tbl, f"{{{_W_NS}}}tblPr")
        changed = True

    tbl_style = tbl_pr.find("w:tblStyle", ns)
    if tbl_style is None:
        tbl_style = ET.SubElement(tbl_pr, f"{{{_W_NS}}}tblStyle")
        changed = True

    if tbl_style.attrib.get(_W_VAL) != style_id:
        tbl_style.attrib[_W_VAL] = style_id
        changed = True
    return changed


def _collect_available_style_ids(styles_xml: bytes, *, style_type: str) -> set[str]:
    ns = {"w": _W_NS}
    root = ET.fromstring(styles_xml)
    return {
        style.attrib.get(f"{{{_W_NS}}}styleId", "").strip()
        for style in root.findall(".//w:style", ns)
        if style.attrib.get(f"{{{_W_NS}}}type") == style_type
    }


def _iter_doc_blocks(body: ET.Element, ns: dict[str, str]) -> list[_DocBlock]:
    blocks: list[_DocBlock] = []
    for index, child in enumerate(list(body)):
        kind = child.tag.rsplit("}", 1)[-1]
        if kind not in {"p", "tbl"}:
            continue
        blocks.append(
            _DocBlock(
                index=index,
                kind=kind,
                text=_normalize_docx_text("".join(child.itertext())),
                element=child,
            )
        )
    return blocks


def _find_anchor_block_index(blocks: list[_DocBlock], anchor_text: str, start_index: int) -> int | None:
    anchor = _normalize_docx_text(anchor_text)
    if not anchor:
        return None
    for idx in range(start_index, len(blocks)):
        if blocks[idx].text.startswith(anchor):
            return idx
    return None


def _resolve_page_start_indexes(blocks: list[_DocBlock], page_metas: tuple[WordBundlePageMeta, ...]) -> list[int | None]:
    starts: list[int | None] = []
    search_from = 0
    for idx, meta in enumerate(page_metas):
        if idx == 0:
            starts.append(0)
            found = _find_anchor_block_index(blocks, meta.anchor_text, 0)
            if found is not None:
                search_from = found + 1
            continue
        found = _find_anchor_block_index(blocks, meta.anchor_text, search_from)
        starts.append(found)
        if found is not None:
            search_from = found + 1
    return starts


def _preserved_page_block_indexes(blocks: list[_DocBlock], page_metas: tuple[WordBundlePageMeta, ...]) -> set[int]:
    starts = _resolve_page_start_indexes(blocks, page_metas)
    preserved: set[int] = set()
    for page_idx, meta in enumerate(page_metas):
        if not meta.source_path.name.lower().startswith(_PRESERVED_SOURCE_PREFIXES):
            continue
        start = starts[page_idx]
        if start is None:
            continue
        end = len(blocks)
        for next_start in starts[page_idx + 1 :]:
            if next_start is not None:
                end = next_start
                break
        preserved.update(range(start, end))
    return preserved


def _table_dimensions(tbl: ET.Element, ns: dict[str, str]) -> tuple[int, int]:
    rows = tbl.findall("w:tr", ns)
    if not rows:
        rows = tbl.findall(".//w:tr", ns)
    row_count = len(rows)
    max_cols = 0
    for row in rows:
        col_count = len(row.findall("w:tc", ns))
        if col_count > max_cols:
            max_cols = col_count
    return row_count, max_cols


def _choose_reference_table_style(tbl: ET.Element, ns: dict[str, str], available_table_styles: set[str]) -> str | None:
    rows, max_cols = _table_dimensions(tbl, ns)
    if rows == 1 and max_cols >= 3 and _REFERENCE_GRID_TABLE_STYLE_ID in available_table_styles:
        return _REFERENCE_GRID_TABLE_STYLE_ID
    if _REFERENCE_TABLE_STYLE_ID in available_table_styles:
        return _REFERENCE_TABLE_STYLE_ID
    if _REFERENCE_GRID_TABLE_STYLE_ID in available_table_styles:
        return _REFERENCE_GRID_TABLE_STYLE_ID
    return None


def _remap_reference_doc_styles(docx_path: Path, page_metas: tuple[WordBundlePageMeta, ...]) -> None:
    with zipfile.ZipFile(docx_path, "r") as zin:
        infos = zin.infolist()
        blobs = {info.filename: zin.read(info.filename) for info in infos}

    styles_xml = blobs.get("word/styles.xml")
    doc_xml = blobs.get("word/document.xml")
    if not styles_xml or not doc_xml or not page_metas:
        return

    available_paragraph_styles = _collect_available_style_ids(styles_xml, style_type="paragraph")
    available_table_styles = _collect_available_style_ids(styles_xml, style_type="table")
    if not {_REFERENCE_H1_STYLE_ID, _REFERENCE_H2_STYLE_ID}.issubset(available_paragraph_styles):
        return
    if not ({_REFERENCE_TABLE_STYLE_ID, _REFERENCE_GRID_TABLE_STYLE_ID} & available_table_styles):
        return

    ns = {"w": _W_NS}
    root = ET.fromstring(doc_xml)
    body = root.find("w:body", ns)
    if body is None:
        return

    blocks = _iter_doc_blocks(body, ns)
    preserved_blocks = _preserved_page_block_indexes(blocks, page_metas)
    changed = False

    for block_idx, block in enumerate(blocks):
        if block_idx in preserved_blocks:
            continue

        if block.kind == "p":
            style_id = _paragraph_style_id(block.element, ns)
            if style_id in _PANDOC_MAJOR_HEADING_STYLE_IDS | {_REFERENCE_H1_STYLE_ID}:
                if _set_paragraph_style_and_outline(
                    block.element,
                    ns,
                    style_id=_REFERENCE_H1_STYLE_ID,
                    outline_level="0",
                ):
                    changed = True
            elif style_id in _PANDOC_SUBHEADING_STYLE_IDS | {_REFERENCE_H2_STYLE_ID}:
                if _set_paragraph_style_and_outline(
                    block.element,
                    ns,
                    style_id=_REFERENCE_H2_STYLE_ID,
                    outline_level="1",
                ):
                    changed = True
            elif style_id in _PANDOC_BODY_STYLE_IDS:
                if _clear_paragraph_style_and_outline(block.element, ns):
                    changed = True
        elif block.kind == "tbl":
            target_style = _choose_reference_table_style(block.element, ns, available_table_styles)
            if target_style and _table_style_id(block.element, ns) != target_style:
                if _set_table_style(block.element, ns, target_style):
                    changed = True
            for para in block.element.findall(".//w:p", ns):
                if _paragraph_style_id(para, ns) in _PANDOC_BODY_STYLE_IDS:
                    if _clear_paragraph_style_and_outline(para, ns):
                        changed = True

    if not changed:
        return

    ET.register_namespace("w", _W_NS)
    blobs["word/document.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    tmp_path = docx_path.with_suffix(".styles.tmp.docx")
    with zipfile.ZipFile(tmp_path, "w") as zout:
        for info in infos:
            zout.writestr(info, blobs[info.filename])
    tmp_path.replace(docx_path)


def _resolve_external_image_target(target: str) -> Path | None:
    candidate = target.strip()
    if not candidate.lower().startswith("file://"):
        return None

    raw = unquote(candidate[7:])
    if raw.startswith("/") and len(raw) > 2 and raw[2] == ":":
        raw = raw[1:]
    return Path(raw)


def _embed_external_docx_images(docx_path: Path) -> None:
    with zipfile.ZipFile(docx_path, "r") as zin:
        infos = zin.infolist()
        blobs = {info.filename: zin.read(info.filename) for info in infos}

    rels_xml = blobs.get("word/_rels/document.xml.rels")
    if not rels_xml:
        return

    rel_root = ET.fromstring(rels_xml)
    existing_members = set(blobs)
    existing_media_names = {Path(name).name for name in existing_members if name.startswith("word/media/")}
    added_members: dict[str, bytes] = {}
    needed_extensions: set[str] = set()
    changed = False
    seq = 1

    for rel in rel_root.findall(f"{{{_REL_NS}}}Relationship"):
        rel_type = rel.attrib.get("Type", "")
        if not rel_type.endswith("/image"):
            continue
        if rel.attrib.get("TargetMode") != "External":
            continue

        source_path = _resolve_external_image_target(rel.attrib.get("Target", ""))
        if source_path is None or not source_path.exists() or not source_path.is_file():
            continue

        suffix = source_path.suffix.lower()
        if suffix not in _IMAGE_CONTENT_TYPES:
            continue

        while True:
            candidate_name = f"image{seq}{suffix}"
            seq += 1
            if candidate_name not in existing_media_names:
                break

        member_name = f"word/media/{candidate_name}"
        added_members[member_name] = source_path.read_bytes()
        existing_media_names.add(candidate_name)
        needed_extensions.add(suffix)

        rel.attrib["Target"] = f"media/{candidate_name}"
        rel.attrib.pop("TargetMode", None)
        changed = True

    if not changed:
        return

    ET.register_namespace("", _REL_NS)
    blobs["word/_rels/document.xml.rels"] = ET.tostring(rel_root, encoding="utf-8", xml_declaration=True)

    content_types_xml = blobs.get("[Content_Types].xml")
    if content_types_xml:
        ct_root = ET.fromstring(content_types_xml)
        existing_defaults = {
            item.attrib.get("Extension", "").lower()
            for item in ct_root.findall(f"{{{_CT_NS}}}Default")
        }
        for suffix in sorted(needed_extensions):
            ext = suffix.lstrip(".")
            if ext in existing_defaults:
                continue
            ET.SubElement(
                ct_root,
                f"{{{_CT_NS}}}Default",
                Extension=ext,
                ContentType=_IMAGE_CONTENT_TYPES[suffix],
            )
        ET.register_namespace("", _CT_NS)
        blobs["[Content_Types].xml"] = ET.tostring(ct_root, encoding="utf-8", xml_declaration=True)

    tmp_path = docx_path.with_suffix(".embed.tmp.docx")
    with zipfile.ZipFile(tmp_path, "w") as zout:
        for info in infos:
            zout.writestr(info, blobs[info.filename])
        for member_name, payload in added_members.items():
            zout.writestr(member_name, payload)
    tmp_path.replace(docx_path)


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
            if _set_paragraph_style_and_outline(
                para,
                ns,
                style_id=style_id,
                outline_level="0",
            ):
                changed = True
            continue
        if style_id in h2_ids:
            if _set_paragraph_style_and_outline(
                para,
                ns,
                style_id=style_id,
                outline_level="1",
            ):
                changed = True
            continue

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
$htmlDoc = $null
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

    $htmlDoc = $word.Documents.Open($htmlPath, $false, $true)
    $doc.Range(0, 0).FormattedText = $htmlDoc.Range().FormattedText

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
    if ($htmlDoc) {{
        $htmlDoc.Close([ref]$false)
    }}
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


def _docx_is_valid(docx_path: Path) -> bool:
    return docx_path.exists() and zipfile.is_zipfile(docx_path)


def export_word_from_bundle(
    cfg: dict,
    model: str | None,
    region: str | None,
    word_output: str,
    *,
    materialized_bundle: MaterializedBundle | None = None,
    output_dir: Path | None = None,
) -> Path:
    bundle_output_dir = output_dir
    bundle_html, reference_doc, page_metas = build_word_bundle_html(
        cfg,
        model,
        region,
        materialized_bundle=materialized_bundle,
        output_dir=bundle_output_dir,
    )

    out_path = Path(word_output)
    if not out_path.is_absolute():
        out_root = bundle_output_dir or (paths.docs_build_dir / "word")
        out_path = out_root / out_path

    _export_docx_via_word(bundle_html, out_path, reference_doc)
    if not _docx_is_valid(out_path):
        print(f"[word_bundle_docx] Word COM produced an invalid DOCX, retrying with pandoc: {out_path}")
        _export_docx_via_pandoc(bundle_html, out_path, reference_doc)
    _embed_external_docx_images(out_path)
    _remap_reference_doc_styles(out_path, page_metas)
    _enforce_docx_outline_levels(out_path)
    return out_path
