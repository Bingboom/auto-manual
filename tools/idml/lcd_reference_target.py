"""Resolve registered LCD presentation ownership without activating a page plan."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.manual_ir import ManualIR
from tools.utils.path_utils import PathSegments, Paths

from .lcd_reference_profile import validate_lcd_reference_profile
from .reference_layout_plan import (
    REGISTRY_SCHEMA_VERSION,
    SUPPORTED_SCHEMA_VERSIONS,
    ReferenceLayoutPlanError,
)


def _read_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReferenceLayoutPlanError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ReferenceLayoutPlanError(f"{label} must contain a JSON object: {path}")
    return payload


def _registered_plan(root: Path, raw_path: Any) -> dict[str, Any]:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ReferenceLayoutPlanError("registered LCD plan path must be non-empty")
    relative = Path(raw_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ReferenceLayoutPlanError("registered LCD plan path must stay repo-relative")
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(root):
        raise ReferenceLayoutPlanError("registered LCD plan path escapes the repository")
    return _read_object(resolved, "registered LCD reference plan")


def find_registered_lcd_profile(
    ir: ManualIR,
    *,
    root: Path,
    language: str,
) -> dict[str, Any] | None:
    """Return the approved LCD profile that owns this exact source page.

    This is deliberately narrower than an approved reference page plan: it
    authorizes only the LCD row-presentation contract and does not activate
    any page count, physical placement, or whole-document identity.
    """
    root = root.resolve()
    registry_path = (
        Paths(root=root).renderer_contracts_dir
        / PathSegments.REFERENCE_LAYOUT_REGISTRY_JSON
    )
    if not registry_path.is_file():
        return None
    registry = _read_object(registry_path, "approved reference layout registry")
    if registry.get("schema_version") != REGISTRY_SCHEMA_VERSION:
        raise ReferenceLayoutPlanError(
            f"registry schema_version must be {REGISTRY_SCHEMA_VERSION}"
        )
    entries = registry.get("plans")
    if not isinstance(entries, list):
        raise ReferenceLayoutPlanError("registry plans must be a list")
    family = [
        entry for entry in entries
        if isinstance(entry, dict)
        and isinstance(entry.get("target"), dict)
        and entry["target"].get("model") == ir.model
        and entry["target"].get("region") == ir.region
    ]
    if not family:
        return None

    normalized_language = language.strip().casefold().replace("_", "-").split("-", 1)[0]
    declaring = [
        entry for entry in family
        if normalized_language in (entry.get("target") or {}).get("languages", [])
    ]
    if not declaring:
        return None

    source_refs = {
        page.source_ref for page in ir.pages
        if page.language == normalized_language
        and Path(page.source_ref).name.startswith(("lcd_icons_", "lcd_display_"))
    }
    matches: list[dict[str, Any]] = []
    for entry in declaring:
        payload = _registered_plan(root, entry.get("path"))
        if payload.get("schema_version") not in SUPPORTED_SCHEMA_VERSIONS:
            raise ReferenceLayoutPlanError("registered LCD plan schema is unsupported")
        if payload.get("target") != entry.get("target"):
            raise ReferenceLayoutPlanError(
                "registered LCD plan target does not match its registry entry"
            )
        approval = payload.get("approval")
        if not isinstance(approval, dict) or approval.get("status") != "approved":
            raise ReferenceLayoutPlanError("registered LCD plan is not approved")
        owned_sources = {
            str(page.get("source_ref") or "")
            for page in payload.get("pages", [])
            if isinstance(page, dict) and page.get("language") == normalized_language
        }
        if not source_refs.intersection(owned_sources):
            continue
        profile = (
            ((payload.get("idml_contract") or {}).get("editable_components") or {})
            .get("lcd_icon_table")
        )
        issues = validate_lcd_reference_profile(profile)
        if issues:
            raise ReferenceLayoutPlanError(
                "registered LCD profile is invalid: " + "; ".join(issues)
            )
        matches.append(profile)
    if len(matches) > 1:
        raise ReferenceLayoutPlanError(
            f"registry has {len(matches)} LCD owners for "
            f"{ir.model}/{ir.region}/{normalized_language}"
        )
    return matches[0] if matches else None
