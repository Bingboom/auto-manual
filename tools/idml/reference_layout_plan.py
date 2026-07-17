"""Load and validate an explicitly approved PDF-to-IDML page contract."""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

from tools.manual_ir import ManualIR
from tools.utils.path_utils import PathSegments, Paths

from .latex_page_plan import SCHEMA_VERSION as LEGACY_PLAN_SCHEMA_VERSION


SCHEMA_VERSION = "approved-reference-layout-plan/v1"
REGISTRY_SCHEMA_VERSION = "approved-reference-layout-registry/v1"
_DIGEST = re.compile(r"[0-9a-f]{64}")
_RFC3339 = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})")


class ReferenceLayoutPlanError(ValueError):
    """An activated approved layout contract is missing, stale, or invalid."""


def _languages(ir: ManualIR) -> list[str]:
    languages: list[str] = []
    for page in ir.pages:
        language = page.language
        if language in {"", "cover", "toc"} or language in languages:
            continue
        languages.append(language)
    return languages


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReferenceLayoutPlanError(f"{label} does not exist: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ReferenceLayoutPlanError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ReferenceLayoutPlanError(f"{label} must contain a JSON object: {path}")
    return payload


def _as_positive_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value if value > 0 else None


def _valid_digest(value: Any) -> bool:
    return isinstance(value, str) and _DIGEST.fullmatch(value) is not None


def validate_approved_reference_plan(
    payload: dict[str, Any],
    ir: ManualIR,
) -> list[str]:
    """Return every reason an approved contract cannot govern this IR."""
    issues: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        issues.append(f"schema_version must be {SCHEMA_VERSION}")

    target = payload.get("target")
    if not isinstance(target, dict):
        issues.append("target must be an object")
        target = {}
    expected_target = {
        "model": ir.model,
        "region": ir.region,
        "languages": _languages(ir),
    }
    for field, expected in expected_target.items():
        if target.get(field) != expected:
            issues.append(f"target.{field} must be {expected!r}")

    source_identity = payload.get("source_identity")
    if not isinstance(source_identity, dict):
        issues.append("source_identity must be an object")
        source_identity = {}
    expected_identity = {
        "manual_ir_schema_version": ir.schema_version,
        "manual_content_sha256": ir.content_sha256,
        "snapshot_sha256": ir.snapshot_sha256,
        "style_contract_sha256": ir.style_contract_sha256,
        "layout_params_sha256": ir.layout_params_sha256,
    }
    for field, expected in expected_identity.items():
        if source_identity.get(field) != expected:
            issues.append(f"source_identity.{field} does not match the current manual IR")
    for field in (
        "manual_content_sha256", "snapshot_sha256",
        "style_contract_sha256", "layout_params_sha256",
    ):
        if not _valid_digest(source_identity.get(field)):
            issues.append(f"source_identity.{field} must be a lowercase SHA-256")

    reference = payload.get("reference_pdf")
    if not isinstance(reference, dict):
        issues.append("reference_pdf must be an object")
        reference = {}
    if not _valid_digest(reference.get("sha256")):
        issues.append("reference_pdf.sha256 must be a lowercase SHA-256")
    physical_page_count = _as_positive_int(reference.get("page_count"))
    if physical_page_count is None:
        issues.append("reference_pdf.page_count must be a positive integer")
        physical_page_count = 0
    if _as_positive_int(reference.get("byte_size")) is None:
        issues.append("reference_pdf.byte_size must be a positive integer")
    page_size = reference.get("page_size_pt")
    if not isinstance(page_size, dict) or any(
        not isinstance(page_size.get(axis), (int, float)) or page_size[axis] <= 0
        for axis in ("width", "height")
    ):
        issues.append("reference_pdf.page_size_pt must contain positive width and height")
    tolerance = reference.get("page_size_tolerance_pt")
    if not isinstance(tolerance, (int, float)) or tolerance <= 0:
        issues.append("reference_pdf.page_size_tolerance_pt must be positive")
    for field in ("logical_id", "file_name", "pdfx", "output_intent", "output_condition"):
        if not isinstance(reference.get(field), str) or not reference[field].strip():
            issues.append(f"reference_pdf.{field} must be a non-empty string")

    approval = payload.get("approval")
    if not isinstance(approval, dict):
        issues.append("approval must be an object")
        approval = {}
    if approval.get("status") != "approved":
        issues.append("approval.status must be approved")
    if not isinstance(approval.get("approved_by"), str) or not approval["approved_by"].strip():
        issues.append("approval.approved_by must be non-empty")
    if not isinstance(approval.get("method"), str) or not approval["method"].strip():
        issues.append("approval.method must be non-empty")
    approved_at = approval.get("approved_at")
    if not isinstance(approved_at, str) or _RFC3339.fullmatch(approved_at) is None:
        issues.append("approval.approved_at must be an RFC3339 timestamp")

    render_contract = payload.get("render_contract")
    if not isinstance(render_contract, dict):
        issues.append("render_contract must be an object")
        render_contract = {}
    for field in ("dpi", "raster_width_px", "raster_height_px"):
        if _as_positive_int(render_contract.get(field)) is None:
            issues.append(f"render_contract.{field} must be a positive integer")
    if not _valid_digest(render_contract.get("display_icc_sha256")):
        issues.append("render_contract.display_icc_sha256 must be a lowercase SHA-256")
    for field in ("gaussian_blur_px",):
        value = render_contract.get(field)
        if not isinstance(value, (int, float)) or value < 0:
            issues.append(f"render_contract.{field} must be non-negative")
    for field in ("max_rgb_mad", "max_changed_pixel_ratio"):
        value = render_contract.get(field)
        if not isinstance(value, (int, float)) or not 0 <= value <= 1:
            issues.append(f"render_contract.{field} must be in 0..1")
    threshold = render_contract.get("changed_channel_threshold")
    if _as_positive_int(threshold) is None or int(threshold) > 255:
        issues.append("render_contract.changed_channel_threshold must be in 1..255")
    dpi = _as_positive_int(render_contract.get("dpi"))
    raster_width = _as_positive_int(render_contract.get("raster_width_px"))
    raster_height = _as_positive_int(render_contract.get("raster_height_px"))
    if (
        dpi is not None
        and raster_width is not None
        and raster_height is not None
        and isinstance(page_size, dict)
        and all(isinstance(page_size.get(axis), (int, float)) for axis in ("width", "height"))
    ):
        expected_raster = (
            math.ceil(float(page_size["width"]) * dpi / 72),
            math.ceil(float(page_size["height"]) * dpi / 72),
        )
        if (raster_width, raster_height) != expected_raster:
            issues.append(
                "render_contract raster dimensions must equal ceil(page_size_pt*dpi/72) "
                f"({expected_raster[0]} x {expected_raster[1]})"
            )

    idml_contract = payload.get("idml_contract")
    if not isinstance(idml_contract, dict):
        issues.append("idml_contract must be an object")
    else:
        forbidden_links = idml_contract.get("forbidden_visible_whole_page_links")
        if not isinstance(forbidden_links, list) or not forbidden_links:
            issues.append(
                "idml_contract.forbidden_visible_whole_page_links "
                "must be a non-empty list"
            )
        elif any(
            not isinstance(item, str)
            or not item.strip()
            or Path(item).name != item
            for item in forbidden_links
        ):
            issues.append(
                "idml_contract.forbidden_visible_whole_page_links "
                "must contain file names only"
            )

    plan_pages = payload.get("pages")
    if not isinstance(plan_pages, list):
        issues.append("pages must be a list")
        return issues
    ir_pages = list(ir.pages)
    if len(plan_pages) != len(ir_pages):
        issues.append(f"pages must contain exactly {len(ir_pages)} entries")

    expected_refs = [page.source_ref for page in ir_pages]
    actual_refs: list[str] = []
    seen_refs: set[str] = set()
    compositions: dict[str, tuple[int, int]] = {}
    split_rules: list[tuple[str, str, str]] = []
    previous_start = 0
    for index, entry in enumerate(plan_pages):
        if not isinstance(entry, dict):
            issues.append(f"pages[{index}] must be an object")
            continue
        source_ref = entry.get("source_ref")
        if not isinstance(source_ref, str):
            issues.append(f"pages[{index}].source_ref must be a string")
            continue
        actual_refs.append(source_ref)
        if source_ref in seen_refs:
            issues.append(f"duplicate source_ref: {source_ref}")
        seen_refs.add(source_ref)
        if index < len(ir_pages):
            source_page = ir_pages[index]
            if source_ref != source_page.source_ref:
                issues.append(f"pages[{index}].source_ref is out of order")
            if entry.get("source_sha256") != source_page.source_sha256:
                issues.append(f"{source_ref}: source_sha256 does not match")
            if entry.get("language") != source_page.language:
                issues.append(f"{source_ref}: language does not match")
        if not _valid_digest(entry.get("source_sha256")):
            issues.append(f"{source_ref}: source_sha256 must be a lowercase SHA-256")
        composition_id = entry.get("composition_id")
        if not isinstance(composition_id, str) or not composition_id.strip():
            issues.append(f"{source_ref}: composition_id must be non-empty")
            continue
        start_page = _as_positive_int(entry.get("start_page"))
        page_count = _as_positive_int(entry.get("page_count"))
        if start_page is None or page_count is None:
            issues.append(f"{source_ref}: start_page and page_count must be positive integers")
            continue
        if start_page < previous_start:
            issues.append(f"{source_ref}: start_page is not monotonic")
        previous_start = start_page
        if physical_page_count and start_page + page_count - 1 > physical_page_count:
            issues.append(f"{source_ref}: composition exceeds the reference page count")
        extent = (start_page, page_count)
        previous_extent = compositions.setdefault(composition_id, extent)
        if previous_extent != extent:
            issues.append(f"composition {composition_id} has inconsistent page ranges")
        flow_split = entry.get("flow_split")
        if flow_split is not None:
            if not isinstance(flow_split, dict):
                issues.append(f"{source_ref}: flow_split must be an object")
                continue
            at_kind = flow_split.get("at_kind")
            occurrence = _as_positive_int(flow_split.get("occurrence"))
            tail_composition = flow_split.get("tail_composition_id")
            if not isinstance(at_kind, str) or not at_kind:
                issues.append(f"{source_ref}: flow_split.at_kind must be non-empty")
            if occurrence is None:
                issues.append(f"{source_ref}: flow_split.occurrence must be positive")
            if not isinstance(tail_composition, str) or not tail_composition:
                issues.append(
                    f"{source_ref}: flow_split.tail_composition_id must be non-empty"
                )
            if index < len(ir_pages) and isinstance(at_kind, str) and occurrence:
                available = sum(
                    block.kind == at_kind for block in ir_pages[index].blocks
                )
                if available < occurrence:
                    issues.append(
                        f"{source_ref}: flow_split cannot find {at_kind} "
                        f"occurrence {occurrence}"
                    )
            if isinstance(tail_composition, str) and tail_composition:
                split_rules.append((source_ref, composition_id, tail_composition))

    if actual_refs != expected_refs:
        missing = [ref for ref in expected_refs if ref not in seen_refs]
        extra = [ref for ref in seen_refs if ref not in set(expected_refs)]
        if missing:
            issues.append("missing source_ref entries: " + ", ".join(missing))
        if extra:
            issues.append("unexpected source_ref entries: " + ", ".join(sorted(extra)))

    cursor = 1
    for composition_id, (start_page, page_count) in sorted(
        compositions.items(), key=lambda item: (item[1][0], item[0]),
    ):
        if start_page > cursor:
            issues.append(f"composition {composition_id} leaves a gap before page {start_page}")
        elif start_page < cursor:
            issues.append(f"composition {composition_id} overlaps page {start_page}")
        cursor = max(cursor, start_page + page_count)
    if physical_page_count and cursor != physical_page_count + 1:
        issues.append(
            f"composition coverage ends at page {cursor - 1}, expected {physical_page_count}"
        )
    for source_ref, composition_id, tail_composition in split_rules:
        if tail_composition not in compositions:
            issues.append(f"{source_ref}: flow_split target composition does not exist")
        elif compositions[tail_composition][0] <= compositions[composition_id][0]:
            issues.append(f"{source_ref}: flow_split target must start on a later page")
    return issues


def _canonical_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def normalize_approved_reference_plan(
    payload: dict[str, Any],
    ir: ManualIR,
    *,
    source_path: Path,
) -> dict[str, Any]:
    """Adapt the approved contract to the established page-plan interface."""
    issues = validate_approved_reference_plan(payload, ir)
    if issues:
        raise ReferenceLayoutPlanError("; ".join(issues))
    reference = payload["reference_pdf"]
    pages = []
    for source_page, approved in zip(ir.pages, payload["pages"], strict=True):
        pages.append({
            "page_id": source_page.page_id,
            "source_ref": source_page.source_ref,
            "source_path": source_page.source_path,
            "source_sha256": source_page.source_sha256,
            "language": source_page.language,
            "latex_start_page": approved["start_page"],
            "matched_anchor": f"approved:{approved['composition_id']}",
            "candidate_count": 0,
            "composition_id": approved["composition_id"],
            "planned_page_count": approved["page_count"],
            "flow_split": approved.get("flow_split"),
        })
    return {
        "schema_version": LEGACY_PLAN_SCHEMA_VERSION,
        "plan_source": "approved-reference",
        "approved_plan_schema_version": SCHEMA_VERSION,
        "approved_plan_sha256": _canonical_sha256(payload),
        "approved_plan_path": source_path.as_posix(),
        "manual_content_sha256": ir.content_sha256,
        "snapshot_sha256": ir.snapshot_sha256,
        "style_contract_sha256": ir.style_contract_sha256,
        "layout_params_sha256": ir.layout_params_sha256,
        "reference_pdf": reference["file_name"],
        "reference_pdf_sha256": reference["sha256"],
        "reference_pdf_byte_size": reference["byte_size"],
        "reference_page_size_pt": reference["page_size_pt"],
        "reference_page_size_tolerance_pt": reference["page_size_tolerance_pt"],
        "physical_page_count": reference["page_count"],
        "source_page_count": len(pages),
        "matched_source_pages": len(pages),
        "unmatched_source_pages": 0,
        "match_rate": 1.0,
        "virtual_pages": [
            {"kind": "toc", "physical_page": page["latex_start_page"]}
            for page in pages if page["language"] == "toc"
        ],
        "pages": pages,
        "render_contract": payload["render_contract"],
        "approval": payload["approval"],
        "idml_contract": payload.get("idml_contract"),
        "approved_contract": payload,
    }


def load_approved_reference_plan(
    *,
    root: Path,
    ir: ManualIR,
) -> dict[str, Any] | None:
    """Return the matching approved plan, or None for an unregistered target.

    Registry presence alone does not activate a target.  Once one exact target
    entry matches, however, a missing or invalid contract is a hard failure and
    the caller must not fall back to fuzzy LaTeX mapping.
    """
    registry_path = (
        Paths(root=root).renderer_contracts_dir
        / PathSegments.REFERENCE_LAYOUT_REGISTRY_JSON
    )
    if not registry_path.is_file():
        return None
    registry = _read_json(registry_path, "approved reference layout registry")
    if registry.get("schema_version") != REGISTRY_SCHEMA_VERSION:
        raise ReferenceLayoutPlanError(
            f"registry schema_version must be {REGISTRY_SCHEMA_VERSION}"
        )
    entries = registry.get("plans")
    if not isinstance(entries, list):
        raise ReferenceLayoutPlanError("registry plans must be a list")
    expected_target = {
        "model": ir.model,
        "region": ir.region,
        "languages": _languages(ir),
    }
    matches = [
        entry for entry in entries
        if isinstance(entry, dict) and entry.get("target") == expected_target
    ]
    if not matches:
        return None
    if len(matches) != 1:
        raise ReferenceLayoutPlanError(
            f"registry has {len(matches)} matching entries for {ir.model}/{ir.region}"
        )
    raw_path = matches[0].get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ReferenceLayoutPlanError("matching registry entry path must be non-empty")
    relative_path = Path(raw_path)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ReferenceLayoutPlanError("approved plan path must stay repo-relative")
    root = root.resolve()
    plan_path = (root / relative_path).resolve()
    if not plan_path.is_relative_to(root):
        raise ReferenceLayoutPlanError("approved plan path escapes the repository")
    payload = _read_json(plan_path, "approved reference layout plan")
    return normalize_approved_reference_plan(payload, ir, source_path=relative_path)
