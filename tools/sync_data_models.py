from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


class RecordSource(Protocol):
    def fetch_records(
        self,
        *,
        base_token: str,
        table_id: str,
        view_id: str | None,
    ) -> list[dict[str, Any]]:
        ...


@dataclass(frozen=True)
class TableSchema:
    logical_name: str
    file_name: str
    columns: tuple[str, ...]


@dataclass(frozen=True)
class TableBinding:
    logical_name: str
    schema: TableSchema
    base_token_env: str
    table_id_env: str
    view_id_env: str | None
    base_token: str
    table_id: str
    view_id: str | None


@dataclass(frozen=True)
class TableSyncResult:
    logical_name: str
    file_name: str
    target_path: Path
    row_count: int
    sha256: str
    previous_sha256: str | None
    changed: bool


@dataclass(frozen=True)
class SyncRunResult:
    export_root: Path
    manifest_path: Path
    dry_run: bool
    provider: str
    cli_bin: str
    requested_tables: tuple[str, ...]
    skipped_tables: tuple[str, ...]
    synced_tables: tuple[TableSyncResult, ...]
    derived_files: tuple[TableSyncResult, ...]
    manifest: dict[str, Any]


TABLE_ORDER = (
    "spec_titles",
    "spec_footnotes",
    "spec_notes",
    "symbols_blocks",
    "lcd_icons",
    "troubleshooting",
    "variable_defaults",
    "variable_lang_overrides",
    "localized_copy",
    "spec_master",
)
SUPPORTED_PROVIDERS = {"lark_cli", "lark-cli", "cli"}
SUPPORTED_IDENTITIES = {"user", "bot"}
ROW_KEY_MAPPING_FIELDNAMES = ("Row_label_source", "Line_order", "Row_key", "Remark")

TABLE_SCHEMAS: dict[str, TableSchema] = {
    "spec_master": TableSchema(
        logical_name="spec_master",
        file_name="Spec_Master.csv",
        columns=(
            "spec_row_key",
            "document_key",
            "Model",
            "Region",
            "Source_lang",
            "Version",
            "Is_Latest",
            "Page",
            "Section",
            "Section_order",
            "Row_order",
            "Row_key",
            "Slot_key",
            "Row_label_source",
            "Row_label_footnote_refs",
            "Line_order",
            "Param_source",
            "Param_footnote_refs",
            "Value_source",
            "Value_footnote_refs",
            "Row_label_fr",
            "Param_fr",
            "Value_fr",
            "Row_label_es",
            "Param_es",
            "Value_es",
            "Row_label_br",
            "Param_br",
            "Value_br",
            "Row_label_de",
            "Param_de",
            "Value_de",
            "Row_label_it",
            "Param_it",
            "Value_it",
            "Row_label_uk",
            "Param_uk",
            "Value_uk",
        ),
    ),
    "spec_footnotes": TableSchema(
        logical_name="spec_footnotes",
        file_name="Spec_Footnotes.csv",
        columns=(
            "Footnote_id",
            "Region",
            "Model",
            "Source_lang",
            "Is_Latest",
            "Page",
            "Footnote_order",
            "Type",
            "Text_en",
            "Text_fr",
            "Text_es",
            "Text_pt-BR",
            "pt-BR",
            "Text_ja",
            "Text_de",
            "Text_it",
            "Text_uk",
            "Enabled",
        ),
    ),
    "spec_notes": TableSchema(
        logical_name="spec_notes",
        file_name="Spec_Notes.csv",
        columns=(
            "Note_id",
            "Region",
            "Model",
            "Source_lang",
            "Is_Latest",
            "Page",
            "Note_order",
            "Type",
            "Text_en",
            "Text_fr",
            "Text_es",
            "Text_pt-BR",
            "Text_ja",
            "Text_de",
            "Text_it",
            "Text_uk",
            "Enabled",
        ),
    ),
    "spec_titles": TableSchema(
        logical_name="spec_titles",
        file_name="spec_titles.csv",
        columns=(
            "title_en",
            "section_order",
            "title_zh",
            "title_jp",
            "title_fr",
            "title_es",
            "title_de",
            "title_it",
            "title_uk",
        ),
    ),
    "symbols_blocks": TableSchema(
        logical_name="symbols_blocks",
        file_name="symbols_blocks.csv",
        columns=(
            "symbol_key",
            "Figure",
            "image_path",
            "label_en",
            "aliases_en",
            "text_en",
            "label_fr",
            "aliases_fr",
            "text_fr",
            "label_es",
            "aliases_es",
            "text_es",
            "label_pt-BR",
            "aliases_pt-BR",
            "text_pt-BR",
            "label_de",
            "aliases_de",
            "text_de",
            "label_it",
            "aliases_it",
            "text_it",
            "label_uk",
            "aliases_uk",
            "text_uk",
            "label_jp",
            "aliases_jp",
            "text_jp",
            "label_zh",
            "aliases_zh",
            "text_zh",
            "Is_Latest",
            "Market",
            "block_type",
            "order",
            "Model",
            "Source_lang",
            "notes",
        ),
    ),
    "lcd_icons": TableSchema(
        logical_name="lcd_icons",
        file_name="lcd_icons_blocks.csv",
        columns=(
            "No.",
            "Model",
            "Is_latest",
            "Version",
            "icon_en",
            "icon_zh",
            "icon_jp",
            "icon_fr",
            "icon_es",
            "icon_pt-BR",
            "icon_br",
            "icon_de",
            "icon_it",
            "icon_ukr",
            "icon_desc_en",
            "icon_desc_zh",
            "icon_desc_jp",
            "icon_desc_fr",
            "icon_desc_es",
            "icon_desc_pt-BR",
            "icon_desc_br",
            "icon_desc_de",
            "icon_desc_it",
            "icon_desc_ukr",
            "has_variables",
            "variable_keys",
            "figure",
            "render_preview_en",
        ),
    ),
    "troubleshooting": TableSchema(
        logical_name="troubleshooting",
        file_name="troubleshooting_blocks.csv",
        columns=(
            "No.",
            "Model",
            "Region",
            "Is_latest",
            "Version",
            "error_code",
            "corrective_measures_en",
            "corrective_measures_fr",
            "corrective_measures_es",
            "corrective_measures_pt-BR",
            "corrective_measures_br",
            "corrective_measures_de",
            "corrective_measures_it",
            "corrective_measures_ukr",
            "corrective_measures_jp",
            "corrective_measures_zh",
            "render_preview_en",
        ),
    ),
    "variable_defaults": TableSchema(
        logical_name="variable_defaults",
        file_name="Variable_Defaults.csv",
        columns=(
            "Variable_key",
            "Model_key",
            "Model",
            "Value",
            "is_default",
        ),
    ),
    "variable_lang_overrides": TableSchema(
        logical_name="variable_lang_overrides",
        file_name="Variable_Lang_Overrides.csv",
        columns=(
            "Variable_key",
            "lang",
            "source_value",
            "Value",
            "from_prefix",
            "to_prefix",
        ),
    ),
    "localized_copy": TableSchema(
        logical_name="localized_copy",
        file_name="Localized_Copy.csv",
        columns=(
            "copy_key",
            "page_id",
            "copy_type",
            "Region",
            "Model",
            "Source_lang",
            "Is_Latest",
            "Version",
            "text_en",
            "text_zh",
            "text_ja",
            "text_fr",
            "text_es",
            "text_pt-BR",
            "text_de",
            "text_it",
            "text_uk",
            "notes",
        ),
    ),
}
