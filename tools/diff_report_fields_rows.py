from __future__ import annotations

from pathlib import Path

from tools.diff_report_fields_extract import extract_field_entries
from tools.diff_report_fields_shared import derive_lang_from_page_key, resolve_spec_paths
from tools.diff_report_fields_sources import (
    build_placeholder_source_lookup,
    build_spec_source_lookup,
    match_placeholder_sources,
    merge_sources,
)
from tools.diff_report_git import git_show_text
from tools.diff_report_models import (
    DiffRow,
    FieldDiffRow,
    FieldEntry,
    PageDiffRow,
    PlaceholderValueSource,
    ResolvedFieldEntry,
    SpecFieldSource,
)


def _resolve_entry_sources(
    *,
    entry: FieldEntry,
    spec_lookup: dict[tuple[str, str], SpecFieldSource],
    placeholder_lookup: dict[str, list[PlaceholderValueSource]],
) -> tuple[str, str, str, str]:
    source = spec_lookup.get((entry.section_title, entry.field_key))
    if source is not None:
        return merge_sources([source])
    matched_sources = match_placeholder_sources(
        field_key=entry.field_key,
        old_value="",
        new_value=entry.field_value,
        placeholder_lookup=placeholder_lookup,
    )
    return merge_sources(matched_sources)


def _annotate_field_entries(
    entries: list[FieldEntry],
    *,
    spec_lookup: dict[tuple[str, str], SpecFieldSource],
    placeholder_lookup: dict[str, list[PlaceholderValueSource]],
) -> list[ResolvedFieldEntry]:
    section_counts: dict[str, int] = {}
    resolved: list[ResolvedFieldEntry] = []
    for entry in entries:
        section_counts[entry.section_title] = section_counts.get(entry.section_title, 0) + 1
        source_section_key, source_row_key, source_line_order, source_csv_line = _resolve_entry_sources(
            entry=entry,
            spec_lookup=spec_lookup,
            placeholder_lookup=placeholder_lookup,
        )
        resolved.append(
            ResolvedFieldEntry(
                section_title=entry.section_title,
                field_key=entry.field_key,
                field_value=entry.field_value,
                source_section_key=source_section_key,
                source_row_key=source_row_key,
                source_line_order=source_line_order,
                source_csv_line=source_csv_line,
                section_order=section_counts[entry.section_title],
            )
        )
    return resolved


def _merge_resolved_sources(entries: list[ResolvedFieldEntry]) -> tuple[str, str, str, str]:
    section_keys: list[str] = []
    row_keys: list[str] = []
    line_orders: list[str] = []
    csv_lines: list[str] = []
    seen_sections: set[str] = set()
    seen_rows: set[str] = set()
    seen_line_orders: set[str] = set()
    seen_csv_lines: set[str] = set()

    for entry in entries:
        if entry.source_section_key and entry.source_section_key not in seen_sections:
            seen_sections.add(entry.source_section_key)
            section_keys.append(entry.source_section_key)
        if entry.source_row_key and entry.source_row_key not in seen_rows:
            seen_rows.add(entry.source_row_key)
            row_keys.append(entry.source_row_key)
        if entry.source_line_order and entry.source_line_order not in seen_line_orders:
            seen_line_orders.add(entry.source_line_order)
            line_orders.append(entry.source_line_order)
        if entry.source_csv_line and entry.source_csv_line not in seen_csv_lines:
            seen_csv_lines.add(entry.source_csv_line)
            csv_lines.append(entry.source_csv_line)

    return "; ".join(section_keys), "; ".join(row_keys), "; ".join(line_orders), "; ".join(csv_lines)


def _format_field_key(old_entry: ResolvedFieldEntry | None, new_entry: ResolvedFieldEntry | None) -> str:
    if old_entry is not None and new_entry is not None:
        if old_entry.field_key == new_entry.field_key:
            return new_entry.field_key
        if old_entry.field_key and new_entry.field_key:
            return f"{old_entry.field_key} -> {new_entry.field_key}"
    if new_entry is not None:
        return new_entry.field_key
    if old_entry is not None:
        return old_entry.field_key
    return ""


