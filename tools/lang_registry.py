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


@dataclass(frozen=True)
class IdmlLanguagePack:
    """Localized copy and display metadata consumed by the IDML exporter."""

    code: str
    toc_code: str
    toc_label: str
    overview_title: str
    symbols_title: str
    symbol_copy: tuple[str, str, str, str]

    @property
    def toc_header(self) -> str:
        return f"{self.toc_code}  {self.toc_label}"


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
            # The bare ``pt-BR`` column is a historical phase2 field and must
            # remain in the exported schema alongside the localized text.
            ("spec_footnotes", _columns("Text_pt-BR", "pt-BR")),
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

IDML_SYMBOL_COPY_KEYS = ("title", "symbol", "meaning", "warning")

# IDML-only language packs belong beside the canonical language registry.  The
# exporter must not carry a second, partially registered language table in its
# loader or TOC modules.
IDML_LANGUAGE_PACKS = {
    code: IdmlLanguagePack(code, toc_code, toc_label, overview, symbols, copy)
    for code, toc_code, toc_label, overview, symbols, copy in (
        (
            "en", "EN", "English", "PRODUCT OVERVIEW", "MEANING OF SYMBOLS",
            ("MEANING OF SYMBOLS", "Symbol", "Meaning", "WARNING"),
        ),
        (
            "zh", "ZH", "中文", "产品概览", "符号含义",
            ("符号含义", "符号", "含义", "警告"),
        ),
        (
            "ja", "JA", "日本語", "製品概要", "記号の意味",
            ("記号の意味", "記号", "意味", "警告"),
        ),
        (
            "fr", "FR", "Français", "APERÇU DU PRODUIT",
            "SIGNIFICATION DES SYMBOLES",
            ("SIGNIFICATION DES SYMBOLES", "Symbole", "Signification", "AVERTISSEMENT"),
        ),
        (
            "es", "ES", "Español", "DESCRIPCIÓN GENERAL DEL PRODUCTO",
            "SIGNIFICADO DE LOS SÍMBOLOS",
            ("SIGNIFICADO DE LOS SÍMBOLOS", "Símbolo", "Significado", "ADVERTENCIA"),
        ),
        (
            "pt-BR", "PT-BR", "Português (Brasil)", "VISÃO GERAL DO PRODUTO",
            "SIGNIFICADO DOS SÍMBOLOS",
            ("SIGNIFICADO DOS SÍMBOLOS", "Símbolo", "Significado", "ADVERTÊNCIA"),
        ),
        (
            "de", "DE", "Deutsch", "PRODUKTÜBERSICHT", "BEDEUTUNG DER SYMBOLE",
            ("BEDEUTUNG DER SYMBOLE", "Symbol", "Bedeutung", "WARNUNG"),
        ),
        (
            "it", "IT", "Italiano", "PANORAMICA DEL PRODOTTO",
            "SIGNIFICATO DEI SIMBOLI",
            ("SIGNIFICATO DEI SIMBOLI", "Simbolo", "Significato", "AVVERTENZA"),
        ),
        (
            "uk", "UK", "Українська", "ОГЛЯД ПРОДУКТУ", "ЗНАЧЕННЯ СИМВОЛІВ",
            ("ЗНАЧЕННЯ СИМВОЛІВ", "Символ", "Значення", "ПОПЕРЕДЖЕННЯ"),
        ),
        (
            "ko", "KO", "한국어", "제품 개요", "기호의 의미",
            ("기호의 의미", "기호", "의미", "경고"),
        ),
    )
}

# Only languages with an approved reference-layout geometry receive governed
# IDML spacing/placement overrides.  Registration of a new language does not
# accidentally opt it into the production-master layout contract.
_IDML_GOVERNED_LANGUAGE_CODES = frozenset(("en", "fr", "es"))

