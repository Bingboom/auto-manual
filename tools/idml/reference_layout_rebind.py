"""Safely refresh an approved reference-layout plan against one Manual IR."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Any

from tools.manual_ir import ManualIR
from tools.render_contract import LAYOUT_PARAMS_HASH_ALGORITHM

from .reference_layout_plan import (
    V2_SCHEMA_VERSION,
    ReferenceLayoutPlanError,
    build_identity_scopes,
    validate_approved_reference_plan,
)


_IDENTITY_FIELDS = (
    "content.manual_ir_schema_version",
    "content.manual_content_sha256",
    "assembly.sha256",
    "style.style_contract_sha256",
    "style.layout_params_sha256",
    "provenance.snapshot_sha256",
)


@dataclass(frozen=True)
class ReferenceLayoutRebindResult:
    """Validated rebind candidate plus a concise mutation summary."""

    plan_path: Path
    candidate: dict[str, Any]
    changed_identity_fields: tuple[str, ...]
    changed_page_bindings: int
    content_reapproved: bool
    wrote: bool


def _read_payload(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReferenceLayoutPlanError(
            f"approved reference layout plan does not exist: {path}"
        ) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ReferenceLayoutPlanError(
            f"cannot read approved reference layout plan {path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise ReferenceLayoutPlanError(
            f"approved reference layout plan must contain a JSON object: {path}"
        )
    return payload


def _source_refs(payload: dict[str, Any]) -> tuple[str, ...]:
    pages = payload.get("pages")
    if not isinstance(pages, list):
        raise ReferenceLayoutPlanError("approved reference layout pages must be a list")
    refs: list[str] = []
    for index, page in enumerate(pages):
        if not isinstance(page, dict) or not isinstance(page.get("source_ref"), str):
            raise ReferenceLayoutPlanError(
                f"approved reference layout pages[{index}].source_ref must be a string"
            )
        refs.append(page["source_ref"])
    return tuple(refs)


def _composition_map(payload: dict[str, Any]) -> tuple[tuple[Any, ...], ...]:
    """Return every physical-layout field that rebind is forbidden to change."""
    pages = payload.get("pages")
    if not isinstance(pages, list):
        raise ReferenceLayoutPlanError("approved reference layout pages must be a list")
    mapping: list[tuple[Any, ...]] = []
    for index, page in enumerate(pages):
        if not isinstance(page, dict):
            raise ReferenceLayoutPlanError(
                f"approved reference layout pages[{index}] must be an object"
            )
        flow_split = page.get("flow_split")
        mapping.append((
            page.get("source_ref"),
            page.get("composition_id"),
            page.get("start_page"),
            page.get("page_count"),
            json.dumps(
                flow_split,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ) if flow_split is not None else None,
        ))
    return tuple(mapping)


def _identity_value(payload: dict[str, Any], dotted: str) -> Any:
    if payload.get("schema_version") == V2_SCHEMA_VERSION:
        value: Any = payload.get("identity")
        for part in dotted.split("."):
            value = value.get(part) if isinstance(value, dict) else None
        return value
    legacy = payload.get("source_identity")
    if not isinstance(legacy, dict):
        return None
    return legacy.get({
        "content.manual_ir_schema_version": "manual_ir_schema_version",
        "content.manual_content_sha256": "manual_content_sha256",
        "style.style_contract_sha256": "style_contract_sha256",
        "style.layout_params_sha256": "layout_params_sha256",
        "provenance.snapshot_sha256": "snapshot_sha256",
    }.get(dotted, ""))


def build_rebound_reference_layout_plan(
    payload: dict[str, Any],
    ir: ManualIR,
    *,
    content_approval: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Return a fully validated binding refresh without changing layout.

    Rebinding is intentionally narrower than approving a new plan. The manual's
    semantic content, assembly identity, source-page order, page languages,
    and every physical composition field must already match. Only style and
    provenance identity fields plus each page's raw source digest may change.
    """
    actual_hash_algorithm = ir.metadata.get("layout_params_hash_algorithm")
    if actual_hash_algorithm != LAYOUT_PARAMS_HASH_ALGORITHM:
        raise ReferenceLayoutPlanError(
            "reference-layout rebind requires Manual IR layout hash algorithm "
            f"{LAYOUT_PARAMS_HASH_ALGORITHM!r}; got {actual_hash_algorithm!r}"
        )
    current_refs = _source_refs(payload)
    expected_refs = tuple(page.source_ref for page in ir.pages)
    if current_refs != expected_refs:
        raise ReferenceLayoutPlanError(
            "reference-layout rebind requires unchanged source_ref order; "
            f"contract={list(current_refs)!r} current={list(expected_refs)!r}"
        )

    old_content = _identity_value(payload, "content.manual_content_sha256")
    if old_content is None:
        raise ReferenceLayoutPlanError(
            "approved reference layout content identity is missing"
        )
    content_changed = old_content != ir.content_sha256
    expected_identity = build_identity_scopes(payload, ir)
    old_assembly = _identity_value(payload, "assembly.sha256")
    # A v1 plan has no assembly pin. Treat creating that identity as a reviewed
    # migration, not as evidence that the assembly is unchanged: the legacy
    # approval could not have covered the semantic page-role projection added
    # by v2.
    assembly_changed = old_assembly != expected_identity["assembly"]["sha256"]
    if (content_changed or assembly_changed) and content_approval is None:
        raise ReferenceLayoutPlanError(
            "reference-layout rebind cannot change content or assembly identity; "
            "those changes require a new layout review and approval"
        )
    if content_approval is not None:
        required = ("status", "approved_by", "approved_at", "method")
        if content_approval.get("status") != "approved" or any(
            not str(content_approval.get(key, "")).strip()
            for key in required[1:]
        ):
            raise ReferenceLayoutPlanError(
                "identity reapproval requires approved status plus non-empty "
                "approved_by, approved_at, and method"
            )

    plan_pages = payload["pages"]
    for plan_page, source_page in zip(plan_pages, ir.pages, strict=True):
        if plan_page.get("language") != source_page.language:
            raise ReferenceLayoutPlanError(
                "reference-layout rebind cannot change page language for "
                f"{source_page.source_ref}: contract={plan_page.get('language')!r} "
                f"current={source_page.language!r}"
            )

    original_composition_map = _composition_map(payload)
    candidate = deepcopy(payload)
    candidate["schema_version"] = V2_SCHEMA_VERSION
    candidate["identity"] = build_identity_scopes(candidate, ir)
    legacy_provenance = _identity_value(payload, "provenance.snapshot_sha256")
    if payload.get("schema_version") != V2_SCHEMA_VERSION and legacy_provenance:
        candidate["identity"]["provenance"]["snapshot_sha256"] = legacy_provenance
    candidate.pop("source_identity", None)
    idml_contract = candidate.get("idml_contract")
    if isinstance(idml_contract, dict):
        idml_contract.setdefault(
            "allowed_unclassified_source_refs",
            [],
        )
    if content_changed or assembly_changed:
        candidate["approval"] = deepcopy(content_approval)
    candidate_pages = candidate["pages"]
    for candidate_page, source_page in zip(candidate_pages, ir.pages, strict=True):
        candidate_page["source_sha256"] = source_page.source_sha256

    if _composition_map(candidate) != original_composition_map:
        raise ReferenceLayoutPlanError(
            "reference-layout rebind must not change the physical composition map"
        )
    issues = validate_approved_reference_plan(candidate, ir)
    if issues:
        raise ReferenceLayoutPlanError(
            "rebound approved reference layout plan is invalid: " + "; ".join(issues)
        )
    return candidate


