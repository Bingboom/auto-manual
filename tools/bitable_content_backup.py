#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Point-in-time CONTENT backup / restore for the Feishu Bitable source-of-truth.

``bitable_schema.py`` mirrors table *structure* (the I5 drill rebuilds a base's
tables/fields from the committed manifests). This tool covers the other half —
the *rows*. Together they answer Milestone K4: a destructive table edit must be
restorable from a dated export.

- ``export``: for every table named in a schema manifest, page through all
  records and write one CSV per table (ALL columns, computed ones included, for
  audit value) plus a ``backup_manifest.json`` (row counts + sha256 per CSV).
  Runs nightly via ``.github/workflows/phase2-content-backup.yml``; the dated
  artifact is the restore point.
- ``restore``: recreate rows from a backup into a target base whose table
  structure already exists (``bitable_schema apply`` first — see ops guide
  §4.7). Writes only simple writable fields (formula / lookup / link / attach
  are never written; their columns are reported as skipped). Refuses non-empty
  target tables so a mistyped token cannot double up a production table.
  Dry-run unless ``--write --yes``; the target token is always explicit, never
  read from env, so a restore cannot silently aim at the live base.
- ``verify``: compare a backup's row counts against a live base (post-restore
  read-back, or "how far has the live base drifted from this restore point").

Deliberately no retry/rate-limit layer here — that arrives with the single
transport client (Milestone K8); a transient export failure surfaces through
the workflow's sentinel Issue instead of being silently retried.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from tools import bitable_schema as bs
except ImportError:  # pragma: no cover - direct execution fallback
    import bitable_schema as bs  # type: ignore[no-redef]

BACKUP_MANIFEST = "backup_manifest.json"
BATCH_CREATE_LIMIT = 200  # lark-cli record-batch-create hard cap per call


