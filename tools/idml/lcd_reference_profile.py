"""Approved-reference presentation rules for editable LCD tables.

The phase2 row number identifies the source record and must remain stable.
An approved printed master may, however, present those rows in a different
order or merge a displayed number across adjacent physical rows.  Keeping
that mapping in the approved reference contract avoids mutating source data
or hard-coding a model-specific exception in the shared table renderer.
"""
from __future__ import annotations

from collections.abc import Sequence
import math
import re
from typing import Any


class LcdReferenceProfileError(ValueError):
    """The approved LCD presentation profile is invalid for its source rows."""


def validate_lcd_reference_profile(profile: Any) -> list[str]:
    """Return contract-shape issues for one LCD presentation profile."""
    if not isinstance(profile, dict):
        return ["must be an object"]
    presentation = profile.get("row_presentation")
    if not isinstance(presentation, list) or not presentation:
        return ["row_presentation must be a non-empty list"]
    issues: list[str] = []
    seen: set[str] = set()
    for index, entry in enumerate(presentation):
        prefix = f"row_presentation[{index}]"
        if not isinstance(entry, dict):
            issues.append(f"{prefix} must be an object")
            continue
        source_no = str(entry.get("source_no") or "").strip()
        display_no = str(entry.get("display_no") or "").strip()
        if not source_no:
            issues.append(f"{prefix}.source_no must be non-empty")
        elif source_no in seen:
            issues.append(f"duplicate source_no: {source_no}")
        else:
            seen.add(source_no)
        if not display_no:
            issues.append(f"{prefix}.display_no must be non-empty")
        span = entry.get("number_row_span", 1)
        if isinstance(span, bool) or not isinstance(span, int) or span < 1:
            issues.append(f"{prefix}.number_row_span must be a positive integer")
        suppress = entry.get("suppress_number", False)
        if not isinstance(suppress, bool):
            issues.append(f"{prefix}.suppress_number must be boolean")
        typography_role = entry.get("typography_role")
        if typography_role is not None and (
            not isinstance(typography_role, str)
            or re.fullmatch(r"[a-z][a-z0-9_]*", typography_role) is None
        ):
            issues.append(
                f"{prefix}.typography_role must be a lowercase token"
            )
        heights = entry.get("row_height_pt_by_language")
        if heights is not None:
            if not isinstance(heights, dict) or not heights:
                issues.append(
                    f"{prefix}.row_height_pt_by_language must be a non-empty object"
                )
            else:
                for language, height in heights.items():
                    height_prefix = (
                        f"{prefix}.row_height_pt_by_language.{language}"
                    )
                    if not isinstance(language, str) or re.fullmatch(
                        r"[a-z][a-z0-9-]*", language
                    ) is None:
                        issues.append(
                            f"{prefix}.row_height_pt_by_language has an invalid language key"
                        )
                    if (
                        isinstance(height, bool)
                        or not isinstance(height, (int, float))
                        or not math.isfinite(float(height))
                        or float(height) <= 0
                    ):
                        issues.append(
                            f"{height_prefix} must be a positive finite number"
                        )
    return issues


def apply_lcd_reference_profile(
    rows: Sequence[dict[str, str]],
    profile: dict[str, Any],
    *,
    language: str | None = None,
) -> tuple[dict[str, str], ...]:
    """Apply an exact, fail-closed approved presentation to source rows."""
    issues = validate_lcd_reference_profile(profile)
    if issues:
        raise LcdReferenceProfileError("; ".join(issues))

    by_source: dict[str, dict[str, str]] = {}
    for row in rows:
        source_no = str(row.get("source_no") or row.get("no") or "").strip()
        if not source_no:
            raise LcdReferenceProfileError("LCD source row has no source number")
        if source_no in by_source:
            raise LcdReferenceProfileError(f"duplicate LCD source row: {source_no}")
        by_source[source_no] = row

    presentation = profile["row_presentation"]
    configured = {str(entry["source_no"]).strip() for entry in presentation}
    actual = set(by_source)
    if configured != actual:
        missing = sorted(actual - configured)
        unknown = sorted(configured - actual)
        details = []
        if missing:
            details.append(f"unmapped source rows: {missing}")
        if unknown:
            details.append(f"unknown configured rows: {unknown}")
        raise LcdReferenceProfileError("; ".join(details))

    result: list[dict[str, str]] = []
    for entry in presentation:
        source_no = str(entry["source_no"]).strip()
        rendered = dict(by_source[source_no])
        rendered["no"] = str(entry["display_no"]).strip()
        rendered["number_row_span"] = str(entry.get("number_row_span", 1))
        rendered["suppress_number"] = "true" if entry.get("suppress_number") else "false"
        rendered["typography_role"] = str(
            entry.get("typography_role") or "default"
        )
        heights = entry.get("row_height_pt_by_language")
        if heights is not None:
            normalized_language = (
                (language or "").strip().casefold().replace("_", "-").split("-", 1)[0]
            )
            if not normalized_language:
                raise LcdReferenceProfileError(
                    f"LCD row {source_no} requires a language for governed height"
                )
            if normalized_language not in heights:
                raise LcdReferenceProfileError(
                    f"LCD row {source_no} has no governed height for "
                    f"language {normalized_language}"
                )
            rendered["row_height_pt"] = f"{float(heights[normalized_language]):g}"
        result.append(rendered)
    return tuple(result)
