"""Explicit semantic page roles for production IDML assembly routing."""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable


class PageRole(str, Enum):
    PREFACE = "preface"
    TOC = "toc"
    FCC = "fcc"
    MAINTENANCE = "maintenance"
    MEANING_OF_SYMBOLS = "meaning_of_symbols"
    INBOX = "inbox"
    PRODUCT_OVERVIEW = "product_overview"
    OPERATION_GUIDE = "operation_guide"
    UPS_MODE = "ups_mode"
    EXTRA_BATTERY = "extra_battery"
    CHARGING = "charging"
    CHARGING_METHODS = "charging_methods"
    STORAGE_MAINTENANCE = "storage_maintenance"
    TROUBLESHOOTING_PROSE = "troubleshooting_prose"
    WARRANTY = "warranty"
    APP_SETUP = "app_setup"
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
    pattern: re.Pattern[str] | None = None

    def matches(self, stem: str) -> bool:
        if self.pattern is not None and self.pattern.fullmatch(stem):
            return True
        return any(
            stem == semantic or stem.endswith(f"_{semantic}")
            for semantic in self.semantic_stems
        )


PAGE_ROLE_RULES: tuple[PageRoleRule, ...] = (
    PageRoleRule(PageRole.COVER, pattern=re.compile(r"cover(?:[-_].+)?")),
    PageRoleRule(PageRole.SAFETY, pattern=re.compile(r"safety(?:[-_].+)?")),
    PageRoleRule(PageRole.SPEC, pattern=re.compile(r"spec(?:[-_].+)?")),
    PageRoleRule(PageRole.LCD, pattern=re.compile(r"lcd_icons(?:[-_].+)?")),
    PageRoleRule(PageRole.SYMBOLS, pattern=re.compile(r"symbols(?:[-_].+)?")),
    PageRoleRule(
        PageRole.TROUBLESHOOTING_DATA,
        pattern=re.compile(r"troubleshooting(?:[-_].+)?"),
    ),
    PageRoleRule(
        PageRole.PREFACE,
        semantic_stems=("00_preface", "00_preface_single_language"),
    ),
    PageRoleRule(PageRole.TOC, semantic_stems=("00_toc",)),
    PageRoleRule(PageRole.FCC, semantic_stems=("01_fcc",)),
    PageRoleRule(
        PageRole.MAINTENANCE,
        semantic_stems=("01_user_maintenance_instructions",),
    ),
    PageRoleRule(
        PageRole.MEANING_OF_SYMBOLS,
        semantic_stems=("01_meaning_of_symbols",),
    ),
    PageRoleRule(PageRole.INBOX, semantic_stems=("02_whats_in_the_box",)),
    PageRoleRule(
        PageRole.PRODUCT_OVERVIEW,
        pattern=re.compile(r"(?:p\d+_)?03_product_overview(?:_.+)?"),
    ),
    PageRoleRule(
        PageRole.OPERATION_GUIDE,
        semantic_stems=("05_operation_guide", "05_operation_guide_placeholder"),
    ),
    PageRoleRule(PageRole.UPS_MODE, semantic_stems=("06_ups_mode",)),
    PageRoleRule(PageRole.EXTRA_BATTERY, semantic_stems=("07_extra_battery",)),
    PageRoleRule(PageRole.CHARGING, semantic_stems=("charging",)),
    PageRoleRule(
        PageRole.CHARGING_METHODS,
        semantic_stems=("08_charging_methods",),
    ),
    PageRoleRule(
        PageRole.STORAGE_MAINTENANCE,
        semantic_stems=("09_storage_and_maintenance",),
    ),
    PageRoleRule(
        PageRole.TROUBLESHOOTING_PROSE,
        semantic_stems=("10_troubleshooting",),
    ),
    PageRoleRule(PageRole.WARRANTY, semantic_stems=("11_warranty",)),
    PageRoleRule(
        PageRole.APP_SETUP,
        semantic_stems=("12_app_setup", "12_app_setup_placeholder"),
    ),
    PageRoleRule(PageRole.BACK_COVER, semantic_stems=("99_back_cover",)),
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
