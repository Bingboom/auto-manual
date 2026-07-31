"""Registry-derived language surfaces for :mod:`tools.content_lint`."""

from __future__ import annotations

from tools import lang_registry


# The East-Asian long-tail is report-only until its source-table population is
# complete, but it must remain visible in the default QC report.
DEFAULT_LANGS = ("fr", "es", "de", "it", "uk", "ja", "ko", "zh")
REPORT_ONLY_LANGS = frozenset({"ja", "ko", "zh"})


def _column_suffix(spec: lang_registry.LanguageSpec, table_name: str, prefix: str) -> str | None:
    marker = f"{prefix}_"
    for column in spec.columns_for_table(table_name):
        if column.startswith(marker):
            return column.removeprefix(marker)
    return None


def _language_suffix_map(table_name: str, prefix: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for spec in lang_registry.LANGUAGE_REGISTRY:
        suffix = _column_suffix(spec, table_name, prefix)
        if suffix is not None:
            values[spec.code] = suffix
    return values


# Per-file language→column-suffix maps are registry-derived.  The source
# snapshot is not uniform: uk uses ukr for LCD/troubleshooting, ja uses jp for
# those IDML-facing fields, and values without a localized spec-master column
# intentionally fall back to Value_source.
_LCD_DESC = _language_suffix_map("lcd_icons", "icon_desc")
_TROUBLE = _language_suffix_map("troubleshooting", "corrective_measures")
_TEXT = {
    spec.code: (
        _column_suffix(spec, "spec_notes", "Text")
        or _column_suffix(spec, "spec_footnotes", "Text")
        or spec.code
    )
    for spec in lang_registry.LANGUAGE_REGISTRY
}
_VALUE = {
    spec.code: _column_suffix(spec, "spec_master", "Value") or "source"
    for spec in lang_registry.LANGUAGE_REGISTRY
}

# All registered languages have a deterministic column fallback for every
# check. Missing physical columns remain an empty observation, never a deep
# KeyError or an implicit English skip.
SUPPORTED_LANGS = tuple(spec.code for spec in lang_registry.LANGUAGE_REGISTRY)


def _canonical_lang(value: object) -> str:
    return lang_registry.canonical_language(value) or str(value or "").strip()


def _status_word_column(value: object) -> str:
    spec = lang_registry.language_spec(value)
    return spec.status_word_column if spec is not None else str(value or "").strip()


def _finding_severity(lang: object, default: str) -> str:
    if default == "FAIL" and _canonical_lang(lang) in REPORT_ONLY_LANGS:
        return "INFO"
    return default
