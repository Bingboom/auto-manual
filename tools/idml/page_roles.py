"""Explicit semantic page roles for production IDML assembly routing."""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable

from tools.lang_registry import LANGUAGE_BY_ALIAS


class PageRole(str, Enum):
    PREFACE = "preface"
    TOC = "toc"
    FCC = "fcc"
    MAINTENANCE = "maintenance"
    MEANING_OF_SYMBOLS = "meaning_of_symbols"
    INBOX = "inbox"
    PRODUCT_OVERVIEW = "product_overview"
    CONNECTIONS = "connections"
    OPERATION_GUIDE = "operation_guide"
    UPS_MODE = "ups_mode"
    EXTRA_BATTERY = "extra_battery"
    CHARGING = "charging"
    CHARGING_METHODS = "charging_methods"
    STORAGE_MAINTENANCE = "storage_maintenance"
    TROUBLESHOOTING_PROSE = "troubleshooting_prose"
    WARRANTY = "warranty"
    APP_SETUP = "app_setup"
    REGULATORY_COMPLIANCE = "regulatory_compliance"
    BACK_COVER = "back_cover"
    COVER = "cover"
    SAFETY = "safety"
    SPEC = "spec"
    LCD = "lcd"
    SYMBOLS = "symbols"
    TROUBLESHOOTING_DATA = "troubleshooting_data"
    UNCLASSIFIED_PROSE = "unclassified_prose"


@dataclass(frozen=True)
class PageRoleRule:
    """One target-neutral source identity to assembly-role binding."""

    role: PageRole
    semantic_stems: tuple[str, ...] = ()
    stable_aliases: tuple[str, ...] = ()
    pattern: re.Pattern[str] | None = None

    def matches(self, stem: str) -> bool:
        if stem in self.stable_aliases:
            return True
        if self.pattern is not None and self.pattern.fullmatch(stem):
            return True
        return any(
            stem == semantic or stem.endswith(f"_{semantic}")
            for semantic in self.semantic_stems
        )


_LANGUAGE_CODES = tuple(sorted(LANGUAGE_BY_ALIAS))
_LANGUAGE_PATTERN = "(?:" + "|".join(_LANGUAGE_CODES) + ")"


def _localized_aliases(stem: str) -> tuple[str, ...]:
    return tuple(f"{stem}_{lang}" for lang in _LANGUAGE_CODES)