def _build_field_diff_row(
    *,
    file_row: DiffRow,
    old_entry: ResolvedFieldEntry | None,
    new_entry: ResolvedFieldEntry | None,
) -> FieldDiffRow | None:
    if old_entry is None and new_entry is None:
        return None

    if old_entry is not None and new_entry is not None:
        change_type = "M"
        if old_entry.field_key == new_entry.field_key and old_entry.field_value == new_entry.field_value:
            return None
    elif new_entry is not None:
        change_type = "A"
    else:
        change_type = "D"

    section_title = new_entry.section_title if new_entry is not None else old_entry.section_title if old_entry is not None else ""
    field_key = _format_field_key(old_entry, new_entry)
    old_value = old_entry.field_value if old_entry is not None else ""
    new_value = new_entry.field_value if new_entry is not None else ""
    source_section_key, source_row_key, source_line_order, source_csv_line = _merge_resolved_sources(
        [entry for entry in (old_entry, new_entry) if entry is not None]
    )
    return FieldDiffRow(
        tracked_root=file_row.tracked_root,
        model=file_row.model,
        region=file_row.region,
        artifact=file_row.artifact,
        section=file_row.section,
        page_key=file_row.page_key,
        file_name=file_row.file_name,
        relative_path=file_row.relative_path,
        section_title=section_title,
        field_key=field_key,
        change_type=change_type,
        old_value=old_value,
        new_value=new_value,
        source_section_key=source_section_key,
        source_row_key=source_row_key,
        source_line_order=source_line_order,
        source_csv_line=source_csv_line,
        from_ref=file_row.from_ref,
        to_ref=file_row.to_ref,
    )


def collect_field_diff_rows(
    *,
    repo_root: Path,
    file_rows: list[DiffRow],
    config_path: Path | None = None,
    data_root: str | None = None,
) -> list[FieldDiffRow]:
    rows: list[FieldDiffRow] = []
    spec_master_csv, spec_titles_csv = resolve_spec_paths(
        repo_root,
        config_path=config_path,
        data_root=data_root,
    )
    spec_lookup_cache: dict[tuple[str, str, str], dict[tuple[str, str], SpecFieldSource]] = {}
    placeholder_lookup_cache: dict[tuple[str, str, str], dict[str, list[PlaceholderValueSource]]] = {}
    for file_row in file_rows:
        chosen_path = file_row.new_path or file_row.old_path
        if not chosen_path.endswith(".rst"):
            continue

        old_text = git_show_text(repo_root, ref=file_row.from_ref, path_text=file_row.old_path or chosen_path)
        new_text = git_show_text(repo_root, ref=file_row.to_ref, path_text=file_row.new_path or chosen_path)
        spec_lookup: dict[tuple[str, str], SpecFieldSource] = {}
        lang = derive_lang_from_page_key(file_row.page_key)
        if file_row.page_key.startswith("spec_") and spec_master_csv.exists():
            cache_key = (file_row.model, file_row.region, lang)
            spec_lookup = spec_lookup_cache.get(cache_key, {})
            if not spec_lookup:
                spec_lookup = build_spec_source_lookup(
                    spec_master_csv=spec_master_csv,
                    spec_titles_csv=spec_titles_csv,
                    model=file_row.model,
                    region=file_row.region,
                    lang=lang,
                )
                spec_lookup_cache[cache_key] = spec_lookup
        placeholder_lookup: dict[str, list[PlaceholderValueSource]] = {}
        if spec_master_csv.exists():
            cache_key = (file_row.model, file_row.region, lang)
            placeholder_lookup = placeholder_lookup_cache.get(cache_key, {})
            if not placeholder_lookup:
                placeholder_lookup = build_placeholder_source_lookup(
                    spec_master_csv=spec_master_csv,
                    model=file_row.model,
                    region=file_row.region,
                    lang=lang,
                )
                placeholder_lookup_cache[cache_key] = placeholder_lookup
        old_entries = _annotate_field_entries(
            extract_field_entries(old_text),
            spec_lookup=spec_lookup,
            placeholder_lookup=placeholder_lookup,
        )
        new_entries = _annotate_field_entries(
            extract_field_entries(new_text),
            spec_lookup=spec_lookup,
            placeholder_lookup=placeholder_lookup,
        )

        matched_old: set[int] = set()
        matched_new: set[int] = set()

        def append_pair(old_index: int | None, new_index: int | None) -> None:
            if old_index is not None:
                matched_old.add(old_index)
            if new_index is not None:
                matched_new.add(new_index)
            row = _build_field_diff_row(
                file_row=file_row,
                old_entry=old_entries[old_index] if old_index is not None else None,
                new_entry=new_entries[new_index] if new_index is not None else None,
            )
            if row is not None:
                rows.append(row)

        old_by_key: dict[tuple[str, str], list[int]] = {}
        new_by_key: dict[tuple[str, str], list[int]] = {}
        for index, entry in enumerate(old_entries):
            old_by_key.setdefault((entry.section_title, entry.field_key), []).append(index)
        for index, entry in enumerate(new_entries):
            new_by_key.setdefault((entry.section_title, entry.field_key), []).append(index)

        for key in sorted(set(old_by_key) | set(new_by_key)):
            old_indexes = old_by_key.get(key, [])
            new_indexes = new_by_key.get(key, [])
            while old_indexes and new_indexes:
                append_pair(old_indexes.pop(0), new_indexes.pop(0))

        old_by_source: dict[tuple[str, str], list[int]] = {}
        new_by_source: dict[tuple[str, str], list[int]] = {}
        for index, entry in enumerate(old_entries):
            if index in matched_old or not entry.source_row_key:
                continue
            old_by_source.setdefault((entry.section_title, entry.source_row_key), []).append(index)
        for index, entry in enumerate(new_entries):
            if index in matched_new or not entry.source_row_key:
                continue
            new_by_source.setdefault((entry.section_title, entry.source_row_key), []).append(index)

        for key in sorted(set(old_by_source) & set(new_by_source)):
            old_indexes = old_by_source.get(key, [])
            new_indexes = new_by_source.get(key, [])
            while old_indexes and new_indexes:
                append_pair(old_indexes.pop(0), new_indexes.pop(0))

        section_names = sorted(
            {
                entry.section_title
                for index, entry in enumerate(old_entries)
                if index not in matched_old
            }
            | {
                entry.section_title
                for index, entry in enumerate(new_entries)
                if index not in matched_new
            }
        )
        for section_title in section_names:
            old_indexes = [
                index
                for index, entry in enumerate(old_entries)
                if index not in matched_old and entry.section_title == section_title
            ]
            new_indexes = [
                index
                for index, entry in enumerate(new_entries)
                if index not in matched_new and entry.section_title == section_title
            ]
            if not old_indexes or len(old_indexes) != len(new_indexes):
                continue
            for old_index, new_index in zip(old_indexes, new_indexes):
                append_pair(old_index, new_index)

        for index, _entry in enumerate(old_entries):
            if index not in matched_old:
                append_pair(index, None)
        for index, _entry in enumerate(new_entries):
            if index not in matched_new:
                append_pair(None, index)
    return rows


