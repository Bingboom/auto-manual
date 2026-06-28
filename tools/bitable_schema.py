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

# Per-run lark-cli routing, set by main() from CLI flags. _PROFILE selects a lark-cli
# config profile (e.g. a separate prod-tenant login, so dev's default profile is never
# touched); _IDENTITY chooses the bot vs user token. Defaults preserve the original
# behavior (active profile, bot identity). Cross-tenant writes typically need
# ``--profile <prod> --identity user`` (the prod owner's token), because the prod app's
# bot may not be a collaborator on the base.
_PROFILE: str | None = None
_IDENTITY: str = "bot"


def _lark(args: list[str], lark_cli: str = "lark-cli") -> dict:
    env = {**os.environ, "LARK_CLI_NO_PROXY": os.environ.get("LARK_CLI_NO_PROXY", "1")}
    cmd = [lark_cli]
    if _PROFILE:
        cmd += ["--profile", _PROFILE]
    a = list(args)
    if "--as" in a:  # callers pass a default "--as bot"; honor the run-level identity instead
        i = a.index("--as")
        del a[i:i + 2]
    cmd += [*a, "--as", _IDENTITY]
    out = subprocess.run(cmd, capture_output=True, text=True, env=env).stdout
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


def _field_for_write(field: dict) -> dict:
    """Convert a manifest field (select options stored as a NAME LIST) into lark-cli's
    create payload, where select options must be OBJECTS: ``[{"name": ...}]``. Passing
    bare strings makes table-create / field-create silently reject the field."""
    out = {k: v for k, v in field.items() if v is not None}
    if out.get("type") == "select" and out.get("options"):
        out["options"] = [{"name": o} if isinstance(o, str) else o for o in out["options"]]
    return out


def _create_table(base_token: str, name: str, simple_fields: list[dict], lark_cli: str) -> tuple[bool, str]:
    # table-create needs >=1 field; create with all simple fields at once.
    fields = [_field_for_write(f) for f in simple_fields] or [{"name": "Name", "type": "text"}]
    fields_json = json.dumps(fields, ensure_ascii=False)
    r = _lark(["base", "+table-create", "--base-token", base_token, "--name", name, "--fields", fields_json, "--format", "json", "--as", "bot"], lark_cli)
    data = r.get("data", {}) or {}
    tid = data.get("table_id") or (data.get("table", {}) or {}).get("table_id") or data.get("id")
    return bool(r.get("ok")), (tid or "")


def _create_field(base_token: str, tid: str, field: dict, lark_cli: str) -> bool:
    payload = _field_for_write(field)
    r = _lark(["base", "+field-create", "--base-token", base_token, "--table-id", tid, "--json", json.dumps(payload, ensure_ascii=False), "--format", "json", "--as", "bot"], lark_cli)
    return bool(r.get("ok"))


def _field_differs(want: dict, have: dict) -> str:
    """Return a human reason if an existing field's shape diverges from the manifest, else ''.
    apply never auto-changes an existing field; this only surfaces silent drift."""
    if (want.get("type") or "") != (have.get("type") or ""):
        return f"type {have.get('type')!r} ≠ {want.get('type')!r}"
    if want.get("type") == "select":
        if set(want.get("options") or []) != set(have.get("options") or []):
            return f"options {have.get('options')} ≠ {want.get('options')}"
        if bool(want.get("multiple")) != bool(have.get("multiple")):
            return f"multiple {have.get('multiple')} ≠ {want.get('multiple')}"
    return ""


