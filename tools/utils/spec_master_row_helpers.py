
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from collections import Counter
import csv
from pathlib import Path
import re

from tools.utils.spec_master_shared import (
    PageValueBinding,
    _LEGACY_PAGE_VALUE_BINDINGS,
    _LEGACY_PAGE_VALUE_KEYS_BY_SIGNATURE,
    _SECTION_NORMALIZATION_RULES,
    _SECTION_ORDER_BY_SECTION,
    _SLOT_KEY_VALUE_ALIASES,
    _SOURCE_COLUMN_NAMES,
    _SOURCE_LANGUAGE_NORMALIZATION,
    _SOURCE_SHARED_BASES,
)

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


def canonicalize_model_token(value: str, *, region: str | None = None) -> str:
    text = (value or "").strip()
    normalized_region = (region or "").strip()
    if not text or not normalized_region:
        return text

    upper_text = text.upper()
    upper_region = normalized_region.upper()
    for separator in ("_", "-"):
        suffix = f"{separator}{upper_region}"
        if upper_text.endswith(suffix):
            candidate = text[: -len(suffix)].strip()
            return candidate.rstrip("_-").strip()
    return text


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

    target_region = (region or "").strip()
    target_model = canonicalize_model_token(model or "", region=target_region)
    row_region = _pick_row_region(row)
    row_model = canonicalize_model_token(_pick_row_model(row), region=row_region or target_region)
    if target_model and row_model and row_model.casefold() != target_model.casefold():
        return False

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
    target_region = (region or "").strip()
    target_model = canonicalize_model_token(model or "", region=target_region)
    row_model = canonicalize_model_token(_pick_row_model(row), region=_pick_row_region(row) or target_region)
    row_region = _pick_row_region(row)

    score = 0
    if row_model and target_model and row_model.casefold() == target_model.casefold():
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


def _normalize_line_order_suffix(line_order: str) -> str:
    text = (line_order or "").strip()
    if not text:
        return "1"
    if text.endswith(".0"):
        text = text[:-2]
    return text or "1"


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
