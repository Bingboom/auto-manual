#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import csv
from collections import Counter
import sys
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.utils.spec_master import normalize_spec_master_csv  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser("normalize Spec_Master.csv into derived outputs")
    parser.add_argument(
        "--csv",
        default="data/phase1/Spec_Master.csv",
        help="path to Spec_Master.csv",
    )
    parser.add_argument(
        "--out-dir",
        default="reports/spec_master",
        help="directory for generated normalized outputs",
    )
    return parser.parse_args()


def resolve_path(raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else (ROOT / path)


def _ordered_fieldnames(rows: tuple[dict[str, str], ...]) -> list[str]:
    if not rows:
        return []
    base_fields = [field for field in rows[0].keys()]
    return base_fields


def write_csv(
    path: Path,
    rows: tuple[dict[str, str], ...],
    *,
    fieldnames: list[str] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered_fieldnames = fieldnames or _ordered_fieldnames(rows)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ordered_fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    args = parse_args()
    csv_path = resolve_path(args.csv)
    out_dir = resolve_path(args.out_dir)

    result = normalize_spec_master_csv(csv_path)

    normalized_path = out_dir / "Spec_Master.normalized.csv"
    anomalies_path = out_dir / "Spec_Master.anomalies.csv"
    fieldnames = _ordered_fieldnames(result.normalized_rows)
    write_csv(normalized_path, result.normalized_rows, fieldnames=fieldnames)
    write_csv(anomalies_path, result.anomaly_rows, fieldnames=fieldnames)

    flag_counter = Counter()
    for row in result.anomaly_rows:
        for flag in (row.get("Review_flags") or "").split(";"):
            text = flag.strip()
            if text:
                flag_counter[text] += 1

    print(f"[normalize_spec_master] Wrote: {normalized_path}")
    print(f"[normalize_spec_master] Wrote: {anomalies_path}")
    print(
        "[normalize_spec_master] Summary: "
        f"normalized_rows={len(result.normalized_rows)}, anomalies={len(result.anomaly_rows)}"
    )
    for code, count in sorted(flag_counter.items()):
        print(f"[normalize_spec_master] Flag {code}: {count}")


if __name__ == "__main__":
    main()
