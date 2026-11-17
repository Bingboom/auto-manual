"""Multilingual quality-control audit and asset/TM/component provenance for manual-ir/v2."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence

from tools import lang_registry
from tools.component_specs.callout import variant_for_label
from tools.corpus.align import (
    AlignedSegmentPair,
    align_ir_pair,
    extract_page_blocks,
    is_noise_segment,
    normalize_page_stem,
    normalize_space,
)
from tools.corpus.discover import (
    SUPPORTED_IR_SCHEMA_VERSION,
    DiscoveredIR,
    IRPair,
    default_anchor_lang,
    load_discovered_ir,
    normalize_lang_key,
)
from tools.manual_copy_source import TM_LANGUAGE_FIELDS
from tools.manual_knowledge.identity import callout_severity

AUDIT_SCHEMA_VERSION = "auto-manual-ir-qc/v1"
PROVENANCE_SCHEMA_VERSION = "auto-manual-ir-provenance/v1"
REPO_ROOT = Path(__file__).resolve().parents[2]

_TEMPLATE_MARKER_RE = re.compile(r"\{\{[^{}]+\}\}")
_TM_MARKER_RE = re.compile(r"(?<!=)==(?!=)([^=\n]+?)(?<!=)==(?!=)")
_TERM_VARIANT_SPLIT_RE = re.compile(r"[/;；,，|]+")
_HASH_ENTRY_SPLIT_RE = re.compile(r"[;,\|\s]+")
_NUMBER_WITH_UNIT_RE = re.compile(
    r"^\d+(?:\.\d+)?(?:mm|cm|m|in|ft|kg|g|lb|lbs|wh|kwh|ah|mah|w|kw|v|mv|a|ma|hz|khz|mhz|ghz|db|rh|s|ms|min|h|hr|hrs)$",
    re.IGNORECASE,
)
_SPEC_UNIT_TOKEN_RE = re.compile(
    r"^(?:mm|cm|m|in|ft|kg|g|lb|lbs|wh|kwh|ah|mah|w|kw|v|mv|a|ma|hz|khz|mhz|ghz|db|rh|s|ms|min|h|hr|hrs|max|ac|dc|c|f|k|ip\d+)$",
    re.IGNORECASE,
)
_MODEL_CODE_RE = re.compile(
    r"^(?:[A-Z]{1,5}-\d{2,5}[A-Z0-9-]*|(?:PTB|JSG)\d+[A-Z0-9-]*|[FE]\d+(?:-[FE]\d+)?|F0-FF)$"
)
_ADMONITION_CLASSES = frozenset(
    {"admonition", "callout", "note", "warning", "caution", "tip", "important"}
)
_SKIP_LEAF_KINDS = frozenset(
    {"comment", "image", "column", "line_break", "thematic_break"}
)

# Brand names and technical tokens that legitimately remain untranslated across locales.
_ALLOWLISTED_TECH_TOKENS = frozenset(
    {
        "jackery",
        "explorer",
        "solarsaga",
        "homepower",
        "usb-c",
        "usb-a",
        "usb",
        "type-c",
        "wi-fi",
        "wifi",
        "bluetooth",
        "mppt",
        "led",
        "lcd",
        "ac",
        "dc",
        "bms",
        "ups",
        "eps",
        "app",
        "fcc",
        "ce",
        "ukca",
        "weee",
        "rohs",
        "anderson",
        "xt60",
        "xt90",
        "mc4",
        "lifepo4",
        "ip65",
        "ip67",
        "can",
        "rs485",
        "rj45",
        "hdmi",
        "sos",
        "qr",
        "ota",
        "ios",
        "android",
        "ul",
        "pse",
        "telec",
        "kc",
        "rcm",
        "ic",
    }
)

_CJK_KR_CALLOUT_SEVERITY: dict[str, str] = {
    "警告": "warning",
    "경고": "warning",
    "danger": "danger",
    "peligro": "danger",
    "위험": "danger",
    "危険": "danger",
    "危险": "danger",
    "注意": "caution",
    "ご注意": "caution",
    "小心": "caution",
    "주의": "caution",
    "注記": "note",
    "注釈": "note",
    "補足": "note",
    "備考": "note",
    "説明": "note",
    "重要": "note",
    "提示": "note",
    "备注": "note",
    "说明": "note",
    "備註": "note",
    "說明": "note",
    "참고": "note",
    "중요": "note",
    "ヒント": "tip",
    "팁": "tip",
}


def resolve_tm_column(lang: str) -> str:
    """Map an IR language code to its TM-B column name without literal language tables."""

    raw = (lang or "").strip()
    normalized = raw.casefold().replace("_", "-")
    if normalized in TM_LANGUAGE_FIELDS:
        return TM_LANGUAGE_FIELDS[normalized]
    spec = lang_registry.language_spec(normalized)
    if spec is not None:
        return spec.tm_column
    return raw


def _cell_to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return normalize_space(value)
    if isinstance(value, dict):
        return normalize_space(str(value.get("name") or value.get("text") or ""))
    if isinstance(value, (list, tuple)):
        parts = [_cell_to_text(item) for item in value]
        return normalize_space(" ".join(part for part in parts if part))
    return normalize_space(str(value))


def _normalize_record_item(item: dict[str, Any]) -> tuple[str, dict[str, str]]:
    fields_raw = item.get("fields")
    if isinstance(fields_raw, dict):
        rid = str(item.get("record_id") or "")
        fields = {str(k): _cell_to_text(v) for k, v in fields_raw.items()}
        return rid, fields
    rid = str(item.get("record_id") or item.get("_record_id") or "")
    fields = {
        str(k): _cell_to_text(v)
        for k, v in item.items()
        if k not in ("record_id", "_record_id")
    }
    return rid, fields


def _load_json_records(path: Path) -> list[tuple[str, dict[str, str]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        raw_rows = payload
    elif isinstance(payload, dict) and isinstance(payload.get("records"), list):
        raw_rows = payload["records"]
    elif isinstance(payload, dict) and isinstance(payload.get("rows"), list):
        raw_rows = payload["rows"]
    else:
        raise ValueError(f"Unsupported Bitable JSON shape in {path}")

    return [_normalize_record_item(item) for item in raw_rows if isinstance(item, dict)]


def _filter_approved_rows(
    rows: Sequence[tuple[str, dict[str, str]]],
) -> list[tuple[str, dict[str, str]]]:
    approved: list[tuple[str, dict[str, str]]] = []
    for rid, fields in rows:
        has_status = "Status" in fields or "status" in fields
        if has_status:
            status_val = (fields.get("Status") or fields.get("status") or "").strip()
            if status_val.casefold() != "approved":
                continue
        approved.append((rid, fields))
    return approved


def _lookup_lang_field(
    fields: dict[str, str],
    col_name: str,
    lang_key: str,
) -> str:
    if col_name in fields:
        return fields[col_name]
    candidates = {col_name.casefold(), lang_key.casefold()}
    for alias, mapped in TM_LANGUAGE_FIELDS.items():
        if mapped.casefold() == col_name.casefold():
            candidates.add(alias.casefold())
    for key, val in fields.items():
        if key.casefold() in candidates:
            return val
    return ""


def _read_ir_json(ir_path: Path) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    resolved = ir_path.resolve()
    try:
        raw = resolved.read_text(encoding="utf-8")
        payload = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, [
            {
                "type": "invalid_ir_json",
                "severity": "error",
                "page_stem": "",
                "message": f"Failed to read or parse IR JSON: {exc}",
            }
        ]
    if not isinstance(payload, dict):
        return None, [
            {
                "type": "invalid_ir_schema",
                "severity": "error",
                "page_stem": "",
                "message": "IR root JSON value must be an object",
            }
        ]
    schema_version = str(payload.get("schema_version") or "").strip()
    if schema_version != SUPPORTED_IR_SCHEMA_VERSION:
        return None, [
            {
                "type": "invalid_schema_version",
                "severity": "error",
                "page_stem": "",
                "message": f"Expected schema_version {SUPPORTED_IR_SCHEMA_VERSION!r}, got {schema_version!r}",
            }
        ]
    pages_raw = payload.get("pages")
    if not isinstance(pages_raw, list) or not any(isinstance(p, dict) for p in pages_raw):
        return None, [
            {
                "type": "empty_pages",
                "severity": "error",
                "page_stem": "",
                "message": "IR must contain a non-empty pages list",
            }
        ]
    return payload, []


def _inline_text(node: dict[str, Any]) -> str:
    parts: list[str] = []

    def _walk(item: Any) -> None:
        if not isinstance(item, dict) or item.get("hidden") is True:
            return
        kind = item.get("kind")
        if kind == "text":
            parts.append(str(item.get("text") or ""))
            return
        if kind == "line_break":
            parts.append(" ")
            return
        if kind in _SKIP_LEAF_KINDS:
            return
        for child in item.get("children") or ():
            _walk(child)

    _walk(node)
    return normalize_space("".join(parts))


def _iter_flow_dicts(node: Any) -> Iterable[dict[str, Any]]:
    if isinstance(node, list):
        for item in node:
            yield from _iter_flow_dicts(item)
        return
    if not isinstance(node, dict) or node.get("hidden") is True:
        return
    yield node
    for child in node.get("children") or ():
        yield from _iter_flow_dicts(child)
    for child in node.get("carrier_flow") or ():
        yield from _iter_flow_dicts(child)


def _check_empty_headings(page: dict[str, Any], page_stem: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for block in page.get("blocks") or ():
        root = block.get("payload") if isinstance(block, dict) and "payload" in block else block
        for node in _iter_flow_dicts(root):
            if node.get("kind") == "heading" and not _inline_text(node):
                findings.append(
                    {
                        "type": "empty_heading",
                        "severity": "error",
                        "page_stem": page_stem,
                        "heading_level": node.get("level"),
                        "message": "Heading block contains no visible text",
                    }
                )
    return findings


def _collect_page_text_segments(page: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    seen: set[str] = set()
    for blk in extract_page_blocks(page):
        for seg in blk.segments:
            if seg.text and seg.text not in seen:
                seen.add(seg.text)
                texts.append(seg.text)
    for block in page.get("blocks") or ():
        root = block.get("payload") if isinstance(block, dict) and "payload" in block else block
        for node in _iter_flow_dicts(root):
            if node.get("kind") == "table_cell":
                cell_text = _inline_text(node)
                if cell_text and cell_text not in seen:
                    seen.add(cell_text)
                    texts.append(cell_text)
    return texts


def _check_unresolved_markers(page: dict[str, Any], page_stem: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for text in _collect_page_text_segments(page):
        for marker_type, pattern in (
            ("unresolved_template_marker", _TEMPLATE_MARKER_RE),
            ("unresolved_tm_marker", _TM_MARKER_RE),
        ):
            for match in pattern.finditer(text):
                marker = match.group(0)
                key = (marker_type, marker, text)
                if key not in seen:
                    seen.add(key)
                    findings.append(
                        {
                            "type": marker_type,
                            "severity": "error",
                            "page_stem": page_stem,
                            "marker": marker,
                            "text": text,
                        }
                    )
    return findings


def _verify_single_asset(
    rel_path: str,
    expected: str,
    root_resolved: Path,
) -> dict[str, Any] | None:
    candidate = (root_resolved / rel_path).resolve()
    if not candidate.is_relative_to(root_resolved):
        return {
            "type": "broken_asset",
            "severity": "error",
            "page_stem": "",
            "asset_path": rel_path,
            "reason": "outside_package_root",
            "expected_sha256": expected,
        }
    if not candidate.is_file():
        return {
            "type": "broken_asset",
            "severity": "error",
            "page_stem": "",
            "asset_path": rel_path,
            "reason": "missing_file",
            "expected_sha256": expected,
        }
    try:
        actual = hashlib.sha256(candidate.read_bytes()).hexdigest().casefold()
    except OSError as exc:
        return {
            "type": "broken_asset",
            "severity": "error",
            "page_stem": "",
            "asset_path": rel_path,
            "reason": f"read_error: {exc}",
            "expected_sha256": expected,
        }
    if actual != expected:
        return {
            "type": "broken_asset",
            "severity": "error",
            "page_stem": "",
            "asset_path": rel_path,
            "reason": "sha256_mismatch",
            "expected_sha256": expected,
            "actual_sha256": actual,
        }
    return None


def _verify_package_assets(
    metadata: dict[str, Any],
    package_root: Path,
) -> tuple[list[dict[str, Any]], int]:
    asset_map = metadata.get("asset_sha256")
    if not isinstance(asset_map, dict):
        return [], 0
    root_resolved = package_root.resolve()
    findings: list[dict[str, Any]] = []
    checked = 0
    for rel_raw, expected_raw in sorted(asset_map.items()):
        checked += 1
        err = _verify_single_asset(
            str(rel_raw),
            str(expected_raw or "").strip().casefold(),
            root_resolved,
        )
        if err is not None:
            findings.append(err)
    return findings, checked


def _is_allowlisted_token(token: str) -> bool:
    if not token or not any(ch.isalpha() for ch in token):
        return True
    if token.casefold() in _ALLOWLISTED_TECH_TOKENS:
        return True
    if _SPEC_UNIT_TOKEN_RE.match(token) or _NUMBER_WITH_UNIT_RE.match(token):
        return True
    if _MODEL_CODE_RE.match(token.upper()):
        return True
    return False


def _is_allowlisted_technical_text(text: str) -> bool:
    norm = normalize_space(text)
    if not norm:
        return True
    raw_parts = re.split(r"[\s,;/|()+:&·•\[\]{}\"']+", norm)
    tokens = [tok.strip(".-_") for tok in raw_parts if tok.strip(".-_")]
    if not tokens:
        return True
    for tok in tokens:
        if _is_allowlisted_token(tok):
            continue
        if "-" in tok:
            subparts = [sub for sub in tok.split("-") if sub]
            if subparts and all(_is_allowlisted_token(sub) for sub in subparts):
                continue
        return False
    return True


def _check_untranslated_residue(
    aligned_pairs: Sequence[AlignedSegmentPair],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for pair in aligned_pairs:
        if is_noise_segment(pair.en_text):
            continue
        en_norm = normalize_space(pair.en_text)
        target_norm = normalize_space(pair.target_text)
        if en_norm == target_norm and not _is_allowlisted_technical_text(en_norm):
            findings.append(
                {
                    "type": "untranslated_english_residue",
                    "severity": "warning",
                    "page_stem": pair.page_stem,
                    "content_attribute": pair.content_attribute,
                    "text": target_norm,
                }
            )
    return findings


def resolve_callout_severity(label: str) -> str:
    """Resolve localized callout label to severity using identity + CJK/KR + callout spec."""

    cleaned = (label or "").strip().lstrip("*").strip().rstrip(":：-").strip()
    if not cleaned:
        return "unknown"
    sev = callout_severity(cleaned)
    if sev != "unknown":
        return sev
    cjk_match = _CJK_KR_CALLOUT_SEVERITY.get(cleaned.casefold())
    if cjk_match:
        return cjk_match
    variant = variant_for_label(cleaned)
    if variant:
        return variant
    return "unknown"


def _html_classes(node: dict[str, Any]) -> set[str]:
    attrs = ((node.get("presentation") or {}).get("html") or {}).get("attributes") or {}
    raw = attrs.get("class")
    if isinstance(raw, str):
        return {tok.strip().casefold() for tok in raw.split() if tok.strip()}
    if isinstance(raw, list):
        return {
            tok.strip().casefold()
            for item in raw
            for tok in str(item).split()
            if tok.strip()
        }
    return set()


def _slot_label(node: dict[str, Any]) -> str:
    spec = node.get("component_spec") or {}
    for slot in spec.get("slots") or ():
        if isinstance(slot, dict) and slot.get("role") == "label":
            val = normalize_space(str(slot.get("content") or ""))
            if val:
                return val
    return ""


def _extract_strip_callout_label(node: dict[str, Any]) -> str:
    slot_val = _slot_label(node)
    if slot_val:
        return slot_val
    for child in _iter_flow_dicts(node.get("carrier_flow") or ()):
        if "manual-callout-label" in _html_classes(child):
            return _inline_text(child)
    return ""


def _extract_admonition_label(node: dict[str, Any]) -> str:
    for child in node.get("children") or ():
        if not isinstance(child, dict) or child.get("hidden") is True:
            continue
        classes = _html_classes(child)
        if "admonition-title" in classes or child.get("kind") == "heading":
            return _inline_text(child)
    return ""


def _callout_label_if_callout(node: dict[str, Any]) -> str | None:
    kind = node.get("kind")
    if kind == "component":
        cid = str((node.get("component_spec") or {}).get("component_id") or "")
        if cid == "HB-CALLOUT-STRIP":
            return _extract_strip_callout_label(node)
        return None
    if kind == "web_callout":
        return _slot_label(node)
    if kind == "group" and (_html_classes(node) & _ADMONITION_CLASSES):
        return _extract_admonition_label(node)
    return None


def _walk_callouts(node: Any, out: list[tuple[str, str]]) -> None:
    if isinstance(node, list):
        for item in node:
            _walk_callouts(item, out)
        return
    if not isinstance(node, dict) or node.get("hidden") is True:
        return
    label = _callout_label_if_callout(node)
    if label is not None:
        out.append((label, resolve_callout_severity(label)))
        return
    for child in node.get("children") or ():
        _walk_callouts(child, out)
    for child in node.get("carrier_flow") or ():
        _walk_callouts(child, out)


def _extract_page_callouts(page: dict[str, Any]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for block in page.get("blocks") or ():
        root = block.get("payload") if isinstance(block, dict) and "payload" in block else block
        _walk_callouts(root, out)
    return out


def _index_unique_pages(pages: Sequence[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_stem: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for page in pages:
        stem = normalize_page_stem(str(page.get("page_id") or ""))
        if stem:
            by_stem[stem].append(page)
    return {stem: group[0] for stem, group in by_stem.items() if len(group) == 1}


def _check_callouts(
    target_pages: Sequence[dict[str, Any]],
    anchor_pages: Sequence[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for page in target_pages:
        stem = normalize_page_stem(str(page.get("page_id") or ""))
        for label, severity in _extract_page_callouts(page):
            if severity == "unknown":
                findings.append(
                    {
                        "type": "unknown_callout_severity",
                        "severity": "warning",
                        "page_stem": stem,
                        "label": label,
                    }
                )

    if anchor_pages is None:
        return findings

    target_by_stem = _index_unique_pages(target_pages)
    anchor_by_stem = _index_unique_pages(anchor_pages)
    for stem in sorted(target_by_stem):
        anchor_page = anchor_by_stem.get(stem)
        if anchor_page is None:
            continue
        anchor_callouts = _extract_page_callouts(anchor_page)
        target_callouts = _extract_page_callouts(target_by_stem[stem])
        anchor_sevs = [sev for _, sev in anchor_callouts]
        target_sevs = [sev for _, sev in target_callouts]
        if anchor_sevs != target_sevs:
            findings.append(
                {
                    "type": "callout_severity_mismatch",
                    "severity": "warning",
                    "page_stem": stem,
                    "anchor_severities": anchor_sevs,
                    "target_severities": target_sevs,
                    "anchor_labels": [lbl for lbl, _ in anchor_callouts],
                    "target_labels": [lbl for lbl, _ in target_callouts],
                }
            )
    return findings


def _compile_term_pattern(en_term: str) -> re.Pattern[str]:
    prefix = r"(?<![A-Za-z0-9_])" if (en_term[0].isalnum() or en_term[0] == "_") else ""
    suffix = r"(?![A-Za-z0-9_])" if (en_term[-1].isalnum() or en_term[-1] == "_") else ""
    return re.compile(prefix + re.escape(en_term) + suffix, re.IGNORECASE)


def _split_target_variants(raw_target: str) -> tuple[str, ...]:
    variants: list[str] = []
    seen: set[str] = set()
    for part in _TERM_VARIANT_SPLIT_RE.split(raw_target or ""):
        norm = normalize_space(part)
        if norm and norm.casefold() not in seen:
            seen.add(norm.casefold())
            variants.append(norm)
    return tuple(variants)


def _load_approved_terms(
    terms_path: Path,
    *,
    en_col: str,
    target_col: str,
    target_lang_key: str,
) -> list[tuple[str, str, re.Pattern[str], tuple[str, ...]]]:
    rows = _filter_approved_rows(_load_json_records(terms_path))
    en_key = default_anchor_lang()
    entries: list[tuple[str, str, re.Pattern[str], tuple[str, ...]]] = []
    for rid, fields in rows:
        en_term = normalize_space(_lookup_lang_field(fields, en_col, en_key))
        raw_target = _lookup_lang_field(fields, target_col, target_lang_key)
        variants = _split_target_variants(raw_target)
        if not en_term or not variants:
            continue
        entries.append((rid, en_term, _compile_term_pattern(en_term), variants))
    return entries


def _check_terms_compliance(
    aligned_pairs: Sequence[AlignedSegmentPair],
    *,
    terms_path: Path,
    target_lang: str,
) -> list[dict[str, Any]]:
    en_col = resolve_tm_column(default_anchor_lang())
    target_lang_key = normalize_lang_key(target_lang)
    target_col = resolve_tm_column(target_lang)
    term_entries = _load_approved_terms(
        terms_path,
        en_col=en_col,
        target_col=target_col,
        target_lang_key=target_lang_key,
    )
    findings: list[dict[str, Any]] = []
    for pair in aligned_pairs:
        en_norm = normalize_space(pair.en_text)
        target_norm = normalize_space(pair.target_text)
        target_folded = target_norm.casefold()
        for rid, en_term, pattern, variants in term_entries:
            if not pattern.search(en_norm):
                continue
            if any(variant.casefold() in target_folded for variant in variants):
                continue
            findings.append(
                {
                    "type": "term_glossary_mismatch",
                    "severity": "warning",
                    "page_stem": pair.page_stem,
                    "term_record_id": rid,
                    "en_term": en_term,
                    "expected_target_terms": list(variants),
                    "en_text": en_norm,
                    "target_text": target_norm,
                }
            )
    return findings


def _align_target_with_anchor(
    target_path: Path,
    anchor_path: Path,
) -> tuple[DiscoveredIR | None, DiscoveredIR | None, list[AlignedSegmentPair], list[dict[str, Any]]]:
    target_ir, target_err = load_discovered_ir(target_path, repo_root=REPO_ROOT)
    anchor_ir, anchor_err = load_discovered_ir(anchor_path, repo_root=REPO_ROOT)
    if target_ir is None or anchor_ir is None:
        detail = target_err or anchor_err or {"reason": "load_error"}
        return (
            target_ir,
            anchor_ir,
            [],
            [
                {
                    "type": "anchor_alignment_unavailable",
                    "severity": "error",
                    "page_stem": "",
                    "message": f"Cannot load anchor/target IR pair: {detail.get('reason')}",
                }
            ],
        )
    pair = IRPair(
        model=target_ir.model,
        region=target_ir.region,
        anchor=anchor_ir,
        target=target_ir,
        pairing_mode="explicit_anchor_ir",
    )
    aligned, _abstained, _aligned_pages = align_ir_pair(pair)
    return target_ir, anchor_ir, aligned, []


def _run_anchor_checks(
    *,
    ir_path: Path,
    anchor_ir_path: Path | None,
    terms_path: Path | None,
    language: str,
) -> tuple[list[dict[str, Any]] | None, list[dict[str, Any]]]:
    if anchor_ir_path is None:
        return None, []
    _t_ir, anchor_ir, aligned_pairs, align_errs = _align_target_with_anchor(
        ir_path, anchor_ir_path
    )
    findings: list[dict[str, Any]] = list(align_errs)
    anchor_pages = list(anchor_ir.pages) if anchor_ir is not None else None
    is_target_lang = normalize_lang_key(language) != normalize_lang_key(default_anchor_lang())
    if is_target_lang and aligned_pairs:
        findings.extend(_check_untranslated_residue(aligned_pairs))
        if terms_path is not None:
            findings.extend(
                _check_terms_compliance(
                    aligned_pairs,
                    terms_path=terms_path,
                    target_lang=language,
                )
            )
    return anchor_pages, findings


def _summarize_findings(findings: Sequence[dict[str, Any]]) -> dict[str, Any]:
    errors = sum(1 for item in findings if item.get("severity") == "error")
    warnings = sum(1 for item in findings if item.get("severity") == "warning")
    by_type = dict(sorted(Counter(str(item.get("type") or "") for item in findings).items()))
    return {
        "errors": errors,
        "warnings": warnings,
        "total_findings": len(findings),
        "by_type": by_type,
    }


def _sort_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        findings,
        key=lambda item: (
            0 if item.get("severity") == "error" else 1,
            str(item.get("type") or ""),
            str(item.get("page_stem") or ""),
            json.dumps(item, ensure_ascii=False, sort_keys=True),
        ),
    )


def _empty_audit_report(
    *,
    ir_path: Path,
    anchor_ir_path: Path | None,
    terms_path: Path | None,
    verify_assets: bool,
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    sorted_findings = _sort_findings(findings)
    return {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "ir_path": str(ir_path),
        "anchor_ir_path": str(anchor_ir_path) if anchor_ir_path else None,
        "terms_path": str(terms_path) if terms_path else None,
        "model": "",
        "region": "",
        "language": "",
        "verify_assets": verify_assets,
        "summary": _summarize_findings(sorted_findings),
        "findings": sorted_findings,
    }


def audit_manual_ir(
    ir_path: Path,
    anchor_ir_path: Path | None = None,
    terms_path: Path | None = None,
    verify_assets: bool = True,
) -> dict[str, Any]:
    """Run structural, asset, English-residue, callout, and glossary checks on manual.ir.json."""

    payload, schema_findings = _read_ir_json(ir_path)
    if payload is None:
        return _empty_audit_report(
            ir_path=ir_path,
            anchor_ir_path=anchor_ir_path,
            terms_path=terms_path,
            verify_assets=verify_assets,
            findings=schema_findings,
        )

    pages = [page for page in payload.get("pages", []) if isinstance(page, dict)]
    raw_meta = payload.get("metadata")
    metadata: dict[str, Any] = raw_meta if isinstance(raw_meta, dict) else {}
    language = str(payload.get("language") or "").strip()
    findings: list[dict[str, Any]] = []

    for page in pages:
        stem = normalize_page_stem(str(page.get("page_id") or ""))
        findings.extend(_check_empty_headings(page, stem))
        findings.extend(_check_unresolved_markers(page, stem))

    checked_assets = 0
    if verify_assets:
        asset_findings, checked_assets = _verify_package_assets(metadata, ir_path.parent)
        findings.extend(asset_findings)

    anchor_pages, anchor_findings = _run_anchor_checks(
        ir_path=ir_path,
        anchor_ir_path=anchor_ir_path,
        terms_path=terms_path,
        language=language,
    )
    findings.extend(anchor_findings)
    findings.extend(_check_callouts(pages, anchor_pages))

    sorted_findings = _sort_findings(findings)
    summary = _summarize_findings(sorted_findings)
    summary["page_count"] = len(pages)
    summary["checked_asset_count"] = checked_assets
    return {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "ir_path": str(ir_path),
        "anchor_ir_path": str(anchor_ir_path) if anchor_ir_path else None,
        "terms_path": str(terms_path) if terms_path else None,
        "model": str(payload.get("model") or ""),
        "region": str(payload.get("region") or ""),
        "language": language,
        "verify_assets": verify_assets,
        "summary": summary,
        "findings": sorted_findings,
    }


def _parse_asset_registry_hashes(csv_path: Path) -> dict[str, list[dict[str, str]]]:
    by_sha: dict[str, list[dict[str, str]]] = defaultdict(list)
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            raw_hashes = (row.get("内容哈希") or "").strip()
            if not raw_hashes:
                continue
            entry = {
                "asset_key": (row.get("asset_key") or "").strip(),
                "category": (row.get("类别") or "").strip(),
                "language_dimension": (row.get("语言维度") or "").strip(),
                "status": (row.get("状态") or "").strip(),
            }
            for token in _HASH_ENTRY_SPLIT_RE.split(raw_hashes):
                if ":" not in token:
                    continue
                _, sha = token.rsplit(":", 1)
                digest = sha.strip().casefold()
                if digest:
                    by_sha[digest].append(entry)
    return dict(by_sha)


def _resolve_registry_csv(asset_registry_csv: Path | None) -> Path | None:
    if asset_registry_csv is not None:
        return asset_registry_csv
    candidate = REPO_ROOT / "data" / "asset_registry.csv"
    return candidate if candidate.is_file() else None


def _build_visual_asset_attribution(
    metadata: dict[str, Any],
    asset_registry_csv: Path | None,
) -> dict[str, Any]:
    asset_map = metadata.get("asset_sha256")
    packaged = asset_map if isinstance(asset_map, dict) else {}
    registry_path = _resolve_registry_csv(asset_registry_csv)
    if registry_path is None:
        return {
            "status": "not_provided",
            "unit": "packaged_asset_files",
            "registry_path": None,
            "total_packaged_assets": len(packaged),
            "registered_asset_count": None,
            "unique_asset_keys": [],
            "matched_assets": [],
            "unregistered_assets": [],
        }

    sha_index = _parse_asset_registry_hashes(registry_path)
    matched_assets: list[dict[str, Any]] = []
    unregistered_assets: list[dict[str, Any]] = []
    unique_keys: set[str] = set()

    for rel_raw, sha_raw in sorted(packaged.items()):
        rel_path = str(rel_raw)
        digest = str(sha_raw or "").strip().casefold()
        hits = sha_index.get(digest, [])
        if hits:
            keys = sorted({hit["asset_key"] for hit in hits if hit["asset_key"]})
            categories = sorted({hit["category"] for hit in hits if hit["category"]})
            unique_keys.update(keys)
            matched_assets.append(
                {
                    "rel_path": rel_path,
                    "sha256": digest,
                    "asset_keys": keys,
                    "categories": categories,
                }
            )
        else:
            unregistered_assets.append({"rel_path": rel_path, "sha256": digest})

    return {
        "status": "attributed",
        "unit": "packaged_asset_files",
        "registry_path": str(registry_path),
        "total_packaged_assets": len(packaged),
        "registered_asset_count": len(matched_assets),
        "unique_asset_keys": sorted(unique_keys),
        "matched_assets": matched_assets,
        "unregistered_assets": unregistered_assets,
    }


def _extract_non_noise_target_segments(
    pages: Sequence[dict[str, Any]],
) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for page in pages:
        stem = normalize_page_stem(str(page.get("page_id") or ""))
        for blk in extract_page_blocks(page):
            for seg in blk.segments:
                norm = normalize_space(seg.text)
                if norm and not is_noise_segment(norm):
                    items.append((stem, norm))
    return items


def _build_tm_pair_index(
    tm_json_path: Path,
    *,
    en_col: str,
    target_col: str,
    target_lang_key: str,
) -> tuple[dict[tuple[str, str], list[str]], dict[str, list[str]]]:
    rows = _filter_approved_rows(_load_json_records(tm_json_path))
    en_key = default_anchor_lang()
    pair_index: dict[tuple[str, str], list[str]] = defaultdict(list)
    target_index: dict[str, list[str]] = defaultdict(list)
    for rid, fields in rows:
        if not rid:
            continue
        en_text = normalize_space(_lookup_lang_field(fields, en_col, en_key))
        target_text = normalize_space(_lookup_lang_field(fields, target_col, target_lang_key))
        if target_text:
            target_index[target_text].append(rid)
        if en_text and target_text:
            pair_index[(en_text, target_text)].append(rid)
    return dict(pair_index), dict(target_index)


def _match_tm_segments(
    *,
    ir_path: Path,
    pages: Sequence[dict[str, Any]],
    language: str,
    anchor_ir_path: Path | None,
    tm_json_path: Path | None,
) -> dict[str, Any]:
    if tm_json_path is None:
        return {
            "status": "not_provided",
            "unit": "translatable_segments",
            "tm_json_path": None,
            "matched_tm_record_ids": [],
            "matched_segment_count": None,
            "total_translatable_segments": len(_extract_non_noise_target_segments(pages)),
            "per_page": [],
        }

    en_col = resolve_tm_column(default_anchor_lang())
    target_lang_key = normalize_lang_key(language)
    target_col = resolve_tm_column(language)
    pair_index, target_index = _build_tm_pair_index(
        tm_json_path,
        en_col=en_col,
        target_col=target_col,
        target_lang_key=target_lang_key,
    )

    page_totals: dict[str, int] = Counter()
    page_matches: dict[str, int] = Counter()
    page_ids: dict[str, set[str]] = defaultdict(set)
    matched_ids: set[str] = set()
    total_segments = 0
    matched_count = 0

    if anchor_ir_path is not None:
        _t_ir, _a_ir, aligned, align_errs = _align_target_with_anchor(ir_path, anchor_ir_path)
        if align_errs:
            raise ValueError(align_errs[0]["message"])
        for seg in aligned:
            total_segments += 1
            page_totals[seg.page_stem] += 1
            rids = pair_index.get(
                (normalize_space(seg.en_text), normalize_space(seg.target_text)), []
            )
            if rids:
                matched_count += 1
                page_matches[seg.page_stem] += 1
                matched_ids.update(rids)
                page_ids[seg.page_stem].update(rids)
    else:
        for stem, text in _extract_non_noise_target_segments(pages):
            total_segments += 1
            page_totals[stem] += 1
            rids = target_index.get(text, [])
            if rids:
                matched_count += 1
                page_matches[stem] += 1
                matched_ids.update(rids)
                page_ids[stem].update(rids)

    per_page = [
        {
            "page_stem": stem,
            "matched_segment_count": page_matches[stem],
            "total_translatable_segments": page_totals[stem],
            "matched_tm_record_ids": sorted(page_ids[stem]),
        }
        for stem in sorted(page_totals)
    ]
    return {
        "status": "attributed",
        "unit": "translatable_segments",
        "tm_json_path": str(tm_json_path),
        "matched_tm_record_ids": sorted(matched_ids),
        "matched_segment_count": matched_count,
        "total_translatable_segments": total_segments,
        "per_page": per_page,
    }


def _build_component_attribution(
    pages: Sequence[dict[str, Any]],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    component_ids: set[str] = set()
    component_block_count = 0
    for page in pages:
        for block in page.get("blocks") or ():
            root = block.get("payload") if isinstance(block, dict) and "payload" in block else block
            for node in _iter_flow_dicts(root):
                if node.get("kind") != "component":
                    continue
                cid = str((node.get("component_spec") or {}).get("component_id") or "").strip()
                if cid:
                    component_ids.add(cid)
                    component_block_count += 1

    overview = metadata.get("overview_instance")
    overview_instance_id = (
        str(overview.get("instance_id")).strip()
        if isinstance(overview, dict) and overview.get("instance_id")
        else None
    )
    return {
        "unit": "component_blocks",
        "component_ids": sorted(component_ids),
        "component_block_count": component_block_count,
        "overview_instance_id": overview_instance_id,
    }


def build_ir_provenance(
    ir_path: Path,
    anchor_ir_path: Path | None = None,
    asset_registry_csv: Path | None = None,
    tm_json_path: Path | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Build separate visual-asset, TM-B, and component attribution sidecar for manual.ir.json."""

    payload, schema_findings = _read_ir_json(ir_path)
    if payload is None:
        msg = schema_findings[0].get("message", "Invalid manual.ir.json")
        raise ValueError(msg)

    pages = [page for page in payload.get("pages", []) if isinstance(page, dict)]
    raw_meta = payload.get("metadata")
    metadata: dict[str, Any] = raw_meta if isinstance(raw_meta, dict) else {}
    language = str(payload.get("language") or "").strip()

    report: dict[str, Any] = {
        "schema_version": PROVENANCE_SCHEMA_VERSION,
        "ir_path": str(ir_path),
        "anchor_ir_path": str(anchor_ir_path) if anchor_ir_path else None,
        "model": str(payload.get("model") or ""),
        "region": str(payload.get("region") or ""),
        "language": language,
        "visual_assets": _build_visual_asset_attribution(metadata, asset_registry_csv),
        "tm_attribution": _match_tm_segments(
            ir_path=ir_path,
            pages=pages,
            language=language,
            anchor_ir_path=anchor_ir_path,
            tm_json_path=tm_json_path,
        ),
        "components": _build_component_attribution(pages, metadata),
    }

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return report


