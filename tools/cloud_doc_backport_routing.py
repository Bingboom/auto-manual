#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Delta classification + routing for cloud-doc backport (debt-paydown D2-4).

Turns a baseline-vs-fetched block diff into routed deltas (Class R/D/T/image/
semantic). Imports the Block model from cloud_doc_backport_model; re-exported by
cloud_doc_backport.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.cloud_doc_backport_model import (  # noqa: E402
    Block,
    _IMAGE_SENTINELS,
    _context,
    _heading_title,
    _location,
    _section_key,
)
from tools.token_resolution_map import classify_data_origin  # noqa: E402
from tools.family_scope import classify_family_scope  # noqa: E402


DELTA_SCHEMA_VERSION = "cloud-doc-backport-delta/v1"

_PLACEHOLDER_RE = re.compile(r"(\{\{[^}]+\}\}|\|[A-Z][A-Z0-9_]+\|)")

_UNIT_VALUE_RE = re.compile(
    r"\b\d+(?:[.,]\d+)?\s?(?:W|V|A|Hz|Wh|kWh|mAh|Ah|degC|°C|%|mm|cm|m|kg|lb)\b",
    re.IGNORECASE,
)

_OUTPUT_TERMS = (
    "output",
    "salida",
    "uscita",
    "ausgang",
    "sortie",
    "saída",
    "saida",
    "вихід",
    "выход",
)

_BUTTON_TERMS = (
    "button",
    "botón",
    "boton",
    "pulsante",
    "taste",
    "knopf",
    "bouton",
    "кнопка",
    "кнопку",
)

def _looks_data_like(*blocks: Block | None) -> bool:
    text = " ".join(block.text for block in blocks if block is not None)
    if any(block and block.kind == "table_row" for block in blocks):
        return True
    return bool(_PLACEHOLDER_RE.search(text) or _UNIT_VALUE_RE.search(text))

def _without_image_placeholders(text: str) -> str:
    value = text
    for sentinel in _IMAGE_SENTINELS:
        value = value.replace(sentinel, "")
    value = value.replace("|", " ")
    return re.sub(r"\s+", " ", value).strip()

def _is_image_asset_delta(old: Block | None, new: Block | None) -> bool:
    old_norm = old.normalized if old is not None else ""
    new_norm = new.normalized if new is not None else ""
    combined = f"{old_norm} {new_norm}"
    if not any(sentinel in combined for sentinel in _IMAGE_SENTINELS):
        return False
    old_text = _without_image_placeholders(old_norm)
    new_text = _without_image_placeholders(new_norm)
    return (not old_text and not new_text) or old_text == new_text

