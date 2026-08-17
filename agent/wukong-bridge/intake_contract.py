"""Pure validation rules shared by Wukong intake staging and commit.

KR onboarding is source-first: the canonical English value/label enters the
source tables with ``Source_lang=en``. Korean localization columns are an
optional later layer and must never block the initial English-source intake.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping

KR_CONTRACT_VERSION = "kr-structured-source-first-v2"

KR_STAGING_REQUIRED_FIELDS = frozenset({
    "document_key",
    "Row_key",
    "Page",
    "行标签",
    "手册值",
    "Source_lang",
    "确认",
    "入库结果",
})

KR_SOURCE_REQUIRED_FIELDS = frozenset({
    "document_key",
    "Row_key",
    "Row_label_source",
    "Value_source",
    "Source_lang",
})

_ROW_KEY_RE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
_NON_ENGLISH_SOURCE_SCRIPT_RE = re.compile(
    r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]"
)
_TIGHT_UNIT_RE = re.compile(
    r"(?<![A-Za-z0-9])\d+(?:\.\d+)?(?:Wh|W|V|A|Hz|kg|Kg|mm|cm|°C)"
    r"(?=\b|[^A-Za-z])"
)


def is_kr_document_key(document_key: str) -> bool:
    """Return True only for a canonical ``<model>_KR`` target key."""
    _model, separator, region = str(document_key).strip().rpartition("_")
    return bool(separator and region.upper() == "KR")


def missing_fields(columns: list[str], required: frozenset[str]) -> list[str]:
    """Return required columns absent from a live table shape."""
    return sorted(required.difference(columns))


def normalize_scalar(value) -> str:
    """Normalize Feishu select/lookup wrappers and ordinary JSON scalars."""
    if value is None:
        return ""
    if isinstance(value, list):
        if len(value) == 1:
            return normalize_scalar(value[0])
        return ",".join(sorted(normalize_scalar(item) for item in value if item is not None))
    if isinstance(value, Mapping):
        return str(value.get("name") or value.get("text") or "").strip()
    return str(value).strip()


def normalize_line_order(value) -> str:
    """Normalize ``1``, ``1.0`` and an empty line number to the same key."""
    text = normalize_scalar(value)
    if not text:
        return "1"
    try:
        number = float(text)
    except ValueError:
        return text
    return str(int(number)) if number.is_integer() else text


def normalize_page(value) -> str:
    """Normalize a Feishu page select into the maintenance-key representation."""
    if isinstance(value, list):
        parts = [normalize_scalar(item).casefold() for item in value]
    else:
        parts = [part.strip().casefold() for part in normalize_scalar(value).split(",")]
    return "+".join(sorted(part for part in parts if part))


def logical_structure_key(row: Mapping, *, section_field: str = "Section") -> tuple[str, str, str, str]:
    """Return the intake completeness key used by the repository.

    ``Section`` is intentionally part of the key: a product can legitimately
    expose the same Row_key/Slot_key/Line_order in both INPUT PORTS and OUTPUT
    PORTS (for example ``dc_expansion_port``).
    """
    return (
        normalize_scalar(row.get("Row_key")).casefold(),
        normalize_scalar(row.get("Slot_key")).casefold(),
        normalize_scalar(row.get(section_field)).casefold(),
        normalize_line_order(row.get("Line_order")),
    )


def structure_identity(row: Mapping, *, section_field: str = "Section") -> tuple[str, str, str, str, str]:
    """Return Page + logical structure key for exact sibling comparison."""
    return (normalize_page(row.get("Page")), *logical_structure_key(
        row, section_field=section_field
    ))


def validate_sibling_structure(
    candidates: Iterable[Mapping],
    references: Iterable[Mapping],
    *,
    candidate_section_field: str = "Section",
    require_complete: bool = False,
) -> dict:
    """Validate candidate routing/identity against a sibling source structure.

    This validates structure only; product-specific values remain operator-
    reviewed staging data. Extra/duplicate/wrong-page candidates are always
    blocking. Missing sibling rows are reported as coverage gaps and become
    blocking only for the commit-time ``require_complete`` gate.
    """
    reference_rows = list(references)
    candidate_rows = list(candidates)
    reference_exact = {
        structure_identity(row): row for row in reference_rows
    }
    reference_by_logical: dict[tuple[str, str, str, str], list[tuple]] = {}
    for identity in reference_exact:
        reference_by_logical.setdefault(identity[1:], []).append(identity)

    violations: list[dict] = []
    seen: dict[tuple, int] = {}
    candidate_exact: set[tuple] = set()
    for index, row in enumerate(candidate_rows):
        row_key = normalize_scalar(row.get("Row_key"))
        section = normalize_scalar(row.get(candidate_section_field))
        page = normalize_page(row.get("Page"))
        identity = structure_identity(row, section_field=candidate_section_field)
        logical = identity[1:]
        if not _ROW_KEY_RE.fullmatch(row_key):
            violations.append({
                "index": index,
                "code": "INVALID_ROW_KEY",
                "message": "Row_key 必须是稳定的 lowercase snake_case",
                "identity": identity,
            })
        if not section:
            violations.append({
                "index": index,
                "code": "MISSING_SECTION",
                "message": "章节/Section 必填，用于区分输入与输出同键行",
                "identity": identity,
            })
        if not page:
            violations.append({
                "index": index,
                "code": "MISSING_PAGE",
                "message": "Page 必填",
                "identity": identity,
            })
        if identity in seen:
            violations.append({
                "index": index,
                "code": "DUPLICATE_STRUCTURE_KEY",
                "message": f"与批次第 {seen[identity]} 行结构键重复",
                "identity": identity,
            })
        else:
            seen[identity] = index
        candidate_exact.add(identity)
        if identity in reference_exact:
            continue
        expected = reference_by_logical.get(logical, [])
        if expected:
            violations.append({
                "index": index,
                "code": "PAGE_ROUTE_MISMATCH",
                "message": "结构键存在，但 Page 路由与姊妹目标不一致",
                "identity": identity,
                "expected_identities": expected,
            })
        else:
            near = [item for item in reference_exact if item[1] == identity[1]]
            violations.append({
                "index": index,
                "code": "STRUCTURE_KEY_NOT_IN_SIBLING",
                "message": "该结构键不在指定姊妹目标中；不得猜测新 Row_key/顺序/Slot_key",
                "identity": identity,
                "sibling_rows_with_same_row_key": near,
            })

    missing = sorted(set(reference_exact).difference(candidate_exact))
    extra = sorted(candidate_exact.difference(reference_exact))
    complete = not missing and not extra and not violations
    if require_complete and missing:
        violations.append({
            "code": "SIBLING_COVERAGE_INCOMPLETE",
            "message": "正式入库前必须覆盖姊妹目标两张源表的完整结构",
            "missing_count": len(missing),
        })
    return {
        "complete": complete,
        "candidate_rows": len(candidate_rows),
        "reference_rows": len(reference_rows),
        "missing_rows": missing,
        "extra_rows": extra,
        "violations": violations,
    }


def validate_kr_source(
    document_key: str,
    *,
    value_source: str,
    row_label_source: str,
    source_lang: str,
) -> list[dict[str, str]]:
    """Validate one row against the KR English-source-first contract."""
    if not is_kr_document_key(document_key):
        return []

    values = {
        "手册值": str(value_source).strip(),
        "行标签": str(row_label_source).strip(),
    }
    codes = {
        "手册值": "MISSING_VALUE_SOURCE",
        "行标签": "MISSING_ROW_LABEL_SOURCE",
    }
    violations = [
        {"code": codes[field], "field": field, "message": f"KR 合同要求 {field} 非空"}
        for field, value in values.items()
        if not value
    ]
    if str(source_lang).strip().lower() != "en":
        violations.append({
            "code": "SOURCE_LANG_NOT_EN",
            "field": "Source_lang",
            "message": "KR 首次入库要求 Source_lang=en；源值写入英文 Value_source",
        })
    for field, value in values.items():
        if value and _NON_ENGLISH_SOURCE_SCRIPT_RE.search(value):
            violations.append({
                "code": "NON_ENGLISH_SOURCE_TEXT",
                "field": field,
                "message": f"KR 首次入库的 {field} 必须是英文源文本；韩文仅写 *_ko",
            })
    return violations


def validate_kr_candidate(document_key: str, row: Mapping) -> list[dict]:
    """Validate source text plus KR staging semantics that structure alone misses."""
    if not is_kr_document_key(document_key):
        return []
    value = normalize_scalar(row.get("手册值") or row.get("Value_source"))
    label = normalize_scalar(row.get("行标签") or row.get("Row_label_source"))
    violations = validate_kr_source(
        document_key,
        value_source=value,
        row_label_source=label,
        source_lang=normalize_scalar(row.get("Source_lang")),
    )
    if _TIGHT_UNIT_RE.search(value):
        violations.append({
            "code": "NON_CANONICAL_UNIT_SPACING",
            "field": "手册值",
            "message": "英文手册值的数字与单位之间需留空格，例如 2048 Wh、19.1 kg、25 °C",
        })
    if re.search(r"\d(?:\.\d+)?\s*V\s*=\s*\d", value):
        violations.append({
            "code": "NON_CANONICAL_DC_SYMBOL",
            "field": "手册值",
            "message": "直流规格使用 ⎓，不要用等号，例如 5 V⎓3 A",
        })

    row_key = normalize_scalar(row.get("Row_key")).casefold()
    line = normalize_line_order(row.get("Line_order"))
    evidence = " ".join(filter(None, [
        normalize_scalar(row.get("规格书原值")), value,
    ])).casefold()
    if row_key == "storage_temperature":
        expected_line = None
        if "1 month" in evidence:
            expected_line = "1"
        elif "3 month" in evidence:
            expected_line = "2"
        elif "1 year" in evidence or "12 month" in evidence:
            expected_line = "3"
        if expected_line and line != expected_line:
            violations.append({
                "code": "STORAGE_LINE_ORDER_MISMATCH",
                "field": "Line_order",
                "message": "存储温度固定顺序为 1 month→1、3 months→2、1 year/12 months→3",
                "expected": expected_line,
                "actual": line,
            })
    if row_key in {"dc_expansion_port", "battery_pack_connection_port"}:
        has_both_directions = (
            ("input" in evidence and "output" in evidence)
            or ("75 a" in evidence and "55 a" in evidence)
            or ("75a" in evidence and "55a" in evidence)
        )
        if has_both_directions:
            violations.append({
                "code": "COMBINED_INPUT_OUTPUT_FACTS",
                "field": "手册值",
                "message": "扩展端口输入 75 A 与输出 55 A 必须按 Section 拆成两条结构行",
            })
    return violations
