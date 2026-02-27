#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diff_safety.py
Stage-1 ChangeLog generator for safety_items.csv WITHOUT changing CSV schema.

Usage:
  python tools/diff_safety.py snapshots/safety_v1.csv snapshots/safety_v2.csv output/ChangeLog_v1_to_v2.xlsx

Rules:
- content key: KEY = f"{part}:{int(float(id))}" when id is numeric and part is not empty
- layout key:  KEY = f"layout:{id}" when id is non-numeric (density/profile/lang keys)
- ignore: rows with empty id
- compare per language field: text_en/text_fr/text_es (if column missing, treated as empty)
- output: one row per (key, language, change)
"""
from __future__ import annotations
from pathlib import Path
import sys
import pandas as pd

LANG_COLS = ["text_en", "text_fr", "text_es"]

def is_number(x: str) -> bool:
    try:
        float(str(x).strip())
        return True
    except Exception:
        return False

def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str).fillna("")
    for c in ["id", "part"]:
        if c not in df.columns:
            df[c] = ""
        df[c] = df[c].astype(str)

    # Ensure language columns exist
    for c in LANG_COLS:
        if c not in df.columns:
            df[c] = ""
        df[c] = df[c].astype(str)

    # Domain
    df["domain"] = df["id"].apply(lambda v: "content" if is_number(v) else "layout")

    # Key
    def make_key(row) -> str:
        rid = str(row["id"]).strip()
        if not rid:
            return ""  # ignored later
        if row["domain"] == "content":
            part = str(row["part"]).strip()
            if not part:
                return ""
            return f"{part}:{int(float(rid))}"
        else:
            return f"layout:{rid}"

    df["key"] = df.apply(make_key, axis=1)
    df = df[df["key"].astype(str).str.strip() != ""].copy()

    # If duplicates exist, keep the first to avoid ambiguity (Stage-1 choice)
    df = df.drop_duplicates(subset=["key"], keep="first")
    return df

def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: python tools/diff_safety.py <old_csv> <new_csv> <out_xlsx>")
        return 2

    old_path = Path(sys.argv[1])
    new_path = Path(sys.argv[2])
    out_path = Path(sys.argv[3])
    out_path.parent.mkdir(parents=True, exist_ok=True)

    old_df = load_csv(old_path)
    new_df = load_csv(new_path)

    merged = old_df.merge(
        new_df,
        on="key",
        how="outer",
        suffixes=("_old", "_new"),
        indicator=True,
    )

    rows = []

    for _, r in merged.iterrows():
        merge_flag = r["_merge"]
        domain = r.get("domain_new", "") or r.get("domain_old", "")
        part   = r.get("part_new", "") or r.get("part_old", "") or "layout"

        if merge_flag == "left_only":
            for col in LANG_COLS:
                rows.append({
                    "change_type": "DEL",
                    "key": r["key"],
                    "domain": domain,
                    "part": part,
                    "language": col.replace("text_", ""),
                    "old_value": r.get(f"{col}_old", ""),
                    "new_value": "",
                })
            continue

        if merge_flag == "right_only":
            for col in LANG_COLS:
                rows.append({
                    "change_type": "ADD",
                    "key": r["key"],
                    "domain": domain,
                    "part": part,
                    "language": col.replace("text_", ""),
                    "old_value": "",
                    "new_value": r.get(f"{col}_new", ""),
                })
            continue

        # both: MOD per language if changed
        for col in LANG_COLS:
            old_val = r.get(f"{col}_old", "")
            new_val = r.get(f"{col}_new", "")
            if old_val != new_val:
                rows.append({
                    "change_type": "MOD",
                    "key": r["key"],
                    "domain": domain,
                    "part": part,
                    "language": col.replace("text_", ""),
                    "old_value": old_val,
                    "new_value": new_val,
                })

    out = pd.DataFrame(rows)

    # Drop empty changes (e.g., ADD but language empty both sides)
    out = out[~((out["old_value"].astype(str).str.strip() == "") &
                (out["new_value"].astype(str).str.strip() == ""))].copy()

    out = out.sort_values(["domain", "part", "key", "language", "change_type"]).reset_index(drop=True)
    out.to_excel(out_path, index=False)
    print(f"[OK] ChangeLog generated -> {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())