"""Registered-component targets: single-language IDML builds on approved parts.

A reference-layout registry entry may declare ``component_targets``: the
languages whose *single-language* build composes its registered components
(LCD presentation profile, native Overview, Charging, Storage and
Troubleshooting, Warranty, base-art operation panels) from the entry's
approved plan.  Those compositions were accepted page by page in InDesign; the
whole book was not, so a declaration never activates a physical page plan.

A declaration is active only while every source page of the build is pinned,
with the same digest, by that approved plan.  Any drift keeps the build on the
ordinary layout and prints a loud warning instead of composing content no one
has reviewed in these compositions.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from tools.manual_ir import ManualIR
from tools.utils.path_utils import PathSegments, Paths

from .reference_layout_plan import (
    REGISTRY_SCHEMA_VERSION,
    SUPPORTED_SCHEMA_VERSIONS,
    ReferenceLayoutPlanError,
)


COMPONENT_TARGET_STATUSES = frozenset({"pilot"})
_DECLARATION_KEYS = frozenset({"language", "status", "evidence"})
_NON_CONTENT_LANGUAGES = frozenset({"", "cover", "toc"})


def _language(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-").split("-", 1)[0]


def _build_languages(ir: ManualIR) -> list[str]:
    """Return the build's content languages in source order."""
    languages: list[str] = []
    for page in ir.pages:
        if page.language in _NON_CONTENT_LANGUAGES or page.language in languages:
            continue
        languages.append(page.language)
    return languages


def _read_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReferenceLayoutPlanError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ReferenceLayoutPlanError(f"{label} must contain a JSON object: {path}")
    return payload


def _declarations(entry: Mapping[str, Any]) -> list[dict[str, str]]:
    raw = entry.get("component_targets")
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ReferenceLayoutPlanError("registry component_targets must be a list")
    declarations: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, item in enumerate(raw):
        prefix = f"component_targets[{index}]"
        if not isinstance(item, dict):
            raise ReferenceLayoutPlanError(f"{prefix} must be an object")
        unknown = sorted(set(item) - _DECLARATION_KEYS)
        if unknown:
            raise ReferenceLayoutPlanError(f"{prefix} has unknown keys: {unknown}")
        language = _language(item.get("language"))
        status = str(item.get("status") or "").strip()
        evidence = str(item.get("evidence") or "").strip()
        if not language:
            raise ReferenceLayoutPlanError(f"{prefix}.language must be non-empty")
        if language in seen:
            raise ReferenceLayoutPlanError(f"{prefix} repeats language {language!r}")
        if status not in COMPONENT_TARGET_STATUSES:
            raise ReferenceLayoutPlanError(
                f"{prefix}.status must be one of {sorted(COMPONENT_TARGET_STATUSES)}"
            )
        if not evidence:
            raise ReferenceLayoutPlanError(f"{prefix}.evidence must be non-empty")
        seen.add(language)
        declarations.append(
            {"language": language, "status": status, "evidence": evidence}
        )
    return declarations


