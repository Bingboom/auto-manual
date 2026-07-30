"""Canonical language metadata shared by the language parity checks.

Consumers derive their language constants and alias handling from this registry
so a new language has one metadata insertion point and parity tests can prove
the resulting surfaces remain aligned.
"""

from __future__ import annotations

from dataclasses import dataclass


CORE_TABLE_NAMES = (
    "spec_master",
    "spec_footnotes",
    "spec_notes",
    "symbols_blocks",
    "lcd_icons",
    "troubleshooting",
)


@dataclass(frozen=True)
class LanguageSpec:
    """The current language contract across source tables and renderers."""

    code: str
    aliases: tuple[str, ...]
    column_suffixes: tuple[str, ...]
    table_columns: tuple[tuple[str, tuple[str, ...]], ...]
    tm_column: str
    localized_copy_column: str
    status_word_column: str
    spec_title_column: str | None
    display_name: str
    template_directory: str
    separator: str

    def columns_for_table(self, table_name: str) -> tuple[str, ...]:
        """Return the language columns for ``table_name``."""

        for name, columns in self.table_columns:
            if name == table_name:
                return columns
        return ()


def _columns(*items: str) -> tuple[str, ...]:
    return tuple(items)


LANGUAGE_REGISTRY = (
    LanguageSpec(
        code="en",
        aliases=("en",),
        column_suffixes=("en",),
        table_columns=(
            ("spec_footnotes", _columns("Text_en")),
            ("spec_notes", _columns("Text_en")),
            ("symbols_blocks", _columns("label_en", "aliases_en", "text_en")),
            ("lcd_icons", _columns("icon_en", "icon_desc_en")),
            ("troubleshooting", _columns("corrective_measures_en")),
        ),
        tm_column="en",
        localized_copy_column="text_en",
        status_word_column="en",
        spec_title_column="title_en",
        display_name="English",
        template_directory="page_shared/en",
        separator=": ",
    ),
    LanguageSpec(
        code="zh",
        aliases=("zh",),
        # ``cn`` is retained as a historical lookup candidate by the IDML
        # loader; the current source-table schemas only contain ``zh``.
        column_suffixes=("zh", "cn"),
        table_columns=(
            ("spec_footnotes", _columns("Text_zh")),
            ("spec_notes", _columns("Text_zh")),
            ("symbols_blocks", _columns("label_zh", "aliases_zh", "text_zh")),
            ("lcd_icons", _columns("icon_zh", "icon_desc_zh")),
            ("troubleshooting", _columns("corrective_measures_zh")),
        ),
        tm_column="zh",
        localized_copy_column="text_zh",
        status_word_column="zh",
        spec_title_column="title_zh",
        display_name="Chinese",
        template_directory="page_zh",
        separator=": ",
    ),
    LanguageSpec(
        code="ja",
        aliases=("ja", "jp"),
        # IDML tries the historical ``jp`` column before the newer ``ja``
        # footnote spelling.  Table-specific columns below remain explicit.
        column_suffixes=("jp", "ja"),
        table_columns=(
            ("spec_footnotes", _columns("Text_ja")),
            ("spec_notes", _columns("Text_ja")),
            ("symbols_blocks", _columns("label_jp", "aliases_jp", "text_jp")),
            ("lcd_icons", _columns("icon_jp", "icon_desc_jp")),
            ("troubleshooting", _columns("corrective_measures_jp")),
        ),
        tm_column="jp",
        localized_copy_column="text_ja",
        status_word_column="jp",
        spec_title_column="title_jp",
        display_name="Japanese",
        template_directory="page_jp",
        separator="：",
    ),
    LanguageSpec(
        code="fr",
        aliases=("fr",),
        column_suffixes=("fr",),
        table_columns=(
            ("spec_master", _columns("Row_label_fr", "Param_fr", "Value_fr")),
            ("spec_footnotes", _columns("Text_fr")),
            ("spec_notes", _columns("Text_fr")),
            ("symbols_blocks", _columns("label_fr", "aliases_fr", "text_fr")),
            ("lcd_icons", _columns("icon_fr", "icon_desc_fr")),
            ("troubleshooting", _columns("corrective_measures_fr")),
        ),
        tm_column="fr",
        localized_copy_column="text_fr",
        status_word_column="fr",
        spec_title_column="title_fr",
        display_name="French",
        template_directory="page_shared/fr",
        separator=" : ",
    ),
    LanguageSpec(
        code="es",
        aliases=("es",),
        column_suffixes=("es",),
        table_columns=(
            ("spec_master", _columns("Row_label_es", "Param_es", "Value_es")),
            ("spec_footnotes", _columns("Text_es")),
            ("spec_notes", _columns("Text_es")),
            ("symbols_blocks", _columns("label_es", "aliases_es", "text_es")),
            ("lcd_icons", _columns("icon_es", "icon_desc_es")),
            ("troubleshooting", _columns("corrective_measures_es")),
        ),
        tm_column="es",
        localized_copy_column="text_es",
        status_word_column="es",
        spec_title_column="title_es",
        display_name="Spanish",
        template_directory="page_shared/es",
        separator=": ",
    ),
    LanguageSpec(
        code="pt-BR",
        # ``pt-BR`` case-folds to the historical ``pt-br`` lookup key.
        aliases=("pt-BR", "pt_br", "br"),
        column_suffixes=("pt-BR", "br"),
        table_columns=(
            ("spec_master", _columns("Row_label_br", "Param_br", "Value_br")),
            ("spec_footnotes", _columns("Text_pt-BR")),
            ("spec_notes", _columns("Text_pt-BR")),
            (
                "symbols_blocks",
                _columns("label_pt-BR", "aliases_pt-BR", "text_pt-BR"),
            ),
            (
                "lcd_icons",
                _columns("icon_pt-BR", "icon_br", "icon_desc_pt-BR", "icon_desc_br"),
            ),
            (
                "troubleshooting",
                _columns("corrective_measures_pt-BR", "corrective_measures_br"),
            ),
        ),
        tm_column="pt-BR",
        localized_copy_column="text_pt-BR",
        status_word_column="pt-BR",
        spec_title_column=None,
        display_name="Portuguese (Brazil)",
        template_directory="page_shared/pt-BR",
        separator=": ",
    ),
    LanguageSpec(
        code="de",
        aliases=("de",),
        column_suffixes=("de",),
        table_columns=(
            ("spec_master", _columns("Row_label_de", "Param_de", "Value_de")),
            ("spec_footnotes", _columns("Text_de")),
            ("spec_notes", _columns("Text_de")),
            ("symbols_blocks", _columns("label_de", "aliases_de", "text_de")),
            ("lcd_icons", _columns("icon_de", "icon_desc_de")),
            ("troubleshooting", _columns("corrective_measures_de")),
        ),
        tm_column="de",
        localized_copy_column="text_de",
        status_word_column="de",
        spec_title_column="title_de",
        display_name="German",
        template_directory="page_shared/de",
        separator=": ",
    ),
    LanguageSpec(
        code="it",
        aliases=("it",),
        column_suffixes=("it",),
        table_columns=(
            ("spec_master", _columns("Row_label_it", "Param_it", "Value_it")),
            ("spec_footnotes", _columns("Text_it")),
            ("spec_notes", _columns("Text_it")),
            ("symbols_blocks", _columns("label_it", "aliases_it", "text_it")),
            ("lcd_icons", _columns("icon_it", "icon_desc_it")),
            ("troubleshooting", _columns("corrective_measures_it")),
        ),
        tm_column="it",
        localized_copy_column="text_it",
        status_word_column="it",
        spec_title_column="title_it",
        display_name="Italian",
        template_directory="page_shared/it",
        separator=": ",
    ),
    LanguageSpec(
        code="uk",
        aliases=("uk", "ukr"),
        column_suffixes=("uk", "ukr"),
        table_columns=(
            ("spec_master", _columns("Row_label_uk", "Param_uk", "Value_uk")),
            ("spec_footnotes", _columns("Text_uk")),
            ("spec_notes", _columns("Text_uk")),
            ("symbols_blocks", _columns("label_uk", "aliases_uk", "text_uk")),
            ("lcd_icons", _columns("icon_ukr", "icon_desc_ukr")),
            ("troubleshooting", _columns("corrective_measures_ukr")),
        ),
        tm_column="uk",
        localized_copy_column="text_uk",
        status_word_column="uk",
        spec_title_column="title_uk",
        display_name="Ukrainian",
        template_directory="page_shared/uk",
        separator=": ",
    ),
    LanguageSpec(
        code="ko",
        aliases=("ko",),
        column_suffixes=("ko",),
        table_columns=(
            ("spec_master", _columns("Row_label_ko", "Param_ko", "Value_ko")),
            ("symbols_blocks", _columns("label_ko", "aliases_ko", "text_ko")),
            ("lcd_icons", _columns("icon_ko", "icon_desc_ko")),
            ("troubleshooting", _columns("corrective_measures_ko")),
        ),
        tm_column="ko",
        localized_copy_column="text_ko",
        status_word_column="ko",
        spec_title_column="title_ko",
        display_name="Korean",
        template_directory="page_shared/ko",
        separator=": ",
    ),
)


LANGUAGE_BY_CODE = {spec.code: spec for spec in LANGUAGE_REGISTRY}
LANGUAGE_BY_ALIAS = {
    alias.casefold(): spec.code
    for spec in LANGUAGE_REGISTRY
    for alias in spec.aliases
}


def canonical_language(value: object) -> str | None:
    """Return the registry code for a canonical code or historical alias."""

    token = str(value or "").strip().casefold()
    return LANGUAGE_BY_ALIAS.get(token)


def language_spec(value: object) -> LanguageSpec | None:
    """Resolve ``value`` to its registry metadata, if registered."""

    code = canonical_language(value)
    return LANGUAGE_BY_CODE.get(code) if code else None


def table_language_columns(table_name: str) -> tuple[str, ...]:
    """Return all language-specific columns in registry order for a table."""

    columns: list[str] = []
    for spec in LANGUAGE_REGISTRY:
        columns.extend(spec.columns_for_table(table_name))
    return tuple(columns)
