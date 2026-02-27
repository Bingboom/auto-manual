#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HB-Docs Demo v2.0 - build.py (framework)

Goal: demo Single Source + multi-SKU + multi-lang + revision tracking + versioning

Usage examples:
  python tools/build.py --all --version 1.0
  python tools/build.py --sku SKU-A --lang zh --version 1.1
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import argparse
import csv
import datetime as dt
import json
import re
import subprocess
import sys
from typing import Dict, List, Iterable, Tuple, Optional


# -----------------------------
# Config (demo-level)
# -----------------------------
ROOT = Path(__file__).resolve().parents[1]  # repo root (adjust if needed)

DATA_DIR = ROOT / "demo_data"          # demo csv folder (you can change)
CONTENT_CSV = DATA_DIR / "content_blocks.csv"
VARS_CSV = DATA_DIR / "product_variables.csv"

OUTPUT_DIR = ROOT / "output"           # final outputs
SNAPSHOT_DIR = ROOT / "snapshots"      # optional: store version snapshots (csv copies)


LANG_MAP = {
    "zh": "text_zh",
    "en": "text_en",
}

SKU_ALL = "ALL"

VAR_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")  # {{param_power}}


@dataclass(frozen=True)
class BuildTarget:
    sku: str
    lang: str
    version: str


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser("HB-Docs Demo v2.0 Builder")
    p.add_argument("--sku", choices=["SKU-A", "SKU-B"], help="Target SKU")
    p.add_argument("--lang", choices=["zh", "en"], help="Target language")
    p.add_argument("--version", required=True, help="Version string, e.g. 1.0 / 1.1")
    p.add_argument("--all", action="store_true", help="Build all SKU × LANG")
    p.add_argument("--dry-run", action="store_true", help="Do not call external builders, only generate logs/artifacts")
    return p.parse_args()