def apply(manifest: dict, base_token: str, write: bool, lark_cli: str) -> dict:
    tl = _lark(["base", "+table-list", "--base-token", base_token, "--format", "json", "--as", "bot"], lark_cli)
    tables = tl.get("data", {}).get("tables") or tl.get("data", {}).get("items") or []
    existing = {t.get("name"): (t.get("id") or t.get("table_id")) for t in tables}
    plan: dict = {"create_tables": [], "create_fields": [], "skip_existing": [], "drift": [],
                  "manual_complex": [], "new_table_ids": {}, "target_tables": sorted(existing), "external_write": bool(write)}

    for tbl in manifest.get("tables", []):
        tname = tbl["name"]
        simple = [f for f in tbl["fields"] if f.get("type") in SIMPLE_TYPES]
        for f in tbl["fields"]:
            if f.get("type") not in SIMPLE_TYPES:
                plan["manual_complex"].append({"table": tname, "field": f["name"], "type": f["type"]})
        if tname not in existing:
            plan["create_tables"].append(tname)
            if write:
                ok, tid = _create_table(base_token, tname, simple, lark_cli)
                if ok and not tid:  # some lark-cli builds don't echo the new id -> re-resolve by name
                    rl = _lark(["base", "+table-list", "--base-token", base_token, "--format", "json", "--as", "bot"], lark_cli)
                    for t in (rl.get("data", {}).get("tables") or rl.get("data", {}).get("items") or []):
                        if t.get("name") == tname:
                            tid = t.get("id") or t.get("table_id") or ""
                if ok and tid:
                    existing[tname] = tid
                    plan["new_table_ids"][tname] = tid
            continue
        # table exists -> add missing fields, flag drift on existing ones (never alter)
        tid = existing[tname]
        fl = _lark(["base", "+field-list", "--base-token", base_token, "--table-id", tid, "--format", "json", "--as", "bot"], lark_cli)
        target = {fe["name"]: fe for fe in (_field_export(f) for f in (fl.get("data", {}).get("items") or fl.get("data", {}).get("fields") or []))}
        for f in tbl["fields"]:
            if f["name"] not in target:
                if f.get("type") in SIMPLE_TYPES:
                    plan["create_fields"].append({"table": tname, "field": f["name"], "type": f["type"]})
                    if write:
                        _create_field(base_token, tid, f, lark_cli)
                # missing complex field already recorded in manual_complex
                continue
            reason = _field_differs(f, target[f["name"]])
            if reason:
                plan["drift"].append({"table": tname, "field": f["name"], "detail": reason})
            else:
                plan["skip_existing"].append({"table": tname, "field": f["name"]})
    return plan


def parity(source_base: str, target_base: str, table_filter: list[str] | None, lark_cli: str) -> dict:
    """Read-only structure diff between two tenants (e.g. dev vs prod).

    Reports what the SOURCE tenant has that the TARGET lacks (missing tables/fields) or
    has differently (drift). The TARGET may legitimately have *extra* tables (reported
    as informational, not a parity failure). Writes nothing.
    """
    src = export(source_base, table_filter, lark_cli)
    plan = apply(src, target_base, write=False, lark_cli=lark_cli)
    src_names = {t["name"] for t in src["tables"]}
    extra = sorted(set(plan["target_tables"]) - src_names) if table_filter is None else []
    return {
        "missing_tables": plan["create_tables"],
        "missing_fields": plan["create_fields"],
        "drift": plan["drift"],
        "manual_complex": plan["manual_complex"],
        "extra_tables": extra,
        "in_parity": not (plan["create_tables"] or plan["create_fields"] or plan["drift"]),
    }