def _safe_filename(table_name: str) -> str:
    return "".join("_" if c in '/\\:*?"<>|' else c for c in table_name) + ".csv"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def export_content(manifest: dict, base_token: str, label: str, out_dir: Path, lark_cli: str) -> dict:
    """Dump every manifest-listed table's rows to ``<out_dir>/<label>/*.csv``."""
    dest = out_dir / label
    dest.mkdir(parents=True, exist_ok=True)
    report: dict = {"label": label, "generated_at": _utc_now(),
                    "schema_version": manifest.get("schema_version"),
                    "tables": [], "missing_tables": []}
    for entry in manifest.get("tables", []):
        name = entry["name"]
        tid = bs._resolve_table_id(base_token, name, lark_cli)
        if not tid:
            report["missing_tables"].append(name)
            continue
        ftypes = bs._field_types(base_token, tid, lark_cli)
        cols = list(ftypes)
        rows, rids = bs._read_records(base_token, tid, lark_cli)
        path = dest / _safe_filename(name)
        with path.open("w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["_record_id", *cols])
            for row, rid in zip(rows, rids):
                w.writerow([rid, *[bs._serialize_cell(row.get(c), ftypes[c]) for c in cols]])
        report["tables"].append({
            "name": name, "table_id": tid, "csv": path.name, "rows": len(rows),
            "columns": cols, "field_types": ftypes,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    (dest / BACKUP_MANIFEST).write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def _load_backup(backup_dir: Path) -> dict:
    mf = backup_dir / BACKUP_MANIFEST
    if not mf.is_file():
        raise FileNotFoundError(f"not a backup dir (no {BACKUP_MANIFEST}): {backup_dir}")
    return json.loads(mf.read_text(encoding="utf-8"))


def _read_backup_rows(backup_dir: Path, entry: dict) -> tuple[list[str], list[dict]]:
    with (backup_dir / entry["csv"]).open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
    cols = [c for c in (reader.fieldnames or []) if c != "_record_id"]
    return cols, rows


def _restore_cell(value: str, ftype: str):
    v = bs._coerce_cell(value, ftype)
    # record-list emits datetime cells as epoch-milliseconds; batch-create wants
    # a number (or a "YYYY-MM-DD hh:mm:ss" string), not a digit-string.
    if ftype == "datetime" and isinstance(v, str) and v.isdigit():
        return int(v)
    return v


def _sync_select_options(base_token: str, tid: str, writable: list[str], rows: list[dict],
                         write: bool, lark_cli: str, plan: dict) -> None:
    """Add backup select values missing from the target field's options.

    batch-create rejects a select value that is not an existing option
    (error 800030005) — and options drift: the live base gains options after
    the schema manifest snapshot. Live-drill finding, 2026-07-17: the TM base
    restore failed exactly this way. field-update uses full PUT semantics, so
    the payload re-sends existing options plus the missing ones.
    """
    fl = bs._lark(["base", "+field-list", "--base-token", base_token, "--table-id", tid,
                   "--format", "json", "--as", "bot"], lark_cli)
    items = {f.get("name"): f for f in (fl.get("data", {}).get("fields") or fl.get("data", {}).get("items") or [])}
    added: dict = {}
    for col in writable:
        item = items.get(col) or {}
        if "select" not in (item.get("type") or ""):
            continue
        opts = item.get("options") or (item.get("property") or {}).get("options") or []
        existing = [o.get("name") for o in opts if isinstance(o, dict) and o.get("name")]
        needed = {(row.get(col) or "").strip() for row in rows} - {""}
        missing = sorted(needed - set(existing))
        if not missing:
            continue
        added[col] = missing
        if write:
            payload = {"name": col, "type": "select",
                       "options": [{"name": n} for n in [*existing, *missing]]}
            if item.get("multiple"):
                payload["multiple"] = True
            resp = bs._lark(["base", "+field-update", "--base-token", base_token, "--table-id", tid,
                             "--field-id", col, "--json", json.dumps(payload, ensure_ascii=False),
                             "--yes", "--format", "json", "--as", "bot"], lark_cli)
            if resp.get("ok") is False or (resp.get("code") not in (None, 0)):
                plan["errors"].append(f"option sync failed for {col}: {str(resp)[:150]}")
    plan["select_options_added"] = added


def restore_content(backup_dir: Path, base_token: str, tables: list[str] | None,
                    write: bool, allow_nonempty: bool, lark_cli: str) -> dict:
    backup = _load_backup(backup_dir)
    selected = [t for t in backup["tables"] if tables is None or t["name"] in tables]
    report: dict = {"write": bool(write), "backup_generated_at": backup.get("generated_at"),
                    "tables": [], "not_in_backup": sorted(set(tables or []) - {t["name"] for t in selected})}
    for entry in selected:
        name = entry["name"]
        plan: dict = {"name": name, "skipped_columns": [], "planned_rows": 0,
                      "created_rows": 0, "empty_rows_skipped": 0, "errors": []}
        report["tables"].append(plan)
        tid = bs._resolve_table_id(base_token, name, lark_cli)
        if not tid:
            plan["errors"].append("table missing on target — run bitable_schema apply first")
            continue
        plan["table_id"] = tid
        target_types = bs._field_types(base_token, tid, lark_cli)
        cols, rows = _read_backup_rows(backup_dir, entry)
        writable = [c for c in cols if target_types.get(c) in bs.SIMPLE_TYPES]
        plan["skipped_columns"] = [c for c in cols if c not in writable]
        existing_rows, _ = bs._read_records(base_token, tid, lark_cli)
        if existing_rows and not allow_nonempty:
            plan["errors"].append(
                f"target table has {len(existing_rows)} row(s); restore only fills empty "
                "tables (use --allow-nonempty to append anyway)")
            continue
        _sync_select_options(base_token, tid, writable, rows, write, lark_cli, plan)
        payload_rows = []
        for row in rows:
            cells = [_restore_cell(row.get(c, ""), target_types[c]) for c in writable]
            # a blank source row round-trips its checkbox cells as False; a row whose
            # only "content" is unchecked checkboxes recreates nothing meaningful
            if all(v is None or v is False for v in cells):
                plan["empty_rows_skipped"] += 1
                continue
            payload_rows.append(cells)
        plan["planned_rows"] = len(payload_rows)
        if not write:
            continue
        for i in range(0, len(payload_rows), BATCH_CREATE_LIMIT):
            chunk = payload_rows[i:i + BATCH_CREATE_LIMIT]
            resp = bs._lark([
                "base", "+record-batch-create", "--base-token", base_token, "--table-id", tid,
                "--json", json.dumps({"fields": writable, "rows": chunk}, ensure_ascii=False),
                "--format", "json", "--as", "bot",
            ], lark_cli)
            if resp.get("ok") is False or (resp.get("code") not in (None, 0)):
                plan["errors"].append(f"batch at row {i}: {str(resp)[:200]}")
                break
            plan["created_rows"] += len(chunk)
        readback, _ = bs._read_records(base_token, tid, lark_cli)
        plan["readback_rows"] = len(readback)
    return report


def verify_content(backup_dir: Path, base_token: str, tables: list[str] | None, lark_cli: str) -> dict:
    backup = _load_backup(backup_dir)
    report: dict = {"backup_generated_at": backup.get("generated_at"), "tables": [], "in_sync": True}
    for entry in backup["tables"]:
        if tables is not None and entry["name"] not in tables:
            continue
        tid = bs._resolve_table_id(base_token, entry["name"], lark_cli)
        live = None
        if tid:
            live_rows, _ = bs._read_records(base_token, tid, lark_cli)
            live = len(live_rows)
        row = {"name": entry["name"], "backup_rows": entry["rows"], "live_rows": live,
               "match": live == entry["rows"]}
        report["tables"].append(row)
        report["in_sync"] = report["in_sync"] and row["match"]
    return report


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Point-in-time content backup/restore for Feishu Bitable bases.")
    sub = p.add_subparsers(dest="command", required=True)

    e = sub.add_parser("export", description="Dump all manifest-listed tables' rows to dated CSVs + backup manifest.")
    e.add_argument("--manifest", required=True, help="schema manifest naming the tables (e.g. bitable_schema/business_base_manifest.json)")
    e.add_argument("--base-token-env", required=True, help="env var holding the SOURCE base token (name recorded, value never)")
    e.add_argument("--label", required=True, help="subdirectory label for this base (e.g. business / tm)")
    e.add_argument("--out", required=True, help="output directory (the dated artifact root)")
    e.add_argument("--lark-cli", default="lark-cli")

    r = sub.add_parser("restore", description="Recreate rows from a backup into an (empty-table) target base. Dry-run unless --write --yes.")
    r.add_argument("--backup", required=True, help="backup label dir containing backup_manifest.json")
    r.add_argument("--base-token", required=True, help="TARGET base token — explicit on purpose; never defaults to the live base env")
    r.add_argument("--tables", help="comma-separated table names (default: every table in the backup)")
    r.add_argument("--allow-nonempty", action="store_true", help="append into a non-empty target table (default: refuse)")
    r.add_argument("--write", action="store_true", help="actually create rows (else dry-run plan)")
    r.add_argument("--yes", action="store_true", help="confirm the TARGET base is correct; REQUIRED together with --write")
    r.add_argument("--lark-cli", default="lark-cli")

    v = sub.add_parser("verify", description="Compare a backup's row counts against a live base.")
    v.add_argument("--backup", required=True)
    v.add_argument("--base-token", required=True)
    v.add_argument("--tables", help="comma-separated table names (default: all)")
    v.add_argument("--lark-cli", default="lark-cli")

    for sp in (e, r, v):
        sp.add_argument("--profile", help="lark-cli config profile to route through")
        sp.add_argument("--identity", default="bot", choices=["bot", "user"], help="lark-cli token identity (default: bot)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    bs._PROFILE = getattr(args, "profile", None)
    bs._IDENTITY = getattr(args, "identity", None) or "bot"
    if args.command == "export":
        import os
        token = os.environ.get(args.base_token_env, "")
        if not token:
            print(f"bitable-content-backup: ${args.base_token_env} is empty", file=sys.stderr)
            return 2
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        report = export_content(manifest, token, args.label, Path(args.out), args.lark_cli)
        total = sum(t["rows"] for t in report["tables"])
        print(f"EXPORT {args.label}: {len(report['tables'])} table(s), {total} row(s) -> {args.out}/{args.label}")
        for t in report["tables"]:
            print(f"  {t['name']}: {t['rows']} rows")
        for name in report["missing_tables"]:
            print(f"  ✗ MISSING on source base: {name}")
        return 1 if report["missing_tables"] else 0
    if args.command == "restore":
        write = bool(args.write and args.yes)
        if args.write and not args.yes:
            print("⚠ --write ignored: re-run with --write --yes once you've confirmed the TARGET base token.")
        tables = [t.strip() for t in args.tables.split(",")] if args.tables else None
        report = restore_content(Path(args.backup), args.base_token, tables, write, args.allow_nonempty, args.lark_cli)
        mode = "WRITE" if write else "dry-run"
        print(f"RESTORE ({mode}) from backup taken {report['backup_generated_at']}:")
        failed = bool(report["not_in_backup"])
        for name in report["not_in_backup"]:
            print(f"  ✗ not in backup: {name}")
        for t in report["tables"]:
            state = f"planned {t['planned_rows']}" + (f", created {t['created_rows']}, readback {t.get('readback_rows')}" if write else "")
            print(f"  {t['name']}: {state}; skipped cols {len(t['skipped_columns'])}, empty rows {t['empty_rows_skipped']}")
            for col, opts in (t.get("select_options_added") or {}).items():
                print(f"    + select options {col}: {', '.join(opts[:8])}{' …' if len(opts) > 8 else ''}")
            for err in t["errors"]:
                failed = True
                print(f"    ✗ {err}")
        return 1 if failed else 0
    if args.command == "verify":
        tables = [t.strip() for t in args.tables.split(",")] if args.tables else None
        report = verify_content(Path(args.backup), args.base_token, tables, args.lark_cli)
        for t in report["tables"]:
            mark = "✓" if t["match"] else "✗"
            print(f"  {mark} {t['name']}: backup {t['backup_rows']} vs live {t['live_rows']}")
        print("VERIFY " + ("✅ counts match" if report["in_sync"] else "✗ mismatch"))
        return 0 if report["in_sync"] else 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