def _atomic_write_payload(path: Path, payload: dict[str, Any]) -> None:
    data = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    mode = stat.S_IMODE(path.stat().st_mode)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_path, mode)
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def rebind_reference_layout_plan(
    plan_path: Path,
    ir: ManualIR,
    *,
    write: bool = False,
    content_approval: dict[str, str] | None = None,
) -> ReferenceLayoutRebindResult:
    """Validate a complete binding refresh and optionally commit it atomically."""
    plan_path = plan_path.resolve()
    payload = _read_payload(plan_path)
    candidate = build_rebound_reference_layout_plan(
        payload,
        ir,
        content_approval=content_approval,
    )

    changed_identity_fields = tuple(
        field
        for field in _IDENTITY_FIELDS
        if _identity_value(payload, field) != _identity_value(candidate, field)
    )
    old_pages = payload["pages"]
    new_pages = candidate["pages"]
    changed_page_bindings = sum(
        old.get("source_sha256") != new.get("source_sha256")
        or old.get("language") != new.get("language")
        for old, new in zip(old_pages, new_pages, strict=True)
    )

    if write:
        _atomic_write_payload(plan_path, candidate)
    return ReferenceLayoutRebindResult(
        plan_path=plan_path,
        candidate=candidate,
        changed_identity_fields=changed_identity_fields,
        changed_page_bindings=changed_page_bindings,
        content_reapproved=(
            _identity_value(payload, "content.manual_content_sha256")
            != _identity_value(candidate, "content.manual_content_sha256")
        ),
        wrote=write,
    )


__all__ = (
    "ReferenceLayoutRebindResult",
    "build_rebound_reference_layout_plan",
    "rebind_reference_layout_plan",
)
