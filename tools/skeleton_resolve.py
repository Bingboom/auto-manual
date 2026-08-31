#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resolve a Skeleton Blueprint into a Resolved Manifest (generate-then-verify).

Three-layer contract (skeleton library, slice S1):

1. Skeleton Blueprint  — ``docs/manifests/skeletons/<cell>/blueprint.yaml``
   owns the stable slot universe, named order profiles, requirement
   (required | optional | capability:<name>), presentation, and semantic
   co-page pairs. No languages, regions, targets, or paths.
2. Product Manual Plan — the in-memory resolution of blueprint x slot
   templates x region profile x optional target plan x language set (dump
   with ``plan``). A target plan selects a declared house-style/order profile,
   optional front/body slots, and terminal slots; it never adds page logic.
3. Resolved Manifest   — the committed ``docs/manifests/manual_*.yaml`` the
   whole pipeline keeps reading. YAML stays the compatibility surface: this
   tool only ever writes the manifest the repository already committed, and
   ``verify`` asserts emitted == committed bytes.

Resolution precedence (fixed): blueprint slots/order profile -> product-plan
optional/terminal selection -> capability annotation (from the slot
requirement; the actual gate stays at build time in
``filter_pages_by_capability``) -> house-style carrier variant -> region
profile (language set, slot overrides, compliance mounting rows) -> language
expansion (``front``/``back`` slots emit once, ``body`` slots emit once per
language in declaration order). Region-profile ``terminal_slots`` remains the
legacy compatibility path when no product-plan selection is supplied.

Contract guard: this module must stay free of slot-specific or region-specific
literals. Every slot decision must trace to one of the declared data carriers;
adding a branch keyed on a particular slot or region here is the
template-clone failure mode reborn, and is a review-rejection criterion.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

_REPO_ROOT = bootstrap_repo_root(__file__, parent_count=1)

_BLUEPRINT_SCHEMA = "skeleton-blueprint/v1"
_SLOT_TEMPLATES_SCHEMA = "skeleton-slot-templates/v1"
_REGION_PROFILE_SCHEMA = "skeleton-region-profile/v1"
_PRODUCT_PLAN_SCHEMA = "skeleton-product-plan/v1"

_BLOCKS = ("front", "body", "back")
_PRESENTATIONS = ("chapter", "subsection", "titled_not_in_toc", "untitled_block")
_SLOT_KEYS = {"slot_id", "block", "requirement", "presentation", "toc"}
_CARRIER_KEYS = {
    "type", "file", "lang", "lang_blocks", "ordinal_neutral",
    "page", "source", "engine", "recipe", "template", "include_dir",
}
_OVERRIDE_KEYS = {"file", "recipe", "template"}
_COMPLIANCE_KEYS = {
    "fragment", "carrier", "file", "mount_after", "repeat_per_language", "presentation",
}
_PRODUCT_PLAN_KEYS = {"house_style_version", "enabled_optional_slots", "terminal_slots"}


