#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HB-Docs Demo v2.0 - build.py (enhanced)

Goal: demo Single Source + multi-SKU + multi-lang + revision tracking + versioning

Key upgrades:
- Snapshot inputs per version into snapshots/v{version}/ (immutable)
- Build reads from snapshots (so old versions are rebuildable)
- revision_log includes base compare old/new (materialized with sku_scope + vars + lang)

Usage examples:
  python tools/build.py --all --version 1.0
  python tools/build.py --all --version 1.1           # auto-compare to previous snapshot
  python tools/build.py --all --version 1.1 --compare-from 1.0
  python tools/build.py --sku SKU-A --lang en --version 1.1
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import argparse
import csv
import datetime as dt
import json
import re
import sys
from typing import Dict, List, Optional


# -----------------------------
# Config (demo-level)
# -----------------------------
ROOT = Path(__file__).resolve().parents[1]  # repo root

DATA_DIR = ROOT / "demo_data"
CONTENT_CSV = DATA_DIR / "content_blocks.csv"
VARS_CSV = DATA_DIR / "product_variables.csv"

OUTPUT_DIR = ROOT / "output"
SNAPSHOT_DIR = ROOT / "snapshots"

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
    p.add_argument("--compare-from", dest="compare_from", default=None,
                   help="Compare against a base version, e.g. 1.0")
    p.add_argument("--snapshot-only", action="store_true",
                   help="Only snapshot demo_data into snapshots/vX.Y, then exit")
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
        raise ValueError("CSV is empty")

    # ===== 1️⃣ 必备列检查 =====
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

    for col in required:
        if col not in rows[0]:
            raise ValueError(f"Missing column: {col}")

    # ===== 2️⃣ content_id 唯一性 =====
    seen = set()
    for r in rows:
        cid = r.get("content_id", "")
        if not cid:
            raise ValueError("content_id is required for every row")
        if cid in seen:
            raise ValueError(f"content_id duplicated: {cid}")
        seen.add(cid)

    # ===== 3️⃣ revision_id 基本合法性检查 =====
    for r in rows:
        rid = r.get("revision_id", "")
        if rid and not rid.isdigit():
            raise ValueError(
                f"CSV column shift detected at content_id={r['content_id']} "
                f"(revision_id='{rid}')"
            )

    return rows



# -----------------------------
# Snapshot helpers
# -----------------------------
def snapshot_version(version: str) -> Path:
    """
    Copy demo_data CSVs to snapshots/v{version}/ as immutable build inputs.
    If destination exists, DO NOT overwrite (snapshot discipline).
    """
    vdir = SNAPSHOT_DIR / f"v{version}"
    vdir.mkdir(parents=True, exist_ok=True)

    for src in [CONTENT_CSV, VARS_CSV]:
        if not src.exists():
            raise FileNotFoundError(f"Missing demo data csv: {src}")
        dst = vdir / src.name
        if not dst.exists():
            dst.write_bytes(src.read_bytes())
    return vdir


def list_snapshot_versions() -> list[str]:
    if not SNAPSHOT_DIR.exists():
        return []
    versions: list[str] = []
    for p in SNAPSHOT_DIR.glob("v*"):
        if p.is_dir():
            name = p.name[1:]  # strip leading 'v'
            if re.match(r"^\d+(\.\d+)+$", name):
                versions.append(name)

    def ver_key(s: str):
        return tuple(int(x) for x in s.split("."))

    return sorted(versions, key=ver_key)


def find_previous_version(current: str) -> Optional[str]:
    versions = list_snapshot_versions()
    if current not in versions:
        return None
    i = versions.index(current)
    if i == 0:
        return None
    return versions[i - 1]


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
        return vars_map.get(key, m.group(0))  # keep placeholder if missing

    return VAR_PATTERN.sub(repl, text)


def render_materialized_rows(
    rows: List[Dict[str, str]],
    sku: str,
    lang: str,
    vars_for_sku: Dict[str, str],
) -> List[Dict[str, str]]:
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


