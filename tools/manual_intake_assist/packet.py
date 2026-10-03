"""Generate explicit source-copy work items, without changing an IR or approving it."""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import re

from bs4 import BeautifulSoup, Comment
import fitz

from tools.manual_ir.hashing import file_sha256

COPY_KEYS = {"text", "alt", "html", "content", "label", "title", "body", "unit", "icon_alt", "accessibility_label"}
SKIP_KEYS = {"metadata", "presentation", "provenance"}
STRUCTURAL_ROLES = {"operation_id", "reference_id", "caption_mode", "caption_layout", "section_index"}


def _copy_key(parent: dict, key: str) -> str:
    """FCC ordered lists need not have a duplicate HTML carrier."""
    return "text" if key == "items" and parent.get("kind") == "list" else key


def copy_items(raw: dict) -> list[dict]:
    """Enumerate visible copy and its occurrences; IDs do not depend on translation."""
    result = []
    ids = [p["page_id"] for p in raw["pages"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate reference page identities")
    for page in raw["pages"]:
        grouped = defaultdict(list)

        def walk(value, path=(), component=None, key="", grouped=grouped):
            if isinstance(value, dict):
                component = value.get("component_id", component)
                for k, child in value.items():
                    if k == "content" and value.get("role") in STRUCTURAL_ROLES:
                        continue
                    if k not in SKIP_KEYS:
                        walk(child, (*path, k), component, _copy_key(value, k))
            elif isinstance(value, list):
                for i, child in enumerate(value):
                    walk(child, (*path, str(i)), component, key)
            elif isinstance(value, str) and (key in COPY_KEYS or key.endswith(("_text", "_html"))):
                texts = [value]
                if key == "html" or key.endswith("_html") or re.search(r"</?[a-zA-Z][^>]*>", value):
                    soup = BeautifulSoup(value, "html.parser")
                    texts = [str(n) for n in soup.find_all(string=True)
                             if not isinstance(n, Comment) and n.parent.name not in {"script", "style"}]
                for index, text in enumerate(texts):
                    if text.strip():
                        grouped[text].append({"path": "/" + "/".join(p.replace("~", "~0").replace("/", "~1") for p in path),
                                              "text_index": index, "component": component})

        walk(page)
        for text, occurrences in grouped.items():
            identity = sha256(json.dumps([page["page_id"], text], ensure_ascii=False).encode()).hexdigest()[:20]
            result.append({"id": identity, "page_id": page["page_id"], "reference": text,
                           "occurrences": occurrences, "native": "", "physical_page": None,
                           "evidence": "", "decision": "pending"})
    return result


def make_packet(reference: Path, source: Path, *, model: str, region: str,
                language: str, pages: list[int]) -> dict:
    if not all(v.strip() for v in (model, region, language)) or not pages or len(set(pages)) != len(pages):
        raise ValueError("explicit target and unique physical source pages required")
    raw = json.loads(reference.read_text(encoding="utf-8"))
    if raw.get("language") != "en":
        raise ValueError("reference must be an English IR (candidate is not approval)")
    source_pages = []
    with fitz.open(source) as doc:
        for number in pages:
            if type(number) is not int or not 1 <= number <= len(doc):
                raise ValueError(f"invalid physical page: {number}")
            page = doc[number - 1]
            blocks = [{"block": i, "bbox": list(b[:4]), "text": b[4]}
                      for i, b in enumerate(page.get_text("blocks", sort=True)) if b[6] == 0]
            source_pages.append({"physical_page": number, "blocks": blocks,
                                 "requires_visual_read": not any(b["text"].strip() for b in blocks)})
    return {"schema_version": "manual-intake-work-packet/v1", "status": "candidate",
            "publication_eligible": False,
            "target": {"model": model, "region": region, "language": language},
            "reference": {"model": raw["model"], "region": raw["region"], "language": "en",
                          "ir_sha256": file_sha256(reference), "approval": "not-asserted"},
            "source_sha256": file_sha256(source), "physical_pages": pages,
            "source_pages": source_pages, "items": copy_items(raw),
            "asset_refs": raw.get("metadata", {}).get("asset_sha256", {}),
            "limitations": ["Source page coverage and semantics require visual review; text extraction can omit outlined text.",
                            "Structural or artwork differences use existing family/diff and baseline exception records.",
                            "This packet cannot approve a baseline or authorize publication."]}


def _item_errors(item: dict, original: dict, pages: list[int]) -> list:
    errors = []
    key = original["id"]
    for field in ("id", "page_id", "reference", "occurrences"):
        if item.get(field) != original[field]:
            errors.append({"id": key, "field": field, "code": "changed_slot"})
    if item.get("decision") not in {"native-copy", "source-identical"}:
        errors.append({"id": key, "code": "unresolved_copy", "fix": "map original native copy, or retain identical source with evidence; structural differences need the existing review path"})
    if not isinstance(item.get("native"), str) or not item["native"].strip():
        errors.append({"id": key, "code": "empty_native"})
    if type(item.get("physical_page")) is not int or item["physical_page"] not in pages:
        errors.append({"id": key, "code": "outside_source_pages"})
    if not isinstance(item.get("evidence"), str) or not item["evidence"].strip():
        errors.append({"id": key, "code": "missing_evidence"})
    if item.get("decision") == "source-identical" and item.get("native") != original["reference"]:
        errors.append({"id": key, "code": "false_identical_copy"})
    if item.get("native") == original["reference"] and item.get("decision") != "source-identical":
        errors.append({"id": key, "code": "unexplained_unchanged_copy"})
    return errors


def check_packet(packet: dict, expected: dict) -> dict:
    """Compare against a freshly rebuilt packet, not the candidate's own counts."""
    errors = []
    for field in set(expected) - {"items"}:
        if packet.get(field) != expected[field]:
            errors.append({"field": field, "code": "changed_binding", "fix": "regenerate against the explicit source/reference; do not edit locked fields"})
    supplied = packet.get("items", [])
    if not isinstance(supplied, list) or any(not isinstance(v, dict) for v in supplied):
        return {"status": "incomplete", "errors": [{"code": "invalid_items"}], "publication_eligible": False}
    by_id = {v.get("id"): v for v in supplied}
    if len(by_id) != len(supplied):
        errors.append({"code": "duplicate_item"})
    wanted = {v["id"] for v in expected["items"]}
    for key in set(by_id) - wanted:
        errors.append({"id": key, "code": "unknown_item"})
    for original in expected["items"]:
        key = original["id"]
        item = by_id.get(key)
        if item is None:
            errors.append({"id": key, "page_id": original["page_id"], "code": "missing_item"})
            continue
        errors.extend(_item_errors(item, original, expected["physical_pages"]))
    return {"status": "copy-mapping-complete" if not errors else "incomplete",
            "expected_items": len(wanted), "errors": errors, "publication_eligible": False,
            "next": "independent source/visual review and existing baseline admission; mapping completeness is not acceptance"}


def native_copy_map(packet: dict, expected: dict) -> dict:
    report = check_packet(packet, expected)
    if report["errors"]:
        raise ValueError("copy mapping incomplete; inspect check report")
    maps = defaultdict(dict)
    evidence = []
    for item in packet["items"]:
        maps[item["page_id"]][item["reference"]] = item["native"]
        evidence.append({"page_id": item["page_id"], "english": item["reference"], "native": item["native"],
                         "physical_page": item["physical_page"], "selection": item["evidence"]})
    return {"language": packet["target"]["language"], "source_sha256": packet["source_sha256"],
            "reference_ir_sha256": packet["reference"]["ir_sha256"],
            "status": "candidate-native-copy-not-approved", "copy_by_page": dict(maps), "evidence": evidence}
