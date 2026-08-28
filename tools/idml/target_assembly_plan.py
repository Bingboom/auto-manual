"""Load a candidate target assembly without claiming visual approval.

This contract contains only target composition data.  It is selected explicitly
by a family config for local validation, never discovered through the approved
reference-layout registry.  Promotion to an approved contract remains a
separate, operator-gated step after native InDesign and PDF review.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from tools.manual_ir import ManualIR
from tools.page_plan import build_renderer_page_plan

from .composition_plan import (
    CompositionPlanError,
    build_composition_plan,
)
from .heading_suffix import split_trailing_parenthetical
from .page_roles import PageRole, classify_page_role


SCHEMA_VERSION = "target-idml-assembly-plan/v1"

# Warranty layout variants a target may select. Each name owns its own
# `idml_warranty_variant_<name>_*` token family, so adding a name here without
# adding its tokens is a no-op rather than a silent inheritance of another
# variant's corrections.
WARRANTY_LAYOUT_VARIANTS = frozenset({"multiline_lead", "bp_default"})
SPECIFICATION_LAYOUT_VARIANTS = frozenset({"reference", "compact"})
OPERATION_LAYOUT_VARIANTS = frozenset({"guidance_stack"})


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


def _validate_flow_prefixes(
    pages: list[dict[str, Any]],
    ir: ManualIR,
) -> list[str]:
    """Validate target-declared prefix routing into an earlier composition."""

    issues: list[str] = []
    positions = {
        str(page.get("composition_id")): int(page.get("start_page") or 0)
        for page in pages
    }
    for page, source_page in zip(pages, ir.pages, strict=True):
        rule = page.get("flow_prefix")
        if rule is None:
            continue
        source_ref = source_page.source_ref
        if not isinstance(rule, dict):
            issues.append(f"{source_ref}: flow_prefix must be an object")
            continue
        until_kind = rule.get("until_kind")
        occurrence = rule.get("occurrence")
        head = rule.get("head_composition_id")
        if not isinstance(until_kind, str) or not until_kind:
            issues.append(f"{source_ref}: flow_prefix.until_kind must be non-empty")
            continue
        try:
            occurrence = _positive_int(
                occurrence,
                label=f"{source_ref}.flow_prefix.occurrence",
            )
        except TargetAssemblyPlanError as exc:
            issues.append(str(exc))
            continue
        if not isinstance(head, str) or not head:
            issues.append(
                f"{source_ref}: flow_prefix.head_composition_id must be non-empty"
            )
            continue
        available = sum(block.kind == until_kind for block in source_page.blocks)
        if available < occurrence:
            issues.append(
                f"{source_ref}: flow_prefix cannot find {until_kind} occurrence "
                f"{occurrence}"
            )
        current = str(page.get("composition_id") or "")
        if head not in positions:
            issues.append(f"{source_ref}: flow_prefix target does not exist: {head}")
        elif positions[head] >= positions.get(current, 0):
            issues.append(f"{source_ref}: flow_prefix target must start earlier")
    return issues


def _finite_number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _validate_page_point(
    value: object,
    *,
    label: str,
    page_width: float,
    page_height: float,
) -> list[str]:
    if not isinstance(value, list) or len(value) != 2:
        return [f"{label} must contain exactly two numbers"]
    x = _finite_number(value[0])
    y = _finite_number(value[1])
    if x is None or y is None:
        return [f"{label} must contain exactly two numbers"]
    if not (0 <= x <= page_width and 0 <= y <= page_height):
        return [f"{label} must stay inside the reference page"]
    return []


def _validate_asset_overrides(
    assets: object,
    *,
    source_ref: str,
    source_page: object,
) -> list[str]:
    """Validate the orthogonal semantic image override namespace."""
    issues: list[str] = []
    refs = assets.get("image_refs") if isinstance(assets, dict) else None
    if (
        not isinstance(assets, dict)
        or not set(assets) <= {"image_refs", "image_roles"}
        or "image_refs" not in assets
    ):
        return [
            f"{source_ref}.composition_data.assets must contain image_refs "
            "and supports optional image_roles"
        ]
    if not isinstance(refs, list):
        return [
            f"{source_ref}.composition_data.assets.image_refs must be a list"
        ]
    source_blocks = getattr(source_page, "blocks", ())
    image_count = sum(block.kind == "image" for block in source_blocks)
    if len(refs) != image_count:
        issues.append(
            f"{source_ref}.composition_data.assets.image_refs must "
            f"contain exactly {image_count} entries"
        )
    for ref in refs:
        if ref is None:
            continue
        if not isinstance(ref, str) or not ref.strip():
            issues.append(
                f"{source_ref}.composition_data.assets.image_refs "
                "must contain non-empty strings or null"
            )
            continue
        relative = Path(ref)
        if relative.is_absolute() or ".." in relative.parts:
            issues.append(
                f"{source_ref}.composition_data.assets.image_refs "
                "must be bundle-relative"
            )
    image_roles = assets.get("image_roles")
    if image_roles is not None:
        allowed_roles = {
            "charging_diagram",
            "compact_diagram",
            "full_measure",
            "reference_measure",
            "wide_diagram",
        }
        if (
            not isinstance(image_roles, list)
            or len(image_roles) != image_count
            or any(role not in allowed_roles for role in image_roles)
        ):
            issues.append(
                f"{source_ref}.composition_data.assets.image_roles must "
                f"contain exactly {image_count} registered semantic roles"
            )
    return issues


def _validate_composition_data(
    pages: list[dict[str, Any]],
    reference: dict[str, Any],
    ir: ManualIR,
) -> list[str]:
    """Validate optional target-only component variants and page geometry."""
    issues: list[str] = []
    page_size = reference.get("page_size_pt")
    page_width = _finite_number(
        page_size.get("width") if isinstance(page_size, dict) else None
    )
    page_height = _finite_number(
        page_size.get("height") if isinstance(page_size, dict) else None
    )
    for page_index, page in enumerate(pages):
        data = page.get("composition_data")
        if data is None:
            continue
        source_ref = str(page.get("source_ref") or "page")
        if not isinstance(data, dict):
            issues.append(f"{source_ref}.composition_data must be an object")
            continue
        page_breaks = data.get("page_breaks")
        if page_breaks is not None:
            if not isinstance(page_breaks, list) or not page_breaks:
                issues.append(
                    f"{source_ref}.composition_data.page_breaks must be a "
                    "non-empty list"
                )
            else:
                source_page = (
                    ir.pages[page_index] if page_index < len(ir.pages) else None
                )
                seen_breaks: set[tuple[str, int]] = set()
                for break_index, rule in enumerate(page_breaks):
                    label = (
                        f"{source_ref}.composition_data.page_breaks[{break_index}]"
                    )
                    if not isinstance(rule, dict) or not set(rule) <= {
                        "at_kind",
                        "occurrence",
                        "top_gap_pt",
                    } or not {"at_kind", "occurrence"} <= set(rule):
                        issues.append(
                            f"{label} requires at_kind and occurrence and "
                            "supports optional top_gap_pt"
                        )
                        continue
                    at_kind = rule.get("at_kind")
                    if not isinstance(at_kind, str) or not at_kind:
                        issues.append(f"{label}.at_kind must be non-empty")
                        continue
                    try:
                        occurrence = _positive_int(
                            rule.get("occurrence"),
                            label=f"{label}.occurrence",
                        )
                    except TargetAssemblyPlanError as exc:
                        issues.append(str(exc))
                        continue
                    key = (at_kind, occurrence)
                    if key in seen_breaks:
                        issues.append(f"{label} duplicates {at_kind} {occurrence}")
                    seen_breaks.add(key)
                    available = sum(
                        block.kind == at_kind
                        for block in (
                            source_page.blocks if source_page is not None else ()
                        )
                    )
                    if available < occurrence:
                        issues.append(
                            f"{label} cannot find {at_kind} occurrence {occurrence}"
                        )
                    if "top_gap_pt" in rule:
                        top_gap = _finite_number(rule["top_gap_pt"])
                        if top_gap is None or not 0 <= top_gap <= 48:
                            issues.append(
                                f"{label}.top_gap_pt must be between 0 and 48"
                            )
            data = {
                key: value for key, value in data.items() if key != "page_breaks"
            }
            if not data:
                continue
        if "assets" in data:
            source_page = (
                ir.pages[page_index] if page_index < len(ir.pages) else None
            )
            issues.extend(_validate_asset_overrides(
                data["assets"],
                source_ref=source_ref,
                source_page=source_page,
            ))
            data = {key: value for key, value in data.items() if key != "assets"}
            if not data:
                continue
        if set(data) == {"charging"}:
            if page.get("page_role") != PageRole.CHARGING.value or page.get(
                "composition_type"
            ) != "charging":
                issues.append(
                    f"{source_ref}.composition_data.charging requires "
                    "a charging composition"
                )
                continue
            charging = data["charging"]
            if not isinstance(charging, dict):
                issues.append(
                    f"{source_ref}.composition_data.charging must be an object"
                )
                continue
            expected = {"image_role", "h2_suffix_pill_indices"}
            if set(charging) != expected:
                issues.append(
                    f"{source_ref}.composition_data.charging must contain "
                    f"exactly {sorted(expected)}"
                )
                continue
            if charging.get("image_role") not in {
                "charging_diagram",
                "full_measure",
                "reference_measure",
            }:
                issues.append(
                    f"{source_ref}.composition_data.charging.image_role is invalid"
                )
            indices = charging.get("h2_suffix_pill_indices")
            if not isinstance(indices, list) or not indices:
                issues.append(
                    f"{source_ref}.composition_data.charging."
                    "h2_suffix_pill_indices must be a non-empty list"
                )
                continue
            if any(
                isinstance(index, bool)
                or not isinstance(index, int)
                or index < 0
                for index in indices
            ):
                issues.append(
                    f"{source_ref}.composition_data.charging."
                    "h2_suffix_pill_indices must contain non-negative integers"
                )
                continue
            if len(set(indices)) != len(indices):
                issues.append(
                    f"{source_ref}.composition_data.charging."
                    "h2_suffix_pill_indices must be unique"
                )
                continue
            source_page = ir.pages[page_index] if page_index < len(ir.pages) else None
            h2s = [
                str(block.payload)
                for block in (source_page.blocks if source_page is not None else ())
                if block.kind == "h2"
            ]
            for index in indices:
                label = (
                    f"{source_ref}.composition_data.charging."
                    "h2_suffix_pill_indices"
                )
                if index >= len(h2s):
                    issues.append(f"{label} index {index} is out of range")
                elif split_trailing_parenthetical(h2s[index]) is None:
                    issues.append(
                        f"{label} index {index} requires a trailing parenthetical"
                    )
            continue
        if set(data) == {"connections"}:
            if page.get("page_role") != PageRole.CONNECTIONS.value or page.get(
                "composition_type"
            ) != "connections":
                issues.append(
                    f"{source_ref}.composition_data.connections requires "
                    "a connections composition"
                )
                continue
            connections = data["connections"]
            if not isinstance(connections, dict):
                issues.append(
                    f"{source_ref}.composition_data.connections must be an object"
                )
                continue
            expected = {"image_role", "layout_variant"}
            if set(connections) != expected:
                issues.append(
                    f"{source_ref}.composition_data.connections must contain "
                    f"exactly {sorted(expected)}"
                )
                continue
            if connections.get("layout_variant") != (
                "notice_before_primary_figure"
            ):
                issues.append(
                    f"{source_ref}.composition_data.connections.layout_variant "
                    "must be notice_before_primary_figure"
                )
            if connections.get("image_role") not in {
                "full_measure",
                "reference_measure",
            }:
                issues.append(
                    f"{source_ref}.composition_data.connections.image_role "
                    "is invalid"
                )
            continue
        if set(data) == {"operation"}:
            if page.get("page_role") != PageRole.OPERATION_GUIDE.value or page.get(
                "composition_type"
            ) != "operation":
                issues.append(
                    f"{source_ref}.composition_data.operation requires "
                    "an operation composition"
                )
                continue
            operation = data["operation"]
            if not isinstance(operation, dict):
                issues.append(
                    f"{source_ref}.composition_data.operation must be an object"
                )
                continue
            if set(operation) != {"layout_variant"}:
                issues.append(
                    f"{source_ref}.composition_data.operation must contain "
                    "exactly ['layout_variant']"
                )
                continue
            if operation.get("layout_variant") not in OPERATION_LAYOUT_VARIANTS:
                issues.append(
                    f"{source_ref}.composition_data.operation.layout_variant "
                    "must be one of "
                    + ", ".join(sorted(OPERATION_LAYOUT_VARIANTS))
                )
            continue
        if set(data) == {"inbox"}:
            if page.get("page_role") != PageRole.INBOX.value or page.get(
                "composition_type"
            ) not in {"inbox_overview", "fcc_inbox_overview"}:
                issues.append(
                    f"{source_ref}.composition_data.inbox requires "
                    "an inbox overview composition on the inbox source"
                )
                continue
            inbox = data["inbox"]
            allowed = {
                "image_width_pt_by_language",
                "card_y",
                "card_height",
                "content_height",
                "badge_y_offset",
                "card_1_content_y_offset",
                "card_2_content_y_offset",
                "card_3_content_y_offset",
                "card_1_image_space_after",
                "card_2_image_space_after",
                "card_3_image_space_after",
                "include_tip",
                "tip_y",
                "tip_height",
                "tip_label_width",
                "stroke_color",
                "stroke_weight",
            }
            if (
                not isinstance(inbox, dict)
                or "image_width_pt_by_language" not in inbox
                or not set(inbox) <= allowed
            ):
                issues.append(
                    f"{source_ref}.composition_data.inbox requires "
                    "image_width_pt_by_language and supports only "
                    + ", ".join(sorted(allowed - {"image_width_pt_by_language"}))
                )
                continue
            widths_by_language = inbox.get("image_width_pt_by_language")
            language = str(page.get("language") or "")
            if (
                not isinstance(widths_by_language, dict)
                or language not in widths_by_language
            ):
                issues.append(
                    f"{source_ref}.composition_data.inbox."
                    "image_width_pt_by_language must contain the page language"
                )
                continue
            if any(
                not isinstance(key, str)
                or not key
                or not isinstance(widths, list)
                or len(widths) != 3
                or any(
                    (value := _finite_number(item)) is None or value <= 0
                    for item in widths
                )
                for key, widths in widths_by_language.items()
            ):
                issues.append(
                    f"{source_ref}.composition_data.inbox."
                    "image_width_pt_by_language values must contain three "
                    "positive numbers"
                )
            for metric in (
                "card_y",
                "card_height",
                "content_height",
                "badge_y_offset",
                "tip_y",
                "tip_height",
                "tip_label_width",
                "stroke_weight",
            ):
                if metric not in inbox:
                    continue
                value = _finite_number(inbox[metric])
                if value is None or value <= 0:
                    issues.append(
                        f"{source_ref}.composition_data.inbox.{metric} "
                        "must be a positive finite number"
                    )
            for metric in (
                "card_1_content_y_offset",
                "card_2_content_y_offset",
                "card_3_content_y_offset",
                "card_1_image_space_after",
                "card_2_image_space_after",
                "card_3_image_space_after",
            ):
                if metric not in inbox:
                    continue
                value = _finite_number(inbox[metric])
                if value is None or (
                    metric.endswith("image_space_after") and value < 0
                ):
                    issues.append(
                        f"{source_ref}.composition_data.inbox.{metric} "
                        "must be a finite number"
                    )
            if "stroke_color" in inbox and (
                not isinstance(inbox["stroke_color"], str)
                or not inbox["stroke_color"].strip()
            ):
                issues.append(
                    f"{source_ref}.composition_data.inbox.stroke_color "
                    "must be a non-empty swatch name"
                )
            if "include_tip" in inbox and not isinstance(
                inbox["include_tip"], bool
            ):
                issues.append(
                    f"{source_ref}.composition_data.inbox.include_tip "
                    "must be a boolean"
                )
            continue
        if set(data) == {"overview"}:
            if page.get("page_role") != PageRole.PRODUCT_OVERVIEW.value or page.get(
                "composition_type"
            ) not in {"inbox_overview", "fcc_inbox_overview"}:
                issues.append(
                    f"{source_ref}.composition_data.overview requires "
                    "an inbox_overview composition on the product overview source"
                )
                continue
            overview = data["overview"]
            if not isinstance(overview, dict) or not set(overview) <= {
                "instance_id",
                "asset_refs",
            } or "instance_id" not in overview:
                issues.append(
                    f"{source_ref}.composition_data.overview must contain "
                    "instance_id and supports optional asset_refs"
                )
                continue
            if not isinstance(overview.get("instance_id"), str) or not str(
                overview.get("instance_id")
            ).strip():
                issues.append(
                    f"{source_ref}.composition_data.overview.instance_id "
                    "must be a non-empty string"
                )
            asset_refs = overview.get("asset_refs")
            if asset_refs is not None:
                if not isinstance(asset_refs, dict) or set(asset_refs) != {
                    "front_art",
                    "right_art",
                }:
                    issues.append(
                        f"{source_ref}.composition_data.overview.asset_refs must "
                        "contain exactly front_art and right_art"
                    )
                elif any(
                    not isinstance(value, str)
                    or not value.strip()
                    or Path(value).is_absolute()
                    or ".." in Path(value).parts
                    for value in asset_refs.values()
                ):
                    issues.append(
                        f"{source_ref}.composition_data.overview.asset_refs values "
                        "must be non-empty bundle-relative strings"
                    )
            continue
        if set(data) == {"app"}:
            if page.get("page_role") != PageRole.APP_SETUP.value or page.get(
                "composition_type"
            ) != "app":
                issues.append(
                    f"{source_ref}.composition_data.app requires an app composition"
                )
                continue
            app = data["app"]
            expected = {
                "instance_id",
                "control_image",
                "control_layout_variant",
                "labels_by_role",
            }
            if (
                not isinstance(app, dict)
                or not expected <= set(app)
                or not set(app) <= expected | {"figure_assets"}
            ):
                issues.append(
                    f"{source_ref}.composition_data.app must contain "
                    f"{sorted(expected)} and supports optional figure_assets"
                )
                continue
            for field in ("instance_id", "control_image"):
                value = app.get(field)
                if (
                    not isinstance(value, str)
                    or not value.strip()
                    or Path(value).is_absolute()
                    or ".." in Path(value).parts
                ):
                    issues.append(
                        f"{source_ref}.composition_data.app.{field} must be a "
                        "non-empty bundle-relative string"
                    )
            if app.get("control_layout_variant") not in {
                "embedded_leaders",
                "reference_extensions",
            }:
                issues.append(
                    f"{source_ref}.composition_data.app.control_layout_variant "
                    "is invalid"
                )
            labels = app.get("labels_by_role")
            required_roles = {"main_power", "dc_usb", "ac"}
            if not isinstance(labels, dict) or set(labels) != required_roles:
                issues.append(
                    f"{source_ref}.composition_data.app.labels_by_role must "
                    "contain exactly ac, dc_usb, and main_power"
                )
            elif any(
                not isinstance(value, str) or not value.strip()
                for value in labels.values()
            ):
                issues.append(
                    f"{source_ref}.composition_data.app.labels_by_role values "
                    "must be non-empty strings"
                )
            figure_assets = app.get("figure_assets")
            allowed_figure_roles = {
                "app_download",
                "app_add_device",
                "app_connect_result",
            }
            if figure_assets is not None and (
                not isinstance(figure_assets, dict)
                or not figure_assets
                or not set(figure_assets) <= allowed_figure_roles
                or any(
                    not isinstance(value, str)
                    or not value.strip()
                    or Path(value).is_absolute()
                    or ".." in Path(value).parts
                    for value in figure_assets.values()
                )
            ):
                issues.append(
                    f"{source_ref}.composition_data.app.figure_assets must be "
                    "a non-empty bundle-relative mapping of App figure roles"
                )
            continue
        if set(data) == {"specifications"}:
            if page.get("page_role") != PageRole.SPEC.value or page.get(
                "composition_type"
            ) not in {"storage_specifications", "specifications"}:
                issues.append(
                    f"{source_ref}.composition_data.specifications requires "
                    "a specifications composition on the spec source"
                )
                continue
            specifications = data["specifications"]
            if not isinstance(specifications, dict):
                issues.append(
                    f"{source_ref}.composition_data.specifications must be an object"
                )
                continue
            allowed = {"layout_variant", "section_groups", "annotation_order"}
            if "layout_variant" not in specifications or not set(
                specifications
            ) <= allowed:
                issues.append(
                    f"{source_ref}.composition_data.specifications must contain "
                    "layout_variant and supports optional section_groups or "
                    "annotation_order"
                )
                continue
            if specifications.get("layout_variant") not in (
                SPECIFICATION_LAYOUT_VARIANTS
            ):
                issues.append(
                    f"{source_ref}.composition_data.specifications."
                    "layout_variant must be one of "
                    + ", ".join(sorted(SPECIFICATION_LAYOUT_VARIANTS))
                )
            annotation_order = specifications.get("annotation_order")
            if annotation_order is not None and (
                not isinstance(annotation_order, list)
                or not annotation_order
                or any(
                    isinstance(index, bool)
                    or not isinstance(index, int)
                    or index < 0
                    for index in annotation_order
                )
                or len(set(annotation_order)) != len(annotation_order)
            ):
                issues.append(
                    f"{source_ref}.composition_data.specifications."
                    "annotation_order must be a non-empty list of unique "
                    "non-negative indices"
                )
            groups = specifications.get("section_groups")
            if groups is None and page.get("composition_type") == "specifications":
                continue
            if not isinstance(groups, list) or not groups:
                issues.append(
                    f"{source_ref}.composition_data.specifications."
                    "section_groups must be a non-empty list"
                )
                continue
            seen_indices: set[int] = set()
            for index, group in enumerate(groups):
                label = (
                    f"{source_ref}.composition_data.specifications."
                    f"section_groups[{index}]"
                )
                if not isinstance(group, dict):
                    issues.append(f"{label} must be an object")
                    continue
                if not set(group) <= {"source_indices", "title"} or (
                    "source_indices" not in group
                ):
                    issues.append(
                        f"{label} supports only source_indices and optional title"
                    )
                    continue
                source_indices = group.get("source_indices")
                if not isinstance(source_indices, list) or not source_indices:
                    issues.append(f"{label}.source_indices must be a non-empty list")
                    continue
                for source_index in source_indices:
                    if (
                        isinstance(source_index, bool)
                        or not isinstance(source_index, int)
                        or source_index < 0
                    ):
                        issues.append(
                            f"{label}.source_indices must contain non-negative integers"
                        )
                        continue
                    if source_index in seen_indices:
                        issues.append(
                            f"{label}.source_indices contains duplicate {source_index}"
                        )
                    seen_indices.add(source_index)
                if "title" in group and not isinstance(group["title"], str):
                    issues.append(f"{label}.title must be a string")
            continue
        if set(data) == {"warranty"}:
            if page.get("page_role") != PageRole.WARRANTY.value or page.get(
                "composition_type"
            ) != "warranty":
                issues.append(
                    f"{source_ref}.composition_data.warranty requires "
                    "a warranty composition"
                )
                continue
            warranty = data["warranty"]
            if not isinstance(warranty, dict):
                issues.append(
                    f"{source_ref}.composition_data.warranty must be an object"
                )
                continue
            if set(warranty) != {"layout_variant"}:
                issues.append(
                    f"{source_ref}.composition_data.warranty must contain "
                    "exactly ['layout_variant']"
                )
                continue
            if warranty.get("layout_variant") not in WARRANTY_LAYOUT_VARIANTS:
                issues.append(
                    f"{source_ref}.composition_data.warranty.layout_variant "
                    "must be one of "
                    + ", ".join(sorted(WARRANTY_LAYOUT_VARIANTS))
                )
            continue
        if set(data) == {"troubleshooting"}:
            if page.get("page_role") != PageRole.TROUBLESHOOTING_DATA.value or page.get(
                "composition_type"
            ) != "troubleshooting":
                issues.append(
                    f"{source_ref}.composition_data.troubleshooting requires "
                    "a troubleshooting composition"
                )
                continue
            troubleshooting = data["troubleshooting"]
            if not isinstance(troubleshooting, dict):
                issues.append(
                    f"{source_ref}.composition_data.troubleshooting must be an object"
                )
                continue
            expected = {
                "connection_image_role",
                "heading_space_after",
                "split",
            }
            if set(troubleshooting) != expected:
                issues.append(
                    f"{source_ref}.composition_data.troubleshooting must contain "
                    f"exactly {sorted(expected)}"
                )
                continue
            if troubleshooting.get("connection_image_role") not in {
                "wide_diagram",
                "full_measure",
                "reference_measure",
            }:
                issues.append(
                    f"{source_ref}.composition_data.troubleshooting."
                    "connection_image_role is invalid"
                )
            split = _finite_number(troubleshooting.get("split"))
            if (
                split is None
                or page_height is None
                or not 0 < split < page_height
            ):
                issues.append(
                    f"{source_ref}.composition_data.troubleshooting.split must "
                    "stay inside the reference page"
                )
            heading_space_after = _finite_number(
                troubleshooting.get("heading_space_after")
            )
            if heading_space_after is None or not 0 <= heading_space_after <= 24:
                issues.append(
                    f"{source_ref}.composition_data.troubleshooting."
                    "heading_space_after must be between 0 and 24"
                )
            continue
        if set(data) != {"lcd"}:
            issues.append(
                f"{source_ref}.composition_data supports only charging, "
                "connections, lcd, operation, specifications, troubleshooting, "
                "or warranty component data"
            )
            continue
        if page.get("page_role") != PageRole.LCD.value or page.get(
            "composition_type"
        ) not in {"lcd", "lcd_operations"}:
            issues.append(
                f"{source_ref}.composition_data.lcd requires an LCD composition"
            )
            continue
        lcd = data["lcd"]
        if not isinstance(lcd, dict):
            issues.append(f"{source_ref}.composition_data.lcd must be an object")
            continue
        allowed = {
            "table_variant",
            "hero_horizontal_scale",
            "hero_callouts",
            "operation_panel_variant",
        }
        unknown = sorted(set(lcd) - allowed)
        if unknown:
            issues.append(
                f"{source_ref}.composition_data.lcd has unknown keys: {unknown}"
            )
        variant = lcd.get("table_variant")
        if variant not in {"number_icon_label_description", "label_description"}:
            issues.append(
                f"{source_ref}.composition_data.lcd.table_variant is invalid"
            )
        operation_panel_variant = lcd.get("operation_panel_variant")
        if operation_panel_variant is not None and (
            page.get("composition_type") != "lcd_operations"
            or operation_panel_variant != "paired_cards"
        ):
            issues.append(
                f"{source_ref}.composition_data.lcd.operation_panel_variant "
                "requires lcd_operations and must be paired_cards"
            )
        scale = _finite_number(lcd.get("hero_horizontal_scale", 1.0))
        if scale is None or not 0.5 <= scale <= 2.0:
            issues.append(
                f"{source_ref}.composition_data.lcd.hero_horizontal_scale "
                "must be between 0.5 and 2.0"
            )
        callouts = lcd.get("hero_callouts", [])
        if not isinstance(callouts, list):
            issues.append(
                f"{source_ref}.composition_data.lcd.hero_callouts must be a list"
            )
            continue
        if callouts and (page_width is None or page_height is None):
            issues.append(
                f"{source_ref}: reference_pdf.page_size_pt is required for callouts"
            )
            continue
        seen_rows: set[int] = set()
        for index, callout in enumerate(callouts):
            label = (
                f"{source_ref}.composition_data.lcd.hero_callouts[{index}]"
            )
            if not isinstance(callout, dict):
                issues.append(f"{label} must be an object")
                continue
            expected = {"row_index", "text_rect", "align", "leader_points"}
            if set(callout) != expected:
                issues.append(f"{label} must contain exactly {sorted(expected)}")
                continue
            try:
                row_index = _positive_int(
                    callout.get("row_index"),
                    label=f"{label}.row_index",
                )
            except TargetAssemblyPlanError as exc:
                issues.append(str(exc))
                continue
            if row_index in seen_rows:
                issues.append(f"{label}.row_index must be unique")
            seen_rows.add(row_index)
            rect = callout.get("text_rect")
            if not isinstance(rect, list) or len(rect) != 4:
                issues.append(f"{label}.text_rect must contain four numbers")
            else:
                values = [_finite_number(value) for value in rect]
                if any(value is None for value in values):
                    issues.append(f"{label}.text_rect must contain four numbers")
                else:
                    x, y, width, height = values  # type: ignore[misc]
                    if (
                        width <= 0
                        or height <= 0
                        or x < 0
                        or y < 0
                        or x + width > page_width  # type: ignore[operator]
                        or y + height > page_height  # type: ignore[operator]
                    ):
                        issues.append(
                            f"{label}.text_rect must stay inside the reference page"
                        )
            if callout.get("align") not in {
                "LeftAlign",
                "CenterAlign",
                "RightAlign",
            }:
                issues.append(f"{label}.align is invalid")
            points = callout.get("leader_points")
            if not isinstance(points, list) or len(points) < 2:
                issues.append(f"{label}.leader_points requires at least two points")
                continue
            for point_index, point in enumerate(points):
                issues.extend(_validate_page_point(
                    point,
                    label=f"{label}.leader_points[{point_index}]",
                    page_width=page_width,  # type: ignore[arg-type]
                    page_height=page_height,  # type: ignore[arg-type]
                ))
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
    page_size = reference.get("page_size_pt")
    page_width = _finite_number(
        page_size.get("width") if isinstance(page_size, dict) else None
    )
    page_height = _finite_number(
        page_size.get("height") if isinstance(page_size, dict) else None
    )

    idml_contract = payload.get("idml_contract")
    if idml_contract is not None:
        editable = (
            idml_contract.get("editable_components")
            if isinstance(idml_contract, dict)
            else None
        )
        back_cover = (
            editable.get("back_cover") if isinstance(editable, dict) else None
        )
        if not isinstance(back_cover, dict) or set(back_cover) != {
            "variant",
            "qr_asset",
            "qr_rect",
        }:
            issues.append(
                "idml_contract supports only editable_components.back_cover with "
                "variant, qr_asset, and qr_rect"
            )
        else:
            if back_cover.get("variant") != "qr_only":
                issues.append("idml_contract back_cover.variant must be qr_only")
            qr_asset = back_cover.get("qr_asset")
            if (
                not isinstance(qr_asset, str)
                or not qr_asset.strip()
                or Path(qr_asset).is_absolute()
                or ".." in Path(qr_asset).parts
            ):
                issues.append(
                    "idml_contract back_cover.qr_asset must be bundle-relative"
                )
            rect = back_cover.get("qr_rect")
            if not isinstance(rect, list) or len(rect) != 4:
                issues.append(
                    "idml_contract back_cover.qr_rect must contain four numbers"
                )
            else:
                values = [_finite_number(value) for value in rect]
                if any(value is None for value in values):
                    issues.append(
                        "idml_contract back_cover.qr_rect must contain four numbers"
                    )
                else:
                    x, y, width, height = values  # type: ignore[misc]
                    if (
                        width <= 0
                        or height <= 0
                        or x < 0
                        or y < 0
                        or page_width is not None and x + width > page_width
                        or page_height is not None and y + height > page_height
                    ):
                        issues.append(
                            "idml_contract back_cover.qr_rect must stay inside "
                            "the reference page"
                        )

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
            "flow_prefix": raw.get("flow_prefix"),
            "composition_data": raw.get("composition_data"),
        }
        normalized_pages.append(normalized)

    issues.extend(_validate_flow_splits(raw_pages, ir))
    issues.extend(_validate_flow_prefixes(raw_pages, ir))
    issues.extend(_validate_composition_data(raw_pages, reference, ir))
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
        "idml_contract": idml_contract,
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
    "SPECIFICATION_LAYOUT_VARIANTS",
    "TargetAssemblyPlanError",
    "load_target_assembly_plan",
    "normalize_target_assembly_plan",
)
