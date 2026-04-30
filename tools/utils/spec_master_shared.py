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
    "charging_temperature": ("CHARGING_TEMPERATURE", ("specifications",)),
    "discharging_temperature": ("DISCHARGING_TEMPERATURE", ("specifications",)),
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