def diff_materialized(
    old_rows: List[Dict[str, str]],
    new_rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    old_map = {r.get("content_id", ""): r for r in old_rows if r.get("content_id", "")}
    new_map = {r.get("content_id", ""): r for r in new_rows if r.get("content_id", "")}

    changes: List[Dict[str, str]] = []
    all_ids = sorted(set(old_map.keys()) | set(new_map.keys()))

    for cid in all_ids:
        o = old_map.get(cid)
        n = new_map.get(cid)

        if o is None and n is not None:
            changes.append({"change_type": "ADD", "content_id": cid, "old": "", "new": n.get("text_resolved", "")})
            continue
        if n is None and o is not None:
            changes.append({"change_type": "DEL", "content_id": cid, "old": o.get("text_resolved", ""), "new": ""})
            continue

        ot = (o.get("text_resolved", "") if o else "")
        nt = (n.get("text_resolved", "") if n else "")
        if ot != nt:
            changes.append({"change_type": "MOD", "content_id": cid, "old": ot, "new": nt})

    return changes


# -----------------------------
# Outputs: revision log + proof artifacts
# -----------------------------
def write_revision_log(
    target_dir: Path,
    target: BuildTarget,
    rows_used: List[Dict[str, str]],
    base_version: Optional[str],
    base_rows_used: Optional[List[Dict[str, str]]],
) -> None:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: List[str] = []
    lines.append("HB-Docs Demo v2.0 Revision Log")
    lines.append(f"Generated at: {now}")
    lines.append(f"Target: sku={target.sku}, lang={target.lang}, version={target.version}")
    if base_version:
        lines.append(f"Compared to: v{base_version}")
    lines.append("")
    lines.append("Items (metadata):")
    for r in rows_used:
        cid = r.get("content_id", "")
        rid = r.get("revision_id", "")
        note = r.get("revision_note", "")
        updated_at = r.get("updated_at", "")
        updated_by = r.get("updated_by", "")
        lines.append(f"- {cid} | rev={rid} | by={updated_by} | at={updated_at} | note={note}")

    if base_version and base_rows_used is not None:
        changes = diff_materialized(base_rows_used, rows_used)
        lines.append("")
        lines.append("Changes (old -> new):")
        if not changes:
            lines.append("- (no text changes after scope/lang/vars resolution)")
        else:
            for ch in changes:
                cid = ch["content_id"]
                ctype = ch["change_type"]
                lines.append(f"- [{ctype}] {cid}")
                if ctype in ("MOD", "DEL"):
                    lines.append(f"  old: {ch['old']}")
                if ctype in ("MOD", "ADD"):
                    lines.append(f"  new: {ch['new']}")

    (target_dir / "revision_log.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_materialized_json(
    target_dir: Path,
    target: BuildTarget,
    rows_used: List[Dict[str, str]],
) -> None:
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
    TODO: Replace this with your real pipeline calls.
    For now: placeholder artifact.
    """
    if dry_run:
        return

    (target_dir / f"Manual_{target.sku}_{target.lang}_v{target.version}.txt").write_text(
        "PLACEHOLDER: replace with actual PDF/HTML build outputs.\n",
        encoding="utf-8",
    )


def build_one(
    target: BuildTarget,
    content_rows: List[Dict[str, str]],
    vars_all: Dict[str, Dict[str, str]],
    dry_run: bool,
    base_version: Optional[str],
) -> None:
    vars_for_sku = vars_all.get(target.sku, {})
    out_dir = OUTPUT_DIR / target.sku / f"v{target.version}" / target.lang
    out_dir.mkdir(parents=True, exist_ok=True)

    rows_used = render_materialized_rows(content_rows, target.sku, target.lang, vars_for_sku)

    base_rows_used = None
    if base_version:
        base_vdir = SNAPSHOT_DIR / f"v{base_version}"
        base_content = load_content(base_vdir / "content_blocks.csv")
        base_vars_all = load_variables(base_vdir / "product_variables.csv")
        base_vars_for_sku = base_vars_all.get(target.sku, {})
        base_rows_used = render_materialized_rows(base_content, target.sku, target.lang, base_vars_for_sku)

    write_revision_log(out_dir, target, rows_used, base_version, base_rows_used)
    write_materialized_json(out_dir, target, rows_used)

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

    # 1) snapshot current demo inputs for this version
    snapshot_version(args.version)

    # 2) resolve base version
    base_version = args.compare_from
    if base_version is None:
        base_version = find_previous_version(args.version)

    if args.snapshot_only:
        print(f"[OK] Snapshot done: {SNAPSHOT_DIR / f'v{args.version}'}")
        return 0

    # 3) load CURRENT version inputs from snapshots (NOT from demo_data)
    cur_vdir = SNAPSHOT_DIR / f"v{args.version}"
    vars_all = load_variables(cur_vdir / "product_variables.csv")
    content_rows = load_content(cur_vdir / "content_blocks.csv")

    targets = resolve_targets(args)
    for t in targets:
        build_one(t, content_rows, vars_all, dry_run=args.dry_run, base_version=base_version)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())