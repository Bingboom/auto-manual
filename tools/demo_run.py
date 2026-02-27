#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HB-Docs Demo v2.0 - One-click demo runner

Runs:
Step 1: Build v1.0 (all)
Step 2: Modify GLOBAL content (scope=ALL), bump revision, Build v1.1
Step 3: Modify SKU-A only content, bump revision, Build v1.2
Step 4: Compare v1.0 -> v1.2 (xlsx + summary)

You can rerun safely if you use new version numbers.
"""

from __future__ import annotations
from pathlib import Path
import csv
import datetime as dt
import subprocess
import sys
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
DEMO_DATA = ROOT / "demo_data"
CONTENT = DEMO_DATA / "content_blocks.csv"

def read_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        rows = [row for row in r]
    return rows

def write_rows(path: Path, rows: List[Dict[str, str]]) -> None:
    if not rows:
        raise ValueError("No rows to write")
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)

def bump_revision(row: Dict[str, str], note: str, by: str = "Tom") -> None:
    rid = row.get("revision_id", "").strip()
    try:
        n = int(rid) if rid else 0
    except:
        n = 0
    row["revision_id"] = str(n + 1)
    row["revision_note"] = note
    row["updated_by"] = by
    row["updated_at"] = dt.date.today().isoformat()

def main() -> int:
    # Version plan (feel free to change)
    v1 = "1.0"
    v2 = "1.1"
    v3 = "1.2"

    build_py = ROOT / "tools" / "build.py"
    compare_py = ROOT / "tools" / "compare.py"

    print("\n=== Step 1: Build v1.0 (initial) ===")
    subprocess.run([sys.executable, str(build_py), "--all", "--version", v1], check=True)

    print("\n=== Step 2: Modify GLOBAL content + Build v1.1 ===")
    rows = read_rows(CONTENT)

    # 修改 ALL scope 的 warning（你可以换成你想演示的 content_id）
    target_global = "warning_all_01"
    found = False
    for r in rows:
        if r.get("content_id") == target_global:
            # 只改中文示例（你也可以改英文）
            r["text_zh"] = "警告：必须使用原装电源线，禁止任何自行改装。"
            bump_revision(r, note="update global warning wording", by="Tom")
            found = True
            break
    if not found:
        raise SystemExit(f"Cannot find content_id={target_global}")

    write_rows(CONTENT, rows)
    subprocess.run([sys.executable, str(build_py), "--all", "--version", v2, "--compare-from", v1], check=True)

    print("\n=== Step 3: Modify SKU-A only content + Build v1.2 ===")
    rows = read_rows(CONTENT)

    target_sku_a = "sku_a_only_note"
    found = False
    for r in rows:
        if r.get("content_id") == target_sku_a:
            r["text_en"] = "SKU-A only: This model supports AC output {{param_voltage}} (UPDATED)."
            bump_revision(r, note="update SKU-A only note", by="Tom")
            found = True
            break
    if not found:
        raise SystemExit(f"Cannot find content_id={target_sku_a}")

    write_rows(CONTENT, rows)
    subprocess.run([sys.executable, str(build_py), "--all", "--version", v3, "--compare-from", v2], check=True)

    print("\n=== Step 4: Compare v1.0 -> v1.2 ===")
    out_xlsx = ROOT / "output" / f"compare_v{v1}_to_v{v3}.xlsx"
    subprocess.run([sys.executable, str(compare_py), "--from", v1, "--to", v3, "--out", str(out_xlsx)], check=True)

    # Add a demo readme
    demo_readme = ROOT / "output" / "DEMO_README.txt"
    demo_readme.write_text(
        "\n".join([
            "HB-Docs Demo v2.0 Outputs",
            "",
            f"- Build outputs: output/<SKU>/vX.Y/<lang>/",
            f"- Compare report: {out_xlsx.name}",
            f"- Compare summary: compare_summary_v{v1}_to_v{v3}.txt",
            "",
            "Suggested talk track:",
            "1) Show v1.0 outputs (4 folders)",
            "2) Show v1.1 revision_log: global warning changed -> all outputs reflect change",
            "3) Show v1.2 revision_log: SKU-A only note changed -> only SKU-A affected",
            "4) Open compare.xlsx: list of changes by scope_class / sku / lang",
        ]) + "\n",
        encoding="utf-8",
    )

    print(f"\n[OK] Demo finished. See: {demo_readme}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())