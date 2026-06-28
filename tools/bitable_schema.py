#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Feishu Bitable schema export / apply for dev -> prod tenant parity.

The repo's code already mirrors dev -> prod (auto-manual -> Hello-Docs). This tool
does the same for the Bitable *structure* so that adding a table/field in the dev
tenant becomes a recorded, replayable change instead of a manual one.

- ``export``: snapshot a tenant base's structure (tables + fields, keyed by NAME, no
  per-tenant IDs) to a committed JSON manifest. The manifest is the version-controlled
  record; its git diff is the change history. It rides the existing code mirror to the
  prod repo.
- ``apply``: idempotently bring a TARGET tenant up to the manifest — create missing
  tables and missing fields, matched by name. ONLY-INCREMENT: never deletes or alters
  existing tables/fields. Dry-run by default; ``--write`` performs creation. Complex
  fields (link / formula / lookup) are reported for manual setup, not auto-created
  (cross-tenant link/formula resolution is unsafe to guess).

Structure is shared (one manifest); per-tenant table IDs stay in the FEISHU_PHASE2_*
env files, never in git.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

# Field types this tool can create in a target tenant. Anything else (link / formula /
# lookup / button / auto_number ...) is recorded but flagged for manual setup, because
# it references other tables/fields whose IDs differ per tenant.
SIMPLE_TYPES = {"text", "number", "checkbox", "datetime", "select", "phone", "url", "rating", "currency", "percent"}
COMPLEX_TYPES = {"link", "one_way_link", "two_way_link", "formula", "lookup", "auto_number", "autonumber", "button", "attachment", "user", "group_chat"}


def _lark(args: list[str], lark_cli: str = "lark-cli") -> dict:
    env = {**os.environ, "LARK_CLI_NO_PROXY": os.environ.get("LARK_CLI_NO_PROXY", "1")}
    out = subprocess.run([lark_cli, *args], capture_output=True, text=True, env=env).stdout
    try:
        return json.loads(out[out.index("{"):])
    except ValueError:
        return {"ok": False, "_raw": out[:200]}


def _norm_select(raw_type: str, multiple: bool) -> str:
    return "select"  # both single_select and multi_select create as type=select (+multiple flag)


def _field_export(f: dict) -> dict:
    name = f.get("field_name") or f.get("name")
    t = (f.get("type") or "").lower()
    prop = f.get("property") or {}
    rec: dict = {"name": name, "type": t}
    if t in ("single_select", "multi_select", "select"):
        rec["type"] = "select"
        rec["multiple"] = bool(f.get("multiple")) or t == "multi_select"
        opts = f.get("options") or prop.get("options") or []
        rec["options"] = [o.get("name") for o in opts if isinstance(o, dict) and o.get("name")]
    return rec


def export(base_token: str, table_filter: list[str] | None, lark_cli: str) -> dict:
    tl = _lark(["base", "+table-list", "--base-token", base_token, "--format", "json", "--as", "bot"], lark_cli)
    tables = tl.get("data", {}).get("tables") or tl.get("data", {}).get("items") or []
    out_tables = []
    for t in tables:
        name = t.get("name")
        tid = t.get("id") or t.get("table_id")
        if table_filter and name not in table_filter:
            continue
        fl = _lark(["base", "+field-list", "--base-token", base_token, "--table-id", tid, "--format", "json", "--as", "bot"], lark_cli)
        items = fl.get("data", {}).get("items") or fl.get("data", {}).get("fields") or []
        out_tables.append({"name": name, "fields": [_field_export(f) for f in items]})
    return {"schema_version": "bitable-schema/v1", "tables": out_tables}


def _create_table(base_token: str, name: str, simple_fields: list[dict], lark_cli: str) -> tuple[bool, str]:
    # table-create needs >=1 field; create with all simple fields at once.
    fields_json = json.dumps(simple_fields or [{"name": "Name", "type": "text"}], ensure_ascii=False)
    r = _lark(["base", "+table-create", "--base-token", base_token, "--name", name, "--fields", fields_json, "--format", "json", "--as", "bot"], lark_cli)
    tid = (r.get("data", {}) or {}).get("table_id") or (r.get("data", {}) or {}).get("table", {}).get("table_id")
    return bool(r.get("ok")), (tid or "")


def _create_field(base_token: str, tid: str, field: dict, lark_cli: str) -> bool:
    payload = {k: v for k, v in field.items() if v is not None}
    r = _lark(["base", "+field-create", "--base-token", base_token, "--table-id", tid, "--json", json.dumps(payload, ensure_ascii=False), "--format", "json", "--as", "bot"], lark_cli)
    return bool(r.get("ok"))