def _safe_int(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def collect_page_diff_rows(file_rows: list[DiffRow], field_rows: list[FieldDiffRow]) -> list[PageDiffRow]:
    field_counts: dict[tuple[str, str, str, str, str, str], int] = {}
    for row in field_rows:
        key = (row.tracked_root, row.model, row.region, row.artifact, row.section, row.page_key)
        field_counts[key] = field_counts.get(key, 0) + 1

    grouped: dict[tuple[str, str, str, str, str, str], list[DiffRow]] = {}
    for row in file_rows:
        key = (row.tracked_root, row.model, row.region, row.artifact, row.section, row.page_key)
        grouped.setdefault(key, []).append(row)

    pages: list[PageDiffRow] = []
    for key in sorted(grouped):
        group = grouped[key]
        change_types = ",".join(sorted({row.change_type for row in group}))
        relative_paths = "; ".join(sorted(row.relative_path for row in group))
        pages.append(
            PageDiffRow(
                tracked_root=key[0],
                model=key[1],
                region=key[2],
                artifact=key[3],
                section=key[4],
                page_key=key[5],
                file_count=str(len(group)),
                change_types=change_types,
                insertions=str(sum(_safe_int(row.insertions) for row in group)),
                deletions=str(sum(_safe_int(row.deletions) for row in group)),
                fields_changed=str(field_counts.get(key, 0)),
                relative_paths=relative_paths,
                from_ref=group[0].from_ref,
                to_ref=group[0].to_ref,
            )
        )
    return pages
