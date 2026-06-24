#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Backport report builders (diff / verify / suggestions / template-proposal / run).

D2-7. Assemble report dicts + write them. Import from the leaf modules; re-exported.
"""
from __future__ import annotations

import sys
import json
import shlex
from typing import Any
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.cloud_doc_backport_model import (  # noqa: E402
    SectionSelection,
    _apply_section_selection,
    _display_path,
    _read_text,
    _report_path_text,
    parse_blocks,
)
from tools.cloud_doc_backport_util import (  # noqa: E402
    NORMALIZER_VERSION,
    REPORT_SCHEMA_VERSION,
    RUN_SCHEMA_VERSION,
    SOURCE_TABLE_SUGGESTIONS_SCHEMA_VERSION,
    TEMPLATE_SYNC_PROPOSAL_SCHEMA_VERSION,
    VERIFY_SCHEMA_VERSION,
    _counter_dict,
    _git_ref,
    _resolve_source_path,
    _utc_now,
    _validate_apply_source,
)
from tools.cloud_doc_backport_routing import (  # noqa: E402
    _PLACEHOLDER_RE,
    _UNIT_VALUE_RE,
    diff_blocks,
)
from tools.cloud_doc_backport_apply import (  # noqa: E402
    _heading_text_key,
)
from tools.cloud_doc_backport_render import (  # noqa: E402
    markdown_apply_report,
    markdown_report,
    markdown_review_run_report,
    markdown_source_table_suggestions_report,
    markdown_template_sync_proposal_report,
    markdown_verify_report,
)
from tools.utils.path_utils import get_paths  # noqa: E402


def _source_kind_for_path(path: Path | None, doc_type: str) -> str | None:
    if path is None:
        return None
    parts = path.as_posix().split("/")
    if "templates" in parts:
        return "template"
    if "_review" in parts:
        return "review"
    return doc_type

def _source_target_payload(source_path: Path | None, doc_type: str) -> dict[str, str] | None:
    if source_path is None:
        return None
    return {
        "path": _report_path_text(source_path),
        "kind": _source_kind_for_path(source_path, doc_type) or doc_type,
    }

def _selection_payload(selection: SectionSelection) -> dict[str, Any]:
    return {
        "requested_title": selection.requested_title,
        "resolved_title": selection.resolved_title,
        "inferred_from": selection.inferred_from,
        "applied": selection.applied,
        "baseline_found": selection.baseline_found,
        "fetched_found": selection.fetched_found,
        "baseline_blocks_before": selection.baseline_blocks_before,
        "fetched_blocks_before": selection.fetched_blocks_before,
        "baseline_blocks_after": selection.baseline_blocks_after,
        "fetched_blocks_after": selection.fetched_blocks_after,
    }

def _attach_source_evidence(
    deltas: list[dict[str, Any]],
    *,
    source_target: dict[str, str] | None,
    baseline_text: str,
) -> None:
    if source_target is None:
        return
    for delta in deltas:
        old_text = delta.get("old_text")
        old_in_source = bool(isinstance(old_text, str) and old_text and old_text in baseline_text)
        delta["source_evidence"] = {
            **source_target,
            "old_text_in_baseline": old_in_source,
            "repo_write_candidate": delta["route_class"] in {"repo_review_text", "repo_template_text"} and old_in_source,
        }

def build_report(
    *,
    run_id: str,
    doc_type: str,
    doc_url: str,
    baseline_path: Path,
    fetched_text: str,
    baseline_text: str,
    command: list[str],
    source_path: Path | None = None,
    section_title: str | None = None,
    section_inferred_from: str | None = None,
    require_section_match: bool = False,
    value_index: dict[str, Any] | None = None,
    family_index: dict[str, Any] | None = None,
) -> dict[str, Any]:
    baseline_blocks = parse_blocks(baseline_text)
    fetched_blocks = parse_blocks(fetched_text)
    baseline_blocks, fetched_blocks, selection = _apply_section_selection(
        baseline_blocks=baseline_blocks,
        fetched_blocks=fetched_blocks,
        section_title=section_title,
        inferred_from=section_inferred_from,
        require_match=require_section_match,
    )
    deltas = diff_blocks(
        baseline_blocks,
        fetched_blocks,
        doc_type=doc_type,
        run_id=run_id,
        value_index=value_index,
        family_index=family_index,
    )
    source_target = _source_target_payload(source_path, doc_type)
    _attach_source_evidence(deltas, source_target=source_target, baseline_text=baseline_text)
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "run_id": run_id,
        "doc_type": doc_type,
        "doc_url": doc_url,
        "baseline": _report_path_text(baseline_path),
        "source_target": source_target,
        "section_selection": _selection_payload(selection),
        "normalizer_version": NORMALIZER_VERSION,
        "result": "DIFF" if deltas else "NO_DIFF",
        "metadata": {
            "generated_at": _utc_now(),
            "git_ref": _git_ref(),
            "command": shlex.join(command),
        },
        "summary": {
            "total_deltas": len(deltas),
            "baseline_blocks": len(baseline_blocks),
            "fetched_blocks": len(fetched_blocks),
            "change_types": _counter_dict([delta["change_type"] for delta in deltas]),
            "route_classes": _counter_dict([delta["route_class"] for delta in deltas]),
            "confidence": _counter_dict([delta["confidence"] for delta in deltas]),
            "semantic_review_required": sum(
                1 for delta in deltas if (delta.get("semantic_review") or {}).get("required")
            ),
        },
        "deltas": deltas,
    }

def write_reports(report: dict[str, Any], out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "cloud_doc_backport_report.json"
    markdown_path = out_dir / "cloud_doc_backport_report.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(markdown_report(report), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}

def write_apply_report(report: dict[str, Any], out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "cloud_doc_backport_apply.json"
    markdown_path = out_dir / "cloud_doc_backport_apply.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(markdown_apply_report(report), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}

def _resolve_report_source(
    diff_report: dict[str, Any],
    *,
    expected_doc_type: str,
    expected_source_kind: str,
    source_path: Path | None,
    command_name: str,
) -> Path:
    if diff_report.get("schema_version") != REPORT_SCHEMA_VERSION:
        raise RuntimeError("report schema is not cloud-doc-backport-report/v1")
    if diff_report.get("doc_type") != expected_doc_type:
        raise RuntimeError(f"{command_name} requires a {expected_doc_type} diff report")
    source_target = diff_report.get("source_target")
    if not isinstance(source_target, dict):
        if source_path is None:
            raise RuntimeError("diff report is missing source_target")
        source_target = {"kind": expected_source_kind}
    elif source_target.get("kind") != expected_source_kind:
        raise RuntimeError(f"diff report source_target.kind must be {expected_source_kind}")
    resolved_source = source_path or _resolve_source_path(str(source_target.get("path") or ""), label="source target")
    _validate_apply_source(resolved_source, kind=expected_source_kind)
    return resolved_source

def _verify_delta(index: int, delta: dict[str, Any], current_text: str) -> dict[str, Any]:
    old_text = delta.get("old_text")
    new_text = delta.get("new_text")
    old_matches = current_text.count(old_text) if isinstance(old_text, str) and old_text else 0
    new_matches = current_text.count(new_text) if isinstance(new_text, str) and new_text else 0
    base_result = {
        "index": index,
        "delta_hash": delta.get("delta_hash"),
        "change_type": delta.get("change_type"),
        "route_class": delta.get("route_class"),
        "old_text": old_text,
        "new_text": new_text,
        "location": delta.get("location") or {},
        "source_evidence": delta.get("source_evidence") or {},
    }
    route_class = delta.get("route_class")
    if route_class == "image_asset_delta":
        return {
            **base_result,
            "category": "image_asset_delta",
            "status": "reported",
            "reason": "image asset delta is report-only",
            "old_matches": old_matches,
            "new_matches": new_matches,
        }
    if route_class == "source_table_suggestion":
        return {
            **base_result,
            "category": "source_table_suggestion",
            "status": "reported",
            "reason": "data-like review delta is report-only",
            "old_matches": old_matches,
            "new_matches": new_matches,
        }
    if route_class != "repo_review_text":
        return {
            **base_result,
            "category": "unsafe_or_ambiguous",
            "status": "blocked",
            "reason": f"route_class is {route_class or 'missing'}",
            "old_matches": 0,
            "new_matches": 0,
        }
    change_type = delta.get("change_type")
    if change_type not in {"replace", "delete"}:
        return {
            **base_result,
            "category": "unsafe_or_ambiguous",
            "status": "blocked",
            "reason": f"unsupported review change_type {change_type or 'missing'}",
            "old_matches": 0,
            "new_matches": 0,
        }
    if not isinstance(old_text, str) or not old_text:
        return {
            **base_result,
            "category": "unsafe_or_ambiguous",
            "status": "blocked",
            "reason": "old_text is missing",
            "old_matches": 0,
            "new_matches": 0,
        }
    if change_type == "replace" and (not isinstance(new_text, str) or not new_text):
        return {
            **base_result,
            "category": "unsafe_or_ambiguous",
            "status": "blocked",
            "reason": "new_text is missing",
            "old_matches": 0,
            "new_matches": 0,
        }

    if change_type == "delete":
        if old_matches == 0:
            return {
                **base_result,
                "category": "applied_resolved",
                "status": "resolved",
                "reason": "deleted old_text no longer exists",
                "old_matches": old_matches,
                "new_matches": new_matches,
            }
        if old_matches == 1:
            return {
                **base_result,
                "category": "still_pending",
                "status": "pending",
                "reason": "deleted old_text still exists",
                "old_matches": old_matches,
                "new_matches": new_matches,
            }
        return {
            **base_result,
            "category": "unsafe_or_ambiguous",
            "status": "blocked",
            "reason": "deleted old_text has an ambiguous match count",
            "old_matches": old_matches,
            "new_matches": new_matches,
        }

    if old_matches == 0 and new_matches >= 1:
        return {
            **base_result,
            "category": "applied_resolved",
            "status": "resolved",
            "reason": "old_text no longer exists and new_text is present",
            "old_matches": old_matches,
            "new_matches": new_matches,
        }
    if old_matches == 1 and new_matches == 0:
        return {
            **base_result,
            "category": "still_pending",
            "status": "pending",
            "reason": "old_text still exists and new_text is absent",
            "old_matches": old_matches,
            "new_matches": new_matches,
        }
    return {
        **base_result,
        "category": "unsafe_or_ambiguous",
        "status": "blocked",
        "reason": "current review source contains an ambiguous old/new text state",
        "old_matches": old_matches,
        "new_matches": new_matches,
    }

def _resolve_baseline_text(diff_report: dict[str, Any]) -> str | None:
    """Best-effort read of the diff baseline (for the F5 rebuild+rediff gate)."""
    baseline = diff_report.get("baseline")
    if not isinstance(baseline, str) or not baseline:
        return None
    for candidate in (Path(baseline), get_paths().root / baseline):
        if candidate.exists():
            try:
                return candidate.read_text(encoding="utf-8")
            except OSError:
                return None
    return None

def _rebuild_rediff_gate(
    *, baseline_text: str, edited_text: str, deltas: list[Any], run_id: str
) -> dict[str, Any]:
    """F5: re-diff baseline vs the edited source; the only changes must be the
    intended repo_review_text deltas (no collateral, none missing)."""

    def pair(delta: dict[str, Any]) -> tuple[Any, Any]:
        # Headings: compare on TITLE only. The reST source re-diff yields `# title` (level 1)
        # while the original delta carries the cloud-doc's `## title` — a raw-normalized
        # compare would never match and would wrongly fail the gate on every heading edit.
        if ((delta.get("location") or {}).get("kind")) == "heading":
            return (
                _heading_text_key(str(delta.get("old_normalized") or "")),
                _heading_text_key(str(delta.get("new_normalized") or "")),
            )
        return (delta.get("old_normalized"), delta.get("new_normalized"))

    expected = {
        pair(delta)
        for delta in deltas
        if isinstance(delta, dict) and delta.get("route_class") == "repo_review_text"
    }
    actual = {
        pair(delta)
        for delta in diff_blocks(
            parse_blocks(baseline_text), parse_blocks(edited_text), doc_type="review", run_id=run_id
        )
    }
    unexpected = sorted(f"{old!r}->{new!r}" for old, new in (actual - expected))
    missing = sorted(f"{old!r}->{new!r}" for old, new in (expected - actual))
    return {
        "skipped": False,
        "passed": not unexpected and not missing,
        "unexpected": unexpected,
        "missing": missing,
    }

def _rebuild_rediff_for_report(
    diff_report: dict[str, Any], edited_text: str, *, baseline_text_override: str | None = None
) -> dict[str, Any]:
    if baseline_text_override is not None:
        # An in-memory pre-edit baseline: run-review reads the source before applying in
        # place, so the gate can run even when the report's baseline IS that same source
        # (the prior skip case). The pre-edit text cannot be recovered from disk after the
        # apply, so it must be passed in.
        return _rebuild_rediff_gate(
            baseline_text=baseline_text_override,
            edited_text=edited_text,
            deltas=diff_report.get("deltas") or [],
            run_id=str(diff_report.get("run_id") or "verify"),
        )
    baseline = diff_report.get("baseline")
    source_path = (diff_report.get("source_target") or {}).get("path")
    if not baseline or (source_path and baseline == source_path):
        # The baseline is the in-place source and no pre-edit snapshot was supplied;
        # after apply the pre-edit text cannot be reconstructed, so the gate is
        # unreliable. It runs only against a distinct baseline snapshot (design §6
        # Baseline Storage) or an explicit in-memory baseline. Skipping is gate-pass.
        return {"skipped": True, "reason": "no distinct baseline snapshot", "passed": True}
    baseline_text = _resolve_baseline_text(diff_report)
    if baseline_text is None:
        return {"skipped": True, "reason": "baseline unavailable", "passed": True}
    return _rebuild_rediff_gate(
        baseline_text=baseline_text,
        edited_text=edited_text,
        deltas=diff_report.get("deltas") or [],
        run_id=str(diff_report.get("run_id") or "verify"),
    )

def build_review_verify_report(
    diff_report: dict[str, Any],
    *,
    source_path: Path | None = None,
    command: list[str] | None = None,
    baseline_text: str | None = None,
) -> dict[str, Any]:
    resolved_source = _resolve_report_source(
        diff_report,
        expected_doc_type="review",
        expected_source_kind="review",
        source_path=source_path,
        command_name="verify-review",
    )
    current_text = _read_text(resolved_source)
    results: list[dict[str, Any]] = []
    for index, delta in enumerate(diff_report.get("deltas") or [], start=1):
        if isinstance(delta, dict):
            results.append(_verify_delta(index, delta, current_text))
        else:
            results.append(
                {
                    "index": index,
                    "category": "unsafe_or_ambiguous",
                    "status": "blocked",
                    "reason": "delta is not an object",
                    "old_matches": 0,
                    "new_matches": 0,
                }
            )
    categories = _counter_dict([str(result["category"]) for result in results])
    failing_categories = {category: categories.get(category, 0) for category in ("still_pending", "unsafe_or_ambiguous")}
    has_failure = any(count for count in failing_categories.values())
    rebuild_rediff = _rebuild_rediff_for_report(diff_report, current_text, baseline_text_override=baseline_text)
    source_table_suggestions = [
        result for result in results if result.get("category") == "source_table_suggestion"
    ]
    return {
        "schema_version": VERIFY_SCHEMA_VERSION,
        "result": "FAIL" if has_failure else "PASS",
        "source_target": {
            "path": _display_path(resolved_source).as_posix(),
            "kind": "review",
        },
        "diff_report": {
            "run_id": diff_report.get("run_id"),
            "result": diff_report.get("result"),
            "schema_version": diff_report.get("schema_version"),
        },
        "metadata": {
            "generated_at": _utc_now(),
            "git_ref": _git_ref(),
            "command": shlex.join(command or []),
        },
        "summary": {
            "total_results": len(results),
            "categories": categories,
            "failing_categories": {key: value for key, value in failing_categories.items() if value},
            "source_table_suggestions": len(source_table_suggestions),
            "rebuild_rediff_passed": rebuild_rediff.get("passed"),
        },
        "rebuild_rediff": rebuild_rediff,
        "source_table_suggestions": source_table_suggestions,
        "results": results,
    }

def write_verify_report(report: dict[str, Any], out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "cloud_doc_backport_verify.json"
    markdown_path = out_dir / "cloud_doc_backport_verify.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(markdown_verify_report(report), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}

def _suggestion_heading_text(suggestion: dict[str, Any]) -> str:
    location = suggestion.get("location") if isinstance(suggestion.get("location"), dict) else {}
    return " > ".join(str(part) for part in (location.get("heading_path") or []) if part)

def _source_table_routing_hint(suggestion: dict[str, Any]) -> dict[str, Any]:
    source_ref = suggestion.get("source_ref") if isinstance(suggestion.get("source_ref"), dict) else {}
    source_table = str(source_ref.get("table") or "").strip()
    if source_table:
        return {
            "route_key": "resolved_source_ref",
            "candidate_source_tables": [source_table],
            "confidence": "high",
            "reason": "delta resolved to an exact source_ref table",
        }
    text = " ".join(
        str(suggestion.get(key) or "") for key in ("old_text", "new_text", "old_normalized", "new_normalized")
    )
    heading = _suggestion_heading_text(suggestion)
    searchable = f"{heading} {text}".lower()
    if _PLACEHOLDER_RE.search(text):
        return {
            "route_key": "placeholder_or_page_value",
            "candidate_source_tables": ["页面占位参数", "Variable_Defaults", "Variable_Lang_Overrides"],
            "confidence": "medium",
            "reason": "placeholder-like token changed in reviewed prose",
        }
    if "troubleshoot" in searchable or "故障" in searchable or "排除" in searchable:
        return {
            "route_key": "troubleshooting_block",
            "candidate_source_tables": ["troubleshooting_blocks", "TROUBLESHOOTING"],
            "confidence": "medium",
            "reason": "suggestion is under a troubleshooting-like heading",
        }
    if "symbol" in searchable or "符号" in searchable or "icon" in searchable or "图标" in searchable:
        return {
            "route_key": "symbol_or_lcd_block",
            "candidate_source_tables": ["symbols_blocks", "lcd_icons"],
            "confidence": "medium",
            "reason": "suggestion is under a symbol/icon-like heading",
        }
    if _UNIT_VALUE_RE.search(text) or "spec" in searchable or "规格" in searchable:
        return {
            "route_key": "spec_or_numeric_value",
            "candidate_source_tables": ["规格参数明细", "Spec_Notes", "Spec_Master read model"],
            "confidence": "medium",
            "reason": "numeric/unit or spec-like value changed",
        }
    location = suggestion.get("location") if isinstance(suggestion.get("location"), dict) else {}
    if location.get("kind") == "table_row":
        return {
            "route_key": "structured_table_row",
            "candidate_source_tables": ["Manual_Copy_Source", "Spec_Notes", "symbols_blocks", "troubleshooting_blocks"],
            "confidence": "low",
            "reason": "review delta came from a table row but no specific table family was inferred",
        }
    return {
        "route_key": "phase2_source_table_review",
        "candidate_source_tables": ["Manual_Copy_Source", "phase2 source tables"],
        "confidence": "low",
        "reason": "data-like review delta needs operator mapping to the source table",
    }

def _operator_locator(suggestion: dict[str, Any]) -> dict[str, Any]:
    location = suggestion.get("location") if isinstance(suggestion.get("location"), dict) else {}
    heading = _suggestion_heading_text(suggestion)
    return {
        "heading_path": location.get("heading_path") or [],
        "heading": heading,
        "line_no": location.get("line_no"),
        "kind": location.get("kind"),
        "old_text": suggestion.get("old_text"),
        "new_text": suggestion.get("new_text"),
    }

def build_source_table_suggestions_report(
    *,
    run_report: dict[str, Any] | None = None,
    diff_report: dict[str, Any] | None = None,
    verify_report: dict[str, Any] | None = None,
    suggestions: list[dict[str, Any]] | None = None,
    command: list[str] | None = None,
) -> dict[str, Any]:
    if suggestions is None:
        if verify_report:
            suggestions = list(verify_report.get("source_table_suggestions") or [])
        elif run_report:
            suggestions = list(run_report.get("source_table_suggestions") or [])
        elif diff_report:
            suggestions = _source_table_suggestions_from_diff(diff_report)
        else:
            suggestions = []
    source_target = (
        (run_report or {}).get("source_target")
        or (verify_report or {}).get("source_target")
        or (diff_report or {}).get("source_target")
    )
    enriched: list[dict[str, Any]] = []
    for fallback_index, suggestion in enumerate(suggestions, start=1):
        if not isinstance(suggestion, dict):
            continue
        routing_hint = _source_table_routing_hint(suggestion)
        enriched.append(
            {
                "index": suggestion.get("index") or fallback_index,
                "delta_hash": suggestion.get("delta_hash"),
                "status": "operator_review_required",
                "external_write": False,
                "routing_hint": routing_hint,
                "operator_locator": _operator_locator(suggestion),
                "old_text": suggestion.get("old_text"),
                "new_text": suggestion.get("new_text"),
                "old_normalized": suggestion.get("old_normalized"),
                "new_normalized": suggestion.get("new_normalized"),
                "source_ref": suggestion.get("source_ref") or {},
                "source_evidence": suggestion.get("source_evidence") or {},
                "semantic_review": suggestion.get("semantic_review") or {},
                "reason": suggestion.get("reason") or "data-like review delta is report-only",
            }
        )
    route_counts = _counter_dict([str(item["routing_hint"]["route_key"]) for item in enriched])
    candidate_tables = sorted(
        {
            table
            for item in enriched
            for table in item.get("routing_hint", {}).get("candidate_source_tables", [])
            if table
        }
    )
    run_id = (
        (run_report or {}).get("diff_report", {}).get("run_id")
        or (verify_report or {}).get("diff_report", {}).get("run_id")
        or (diff_report or {}).get("run_id")
    )
    return {
        "schema_version": SOURCE_TABLE_SUGGESTIONS_SCHEMA_VERSION,
        "result": "HAS_SUGGESTIONS" if enriched else "NO_SUGGESTIONS",
        "run_id": run_id,
        "source_target": source_target,
        "metadata": {
            "generated_at": _utc_now(),
            "git_ref": _git_ref(),
            "command": shlex.join(command or []),
        },
        "summary": {
            "total_suggestions": len(enriched),
            "route_keys": route_counts,
            "candidate_source_tables": candidate_tables,
            "external_write": False,
        },
        "operator_contract": {
            "purpose": "Review report-only data-like deltas before updating Feishu phase2 source tables.",
            "external_write": False,
            "next_steps": [
                "Update the appropriate Feishu phase2 source row manually.",
                "Run sync-data for the affected source table.",
                "Run sync-review or the target build/check flow to regenerate the review package.",
            ],
        },
        "suggestions": enriched,
    }

def write_source_table_suggestions_report(report: dict[str, Any], out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "cloud_doc_backport_source_table_suggestions.json"
    markdown_path = out_dir / "cloud_doc_backport_source_table_suggestions.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(markdown_source_table_suggestions_report(report), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}

def _source_table_suggestions_from_diff(diff_report: dict[str, Any]) -> list[dict[str, Any]]:
    suggestions: list[dict[str, Any]] = []
    for index, delta in enumerate(diff_report.get("deltas") or [], start=1):
        if not isinstance(delta, dict) or delta.get("route_class") != "source_table_suggestion":
            continue
        suggestions.append(
            {
                "index": index,
                "delta_hash": delta.get("delta_hash"),
                "change_type": delta.get("change_type"),
                "route_class": delta.get("route_class"),
                "old_text": delta.get("old_text"),
                "new_text": delta.get("new_text"),
                "old_normalized": delta.get("old_normalized"),
                "new_normalized": delta.get("new_normalized"),
                "location": delta.get("location") or {},
                "source_ref": delta.get("source_ref") or {},
                "source_evidence": delta.get("source_evidence") or {},
                "semantic_review": delta.get("semantic_review") or {},
                "status": "reported",
                "reason": "data-like review delta is report-only",
            }
        )
    return suggestions

def _template_sync_proposals_from_diff(diff_report: dict[str, Any]) -> list[dict[str, Any]]:
    """F4: report-only proposals for Class T (shared-across-family) review deltas."""
    proposals: list[dict[str, Any]] = []
    for index, delta in enumerate(diff_report.get("deltas") or [], start=1):
        if not isinstance(delta, dict):
            continue
        family_scope = delta.get("family_scope")
        if not (isinstance(family_scope, dict) and family_scope.get("shared")):
            continue
        proposals.append(
            {
                "index": index,
                "delta_hash": delta.get("delta_hash"),
                "change_type": delta.get("change_type"),
                "old_text": delta.get("old_text"),
                "new_text": delta.get("new_text"),
                "location": delta.get("location") or {},
                "family_scope": family_scope,
                "target_templates": list(family_scope.get("targets") or []),
                "post_apply": "rebuild + sync-review the affected family targets, then verify (R7 rebuild+rediff gate)",
                "status": "reported",
                "reason": "span identical across the family - apply as a shared template change after review (R5)",
            }
        )
    return proposals

def build_template_sync_proposal_report(*, diff_report: dict[str, Any], command: list[str]) -> dict[str, Any]:
    proposals = _template_sync_proposals_from_diff(diff_report)
    return {
        "schema_version": TEMPLATE_SYNC_PROPOSAL_SCHEMA_VERSION,
        "run_id": diff_report.get("run_id"),
        "external_write": False,
        "summary": {"proposals": len(proposals)},
        "proposals": proposals,
        "metadata": {
            "generated_at": _utc_now(),
            "git_ref": _git_ref(),
            "command": shlex.join(command),
        },
    }

def write_template_sync_proposal_report(report: dict[str, Any], out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "cloud_doc_backport_template_sync_proposal.json"
    markdown_path = out_dir / "cloud_doc_backport_template_sync_proposal.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(markdown_template_sync_proposal_report(report), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}

def _repo_text_changes_from_diff(diff_report: dict[str, Any]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for index, delta in enumerate(diff_report.get("deltas") or [], start=1):
        if not isinstance(delta, dict) or delta.get("route_class") != "repo_review_text":
            continue
        changes.append(
            {
                "index": index,
                "delta_hash": delta.get("delta_hash"),
                "change_type": delta.get("change_type"),
                "route_class": delta.get("route_class"),
                "old_text": delta.get("old_text"),
                "new_text": delta.get("new_text"),
                "location": delta.get("location") or {},
                "source_evidence": delta.get("source_evidence") or {},
                "status": "repo_write_candidate",
            }
        )
    return changes

def _display_report_paths(paths: dict[str, Path]) -> dict[str, str]:
    return {key: _display_path(path).as_posix() for key, path in sorted(paths.items())}

def build_review_run_report(
    diff_report: dict[str, Any],
    *,
    apply_report: dict[str, Any] | None,
    verify_report: dict[str, Any] | None,
    write: bool,
    output_paths: dict[str, Path],
    command: list[str] | None = None,
) -> dict[str, Any]:
    diff_summary = diff_report.get("summary") or {}
    apply_summary = apply_report.get("summary") if apply_report else {}
    verify_summary = verify_report.get("summary") if verify_report else {}
    changed = bool(apply_summary.get("changed")) if isinstance(apply_summary, dict) else False
    verify_result = verify_report.get("result") if verify_report else None
    rebuild_rediff = verify_report.get("rebuild_rediff") if verify_report else None
    rebuild_ok = rebuild_rediff.get("passed", True) if isinstance(rebuild_rediff, dict) else True
    if diff_report.get("result") == "NO_DIFF":
        result = "NO_DIFF"
    elif not write:
        result = "DRY_RUN"
    elif verify_result == "PASS" and rebuild_ok:
        # F5: a write run is PR_READY only when the rebuild+rediff gate confirms the
        # edit reproduces the accepted doc and changes nothing else.
        result = "PR_READY" if changed else "PASS"
    else:
        result = "FAIL"

    if verify_report:
        source_table_suggestions = list(verify_report.get("source_table_suggestions") or [])
    else:
        source_table_suggestions = _source_table_suggestions_from_diff(diff_report)
    review_source_changes = _repo_text_changes_from_diff(diff_report)

    next_actions = {
        "NO_DIFF": ["No source change is needed."],
        "DRY_RUN": ["Review the apply report, then rerun with --write to patch the review source."],
        "PR_READY": ["Open a PR with the changed docs/_review source and attach the run report."],
        "PASS": ["No review-source PR is needed; route source-table suggestions deliberately if any exist."],
        "FAIL": ["Inspect the verify report before opening a PR."],
    }[result]

    return {
        "schema_version": RUN_SCHEMA_VERSION,
        "result": result,
        "mode": "write" if write else "dry-run",
        "source_target": diff_report.get("source_target"),
        "section_selection": diff_report.get("section_selection") or {},
        "diff_report": {
            "run_id": diff_report.get("run_id"),
            "result": diff_report.get("result"),
            "schema_version": diff_report.get("schema_version"),
        },
        "apply_report": {
            "mode": apply_report.get("mode"),
            "schema_version": apply_report.get("schema_version"),
        }
        if apply_report
        else None,
        "verify_report": {
            "result": verify_report.get("result"),
            "schema_version": verify_report.get("schema_version"),
        }
        if verify_report
        else None,
        "metadata": {
            "generated_at": _utc_now(),
            "git_ref": _git_ref(),
            "command": shlex.join(command or []),
        },
        "summary": {
            "total_deltas": int(diff_summary.get("total_deltas") or 0),
            "route_classes": dict(diff_summary.get("route_classes") or {}),
            "apply_statuses": dict(apply_summary.get("statuses") or {}) if isinstance(apply_summary, dict) else {},
            "verify_categories": dict(verify_summary.get("categories") or {})
            if isinstance(verify_summary, dict)
            else {},
            "verify_failing_categories": dict(verify_summary.get("failing_categories") or {})
            if isinstance(verify_summary, dict)
            else {},
            "changed": changed,
            "pr_ready": result == "PR_READY",
            "review_source_changes": len(review_source_changes),
            "source_table_suggestions": len(source_table_suggestions),
        },
        "reports": _display_report_paths(output_paths),
        "next_actions": next_actions,
        "review_source_changes": review_source_changes,
        "source_table_suggestions": source_table_suggestions,
    }

def write_review_run_report(report: dict[str, Any], out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "cloud_doc_backport_run.json"
    markdown_path = out_dir / "cloud_doc_backport_run.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(markdown_review_run_report(report), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}