def _write_report_output(report: dict[str, Any], output_path: Path | None) -> str:
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
    return rendered


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for audit and provenance subcommands."""

    parser = argparse.ArgumentParser(
        description="Multilingual QC audit and asset/TM/component provenance for <MODEL> manual.ir.json bundles."
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    audit_cmd = subcommands.add_parser(
        "audit",
        help="Run structural, asset, residue, callout, and glossary checks on manual.ir.json.",
    )
    audit_cmd.add_argument("--ir", type=Path, required=True, help="Target manual.ir.json path")
    audit_cmd.add_argument("--anchor-ir", type=Path, default=None, help="Optional English anchor manual.ir.json")
    audit_cmd.add_argument("--terms-json", type=Path, default=None, help="Optional TM-B Terms JSON export")
    audit_cmd.add_argument(
        "--no-verify-assets",
        dest="verify_assets",
        action="store_false",
        help="Skip verifying metadata.asset_sha256 files on disk",
    )
    audit_cmd.set_defaults(verify_assets=True)
    audit_cmd.add_argument("--strict", action="store_true", help="Exit 1 on warnings as well as errors")
    audit_cmd.add_argument("--output", type=Path, default=None, help="Optional JSON output file path")

    prov_cmd = subcommands.add_parser(
        "provenance",
        help="Build non-mutating visual-asset, TM-B, and component attribution sidecar JSON.",
    )
    prov_cmd.add_argument("--ir", type=Path, required=True, help="Target manual.ir.json path")
    prov_cmd.add_argument("--anchor-ir", type=Path, default=None, help="Optional English anchor manual.ir.json")
    prov_cmd.add_argument("--asset-registry", type=Path, default=None, help="Optional asset_registry.csv override")
    prov_cmd.add_argument("--tm-json", type=Path, default=None, help="Optional TM-B Translation_Memory JSON export")
    prov_cmd.add_argument("--output", type=Path, default=None, help="Optional JSON sidecar output file path")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for tools.web.ir_qc."""

    args = parse_args(argv)
    if args.command == "audit":
        report = audit_manual_ir(
            args.ir,
            anchor_ir_path=args.anchor_ir,
            terms_path=args.terms_json,
            verify_assets=args.verify_assets,
        )
        print(_write_report_output(report, args.output))
        summary = report["summary"]
        if summary["errors"] > 0 or (args.strict and summary["warnings"] > 0):
            return 1
        return 0

    try:
        report = build_ir_provenance(
            args.ir,
            anchor_ir_path=args.anchor_ir,
            asset_registry_csv=args.asset_registry,
            tm_json_path=args.tm_json,
            output_path=args.output,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"[ir_qc] ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


__all__ = [
    "AUDIT_SCHEMA_VERSION",
    "PROVENANCE_SCHEMA_VERSION",
    "audit_manual_ir",
    "build_ir_provenance",
    "main",
    "resolve_callout_severity",
    "resolve_tm_column",
]


if __name__ == "__main__":
    raise SystemExit(main())
