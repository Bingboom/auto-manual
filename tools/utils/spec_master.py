#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from collections import Counter, defaultdict
import csv
from dataclasses import dataclass
from pathlib import Path
import re
from typing import cast


@dataclass(frozen=True)
class ProductNameMatch:
    product_name: str
    region: str | None


@dataclass(frozen=True)
class SpecValueMatch:
    value: str
    region: str | None
    row: dict[str, str]


@dataclass(frozen=True)
class PageValueBinding:
    row_key: str
    section: str
    section_order: str
    row_label_source: str
    placement_key: str = ""
    value_role: str = ""
    variant_key: str = ""
    usage_type: str = "page_value"


@dataclass(frozen=True)
class SpecMasterSectionSummary:
    section: str
    suggested_section: str
    category: str
    row_count: int
    orders: tuple[str, ...]
    models: tuple[str, ...]
    regions: tuple[str, ...]
    note: str


@dataclass(frozen=True)
class SpecMasterSectionOrderConflict:
    section_order: str
    sections: tuple[str, ...]


@dataclass(frozen=True)
class SpecMasterAuditIssue:
    code: str
    message: str
    line: int | None
    model: str | None
    region: str | None
    section: str | None
    row_key: str | None


@dataclass(frozen=True)
class SpecMasterAuditResult:
    total_rows: int
    unique_sections: int
    section_summaries: tuple[SpecMasterSectionSummary, ...]
    order_conflicts: tuple[SpecMasterSectionOrderConflict, ...]
    issues: tuple[SpecMasterAuditIssue, ...]


@dataclass(frozen=True)
class SpecMasterNormalizationResult:
    normalized_rows: tuple[dict[str, str], ...]
    anomaly_rows: tuple[dict[str, str], ...]


@dataclass(frozen=True)
class SpecMasterAppliedRepair:
    line: int
    model: str | None
    region: str | None
    row_key: str | None
    column: str
    old_value: str
    new_value: str


@dataclass(frozen=True)
class SpecMasterRepairResult:
    repaired_rows: tuple[dict[str, str], ...]
    applied_repairs: tuple[SpecMasterAppliedRepair, ...]
    removed_duplicate_lines: tuple[int, ...]


