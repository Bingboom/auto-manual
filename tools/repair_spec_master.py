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
    SpecMasterAppliedRepair,
    read_spec_master_rows,
    repair_known_spec_master_values,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        "repair Spec_Master section names, labels, and template values"
    )
    parser.add_argument(
        "--csv",
        default="data/phase1/Spec_Master.csv",
        help="path to source Spec_Master.csv",
    )
    parser.add_argument(
        "--out",
        default="reports/spec_master/Spec_Master.repaired.csv",
        help="path for repaired CSV output",
    )
    parser.add_argument(
        "--report",
        default="reports/spec_master/Spec_Master.repairs.csv",
        help="path for repair detail CSV output",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="also write repaired rows back to the source CSV",
    )
    return parser.parse_args()


def resolve_path(raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else (ROOT / path)


def write_rows_csv(path: Path, rows: tuple[dict[str, str], ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [key for key in rows[0].keys() if key != "__line__"] if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: value for key, value in row.items() if key != "__line__"})


def write_repairs_csv(path: Path, repairs: tuple[SpecMasterAppliedRepair, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["line", "model", "region", "row_key", "column", "old_value", "new_value"],
        )
        writer.writeheader()
        for repair in repairs:
            writer.writerow(
                {
                    "line": repair.line,
                    "model": repair.model or "",
                    "region": repair.region or "",
                    "row_key": repair.row_key or "",
                    "column": repair.column,
                    "old_value": repair.old_value,
                    "new_value": repair.new_value,
                }
            )


def main() -> None:
    args = parse_args()
    csv_path = resolve_path(args.csv)
    out_path = resolve_path(args.out)
    report_path = resolve_path(args.report)

    rows = read_spec_master_rows(csv_path)
    result = repair_known_spec_master_values(rows)

    write_rows_csv(out_path, result.repaired_rows)
    write_repairs_csv(report_path, result.applied_repairs)
    if args.in_place:
        write_rows_csv(csv_path, result.repaired_rows)

    print(f"[repair_spec_master] Wrote: {out_path}")
    print(f"[repair_spec_master] Wrote: {report_path}")
    if args.in_place:
        print(f"[repair_spec_master] Updated source: {csv_path}")
    print(f"[repair_spec_master] Applied repairs: {len(result.applied_repairs)}")
    print(f"[repair_spec_master] Removed duplicates: {len(result.removed_duplicate_lines)}")


if __name__ == "__main__":
    main()