class SkeletonResolveError(RuntimeError):
    pass


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        raise SkeletonResolveError("PyYAML not installed. Please run: pip install pyyaml") from exc
    if not path.exists():
        raise SkeletonResolveError(f"carrier not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SkeletonResolveError(f"carrier root must be a mapping: {path}")
    return data


def _require_schema(data: dict[str, Any], expected: str, path: Path) -> None:
    actual = data.get("schema_version")
    if actual != expected:
        raise SkeletonResolveError(
            f"{path}: schema_version must be {expected!r}, got {actual!r}"
        )


def _substitute(value: str, *, lang: str, primary_lang: str) -> str:
    # Only the two resolver tokens are substituted; ``{model}`` and friends
    # pass through verbatim for the build-time page pipeline.
    return value.replace("{lang}", lang).replace("{primary_lang}", primary_lang)


def load_blueprint(path: Path) -> dict[str, Any]:
    data = _load_yaml(path)
    _require_schema(data, _BLUEPRINT_SCHEMA, path)
    slots_raw = data.get("slots")
    if not isinstance(slots_raw, list) or not slots_raw:
        raise SkeletonResolveError(f"{path}: slots must be a non-empty list")
    seen: set[str] = set()
    for idx, slot in enumerate(slots_raw, start=1):
        if not isinstance(slot, dict):
            raise SkeletonResolveError(f"{path}: slots[{idx}] must be a mapping")
        unknown = sorted(set(slot) - _SLOT_KEYS)
        if unknown:
            raise SkeletonResolveError(
                f"{path}: slots[{idx}] has unsupported fields: {', '.join(unknown)}"
            )
        slot_id = slot.get("slot_id")
        if not isinstance(slot_id, str) or not slot_id.strip():
            raise SkeletonResolveError(f"{path}: slots[{idx}].slot_id must be a non-empty string")
        if slot_id in seen:
            raise SkeletonResolveError(f"{path}: duplicate slot_id: {slot_id}")
        seen.add(slot_id)
        if slot.get("block") not in _BLOCKS:
            raise SkeletonResolveError(
                f"{path}: slots[{idx}].block must be one of {_BLOCKS}"
            )
        requirement = slot.get("requirement")
        if not isinstance(requirement, str) or not (
            requirement in {"required", "optional"}
            or requirement.startswith("capability:")
        ):
            raise SkeletonResolveError(
                f"{path}: slots[{idx}].requirement must be "
                "required | optional | capability:<name>"
            )
        if requirement.startswith("capability:") and not requirement.split(":", 1)[1].strip():
            raise SkeletonResolveError(
                f"{path}: slots[{idx}].requirement capability name must be non-empty"
            )
        if slot.get("presentation") not in _PRESENTATIONS:
            raise SkeletonResolveError(
                f"{path}: slots[{idx}].presentation must be one of {_PRESENTATIONS}"
            )
        if not isinstance(slot.get("toc"), bool):
            raise SkeletonResolveError(f"{path}: slots[{idx}].toc must be a boolean")
    groups = data.get("co_page_groups", [])
    if not isinstance(groups, list):
        raise SkeletonResolveError(f"{path}: co_page_groups must be a list")
    for group in groups:
        if not isinstance(group, list) or not all(isinstance(i, str) for i in group):
            raise SkeletonResolveError(f"{path}: co_page_groups entries must be lists of slot ids")
        missing = sorted(set(group) - seen)
        if missing:
            raise SkeletonResolveError(
                f"{path}: co_page_groups references unknown slots: {', '.join(missing)}"
            )
    order_profiles = data.get("order_profiles", {})
    if not isinstance(order_profiles, dict):
        raise SkeletonResolveError(f"{path}: order_profiles must be a mapping")
    default_profile = data.get("default_order_profile")
    if order_profiles:
        if not isinstance(default_profile, str) or default_profile not in order_profiles:
            raise SkeletonResolveError(
                f"{path}: default_order_profile must name one declared order profile"
            )
    elif default_profile is not None:
        raise SkeletonResolveError(
            f"{path}: default_order_profile requires declared order_profiles"
        )
    blocks_by_id = {slot["slot_id"]: slot["block"] for slot in slots_raw}
    for profile_name, order in order_profiles.items():
        if not isinstance(profile_name, str) or not profile_name.strip():
            raise SkeletonResolveError(f"{path}: order profile names must be non-empty strings")
        if not isinstance(order, list) or not all(
            isinstance(item, str) and item.strip() for item in order
        ):
            raise SkeletonResolveError(
                f"{path}: order_profiles.{profile_name} must be a list of slot ids"
            )
        if len(order) != len(set(order)):
            raise SkeletonResolveError(
                f"{path}: order_profiles.{profile_name} contains duplicate slot ids"
            )
        missing = sorted(seen - set(order))
        unknown = sorted(set(order) - seen)
        if missing or unknown:
            raise SkeletonResolveError(
                f"{path}: order_profiles.{profile_name} must contain the complete slot "
                f"universe (missing={missing}, unknown={unknown})"
            )
        block_positions = [_BLOCKS.index(blocks_by_id[slot_id]) for slot_id in order]
        if block_positions != sorted(block_positions):
            raise SkeletonResolveError(
                f"{path}: order_profiles.{profile_name} must preserve front/body/back "
                "block order"
            )
    return data


def load_slot_template_catalog(
    path: Path,
    blueprint: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, dict[str, Any]]]]:
    data = _load_yaml(path)
    _require_schema(data, _SLOT_TEMPLATES_SCHEMA, path)
    slots_raw = data.get("slots")
    if not isinstance(slots_raw, dict):
        raise SkeletonResolveError(f"{path}: slots must be a mapping")
    blueprint_ids = {slot["slot_id"] for slot in blueprint["slots"]}
    unknown = sorted(set(slots_raw) - blueprint_ids)
    if unknown:
        raise SkeletonResolveError(
            f"{path}: maps slots absent from the blueprint: {', '.join(unknown)}"
        )
    missing = sorted(blueprint_ids - set(slots_raw))
    if missing:
        raise SkeletonResolveError(
            f"{path}: blueprint slots without a carrier mapping: {', '.join(missing)}"
        )
    blocks = {slot["slot_id"]: slot["block"] for slot in blueprint["slots"]}
    for slot_id, carrier in slots_raw.items():
        if not isinstance(carrier, dict):
            raise SkeletonResolveError(f"{path}: slots.{slot_id} must be a mapping")
        bad = sorted(set(carrier) - _CARRIER_KEYS)
        if bad:
            raise SkeletonResolveError(
                f"{path}: slots.{slot_id} has unsupported fields: {', '.join(bad)}"
            )
        # 'lang' is documentation of the front/back single-emission fact, not a
        # control: entry languages always come from the block expansion. Reject
        # it anywhere it would read as a control and be silently ignored.
        lang_value = carrier.get("lang")
        if lang_value is not None:
            if blocks.get(slot_id) == "body":
                raise SkeletonResolveError(
                    f"{path}: slots.{slot_id}: 'lang' is not allowed on body slots "
                    "(body slots expand once per language; the key would be ignored)"
                )
            if lang_value != "primary":
                raise SkeletonResolveError(
                    f"{path}: slots.{slot_id}: 'lang' only supports 'primary'"
                )
    style_profiles = data.get("house_style_versions", {})
    if not isinstance(style_profiles, dict):
        raise SkeletonResolveError(f"{path}: house_style_versions must be a mapping")
    declared_profiles = set((blueprint.get("order_profiles") or {}).keys())
    unknown_profiles = sorted(set(style_profiles) - declared_profiles)
    if unknown_profiles:
        raise SkeletonResolveError(
            f"{path}: house_style_versions references undeclared order profiles: "
            f"{', '.join(unknown_profiles)}"
        )
    for profile_name, overrides in style_profiles.items():
        if not isinstance(overrides, dict):
            raise SkeletonResolveError(
                f"{path}: house_style_versions.{profile_name} must be a mapping"
            )
        for slot_id, override in overrides.items():
            if slot_id not in blueprint_ids:
                raise SkeletonResolveError(
                    f"{path}: house_style_versions.{profile_name} references unknown "
                    f"slot: {slot_id}"
                )
            if not isinstance(override, dict):
                raise SkeletonResolveError(
                    f"{path}: house_style_versions.{profile_name}.{slot_id} must be a mapping"
                )
            bad = sorted(set(override) - _OVERRIDE_KEYS)
            if bad:
                raise SkeletonResolveError(
                    f"{path}: house_style_versions.{profile_name}.{slot_id} has "
                    f"unsupported fields: {', '.join(bad)}"
                )
    return slots_raw, style_profiles


