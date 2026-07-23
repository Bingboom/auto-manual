"""Semantic control-label contract shared by overview and App figures.

The Product Overview table is the source of truth for localized button names.
Approved App compositions may use a shorter display variant, but both the
source label and the rendered editable label are bound by the approved layout
contract.  This keeps the App artwork and its top-layer text frames same-source
without adding renderer-only blocks to Manual IR.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
from typing import Any

from tools.manual_ir import ManualIR, ManualPage


CONTROL_LABEL_ROLES = ("main_power", "dc_usb", "ac")
CONTROL_LABEL_SLOTS = {
    "main_power": (0, 0),
    "dc_usb": (2, 0),
    "ac": (3, 1),
}

_OVERVIEW_STEM = re.compile(
    r"(?:p\d+_)?03_product_overview(?:_placeholder)?$",
    re.IGNORECASE,
)
_LEADING_BOLD = re.compile(r"^\s*\*\*(.+?)\*\*")


def language_code(value: object) -> str:
    """Normalize an IETF/underscore locale to its primary language subtag."""
    normalized = str(value or "").strip().lower().replace("_", "-")
    return normalized.split("-", 1)[0]


def _is_overview_page(page: ManualPage) -> bool:
    return _OVERVIEW_STEM.fullmatch(Path(page.source_path).stem) is not None


def manual_uses_app_add_device(ir: ManualIR) -> bool:
    """Return whether this manual contains the governed App device figure."""
    for page in ir.pages:
        for block in page.blocks:
            if block.kind != "image" or not isinstance(block.payload, str):
                continue
            if Path(block.payload).stem.casefold().startswith("add_device"):
                return True
    return False


def _first_table(page: ManualPage) -> list[list[Any]]:
    block = next((block for block in page.blocks if block.kind == "table"), None)
    if block is None or not isinstance(block.payload, list):
        raise ValueError(
            f"{page.source_ref}: Product Overview requires a first table"
        )
    if not all(isinstance(row, list) for row in block.payload):
        raise ValueError(
            f"{page.source_ref}: Product Overview first table rows must be lists"
        )
    return block.payload


def _slot_label(page: ManualPage, table: list[list[Any]], role: str) -> str:
    row_index, column_index = CONTROL_LABEL_SLOTS[role]
    if row_index >= len(table) or column_index >= len(table[row_index]):
        raise ValueError(
            f"{page.source_ref}: Product Overview first table is missing "
            f"{role} at row {row_index} column {column_index}"
        )
    cell = table[row_index][column_index]
    if not isinstance(cell, str):
        raise ValueError(
            f"{page.source_ref}: Product Overview {role} slot must be text"
        )
    match = _LEADING_BOLD.match(cell)
    label = match.group(1).strip() if match else ""
    if not label:
        raise ValueError(
            f"{page.source_ref}: Product Overview {role} slot must start "
            "with one non-empty bold label"
        )
    return label


def extract_overview_control_labels(
    ir: ManualIR,
    languages: list[str] | tuple[str, ...],
) -> dict[str, dict[str, str]]:
    """Build the stable ``language + role`` index from overview table slots.

    Approved targets fail closed on missing/duplicate overview pages, malformed
    table geometry, empty labels, or the same label assigned to two roles.
    """
    required_languages = tuple(language_code(item) for item in languages)
    if any(not item for item in required_languages):
        raise ValueError("control-label languages must be non-empty")
    if len(set(required_languages)) != len(required_languages):
        raise ValueError("control-label languages must be unique")

    pages_by_language: dict[str, list[ManualPage]] = {
        language: [] for language in required_languages
    }
    for page in ir.pages:
        language = language_code(page.language)
        if language in pages_by_language and _is_overview_page(page):
            pages_by_language[language].append(page)

    labels_by_language: dict[str, dict[str, str]] = {}
    for language in required_languages:
        pages = pages_by_language[language]
        if len(pages) != 1:
            raise ValueError(
                "approved control-label source requires exactly one Product "
                f"Overview page for {language}; found {len(pages)}"
            )
        page = pages[0]
        table = _first_table(page)
        labels = {
            role: _slot_label(page, table, role)
            for role in CONTROL_LABEL_ROLES
        }
        duplicates = sorted(
            label for label, count in Counter(labels.values()).items()
            if count > 1
        )
        if duplicates:
            raise ValueError(
                f"{page.source_ref}: Product Overview control labels must be "
                "unique across roles; duplicate " + ", ".join(duplicates)
            )
        labels_by_language[language] = labels
    return labels_by_language


def _role_map_issues(value: Any, path: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{path} must be an object"]
    actual_roles = set(value)
    required_roles = set(CONTROL_LABEL_ROLES)
    issues: list[str] = []
    if actual_roles != required_roles:
        missing = sorted(required_roles - actual_roles)
        extra = sorted(actual_roles - required_roles)
        if missing:
            issues.append(f"{path} is missing roles: {', '.join(missing)}")
        if extra:
            issues.append(f"{path} has unexpected roles: {', '.join(extra)}")
    for role in CONTROL_LABEL_ROLES:
        label = value.get(role)
        if not isinstance(label, str) or not label.strip():
            issues.append(f"{path}.{role} must be a non-empty string")
    labels = [value.get(role) for role in CONTROL_LABEL_ROLES]
    if all(isinstance(label, str) and label.strip() for label in labels):
        duplicates = sorted(
            label for label, count in Counter(labels).items() if count > 1
        )
        if duplicates:
            issues.append(
                f"{path} labels must be unique across roles: "
                + ", ".join(duplicates)
            )
    return issues


def validate_app_control_label_contract(
    idml_contract: dict[str, Any],
    ir: ManualIR,
    languages: list[str],
) -> list[str]:
    """Validate App label base/variant bindings against current Manual IR."""
    editable = idml_contract.get("editable_components")
    app = editable.get("app_add_device") if isinstance(editable, dict) else None
    labels_contract = app.get("control_labels") if isinstance(app, dict) else None
    required = manual_uses_app_add_device(ir)
    if not required and labels_contract is None:
        return []
    if not isinstance(editable, dict):
        return ["idml_contract.editable_components must be an object"]
    if not isinstance(app, dict):
        return ["idml_contract.editable_components.app_add_device must be an object"]
    if not isinstance(labels_contract, dict):
        return [
            "idml_contract.editable_components.app_add_device.control_labels "
            "must be an object"
        ]

    expected_languages = [language_code(item) for item in languages]
    issues: list[str] = []
    actual_languages = set(labels_contract)
    expected_set = set(expected_languages)
    if actual_languages != expected_set:
        missing = sorted(expected_set - actual_languages)
        extra = sorted(actual_languages - expected_set)
        if missing:
            issues.append(
                "idml_contract App control_labels is missing languages: "
                + ", ".join(missing)
            )
        if extra:
            issues.append(
                "idml_contract App control_labels has unexpected languages: "
                + ", ".join(extra)
            )

    try:
        source_labels = extract_overview_control_labels(ir, expected_languages)
    except ValueError as exc:
        issues.append(str(exc))
        source_labels = {}

    for language in expected_languages:
        language_contract = labels_contract.get(language)
        path = (
            "idml_contract.editable_components.app_add_device.control_labels."
            + language
        )
        if not isinstance(language_contract, dict):
            issues.append(f"{path} must be an object")
            continue
        base = language_contract.get("base_labels_by_role")
        render = language_contract.get("render_labels_by_role")
        issues.extend(_role_map_issues(base, f"{path}.base_labels_by_role"))
        issues.extend(_role_map_issues(render, f"{path}.render_labels_by_role"))
        expected_base = source_labels.get(language)
        if isinstance(base, dict) and expected_base is not None:
            for role in CONTROL_LABEL_ROLES:
                if base.get(role) != expected_base[role]:
                    issues.append(
                        f"{path}.base_labels_by_role.{role} does not match "
                        "the Product Overview source slot"
                    )
    return issues


def approved_app_control_labels(
    page_plan: dict[str, Any] | None,
    language: object,
) -> tuple[dict[str, str], dict[str, str]]:
    """Return approved base/render role maps or raise on any contract gap."""
    approved = (page_plan or {}).get("approved_contract")
    idml_contract = approved.get("idml_contract") if isinstance(approved, dict) else None
    editable = (
        idml_contract.get("editable_components")
        if isinstance(idml_contract, dict) else None
    )
    app = editable.get("app_add_device") if isinstance(editable, dict) else None
    labels = app.get("control_labels") if isinstance(app, dict) else None
    code = language_code(language)
    language_contract = labels.get(code) if isinstance(labels, dict) else None
    if not isinstance(language_contract, dict):
        raise ValueError(
            "approved App control-label contract is missing language " + repr(code)
        )

    result: list[dict[str, str]] = []
    for field in ("base_labels_by_role", "render_labels_by_role"):
        value = language_contract.get(field)
        issues = _role_map_issues(
            value,
            "approved App control-label contract " + field,
        )
        if issues:
            raise ValueError("; ".join(issues))
        result.append({role: value[role].strip() for role in CONTROL_LABEL_ROLES})
    return result[0], result[1]


def matches_base_label_block(text: str, labels_by_role: dict[str, str]) -> bool:
    """Match only a three-line duplicate; preserve unrelated adjacent prose."""
    visible = [line.strip() for line in text.splitlines() if line.strip()]
    semantic = [labels_by_role[role] for role in CONTROL_LABEL_ROLES]
    return sorted(visible) == sorted(semantic)


__all__ = [
    "CONTROL_LABEL_ROLES",
    "CONTROL_LABEL_SLOTS",
    "approved_app_control_labels",
    "extract_overview_control_labels",
    "language_code",
    "manual_uses_app_add_device",
    "matches_base_label_block",
    "validate_app_control_label_contract",
]
