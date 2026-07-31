"""Build a review-only draft from an existing reference-layout contract.

The scaffold refreshes the identity fields and per-source digests from a
validated Manual IR while preserving the seed contract's physical composition
map.  It deliberately produces a draft, never edits the registry, and never
returns a production-eligible contract.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from tools.manual_ir import ManualIR
from tools.render_contract import LAYOUT_PARAMS_HASH_ALGORITHM

from .reference_layout_plan import (
    ReferenceLayoutPlanError,
    SCHEMA_VERSION,
    validate_approved_reference_plan,
)


SCAFFOLD_SCHEMA_VERSION = "reference-layout-scaffold/v1"


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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _composition_map(payload: dict[str, Any]) -> tuple[tuple[Any, ...], ...]:
    pages = payload.get("pages")
    if not isinstance(pages, list):
        raise ReferenceLayoutPlanError("reference layout seed pages must be a list")
    result: list[tuple[Any, ...]] = []
    for index, page in enumerate(pages):
        if not isinstance(page, dict):
            raise ReferenceLayoutPlanError(f"reference layout seed pages[{index}] must be an object")
        result.append((
            page.get("source_ref"),
            page.get("composition_id"),
            page.get("start_page"),
            page.get("page_count"),
            json.dumps(
                page.get("flow_split"),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ) if page.get("flow_split") is not None else None,
        ))
    return tuple(result)


def _languages(ir: ManualIR) -> list[str]:
    languages: list[str] = []
    for page in ir.pages:
        if page.language in {"", "cover", "toc"} or page.language in languages:
            continue
        languages.append(page.language)
    return languages


def _validate_seed_shape(seed: dict[str, Any], ir: ManualIR) -> None:
    if seed.get("schema_version") != SCHEMA_VERSION:
        raise ReferenceLayoutPlanError(
            f"reference layout seed schema_version must be {SCHEMA_VERSION}"
        )
    target = seed.get("target")
    expected_target = {
        "model": ir.model,
        "region": ir.region,
        "languages": _languages(ir),
    }
    if target != expected_target:
        raise ReferenceLayoutPlanError(
            "reference layout scaffold requires an exact seed target; "
            f"seed={target!r} current={expected_target!r}"
        )
    seed_pages = seed.get("pages")
    if not isinstance(seed_pages, list):
        raise ReferenceLayoutPlanError("reference layout seed pages must be a list")
    current_refs = tuple(page.source_ref for page in ir.pages)
    seed_refs = tuple(
        page.get("source_ref") if isinstance(page, dict) else None
        for page in seed_pages
    )
    if seed_refs != current_refs:
        raise ReferenceLayoutPlanError(
            "reference layout scaffold requires unchanged source_ref order; "
            f"seed={list(seed_refs)!r} current={list(current_refs)!r}"
        )
    if len(seed_pages) != len(ir.pages):
        raise ReferenceLayoutPlanError(
            "reference layout scaffold requires one seed page per Manual IR page"
        )
    for index, (seed_page, ir_page) in enumerate(zip(seed_pages, ir.pages, strict=True)):
        if not isinstance(seed_page, dict):
            raise ReferenceLayoutPlanError(f"reference layout seed pages[{index}] must be an object")
        if seed_page.get("language") != ir_page.language:
            raise ReferenceLayoutPlanError(
                "reference layout scaffold cannot change page language for "
                f"{ir_page.source_ref}: seed={seed_page.get('language')!r} "
                f"current={ir_page.language!r}"
            )


def _draft_candidate(seed: dict[str, Any], ir: ManualIR, *, seed_path: Path) -> dict[str, Any]:
    if ir.schema_version != "manual-ir/v1":
        raise ReferenceLayoutPlanError(
            f"reference layout scaffold requires manual-ir/v1; got {ir.schema_version!r}"
        )
    if ir.metadata.get("layout_params_hash_algorithm") != LAYOUT_PARAMS_HASH_ALGORITHM:
        raise ReferenceLayoutPlanError(
            "reference layout scaffold requires Manual IR layout hash algorithm "
            f"{LAYOUT_PARAMS_HASH_ALGORITHM!r}"
        )
    if not isinstance(ir.snapshot_sha256, str) or len(ir.snapshot_sha256) != 64:
        raise ReferenceLayoutPlanError(
            "reference layout scaffold requires a frozen snapshot_sha256"
        )

    _validate_seed_shape(seed, ir)
    original_map = _composition_map(seed)
    candidate = deepcopy(seed)
    candidate["source_identity"] = {
        "manual_ir_schema_version": ir.schema_version,
        "manual_content_sha256": ir.content_sha256,
        "snapshot_sha256": ir.snapshot_sha256,
        "style_contract_sha256": ir.style_contract_sha256,
        "layout_params_sha256": ir.layout_params_sha256,
    }
    for seed_page, ir_page in zip(candidate["pages"], ir.pages, strict=True):
        seed_page["source_sha256"] = ir_page.source_sha256

    # Validate the full physical plan before changing its approval state. This
    # reuses the production validator but does not activate the candidate.
    validation_payload = deepcopy(candidate)
    validation_payload["approval"] = {
        "status": "approved",
        "approved_by": "scaffold-validator",
        "approved_at": "2026-01-01T00:00:00Z",
        "method": "scaffold-only validation; not an approval",
    }
    issues = validate_approved_reference_plan(validation_payload, ir)
    if issues:
        raise ReferenceLayoutPlanError(
            "reference layout scaffold seed is not a valid physical contract: "
            + "; ".join(issues)
        )
    if _composition_map(candidate) != original_map:
        raise ReferenceLayoutPlanError(
            "reference layout scaffold must preserve the physical composition map"
        )

    candidate["approval"] = {
        "status": "draft",
        "approved_by": None,
        "approved_at": None,
        "method": "reference-layout-scaffold/v1; composition and approval review required",
    }
    candidate["scaffold"] = {
        "schema_version": SCAFFOLD_SCHEMA_VERSION,
        "status": "draft",
        "production_eligible": False,
        "registry_update": "required-after-approval",
        "seed_plan": {
            "path": seed_path.as_posix(),
            "sha256": _sha256(seed_path.resolve()),
        },
        "review_scope": {
            "composition_map": "copied-from-seed-and-preserved",
            "source_identity": "refreshed-from-manual-ir",
            "approval": "required",
        },
    }
    return candidate


def build_reference_layout_scaffold(
    seed_path: Path,
    ir: ManualIR,
) -> dict[str, Any]:
    """Return a non-activating draft preserving the seed composition map."""
    display_path = seed_path
    resolved_path = seed_path.resolve()
    seed = _read_json(resolved_path, "reference layout seed")
    return _draft_candidate(seed, ir, seed_path=display_path)


__all__ = (
    "SCAFFOLD_SCHEMA_VERSION",
    "build_reference_layout_scaffold",
)
