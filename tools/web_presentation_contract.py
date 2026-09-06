"""Resolve the layered Web presentation contract for one document target."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path
from typing import Any


STACK_SCHEMA_VERSION = "web-manual-presentation-stack/v1"
BASE_SCHEMA_VERSION = "web-manual-shared-base/v1"
SKELETON_SCHEMA_VERSION = "web-manual-skeleton-profile/v1"
TARGET_OVERLAYS_SCHEMA_VERSION = "web-manual-target-overlays/v1"
FIGURE_DEBT_SCHEMA_VERSION = "web-figure-debt-baseline/v1"
CONTRACT_SCHEMA_VERSION = "web-manual-presentation/v2"
LEGACY_CONTRACT_SCHEMA_VERSION = "web-manual-presentation/v1"
_FINISHED_FIGURE_STATUSES = ("finished-panel", "approved-composite")
_DEBT_FIGURE_STATUSES = frozenset({"editable-fallback", "missing"})


class WebPresentationContractError(ValueError):
    """A presentation layer is malformed, ambiguous, or escapes its registry."""


def _list_by_id(value: list[Any], *, field: str) -> dict[str, Mapping[str, Any]] | None:
    if not value or not all(
        isinstance(item, Mapping) and str(item.get("id") or "").strip()
        for item in value
    ):
        return None
    indexed: dict[str, Mapping[str, Any]] = {}
    for item in value:
        item_id = str(item["id"])
        if item_id in indexed:
            raise WebPresentationContractError(f"{field} contains duplicate id {item_id!r}")
        indexed[item_id] = item
    return indexed


def merge_contract_layers(base: Any, override: Any, *, field: str = "contract") -> Any:
    """Deep-merge one layer; stable-ID lists merge and ordinary lists replace."""

    if isinstance(base, Mapping) and isinstance(override, Mapping):
        merged = deepcopy(dict(base))
        for key, value in override.items():
            child_field = f"{field}.{key}"
            merged[key] = (
                merge_contract_layers(merged[key], value, field=child_field)
                if key in merged
                else deepcopy(value)
            )
        return merged
    if isinstance(base, list) and isinstance(override, list):
        base_by_id = _list_by_id(base, field=field)
        override_by_id = _list_by_id(override, field=field)
        if base_by_id is not None and override_by_id is not None:
            merged = [
                merge_contract_layers(
                    item,
                    override_by_id[str(item["id"])],
                    field=f"{field}[id={item['id']!r}]",
                )
                if str(item["id"]) in override_by_id
                else deepcopy(item)
                for item in base
            ]
            base_ids = set(base_by_id)
            merged.extend(
                deepcopy(item)
                for item in override
                if str(item["id"]) not in base_ids
            )
            return merged
    return deepcopy(override)


def _read_mapping(path: Path, *, field: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WebPresentationContractError(f"cannot load {field} {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise WebPresentationContractError(f"{field} must contain a JSON object: {path}")
    return payload


def _layer_path(root: Path, raw: Any, *, field: str) -> Path:
    text = str(raw or "").strip()
    if not text:
        raise WebPresentationContractError(f"{field} must be a non-empty relative path")
    candidate = (root / text).resolve(strict=False)
    if not candidate.is_relative_to(root):
        raise WebPresentationContractError(f"{field} escapes contract directory: {text}")
    return candidate


def _non_empty(value: Any, *, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise WebPresentationContractError(f"{field} must be a non-empty string")
    return text


def _load_base(root: Path, raw_path: Any) -> tuple[str, dict[str, Any]]:
    path = _layer_path(root, raw_path, field="shared_base")
    payload = _read_mapping(path, field="shared base")
    if payload.get("schema_version") != BASE_SCHEMA_VERSION:
        raise WebPresentationContractError(f"unsupported shared base schema in {path}")
    layer_id = _non_empty(payload.get("base_id"), field="shared base.base_id")
    contract = payload.get("contract")
    if not isinstance(contract, Mapping):
        raise WebPresentationContractError("shared base.contract must be an object")
    return layer_id, deepcopy(dict(contract))


def _load_skeletons(
    root: Path,
    raw_registry: Any,
) -> dict[str, dict[str, Any]]:
    if not isinstance(raw_registry, Mapping) or not raw_registry:
        raise WebPresentationContractError("skeleton_profiles must be a non-empty object")
    profiles: dict[str, dict[str, Any]] = {}
    for raw_profile_id, raw_path in raw_registry.items():
        profile_id = _non_empty(raw_profile_id, field="skeleton profile id")
        path = _layer_path(
            root,
            raw_path,
            field=f"skeleton_profiles.{profile_id}",
        )
        payload = _read_mapping(path, field=f"skeleton profile {profile_id}")
        if payload.get("schema_version") != SKELETON_SCHEMA_VERSION:
            raise WebPresentationContractError(
                f"unsupported skeleton profile schema in {path}"
            )
        if payload.get("profile_id") != profile_id:
            raise WebPresentationContractError(
                f"skeleton profile {path} must declare profile_id {profile_id!r}"
            )
        contract = payload.get("contract")
        if not isinstance(contract, Mapping):
            raise WebPresentationContractError(
                f"skeleton profile {profile_id}.contract must be an object"
            )
        profiles[profile_id] = deepcopy(dict(contract))
    return profiles


def _load_target_overlays(
    root: Path,
    raw_paths: Any,
    *,
    skeletons: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if not isinstance(raw_paths, list):
        raise WebPresentationContractError("target_overlays must be a list")
    overlays: list[dict[str, Any]] = []
    overlay_ids: set[str] = set()
    target_keys: set[tuple[str, str]] = set()
    for path_index, raw_path in enumerate(raw_paths):
        path = _layer_path(root, raw_path, field=f"target_overlays[{path_index}]")
        payload = _read_mapping(path, field="target overlay registry")
        if payload.get("schema_version") != TARGET_OVERLAYS_SCHEMA_VERSION:
            raise WebPresentationContractError(
                f"unsupported target overlay registry schema in {path}"
            )
        raw_overlays = payload.get("overlays")
        if not isinstance(raw_overlays, list) or not raw_overlays:
            raise WebPresentationContractError(f"{path}: overlays must be non-empty")
        for overlay_index, raw_overlay in enumerate(raw_overlays):
            prefix = f"{path}: overlays[{overlay_index}]"
            if not isinstance(raw_overlay, Mapping):
                raise WebPresentationContractError(f"{prefix} must be an object")
            overlay = deepcopy(dict(raw_overlay))
            overlay_id = _non_empty(overlay.get("overlay_id"), field=f"{prefix}.overlay_id")
            if overlay_id in overlay_ids:
                raise WebPresentationContractError(
                    f"duplicate target overlay id {overlay_id!r}"
                )
            overlay_ids.add(overlay_id)
            target = overlay.get("target")
            if not isinstance(target, Mapping):
                raise WebPresentationContractError(f"{prefix}.target must be an object")
            model = _non_empty(target.get("model"), field=f"{prefix}.target.model")
            region = _non_empty(target.get("region"), field=f"{prefix}.target.region")
            target_key = (model.casefold(), region.casefold())
            if target_key in target_keys:
                raise WebPresentationContractError(
                    f"duplicate target overlay for {model}/{region}"
                )
            target_keys.add(target_key)
            profile_id = _non_empty(
                overlay.get("skeleton_profile"),
                field=f"{prefix}.skeleton_profile",
            )
            if profile_id not in skeletons:
                raise WebPresentationContractError(
                    f"{prefix}.skeleton_profile names unknown profile {profile_id!r}"
                )
            capabilities = overlay.get("capabilities", {})
            if not isinstance(capabilities, Mapping):
                raise WebPresentationContractError(f"{prefix}.capabilities must be an object")
            normalized_capabilities = {
                "figures": capabilities.get("figures", False),
                "legacy_target_components": capabilities.get(
                    "legacy_target_components", False
                ),
            }
            if any(not isinstance(value, bool) for value in normalized_capabilities.values()):
                raise WebPresentationContractError(
                    f"{prefix}.capabilities values must be booleans"
                )
            overrides = overlay.get("contract_overrides", {})
            if not isinstance(overrides, Mapping):
                raise WebPresentationContractError(
                    f"{prefix}.contract_overrides must be an object"
                )
            forbidden = {"schema_version", "figure_targets", "presentation_layers"}
            overlap = forbidden.intersection(overrides)
            if overlap:
                raise WebPresentationContractError(
                    f"{prefix}.contract_overrides cannot own derived fields {sorted(overlap)}"
                )
            coverage = overlay.get("figure_coverage")
            if coverage is not None and not isinstance(coverage, Mapping):
                raise WebPresentationContractError(
                    f"{prefix}.figure_coverage must be an object"
                )
            if isinstance(coverage, Mapping) and "target" in coverage:
                raise WebPresentationContractError(
                    f"{prefix}.figure_coverage cannot override its overlay target"
                )
            overlay["target"] = {"model": model, "region": region}
            overlay["skeleton_profile"] = profile_id
            overlay["capabilities"] = normalized_capabilities
            overlay["contract_overrides"] = deepcopy(dict(overrides))
            overlay["figure_coverage"] = (
                deepcopy(dict(coverage)) if coverage is not None else None
            )
            overlays.append(overlay)
    return overlays


def _string_list(value: Any, *, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise WebPresentationContractError(f"{field} must be a non-empty list")
    normalized = [str(item).strip() for item in value]
    if any(not item for item in normalized) or len(normalized) != len(set(normalized)):
        raise WebPresentationContractError(
            f"{field} contains an empty or duplicate value"
        )
    return normalized


def _derived_figure_slots(
    contract: Mapping[str, Any],
    *,
    target: Mapping[str, str],
) -> list[str]:
    """Return every final-art slot declared by this resolved target skeleton."""

    from tools.component_specs.overview_instance import resolve_overview_instance

    slots: list[str] = []
    overview = contract.get("product_overview")
    if isinstance(overview, Mapping) and overview.get("source_patterns"):
        try:
            instance = resolve_overview_instance(
                model=target["model"],
                region=target["region"],
            )
        except Exception as exc:
            raise WebPresentationContractError(
                "figure-capable target has no unambiguous Overview instance: "
                f"{target['model']}/{target['region']}: {exc}"
            ) from exc
        for view in instance.get("views", []):
            if isinstance(view, Mapping):
                key = str(view.get("web_replace_key") or "").strip()
                if key:
                    slots.append(key)

    operations = contract.get("operations")
    if isinstance(operations, Mapping):
        for figure in operations.get("figures", []):
            if isinstance(figure, Mapping):
                key = str(figure.get("web_replace_key") or "").strip()
                if key:
                    slots.append(key)

    references = contract.get("reference_figures")
    if isinstance(references, Mapping):
        for figure in references.get("figures", []):
            if not isinstance(figure, Mapping):
                continue
            identifier = str(figure.get("id") or "").casefold()
            image_key = str(figure.get("image_key") or "").casefold()
            if not (
                identifier.startswith("charging-")
                or image_key.startswith("charging/")
            ):
                continue
            key = str(figure.get("web_replace_key") or "").strip()
            if key:
                slots.append(key)

    if len(slots) != len(set(slots)):
        raise WebPresentationContractError(
            f"figure-capable target has duplicate derived slots: {target['model']}/"
            f"{target['region']}"
        )
    return slots


def _normalize_coverage_policy(
    overlay: Mapping[str, Any],
    *,
    resolved_contract: Mapping[str, Any],
) -> dict[str, Any] | None:
    prefix = f"target_overlays.{overlay['overlay_id']}.figure_coverage"
    coverage = overlay.get("figure_coverage")
    figures_enabled = bool(overlay["capabilities"]["figures"])
    if not isinstance(coverage, Mapping):
        if figures_enabled:
            raise WebPresentationContractError(
                f"{prefix}: figures=true requires figure_coverage"
            )
        return None
    if "known_debt" in coverage:
        raise WebPresentationContractError(
            f"{prefix}.known_debt must live in the figure debt baseline"
        )
    policy_id = _non_empty(coverage.get("policy_id"), field=f"{prefix}.policy_id")
    locales = [
        locale.casefold()
        for locale in _string_list(coverage.get("locales"), field=f"{prefix}.locales")
    ]
    if len(locales) != len(set(locales)):
        raise WebPresentationContractError(f"{prefix}.locales contains duplicates")
    required_slots = _string_list(
        coverage.get("required_slots"), field=f"{prefix}.required_slots"
    )
    allowed_statuses = _string_list(
        coverage.get("allowed_statuses"), field=f"{prefix}.allowed_statuses"
    )
    if tuple(allowed_statuses) != _FINISHED_FIGURE_STATUSES:
        raise WebPresentationContractError(
            f"{prefix}.allowed_statuses must contain only finished artwork: "
            f"{list(_FINISHED_FIGURE_STATUSES)}"
        )
    if figures_enabled:
        derived = _derived_figure_slots(resolved_contract, target=overlay["target"])
        missing = [slot for slot in derived if slot not in required_slots]
        extra = [slot for slot in required_slots if slot not in derived]
        if missing or extra:
            raise WebPresentationContractError(
                f"{prefix}.required_slots are incomplete or out of scope; "
                f"missing={missing}, extra={extra}"
            )
    return {
        "policy_id": policy_id,
        "locales": locales,
        "required_slots": required_slots,
        "allowed_statuses": allowed_statuses,
    }


def _load_figure_debt(
    root: Path,
    raw_path: Any,
    *,
    overlays: list[dict[str, Any]],
) -> dict[tuple[str, str], list[dict[str, str]]]:
    path = _layer_path(root, raw_path, field="figure_debt_baseline")
    payload = _read_mapping(path, field="figure debt baseline")
    if payload.get("schema_version") != FIGURE_DEBT_SCHEMA_VERSION:
        raise WebPresentationContractError(
            f"unsupported figure debt baseline schema in {path}"
        )
    raw_targets = payload.get("targets")
    if not isinstance(raw_targets, list):
        raise WebPresentationContractError(f"{path}: targets must be a list")
    overlay_by_target = {
        (
            str(overlay["target"]["model"]).casefold(),
            str(overlay["target"]["region"]).casefold(),
        ): overlay
        for overlay in overlays
    }
    result: dict[tuple[str, str], list[dict[str, str]]] = {}
    for index, raw_target in enumerate(raw_targets):
        prefix = f"{path}: targets[{index}]"
        if not isinstance(raw_target, Mapping):
            raise WebPresentationContractError(f"{prefix} must be an object")
        target = raw_target.get("target")
        if not isinstance(target, Mapping):
            raise WebPresentationContractError(f"{prefix}.target must be an object")
        model = _non_empty(target.get("model"), field=f"{prefix}.target.model")
        region = _non_empty(target.get("region"), field=f"{prefix}.target.region")
        target_key = (model.casefold(), region.casefold())
        if target_key in result:
            raise WebPresentationContractError(
                f"duplicate figure debt baseline target {model}/{region}"
            )
        overlay = overlay_by_target.get(target_key)
        if overlay is None:
            raise WebPresentationContractError(
                f"figure debt baseline target {model}/{region} has no target overlay"
            )
        coverage = overlay.get("figure_coverage")
        if not isinstance(coverage, Mapping):
            raise WebPresentationContractError(
                f"figure debt baseline target {model}/{region} has no coverage policy"
            )
        policy_id = _non_empty(raw_target.get("policy_id"), field=f"{prefix}.policy_id")
        if policy_id != coverage["policy_id"]:
            raise WebPresentationContractError(
                f"{prefix}.policy_id does not match target coverage policy"
            )
        raw_debt = raw_target.get("known_debt")
        if not isinstance(raw_debt, list):
            raise WebPresentationContractError(f"{prefix}.known_debt must be a list")
        normalized: list[dict[str, str]] = []
        identities: set[tuple[str, str]] = set()
        for debt_index, raw_entry in enumerate(raw_debt):
            debt_prefix = f"{prefix}.known_debt[{debt_index}]"
            if not isinstance(raw_entry, Mapping):
                raise WebPresentationContractError(f"{debt_prefix} must be an object")
            locale = _non_empty(raw_entry.get("locale"), field=f"{debt_prefix}.locale").casefold()
            slot_id = _non_empty(raw_entry.get("slot_id"), field=f"{debt_prefix}.slot_id")
            status = _non_empty(raw_entry.get("status"), field=f"{debt_prefix}.status")
            if locale not in coverage["locales"]:
                raise WebPresentationContractError(
                    f"{debt_prefix}.locale is outside the coverage policy"
                )
            if slot_id not in coverage["required_slots"]:
                raise WebPresentationContractError(
                    f"{debt_prefix}.slot_id is outside the coverage policy"
                )
            if status not in _DEBT_FIGURE_STATUSES:
                raise WebPresentationContractError(
                    f"{debt_prefix}.status must be editable-fallback or missing"
                )
            identity = (locale, slot_id)
            if identity in identities:
                raise WebPresentationContractError(
                    f"{prefix}.known_debt repeats {locale}/{slot_id}"
                )
            identities.add(identity)
            normalized.append(
                {"locale": locale, "slot_id": slot_id, "status": status}
            )
        result[target_key] = normalized
    return result


def _coverage_requirement(overlay: Mapping[str, Any]) -> dict[str, Any] | None:
    coverage = overlay.get("figure_coverage")
    if not isinstance(coverage, Mapping):
        return None
    return {
        "target": deepcopy(dict(overlay["target"])),
        **deepcopy(dict(coverage)),
    }


def _finalize_contract(
    contract: dict[str, Any],
    *,
    base_id: str,
    skeleton_profile: str | None,
    target_overlay: Mapping[str, Any] | None,
    figure_targets: list[dict[str, str]],
    legacy_targets: list[dict[str, str]],
    coverage_requirements: list[dict[str, Any]],
) -> dict[str, Any]:
    finalized = deepcopy(contract)
    finalized["schema_version"] = CONTRACT_SCHEMA_VERSION
    finalized["figure_targets"] = deepcopy(figure_targets)
    preface = finalized.get("preface")
    if not isinstance(preface, Mapping):
        raise WebPresentationContractError("resolved contract.preface must be an object")
    finalized["preface"] = {**deepcopy(dict(preface)), "targets": deepcopy(legacy_targets)}
    figure_coverage = finalized.get("figure_coverage", {})
    if not isinstance(figure_coverage, Mapping):
        raise WebPresentationContractError(
            "resolved contract.figure_coverage must be an object"
        )
    finalized["figure_coverage"] = {
        **deepcopy(dict(figure_coverage)),
        "requirements": deepcopy(coverage_requirements),
    }
    finalized["presentation_layers"] = {
        "base": base_id,
        "skeleton_profile": skeleton_profile,
        "target_overlay": (
            str(target_overlay["overlay_id"]) if target_overlay is not None else None
        ),
    }
    return finalized


def _matches_target(overlay: Mapping[str, Any], *, model: str, region: str) -> bool:
    target = overlay["target"]
    return (
        str(target["model"]).casefold() == model.casefold()
        and str(target["region"]).casefold() == region.casefold()
    )


@lru_cache(maxsize=16)
def _load_cached(path_text: str, model: str, region: str) -> dict[str, Any]:
    path = Path(path_text)
    entry = _read_mapping(path, field="web manual contract")
    if entry.get("schema_version") == LEGACY_CONTRACT_SCHEMA_VERSION:
        return deepcopy(entry)
    if entry.get("schema_version") != STACK_SCHEMA_VERSION:
        raise WebPresentationContractError(f"unsupported web manual contract schema in {path}")
    if bool(model) != bool(region):
        raise WebPresentationContractError("model and region must be supplied together")

    root = path.parent.resolve(strict=False)
    base_id, base = _load_base(root, entry.get("shared_base"))
    skeletons = _load_skeletons(root, entry.get("skeleton_profiles"))
    overlays = _load_target_overlays(
        root,
        entry.get("target_overlays"),
        skeletons=skeletons,
    )
    policy_ids: set[str] = set()
    for overlay in overlays:
        profile_id = str(overlay["skeleton_profile"])
        resolved_overlay = merge_contract_layers(
            base,
            skeletons[profile_id],
            field=f"skeleton_profiles.{profile_id}",
        )
        resolved_overlay = merge_contract_layers(
            resolved_overlay,
            overlay["contract_overrides"],
            field=f"target_overlays.{overlay['overlay_id']}.contract_overrides",
        )
        coverage = _normalize_coverage_policy(
            overlay,
            resolved_contract=resolved_overlay,
        )
        if coverage is not None:
            if coverage["policy_id"] in policy_ids:
                raise WebPresentationContractError(
                    f"duplicate figure coverage policy_id {coverage['policy_id']!r}"
                )
            policy_ids.add(coverage["policy_id"])
        overlay["figure_coverage"] = coverage
    debt_by_target = _load_figure_debt(
        root,
        entry.get("figure_debt_baseline"),
        overlays=overlays,
    )
    for overlay in overlays:
        coverage = overlay.get("figure_coverage")
        if not isinstance(coverage, dict):
            continue
        key = (
            str(overlay["target"]["model"]).casefold(),
            str(overlay["target"]["region"]).casefold(),
        )
        coverage["known_debt"] = deepcopy(debt_by_target.get(key, []))

    if model and region:
        matches = [
            overlay
            for overlay in overlays
            if _matches_target(overlay, model=model, region=region)
        ]
        if len(matches) > 1:
            raise WebPresentationContractError(
                f"multiple target overlays match {model}/{region}"
            )
        if not matches:
            return _finalize_contract(
                base,
                base_id=base_id,
                skeleton_profile=None,
                target_overlay=None,
                figure_targets=[],
                legacy_targets=[],
                coverage_requirements=[],
            )
        overlay = matches[0]
        profile_id = str(overlay["skeleton_profile"])
        resolved = merge_contract_layers(
            base,
            skeletons[profile_id],
            field=f"skeleton_profiles.{profile_id}",
        )
        resolved = merge_contract_layers(
            resolved,
            overlay["contract_overrides"],
            field=f"target_overlays.{overlay['overlay_id']}.contract_overrides",
        )
        target = deepcopy(dict(overlay["target"]))
        capabilities = overlay["capabilities"]
        coverage = _coverage_requirement(overlay)
        return _finalize_contract(
            resolved,
            base_id=base_id,
            skeleton_profile=profile_id,
            target_overlay=overlay,
            figure_targets=[target] if capabilities["figures"] else [],
            legacy_targets=(
                [target] if capabilities["legacy_target_components"] else []
            ),
            coverage_requirements=[coverage] if coverage is not None else [],
        )

    compatibility_profile = _non_empty(
        entry.get("compatibility_skeleton_profile"),
        field="compatibility_skeleton_profile",
    )
    if compatibility_profile not in skeletons:
        raise WebPresentationContractError(
            "compatibility_skeleton_profile names unknown profile "
            f"{compatibility_profile!r}"
        )
    resolved = merge_contract_layers(
        base,
        skeletons[compatibility_profile],
        field=f"skeleton_profiles.{compatibility_profile}",
    )
    figure_targets = [
        deepcopy(dict(overlay["target"]))
        for overlay in overlays
        if overlay["capabilities"]["figures"]
    ]
    legacy_targets = [
        deepcopy(dict(overlay["target"]))
        for overlay in overlays
        if overlay["capabilities"]["legacy_target_components"]
    ]
    coverage_requirements = [
        requirement
        for overlay in overlays
        if (requirement := _coverage_requirement(overlay)) is not None
    ]
    return _finalize_contract(
        resolved,
        base_id=base_id,
        skeleton_profile=compatibility_profile,
        target_overlay=None,
        figure_targets=figure_targets,
        legacy_targets=legacy_targets,
        coverage_requirements=coverage_requirements,
    )


def load_web_presentation_contract(
    path: Path,
    *,
    model: str | None = None,
    region: str | None = None,
) -> dict[str, Any]:
    resolved = path.resolve(strict=False)
    return deepcopy(
        _load_cached(
            str(resolved),
            str(model or "").strip(),
            str(region or "").strip(),
        )
    )


__all__ = [
    "BASE_SCHEMA_VERSION",
    "CONTRACT_SCHEMA_VERSION",
    "FIGURE_DEBT_SCHEMA_VERSION",
    "SKELETON_SCHEMA_VERSION",
    "STACK_SCHEMA_VERSION",
    "TARGET_OVERLAYS_SCHEMA_VERSION",
    "WebPresentationContractError",
    "load_web_presentation_contract",
    "merge_contract_layers",
]
