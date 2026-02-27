#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HB-Docs Demo v2.0 - compare.py (final)

What it does:
- Compare two snapshot versions (snapshots/vX.Y/) for 2 SKU × 2 Lang
- Diff on materialized text (sku_scope filter + variable injection + language select)
- Normalize text before compare (ignore whitespace/newlines differences)
- Add scope_class for management-friendly reading (GLOBAL / SKU-A_ONLY / SKU-B_ONLY)
- Output:
  1) Excel diff report (xlsx)
  2) Summary text (compare_summary_vX_to_vY.txt)

Usage:
  python tools/compare.py --from 1.0 --to 1.2
  python tools/compare.py --from 1.0 --to 1.2 --out output/compare.xlsx
"""

from __future__ import annotations
from pathlib import Path
import argparse
import csv
import re
from typing import Dict, List, Optional

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = ROOT / "snapshots"

LANG_MAP = {"zh": "text_zh", "en": "text_en"}
SKUS = ["SKU-A", "SKU-B"]
LANGS = ["zh", "en"]
SKU_ALL = "ALL"
VAR_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")


# -----------------------------
# Helpers
# -----------------------------
def normalize_text(s: str) -> str:
    # Collapse all whitespace (space, tabs, newlines) into single spaces
    return " ".join((s or "").split())


def read_csv_dicts(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows: list[dict[str, str]] = []
        for r in reader:
            if r is None:
                continue

            # If a CSV row has extra columns (commas not quoted), DictReader puts them under key None
            if None in r:
                raise ValueError(
                    f"CSV parse error (extra columns). Check quotes/commas in: {path}"
                )

            clean: dict[str, str] = {}
            for k, v in r.items():
                if v is None:
                    clean[k] = ""
                elif isinstance(v, str):
                    clean[k] = v.strip()
                else:
                    clean[k] = ""
            rows.append(clean)
        return rows


def load_variables(vars_csv: Path) -> Dict[str, Dict[str, str]]:
    rows = read_csv_dicts(vars_csv)
    out: Dict[str, Dict[str, str]] = {}
    for r in rows:
        sku = r.get("sku_id", "").strip()
        if not sku:
            continue
        out[sku] = {k: v for k, v in r.items() if k != "sku_id"}
    return out


def load_content(content_csv: Path) -> List[Dict[str, str]]:
    rows = read_csv_dicts(content_csv)
    if not rows:
        raise ValueError("content_blocks.csv is empty")

    required = [
        "content_id",
        "sku_scope",
        "type",
        "text_zh",
        "text_en",
        "revision_id",
        "revision_note",
        "updated_at",
        "updated_by",
    ]
    for c in required:
        if c not in rows[0]:
            raise ValueError(f"Missing column in content_blocks.csv: {c}")

    # Unique content_id
    seen = set()
    for r in rows:
        cid = r.get("content_id", "")
        if not cid:
            raise ValueError("content_id is required for every row")
        if cid in seen:
            raise ValueError(f"content_id duplicated: {cid}")
        seen.add(cid)

    # Column-shift sanity: revision_id should be digits (demo discipline)
    for r in rows:
        rid = r.get("revision_id", "")
        if rid and not rid.isdigit():
            raise ValueError(
                f"CSV column shift detected at content_id={r.get('content_id','')} (revision_id='{rid}')"
            )

    return rows


def in_scope(row: Dict[str, str], sku: str) -> bool:
    scope = (row.get("sku_scope") or "").strip()
    return scope == SKU_ALL or scope == sku


def inject_vars(text: str, vars_map: Dict[str, str]) -> str:
    if not text:
        return ""

    def repl(m: re.Match) -> str:
        key = m.group(1)
        return vars_map.get(key, m.group(0))

    return VAR_PATTERN.sub(repl, text)


def materialize(
    rows: List[Dict[str, str]],
    sku: str,
    lang: str,
    vars_for_sku: Dict[str, str],
) -> Dict[str, Dict[str, str]]:
    """
    Return map: content_id -> record {text_resolved, sku_scope, revision_*}
    """
    text_col = LANG_MAP[lang]
    out: Dict[str, Dict[str, str]] = {}
    for r in rows:
        if not in_scope(r, sku):
            continue
        cid = r["content_id"]
        text = inject_vars(r.get(text_col, ""), vars_for_sku)
        out[cid] = {
            "content_id": cid,
            "sku_scope": r.get("sku_scope", ""),
            "type": r.get("type", ""),
            "text_resolved": text,
            "revision_id": r.get("revision_id", ""),
            "revision_note": r.get("revision_note", ""),
            "updated_at": r.get("updated_at", ""),
            "updated_by": r.get("updated_by", ""),
        }
    return out


def scope_classify(sku_scope: str) -> str:
    s = (sku_scope or "").strip()
    if s == SKU_ALL:
        return "GLOBAL"
    return f"{s}_ONLY"  # e.g., SKU-A_ONLY / SKU-B_ONLY


def diff_maps(
    old_map: Dict[str, Dict[str, str]],
    new_map: Dict[str, Dict[str, str]],
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    all_ids = sorted(set(old_map.keys()) | set(new_map.keys()))

    for cid in all_ids:
        o = old_map.get(cid)
        n = new_map.get(cid)

        if o is None and n is not None:
            sku_scope = n.get("sku_scope", "")
            rows.append(
                {
                    "change_type": "ADD",
                    "content_id": cid,
                    "sku_scope": sku_scope,
                    "scope_class": scope_classify(sku_scope),
                    "old_text": "",
                    "new_text": n.get("text_resolved", ""),
                    "revision_id": n.get("revision_id", ""),
                    "updated_by": n.get("updated_by", ""),
                    "updated_at": n.get("updated_at", ""),
                    "revision_note": n.get("revision_note", ""),
                }
            )
            continue

        if n is None and o is not None:
            sku_scope = o.get("sku_scope", "")
            rows.append(
                {
                    "change_type": "DEL",
                    "content_id": cid,
                    "sku_scope": sku_scope,
                    "scope_class": scope_classify(sku_scope),
                    "old_text": o.get("text_resolved", ""),
                    "new_text": "",
                    "revision_id": o.get("revision_id", ""),
                    "updated_by": o.get("updated_by", ""),
                    "updated_at": o.get("updated_at", ""),
                    "revision_note": o.get("revision_note", ""),
                }
            )
            continue

        assert o is not None and n is not None
        ot = o.get("text_resolved", "")
        nt = n.get("text_resolved", "")

        if normalize_text(ot) != normalize_text(nt):
            sku_scope = n.get("sku_scope", o.get("sku_scope", ""))
            rows.append(
                {
                    "change_type": "MOD",
                    "content_id": cid,
                    "sku_scope": sku_scope,
                    "scope_class": scope_classify(sku_scope),
                    "old_text": ot,
                    "new_text": nt,
                    "revision_id": n.get("revision_id", ""),
                    "updated_by": n.get("updated_by", ""),
                    "updated_at": n.get("updated_at", ""),
                    "revision_note": n.get("revision_note", ""),
                }
            )

    return rows


def write_summary_txt(df: pd.DataFrame, v_from: str, v_to: str, out_dir: Path) -> Path:
    """
    Create a simple compare summary for management reading.
    """
    out_path = out_dir / f"compare_summary_v{v_from}_to_v{v_to}.txt"

    if df.empty:
        text = [
            f"Compare Summary: v{v_from} -> v{v_to}",
            "",
            "Total changes: 0",
        ]
        out_path.write_text("\n".join(text) + "\n", encoding="utf-8")
        return out_path

    total = len(df)
    by_scope = df["scope_class"].value_counts().to_dict()
    by_lang = df["lang"].value_counts().to_dict()
    by_sku = df["sku"].value_counts().to_dict()
    by_type = df["change_type"].value_counts().to_dict()

    lines: List[str] = []
    lines.append(f"Compare Summary: v{v_from} -> v{v_to}")
    lines.append("")
    lines.append(f"Total changes: {total}")
    lines.append("")

    lines.append("By change_type:")
    for k in ["MOD", "ADD", "DEL"]:
        if k in by_type:
            lines.append(f"- {k}: {by_type[k]}")
    lines.append("")

    lines.append("By scope_class:")
    for k in sorted(by_scope.keys()):
        lines.append(f"- {k}: {by_scope[k]}")
    lines.append("")

    lines.append("By SKU:")
    for k in sorted(by_sku.keys()):
        lines.append(f"- {k}: {by_sku[k]}")
    lines.append("")

    lines.append("By language:")
    for k in sorted(by_lang.keys()):
        lines.append(f"- {k}: {by_lang[k]}")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


# -----------------------------
# Main
# -----------------------------
def main() -> int:
    ap = argparse.ArgumentParser("HB-Docs Demo v2.0 compare (final)")
    ap.add_argument("--from", dest="v_from", required=True, help="Base version, e.g. 1.0")
    ap.add_argument("--to", dest="v_to", required=True, help="Target version, e.g. 1.1")
    ap.add_argument(
        "--out",
        dest="out",
        default=None,
        help="Output xlsx path (default: output/compare_vX_to_vY.xlsx)",
    )
    args = ap.parse_args()

    v_from_dir = SNAPSHOT_DIR / f"v{args.v_from}"
    v_to_dir = SNAPSHOT_DIR / f"v{args.v_to}"
    if not v_from_dir.exists():
        raise SystemExit(f"Missing snapshots for version {args.v_from}: {v_from_dir}")
    if not v_to_dir.exists():
        raise SystemExit(f"Missing snapshots for version {args.v_to}: {v_to_dir}")

    old_content = load_content(v_from_dir / "content_blocks.csv")
    new_content = load_content(v_to_dir / "content_blocks.csv")
    old_vars = load_variables(v_from_dir / "product_variables.csv")
    new_vars = load_variables(v_to_dir / "product_variables.csv")

    all_changes: List[Dict[str, str]] = []

    for sku in SKUS:
        for lang in LANGS:
            old_map = materialize(old_content, sku, lang, old_vars.get(sku, {}))
            new_map = materialize(new_content, sku, lang, new_vars.get(sku, {}))
            diffs = diff_maps(old_map, new_map)
            for d in diffs:
                d["sku"] = sku
                d["lang"] = lang
                all_changes.append(d)

    df = pd.DataFrame(all_changes)
    if df.empty:
        df = pd.DataFrame(
            columns=[
                "sku",
                "lang",
                "change_type",
                "scope_class",
                "content_id",
                "sku_scope",
                "old_text",
                "new_text",
                "revision_id",
                "updated_by",
                "updated_at",
                "revision_note",
            ]
        )

    # Sort for readability
    df = df.sort_values(
        ["sku", "lang", "scope_class", "change_type", "content_id"],
        ascending=[True, True, True, True, True],
    ).reset_index(drop=True)

    out_path = Path(args.out) if args.out else (ROOT / "output" / f"compare_v{args.v_from}_to_v{args.v_to}.xlsx")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_excel(out_path, index=False)

    # Write summary txt alongside the xlsx
    summary_path = write_summary_txt(df, args.v_from, args.v_to, out_path.parent)

    print(f"[OK] Compare report -> {out_path}")
    print(f"[OK] Summary -> {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())