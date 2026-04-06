#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.utils.spec_master import (  # noqa: E402
    build_row_label_row_key_mapping_markdown,
    build_row_label_row_key_mapping_rows,
    read_spec_master_rows,
)

ROW_KEY_MAPPING_FIELDNAMES = ("Row_label_source", "Line_order", "Row_key", "Remark")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser("export Spec_Master Row_label_source to Row_key mapping")
    parser.add_argument(
        "--csv",
        default="data/phase1/Spec_Master.csv",
        help="path to source Spec_Master.csv",
    )
    parser.add_argument(
        "--out",
        default="data/phase1/row_key_mapping.csv",
        help="path for generated mapping CSV",
    )
    parser.add_argument(
        "--md-out",
        default="reports/spec_master/row_key_mapping.md",
        help="path for generated mapping Markdown mirror",
    )
    return parser.parse_args()


def resolve_path(raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else (ROOT / path)


def read_existing_mapping_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows: list[dict[str, str]] = []
        for row in reader:
            rows.append(
                {
                    "Row_label_source": (row.get("Row_label_source") or "").strip(),
                    "Line_order": (row.get("Line_order") or "").strip(),
                    "Row_key": (row.get("Row_key") or "").strip(),
                    "Remark": (row.get("Remark") or "").strip(),
                }
            )
        return rows


def write_mapping_csv(path: Path, rows: tuple[dict[str, str], ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ROW_KEY_MAPPING_FIELDNAMES))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    args = parse_args()
    csv_path = resolve_path(args.csv)
    out_path = resolve_path(args.out)
    md_out_path = resolve_path(args.md_out)

    rows = read_spec_master_rows(csv_path)
    existing_mapping_rows = read_existing_mapping_rows(out_path)
    mapping_rows = build_row_label_row_key_mapping_rows(rows, existing_rows=existing_mapping_rows)
    markdown = build_row_label_row_key_mapping_markdown(mapping_rows)
    write_mapping_csv(out_path, mapping_rows)
    write_markdown(md_out_path, markdown)

    print(f"[export_spec_master_row_key_mapping] Wrote: {out_path}")
    print(f"[export_spec_master_row_key_mapping] Wrote: {md_out_path}")
    print(f"[export_spec_master_row_key_mapping] Rows: {len(mapping_rows)}")


if __name__ == "__main__":
    main()