# -----------------------------
# CSV loading helpers
# -----------------------------
def read_csv_dicts(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows: list[dict[str, str]] = []
        for r in reader:
            if r is None:
                continue
            # 清洗：把 None 变成 ""，并 strip
            clean: dict[str, str] = {}
            for k, v in r.items():
                if v is None:
                    clean[k] = ""
                elif isinstance(v, str):
                    clean[k] = v.strip()
                else:
                    # 极端情况（不太会发生）：非字符串一律转空
                    clean[k] = ""
            rows.append(clean)
        return rows


def load_variables(vars_csv: Path) -> Dict[str, Dict[str, str]]:
    """
    Returns:
      {
        "SKU-A": {"param_power":"500W", ...},
        "SKU-B": {...}
      }
    """
    rows = read_csv_dicts(vars_csv)
    out: Dict[str, Dict[str, str]] = {}
    for r in rows:
        sku = r.get("sku_id", "").strip()
        if not sku:
            continue
        out[sku] = {k: v for k, v in r.items() if k != "sku_id"}
    return out


def load_content(content_csv: Path) -> List[Dict[str, str]]:
    """
    Each row must include:
      content_id, sku_scope, type, text_zh, text_en, revision_id, revision_note, updated_at, updated_by
    """
    rows = read_csv_dicts(content_csv)
    # minimal validation
    seen = set()
    for r in rows:
        cid = r.get("content_id", "")
        if not cid:
            raise ValueError("content_id is required for every row")
        if cid in seen:
            raise ValueError(f"content_id duplicated: {cid}")
        seen.add(cid)
    return rows


# -----------------------------
# Core: scope filtering + variable injection
# -----------------------------
def in_scope(row: Dict[str, str], sku: str) -> bool:
    scope = (row.get("sku_scope") or "").strip()
    return scope == SKU_ALL or scope == sku


def inject_vars(text: str, vars_map: Dict[str, str]) -> str:
    if not text:
        return ""

    def repl(m: re.Match) -> str:
        key = m.group(1)
        return vars_map.get(key, m.group(0))  # keep original if missing

    return VAR_PATTERN.sub(repl, text)


def render_materialized_rows(
    rows: List[Dict[str, str]],
    sku: str,
    lang: str,
    vars_for_sku: Dict[str, str],
) -> List[Dict[str, str]]:
    """
    Return rows filtered by sku_scope and with text field resolved for lang and variables injected.
    """
    text_col = LANG_MAP[lang]
    out: List[Dict[str, str]] = []
    for r in rows:
        if not in_scope(r, sku):
            continue
        text = r.get(text_col, "")
        text = inject_vars(text, vars_for_sku)
        rr = dict(r)
        rr["text_resolved"] = text
        rr["lang"] = lang
        rr["sku"] = sku
        out.append(rr)
    return out


# -----------------------------
# Outputs: revision log / (optional) changelog hooks
# -----------------------------
def write_revision_log(
    target_dir: Path,
    target: BuildTarget,
    rows_used: List[Dict[str, str]],
) -> None:
    """
    For demo: aggregate revision fields for rows used in this build.
    """
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append(f"HB-Docs Demo v2.0 Revision Log")
    lines.append(f"Generated at: {now}")
    lines.append(f"Target: sku={target.sku}, lang={target.lang}, version={target.version}")
    lines.append("")
    lines.append("Items:")
    for r in rows_used:
        cid = r.get("content_id", "")
        rid = r.get("revision_id", "")
        note = r.get("revision_note", "")
        updated_at = r.get("updated_at", "")
        updated_by = r.get("updated_by", "")
        lines.append(f"- {cid} | rev={rid} | by={updated_by} | at={updated_at} | note={note}")
    (target_dir / "revision_log.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_materialized_json(
    target_dir: Path,
    target: BuildTarget,
    rows_used: List[Dict[str, str]],
) -> None:
    """
    Useful for demo proof: show the single-source data after scope+vars+lang resolution.
    """
    payload = {
        "sku": target.sku,
        "lang": target.lang,
        "version": target.version,
        "items": [
            {
                "content_id": r.get("content_id"),
                "type": r.get("type"),
                "sku_scope": r.get("sku_scope"),
                "text": r.get("text_resolved"),
                "revision_id": r.get("revision_id"),
            }
            for r in rows_used
        ],
    }
    (target_dir / "materialized.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


# -----------------------------
# Hook: integrate with your existing pipeline
# -----------------------------
def call_existing_build_pipeline(target_dir: Path, target: BuildTarget, dry_run: bool) -> None:
    """
    TODO: Replace this with your real pipeline calls:
      1) csv -> rst (render_rst.py)
      2) rst -> pdf (build_docs.py / sphinx-build / latexmk)
    For now, we just create a placeholder file to prove the build ran.
    """
    if dry_run:
        return

    # Placeholder "artifact" for demo: later replace with actual PDF/HTML outputs
    (target_dir / f"Manual_{target.sku}_{target.lang}_v{target.version}.txt").write_text(
        "PLACEHOLDER: replace with actual PDF/HTML build outputs.\n",
        encoding="utf-8",
    )

    # Example of calling external scripts (commented):
    # subprocess.run([sys.executable, "tools/render_rst.py", "--sku", target.sku, "--lang", target.lang], check=True)
    # subprocess.run([sys.executable, "tools/build_docs.py", "--sku", target.sku, "--lang", target.lang, "--version", target.version], check=True)


def build_one(target: BuildTarget, content_rows: List[Dict[str, str]], vars_all: Dict[str, Dict[str, str]], dry_run: bool) -> None:
    vars_for_sku = vars_all.get(target.sku, {})
    out_dir = OUTPUT_DIR / target.sku / f"v{target.version}" / target.lang
    out_dir.mkdir(parents=True, exist_ok=True)

    rows_used = render_materialized_rows(content_rows, target.sku, target.lang, vars_for_sku)

    # Stage-1 outputs: revision log + materialized proof
    write_revision_log(out_dir, target, rows_used)
    write_materialized_json(out_dir, target, rows_used)

    # Hook: call your existing pipeline
    call_existing_build_pipeline(out_dir, target, dry_run=dry_run)

    print(f"[OK] Built: {out_dir}")


def resolve_targets(args: argparse.Namespace) -> List[BuildTarget]:
    if args.all:
        return [
            BuildTarget("SKU-A", "zh", args.version),
            BuildTarget("SKU-A", "en", args.version),
            BuildTarget("SKU-B", "zh", args.version),
            BuildTarget("SKU-B", "en", args.version),
        ]

    if not args.sku or not args.lang:
        raise SystemExit("When not using --all, you must specify --sku and --lang.")

    return [BuildTarget(args.sku, args.lang, args.version)]


def main() -> int:
    args = parse_args()

    # Load data
    vars_all = load_variables(VARS_CSV)
    content_rows = load_content(CONTENT_CSV)

    targets = resolve_targets(args)

    for t in targets:
        build_one(t, content_rows, vars_all, dry_run=args.dry_run)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())