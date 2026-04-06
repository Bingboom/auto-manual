from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DiffRow:
    tracked_root: str
    model: str
    region: str
    artifact: str
    section: str
    page_key: str
    file_name: str
    relative_path: str
    change_type: str
    insertions: str
    deletions: str
    old_path: str
    new_path: str
    from_ref: str
    to_ref: str


@dataclass(frozen=True)
class PageDiffRow:
    tracked_root: str
    model: str
    region: str
    artifact: str
    section: str
    page_key: str
    file_count: str
    change_types: str
    insertions: str
    deletions: str
    fields_changed: str
    relative_paths: str
    from_ref: str
    to_ref: str


@dataclass(frozen=True)
class FieldEntry:
    section_title: str
    field_key: str
    field_value: str


@dataclass(frozen=True)
class SpecFieldSource:
    section_title: str
    field_key: str
    source_section_key: str
    source_row_key: str
    source_line_order: str
    source_csv_line: str


@dataclass(frozen=True)
class PlaceholderValueSource:
    match_value: str
    source_section_key: str
    source_row_key: str
    source_line_order: str
    source_csv_line: str


@dataclass(frozen=True)
class FieldDiffRow:
    tracked_root: str
    model: str
    region: str
    artifact: str
    section: str
    page_key: str
    file_name: str
    relative_path: str
    section_title: str
    field_key: str
    change_type: str
    old_value: str
    new_value: str
    source_section_key: str
    source_row_key: str
    source_line_order: str
    source_csv_line: str
    from_ref: str
    to_ref: str


@dataclass(frozen=True)
class ResolvedFieldEntry:
    section_title: str
    field_key: str
    field_value: str
    source_section_key: str
    source_row_key: str
    source_line_order: str
    source_csv_line: str
    section_order: int


@dataclass(frozen=True)
class GeneratedReports:
    index_html: Path
    files_csv: Path
    files_html: Path
    pages_csv: Path
    pages_html: Path
    fields_csv: Path
    fields_html: Path
    legacy_csv: Path
    legacy_html: Path