def _approved_plan(root: Path, entry: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    raw_path = entry.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ReferenceLayoutPlanError("component target registry path must be non-empty")
    relative = Path(raw_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ReferenceLayoutPlanError("component target plan path must stay repo-relative")
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(root):
        raise ReferenceLayoutPlanError("component target plan path escapes the repository")
    payload = _read_object(resolved, "component target plan")
    if payload.get("schema_version") not in SUPPORTED_SCHEMA_VERSIONS:
        raise ReferenceLayoutPlanError("component target plan schema is unsupported")
    if payload.get("target") != entry.get("target"):
        raise ReferenceLayoutPlanError(
            "component target plan target does not match its registry entry"
        )
    approval = payload.get("approval")
    if not isinstance(approval, dict) or approval.get("status") != "approved":
        raise ReferenceLayoutPlanError("component target plan is not approved")
    if not isinstance(payload.get("pages"), list):
        raise ReferenceLayoutPlanError("component target plan pages must be a list")
    return relative.as_posix(), payload


@dataclass(frozen=True)
class ComponentTarget:
    """One declared (model, region, language) build and whether it composes."""

    model: str
    region: str
    language: str
    status: str
    evidence: str
    plan_path: str
    plan: Mapping[str, Any] = field(repr=False)
    built_sources: frozenset[str] = frozenset()
    issues: tuple[str, ...] = ()

    @property
    def active(self) -> bool:
        return not self.issues

    @property
    def label(self) -> str:
        return f"{self.model}/{self.region}/{self.language}"

    def source_pins(self) -> dict[str, Mapping[str, Any]]:
        """Return the approved plan's pinned pages for this language."""
        return {
            str(page.get("source_ref") or ""): page
            for page in self.plan.get("pages", [])
            if isinstance(page, dict) and _language(page.get("language")) == self.language
        }

    def report(self) -> None:
        """Print the activation decision at the exporter boundary."""
        if self.active:
            print(
                f"[export-idml] COMPONENT TARGET OK ({self.status}): {self.label} | "
                f"pinned={len(self.built_sources)}/{len(self.built_sources)} "
                f"by {self.plan_path}"
            )
            return
        print(
            f"[export-idml] WARNING: COMPONENT TARGET INERT ({self.status}): "
            f"{self.label} keeps the ordinary layout; {len(self.issues)} issue(s)"
        )
        for issue in self.issues:
            print(f"[export-idml] WARNING:   {issue}")


def resolve_component_target(
    ir: ManualIR,
    *,
    root: Path,
    language: str | None,
    assembly_plan: Path | None = None,
) -> ComponentTarget | None:
    """Return this build's component-target declaration, or None if undeclared.

    Only a single-language build of a declared language is a component target.
    Malformed declarations and plans fail closed; content drift does not — it
    returns an inert target whose ``issues`` name every drifted source.
    """
    root = root.resolve()
    registry_path = (
        Paths(root=root).renderer_contracts_dir
        / PathSegments.REFERENCE_LAYOUT_REGISTRY_JSON
    )
    build_language = _language(language)
    build_languages = _build_languages(ir)
    if not registry_path.is_file() or not build_language:
        return None
    if build_languages != [build_language]:
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
    declared = [
        (entry, declaration)
        for entry in family
        for declaration in _declarations(entry)
        if declaration["language"] == build_language
    ]
    if not declared:
        return None
    if len(declared) > 1:
        raise ReferenceLayoutPlanError(
            f"registry declares {ir.model}/{ir.region}/{build_language} as a "
            f"component target {len(declared)} times"
        )
    entry, declaration = declared[0]
    plan_path, plan = _approved_plan(root, entry)
    target = ComponentTarget(
        model=ir.model,
        region=ir.region,
        language=build_language,
        status=declaration["status"],
        evidence=declaration["evidence"],
        plan_path=plan_path,
        plan=plan,
    )
    pins = target.source_pins()
    if len(pins) != sum(
        1 for page in plan["pages"]
        if isinstance(page, dict) and _language(page.get("language")) == build_language
    ):
        raise ReferenceLayoutPlanError(f"{plan_path}: duplicate pinned source")

    issues: list[str] = []
    if assembly_plan is not None:
        issues.append(f"superseded by the configured target assembly plan {assembly_plan}")
    exact_target = {"model": ir.model, "region": ir.region, "languages": build_languages}
    if any(item.get("target") == exact_target for item in family):
        issues.append("superseded by the approved reference plan registered for this build")
    built = [page for page in ir.pages if page.language == build_language]
    for page in built:
        pin = pins.get(page.source_ref)
        if pin is None:
            issues.append(f"{page.source_ref}: not pinned by {plan_path}")
        elif pin.get("source_sha256") != page.source_sha256:
            issues.append(
                f"{page.source_ref}: source_sha256 does not match "
                f"(pinned={str(pin.get('source_sha256'))[:12]}, "
                f"built={page.source_sha256[:12]})"
            )
    return ComponentTarget(
        model=target.model,
        region=target.region,
        language=target.language,
        status=target.status,
        evidence=target.evidence,
        plan_path=target.plan_path,
        plan=plan,
        built_sources=frozenset(page.source_ref for page in built),
        issues=tuple(issues),
    )


__all__ = [
    "COMPONENT_TARGET_STATUSES",
    "ComponentTarget",
    "resolve_component_target",
]