_SECTION_ORDER_BY_SECTION: dict[str, str] = {
    "GENERAL INFO": "1",
    "INPUT PORTS": "2",
    "OUTPUT PORTS": "3",
    "ENVIRONMENTAL": "4",
    "BATTERY": "5",
    "MECHANICAL": "6",
    "CONTROLS": "7",
    "SETTINGS": "8",
    "ACCESSORIES": "9",
    "TEMPLATE VARS": "99",
}
_LEGACY_PAGE_VALUE_BINDINGS: dict[str, PageValueBinding] = {
    "tpl_main_power_button_label": PageValueBinding(
        row_key="main_power_button",
        section="CONTROLS",
        section_order="7",
        row_label_source="Main Power Button",
        value_role="label",
    ),
    "tpl_dc_usb_power_button_label": PageValueBinding(
        row_key="dc_usb_power_button",
        section="CONTROLS",
        section_order="7",
        row_label_source="DC/USB Power Button",
        value_role="label",
    ),
    "tpl_ac_power_button_label": PageValueBinding(
        row_key="ac_power_button",
        section="CONTROLS",
        section_order="7",
        row_label_source="AC Power Button",
        value_role="label",
    ),
    "tpl_front_dc12_port_label": PageValueBinding(
        row_key="dc12_port",
        section="OUTPUT PORTS",
        section_order="3",
        row_label_source="DC 12V Port",
        placement_key="front",
        value_role="label",
    ),
    "tpl_front_dc12_port_spec": PageValueBinding(
        row_key="dc12_port",
        section="OUTPUT PORTS",
        section_order="3",
        row_label_source="DC 12V Port",
        placement_key="front",
        value_role="spec",
    ),
    "tpl_front_usb_c_low_label": PageValueBinding(
        row_key="usb_c",
        section="OUTPUT PORTS",
        section_order="3",
        row_label_source="USB-C 30W Output",
        placement_key="front",
        value_role="label",
        variant_key="low",
    ),
    "tpl_front_usb_c_low_spec": PageValueBinding(
        row_key="usb_c",
        section="OUTPUT PORTS",
        section_order="3",
        row_label_source="USB-C 30W Output",
        placement_key="front",
        value_role="spec",
        variant_key="low",
    ),
    "tpl_front_usb_c_high_label": PageValueBinding(
        row_key="usb_c",
        section="OUTPUT PORTS",
        section_order="3",
        row_label_source="USB-C 100W Output",
        placement_key="front",
        value_role="label",
        variant_key="high",
    ),
    "tpl_front_usb_c_high_spec": PageValueBinding(
        row_key="usb_c",
        section="OUTPUT PORTS",
        section_order="3",
        row_label_source="USB-C 100W Output",
        placement_key="front",
        value_role="spec",
        variant_key="high",
    ),
    "tpl_front_usb_a_label": PageValueBinding(
        row_key="usb_a",
        section="OUTPUT PORTS",
        section_order="3",
        row_label_source="USB-A 18W Output",
        placement_key="front",
        value_role="label",
    ),
    "tpl_front_usb_a_spec": PageValueBinding(
        row_key="usb_a",
        section="OUTPUT PORTS",
        section_order="3",
        row_label_source="USB-A 18W Output",
        placement_key="front",
        value_role="spec",
    ),
    "tpl_front_ac_output_label": PageValueBinding(
        row_key="ac_output",
        section="OUTPUT PORTS",
        section_order="3",
        row_label_source="AC Output",
        placement_key="front",
        value_role="label",
    ),
    "tpl_front_ac_output_spec": PageValueBinding(
        row_key="ac_output",
        section="OUTPUT PORTS",
        section_order="3",
        row_label_source="AC Output",
        placement_key="front",
        value_role="spec",
    ),
    "tpl_front_total_output_label": PageValueBinding(
        row_key="total_output",
        section="OUTPUT PORTS",
        section_order="3",
        row_label_source="Total Output",
        placement_key="front",
        value_role="label",
    ),
    "tpl_front_total_output_spec": PageValueBinding(
        row_key="total_output",
        section="OUTPUT PORTS",
        section_order="3",
        row_label_source="Total Output",
        placement_key="front",
        value_role="spec",
    ),
    "tpl_side_dc_input_label": PageValueBinding(
        row_key="dc_input",
        section="INPUT PORTS",
        section_order="2",
        row_label_source="DC Input (2 x DC8020 Ports)",
        placement_key="side",
        value_role="label",
    ),
    "tpl_side_dc_input_pv_spec": PageValueBinding(
        row_key="dc_input",
        section="INPUT PORTS",
        section_order="2",
        row_label_source="PV Input",
        placement_key="side",
        value_role="spec",
        variant_key="pv",
    ),
    "tpl_side_dc_input_car_spec": PageValueBinding(
        row_key="dc_input",
        section="INPUT PORTS",
        section_order="2",
        row_label_source="Car Input",
        placement_key="side",
        value_role="spec",
        variant_key="car",
    ),
    "tpl_side_ac_input_label": PageValueBinding(
        row_key="ac_input",
        section="INPUT PORTS",
        section_order="2",
        row_label_source="AC Input",
        placement_key="side",
        value_role="label",
    ),
    "tpl_side_ac_input_spec": PageValueBinding(
        row_key="ac_input",
        section="INPUT PORTS",
        section_order="2",
        row_label_source="AC Input",
        placement_key="side",
        value_role="spec",
    ),
    "tpl_ups_bypass_output_text": PageValueBinding(
        row_key="ups_bypass_output",
        section="OUTPUT PORTS",
        section_order="3",
        row_label_source="UPS Bypass Output",
        value_role="text",
    ),
    "tpl_usb_c_high_power_port_label": PageValueBinding(
        row_key="usb_c_high_power_port",
        section="OUTPUT PORTS",
        section_order="3",
        row_label_source="USB-C 100W Port",
        value_role="label",
    ),
    "tpl_default_standby_duration": PageValueBinding(
        row_key="default_standby_duration",
        section="SETTINGS",
        section_order="8",
        row_label_source="Default Standby Duration",
    ),
    "tpl_energy_saving_auto_off_duration": PageValueBinding(
        row_key="energy_saving_auto_off_duration",
        section="SETTINGS",
        section_order="8",
        row_label_source="Energy Saving Auto Off Duration",
    ),
    "tpl_energy_saving_ac_threshold": PageValueBinding(
        row_key="energy_saving_ac_threshold",
        section="SETTINGS",
        section_order="8",
        row_label_source="Energy Saving AC Threshold",
    ),
    "tpl_energy_saving_dc_threshold": PageValueBinding(
        row_key="energy_saving_dc_threshold",
        section="SETTINGS",
        section_order="8",
        row_label_source="Energy Saving DC Threshold",
    ),
    "tpl_usb_c_high_power_cable_name": PageValueBinding(
        row_key="usb_c_high_power_cable_name",
        section="ACCESSORIES",
        section_order="9",
        row_label_source="USB-C High Power Cable",
    ),
    "tpl_car_battery_charging_cable_name": PageValueBinding(
        row_key="car_battery_charging_cable_name",
        section="ACCESSORIES",
        section_order="9",
        row_label_source="Car Battery Charging Cable",
    ),
    "tpl_battery_pack_name": PageValueBinding(
        row_key="battery_pack_name",
        section="ACCESSORIES",
        section_order="9",
        row_label_source="Battery Pack Name",
    ),
}
_LEGACY_PAGE_VALUE_KEYS_BY_SIGNATURE: dict[tuple[str, str, str, str, str], str] = {
    (
        binding.row_key,
        binding.usage_type,
        binding.placement_key,
        binding.value_role,
        binding.variant_key,
    ): legacy_key
    for legacy_key, binding in _LEGACY_PAGE_VALUE_BINDINGS.items()
}
_SECTION_NORMALIZATION_RULES: dict[str, tuple[str, str, str]] = {
    "ENVIRONMENTAL OPERATING TEMPERATURE": (
        "ENVIRONMENTAL",
        "spec",
        "Consider moving these rows under `ENVIRONMENTAL` and introducing a sub-section field when needed.",
    ),
    "TEMPLATE VARS": (
        "TEMPLATE VARS",
        "template",
        "Separate placeholder/template rows from the main specification table before section-level analysis.",
    ),
}
_DERIVED_MULTILINE_PLACEHOLDERS: dict[str, tuple[str, tuple[str, ...] | None]] = {
    "storage_temperature": ("STORAGE_TEMPERATURE", ("storage",)),
}
_SLOT_KEY_VALUE_ALIASES = {"", "value", "default", "name"}
_KNOWN_ROW_LABEL_REPAIRS: dict[str, str] = {
    "??????": "Rated Capacity",
    "棰濆畾瀹归噺": "Rated Capacity",
}
_KNOWN_VALUE_REPAIRS: dict[tuple[str, str, str, str], str] = {
    ("JE-2000F", "US", "tpl_front_dc12_port_spec", "Value_source"): "12V/10A Max",
    ("JE-2000F", "JP", "tpl_main_power_button_label", "Value_source"): "メイン電源ボタン",
}
_SOURCE_COLUMN_NAMES: dict[str, tuple[str, ...]] = {
    "Row_label": ("Row_label_source", "row_label_source"),
    "Param": ("Param_source", "param_source"),
    "Value": ("Value_source", "value_source"),
}
_SOURCE_SHARED_BASES = frozenset(_SOURCE_COLUMN_NAMES)
_SOURCE_LANGUAGE_NORMALIZATION = {
    "en": "en",
    "english": "en",
    "英语": "en",
    "英文": "en",
    "ja": "ja",
    "jp": "ja",
    "japanese": "ja",
    "日语": "ja",
    "日文": "ja",
    "zh": "zh",
    "cn": "zh",
    "chinese": "zh",
    "中文": "zh",
    "汉语": "zh",
    "漢語": "zh",
    "fr": "fr",
    "french": "fr",
    "法语": "fr",
    "法文": "fr",
    "es": "es",
    "spanish": "es",
    "西语": "es",
    "西班牙语": "es",
}


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows: list[dict[str, str]] = []
        for line, row in enumerate(csv.DictReader(f), start=2):
            row["__line__"] = str(line)
            rows.append(row)
        return rows


def _first_non_empty(row: dict[str, str], keys: list[str]) -> str:
    for key in keys:
        value = (row.get(key) or "").strip()
        if value:
            return value
    return ""


