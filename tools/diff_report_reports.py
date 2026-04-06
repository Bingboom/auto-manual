from __future__ import annotations

from pathlib import Path

from tools.diff_report_fields import collect_field_diff_rows, collect_page_diff_rows
from tools.diff_report_git import build_report_base_name, collect_diff_rows, detect_initial_baseline
from tools.diff_report_models import DiffRow, GeneratedReports
from tools.diff_report_render import write_csv_report, write_html_report, write_index_report


def generate_diff_report(
    *,
    repo_root: Path,
    tracked_root: Path,
    from_ref: str,
    to_ref: str,
    output_dir: Path,
    config_path: Path | None = None,
    data_root: str | None = None,
    ignore_initial_adds: bool = True,
) -> tuple[Path, Path]:
    raw_file_rows = collect_diff_rows(
        repo_root=repo_root,
        tracked_root=tracked_root,
        from_ref=from_ref,
        to_ref=to_ref,
    )
    is_initial_baseline = detect_initial_baseline(
        repo_root=repo_root,
        tracked_root=tracked_root,
        from_ref=from_ref,
        to_ref=to_ref,
        file_rows=raw_file_rows,
    )
    notices: list[str] = []
    if is_initial_baseline:
        notices.append(
            "Initial baseline detected for this tracked root. All Added rows are expected because the subtree did not exist at the from-ref."
        )
    if is_initial_baseline and ignore_initial_adds:
        notices.append(
            "Initial Added rows were excluded by default. Pass --include-initial-adds to keep them."
        )
        file_rows: list[DiffRow] = []
    else:
        file_rows = raw_file_rows

    field_rows = collect_field_diff_rows(
        repo_root=repo_root,
        file_rows=file_rows,
        config_path=config_path,
        data_root=data_root,
    )
    page_rows = collect_page_diff_rows(file_rows, field_rows)

    base_name = build_report_base_name(tracked_root, from_ref, to_ref)
    reports = GeneratedReports(
        index_html=output_dir / f"{base_name}_index.html",
        files_csv=output_dir / f"{base_name}_files.csv",
        files_html=output_dir / f"{base_name}_files.html",
        pages_csv=output_dir / f"{base_name}_pages.csv",
        pages_html=output_dir / f"{base_name}_pages.html",
        fields_csv=output_dir / f"{base_name}_fields.csv",
        fields_html=output_dir / f"{base_name}_fields.html",
        legacy_csv=output_dir / f"{base_name}.csv",
        legacy_html=output_dir / f"{base_name}.html",
    )

    file_headers = [
        "tracked_root",
        "model",
        "region",
        "artifact",
        "section",
        "page_key",
        "file_name",
        "relative_path",
        "change_type",
        "insertions",
        "deletions",
        "old_path",
        "new_path",
        "from_ref",
        "to_ref",
    ]
    page_headers = [
        "tracked_root",
        "model",
        "region",
        "artifact",
        "section",
        "page_key",
        "file_count",
        "change_types",
        "insertions",
        "deletions",
        "fields_changed",
        "relative_paths",
        "from_ref",
        "to_ref",
    ]
    field_headers = [
        "tracked_root",
        "model",
        "region",
        "artifact",
        "section",
        "page_key",
        "file_name",
        "relative_path",
        "section_title",
        "field_key",
        "change_type",
        "old_value",
        "new_value",
        "source_section_key",
        "source_row_key",
        "source_line_order",
        "source_csv_line",
        "from_ref",
        "to_ref",
    ]

    write_csv_report(file_rows, reports.files_csv, file_headers)
    write_csv_report(file_rows, reports.legacy_csv, file_headers)
    write_csv_report(page_rows, reports.pages_csv, page_headers)
    write_csv_report(field_rows, reports.fields_csv, field_headers)

    write_html_report(
        file_rows,
        reports.files_html,
        title="RST Diff Report - Files",
        headers=file_headers,
        summary_cards=[
            ("files", str(len(file_rows))),
            ("added", str(sum(1 for row in file_rows if row.change_type == "A"))),
            ("modified", str(sum(1 for row in file_rows if row.change_type == "M"))),
            ("deleted", str(sum(1 for row in file_rows if row.change_type == "D"))),
            ("renamed", str(sum(1 for row in file_rows if row.change_type == "R"))),
        ],
        from_ref=from_ref,
        to_ref=to_ref,
        filter_columns=["model", "region", "section", "change_type"],
        enable_text_search=True,
        notices=notices,
    )
    write_html_report(
        file_rows,
        reports.legacy_html,
        title="RST Diff Report - Files",
        headers=file_headers,
        summary_cards=[
            ("files", str(len(file_rows))),
            ("added", str(sum(1 for row in file_rows if row.change_type == "A"))),
            ("modified", str(sum(1 for row in file_rows if row.change_type == "M"))),
            ("deleted", str(sum(1 for row in file_rows if row.change_type == "D"))),
            ("renamed", str(sum(1 for row in file_rows if row.change_type == "R"))),
        ],
        from_ref=from_ref,
        to_ref=to_ref,
        filter_columns=["model", "region", "section", "change_type"],
        enable_text_search=True,
        notices=notices,
    )
    write_html_report(
        page_rows,
        reports.pages_html,
        title="RST Diff Report - Pages",
        headers=page_headers,
        summary_cards=[
            ("pages", str(len(page_rows))),
            ("files touched", str(len(file_rows))),
            ("field changes", str(len(field_rows))),
        ],
        from_ref=from_ref,
        to_ref=to_ref,
        filter_columns=["model", "region", "page_key", "change_types"],
        enable_text_search=True,
        notices=notices,
    )
    write_html_report(
        field_rows,
        reports.fields_html,
        title="RST Diff Report - Fields",
        headers=field_headers,
        summary_cards=[
            ("field changes", str(len(field_rows))),
            ("added", str(sum(1 for row in field_rows if row.change_type == "A"))),
            ("modified", str(sum(1 for row in field_rows if row.change_type == "M"))),
            ("deleted", str(sum(1 for row in field_rows if row.change_type == "D"))),
        ],
        from_ref=from_ref,
        to_ref=to_ref,
        filter_columns=["model", "region", "page_key", "source_row_key", "change_type"],
        enable_text_search=True,
        notices=notices,
    )
    write_index_report(
        reports=reports,
        file_rows=file_rows,
        page_rows=page_rows,
        field_rows=field_rows,
        html_path=reports.index_html,
        tracked_root=tracked_root,
        from_ref=from_ref,
        to_ref=to_ref,
        notices=notices,
    )
    return reports.legacy_csv, reports.legacy_html
