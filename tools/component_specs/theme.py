"""Load and validate semantic theme-role projections for ComponentSpec."""
from __future__ import annotations

import hashlib
import json
from collections.abc import Collection, Mapping
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment/setup failure
    raise RuntimeError("PyYAML is required to load the manual theme") from exc

from tools.component_specs.model import ComponentSpec, ComponentSpecError
from tools.component_specs.registry import RENDERERS, load_component_registry
from tools.utils.path_utils import Paths, repo_root


THEME_SCHEMA_VERSION = "manual-theme/v1"
_ROLE_KEYS = frozenset({"bindings"})
_COMPONENT_ROLE_KEYS = frozenset({"component_ids", "theme_roles"})
_BINDING_KINDS = {
    "web": frozenset({"css-custom-property"}),
    "latex": frozenset({"color", "layout-token", "macro"}),
    "idml": frozenset(
        {
            "color",
            "layout-token",
            "object-style",
            "paragraph-style",
            "property-adapter",
            "table-style",
        }
    ),
    "word": frozenset(
        {"html-class", "property-adapter", "style", "table-style"}
    ),
}


def default_theme_path() -> Path:
    return Paths(root=repo_root()).manual_theme_contract


def _unique_non_empty_strings(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and item.strip() for item in value)
        and len(value) == len(set(value))
    )


def validate_manual_theme(
    theme: Mapping[str, Any],
    *,
    component_registry: Mapping[str, Any] | None = None,
    layout_token_names: Collection[str] | None = None,
) -> list[str]:
    """Validate ownership, four-renderer bindings, and registry parity."""
    issues: list[str] = []
    if theme.get("schema_version") != THEME_SCHEMA_VERSION:
        issues.append(f"schema_version must be {THEME_SCHEMA_VERSION!r}")
    if not isinstance(theme.get("theme_id"), str) or not theme["theme_id"].strip():
        issues.append("theme_id must be a non-empty string")

    component_roles = theme.get("component_roles")
    roles = theme.get("roles")
    if not isinstance(component_roles, Mapping) or not component_roles:
        issues.append("component_roles must be a non-empty mapping")
        component_roles = {}
    if not isinstance(roles, Mapping) or not roles:
        issues.append("roles must be a non-empty mapping")
        roles = {}

    registry = component_registry or load_component_registry()
    registered_components = registry.get("components")
    if not isinstance(registered_components, Mapping):
        registered_components = {}

    consumed_roles: set[str] = set()
    declared_component_ids: dict[str, set[str]] = {}
    for component_role, raw_projection in component_roles.items():
        prefix = f"component_roles.{component_role}"
        if not isinstance(component_role, str) or not component_role.startswith("component."):
            issues.append(f"{prefix}: role must start with 'component.'")
        if not isinstance(raw_projection, Mapping):
            issues.append(f"{prefix} must be a mapping")
            continue
        unknown_keys = set(raw_projection) - _COMPONENT_ROLE_KEYS
        if unknown_keys:
            issues.append(f"{prefix} has unsupported keys {sorted(unknown_keys)!r}")
        component_ids = raw_projection.get("component_ids")
        theme_roles = raw_projection.get("theme_roles")
        if not _unique_non_empty_strings(component_ids):
            issues.append(f"{prefix}.component_ids must be a unique non-empty string list")
            component_ids = []
        if not _unique_non_empty_strings(theme_roles):
            issues.append(f"{prefix}.theme_roles must be a unique non-empty string list")
            theme_roles = []
        consumed_roles.update(theme_roles)
        declared_component_ids[component_role] = set(component_ids)
        for component_id in component_ids:
            component = registered_components.get(component_id)
            if not isinstance(component, Mapping):
                issues.append(f"{prefix}: unknown component ID {component_id!r}")
                continue
            if component_role not in component.get("token_roles", []):
                issues.append(
                    f"{prefix}: {component_id} does not declare token role "
                    f"{component_role!r}"
                )
        for theme_role in theme_roles:
            if theme_role not in roles:
                issues.append(f"{prefix}: unknown theme role {theme_role!r}")

    for component_id, component in registered_components.items():
        if not isinstance(component, Mapping):
            continue
        for component_role in component.get("token_roles", []):
            owners = declared_component_ids.get(component_role, set())
            if component_id not in owners:
                issues.append(
                    f"components.{component_id}: token role {component_role!r} "
                    "has no theme projection"
                )

    for role, raw_role in roles.items():
        prefix = f"roles.{role}"
        if not isinstance(role, str) or "." not in role:
            issues.append(f"{prefix}: theme role must be a dotted semantic name")
        if role not in consumed_roles:
            issues.append(f"{prefix}: theme role has no component consumer")
        if not isinstance(raw_role, Mapping):
            issues.append(f"{prefix} must be a mapping")
            continue
        unknown_keys = set(raw_role) - _ROLE_KEYS
        if unknown_keys:
            issues.append(f"{prefix} has unsupported keys {sorted(unknown_keys)!r}")
        bindings = raw_role.get("bindings")
        if not isinstance(bindings, Mapping):
            issues.append(f"{prefix}.bindings must be a mapping")
            continue
        unknown_renderers = set(bindings) - set(RENDERERS)
        if unknown_renderers:
            issues.append(
                f"{prefix}.bindings has unknown renderers {sorted(unknown_renderers)!r}"
            )
        for renderer in RENDERERS:
            binding_prefix = f"{prefix}.bindings.{renderer}"
            binding = bindings.get(renderer)
            if not isinstance(binding, Mapping):
                issues.append(f"{binding_prefix} must be a mapping")
                continue
            if set(binding) != {"kind", "name"}:
                issues.append(f"{binding_prefix} must contain only kind and name")
            kind = binding.get("kind")
            name = binding.get("name")
            if kind not in _BINDING_KINDS[renderer]:
                issues.append(f"{binding_prefix}.kind is invalid: {kind!r}")
            if not isinstance(name, str) or not name.strip():
                issues.append(f"{binding_prefix}.name must be a non-empty string")
            if kind == "css-custom-property" and not str(name).startswith("--"):
                issues.append(f"{binding_prefix}.name must start with '--'")
            if kind == "layout-token" and layout_token_names is not None:
                if name not in layout_token_names:
                    issues.append(f"{binding_prefix}: unknown layout token {name!r}")
    return issues


