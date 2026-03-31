#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.utils.spec_master import (  # noqa: E402
    build_row_label_row_key_mapping_markdown,
    build_row_label_row_key_mapping_rows,
    read_spec_master_rows,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser("export Spec_Master Row_label_source to Row_key mapping")
    parser.add_argument(
        "--csv",
        default="data/phase1/Spec_Master.csv",
        help="path to source Spec_Master.csv",
    )
    parser.add_argument(
        "--out",
        default="reports/spec_master/row_key_mapping.csv",
        help="path for generated mapping CSV",
    )
    parser.add_argument(
        "--md-out",
        default="reports/spec_master/row_key_mapping.md",
        help="path for generated mapping Markdown",
    )
    return parser.parse_args()


def resolve_path(raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else (ROOT / path)


def write_mapping_csv(path: Path, rows: tuple[dict[str, str], ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
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
    mapping_rows = build_row_label_row_key_mapping_rows(rows)
    markdown = build_row_label_row_key_mapping_markdown(mapping_rows)
    write_mapping_csv(out_path, mapping_rows)
    write_markdown(md_out_path, markdown)

    print(f"[export_spec_master_row_key_mapping] Wrote: {out_path}")
    print(f"[export_spec_master_row_key_mapping] Wrote: {md_out_path}")
    print(f"[export_spec_master_row_key_mapping] Rows: {len(mapping_rows)}")


if __name__ == "__main__":
    main()