def _contains_any_term(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.casefold()
    return any(term.casefold() in lowered for term in terms)

def _semantic_review_flags(old: Block | None, new: Block | None) -> list[dict[str, str]]:
    old_text = old.normalized if old is not None else ""
    new_text = new.normalized if new is not None else ""
    if not old_text or not new_text:
        return []
    old_output = _contains_any_term(old_text, _OUTPUT_TERMS)
    new_output = _contains_any_term(new_text, _OUTPUT_TERMS)
    old_button = _contains_any_term(old_text, _BUTTON_TERMS)
    new_button = _contains_any_term(new_text, _BUTTON_TERMS)
    flags: list[dict[str, str]] = []
    if old_output and new_button and not old_button:
        flags.append(
            {
                "type": "output_to_button",
                "severity": "review_required",
                "reason": "changed output terminology to button terminology; confirm whether the sentence refers to controls",
            }
        )
    if old_button and new_output and not old_output:
        flags.append(
            {
                "type": "button_to_output",
                "severity": "review_required",
                "reason": "changed button terminology to output terminology; confirm whether the sentence refers to outputs",
            }
        )
    return flags

def _classify_route(
    doc_type: str,
    old: Block | None,
    new: Block | None,
    data_origin: dict[str, Any] | None = None,
    family_scope: dict[str, Any] | None = None,
    *,
    value_index_present: bool = False,
    semantic_review_flags: list[dict[str, str]] | None = None,
) -> tuple[str, str, str]:
    if _is_image_asset_delta(old, new):
        return (
            "image_asset_delta",
            "medium",
            "image-only/token-only delta; route to image asset handling, not source tables",
        )
    if data_origin is not None:
        # F2: the old text resolved to a data value (whole-text or table-cell match),
        # so this is a data-origin (Class D) delta — deterministic, not the heuristic guess.
        if doc_type == "review":
            return (
                "source_table_suggestion",
                "high",
                f"resolved data value from {data_origin.get('table')}",
            )
        return (
            "needs_human_mapping",
            "low",
            "resolved data value in a template-maintenance document",
        )
    # Data-like detection. A table row is structurally source-table content, so it stays
    # Class D even when no specific cell value is in the snapshot (safe — never write table
    # markup to _review). For non-table prose, the value index is **authoritative** when
    # present: a delta that resolved to no source value is genuinely review text, so route
    # it as such instead of the `_looks_data_like` guess (which over-flags any unit/number-
    # bearing prose). Without an index, keep the heuristic (prior behavior).
    table_like = any(block is not None and block.kind == "table_row" for block in (old, new))
    if table_like:
        data_like = True
    elif value_index_present:
        data_like = False
    else:
        data_like = _looks_data_like(old, new)
    if data_like:
        if doc_type == "review":
            return (
                "source_table_suggestion",
                "medium",
                "table/value/placeholder-like delta in a review document",
            )
        return (
            "needs_human_mapping",
            "low",
            "data-like delta in a template-maintenance document",
        )
    if doc_type == "review":
        if semantic_review_flags:
            return (
                "needs_human_mapping",
                "low",
                "semantic terminology risk requires operator confirmation before writing review RST",
            )
        if family_scope is not None and family_scope.get("shared"):
            # F3: the span is identical across the family — template-origin shared
            # content. Flag for a human decision (shared-template change vs
            # target-local override) with blast radius; do not auto-route (R5).
            count = len(family_scope.get("targets") or [])
            return (
                "needs_human_mapping",
                "medium",
                f"span is identical across {count} family target(s): decide shared-template change vs target-local override",
            )
        return ("repo_review_text", "medium", "text delta in a review document")
    return ("repo_template_text", "medium", "text delta in a template document")

def _delta_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def _make_delta(
    *,
    run_id: str,
    doc_type: str,
    change_type: str,
    old: Block | None,
    new: Block | None,
    old_index: int | None,
    new_index: int | None,
    baseline_blocks: list[Block],
    fetched_blocks: list[Block],
    value_index: dict[str, Any] | None = None,
    family_index: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data_origin = (
        # Match the normalized (markdown-stripped) text so a table-cell value compares
        # cleanly against the snapshot CSV values (cell-level resolution).
        classify_data_origin(old.normalized, value_index) if (value_index and old is not None) else None
    )
    family_scope = (
        classify_family_scope(old.text, family_index)
        if (family_index and old is not None and data_origin is None)
        else None
    )
    semantic_flags = _semantic_review_flags(old, new)
    route_class, confidence, reason = _classify_route(
        doc_type,
        old,
        new,
        data_origin,
        family_scope,
        value_index_present=bool(value_index),
        semantic_review_flags=semantic_flags,
    )
    hash_payload = {
        "doc_type": doc_type,
        "change_type": change_type,
        "old": old.normalized if old else None,
        "new": new.normalized if new else None,
        "location": _location(new or old),
    }
    context: dict[str, Any] = {}
    if old_index is not None:
        context["baseline"] = _context(baseline_blocks, old_index)
    if new_index is not None:
        context["fetched"] = _context(fetched_blocks, new_index)
    return {
        "schema_version": DELTA_SCHEMA_VERSION,
        "run_id": run_id,
        "delta_hash": _delta_hash(hash_payload),
        "doc_type": doc_type,
        "change_type": change_type,
        "route_class": route_class,
        "confidence": confidence,
        "classification_reason": reason,
        "source_ref": data_origin,
        "family_scope": family_scope,
        "semantic_review": {"required": bool(semantic_flags), "flags": semantic_flags},
        "location": _location(new or old),
        "old_text": old.text if old else None,
        "new_text": new.text if new else None,
        "old_normalized": old.normalized if old else None,
        "new_normalized": new.normalized if new else None,
        "context": context,
    }

def diff_blocks(
    baseline_blocks: list[Block],
    fetched_blocks: list[Block],
    *,
    doc_type: str,
    run_id: str,
    value_index: dict[str, Any] | None = None,
    family_index: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    import difflib

    def diff_key(block: Block) -> str:
        if block.kind == "heading":
            return "heading:" + _section_key(_heading_title(block))
        return block.normalized

    baseline_norm = [diff_key(block) for block in baseline_blocks]
    fetched_norm = [diff_key(block) for block in fetched_blocks]
    matcher = difflib.SequenceMatcher(None, baseline_norm, fetched_norm, autojunk=False)
    deltas: list[dict[str, Any]] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag == "replace":
            old_range = list(range(i1, i2))
            new_range = list(range(j1, j2))
            paired = min(len(old_range), len(new_range))
            for offset in range(paired):
                old_index = old_range[offset]
                new_index = new_range[offset]
                deltas.append(
                    _make_delta(
                        run_id=run_id,
                        doc_type=doc_type,
                        change_type="replace",
                        old=baseline_blocks[old_index],
                        new=fetched_blocks[new_index],
                        old_index=old_index,
                        new_index=new_index,
                        baseline_blocks=baseline_blocks,
                        fetched_blocks=fetched_blocks,
                        value_index=value_index,
                        family_index=family_index,
                    )
                )
            for old_index in old_range[paired:]:
                deltas.append(
                    _make_delta(
                        run_id=run_id,
                        doc_type=doc_type,
                        change_type="delete",
                        old=baseline_blocks[old_index],
                        new=None,
                        old_index=old_index,
                        new_index=None,
                        baseline_blocks=baseline_blocks,
                        fetched_blocks=fetched_blocks,
                        value_index=value_index,
                        family_index=family_index,
                    )
                )
            for new_index in new_range[paired:]:
                deltas.append(
                    _make_delta(
                        run_id=run_id,
                        doc_type=doc_type,
                        change_type="insert",
                        old=None,
                        new=fetched_blocks[new_index],
                        old_index=None,
                        new_index=new_index,
                        baseline_blocks=baseline_blocks,
                        fetched_blocks=fetched_blocks,
                        value_index=value_index,
                        family_index=family_index,
                    )
                )
            continue

        if tag == "delete":
            for old_index in range(i1, i2):
                deltas.append(
                    _make_delta(
                        run_id=run_id,
                        doc_type=doc_type,
                        change_type="delete",
                        old=baseline_blocks[old_index],
                        new=None,
                        old_index=old_index,
                        new_index=None,
                        baseline_blocks=baseline_blocks,
                        fetched_blocks=fetched_blocks,
                        value_index=value_index,
                        family_index=family_index,
                    )
                )
            continue

        if tag == "insert":
            for new_index in range(j1, j2):
                deltas.append(
                    _make_delta(
                        run_id=run_id,
                        doc_type=doc_type,
                        change_type="insert",
                        old=None,
                        new=fetched_blocks[new_index],
                        old_index=None,
                        new_index=new_index,
                        baseline_blocks=baseline_blocks,
                        fetched_blocks=fetched_blocks,
                        value_index=value_index,
                        family_index=family_index,
                    )
                )
    return deltas
