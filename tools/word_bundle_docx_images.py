#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import zipfile
from pathlib import Path
from urllib.parse import unquote
from xml.etree import ElementTree as ET

from tools.word_bundle_docx_xml import serialize_xml_preserving_namespaces

_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
_DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
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


def _resolve_external_image_target(target: str) -> Path | None:
    candidate = target.strip()
    if not candidate.lower().startswith("file://"):
        return None

    raw = unquote(candidate[7:])
    if raw.startswith("/") and len(raw) > 2 and raw[2] == ":":
        raw = raw[1:]
    return Path(raw)


def embed_external_docx_images(docx_path: Path) -> None:
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
    converted_rel_ids: set[str] = set()
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
        rel_id = rel.attrib.get("Id", "").strip()
        if rel_id:
            converted_rel_ids.add(rel_id)
        changed = True

    if not changed:
        return

    doc_rel_link = f"{{{_DOC_REL_NS}}}link"
    doc_rel_embed = f"{{{_DOC_REL_NS}}}embed"
    for member_name, payload in tuple(blobs.items()):
        if not member_name.startswith("word/") or not member_name.endswith(".xml"):
            continue
        try:
            xml_root = ET.fromstring(payload)
        except ET.ParseError:
            continue

        xml_changed = False
        for element in xml_root.iter():
            rel_id = element.attrib.get(doc_rel_link, "").strip()
            if not rel_id or rel_id not in converted_rel_ids:
                continue
            element.attrib[doc_rel_embed] = rel_id
            element.attrib.pop(doc_rel_link, None)
            xml_changed = True

        if xml_changed:
            blobs[member_name] = serialize_xml_preserving_namespaces(xml_root, original_xml=payload)

    blobs["word/_rels/document.xml.rels"] = serialize_xml_preserving_namespaces(rel_root, original_xml=rels_xml)

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
        blobs["[Content_Types].xml"] = serialize_xml_preserving_namespaces(ct_root, original_xml=content_types_xml)

    tmp_path = docx_path.with_suffix(".embed.tmp.docx")
    with zipfile.ZipFile(tmp_path, "w") as zout:
        for info in infos:
            zout.writestr(info, blobs[info.filename])
        for member_name, payload in added_members.items():
            zout.writestr(member_name, payload)
    tmp_path.replace(docx_path)
