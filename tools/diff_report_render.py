from __future__ import annotations

import csv
import html
from dataclasses import asdict
from pathlib import Path
from urllib.parse import urlencode

from tools.diff_report_git import sanitize_token
from tools.diff_report_models import DiffRow, FieldDiffRow, GeneratedReports, PageDiffRow


def write_csv_report(rows: list[object], csv_path: Path, fieldnames: list[str]) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: asdict(row).get(name, "") for name in fieldnames})


def write_html_report(
    rows: list[object],
    html_path: Path,
    *,
    title: str,
    headers: list[str],
    summary_cards: list[tuple[str, str]],
    from_ref: str,
    to_ref: str,
    filter_columns: list[str] | None = None,
    enable_text_search: bool = False,
    notices: list[str] | None = None,
) -> None:
    html_path.parent.mkdir(parents=True, exist_ok=True)
    table_head = "".join(f"<th>{html.escape(col)}</th>" for col in headers)
    table_rows = []
    active_filter_columns = filter_columns or []
    filter_tokens = {column: sanitize_token(column).replace(".", "_") for column in active_filter_columns}
    for row in rows:
        row_dict = asdict(row)
        attrs: list[str] = ['data-report-row="1"']
        if enable_text_search:
            search_text = " ".join(str(row_dict.get(col, "")) for col in headers).lower()
            attrs.append(f'data-search="{html.escape(search_text, quote=True)}"')
        for column, token in filter_tokens.items():
            attrs.append(f'data-filter-{token}="{html.escape(str(row_dict.get(column, "")), quote=True)}"')
        cols = "".join(f"<td>{html.escape(str(row_dict.get(col, '')))}</td>" for col in headers)
        table_rows.append(f"<tr {' '.join(attrs)}>{cols}</tr>")

    cards_html = "".join(
        f'<div class="card"><strong>{html.escape(value)}</strong><div class="muted">{html.escape(label)}</div></div>'
        for label, value in summary_cards
    )
    filter_controls: list[str] = []
    if enable_text_search:
        filter_controls.append(
            '<label class="filter-item"><span>Search</span><input id="filter-search" type="search" placeholder="Search rows" /></label>'
        )
    for column in active_filter_columns:
        token = filter_tokens[column]
        values = sorted(
            {
                str(asdict(row).get(column, "")).strip()
                for row in rows
                if str(asdict(row).get(column, "")).strip()
            }
        )
        options = ['<option value="">All</option>'] + [
            f'<option value="{html.escape(value, quote=True)}">{html.escape(value)}</option>' for value in values
        ]
        filter_controls.append(
            f'<label class="filter-item"><span>{html.escape(column)}</span><select id="filter-{token}" data-filter-token="{token}">{"".join(options)}</select></label>'
        )
    filter_bar_html = ""
    filter_script = ""
    notice_html = ""
    notice_items = [item.strip() for item in (notices or []) if item.strip()]
    if notice_items:
        notice_html = "\n".join(
            [
                '  <div class="notices">',
                *[f'    <div class="notice">{html.escape(item)}</div>' for item in notice_items],
                "  </div>",
            ]
        )
    if filter_controls:
        filter_bar_html = "\n".join(
            [
                '  <div class="filters">',
                '    <div class="filters-grid">',
                *[f"      {item}" for item in filter_controls],
                "    </div>",
                '    <div class="muted" id="filter-result-count"></div>',
                "  </div>",
            ]
        )
        filter_script = "\n".join(
            [
                "  <script>",
                "    (function () {",
                "      const rows = Array.from(document.querySelectorAll('tr[data-report-row=\"1\"]'));",
                "      const searchInput = document.getElementById('filter-search');",
                "      const selects = Array.from(document.querySelectorAll('select[data-filter-token]'));",
                "      const resultCount = document.getElementById('filter-result-count');",
                "      const params = new URLSearchParams(window.location.search);",
                "      function syncQueryString() {",
                "        const next = new URLSearchParams();",
                "        if (searchInput && searchInput.value.trim()) {",
                "          next.set('search', searchInput.value.trim());",
                "        }",
                "        selects.forEach((select) => {",
                "          const token = select.getAttribute('data-filter-token');",
                "          if (token && select.value) {",
                "            next.set(token, select.value);",
                "          }",
                "        });",
                "        const query = next.toString();",
                "        const target = `${window.location.pathname}${query ? '?' + query : ''}${window.location.hash}`;",
                "        window.history.replaceState(null, '', target);",
                "      }",
                "      function applyFilters() {",
                "        const search = searchInput ? searchInput.value.trim().toLowerCase() : '';",
                "        let visible = 0;",
                "        rows.forEach((row) => {",
                "          let ok = true;",
                "          if (search) {",
                "            const haystack = (row.getAttribute('data-search') || '').toLowerCase();",
                "            ok = haystack.includes(search);",
                "          }",
                "          if (ok) {",
                "            selects.forEach((select) => {",
                "              const token = select.getAttribute('data-filter-token');",
                "              const wanted = select.value;",
                "              if (!wanted) {",
                "                return;",
                "              }",
                "              const actual = row.getAttribute('data-filter-' + token) || '';",
                "              if (actual !== wanted) {",
                "                ok = false;",
                "              }",
                "            });",
                "          }",
                "          row.hidden = !ok;",
                "          if (ok) {",
                "            visible += 1;",
                "          }",
                "        });",
                "        if (resultCount) {",
                "          resultCount.textContent = `${visible} / ${rows.length} rows visible`;",
                "        }",
                "      }",
                "      if (searchInput) {",
                "        const initialSearch = params.get('search') || '';",
                "        if (initialSearch) {",
                "          searchInput.value = initialSearch;",
                "        }",
                "      }",
                "      selects.forEach((select) => {",
                "        const token = select.getAttribute('data-filter-token');",
                "        if (!token) {",
                "          return;",
                "        }",
                "        const wanted = params.get(token);",
                "        if (!wanted) {",
                "          return;",
                "        }",
                "        const option = Array.from(select.options).find((item) => item.value === wanted);",
                "        if (option) {",
                "          select.value = wanted;",
                "        }",
                "      });",
                "      if (searchInput) {",
                "        searchInput.addEventListener('input', () => { syncQueryString(); applyFilters(); });",
                "      }",
                "      selects.forEach((select) => select.addEventListener('change', () => { syncQueryString(); applyFilters(); }));",
                "      applyFilters();",
                "    }());",
                "  </script>",
            ]
        )
    html_text = "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8" />',
            f"  <title>{html.escape(title)}</title>",
            "  <style>",
            "    body { font-family: Segoe UI, Arial, sans-serif; margin: 24px; }",
            "    table { border-collapse: collapse; width: 100%; font-size: 13px; }",
            "    th, td { border: 1px solid #d0d7de; padding: 6px 8px; text-align: left; vertical-align: top; }",
            "    th { background: #f6f8fa; position: sticky; top: 0; }",
            "    .summary { display: flex; gap: 16px; margin: 16px 0; flex-wrap: wrap; }",
            "    .card { border: 1px solid #d0d7de; border-radius: 8px; padding: 10px 12px; min-width: 120px; }",
            "    .notices { display: grid; gap: 10px; margin: 16px 0; }",
            "    .notice { border: 1px solid #d8b566; background: #fff8c5; border-radius: 8px; padding: 12px 14px; color: #5c4700; }",
            "    .filters { border: 1px solid #d0d7de; border-radius: 8px; padding: 12px; margin: 16px 0; background: #f6f8fa; }",
            "    .filters-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }",
            "    .filter-item { display: flex; flex-direction: column; gap: 6px; font-size: 12px; }",
            "    .filter-item input, .filter-item select { border: 1px solid #d0d7de; border-radius: 6px; padding: 8px 10px; font-size: 13px; background: #fff; }",
            "    .muted { color: #57606a; }",
            "  </style>",
            "</head>",
            "<body>",
            f"  <h1>{html.escape(title)}</h1>",
            f"  <p class=\"muted\">{html.escape(from_ref)} -> {html.escape(to_ref)}</p>",
            f"  <div class=\"summary\">{cards_html}</div>",
            notice_html,
            filter_bar_html,
            "  <table>",
            f"    <thead><tr>{table_head}</tr></thead>",
            f"    <tbody>{''.join(table_rows)}</tbody>",
            "  </table>",
            filter_script,
            "</body>",
            "</html>",
        ]
    )
    html_path.write_text(html_text, encoding="utf-8")