def _add_routing(sp: argparse.ArgumentParser) -> None:
    """Add the shared lark-cli routing flags (profile + identity) to a subparser."""
    sp.add_argument("--profile", help="lark-cli config profile to route through (e.g. a separate prod-tenant login; dev's default profile is left untouched)")
    sp.add_argument("--identity", default="bot", choices=["bot", "user"], help="lark-cli token identity (default: bot; cross-tenant writes usually need 'user', the base owner's token)")


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Export / apply Feishu Bitable schema for dev->prod tenant parity.")
    sub = p.add_subparsers(dest="command", required=True)

    e = sub.add_parser("export", description="Snapshot a tenant base's table/field structure to a committed manifest (name-keyed, no IDs).")
    e.add_argument("--base-token", default=os.environ.get("FEISHU_PHASE2_BASE_TOKEN"), help="source base token (default: $FEISHU_PHASE2_BASE_TOKEN)")
    e.add_argument("--tables", help="comma-separated table names to export; omit for the whole base")
    e.add_argument("--out", required=True, help="manifest output path (committed)")
    e.add_argument("--lark-cli", default="lark-cli")
    _add_routing(e)

    a = sub.add_parser("apply", description="Idempotently create missing tables/fields in a TARGET tenant from the manifest. Dry-run unless --write.")
    a.add_argument("--manifest", required=True)
    a.add_argument("--base-token", required=True, help="TARGET (e.g. prod) base token")
    a.add_argument("--write", action="store_true", help="actually create missing tables/fields (else dry-run plan)")
    a.add_argument("--yes", action="store_true", help="confirm the TARGET base is correct; REQUIRED together with --write")
    a.add_argument("--lark-cli", default="lark-cli")
    _add_routing(a)

    pa = sub.add_parser("parity", description="Read-only: report structure differences between a SOURCE tenant (e.g. dev) and a TARGET tenant (e.g. prod). Exit 1 if the target lags/diverges — usable as a CI parity gate.")
    pa.add_argument("--source-base", required=True, help="reference tenant base token (e.g. dev)")
    pa.add_argument("--target-base", required=True, help="tenant to check (e.g. prod)")
    pa.add_argument("--tables", help="comma-separated table names; omit for the whole base")
    pa.add_argument("--lark-cli", default="lark-cli")
    _add_routing(pa)
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    global _PROFILE, _IDENTITY
    _PROFILE = getattr(args, "profile", None)
    _IDENTITY = getattr(args, "identity", None) or "bot"
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
        write = bool(args.write and args.yes)
        plan = apply(manifest, args.base_token, write, args.lark_cli)
        print(f"Target base: {args.base_token}  ({len(plan['target_tables'])} existing tables)")
        if args.write and not args.yes:
            print("⚠ --write ignored: re-run with --write --yes once you've confirmed this is the intended (prod) base.")
        mode = "WRITE" if plan["external_write"] else "dry-run"
        print(f"APPLY ({mode}): create {len(plan['create_tables'])} table(s), {len(plan['create_fields'])} field(s); "
              f"skip {len(plan['skip_existing'])}; DRIFT {len(plan['drift'])}; {len(plan['manual_complex'])} complex (manual)")
        for t in plan["create_tables"]:
            print(f"  + TABLE {t}{'  -> ' + plan['new_table_ids'].get(t, '') if plan['new_table_ids'].get(t) else ''}")
        for f in plan["create_fields"]:
            print(f"  + FIELD {f['table']}.{f['field']} ({f['type']})")
        for d in plan["drift"]:
            print(f"  ⚠ DRIFT {d['table']}.{d['field']}: {d['detail']} — NOT changed, reconcile by hand")
        for f in plan["manual_complex"]:
            print(f"  ! MANUAL {f['table']}.{f['field']} ({f['type']}) — link/formula/lookup, set up by hand")
        if plan["new_table_ids"]:
            print("\nAdd these to the target tenant's FEISHU_PHASE2_* env:")
            for n, i in plan["new_table_ids"].items():
                print(f"  # {n} = {i}")
        return 0
    if args.command == "parity":
        tables = [t.strip() for t in args.tables.split(",")] if args.tables else None
        res = parity(args.source_base, args.target_base, tables, args.lark_cli)
        if res["in_parity"]:
            print("PARITY ✅ — target has every table/field the source defines")
        else:
            print(f"PARITY ✗ — target lags source: {len(res['missing_tables'])} table(s), "
                  f"{len(res['missing_fields'])} field(s), {len(res['drift'])} drift")
        for t in res["missing_tables"]:
            print(f"  - MISSING TABLE {t}")
        for f in res["missing_fields"]:
            print(f"  - MISSING FIELD {f['table']}.{f['field']} ({f['type']})")
        for d in res["drift"]:
            print(f"  ⚠ DRIFT {d['table']}.{d['field']}: {d['detail']}")
        if res["extra_tables"]:
            print(f"  (target also has {len(res['extra_tables'])} extra table(s) not in source — informational)")
        return 0 if res["in_parity"] else 1
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