def apply(manifest: dict, base_token: str, write: bool, lark_cli: str) -> dict:
    tl = _lark(["base", "+table-list", "--base-token", base_token, "--format", "json", "--as", "bot"], lark_cli)
    tables = tl.get("data", {}).get("tables") or tl.get("data", {}).get("items") or []
    existing = {t.get("name"): (t.get("id") or t.get("table_id")) for t in tables}
    plan: dict = {"create_tables": [], "create_fields": [], "skip_existing": [], "manual_complex": [], "new_table_ids": {}, "external_write": bool(write)}

    for tbl in manifest.get("tables", []):
        tname = tbl["name"]
        simple = [f for f in tbl["fields"] if f.get("type") in SIMPLE_TYPES]
        complex_ = [f for f in tbl["fields"] if f.get("type") not in SIMPLE_TYPES]
        for f in complex_:
            plan["manual_complex"].append({"table": tname, "field": f["name"], "type": f["type"]})
        if tname not in existing:
            plan["create_tables"].append(tname)
            if write:
                ok, tid = _create_table(base_token, tname, simple, lark_cli)
                if ok and tid:
                    existing[tname] = tid
                    plan["new_table_ids"][tname] = tid
            continue
        # table exists -> add missing fields
        tid = existing[tname]
        fl = _lark(["base", "+field-list", "--base-token", base_token, "--table-id", tid, "--format", "json", "--as", "bot"], lark_cli)
        have = {(f.get("field_name") or f.get("name")) for f in (fl.get("data", {}).get("items") or fl.get("data", {}).get("fields") or [])}
        for f in simple:
            if f["name"] in have:
                plan["skip_existing"].append({"table": tname, "field": f["name"]})
            else:
                plan["create_fields"].append({"table": tname, "field": f["name"], "type": f["type"]})
                if write:
                    _create_field(base_token, tid, f, lark_cli)
    return plan


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Export / apply Feishu Bitable schema for dev->prod tenant parity.")
    sub = p.add_subparsers(dest="command", required=True)

    e = sub.add_parser("export", description="Snapshot a tenant base's table/field structure to a committed manifest (name-keyed, no IDs).")
    e.add_argument("--base-token", default=os.environ.get("FEISHU_PHASE2_BASE_TOKEN"), help="source base token (default: $FEISHU_PHASE2_BASE_TOKEN)")
    e.add_argument("--tables", help="comma-separated table names to export; omit for the whole base")
    e.add_argument("--out", required=True, help="manifest output path (committed)")
    e.add_argument("--lark-cli", default="lark-cli")

    a = sub.add_parser("apply", description="Idempotently create missing tables/fields in a TARGET tenant from the manifest. Dry-run unless --write.")
    a.add_argument("--manifest", required=True)
    a.add_argument("--base-token", required=True, help="TARGET (e.g. prod) base token")
    a.add_argument("--write", action="store_true", help="actually create missing tables/fields (else dry-run plan)")
    a.add_argument("--lark-cli", default="lark-cli")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "export":
        if not args.base_token:
            print("bitable-schema: --base-token or $FEISHU_PHASE2_BASE_TOKEN required", file=sys.stderr)
            return 2
        manifest = export(args.base_token, [t.strip() for t in args.tables.split(",")] if args.tables else None, args.lark_cli)
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"WROTE {out}  ({len(manifest['tables'])} tables)")
        for t in manifest["tables"]:
            print(f"  {t['name']}: {len(t['fields'])} fields")
        return 0
    if args.command == "apply":
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        plan = apply(manifest, args.base_token, args.write, args.lark_cli)
        mode = "WRITE" if plan["external_write"] else "dry-run"
        print(f"APPLY ({mode}): create {len(plan['create_tables'])} table(s), {len(plan['create_fields'])} field(s); "
              f"skip {len(plan['skip_existing'])} existing; {len(plan['manual_complex'])} complex field(s) need manual setup")
        for t in plan["create_tables"]:
            print(f"  + TABLE {t}{'  -> ' + plan['new_table_ids'].get(t, '') if plan['new_table_ids'].get(t) else ''}")
        for f in plan["create_fields"]:
            print(f"  + FIELD {f['table']}.{f['field']} ({f['type']})")
        for f in plan["manual_complex"]:
            print(f"  ! MANUAL {f['table']}.{f['field']} ({f['type']}) — link/formula/lookup, set up by hand")
        if plan["new_table_ids"]:
            print("\nAdd these to the target tenant's FEISHU_PHASE2_* env:")
            for n, i in plan["new_table_ids"].items():
                print(f"  # {n} = {i}")
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