# Source-table headers retain their historical order for snapshot and manifest
# compatibility.  Keep that order in the registry so schema consumers do not
# repeat language lists in their own TABLE_SCHEMAS definitions.
TABLE_LANGUAGE_ORDER = {
    "spec_master": ("fr", "es", "pt-BR", "de", "it", "uk", "ko"),
    "spec_footnotes": (
        "en", "fr", "es", "pt-BR", "ja", "zh", "de", "it", "uk",
    ),
    "spec_notes": (
        "en", "fr", "es", "pt-BR", "ja", "zh", "de", "it", "uk",
    ),
    "symbols_blocks": (
        "en", "fr", "es", "pt-BR", "de", "it", "uk", "ja", "zh", "ko",
    ),
    "lcd_icons": (
        "en", "zh", "ja", "fr", "es", "pt-BR", "de", "it", "uk", "ko",
    ),
    "troubleshooting": (
        "en", "fr", "es", "pt-BR", "de", "it", "uk", "ja", "zh", "ko",
    ),
}


def _table_specs_in_schema_order(table_name: str) -> tuple[LanguageSpec, ...]:
    """Return registered languages in the target table's legacy order."""

    codes = TABLE_LANGUAGE_ORDER.get(table_name)
    if codes is None:
        return LANGUAGE_REGISTRY
    # Preserve the historical order for languages already shipped, then append
    # any newly registered language automatically. A new registry row must not
    # require a second edit to this compatibility-order table.
    ordered_codes = (*codes, *(spec.code for spec in LANGUAGE_REGISTRY))
    seen: set[str] = set()
    ordered: list[LanguageSpec] = []
    for code in ordered_codes:
        if code in seen:
            continue
        spec = LANGUAGE_BY_CODE.get(code)
        if spec is None:
            continue
        seen.add(code)
        ordered.append(spec)
    return tuple(ordered)


def canonical_language(value: object) -> str | None:
    """Return the registry code for a canonical code or historical alias."""

    token = str(value or "").strip().casefold()
    return LANGUAGE_BY_ALIAS.get(token)


def language_spec(value: object) -> LanguageSpec | None:
    """Resolve ``value`` to its registry metadata, if registered."""

    code = canonical_language(value)
    return LANGUAGE_BY_CODE.get(code) if code else None


def idml_language_pack(value: object) -> IdmlLanguagePack | None:
    """Resolve canonical language or alias to its IDML language pack."""

    code = canonical_language(value)
    return IDML_LANGUAGE_PACKS.get(code) if code else None


def governed_languages() -> tuple[str, ...]:
    """Return languages with an approved, reference-bound IDML layout."""

    return tuple(
        spec.code
        for spec in LANGUAGE_REGISTRY
        if spec.code in _IDML_GOVERNED_LANGUAGE_CODES
    )


def language_display_labels() -> dict[str, str]:
    """Return display labels keyed by every registered canonical/alias token."""

    return {
        alias.casefold(): spec.display_name
        for spec in LANGUAGE_REGISTRY
        for alias in spec.aliases
    }


def language_alias_candidates(value: object) -> tuple[str, ...]:
    """Return registered historical aliases in lookup precedence order."""

    token = str(value or "").strip().casefold()
    if not token:
        return ()
    spec = language_spec(value)
    if spec is None:
        return (token,)
    aliases = tuple(alias.casefold() for alias in spec.aliases)
    if token not in aliases:
        return aliases
    index = aliases.index(token)
    return aliases[index:] + aliases[:index]


def table_language_columns(table_name: str) -> tuple[str, ...]:
    """Return all language-specific columns in schema order for a table."""

    columns: list[str] = []
    for spec in _table_specs_in_schema_order(table_name):
        columns.extend(spec.columns_for_table(table_name))

    if table_name == "lcd_icons":
        icon_columns = [
            column
            for column in columns
            if column.startswith("icon_") and not column.startswith("icon_desc_")
        ]
        description_columns = [column for column in columns if column.startswith("icon_desc_")]
        return tuple((*icon_columns, *description_columns))

    return tuple(columns)