def _build_relative_report_link(path: Path, filters: dict[str, str] | None = None) -> str:
    query = ""
    if filters:
        clean_filters = {key: value for key, value in filters.items() if value}
        if clean_filters:
            query = "?" + urlencode(clean_filters)
    return f"{path.name}{query}"


def write_index_report(
    *,
    reports: GeneratedReports,
    file_rows: list[DiffRow],
    page_rows: list[PageDiffRow],
    field_rows: list[FieldDiffRow],
    html_path: Path,
    tracked_root: Path,
    from_ref: str,
    to_ref: str,
    notices: list[str] | None = None,
) -> None:
    html_path.parent.mkdir(parents=True, exist_ok=True)

    targets: dict[tuple[str, str], dict[str, int]] = {}
    for row in file_rows:
        key = (row.model, row.region)
        target = targets.setdefault(key, {"files": 0, "pages": 0, "fields": 0})
        target["files"] += 1
    for row in page_rows:
        key = (row.model, row.region)
        target = targets.setdefault(key, {"files": 0, "pages": 0, "fields": 0})
        target["pages"] += 1
    for row in field_rows:
        key = (row.model, row.region)
        target = targets.setdefault(key, {"files": 0, "pages": 0, "fields": 0})
        target["fields"] += 1

    overview_cards = [
        ("tracked root", tracked_root.as_posix()),
        ("targets", str(len(targets))),
        ("files", str(len(file_rows))),
        ("pages", str(len(page_rows))),
        ("field changes", str(len(field_rows))),
    ]
    overview_html = "".join(
        f'<div class="card"><strong>{html.escape(value)}</strong><div class="muted">{html.escape(label)}</div></div>'
        for label, value in overview_cards
    )
    notice_items = [item.strip() for item in (notices or []) if item.strip()]
    notice_html = ""
    if notice_items:
        notice_html = "\n".join(
            [
                '  <div class="notices">',
                *[f'    <div class="notice">{html.escape(item)}</div>' for item in notice_items],
                "  </div>",
            ]
        )

    report_cards = [
        ("Files", "File-level diff table with insertions and deletions.", reports.files_html.name, len(file_rows)),
        ("Pages", "Page-level rollup with fields_changed counts.", reports.pages_html.name, len(page_rows)),
        ("Fields", "Structured field diff with source_row_key back-mapping.", reports.fields_html.name, len(field_rows)),
    ]
    report_links_html = "".join(
        [
            "\n".join(
                [
                    '<a class="nav-card" href="{href}">'.format(href=html.escape(path)),
                    f'  <div class="nav-title">{html.escape(title)}</div>',
                    f'  <div class="muted">{html.escape(description)}</div>',
                    f'  <div class="nav-meta">{count} rows</div>',
                    "</a>",
                ]
            )
            for title, description, path, count in report_cards
        ]
    )

    target_rows: list[str] = []
    for model, region in sorted(targets):
        stats = targets[(model, region)]
        filters = {"model": model, "region": region}
        target_rows.append(
            "\n".join(
                [
                    "<tr>",
                    f"  <td><strong>{html.escape(model)}/{html.escape(region)}</strong></td>",
                    f"  <td>{stats['files']}</td>",
                    f"  <td>{stats['pages']}</td>",
                    f"  <td>{stats['fields']}</td>",
                    "  <td>",
                    f'    <a href="{html.escape(_build_relative_report_link(reports.files_html, filters))}">files</a> | ',
                    f'    <a href="{html.escape(_build_relative_report_link(reports.pages_html, filters))}">pages</a> | ',
                    f'    <a href="{html.escape(_build_relative_report_link(reports.fields_html, filters))}">fields</a>',
                    "  </td>",
                    "</tr>",
                ]
            )
        )

    html_text = "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8" />',
            "  <title>RST Diff Report - Index</title>",
            "  <style>",
            "    body { font-family: Segoe UI, Arial, sans-serif; margin: 24px; }",
            "    a { color: #0969da; text-decoration: none; }",
            "    a:hover { text-decoration: underline; }",
            "    .summary { display: flex; gap: 16px; margin: 16px 0 24px; flex-wrap: wrap; }",
            "    .card { border: 1px solid #d0d7de; border-radius: 8px; padding: 10px 12px; min-width: 140px; background: #fff; }",
            "    .notices { display: grid; gap: 10px; margin: 16px 0; }",
            "    .notice { border: 1px solid #d8b566; background: #fff8c5; border-radius: 8px; padding: 12px 14px; color: #5c4700; }",
            "    .nav-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin: 16px 0 24px; }",
            "    .nav-card { display: block; border: 1px solid #d0d7de; border-radius: 10px; padding: 14px; background: #f6f8fa; }",
            "    .nav-title { font-weight: 600; margin-bottom: 6px; }",
            "    .nav-meta { margin-top: 8px; color: #24292f; font-size: 12px; }",
            "    table { border-collapse: collapse; width: 100%; font-size: 13px; margin-top: 16px; }",
            "    th, td { border: 1px solid #d0d7de; padding: 8px 10px; text-align: left; vertical-align: top; }",
            "    th { background: #f6f8fa; }",
            "    .muted { color: #57606a; }",
            "  </style>",
            "</head>",
            "<body>",
            "  <h1>RST Diff Report - Index</h1>",
            f"  <p class=\"muted\">{html.escape(from_ref)} -> {html.escape(to_ref)}</p>",
            f"  <div class=\"summary\">{overview_html}</div>",
            notice_html,
            "  <h2>Report Views</h2>",
            "  <div class=\"nav-grid\">",
            report_links_html,
            "  </div>",
            "  <h2>Jump by Target</h2>",
            "  <p class=\"muted\">These links open the report pages with model/region filters pre-applied.</p>",
            "  <table>",
            "    <thead><tr><th>Target</th><th>Files</th><th>Pages</th><th>Field Changes</th><th>Links</th></tr></thead>",
            f"    <tbody>{''.join(target_rows)}</tbody>",
            "  </table>",
            "</body>",
            "</html>",
        ]
    )
    html_path.write_text(html_text, encoding="utf-8")
