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


_PROJECT_CODE_RE = re.compile(r"-(US|JP|EU)(?:-|$)", re.IGNORECASE)
_PROJECT_CODE_KEYS = (
    "project_code",
    "Project_Code",
    "项目代码",
    "椤圭洰浠ｇ爜",
)
_PROJECT_CODE_FILL_BY_MODEL_REGION: dict[tuple[str, str], str] = {
    ("JE-2000F", "JP"): "HTE154-JP",
    ("JE-2000E", "JP"): "HTE152-JP",
    ("JE-2000F", "US"): "HTE154-US",
    ("JE-1000F", "JP"): "HTE153-JP",
    ("JE-1000F", "US"): "HTE153-US",
}
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
_TEMPLATE_ROW_KEY_METADATA: dict[str, tuple[str, str, str]] = {
    "tpl_power_button_label": ("CONTROLS", "7", "Power Button"),
    "tpl_usb_power_button_label": ("CONTROLS", "7", "USB Power Button"),
    "tpl_main_power_button_label": ("CONTROLS", "7", "Main Power Button"),
    "tpl_dc_usb_power_button_label": ("CONTROLS", "7", "DC/USB Power Button"),
    "tpl_ac_power_button_label": ("CONTROLS", "7", "AC Power Button"),
    "tpl_front_dc12_port_label": ("OUTPUT PORTS", "3", "DC 12V Port"),
    "tpl_front_dc12_port_spec": ("OUTPUT PORTS", "3", "DC 12V Port"),
    "tpl_front_usb_c_low_label": ("OUTPUT PORTS", "3", "USB-C 30W Output"),
    "tpl_front_usb_c_low_spec": ("OUTPUT PORTS", "3", "USB-C 30W Output"),
    "tpl_front_usb_c_high_label": ("OUTPUT PORTS", "3", "USB-C 100W Output"),
    "tpl_front_usb_c_high_spec": ("OUTPUT PORTS", "3", "USB-C 100W Output"),
    "tpl_front_usb_a_label": ("OUTPUT PORTS", "3", "USB-A 18W Output"),
    "tpl_front_usb_a_spec": ("OUTPUT PORTS", "3", "USB-A 18W Output"),
    "tpl_front_ac_output_label": ("OUTPUT PORTS", "3", "AC Output"),
    "tpl_front_ac_output_spec": ("OUTPUT PORTS", "3", "AC Output"),
    "tpl_front_total_output_label": ("OUTPUT PORTS", "3", "Total Output"),
    "tpl_front_total_output_spec": ("OUTPUT PORTS", "3", "Total Output"),
    "tpl_side_dc_input_label": ("INPUT PORTS", "2", "DC Input (2 x DC8020 Ports)"),
    "tpl_side_dc_input_pv_spec": ("INPUT PORTS", "2", "PV Input"),
    "tpl_side_dc_input_car_spec": ("INPUT PORTS", "2", "Car Input"),
    "tpl_side_ac_input_label": ("INPUT PORTS", "2", "AC Input"),
    "tpl_side_ac_input_spec": ("INPUT PORTS", "2", "AC Input"),
    "tpl_ups_bypass_output_text": ("OUTPUT PORTS", "3", "UPS Bypass Output"),
    "tpl_usb_c_high_power_port_label": ("OUTPUT PORTS", "3", "USB-C 100W Port"),
    "tpl_default_standby_duration": ("SETTINGS", "8", "Default Standby Duration"),
    "tpl_energy_saving_auto_off_duration": ("SETTINGS", "8", "Energy Saving Auto Off Duration"),
    "tpl_energy_saving_ac_threshold": ("SETTINGS", "8", "Energy Saving AC Threshold"),
    "tpl_energy_saving_dc_threshold": ("SETTINGS", "8", "Energy Saving DC Threshold"),
    "tpl_usb_c_high_power_cable_name": ("ACCESSORIES", "9", "USB-C High Power Cable"),
    "tpl_car_battery_charging_cable_name": ("ACCESSORIES", "9", "Car Battery Charging Cable"),
    "tpl_battery_pack_name": ("ACCESSORIES", "9", "Battery Pack Name"),
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
_KNOWN_ROW_LABEL_REPAIRS: dict[str, str] = {
    "1×ACポート": "1 × AC Input",
    "1×USB-Aポート": "1 × USB-A",
    "2×DC8020ポート": "2 × DC8020 Ports",
    "2×USB-Cポート": "2 × USB-C",
    "3×ACポート": "3 × AC",
    "AC充电功率最大": "Maximum AC Charging Power",
    "AC入力": "AC Input",
    "AC出力": "AC Output",
    "AC出力(パススルー)②": "AC Output in Bypass Mode②",
    "AC出力(パススルー時)": "AC Output in Bypass Mode",
    "AC出力合計": "AC Total Output",
    "AC插座数量": "Number of AC Outlets",
    "AC旁路输出": "AC Output in Bypass Mode",
    "AC输入规格": "AC Input Specifications",
    "DC输入功率上限": "Maximum DC Input Power",
    "USB-A 输出": "USB-A Output",
    "USB-Aポート": "USB-A",
    "USB-C PD 输出": "USB-C PD Output",
    "USB-C 输出": "USB-C Output",
    "USB-Cポート": "USB-C",
    "サイクル寿命": "Cycle Life",
    "サイズ&重量": "Size & Weight",
    "シガーソケット出力": "Car Port Output",
    "バッテリータイプ": "Battery Type",
    "交流输出峰值功率": "Peak AC Output Power",
    "交流输出电压/频率": "AC Output Voltage / Frequency",
    "交流输出电流": "AC Output Current",
    "交流输出额定功率": "Rated AC Output Power",
    "产品名称": "Product Name",
    "产品重量": "Weight",
    "保存温度": "Storage Temperature",
    "储存环境温度": "Storage Temperature",
    "充电方式": "Charging Method",
    "充电温度": "Charging Temperature",
    "充电输入": "Charging Input",
    "充電時間": "Charging Time",
    "充電温度": "Charging Temperature",
    "動作温度": "Operating Temperature",
    "動作湿度": "Operating Humidity",
    "型号": "Model No.",
    "型番": "Model No.",
    "外壳材质": "Housing Material",
    "定格容量": "Rated Capacity",
    "尺寸-宽": "Dimensions - Width",
    "尺寸-长": "Dimensions - Length",
    "尺寸-高": "Dimensions - Height",
    "工作湿度": "Operating Humidity",
    "循环寿命": "Cycle Life",
    "扩容口最大电流": "Maximum Expansion Port Current",
    "扩容口电压范围": "Expansion Port Voltage Range",
    "拡張バッテリーポート": "Expansion Battery Port",
    "放电容量": "Discharge Capacity",
    "放电温度": "Discharge Temperature",
    "放電容量": "Discharge Capacity",
    "汚染度": "Pollution Degree",
    "污染等级": "Pollution Degree",
    "电压结构": "Voltage Configuration",
    "电池化学体系": "Cell Chemistry",
    "製品の名称": "Product Name",
    "车充输出": "Car Port Output",
    "重量": "Weight",
    "電圧構成": "Voltage Configuration",
    "额定容量": "Rated Capacity",
}
_KNOWN_VALUE_REPAIRS: dict[tuple[str, str, str, str], str] = {
    ("JE-2000F", "US", "tpl_front_dc12_port_spec", "Value_en"): "12V/10A Max",
    (
        "JE-2000F",
        "US",
        "tpl_front_usb_c_low_spec",
        "Value_en",
    ): "30W Max, 5V/3A, 9V/3A, 12V/2.5A, 15V/2A, 20V/1.5A",
    (
        "JE-2000F",
        "US",
        "tpl_front_usb_c_high_spec",
        "Value_en",
    ): "100W Max, 5V/3A, 9V/3A, 12V/3A, 15V/3A, 20V/5A",
    ("JE-2000F", "US", "tpl_front_usb_a_spec", "Value_en"): "18W Max, 5-6V/3A, 6-9V/2A, 9-12V/1.5A",
    ("JE-2000F", "US", "tpl_side_dc_input_label", "Value_en"): "DC Input (2 x DC8020 Ports)",
    (
        "JE-2000F",
        "US",
        "tpl_side_dc_input_pv_spec",
        "Value_en",
    ): "PV: 16-60V/12A Max, combined up to 21A / 400W Max",
    (
        "JE-2000F",
        "US",
        "tpl_side_dc_input_car_spec",
        "Value_en",
    ): "Car: 11-16V/8A Max, combined up to 8A Max",
    ("JE-2000F", "JP", "tpl_main_power_button_label", "Value_en"): "メイン電源ボタン",
    ("JE-2000F", "JP", "tpl_dc_usb_power_button_label", "Value_en"): "DC/USB出力ボタン",
    ("JE-2000F", "JP", "tpl_ac_power_button_label", "Value_en"): "AC出力ボタン",
    ("JE-2000F", "JP", "tpl_front_dc12_port_label", "Value_en"): "12Vシガーソケット出力",
    ("JE-2000F", "JP", "tpl_front_dc12_port_spec", "Value_en"): "12V/10A 最大",
    ("JE-2000F", "JP", "tpl_front_usb_c_low_label", "Value_en"): "USB-C 30W出力",
    (
        "JE-2000F",
        "JP",
        "tpl_front_usb_c_low_spec",
        "Value_en",
    ): "5V/3A、9V/3A、12V/2.5A、15V/2A、20V/1.5A、最大30W",
    ("JE-2000F", "JP", "tpl_front_usb_c_high_label", "Value_en"): "USB-C 100W出力",
    (
        "JE-2000F",
        "JP",
        "tpl_front_usb_c_high_spec",
        "Value_en",
    ): "5V/3A、9V/3A、12V/3A、15V/3A、20V/5A、最大100W",
    ("JE-2000F", "JP", "tpl_front_usb_a_label", "Value_en"): "USB-A 18W出力",
    (
        "JE-2000F",
        "JP",
        "tpl_front_usb_a_spec",
        "Value_en",
    ): "5-6V/3A、6-9V/2A、9-12V/1.5A、最大18W",
    ("JE-2000F", "JP", "tpl_front_ac_output_label", "Value_en"): "AC出力",
    (
        "JE-2000F",
        "JP",
        "tpl_front_ac_output_spec",
        "Value_en",
    ): "100V~ 50Hz/60Hz、20A、定格2000W、3秒2200W、瞬間最大4400W",
    ("JE-2000F", "JP", "tpl_side_dc_input_label", "Value_en"): "DC入力（DC8020ポート×2）",
    (
        "JE-2000F",
        "JP",
        "tpl_side_dc_input_pv_spec",
        "Value_en",
    ): "PV: 16-60V/12A、2ポート合計最大21A/400W",
    (
        "JE-2000F",
        "JP",
        "tpl_side_dc_input_car_spec",
        "Value_en",
    ): "車載充電: 11-16V/8A、2ポート合計最大8A",
    ("JE-2000F", "JP", "tpl_side_ac_input_label", "Value_en"): "AC入力",
    (
        "JE-2000F",
        "JP",
        "tpl_side_ac_input_spec",
        "Value_en",
    ): "100V-120V~ 50Hz/60Hz、15A 最大、急速充電 約1500W",
    ("JE-2000F", "JP", "tpl_default_standby_duration", "Value_en"): "2時間",
    ("JE-2000F", "JP", "tpl_energy_saving_auto_off_duration", "Value_en"): "12時間",
    (
        "JE-2000F",
        "JP",
        "tpl_usb_c_high_power_cable_name",
        "Value_en",
    ): "Jackery USB-C to USB-C 5A ケーブル",
    (
        "JE-2000F",
        "JP",
        "tpl_car_battery_charging_cable_name",
        "Value_en",
    ): "Jackery 12V 自動車用バッテリー充電ケーブル",
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


def _pick_project_code(row: dict[str, str]) -> str:
    return _first_non_empty(row, list(_PROJECT_CODE_KEYS))


def _pick_project_code_key(row: dict[str, str]) -> str | None:
    for key in _PROJECT_CODE_KEYS:
        if key in row:
            return key
    return None


def _normalize_project_code(project_code: str, region: str) -> str:
    code = (project_code or "").strip()
    normalized_region = (region or "").strip().upper()
    if len(code) < 6 or not normalized_region:
        return code
    return f"{code[:6]}-{normalized_region}"


def _template_row_metadata(row_key: str) -> tuple[str, str, str] | None:
    return _TEMPLATE_ROW_KEY_METADATA.get((row_key or "").strip().lower())


def _is_template_row(row_key: str, section: str) -> bool:
    return (row_key or "").strip().lower().startswith("tpl_") or (
        (section or "").strip().upper() == "TEMPLATE VARS"
    )


def _pick_section(row: dict[str, str]) -> str:
    return _first_non_empty(row, ["Section", "section"])


def _pick_section_order(row: dict[str, str]) -> str:
    return _first_non_empty(row, ["Section_order", "section_order"])


def _pick_row_label_en(row: dict[str, str]) -> str:
    return _first_non_empty(row, ["Row_label_en", "row_label_en"])


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
    keys = [
        f"{base}_{lang}",
        f"{base}_{lang.lower()}",
        f"{base}_{lang.upper()}",
        f"{base}_en",
        base,
        "Spec_Value",
    ]
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


def _normalize_page_filters(pages: str | list[str] | tuple[str, ...] | set[str] | None) -> set[str] | None:
    if pages is None:
        return None
    if isinstance(pages, str):
        raw_items = [pages]
    else:
        raw_items = list(pages)

    normalized = {(item or "").strip().lower() for item in raw_items if (item or "").strip()}
    return normalized or None


def _row_matches_target(
    row: dict[str, str],
    *,
    model: str | None,
    region: str | None,
    row_key: str | None = None,
    pages: str | list[str] | tuple[str, ...] | set[str] | None = None,
    line_order: str | int | None = None,
) -> bool:
    if not _is_truthy(_first_non_empty(row, ["enabled", "Enabled"])):
        return False
    if not _is_truthy(_first_non_empty(row, ["Is_Latest", "is_latest"])):
        return False

    target_key = (row_key or "").strip().lower()
    if target_key and _pick_row_key(row) != target_key:
        return False

    page_filters = _normalize_page_filters(pages)
    page_value = _first_non_empty(row, ["Page", "page"]).lower()
    if page_filters and page_value and page_value not in page_filters:
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

    if _first_non_empty(row, [f"Value_{lang}", f"Value_{lang.lower()}"]):
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
) -> SpecValueMatch | None:
    for row in _iter_ranked_rows(
        rows,
        model=model,
        region=region,
        lang=lang,
        row_key=row_key,
        pages=pages,
        line_order=line_order,
    ):
        value = _pick_lang_value(row, "Value", lang)
        if value:
            return SpecValueMatch(
                value=value,
                region=_pick_row_region(row) or None,
                row=row,
            )
    return None


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
    )
    if model_match:
        substitutions["MODEL_NO"] = model_match.value

    for row in _iter_ranked_rows(
        rows,
        model=model,
        region=region,
        lang=lang,
        pages=("spec", "specifications"),
    ):
        raw_key = _pick_row_key(row)
        if not raw_key.startswith("tpl_"):
            continue

        value = _pick_lang_value(row, "Value", lang)
        if not value:
            continue

        placeholder = raw_key[4:].upper()
        line_order_value = _first_non_empty(row, ["Line_order", "line_order"])
        if line_order_value not in {"", "1", "1.0"}:
            placeholder = f"{placeholder}_{line_order_value.replace('.', '_')}"
        substitutions.setdefault(placeholder, value)

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
        project_code = _pick_project_code(row)
        region = _pick_row_region(row) or None
        section = _pick_section(row) or None
        row_key = _pick_row_key(row) or None
        model = _pick_row_model(row) or None

        if project_code and region:
            match = _PROJECT_CODE_RE.search(project_code)
            if match and match.group(1).upper() != region.upper():
                issues.append(
                    SpecMasterAuditIssue(
                        code="PROJECT_REGION_MISMATCH",
                        message=(
                            f"Project code `{project_code}` suggests region `{match.group(1).upper()}` "
                            f"but row region is `{region}`"
                        ),
                        line=line_number,
                        model=model,
                        region=region,
                        section=section,
                        row_key=row_key,
                    )
                )

        label_en = _pick_row_label_en(row)
        if label_en and _contains_east_asian_text(label_en):
            issues.append(
                SpecMasterAuditIssue(
                    code="ROW_LABEL_EN_CONTAINS_EAST_ASIAN_TEXT",
                    message=(
                        "`Row_label_en` contains East Asian text in an English-labeled "
                        f"column: {label_en}"
                    ),
                    line=line_number,
                    model=model,
                    region=region,
                    section=section,
                    row_key=row_key,
                )
            )

        value_en = _pick_lang_value(row, "Value", "en")
        if _is_template_row(row_key, section) and "?" in value_en:
            issues.append(
                SpecMasterAuditIssue(
                    code="SUSPECT_TEMPLATE_VALUE",
                    message=f"Template value contains literal `?`: {value_en}",
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

        if _is_template_row(row_key, original_section):
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
        if not _is_template_row(row_key, _pick_section(raw_row)):
            continue

        metadata = _template_row_metadata(row_key)
        if metadata is None:
            continue

        usage_row = usage[row_key]
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

        row_label = (raw_row.get("Row_label_en") or "").strip()
        if row_label:
            cast(set[str], usage_row["row_labels"]).add(row_label)

    mapping_rows: list[dict[str, str]] = []
    for row_key, (section, section_order, row_label_en) in _TEMPLATE_ROW_KEY_METADATA.items():
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
                "Section": section,
                "Section_order": section_order,
                "Row_label_en": row_label_en,
                "Usage_count": usage_count,
                "Models": ",".join(models),
                "Regions": ",".join(regions),
                "Observed_sections": ",".join(sections),
                "Observed_section_orders": ",".join(section_orders),
                "Observed_row_labels_en": " | ".join(row_labels),
            }
        )

    return tuple(
        sorted(
            mapping_rows,
            key=lambda row: (
                int(row["Section_order"]),
                row["Section"],
                row["Row_label_en"],
                row["Row_key"],
            ),
        )
    )


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
            key=lambda row: (row["Row_label_en"], row["Row_key"]),
        )
        lines.extend(
            [
                f"## {section} (`{section_order}`)",
                "",
                "| Row_key | Row_label_en | Usage_count | Models | Regions |",
                "| --- | --- | ---: | --- | --- |",
            ]
        )
        for row in rows_in_section:
            lines.append(
                "| {row_key} | {row_label} | {usage} | {models} | {regions} |".format(
                    row_key=row["Row_key"],
                    row_label=row["Row_label_en"],
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
        project_code_key = _pick_project_code_key(row)
        template_metadata = _template_row_metadata(row_key)

        if project_code_key is not None:
            old_project_code = row.get(project_code_key, "")
            if (old_project_code or "").strip():
                new_project_code = _normalize_project_code(old_project_code, region)
            else:
                new_project_code = _PROJECT_CODE_FILL_BY_MODEL_REGION.get(
                    ((model or "").strip(), (region or "").strip().upper()),
                    old_project_code,
                )
            if old_project_code != new_project_code:
                row[project_code_key] = new_project_code
                applied_repairs.append(
                    SpecMasterAppliedRepair(
                        line=line_number,
                        model=model or None,
                        region=region or None,
                        row_key=row_key or None,
                        column=project_code_key,
                        old_value=old_project_code,
                        new_value=new_project_code,
                    )
                )

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

            old_template_label = row.get("Row_label_en", "")
            if old_template_label != mapped_row_label:
                row["Row_label_en"] = mapped_row_label
                applied_repairs.append(
                    SpecMasterAppliedRepair(
                        line=line_number,
                        model=model or None,
                        region=region or None,
                        row_key=row_key or None,
                        column="Row_label_en",
                        old_value=old_template_label,
                        new_value=mapped_row_label,
                    )
                )

        old_label = row.get("Row_label_en", "")
        new_label = _KNOWN_ROW_LABEL_REPAIRS.get(old_label.strip())
        if new_label is not None and old_label != new_label:
            row["Row_label_en"] = new_label
            applied_repairs.append(
                SpecMasterAppliedRepair(
                    line=line_number,
                    model=model or None,
                    region=region or None,
                    row_key=row_key or None,
                    column="Row_label_en",
                    old_value=old_label,
                    new_value=new_label,
                )
            )

        for column in ("Value_en",):
            repair_key = (model, region, row_key, column)
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