PAGE_ROLE_RULES: tuple[PageRoleRule, ...] = (
    PageRoleRule(
        PageRole.COVER,
        stable_aliases=("cover",),
        pattern=re.compile(
            rf"cover(?:[-_][a-z0-9]*[0-9][a-z0-9]*)?"
            rf"[-_]{_LANGUAGE_PATTERN}"
        ),
    ),
    PageRoleRule(
        PageRole.SAFETY,
        stable_aliases=_localized_aliases("safety_info"),
        pattern=re.compile(rf"safety_{_LANGUAGE_PATTERN}"),
    ),
    PageRoleRule(
        PageRole.SPEC,
        stable_aliases=_localized_aliases("specifications"),
        pattern=re.compile(rf"spec_(?:{_LANGUAGE_PATTERN}|template)"),
    ),
    PageRoleRule(
        PageRole.LCD,
        stable_aliases=_localized_aliases("lcd_display"),
        pattern=re.compile(rf"lcd_icons_(?:{_LANGUAGE_PATTERN}|template)"),
    ),
    PageRoleRule(
        PageRole.SYMBOLS,
        stable_aliases=_localized_aliases("symbol_meaning"),
        pattern=re.compile(rf"symbols_(?:{_LANGUAGE_PATTERN}|template)"),
    ),
    PageRoleRule(
        PageRole.TROUBLESHOOTING_DATA,
        stable_aliases=_localized_aliases("troubleshooting"),
        pattern=re.compile(rf"troubleshooting_(?:{_LANGUAGE_PATTERN}|template)"),
    ),
    PageRoleRule(
        PageRole.PREFACE,
        semantic_stems=("00_preface", "00_preface_single_language"),
        stable_aliases=("preface_important",),
    ),
    PageRoleRule(
        PageRole.TOC,
        semantic_stems=("00_toc",),
        stable_aliases=("toc",),
    ),
    PageRoleRule(
        PageRole.FCC,
        semantic_stems=("01_fcc",),
        stable_aliases=_localized_aliases("fcc"),
    ),
    PageRoleRule(
        PageRole.MAINTENANCE,
        semantic_stems=("01_user_maintenance_instructions",),
    ),
    PageRoleRule(
        PageRole.MEANING_OF_SYMBOLS,
        semantic_stems=("01_meaning_of_symbols",),
    ),
    PageRoleRule(
        PageRole.INBOX,
        semantic_stems=("02_whats_in_the_box",),
        stable_aliases=_localized_aliases("box_contents"),
    ),
    PageRoleRule(
        PageRole.PRODUCT_OVERVIEW,
        stable_aliases=_localized_aliases("product_overview"),
        pattern=re.compile(r"(?:p\d+_)?03_product_overview(?:_.+)?"),
    ),
    PageRoleRule(
        PageRole.CONNECTIONS,
        semantic_stems=("04_connections",),
        stable_aliases=_localized_aliases("connections"),
    ),
    PageRoleRule(
        PageRole.OPERATION_GUIDE,
        semantic_stems=("05_operation_guide", "05_operation_guide_placeholder"),
        stable_aliases=_localized_aliases("operation"),
    ),
    PageRoleRule(PageRole.UPS_MODE, semantic_stems=("06_ups_mode",)),
    PageRoleRule(PageRole.EXTRA_BATTERY, semantic_stems=("07_extra_battery",)),
    PageRoleRule(
        PageRole.CHARGING,
        semantic_stems=("charging",),
        stable_aliases=_localized_aliases("charging"),
    ),
    PageRoleRule(
        PageRole.CHARGING_METHODS,
        semantic_stems=("08_charging_methods",),
    ),
    PageRoleRule(
        PageRole.STORAGE_MAINTENANCE,
        semantic_stems=("09_storage", "09_storage_and_maintenance"),
        stable_aliases=_localized_aliases("storage"),
    ),
    PageRoleRule(
        PageRole.TROUBLESHOOTING_PROSE,
        semantic_stems=("10_troubleshooting",),
    ),
    PageRoleRule(
        PageRole.WARRANTY,
        semantic_stems=("11_warranty",),
        stable_aliases=_localized_aliases("warranty"),
    ),
    PageRoleRule(
        PageRole.APP_SETUP,
        semantic_stems=("12_app_setup", "12_app_setup_placeholder"),
    ),
    PageRoleRule(
        PageRole.REGULATORY_COMPLIANCE,
        stable_aliases=("regulatory_compliance",),
        pattern=re.compile(r"99_regulatory_compliance(?:_[a-z0-9-]+)?"),
    ),
    PageRoleRule(
        PageRole.BACK_COVER,
        semantic_stems=("99_back_cover",),
        stable_aliases=("back_cover",),
    ),
)


def classify_page_role(page_path: Path) -> PageRole:
    """Classify one source page without model, region, or language branches."""

    stem = page_path.stem.casefold()
    for rule in PAGE_ROLE_RULES:
        if rule.matches(stem):
            return rule.role
    return PageRole.UNCLASSIFIED_PROSE


def assembly_coverage_warning(
    assignments: Iterable[tuple[Path, PageRole]],
) -> str | None:
    """Render one stable warning for pages using the historical prose fallback."""

    source_refs: list[str] = []
    seen: set[str] = set()
    for source_ref, role in assignments:
        value = source_ref.as_posix()
        if role is PageRole.UNCLASSIFIED_PROSE and value not in seen:
            source_refs.append(value)
            seen.add(value)
    if not source_refs:
        return None
    return (
        "[export-idml] WARNING: assembly coverage used unclassified prose "
        f"fallback for {len(source_refs)} source page(s): "
        + ", ".join(source_refs)
    )


__all__ = (
    "PAGE_ROLE_RULES",
    "PageRole",
    "PageRoleRule",
    "assembly_coverage_warning",
    "classify_page_role",
)
