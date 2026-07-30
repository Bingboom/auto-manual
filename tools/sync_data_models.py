from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from tools import lang_registry
from tools.manual_copy_source import (
    MANUAL_COPY_SOURCE_COLUMNS,
    MANUAL_COPY_SOURCE_FILE,
    TRANSLATION_MEMORY_COLUMNS,
)


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
    "spec_footnotes",
    "spec_notes",
    "symbols_blocks",
    "lcd_icons",
    "troubleshooting",
    "variable_defaults",
    "variable_lang_overrides",
    "manual_copy_source",
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
            *lang_registry.table_language_columns("spec_master"),
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
            *lang_registry.table_language_columns("spec_footnotes"),
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
            *lang_registry.table_language_columns("spec_notes"),
            "Enabled",
        ),
    ),
    "symbols_blocks": TableSchema(
        logical_name="symbols_blocks",
        file_name="symbols_blocks.csv",
        columns=(
            "symbol_key",
            "Figure",
            "image_path",
            *lang_registry.table_language_columns("symbols_blocks"),
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
            *lang_registry.table_language_columns("lcd_icons"),
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
            *lang_registry.table_language_columns("troubleshooting"),
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
    "manual_copy_source": TableSchema(
        logical_name="manual_copy_source",
        file_name=MANUAL_COPY_SOURCE_FILE,
        columns=MANUAL_COPY_SOURCE_COLUMNS,
    ),
    "translation_memory": TableSchema(
        logical_name="translation_memory",
        file_name="Translation_Memory.csv",
        columns=TRANSLATION_MEMORY_COLUMNS,
    ),
}