def _first_existing_key(row: dict[str, str], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        if key in row:
            return key
    return None


def _source_column_names(base: str) -> tuple[str, ...]:
    return _SOURCE_COLUMN_NAMES.get(base, (f"{base}_source", f"{base.lower()}_source"))


def _pick_source_value(row: dict[str, str], base: str) -> str:
    return _first_non_empty(row, list(_source_column_names(base)))


def _source_column_name(row: dict[str, str], base: str) -> str:
    return _first_existing_key(row, _source_column_names(base)) or f"{base}_source"


def _set_source_value(row: dict[str, str], base: str, value: str) -> str:
    column = _source_column_name(row, base)
    row[column] = value
    return column
def normalize_source_lang(value: str) -> str:
    token = (value or "").strip()
    if not token:
        return ""
    return _SOURCE_LANGUAGE_NORMALIZATION.get(token.casefold(), "")


def source_language_for_row(row: dict[str, str]) -> str:
    return normalize_source_lang(_first_non_empty(row, ["Source_lang", "source_lang"]))


def _source_language_uses_latin_script(source_lang: str) -> bool:
    return normalize_source_lang(source_lang) == "en"


def _contains_east_asian_text(value: str) -> bool:
    for ch in value or "":
        codepoint = ord(ch)
        if 0x3400 <= codepoint <= 0x4DBF:
            return True
        if 0x4E00 <= codepoint <= 0x9FFF:
            return True
        if 0x3040 <= codepoint <= 0x30FF:
            return True
        if 0x31F0 <= codepoint <= 0x31FF:
            return True
        if 0xAC00 <= codepoint <= 0xD7AF:
            return True
    return False


def _sort_text_numbers(values: set[str]) -> tuple[str, ...]:
    def sort_key(raw: str) -> tuple[int, float | str]:
        text = (raw or "").strip()
        try:
            return (0, float(text))
        except ValueError:
            return (1, text)

    return tuple(sorted((value for value in values if (value or "").strip()), key=sort_key))


def _template_row_metadata(row_key: str) -> tuple[str, str, str] | None:
    binding = _legacy_page_value_binding(row_key)
    if binding is None:
        return None
    return (binding.section, binding.section_order, binding.row_label_source)


def _is_template_row(row_key: str, section: str, row: dict[str, str] | None = None) -> bool:
    if row is not None and is_page_value_row(row):
        return True
    return (row_key or "").strip().lower().startswith("tpl_") or ((section or "").strip().upper() == "TEMPLATE VARS")


def _pick_section(row: dict[str, str]) -> str:
    return _first_non_empty(row, ["Section", "section"])


def _pick_section_order(row: dict[str, str]) -> str:
    return _first_non_empty(row, ["Section_order", "section_order"])


def _pick_row_label_source(row: dict[str, str]) -> str:
    return _pick_source_value(row, "Row_label")


def _normalize_section_summary(section: str) -> tuple[str, str, str]:
    suggested_section, category, note = _SECTION_NORMALIZATION_RULES.get(
        section,
        (section, "spec", ""),
    )
    return suggested_section, category, note


def _is_truthy(value: str) -> bool:
    text = (value or "").strip().lower()
    if not text:
        return True
    return text in {"1", "true", "yes", "y"}


def _pick_lang_value(row: dict[str, str], base: str, lang: str) -> str:
    normalized_lang = (lang or "").strip().lower()
    source_lang = source_language_for_row(row)
    keys: list[str] = []
    if base in _SOURCE_SHARED_BASES and (normalized_lang == "en" or (source_lang and normalized_lang == source_lang)):
        keys.extend(_source_column_names(base))
    else:
        keys.extend(
            [
                f"{base}_{lang}",
                f"{base}_{lang.lower()}",
                f"{base}_{lang.upper()}",
            ]
        )
        if base in _SOURCE_SHARED_BASES:
            keys.extend(_source_column_names(base))
    keys.extend([base, "Spec_Value"])
    keys = list(dict.fromkeys(keys))
    return _first_non_empty(row, keys)


def _pick_row_key(row: dict[str, str]) -> str:
    return _first_non_empty(row, ["Row_key", "row_key"]).lower()


def _pick_row_model(row: dict[str, str]) -> str:
    return _first_non_empty(
        row,
        ["Model", "model", "Product_Model", "product_model", "Model_No", "model_no"],
    )


def _pick_row_region(row: dict[str, str]) -> str:
    return _first_non_empty(row, ["Region", "region"])


def _normalize_slot_key(raw: str) -> str:
    tokens = [token.strip().lower() for token in str(raw).replace("/", ".").split(".") if token.strip()]
    return ".".join(tokens)


def _compose_slot_key(
    *,
    placement_key: str = "",
    variant_key: str = "",
    value_role: str = "",
) -> str:
    role_token = (value_role or "").strip().lower() or "value"
    parts: list[str] = []
    if placement_key:
        parts.append((placement_key or "").strip().lower())
    if variant_key:
        parts.append((variant_key or "").strip().lower())
    parts.append(role_token)
    return ".".join(part for part in parts if part)


def _parse_slot_key(raw: str) -> tuple[str, str, str] | None:
    slot_key = _normalize_slot_key(raw)
    if not slot_key:
        return None

    parts = slot_key.split(".")
    if len(parts) == 1:
        placement_key = ""
        variant_key = ""
        role_token = parts[0]
    elif len(parts) == 2:
        placement_key = parts[0]
        variant_key = ""
        role_token = parts[1]
    elif len(parts) == 3:
        placement_key = parts[0]
        variant_key = parts[1]
        role_token = parts[2]
    else:
        return None

    value_role = "" if role_token in _SLOT_KEY_VALUE_ALIASES else role_token
    return placement_key, variant_key, value_role


def _pick_slot_key(row: dict[str, str]) -> str:
    raw = _first_non_empty(row, ["Slot_key", "slot_key"])
    if raw:
        return _normalize_slot_key(raw)

    legacy_binding = _legacy_page_value_binding(_pick_row_key(row))
    if legacy_binding is not None:
        return _compose_slot_key(
            placement_key=legacy_binding.placement_key,
            variant_key=legacy_binding.variant_key,
            value_role=legacy_binding.value_role,
        )

    usage_type = _first_non_empty(row, ["Usage_type", "usage_type", "Row_type", "row_type"]).lower()
    if usage_type != "page_value":
        return ""

    return _compose_slot_key(
        placement_key=_first_non_empty(row, ["Placement_key", "placement_key"]).lower(),
        variant_key=_first_non_empty(row, ["Variant_key", "variant_key"]).lower(),
        value_role=_first_non_empty(row, ["Value_role", "value_role"]).lower(),
    )


def _pick_usage_type(row: dict[str, str]) -> str:
    raw = _first_non_empty(row, ["Usage_type", "usage_type", "Row_type", "row_type"]).lower()
    if raw:
        return raw
    if _pick_slot_key(row):
        return "page_value"
    return ""


def _pick_placement_key(row: dict[str, str]) -> str:
    raw = _first_non_empty(row, ["Placement_key", "placement_key"]).lower()
    if raw:
        return raw
    parsed = _parse_slot_key(_pick_slot_key(row))
    return parsed[0] if parsed is not None else ""


def _pick_value_role(row: dict[str, str]) -> str:
    raw = _first_non_empty(row, ["Value_role", "value_role"]).lower()
    if raw:
        return raw
    parsed = _parse_slot_key(_pick_slot_key(row))
    return parsed[2] if parsed is not None else ""


def _pick_variant_key(row: dict[str, str]) -> str:
    raw = _first_non_empty(row, ["Variant_key", "variant_key"]).lower()
    if raw:
        return raw
    parsed = _parse_slot_key(_pick_slot_key(row))
    return parsed[1] if parsed is not None else ""


def _page_value_signature(
    *,
    row_key: str,
    usage_type: str = "",
    placement_key: str = "",
    value_role: str = "",
    variant_key: str = "",
) -> tuple[str, str, str, str, str]:
    return (
        (row_key or "").strip().lower(),
        (usage_type or "").strip().lower(),
        (placement_key or "").strip().lower(),
        (value_role or "").strip().lower(),
        (variant_key or "").strip().lower(),
    )


def _legacy_page_value_binding(row_key: str) -> PageValueBinding | None:
    return _LEGACY_PAGE_VALUE_BINDINGS.get((row_key or "").strip().lower())


def _row_page_value_binding(row: dict[str, str]) -> PageValueBinding | None:
    legacy_binding = _legacy_page_value_binding(_pick_row_key(row))
    if legacy_binding is not None:
        return legacy_binding

    if _pick_usage_type(row) != "page_value":
        return None

    row_key = _pick_row_key(row)
    if not row_key:
        return None

    return PageValueBinding(
        row_key=row_key,
        section=_pick_section(row),
        section_order=_pick_section_order(row),
        row_label_source=_pick_row_label_source(row),
        placement_key=_pick_placement_key(row),
        value_role=_pick_value_role(row),
        variant_key=_pick_variant_key(row),
        usage_type="page_value",
    )


def is_page_value_row(row: dict[str, str]) -> bool:
    return _row_page_value_binding(row) is not None


def resolve_legacy_page_value_key(row: dict[str, str]) -> str | None:
    binding = _row_page_value_binding(row)
    if binding is None:
        return None
    return _LEGACY_PAGE_VALUE_KEYS_BY_SIGNATURE.get(
        _page_value_signature(
            row_key=binding.row_key,
            usage_type=binding.usage_type,
            placement_key=binding.placement_key,
            value_role=binding.value_role,
            variant_key=binding.variant_key,
        )
    )


def resolve_page_value_placeholder_name(row: dict[str, str]) -> str | None:
    binding = _row_page_value_binding(row)
    if binding is None:
        return None

    legacy_key = resolve_legacy_page_value_key(row)
    if legacy_key is not None and legacy_key.startswith("tpl_"):
        return legacy_key[4:].upper()

    parts: list[str] = []
    if binding.placement_key:
        parts.append(binding.placement_key.upper())
    parts.append(binding.row_key.upper())
    if binding.variant_key:
        parts.append(binding.variant_key.upper())
    if binding.value_role:
        parts.append(binding.value_role.upper())
    return "_".join(part for part in parts if part)


def page_value_role(row: dict[str, str]) -> str:
    binding = _row_page_value_binding(row)
    return binding.value_role if binding is not None else ""


def _page_value_metadata_from_row(row: dict[str, str]) -> tuple[str, str, str] | None:
    binding = _row_page_value_binding(row)
    if binding is None:
        return None
    return (binding.section, binding.section_order, binding.row_label_source)


def normalize_page_tokens(raw: str | None) -> tuple[str, ...]:
    if raw is None:
        return ()
    return tuple(token for token in (item.strip().lower() for item in str(raw).split(",")) if token)


def _normalize_page_filters(pages: str | list[str] | tuple[str, ...] | set[str] | None) -> set[str] | None:
    if pages is None:
        return None
    if isinstance(pages, str):
        raw_items = [pages]
    else:
        raw_items = list(pages)

    normalized = {
        token
        for item in raw_items
        for token in normalize_page_tokens(item)
    }
    return normalized or None


def page_value_matches(
    raw_page: str | None,
    pages: str | list[str] | tuple[str, ...] | set[str] | None,
) -> bool:
    page_filters = _normalize_page_filters(pages)
    if not page_filters:
        return True
    page_tokens = set(normalize_page_tokens(raw_page))
    if not page_tokens:
        return True
    return not page_filters.isdisjoint(page_tokens)


def _row_matches_target(
    row: dict[str, str],
    *,
    model: str | None,
    region: str | None,
    row_key: str | None = None,
    pages: str | list[str] | tuple[str, ...] | set[str] | None = None,
    line_order: str | int | None = None,
    usage_type: str | None = None,
    placement_key: str | None = None,
    value_role: str | None = None,
    variant_key: str | None = None,
) -> bool:
    if not _is_truthy(_first_non_empty(row, ["enabled", "Enabled"])):
        return False
    if not _is_truthy(_first_non_empty(row, ["Is_Latest", "is_latest"])):
        return False

    target_key = (row_key or "").strip().lower()
    legacy_binding = _legacy_page_value_binding(target_key) if target_key else None
    if legacy_binding is not None:
        row_binding = _row_page_value_binding(row)
        if row_binding is None:
            return False
        if _page_value_signature(
            row_key=row_binding.row_key,
            usage_type=row_binding.usage_type,
            placement_key=row_binding.placement_key,
            value_role=row_binding.value_role,
            variant_key=row_binding.variant_key,
        ) != _page_value_signature(
            row_key=legacy_binding.row_key,
            usage_type=legacy_binding.usage_type,
            placement_key=legacy_binding.placement_key,
            value_role=legacy_binding.value_role,
            variant_key=legacy_binding.variant_key,
        ):
            return False
    elif target_key and _pick_row_key(row) != target_key:
        return False

    if not page_value_matches(_first_non_empty(row, ["Page", "page"]), pages):
        return False

    target_model = (model or "").strip()
    row_model = _pick_row_model(row)
    if target_model and row_model and row_model != target_model:
        return False

    target_region = (region or "").strip()
    row_region = _pick_row_region(row)
    if target_region and row_region and row_region != target_region:
        return False

    if line_order is not None:
        wanted = str(line_order).strip()
        if wanted and _first_non_empty(row, ["Line_order", "line_order"]) != wanted:
            return False

    if usage_type or placement_key or value_role or variant_key:
        row_binding = _row_page_value_binding(row)
        if row_binding is None:
            return False
        if usage_type and row_binding.usage_type != (usage_type or "").strip().lower():
            return False
        if placement_key and row_binding.placement_key != (placement_key or "").strip().lower():
            return False
        if value_role and row_binding.value_role != (value_role or "").strip().lower():
            return False
        if variant_key and row_binding.variant_key != (variant_key or "").strip().lower():
            return False

    return True


def _score_row(
    row: dict[str, str],
    *,
    model: str | None,
    region: str | None,
    lang: str,
) -> int:
    target_model = (model or "").strip()
    target_region = (region or "").strip()
    row_model = _pick_row_model(row)
    row_region = _pick_row_region(row)

    score = 0
    if row_model and target_model and row_model == target_model:
        score += 8
    if row_region and target_region and row_region == target_region:
        score += 8
    if not target_region and not row_region:
        score += 2

    if _pick_lang_value(row, "Value", lang):
        score += 2
    if _first_non_empty(row, ["Is_Latest", "is_latest"]):
        score += 1
    return score


def _row_line_num(row: dict[str, str], idx: int) -> int:
    line_num_text = (row.get("__line__") or "0").strip()
    try:
        return int(line_num_text)
    except ValueError:
        return idx + 2


def _iter_ranked_rows(
    rows: list[dict[str, str]],
    *,
    model: str | None,
    region: str | None,
    lang: str,
    row_key: str | None = None,
    pages: str | list[str] | tuple[str, ...] | set[str] | None = None,
    line_order: str | int | None = None,
    usage_type: str | None = None,
    placement_key: str | None = None,
    value_role: str | None = None,
    variant_key: str | None = None,
) -> list[dict[str, str]]:
    target_model = (model or "").strip()
    target_region = (region or "").strip()
    candidates: list[tuple[int, int, int, dict[str, str]]] = []
    for idx, row in enumerate(rows):
        if not _row_matches_target(
            row,
            model=target_model or None,
            region=target_region or None,
            row_key=row_key,
            pages=pages,
            line_order=line_order,
            usage_type=usage_type,
            placement_key=placement_key,
            value_role=value_role,
            variant_key=variant_key,
        ):
            continue
        score = _score_row(row, model=target_model or None, region=target_region or None, lang=lang)
        candidates.append((score, _row_line_num(row, idx), idx, row))

    candidates.sort(key=lambda x: (-x[0], x[1], x[2]))
    return [item[3] for item in candidates]


def resolve_spec_value_from_rows(
    rows: list[dict[str, str]],
    *,
    model: str | None,
    region: str | None,
    lang: str,
    row_key: str,
    pages: str | list[str] | tuple[str, ...] | set[str] | None = ("spec", "specifications"),
    line_order: str | int | None = None,
    usage_type: str | None = None,
    placement_key: str | None = None,
    value_role: str | None = None,
    variant_key: str | None = None,
) -> SpecValueMatch | None:
    for row in _iter_ranked_rows(
        rows,
        model=model,
        region=region,
        lang=lang,
        row_key=row_key,
        pages=pages,
        line_order=line_order,
        usage_type=usage_type,
        placement_key=placement_key,
        value_role=value_role,
        variant_key=variant_key,
    ):
        value = _pick_lang_value(row, "Value", lang)
        if value:
            return SpecValueMatch(
                value=value,
                region=_pick_row_region(row) or None,
                row=row,
            )
    return None


def collect_matching_spec_rows(
    rows: list[dict[str, str]],
    *,
    model: str | None,
    region: str | None,
    lang: str,
    row_key: str,
    pages: str | list[str] | tuple[str, ...] | set[str] | None = ("spec", "specifications"),
    line_order: str | int | None = None,
    usage_type: str | None = None,
    placement_key: str | None = None,
    value_role: str | None = None,
    variant_key: str | None = None,
) -> tuple[dict[str, str], ...]:
    return tuple(
        _iter_ranked_rows(
            rows,
            model=model,
            region=region,
            lang=lang,
            row_key=row_key,
            pages=pages,
            line_order=line_order,
            usage_type=usage_type,
            placement_key=placement_key,
            value_role=value_role,
            variant_key=variant_key,
        )
    )


def collect_spec_value_matches_from_rows(
    rows: list[dict[str, str]],
    *,
    model: str | None,
    region: str | None,
    lang: str,
    row_key: str,
    pages: str | list[str] | tuple[str, ...] | set[str] | None = ("spec", "specifications"),
    line_order: str | int | None = None,
    usage_type: str | None = None,
    placement_key: str | None = None,
    value_role: str | None = None,
    variant_key: str | None = None,
) -> tuple[SpecValueMatch, ...]:
    matches: list[SpecValueMatch] = []
    for row in collect_matching_spec_rows(
        rows,
        model=model,
        region=region,
        lang=lang,
        row_key=row_key,
        pages=pages,
        line_order=line_order,
        usage_type=usage_type,
        placement_key=placement_key,
        value_role=value_role,
        variant_key=variant_key,
    ):
        value = _pick_lang_value(row, "Value", lang)
        if not value:
            continue
        matches.append(
            SpecValueMatch(
                value=value,
                region=_pick_row_region(row) or None,
                row=row,
            )
        )
    return tuple(matches)


def _derive_short_product_name(name: str) -> str:
    text = (name or "").strip()
    if not text:
        return ""
    prefix = "Jackery "
    if text.startswith(prefix):
        return text[len(prefix) :].strip()
    return text


def _derive_label_lower(value: str) -> str:
    tokens = value.split()
    lowered: list[str] = []
    for token in tokens:
        if token.upper() == "BUTTON":
            lowered.append("button")
            continue
        if token.isupper():
            lowered.append(token)
            continue
        lowered.append(token.lower())
    return " ".join(lowered)


def _normalize_line_order_suffix(line_order: str) -> str:
    text = (line_order or "").strip()
    if not text:
        return "1"
    if text.endswith(".0"):
        text = text[:-2]
    return text or "1"


def _compose_placeholder_line_value(row: dict[str, str], *, lang: str) -> str:
    direct_text = _pick_lang_value(row, "line_text", lang)
    if direct_text:
        return direct_text

    param = _pick_lang_value(row, "Param", lang)
    value = _pick_lang_value(row, "Value", lang)
    if param and value:
        separator = _first_non_empty(row, ["param_value_sep", "Param_value_sep"])
        if not separator:
            separator = " : " if lang == "fr" else "：" if lang == "ja" else ": "
        return f"{param}{separator}{value}"
    return value or param


def _with_derived_substitutions(substitutions: dict[str, str]) -> dict[str, str]:
    out = dict(substitutions)
    for key, value in list(out.items()):
        if key.endswith("_BOLD") or key.endswith("_LOWER"):
            continue
        if value:
            out.setdefault(f"{key}_BOLD", f"**{value}**")
        if key.endswith("_LABEL"):
            out.setdefault(f"{key}_LOWER", _derive_label_lower(value))
    return out


def resolve_template_substitutions_from_rows(
    rows: list[dict[str, str]],
    *,
    model: str | None,
    region: str | None,
    lang: str,
) -> dict[str, str]:
    substitutions: dict[str, str] = {}

    product_match = resolve_spec_value_from_rows(
        rows,
        model=model,
        region=region,
        lang=lang,
        row_key="product_name",
        pages=None,
    )
    if product_match:
        substitutions["PRODUCT_NAME"] = product_match.value
        short_name = _derive_short_product_name(product_match.value)
        if short_name:
            substitutions["PRODUCT_SHORT_NAME"] = short_name

    model_match = resolve_spec_value_from_rows(
        rows,
        model=model,
        region=region,
        lang=lang,
        row_key="model_no",
        pages=None,
    )
    if model_match:
        substitutions["MODEL_NO"] = model_match.value

    for row in _iter_ranked_rows(
        rows,
        model=model,
        region=region,
        lang=lang,
        pages=None,
    ):
        placeholder = resolve_page_value_placeholder_name(row)
        if not placeholder:
            continue

        value = _pick_lang_value(row, "Value", lang)
        if not value:
            continue

        line_order_value = _first_non_empty(row, ["Line_order", "line_order"])
        if line_order_value not in {"", "1", "1.0"}:
            placeholder = f"{placeholder}_{line_order_value.replace('.', '_')}"
        substitutions.setdefault(placeholder, value)

    for row_key, (placeholder_base, pages) in _DERIVED_MULTILINE_PLACEHOLDERS.items():
        for row in _iter_ranked_rows(
            rows,
            model=model,
            region=region,
            lang=lang,
            row_key=row_key,
            pages=pages,
        ):
            line_order_value = _normalize_line_order_suffix(_first_non_empty(row, ["Line_order", "line_order"]))
            param = _pick_lang_value(row, "Param", lang)
            value = _pick_lang_value(row, "Value", lang)
            line_value = _compose_placeholder_line_value(row, lang=lang)
            if line_value:
                substitutions.setdefault(f"{placeholder_base}_LINE_{line_order_value}", line_value)
            if param:
                substitutions.setdefault(f"{placeholder_base}_PARAM_{line_order_value}", param)
            if value:
                substitutions.setdefault(f"{placeholder_base}_VALUE_{line_order_value}", value)

    return _with_derived_substitutions(substitutions)


def resolve_product_name_from_rows(
    rows: list[dict[str, str]],
    *,
    model: str | None,
    region: str | None,
    lang: str,
) -> ProductNameMatch | None:
    match = resolve_spec_value_from_rows(
        rows,
        model=model,
        region=region,
        lang=lang,
        row_key="product_name",
        pages=None,
    )
    if not match:
        return None
    return ProductNameMatch(product_name=match.value, region=match.region)


def resolve_product_name_from_spec_master(
    spec_master_csv: Path,
    *,
    model: str | None,
    region: str | None,
    lang: str,
) -> ProductNameMatch | None:
    rows = _read_csv_rows(spec_master_csv)
    if not rows:
        return None
    return resolve_product_name_from_rows(rows, model=model, region=region, lang=lang)


def resolve_template_substitutions_from_spec_master(
    spec_master_csv: Path,
    *,
    model: str | None,
    region: str | None,
    lang: str,
) -> dict[str, str]:
    rows = _read_csv_rows(spec_master_csv)
    if not rows:
        return {}
    return resolve_template_substitutions_from_rows(rows, model=model, region=region, lang=lang)


def read_spec_master_rows(spec_master_csv: Path) -> list[dict[str, str]]:
    return _read_csv_rows(spec_master_csv)


def audit_spec_master_rows(rows: list[dict[str, str]]) -> SpecMasterAuditResult:
    section_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    order_map: dict[str, set[str]] = defaultdict(set)
    issues: list[SpecMasterAuditIssue] = []

    for row in rows:
        section = _pick_section(row)
        if section:
            section_groups[section].append(row)
            order_value = _pick_section_order(row)
            if order_value:
                order_map[order_value].add(section)

    order_conflicts: list[SpecMasterSectionOrderConflict] = []
    for order_value in _sort_text_numbers(set(order_map)):
        sections = tuple(sorted(order_map[order_value]))
        if len(sections) <= 1:
            continue
        order_conflicts.append(
            SpecMasterSectionOrderConflict(
                section_order=order_value,
                sections=sections,
            )
        )
        issues.append(
            SpecMasterAuditIssue(
                code="SECTION_ORDER_COLLISION",
                message=(
                    f"Section_order `{order_value}` is shared by multiple sections: "
                    f"{', '.join(sections)}"
                ),
                line=None,
                model=None,
                region=None,
                section=None,
                row_key=None,
            )
        )

    section_summaries: list[SpecMasterSectionSummary] = []
    for section, grouped_rows in section_groups.items():
        suggested_section, category, note = _normalize_section_summary(section)
        section_summaries.append(
            SpecMasterSectionSummary(
                section=section,
                suggested_section=suggested_section,
                category=category,
                row_count=len(grouped_rows),
                orders=_sort_text_numbers({_pick_section_order(row) for row in grouped_rows}),
                models=tuple(sorted({_pick_row_model(row) for row in grouped_rows if _pick_row_model(row)})),
                regions=tuple(sorted({_pick_row_region(row) for row in grouped_rows if _pick_row_region(row)})),
                note=note,
            )
        )

    def summary_sort_key(item: SpecMasterSectionSummary) -> tuple[tuple[int, float | str], str]:
        order_value = item.orders[0] if item.orders else ""
        try:
            return ((0, float(order_value)), item.section)
        except ValueError:
            return ((1, order_value), item.section)

    section_summaries.sort(key=summary_sort_key)

    seen_rows: dict[tuple[tuple[str, str], ...], int] = {}
    for idx, row in enumerate(rows):
        line_number = _row_line_num(row, idx)
        region = _pick_row_region(row) or None
        section = _pick_section(row) or None
        row_key = _pick_row_key(row) or None
        model = _pick_row_model(row) or None

        source_label = _pick_row_label_source(row)
        if (
            source_label
            and _source_language_uses_latin_script(source_language_for_row(row))
            and _contains_east_asian_text(source_label)
        ):
            issues.append(
                SpecMasterAuditIssue(
                    code="ROW_LABEL_SOURCE_CONTAINS_EAST_ASIAN_TEXT",
                    message=(
                        "`Row_label_source` contains East Asian text for row "
                        f"(region `{(region or '').strip().upper()}`) whose declared source language is "
                        f"`{source_language_for_row(row) or 'unknown'}`: {source_label}"
                    ),
                    line=line_number,
                    model=model,
                    region=region,
                    section=section,
                    row_key=row_key,
                )
            )

        raw_slot_key = _first_non_empty(row, ["Slot_key", "slot_key"])
        if raw_slot_key and _parse_slot_key(raw_slot_key) is None:
            issues.append(
                SpecMasterAuditIssue(
                    code="INVALID_SLOT_KEY",
                    message=(
                        f"`Slot_key` must use `role`, `placement.role`, or "
                        f"`placement.variant.role`: {raw_slot_key}"
                    ),
                    line=line_number,
                    model=model,
                    region=region,
                    section=section,
                    row_key=row_key,
                )
            )

        source_value = _pick_source_value(row, "Value")
        if _is_template_row(row_key, section, row) and "?" in source_value:
            issues.append(
                SpecMasterAuditIssue(
                    code="SUSPECT_TEMPLATE_VALUE",
                    message=f"Template value contains literal `?`: {source_value}",
                    line=line_number,
                    model=model,
                    region=region,
                    section=section,
                    row_key=row_key,
                )
            )

        normalized_items = tuple(sorted((key, row.get(key, "")) for key in row if key != "__line__"))
        previous_line = seen_rows.get(normalized_items)
        if previous_line is not None:
            issues.append(
                SpecMasterAuditIssue(
                    code="EXACT_DUPLICATE_ROW",
                    message=f"Row duplicates line {previous_line}",
                    line=line_number,
                    model=model,
                    region=region,
                    section=section,
                    row_key=row_key,
                )
            )
        else:
            seen_rows[normalized_items] = line_number

    issues.sort(
        key=lambda item: (
            item.code,
            item.line if item.line is not None else -1,
            item.section or "",
            item.row_key or "",
        )
    )

    return SpecMasterAuditResult(
        total_rows=len(rows),
        unique_sections=len(section_summaries),
        section_summaries=tuple(section_summaries),
        order_conflicts=tuple(order_conflicts),
        issues=tuple(issues),
    )


def audit_spec_master_csv(spec_master_csv: Path) -> SpecMasterAuditResult:
    return audit_spec_master_rows(read_spec_master_rows(spec_master_csv))


def _row_issue_map(issues: tuple[SpecMasterAuditIssue, ...]) -> dict[int, list[SpecMasterAuditIssue]]:
    issue_map: dict[int, list[SpecMasterAuditIssue]] = defaultdict(list)
    for issue in issues:
        if issue.line is None:
            continue
        issue_map[issue.line].append(issue)
    return issue_map


def normalize_spec_master_rows(rows: list[dict[str, str]]) -> SpecMasterNormalizationResult:
    audit = audit_spec_master_rows(rows)
    issue_map = _row_issue_map(audit.issues)
    conflicting_orders = {conflict.section_order for conflict in audit.order_conflicts}

    normalized_rows: list[dict[str, str]] = []
    anomaly_rows: list[dict[str, str]] = []

    for idx, raw_row in enumerate(rows):
        row = {key: value for key, value in raw_row.items() if key != "__line__"}
        line_number = str(_row_line_num(raw_row, idx))
        original_section = _pick_section(raw_row)
        normalized_section, category, note = _normalize_section_summary(original_section)
        row_key = _pick_row_key(raw_row)

        if _is_template_row(row_key, original_section, raw_row):
            category = "template"
            if not note:
                note = "Template placeholder row should remain distinguishable even when grouped under a mapped section."

        review_flags: list[str] = []
        review_messages: list[str] = []

        if original_section != normalized_section:
            review_flags.append("SECTION_NORMALIZED")
            review_messages.append(
                f"Section normalized from `{original_section}` to `{normalized_section}`"
            )
        if category == "template":
            review_flags.append("TEMPLATE_RECORD")
            review_messages.append(
                "Template placeholder row is kept in the derived output but should be split from the spec source."
            )
        section_order = _pick_section_order(raw_row)
        if section_order and section_order in conflicting_orders:
            review_flags.append("SECTION_ORDER_COLLISION")
            review_messages.append(
                f"Section_order `{section_order}` is shared by multiple sections."
            )
        for issue in issue_map.get(int(line_number), []):
            review_flags.append(issue.code)
            review_messages.append(issue.message)

        deduped_flags = list(dict.fromkeys(review_flags))
        deduped_messages = list(dict.fromkeys(review_messages))

        normalized_row = dict(row)
        normalized_row["Section_original"] = original_section
        normalized_row["Section"] = normalized_section
        normalized_row["Section_normalized"] = normalized_section
        normalized_row["Record_category"] = category
        normalized_row["Normalization_applied"] = "YES" if original_section != normalized_section else "NO"
        normalized_row["Normalization_note"] = note
        normalized_row["Source_line"] = line_number
        normalized_row["Review_flags"] = ";".join(deduped_flags)
        normalized_row["Review_messages"] = " | ".join(deduped_messages)
        normalized_rows.append(normalized_row)

        if deduped_flags:
            anomaly_rows.append(normalized_row)

    return SpecMasterNormalizationResult(
        normalized_rows=tuple(normalized_rows),
        anomaly_rows=tuple(anomaly_rows),
    )


def normalize_spec_master_csv(spec_master_csv: Path) -> SpecMasterNormalizationResult:
    return normalize_spec_master_rows(read_spec_master_rows(spec_master_csv))


def build_template_row_key_mapping_rows(
    rows: list[dict[str, str]],
) -> tuple[dict[str, str], ...]:
    usage: dict[str, dict[str, object]] = defaultdict(
        lambda: {
            "count": 0,
            "models": set(),
            "regions": set(),
            "sections": set(),
            "section_orders": set(),
            "row_labels": set(),
        }
    )

    for raw_row in rows:
        row_key = _pick_row_key(raw_row)
        if not _is_template_row(row_key, _pick_section(raw_row), raw_row):
            continue

        metadata = _page_value_metadata_from_row(raw_row)
        if metadata is None:
            continue

        usage_row = usage[resolve_legacy_page_value_key(raw_row) or row_key]
        usage_row["count"] = int(usage_row["count"]) + 1

        model = (_pick_row_model(raw_row) or "").strip()
        if model:
            cast(set[str], usage_row["models"]).add(model)

        region = (_pick_row_region(raw_row) or "").strip().upper()
        if region:
            cast(set[str], usage_row["regions"]).add(region)

        section = _pick_section(raw_row).strip()
        if section:
            cast(set[str], usage_row["sections"]).add(section)

        section_order = _pick_section_order(raw_row).strip()
        if section_order:
            cast(set[str], usage_row["section_orders"]).add(section_order)

        row_label = _pick_row_label_source(raw_row).strip()
        if row_label:
            cast(set[str], usage_row["row_labels"]).add(row_label)

    mapping_rows: list[dict[str, str]] = []
    for row_key, binding in _LEGACY_PAGE_VALUE_BINDINGS.items():
        observed = usage.get(row_key)
        models = sorted(cast(set[str], observed["models"])) if observed else []
        regions = sorted(cast(set[str], observed["regions"])) if observed else []
        sections = sorted(cast(set[str], observed["sections"])) if observed else []
        section_orders = sorted(cast(set[str], observed["section_orders"])) if observed else []
        row_labels = sorted(cast(set[str], observed["row_labels"])) if observed else []
        usage_count = str(int(observed["count"])) if observed else "0"

        mapping_rows.append(
            {
                "Row_key": row_key,
                "Section": binding.section,
                "Section_order": binding.section_order,
                "Row_label_source": binding.row_label_source,
                "Usage_count": usage_count,
                "Models": ",".join(models),
                "Regions": ",".join(regions),
                "Observed_sections": ",".join(sections),
                "Observed_section_orders": ",".join(section_orders),
                "Observed_row_labels_source": " | ".join(row_labels),
            }
        )

    return tuple(
        sorted(
            mapping_rows,
            key=lambda row: (
                int(row["Section_order"]),
                row["Section"],
                row["Row_label_source"],
                row["Row_key"],
            ),
        )
    )


def build_row_label_row_key_mapping_rows(
    rows: list[dict[str, str]],
    existing_rows: list[dict[str, str]] | None = None,
) -> tuple[dict[str, str], ...]:
    observed_keys: dict[tuple[str, str], set[str]] = defaultdict(set)

    for raw_row in rows:
        if not _is_truthy(_first_non_empty(raw_row, ["Is_Latest", "is_latest"])):
            continue

        row_label = _pick_row_label_source(raw_row).strip()
        if not row_label:
            continue

        line_order = _normalize_line_order_suffix(_first_non_empty(raw_row, ["Line_order", "line_order"]))
        row_key = _pick_row_key(raw_row).strip()
        if row_key:
            observed_keys[(row_label, line_order)].add(row_key)

    existing_by_pair: dict[tuple[str, str], dict[str, str]] = {}
    existing_by_label: dict[str, dict[str, str]] = {}
    for raw_row in existing_rows or []:
        row_label = (raw_row.get("Row_label_source") or "").strip()
        if not row_label:
            continue

        line_order = (raw_row.get("Line_order") or "").strip()
        record = {
            "Row_key": (raw_row.get("Row_key") or "").strip(),
            "Remark": (raw_row.get("Remark") or "").strip(),
        }
        if line_order:
            existing_by_pair[(row_label, line_order)] = record
        else:
            existing_by_label[row_label] = record

    mapping_rows: list[dict[str, str]] = []
    observed_pairs = set(observed_keys)
    observed_labels = {row_label for row_label, _line_order in observed_pairs}
    observed_pairs.update(existing_by_pair)
    observed_pairs.update(
        (row_label, "")
        for row_label in existing_by_label
        if row_label not in observed_labels
    )

    def _line_order_sort_key(value: str) -> tuple[int, str]:
        if value.isdigit():
            return (0, f"{int(value):08d}")
        if not value:
            return (1, "")
        return (2, value)

    for row_label, line_order in sorted(
        observed_pairs,
        key=lambda item: (item[0], _line_order_sort_key(item[1])),
    ):
        existing_row = existing_by_pair.get((row_label, line_order), {})
        fallback_row = existing_by_label.get(row_label, {})
        row_key = existing_row.get("Row_key", "").strip()
        if not row_key:
            row_key = fallback_row.get("Row_key", "").strip()
        if not row_key:
            candidate_row_keys = sorted(observed_keys.get((row_label, line_order), set()))
            if candidate_row_keys:
                row_key = candidate_row_keys[0]

        mapping_rows.append(
            {
                "Row_label_source": row_label,
                "Line_order": line_order,
                "Row_key": row_key,
                "Remark": existing_row.get("Remark", "").strip()
                or fallback_row.get("Remark", "").strip(),
            }
        )

    return tuple(mapping_rows)


def build_row_label_row_key_mapping_markdown(
    mapping_rows: tuple[dict[str, str], ...],
) -> str:
    lines = [
        "# Spec Master Row Label to Row Key Mapping",
        "",
        "Manual mapping reference for `Spec_Master.csv` `Row_label_source + Line_order` to `Row_key` lookup.",
        "",
        "| Row_label_source | Line_order | Row_key | Remark |",
        "| --- | ---: | --- | --- |",
    ]

    for row in mapping_rows:
        lines.append(
            "| {row_label} | {line_order} | {row_key} | {remark} |".format(
                row_label=row["Row_label_source"],
                line_order=row["Line_order"] or "-",
                row_key=row["Row_key"],
                remark=row["Remark"] or "-",
            )
        )

    lines.append("")
    return "\n".join(lines)


def build_template_row_key_mapping_markdown(
    mapping_rows: tuple[dict[str, str], ...],
) -> str:
    lines = [
        "# Spec Master Row Key Mapping",
        "",
        "Grouped canonical mapping for template-style `row_key` values.",
        "",
    ]

    grouped_rows: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in mapping_rows:
        grouped_rows[(row["Section_order"], row["Section"])].append(row)

    for section_order, section in sorted(grouped_rows, key=lambda item: (int(item[0]), item[1])):
        rows_in_section = sorted(
            grouped_rows[(section_order, section)],
            key=lambda row: (row["Row_label_source"], row["Row_key"]),
        )
        lines.extend(
            [
                f"## {section} (`{section_order}`)",
                "",
                "| Row_key | Row_label_source | Usage_count | Models | Regions |",
                "| --- | --- | ---: | --- | --- |",
            ]
        )
        for row in rows_in_section:
            lines.append(
                "| {row_key} | {row_label} | {usage} | {models} | {regions} |".format(
                    row_key=row["Row_key"],
                    row_label=row["Row_label_source"],
                    usage=row["Usage_count"],
                    models=row["Models"] or "-",
                    regions=row["Regions"] or "-",
                )
            )
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def repair_known_spec_master_values(rows: list[dict[str, str]]) -> SpecMasterRepairResult:
    repaired_rows: list[dict[str, str]] = []
    applied_repairs: list[SpecMasterAppliedRepair] = []

    for idx, raw_row in enumerate(rows):
        row = dict(raw_row)
        line_number = _row_line_num(raw_row, idx)
        model = _pick_row_model(row)
        region = _pick_row_region(row)
        row_key = _pick_row_key(row)
        template_metadata = _page_value_metadata_from_row(row)

        old_section = row.get("Section", "")
        new_section, _, _ = _normalize_section_summary(old_section)
        if old_section != new_section:
            row["Section"] = new_section
            applied_repairs.append(
                SpecMasterAppliedRepair(
                    line=line_number,
                    model=model or None,
                    region=region or None,
                    row_key=row_key or None,
                    column="Section",
                    old_value=old_section,
                    new_value=new_section,
                )
            )

        if template_metadata is not None:
            mapped_section, mapped_section_order, mapped_row_label = template_metadata

            if row.get("Section", "") != mapped_section:
                applied_repairs.append(
                    SpecMasterAppliedRepair(
                        line=line_number,
                        model=model or None,
                        region=region or None,
                        row_key=row_key or None,
                        column="Section",
                        old_value=row.get("Section", ""),
                        new_value=mapped_section,
                    )
                )
                row["Section"] = mapped_section

            old_section_order = row.get("Section_order", "")
            if old_section_order != mapped_section_order:
                row["Section_order"] = mapped_section_order
                applied_repairs.append(
                    SpecMasterAppliedRepair(
                        line=line_number,
                        model=model or None,
                        region=region or None,
                        row_key=row_key or None,
                        column="Section_order",
                        old_value=old_section_order,
                        new_value=mapped_section_order,
                    )
                )

            source_label_column = _source_column_name(row, "Row_label")
            old_template_label = _pick_row_label_source(row)
            if old_template_label != mapped_row_label:
                _set_source_value(row, "Row_label", mapped_row_label)
                applied_repairs.append(
                    SpecMasterAppliedRepair(
                        line=line_number,
                        model=model or None,
                        region=region or None,
                        row_key=row_key or None,
                        column=source_label_column,
                        old_value=old_template_label,
                        new_value=mapped_row_label,
                    )
                )

        source_label_column = _source_column_name(row, "Row_label")
        old_label = _pick_row_label_source(row)
        new_label = _KNOWN_ROW_LABEL_REPAIRS.get(old_label.strip())
        if new_label is not None and old_label != new_label:
            _set_source_value(row, "Row_label", new_label)
            applied_repairs.append(
                SpecMasterAppliedRepair(
                    line=line_number,
                    model=model or None,
                    region=region or None,
                    row_key=row_key or None,
                    column=source_label_column,
                    old_value=old_label,
                    new_value=new_label,
                )
            )

        value_columns = ((_source_column_name(row, "Value"), "Value_source"),)
        for column, repair_column in value_columns:
            repair_lookup_row_key = resolve_legacy_page_value_key(row) or row_key
            repair_key = (model, region, repair_lookup_row_key, repair_column)
            new_value = _KNOWN_VALUE_REPAIRS.get(repair_key)
            if new_value is None:
                continue
            old_value = row.get(column, "")
            if old_value == new_value:
                continue
            row[column] = new_value
            applied_repairs.append(
                SpecMasterAppliedRepair(
                    line=line_number,
                    model=model or None,
                    region=region or None,
                    row_key=row_key or None,
                    column=column,
                    old_value=old_value,
                    new_value=new_value,
                )
            )

        repaired_rows.append(row)

    deduped_rows: list[dict[str, str]] = []
    removed_duplicate_lines: list[int] = []
    seen_rows: set[tuple[tuple[str, str], ...]] = set()
    for idx, row in enumerate(repaired_rows):
        normalized_items = tuple(sorted((key, value) for key, value in row.items() if key != "__line__"))
        if normalized_items in seen_rows:
            removed_duplicate_lines.append(_row_line_num(row, idx))
            continue
        seen_rows.add(normalized_items)
        deduped_rows.append(row)

    return SpecMasterRepairResult(
        repaired_rows=tuple(deduped_rows),
        applied_repairs=tuple(applied_repairs),
        removed_duplicate_lines=tuple(removed_duplicate_lines),
    )


def repair_known_spec_master_csv(spec_master_csv: Path) -> SpecMasterRepairResult:
    return repair_known_spec_master_values(read_spec_master_rows(spec_master_csv))