def load_manual_theme(
    path: Path | None = None,
    *,
    component_registry: Mapping[str, Any] | None = None,
    layout_token_names: Collection[str] | None = None,
) -> dict[str, Any]:
    theme_path = (path or default_theme_path()).resolve()
    try:
        payload = yaml.safe_load(theme_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ComponentSpecError(f"cannot load manual theme {theme_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ComponentSpecError(f"manual theme must contain a mapping: {theme_path}")
    issues = validate_manual_theme(
        payload,
        component_registry=component_registry,
        layout_token_names=layout_token_names,
    )
    if issues:
        raise ComponentSpecError("invalid manual theme: " + "; ".join(issues))
    return payload


def require_component_theme_roles(
    spec: ComponentSpec,
    theme: Mapping[str, Any] | None = None,
) -> ComponentSpec:
    active_theme = theme or load_manual_theme()
    component_roles = active_theme["component_roles"]
    for component_role in spec.token_roles:
        projection = component_roles.get(component_role)
        if not isinstance(projection, Mapping):
            raise ComponentSpecError(
                f"{spec.component_id}: theme has no projection for {component_role!r}"
            )
        if spec.component_id not in projection.get("component_ids", []):
            raise ComponentSpecError(
                f"{spec.component_id}: theme role {component_role!r} does not own component"
            )
    return spec


def theme_sha256(theme: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        theme,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


__all__ = [
    "THEME_SCHEMA_VERSION",
    "default_theme_path",
    "load_manual_theme",
    "require_component_theme_roles",
    "theme_sha256",
    "validate_manual_theme",
]
