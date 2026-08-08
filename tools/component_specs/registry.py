"""Load and validate the renderer-neutral component registry."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment/setup failure
    raise RuntimeError("PyYAML is required to load the component registry") from exc

from tools.component_specs.model import ComponentSpec, ComponentSpecError, SCHEMA_VERSION
from tools.utils.path_utils import Paths, repo_root


REGISTRY_SCHEMA_VERSION = "component-registry/v1"
RENDERERS = ("web", "latex", "idml", "word")
CAPABILITIES = frozenset({"rendered", "projection-only", "not-applicable"})
REGISTERED_ADAPTER_KEYS: dict[str, frozenset[str]] = {
    "web": frozenset(
        {"manual_callout_table", "hb_spec_table", "hb_fcc", "hb_inbox"}
    ),
    "latex": frozenset(
        {
            "hb_latex_callout",
            "hb_latex_spec_table",
            "hb_latex_fcc",
            "hb_latex_inbox",
        }
    ),
    "idml": frozenset(
        {"idml_notice", "idml_spec_table", "idml_fcc", "idml_inbox"}
    ),
    "word": frozenset(
        {"word_manual_callout_table", "word_spec_table", "word_fcc", "word_inbox"}
    ),
}
LOCALE_POLICIES = frozenset({"exact", "shared"})


def default_registry_path() -> Path:
    return Paths(root=repo_root()).component_registry_contract


def _non_empty_strings(value: Any, *, allow_empty: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(isinstance(item, str) and item.strip() for item in value)
        and len(value) == len(set(value))
    )


def _validate_structured_rows(value: Any, *, prefix: str) -> list[str]:
    issues: list[str] = []
    if not isinstance(value, list) or not value:
        return [f"{prefix} must be a non-empty list"]
    for index, group in enumerate(value):
        group_prefix = f"{prefix}[{index}]"
        if not isinstance(group, Mapping):
            issues.append(f"{group_prefix} must be a mapping")
            continue
        if set(group) != {"label", "label_rowspan", "values", "references"}:
            issues.append(f"{group_prefix} has an invalid structured-row shape")
            continue
        if not isinstance(group.get("label"), str) or not group["label"].strip():
            issues.append(f"{group_prefix}.label must be a non-empty string")
        values = group.get("values")
        if not isinstance(values, list) or not values:
            issues.append(f"{group_prefix}.values must be a non-empty list")
            continue
        if group.get("label_rowspan") != len(values):
            issues.append(f"{group_prefix}.label_rowspan must equal value count")
        if not _non_empty_strings(group.get("references"), allow_empty=True):
            issues.append(f"{group_prefix}.references must be a unique string list")
        for value_index, item in enumerate(values):
            value_prefix = f"{group_prefix}.values[{value_index}]"
            if not isinstance(item, Mapping) or set(item) != {"text", "references"}:
                issues.append(f"{value_prefix} has an invalid value shape")
                continue
            if not isinstance(item.get("text"), str):
                issues.append(f"{value_prefix}.text must be a string")
            if not _non_empty_strings(item.get("references"), allow_empty=True):
                issues.append(f"{value_prefix}.references must be a unique string list")
    return issues


def validate_component_registry(registry: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    if registry.get("schema_version") != REGISTRY_SCHEMA_VERSION:
        issues.append(f"schema_version must be {REGISTRY_SCHEMA_VERSION!r}")
    if not isinstance(registry.get("registry_id"), str) or not registry["registry_id"].strip():
        issues.append("registry_id must be a non-empty string")
    components = registry.get("components")
    if not isinstance(components, Mapping) or not components:
        return issues + ["components must be a non-empty mapping"]
    for component_id, raw_component in components.items():
        prefix = f"components.{component_id}"
        if not isinstance(component_id, str) or not component_id.startswith("HB-"):
            issues.append(f"{prefix}: component ID must start with HB-")
        if not isinstance(raw_component, Mapping):
            issues.append(f"{prefix} must be a mapping")
            continue
        if raw_component.get("style_id") != component_id:
            issues.append(f"{prefix}.style_id must equal {component_id!r}")
        variants = raw_component.get("variants")
        if not _non_empty_strings(variants):
            issues.append(f"{prefix}.variants must be a unique non-empty string list")
        source_kinds = raw_component.get("source_kinds")
        if not _non_empty_strings(source_kinds):
            issues.append(f"{prefix}.source_kinds must be a unique non-empty string list")
        token_roles = raw_component.get("token_roles")
        if not _non_empty_strings(token_roles):
            issues.append(f"{prefix}.token_roles must be a unique non-empty string list")
        slots = raw_component.get("slots")
        if not isinstance(slots, Mapping) or not slots:
            issues.append(f"{prefix}.slots must be a non-empty mapping")
        else:
            for role, raw_slot in slots.items():
                slot_prefix = f"{prefix}.slots.{role}"
                if not isinstance(role, str) or not role.strip():
                    issues.append(f"{slot_prefix}: role must be a non-empty string")
                if not isinstance(raw_slot, Mapping):
                    issues.append(f"{slot_prefix} must be a mapping")
                    continue
                if not isinstance(raw_slot.get("required"), bool):
                    issues.append(f"{slot_prefix}.required must be boolean")
                if not _non_empty_strings(raw_slot.get("content_kinds")):
                    issues.append(
                        f"{slot_prefix}.content_kinds must be a unique non-empty string list"
                    )
        assets = raw_component.get("asset_roles")
        if not isinstance(assets, Mapping):
            issues.append(f"{prefix}.asset_roles must be a mapping")
        else:
            for role, raw_asset in assets.items():
                asset_prefix = f"{prefix}.asset_roles.{role}"
                if not isinstance(role, str) or not role.strip():
                    issues.append(f"{asset_prefix}: role must be a non-empty string")
                if not isinstance(raw_asset, Mapping):
                    issues.append(f"{asset_prefix} must be a mapping")
                    continue
                if set(raw_asset) != {"required", "locale_policies"}:
                    issues.append(f"{asset_prefix} has an invalid asset-role shape")
                if not isinstance(raw_asset.get("required"), bool):
                    issues.append(f"{asset_prefix}.required must be boolean")
                policies = raw_asset.get("locale_policies")
                if not _non_empty_strings(policies) or not set(policies).issubset(
                    LOCALE_POLICIES
                ):
                    issues.append(
                        f"{asset_prefix}.locale_policies must use registered policies"
                    )
        adapters = raw_component.get("adapters")
        if not isinstance(adapters, Mapping):
            issues.append(f"{prefix}.adapters must be a mapping")
            continue
        for renderer in set(adapters) - set(RENDERERS):
            issues.append(f"{prefix}.adapters has unknown renderer {renderer!r}")
        for renderer in RENDERERS:
            adapter_prefix = f"{prefix}.adapters.{renderer}"
            binding = adapters.get(renderer)
            if not isinstance(binding, Mapping):
                issues.append(f"{adapter_prefix} must be a mapping")
                continue
            capability = binding.get("capability")
            if capability not in CAPABILITIES:
                issues.append(f"{adapter_prefix}.capability is invalid: {capability!r}")
            key = binding.get("key")
            if key not in REGISTERED_ADAPTER_KEYS[renderer]:
                issues.append(f"{adapter_prefix}.key is unregistered: {key!r}")
    return issues


def load_component_registry(path: Path | None = None) -> dict[str, Any]:
    registry_path = (path or default_registry_path()).resolve()
    try:
        payload = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ComponentSpecError(f"cannot load component registry {registry_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ComponentSpecError(f"component registry must contain a mapping: {registry_path}")
    issues = validate_component_registry(payload)
    if issues:
        raise ComponentSpecError("invalid component registry: " + "; ".join(issues))
    return payload


def registry_sha256(registry: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        registry,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_component_spec(
    spec: ComponentSpec,
    registry: Mapping[str, Any] | None = None,
) -> list[str]:
    active_registry = registry if registry is not None else load_component_registry()
    issues: list[str] = []
    if spec.schema_version != SCHEMA_VERSION:
        issues.append(f"schema_version must be {SCHEMA_VERSION!r}")
    components = active_registry.get("components")
    definition = components.get(spec.component_id) if isinstance(components, Mapping) else None
    if not isinstance(definition, Mapping):
        return issues + [f"unknown component_id {spec.component_id!r}"]
    if spec.variant not in definition.get("variants", []):
        issues.append(f"{spec.component_id}: unknown variant {spec.variant!r}")
    if not spec.source_ref.strip():
        issues.append(f"{spec.component_id}: source_ref must be a non-empty string")
    if not spec.language.strip():
        issues.append(f"{spec.component_id}: language must be a non-empty string")
    slot_definitions = definition.get("slots")
    seen_slots: set[str] = set()
    for slot in spec.slots:
        if slot.role in seen_slots:
            issues.append(f"{spec.component_id}: duplicate slot role {slot.role!r}")
        seen_slots.add(slot.role)
        slot_definition = (
            slot_definitions.get(slot.role)
            if isinstance(slot_definitions, Mapping)
            else None
        )
        if not isinstance(slot_definition, Mapping):
            issues.append(f"{spec.component_id}: unknown slot role {slot.role!r}")
            continue
        if slot.content_kind not in slot_definition.get("content_kinds", []):
            issues.append(
                f"{spec.component_id}.{slot.role}: unsupported content_kind "
                f"{slot.content_kind!r}"
            )
        try:
            json.dumps(slot.content, ensure_ascii=False)
        except (TypeError, ValueError):
            issues.append(f"{spec.component_id}.{slot.role}: content must be JSON-serializable")
        if slot.content_kind == "structured_rows":
            issues.extend(
                _validate_structured_rows(
                    slot.content,
                    prefix=f"{spec.component_id}.{slot.role}",
                )
            )
    if isinstance(slot_definitions, Mapping):
        for role, slot_definition in slot_definitions.items():
            if isinstance(slot_definition, Mapping) and slot_definition.get("required"):
                if role not in seen_slots:
                    issues.append(f"{spec.component_id}: missing required slot {role!r}")
    asset_definitions = definition.get("asset_roles")
    seen_assets: set[str] = set()
    for asset in spec.assets:
        if asset.role in seen_assets:
            issues.append(f"{spec.component_id}: duplicate asset role {asset.role!r}")
        seen_assets.add(asset.role)
        asset_definition = (
            asset_definitions.get(asset.role)
            if isinstance(asset_definitions, Mapping)
            else None
        )
        if not isinstance(asset_definition, Mapping):
            issues.append(f"{spec.component_id}: unknown asset role {asset.role!r}")
        if not asset.asset_ref.strip():
            issues.append(f"{spec.component_id}.{asset.role}: asset_ref must be non-empty")
        if asset.locale_policy not in LOCALE_POLICIES:
            issues.append(
                f"{spec.component_id}.{asset.role}: unsupported locale_policy "
                f"{asset.locale_policy!r}"
            )
        elif isinstance(asset_definition, Mapping) and asset.locale_policy not in (
            asset_definition.get("locale_policies") or []
        ):
            issues.append(
                f"{spec.component_id}.{asset.role}: locale_policy "
                f"{asset.locale_policy!r} is not allowed by the registry"
            )
    if isinstance(asset_definitions, Mapping):
        for role, asset_definition in asset_definitions.items():
            if isinstance(asset_definition, Mapping) and asset_definition.get("required"):
                if role not in seen_assets:
                    issues.append(f"{spec.component_id}: missing required asset {role!r}")
    expected_token_roles = tuple(definition.get("token_roles") or [])
    if spec.token_roles != expected_token_roles:
        issues.append(
            f"{spec.component_id}: token_roles must equal registry roles "
            f"{expected_token_roles!r}"
        )
    try:
        json.dumps(spec.metadata, ensure_ascii=False)
    except (TypeError, ValueError):
        issues.append(f"{spec.component_id}: metadata must be JSON-serializable")
    return issues


def require_valid_component_spec(
    spec: ComponentSpec,
    registry: Mapping[str, Any] | None = None,
) -> ComponentSpec:
    issues = validate_component_spec(spec, registry)
    if issues:
        raise ComponentSpecError("; ".join(issues))
    return spec


def adapter_binding(
    spec: ComponentSpec,
    renderer: str,
    registry: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    active_registry = registry if registry is not None else load_component_registry()
    require_valid_component_spec(spec, active_registry)
    if renderer not in RENDERERS:
        raise ComponentSpecError(f"unknown renderer {renderer!r}")
    binding = active_registry["components"][spec.component_id]["adapters"][renderer]
    if binding["key"] not in REGISTERED_ADAPTER_KEYS[renderer]:
        raise ComponentSpecError(
            f"{spec.component_id}: unregistered {renderer} adapter {binding['key']!r}"
        )
    return binding


__all__ = [
    "CAPABILITIES",
    "REGISTERED_ADAPTER_KEYS",
    "REGISTRY_SCHEMA_VERSION",
    "RENDERERS",
    "adapter_binding",
    "default_registry_path",
    "load_component_registry",
    "registry_sha256",
    "require_valid_component_spec",
    "validate_component_registry",
    "validate_component_spec",
]
