"""Load a candidate target assembly without claiming visual approval.

This contract contains only target composition data.  It is selected explicitly
by a family config for local validation, never discovered through the approved
reference-layout registry.  Promotion to an approved contract remains a
separate, operator-gated step after native InDesign and PDF review.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.manual_ir import ManualIR
from tools.page_plan import build_renderer_page_plan

from .composition_plan import (
    CompositionPlanError,
    build_composition_plan,
)
from .page_roles import PageRole, classify_page_role


SCHEMA_VERSION = "target-idml-assembly-plan/v1"


class TargetAssemblyPlanError(ValueError):
    """A configured candidate target assembly is invalid for the current IR."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise TargetAssemblyPlanError(
            f"target assembly plan does not exist: {path}"
        ) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise TargetAssemblyPlanError(
            f"cannot read target assembly plan {path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise TargetAssemblyPlanError("target assembly plan must contain an object")
    return payload


def _languages(ir: ManualIR) -> list[str]:
    languages: list[str] = []
    for page in ir.pages:
        if page.language in {"", "cover", "toc"} or page.language in languages:
            continue
        languages.append(page.language)
    return languages


def _positive_int(value: object, *, label: str) -> int:
    if isinstance(value, bool):
        raise TargetAssemblyPlanError(f"{label} must be a positive integer")
    try:
        result = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise TargetAssemblyPlanError(f"{label} must be a positive integer") from exc
    if result <= 0:
        raise TargetAssemblyPlanError(f"{label} must be a positive integer")
    return result


def _validate_flow_splits(
    pages: list[dict[str, Any]],
    ir: ManualIR,
) -> list[str]:
    issues: list[str] = []
    positions = {
        str(page.get("composition_id")): int(page.get("start_page") or 0)
        for page in pages
    }
    for page, source_page in zip(pages, ir.pages, strict=True):
        rule = page.get("flow_split")
        if rule is None:
            continue
        source_ref = source_page.source_ref
        if not isinstance(rule, dict):
            issues.append(f"{source_ref}: flow_split must be an object")
            continue
        at_kind = rule.get("at_kind")
        occurrence = rule.get("occurrence")
        tail = rule.get("tail_composition_id")
        if not isinstance(at_kind, str) or not at_kind:
            issues.append(f"{source_ref}: flow_split.at_kind must be non-empty")
            continue
        try:
            occurrence = _positive_int(
                occurrence,
                label=f"{source_ref}.flow_split.occurrence",
            )
        except TargetAssemblyPlanError as exc:
            issues.append(str(exc))
            continue
        if not isinstance(tail, str) or not tail:
            issues.append(
                f"{source_ref}: flow_split.tail_composition_id must be non-empty"
            )
            continue
        available = sum(block.kind == at_kind for block in source_page.blocks)
        if available < occurrence:
            issues.append(
                f"{source_ref}: flow_split cannot find {at_kind} occurrence "
                f"{occurrence}"
            )
        current = str(page.get("composition_id") or "")
        if tail not in positions:
            issues.append(f"{source_ref}: flow_split target does not exist: {tail}")
        elif positions[tail] <= positions.get(current, 0):
            issues.append(f"{source_ref}: flow_split target must start later")
    return issues


def normalize_target_assembly_plan(
    payload: dict[str, Any],
    ir: ManualIR,
    *,
    source_path: Path,
) -> dict[str, Any]:
    """Validate and adapt candidate target data to the page-plan interface."""
    issues: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        issues.append(f"schema_version must be {SCHEMA_VERSION}")
    if payload.get("status") != "candidate":
        issues.append("status must be candidate")
    if payload.get("production_eligible") is not False:
        issues.append("production_eligible must be false before visual approval")
    target = payload.get("target")
    expected_target = {
        "model": ir.model,
        "region": ir.region,
        "languages": _languages(ir),
    }
    if target != expected_target:
        issues.append(
            f"target must match current Manual IR: expected={expected_target!r}"
        )
    physical_page_count = _positive_int(
        payload.get("physical_page_count"),
        label="physical_page_count",
    )
    reference = payload.get("reference_pdf")
    if not isinstance(reference, dict):
        issues.append("reference_pdf must be an object")
        reference = {}
    if reference.get("page_count") != physical_page_count:
        issues.append("reference_pdf.page_count must equal physical_page_count")

    raw_pages = payload.get("pages")
    if not isinstance(raw_pages, list):
        raise TargetAssemblyPlanError("pages must be a list")
    if len(raw_pages) != len(ir.pages):
        issues.append(f"pages must contain exactly {len(ir.pages)} entries")

    normalized_pages: list[dict[str, Any]] = []
    for index, source_page in enumerate(ir.pages):
        raw = raw_pages[index] if index < len(raw_pages) else {}
        if not isinstance(raw, dict):
            issues.append(f"pages[{index}] must be an object")
            raw = {}
        source_ref = raw.get("source_ref")
        if source_ref != source_page.source_ref:
            issues.append(f"pages[{index}].source_ref is out of order")
        if raw.get("language") != source_page.language:
            issues.append(f"{source_page.source_ref}: language does not match")
        role = classify_page_role(Path(source_page.source_ref))
        if role is PageRole.UNCLASSIFIED_PROSE:
            issues.append(
                f"{source_page.source_ref}: candidate assembly forbids "
                "unclassified prose"
            )
        if raw.get("page_role") != role.value:
            issues.append(f"{source_page.source_ref}: page_role does not match")
        normalized = {
            "page_id": source_page.page_id,
            "source_ref": source_page.source_ref,
            "source_path": source_page.source_path,
            "source_sha256": source_page.source_sha256,
            "language": source_page.language,
            "page_role": role.value,
            "latex_start_page": raw.get("start_page"),
            "matched_anchor": f"assembly:{raw.get('composition_id')}",
            "candidate_count": 0,
            "composition_id": raw.get("composition_id"),
            "composition_type": raw.get("composition_type"),
            "planned_page_count": raw.get("page_count"),
            "flow_split": raw.get("flow_split"),
        }
        normalized_pages.append(normalized)

    issues.extend(_validate_flow_splits(raw_pages, ir))
    normalized: dict[str, Any] = {
        "schema_version": "latex-page-plan/v1",
        "plan_source": "target-assembly",
        "target_assembly_schema_version": payload.get("schema_version"),
        "target_assembly_plan_path": source_path.as_posix(),
        "target_assembly_status": payload.get("status"),
        "manual_content_sha256": ir.content_sha256,
        "snapshot_sha256": ir.snapshot_sha256,
        "style_contract_sha256": ir.style_contract_sha256,
        "layout_params_sha256": ir.layout_params_sha256,
        "reference_pdf": reference.get("file_name"),
        "reference_pdf_sha256": reference.get("sha256"),
        "reference_pdf_byte_size": reference.get("byte_size"),
        "reference_page_size_pt": reference.get("page_size_pt"),
        "physical_page_count": physical_page_count,
        "source_page_count": len(normalized_pages),
        "matched_source_pages": len(normalized_pages),
        "unmatched_source_pages": 0,
        "match_rate": 1.0,
        "placed_source_pages": 0,
        "virtual_pages": [
            {"kind": "toc", "physical_page": page["latex_start_page"]}
            for page in normalized_pages
            if page["page_role"] == PageRole.TOC.value
        ],
        "pages": normalized_pages,
        "target_assembly_plan": payload,
    }
    try:
        composition_plan = build_composition_plan(normalized)
        normalized["renderer_page_plan"] = build_renderer_page_plan(
            normalized
        ).to_dict()
    except CompositionPlanError as exc:
        issues.append(str(exc))
        composition_plan = None
    if composition_plan is not None:
        normalized["composition_count"] = len(composition_plan.compositions)
    if issues:
        raise TargetAssemblyPlanError("; ".join(issues))
    return normalized


def load_target_assembly_plan(path: Path, ir: ManualIR) -> dict[str, Any]:
    return normalize_target_assembly_plan(
        _read_json(path),
        ir,
        source_path=path,
    )


__all__ = (
    "SCHEMA_VERSION",
    "TargetAssemblyPlanError",
    "load_target_assembly_plan",
    "normalize_target_assembly_plan",
)