def load_slot_templates(path: Path, blueprint: dict[str, Any]) -> dict[str, dict[str, Any]]:
    slots, _ = load_slot_template_catalog(path, blueprint)
    return slots


def load_slot_template_profiles(
    path: Path,
    blueprint: dict[str, Any],
) -> dict[str, dict[str, dict[str, Any]]]:
    _, profiles = load_slot_template_catalog(path, blueprint)
    return profiles


def load_region_profile(path: Path, blueprint: dict[str, Any]) -> dict[str, Any]:
    data = _load_yaml(path)
    _require_schema(data, _REGION_PROFILE_SCHEMA, path)
    language_set = data.get("language_set")
    if not isinstance(language_set, list) or not language_set or not all(
        isinstance(item, str) and item.strip() for item in language_set
    ):
        raise SkeletonResolveError(f"{path}: language_set must be a non-empty list of strings")
    if len(set(language_set)) != len(language_set):
        raise SkeletonResolveError(
            f"{path}: language_set contains duplicates: {language_set}"
        )
    primary = data.get("primary_lang")
    if not isinstance(primary, str) or primary not in language_set:
        raise SkeletonResolveError(f"{path}: primary_lang must be a member of language_set")
    blueprint_ids = {slot["slot_id"] for slot in blueprint["slots"]}
    back_ids = {
        slot["slot_id"] for slot in blueprint["slots"] if slot["block"] == "back"
    }
    terminal_slots = data.get("terminal_slots")
    if terminal_slots is not None:
        if not isinstance(terminal_slots, list) or not all(
            isinstance(item, str) and item.strip() for item in terminal_slots
        ):
            raise SkeletonResolveError(
                f"{path}: terminal_slots must be a list of non-empty strings"
            )
        if len(set(terminal_slots)) != len(terminal_slots):
            raise SkeletonResolveError(
                f"{path}: terminal_slots contains duplicates: {terminal_slots}"
            )
        non_terminal = sorted(set(terminal_slots) - back_ids)
        if non_terminal:
            raise SkeletonResolveError(
                f"{path}: terminal_slots references non-back or unknown slots: "
                f"{', '.join(non_terminal)}"
            )
    overrides = data.get("slot_overrides", {})
    if not isinstance(overrides, dict):
        raise SkeletonResolveError(f"{path}: slot_overrides must be a mapping")
    for slot_id, override in overrides.items():
        if slot_id not in blueprint_ids:
            raise SkeletonResolveError(
                f"{path}: slot_overrides references unknown slot: {slot_id}"
            )
        if not isinstance(override, dict):
            raise SkeletonResolveError(f"{path}: slot_overrides.{slot_id} must be a mapping")
        bad = sorted(set(override) - _OVERRIDE_KEYS)
        if bad:
            raise SkeletonResolveError(
                f"{path}: slot_overrides.{slot_id} has unsupported fields: {', '.join(bad)}"
            )
    compliance = data.get("compliance", [])
    if not isinstance(compliance, list):
        raise SkeletonResolveError(f"{path}: compliance must be a list")
    for idx, row in enumerate(compliance, start=1):
        if not isinstance(row, dict):
            raise SkeletonResolveError(f"{path}: compliance[{idx}] must be a mapping")
        bad = sorted(set(row) - _COMPLIANCE_KEYS)
        if bad:
            raise SkeletonResolveError(
                f"{path}: compliance[{idx}] has unsupported fields: {', '.join(bad)}"
            )
        for field in ("fragment", "carrier", "file", "mount_after"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise SkeletonResolveError(
                    f"{path}: compliance[{idx}].{field} must be a non-empty string"
                )
        if row["carrier"] != "rst_include":
            raise SkeletonResolveError(
                f"{path}: compliance[{idx}].carrier only supports rst_include today"
            )
        if row["mount_after"] not in blueprint_ids:
            raise SkeletonResolveError(
                f"{path}: compliance[{idx}].mount_after references unknown slot: {row['mount_after']}"
            )
        if row["fragment"] in blueprint_ids:
            raise SkeletonResolveError(
                f"{path}: compliance[{idx}].fragment '{row['fragment']}' collides with a "
                "blueprint slot id (emitted slot_ids would duplicate)"
            )
    return data


def _string_list(value: Any, *, label: str) -> list[str]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise SkeletonResolveError(f"{label} must be a list of non-empty strings")
    if len(value) != len(set(value)):
        raise SkeletonResolveError(f"{label} contains duplicates: {value}")
    return list(value)


def _normalize_product_plan(
    blueprint: dict[str, Any],
    product_plan: dict[str, Any] | None,
) -> dict[str, Any]:
    """Validate target-owned selections without introducing target branches.

    An absent plan intentionally resolves the blueprint's required/capability
    core and its declared default order. Optional front/body slots stay absent;
    optional back slots require an explicit terminal selection. This gives a
    skeleton a safe, target-neutral anchor while real targets add only data.
    """

    raw = dict(product_plan or {})
    unknown = sorted(set(raw) - _PRODUCT_PLAN_KEYS)
    if unknown:
        raise SkeletonResolveError(
            f"product plan has unsupported fields: {', '.join(unknown)}"
        )

    order_profiles = blueprint.get("order_profiles") or {}
    style_version = raw.get("house_style_version")
    if style_version is None:
        style_version = blueprint.get("default_order_profile")
    if style_version is not None and (
        not isinstance(style_version, str) or style_version not in order_profiles
    ):
        raise SkeletonResolveError(
            "product plan house_style_version must name a declared order profile"
        )

    enabled = _string_list(
        raw.get("enabled_optional_slots", []),
        label="product plan enabled_optional_slots",
    )
    slots_by_id = {slot["slot_id"]: slot for slot in blueprint["slots"]}
    optional_ids = {
        slot_id
        for slot_id, slot in slots_by_id.items()
        if slot["requirement"] == "optional"
    }
    invalid_enabled = sorted(set(enabled) - optional_ids)
    if invalid_enabled:
        raise SkeletonResolveError(
            "product plan enabled_optional_slots references required, capability, "
            f"or unknown slots: {', '.join(invalid_enabled)}"
        )
    enabled_back = sorted(
        slot_id for slot_id in enabled if slots_by_id[slot_id]["block"] == "back"
    )
    if enabled_back:
        raise SkeletonResolveError(
            "product plan back slots must be selected only through terminal_slots: "
            f"{', '.join(enabled_back)}"
        )

    terminal_slots: list[str] | None = None
    if "terminal_slots" in raw:
        terminal_slots = _string_list(
            raw["terminal_slots"],
            label="product plan terminal_slots",
        )
        back_ids = {
            slot_id for slot_id, slot in slots_by_id.items() if slot["block"] == "back"
        }
        invalid_terminal = sorted(set(terminal_slots) - back_ids)
        if invalid_terminal:
            raise SkeletonResolveError(
                "product plan terminal_slots references non-back or unknown slots: "
                f"{', '.join(invalid_terminal)}"
            )

    return {
        "house_style_version": style_version,
        "enabled_optional_slots": enabled,
        "terminal_slots": terminal_slots,
    }


def load_product_plan(path: Path, blueprint: dict[str, Any]) -> dict[str, Any]:
    """Load a target data carrier for the Python resolver API.

    The public CLI surface intentionally stays unchanged in R3b. A later target
    slice may pass this normalized mapping from its target-registration layer.
    """

    data = _load_yaml(path)
    _require_schema(data, _PRODUCT_PLAN_SCHEMA, path)
    plan_id = data.get("plan_id")
    if not isinstance(plan_id, str) or not plan_id.strip():
        raise SkeletonResolveError(f"{path}: plan_id must be a non-empty string")
    allowed = {"schema_version", "plan_id", *_PRODUCT_PLAN_KEYS}
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise SkeletonResolveError(
            f"{path}: product plan has unsupported fields: {', '.join(unknown)}"
        )
    normalized = _normalize_product_plan(
        blueprint,
        {key: data[key] for key in _PRODUCT_PLAN_KEYS if key in data},
    )
    return {key: value for key, value in normalized.items() if value is not None}


def _merged_carrier(
    slot_id: str,
    slot_templates: dict[str, dict[str, Any]],
    profile: dict[str, Any],
    *,
    style_overrides: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    merged = dict(slot_templates[slot_id])
    style_override = style_overrides.get(slot_id, {})
    merged.update({k: v for k, v in style_override.items() if v is not None})
    override = (profile.get("slot_overrides") or {}).get(slot_id, {})
    merged.update({k: v for k, v in override.items() if v is not None})
    return merged


def _capability_of(slot: dict[str, Any]) -> str | None:
    requirement = slot["requirement"]
    if requirement.startswith("capability:"):
        return requirement.split(":", 1)[1].strip()
    return None


def _entry_for(
    slot: dict[str, Any],
    carrier: dict[str, Any],
    *,
    slot_id: str,
    lang: str,
    primary_lang: str,
) -> dict[str, Any]:
    page_type = carrier.get("type")
    capability = _capability_of(slot)
    if page_type == "cover_pdf":
        file_value = carrier.get("file")
        if not isinstance(file_value, str) or not file_value.strip():
            raise SkeletonResolveError(f"slot {slot['slot_id']}: cover_pdf carrier requires file")
        entry: dict[str, Any] = {"type": page_type, "slot_id": slot_id, "file": file_value}
    elif page_type == "rst_include":
        file_value = carrier.get("file")
        if not isinstance(file_value, str) or not file_value.strip():
            raise SkeletonResolveError(
                f"slot {slot['slot_id']}: rst_include carrier requires file "
                "(family template missing and no region override supplied)"
            )
        entry = {
            "type": page_type,
            "slot_id": slot_id,
            "lang": lang,
            "file": _substitute(file_value, lang=lang, primary_lang=primary_lang),
        }
        if carrier.get("lang_blocks"):
            entry["lang_blocks"] = True
        if carrier.get("ordinal_neutral"):
            entry["ordinal_neutral"] = True
    elif page_type == "csv_page":
        page_value = carrier.get("page")
        if not isinstance(page_value, str) or not page_value.strip():
            raise SkeletonResolveError(f"slot {slot['slot_id']}: csv_page carrier requires page")
        entry = {
            "type": page_type,
            "slot_id": slot_id,
            "source": str(carrier.get("source", "phase2")),
            "page": page_value,
            "langs": [lang],
            "include_dir": carrier.get("include_dir"),
        }
    elif page_type == "generated_page":
        entry = {
            "type": page_type,
            "slot_id": slot_id,
            "page": carrier.get("page"),
            "engine": carrier.get("engine"),
            "recipe": carrier.get("recipe"),
            "template": carrier.get("template"),
            "langs": [lang],
            "include_dir": carrier.get("include_dir"),
        }
        for field in ("page", "engine", "recipe", "template"):
            if not isinstance(entry[field], str) or not entry[field].strip():
                raise SkeletonResolveError(
                    f"slot {slot['slot_id']}: generated_page carrier requires {field} "
                    "(per-line fields come from the region profile)"
                )
        entry["recipe"] = _substitute(entry["recipe"], lang=lang, primary_lang=primary_lang)
        entry["template"] = _substitute(entry["template"], lang=lang, primary_lang=primary_lang)
    else:
        raise SkeletonResolveError(
            f"slot {slot['slot_id']}: unsupported carrier type: {page_type!r}"
        )
    if capability:
        entry["capability"] = capability
    return entry


def resolve_plan(
    blueprint: dict[str, Any],
    slot_templates: dict[str, dict[str, Any]],
    profile: dict[str, Any],
    *,
    manifest_id: str,
    product_plan: dict[str, Any] | None = None,
    slot_template_profiles: dict[str, dict[str, dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    if (blueprint.get("order_profiles") or {}) and slot_template_profiles is None:
        raise SkeletonResolveError(
            "declared order profiles require the slot-template profile catalog; "
            "load both with load_slot_template_catalog"
        )
    selection = _normalize_product_plan(blueprint, product_plan)
    style_version = selection["house_style_version"]
    style_overrides = (slot_template_profiles or {}).get(style_version, {})
    primary_lang = profile["primary_lang"]
    language_set = list(profile["language_set"])
    compliance_by_anchor: dict[str, list[dict[str, Any]]] = {}
    for row in profile.get("compliance", []):
        compliance_by_anchor.setdefault(row["mount_after"], []).append(row)

    pages: list[dict[str, Any]] = []

    def emit_slot(slot: dict[str, Any], *, lang: str, qualified: bool) -> None:
        slot_id = slot["slot_id"]
        entry_slot_id = f"{slot_id}_{lang}" if qualified else slot_id
        carrier = _merged_carrier(
            slot_id,
            slot_templates,
            profile,
            style_overrides=style_overrides,
        )
        pages.append(
            _entry_for(slot, carrier, slot_id=entry_slot_id, lang=lang, primary_lang=primary_lang)
        )
        for row in compliance_by_anchor.get(slot_id, []):
            if not row.get("repeat_per_language", False) and lang != primary_lang:
                continue
            pages.append(
                {
                    "type": row["carrier"],
                    "slot_id": f"{row['fragment']}_{lang}",
                    "lang": lang,
                    "file": _substitute(row["file"], lang=lang, primary_lang=primary_lang),
                }
            )

    slots_by_id = {slot["slot_id"]: slot for slot in blueprint["slots"]}
    order = (
        blueprint["order_profiles"][style_version]
        if style_version is not None
        else [slot["slot_id"] for slot in blueprint["slots"]]
    )
    ordered_slots = [slots_by_id[slot_id] for slot_id in order]
    enabled_optional = set(selection["enabled_optional_slots"])

    def selected_front_or_body(slot: dict[str, Any]) -> bool:
        return slot["requirement"] != "optional" or slot["slot_id"] in enabled_optional

    front = [
        slot
        for slot in ordered_slots
        if slot["block"] == "front" and selected_front_or_body(slot)
    ]
    body = [
        slot
        for slot in ordered_slots
        if slot["block"] == "body" and selected_front_or_body(slot)
    ]
    back = [slot for slot in ordered_slots if slot["block"] == "back"]
    terminal_slots = selection["terminal_slots"]
    if terminal_slots is None and "terminal_slots" in profile:
        terminal_slots = list(profile["terminal_slots"])
    if terminal_slots is not None:
        terminal_set = set(terminal_slots)
        back = [slot for slot in back if slot["slot_id"] in terminal_set]
    else:
        back = [slot for slot in back if slot["requirement"] != "optional"]

    for slot in front:
        emit_slot(slot, lang=primary_lang, qualified=False)
    for lang in language_set:
        for slot in body:
            emit_slot(slot, lang=lang, qualified=True)
    for slot in back:
        emit_slot(slot, lang=primary_lang, qualified=False)

    # Safety net: the gate must never certify a manifest its own pipeline
    # rejects. parse_config_pages enforces uniqueness downstream; enforce it
    # here too so emit/verify fail at the source.
    emitted_ids = [entry["slot_id"] for entry in pages]
    duplicates = sorted({sid for sid in emitted_ids if emitted_ids.count(sid) > 1})
    if duplicates:
        raise SkeletonResolveError(
            f"resolved plan emits duplicate slot_ids: {', '.join(duplicates)}"
        )

    return {"manifest_id": manifest_id, "pages": pages}


_FIELD_ORDER = (
    "type", "slot_id", "lang", "source", "page", "engine", "recipe",
    "template", "file", "langs", "include_dir", "capability",
    "lang_blocks", "ordinal_neutral",
)


def _yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value)
    # Quote anything YAML would reparse as a different type or reject
    # ('no' -> False, values starting with '{', ': ' inside, '#', ...).
    # A bare scalar is only allowed when it round-trips to the same string.
    try:
        import yaml

        reparsed = yaml.safe_load(text)
    except Exception:
        reparsed = None
    if isinstance(reparsed, str) and reparsed == text and "\n" not in text:
        return text
    import json

    return json.dumps(text, ensure_ascii=False)


def emit_manifest_yaml(plan: dict[str, Any], *, header: list[str]) -> str:
    lines: list[str] = []
    for comment in header:
        lines.append(f"# {comment}" if comment else "#")
    lines.append(f"manifest_id: {plan['manifest_id']}")
    lines.append("pages:")
    for entry in plan["pages"]:
        first = True
        for field in _FIELD_ORDER:
            if field not in entry or entry[field] is None:
                continue
            value = entry[field]
            prefix = "  - " if first else "    "
            first = False
            if field == "langs":
                rendered = "[" + ", ".join(_yaml_scalar(item) for item in value) + "]"
                lines.append(f"{prefix}{field}: {rendered}")
            else:
                lines.append(f"{prefix}{field}: {_yaml_scalar(value)}")
        unknown = sorted(set(entry) - set(_FIELD_ORDER))
        if unknown:
            raise SkeletonResolveError(f"entry has fields outside the emitter order: {unknown}")
    text = "\n".join(lines) + "\n"
    _assert_round_trip(text, plan)
    return text


def _assert_round_trip(text: str, plan: dict[str, Any]) -> None:
    """The gate must never certify bytes its own pipeline reparses differently.

    Every emitted manifest is reparsed here and compared field-for-field
    against the plan; any drift (type coercion, scanner error, lost field)
    fails emit/verify at the source instead of at build time.
    """

    import yaml

    try:
        data = yaml.safe_load(text)
    except Exception as exc:
        raise SkeletonResolveError(f"emitted YAML does not reparse: {exc}") from exc
    if not isinstance(data, dict) or data.get("manifest_id") != plan["manifest_id"]:
        raise SkeletonResolveError("emitted YAML lost or changed manifest_id on reparse")
    reparsed_pages = data.get("pages")
    expected_pages = [
        {k: (list(v) if isinstance(v, tuple) else v) for k, v in entry.items() if v is not None}
        for entry in plan["pages"]
    ]
    if reparsed_pages != expected_pages:
        raise SkeletonResolveError(
            "emitted YAML reparses to a different page list than the resolved plan"
        )


def _repo_relative_posix(path: Path) -> str:
    """Normalize a CLI-spelled path to its repo-relative posix form.

    The generated header must not depend on how the operator spelled the path
    (absolute vs relative), or verify becomes spelling-sensitive and emit can
    commit machine-local paths.
    """

    resolved = path.resolve()
    try:
        return resolved.relative_to(Path(_REPO_ROOT).resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def build_header(skeleton_dir: Path, region_profile: Path, manifest_id: str) -> list[str]:
    skeleton_ref = _repo_relative_posix(skeleton_dir)
    profile_ref = _repo_relative_posix(region_profile)
    return [
        "Resolved Manifest — generated by tools/skeleton_resolve.py. Do not hand-edit.",
        f"Sources: {skeleton_ref}/blueprint.yaml + slot_templates.yaml",
        f"         + {profile_ref}",
        "Regenerate: python tools/skeleton_resolve.py emit "
        f"--skeleton-dir {skeleton_ref} "
        f"--region-profile {profile_ref} "
        f"--manifest-id {manifest_id} --out <this file>",
    ]


def _build(args: argparse.Namespace) -> tuple[str, dict[str, Any]]:
    skeleton_dir = args.skeleton_dir
    blueprint = load_blueprint(skeleton_dir / "blueprint.yaml")
    slot_templates, slot_template_profiles = load_slot_template_catalog(
        skeleton_dir / "slot_templates.yaml",
        blueprint,
    )
    profile = load_region_profile(args.region_profile, blueprint)
    plan = resolve_plan(
        blueprint,
        slot_templates,
        profile,
        manifest_id=args.manifest_id,
        slot_template_profiles=slot_template_profiles,
    )
    header = build_header(skeleton_dir, args.region_profile, args.manifest_id)
    return emit_manifest_yaml(plan, header=header), plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("emit", "verify", "plan"):
        p = sub.add_parser(name)
        p.add_argument("--skeleton-dir", type=Path, required=True)
        p.add_argument("--region-profile", type=Path, required=True)
        p.add_argument("--manifest-id", required=True)
        if name == "emit":
            p.add_argument("--out", type=Path)
        if name == "verify":
            p.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        text, plan = _build(args)
        if args.command == "plan":
            import json

            print(json.dumps(plan, ensure_ascii=False, indent=2))
            return 0
        if args.command == "emit":
            if args.out is None:
                print(text, end="")
            else:
                args.out.write_text(text, encoding="utf-8")
                print(f"[skeleton-resolve] wrote {args.out}")
            return 0
        committed = args.manifest.read_text(encoding="utf-8")
        if committed == text:
            print(f"[skeleton-resolve] OK: {args.manifest} is byte-identical to the resolved output")
            return 0
        print(
            f"[skeleton-resolve] MISMATCH: {args.manifest} differs from the resolved output",
            file=sys.stderr,
        )
        return 1
    except SkeletonResolveError as exc:
        print(f"skeleton_resolve: ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
