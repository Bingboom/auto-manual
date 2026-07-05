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
import csv
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
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    # reads emit JSON on stdout; some writes (record-upsert) emit it on stderr -> try both
    for text in (proc.stdout, (proc.stdout or "") + (proc.stderr or "")):
        try:
            return json.loads(text[text.index("{"):])
        except ValueError:
            continue
    return {"ok": False, "_raw": ((proc.stdout or "") + (proc.stderr or ""))[:200]}


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


def parity(
    source_base: str,
    target_base: str,
    table_filter: list[str] | None,
    lark_cli: str,
    ignore_prefixes: "tuple[str, ...] | list[str] | None" = None,
    ignore_names: "set[str] | list[str] | None" = None,
) -> dict:
    """Read-only structure diff between two tenants (e.g. dev vs prod).

    Reports what the SOURCE tenant has that the TARGET lacks (missing tables/fields) or
    has differently (drift). The TARGET may legitimately have *extra* tables (reported
    as informational, not a parity failure). Writes nothing.

    ``ignore_prefixes`` / ``ignore_names`` drop SOURCE-only scratch tables (e.g. the dev
    tenant's ``99_*`` experiment/archive tables, ``QC_Report``) from the comparison so a
    prod-lag alert isn't permanently red over tables prod is correct NOT to have.
    """
    ignore_prefixes = tuple(ignore_prefixes or ())
    ignore_names = set(ignore_names or ())

    def _ignored(name: str) -> bool:
        return name in ignore_names or any(name.startswith(p) for p in ignore_prefixes)

    src = export(source_base, table_filter, lark_cli)
    src["tables"] = [t for t in src["tables"] if not _ignored(t["name"])]
    plan = apply(src, target_base, write=False, lark_cli=lark_cli)
    src_names = {t["name"] for t in src["tables"]}
    extra = sorted(n for n in (set(plan["target_tables"]) - src_names) if not _ignored(n)) if table_filter is None else []
    return {
        "missing_tables": plan["create_tables"],
        "missing_fields": plan["create_fields"],
        "drift": plan["drift"],
        "manual_complex": plan["manual_complex"],
        "extra_tables": extra,
        "in_parity": not (plan["create_tables"] or plan["create_fields"] or plan["drift"]),
    }


# --- reference-data seed sync (Gap C) ---------------------------------------
# Structure rides `apply`/`parity`; this syncs the ROWS of small reference/config tables
# (rule library, dictionaries) that must match across tenants, idempotently by a business
# key. Business data (per-model spec/page rows) stays in its tenant and is NOT synced here.


def _resolve_table_id(base_token: str, table_name: str, lark_cli: str) -> str | None:
    tl = _lark(["base", "+table-list", "--base-token", base_token, "--format", "json", "--as", "bot"], lark_cli)
    for t in (tl.get("data", {}).get("tables") or tl.get("data", {}).get("items") or []):
        if t.get("name") == table_name:
            return t.get("id") or t.get("table_id")
    return None


def _field_types(base_token: str, tid: str, lark_cli: str) -> dict:
    fl = _lark(["base", "+field-list", "--base-token", base_token, "--table-id", tid, "--format", "json", "--as", "bot"], lark_cli)
    return {f.get("name"): (f.get("type") or "").lower() for f in (fl.get("data", {}).get("fields") or fl.get("data", {}).get("items") or [])}


def _norm_cell(v) -> str:
    """Canonical string for comparing a cell value across tenants / CSV."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else ""
    if isinstance(v, (int, float)):
        return str(int(v)) if float(v).is_integer() else str(v)
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, list):
        return "".join(_norm_cell(x) for x in v)
    if isinstance(v, dict):
        return str(v.get("text") or v.get("name") or v.get("value") or "")
    return str(v)


def _serialize_cell(v, ftype: str) -> str:
    """Record value -> CSV string (checkbox as True/False to match committed seeds)."""
    if ftype == "checkbox":
        return "True" if v in (True, 1, "true", "True", "1") else "False"
    return _norm_cell(v)


def _coerce_cell(value: str, ftype: str):
    """CSV string -> typed record value for writing (None for an empty cell)."""
    v = (value or "").strip()
    if v == "":
        return None
    if ftype == "checkbox":
        return v.lower() in ("true", "1", "yes", "✓")
    if ftype in ("number", "currency", "percent", "rating"):
        try:
            f = float(v)
            return int(f) if f.is_integer() else f
        except ValueError:
            return v
    return v


def _field_id_name_map(base_token: str, tid: str, lark_cli: str) -> dict[str, str]:
    """``{field_id: authoritative field name}`` from ``+field-list``.

    record-list returns column *display* names in ``fields``, which can diverge
    from the real field names (``+field-list``). Keying rows off the display
    names then makes ``_kv`` / ``seed_export`` read the wrong column -> empty ->
    updates get misclassified as creates. Rebuild names from field-list, the same
    authoritative source ``sync_data`` uses.
    """
    fl = _lark(["base", "+field-list", "--base-token", base_token, "--table-id", tid, "--format", "json", "--as", "bot"], lark_cli)
    items = fl.get("data", {}).get("fields") or fl.get("data", {}).get("items") or []
    mapping: dict[str, str] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        field_id = str(item.get("field_id") or item.get("id") or "").strip()
        name = str(item.get("field_name") or item.get("name") or "").strip()
        if field_id and name:
            mapping[field_id] = name
    return mapping


def _read_records(base_token: str, tid: str, lark_cli: str) -> tuple[list[dict], list[str]]:
    """Return ([row dict], [record_id]) for a table, following pagination.

    Rows are keyed by the authoritative field names (from ``+field-list`` via the
    record-list ``field_id_list``), not the record-list display names, which can
    diverge and misalign seed_export / seed_import against the real columns.

    Reference tables are usually small, but a single ``--limit 200`` call silently
    truncated any table past 200 rows: ``seed_export`` would drop the tail from the
    committed CSV and ``seed_import`` would classify those rows as ``create`` and
    duplicate them on every run (breaking the idempotency contract). Page with
    ``--offset`` / ``has_more`` so every row is seen.
    """
    id_name = _field_id_name_map(base_token, tid, lark_cli)
    rows: list[dict] = []
    rids: list[str] = []
    offset = 0
    limit = 200
    while True:
        args = [
            "base", "+record-list", "--base-token", base_token, "--table-id", tid,
            "--limit", str(limit), "--format", "json", "--as", "bot",
        ]
        if offset:
            args += ["--offset", str(offset)]
        data = _lark(args, lark_cli).get("data", {}) or {}
        display = data.get("fields") or []
        field_ids = data.get("field_id_list") or []
        if field_ids:
            # Rebuild column names from field-list; fall back to the display name
            # (then the raw id) per position when a field is not in the map.
            col_names = [
                id_name.get(str(fid)) or (display[i] if i < len(display) else str(fid))
                for i, fid in enumerate(field_ids)
            ]
        else:
            col_names = display  # older CLI without field_id_list: display names as-is
        page_rows = [dict(zip(col_names, row)) for row in (data.get("data") or [])]
        rows.extend(page_rows)
        rids.extend(data.get("record_id_list") or [])
        if not bool(data.get("has_more")):
            break
        if not page_rows:
            raise RuntimeError(f"record-list signaled has_more but returned no rows for table {tid}")
        offset += len(page_rows)
    return rows, rids


def seed_export(base_token: str, table_name: str, lark_cli: str) -> tuple[list[str], list[dict]]:
    """Snapshot a reference table's simple-field rows to (columns, rows) for a committed CSV."""
    tid = _resolve_table_id(base_token, table_name, lark_cli)
    if not tid:
        raise ValueError(f"table not found: {table_name}")
    ftypes = _field_types(base_token, tid, lark_cli)
    cols = [n for n, t in ftypes.items() if t in SIMPLE_TYPES]
    rows, _ = _read_records(base_token, tid, lark_cli)
    return cols, [{c: _serialize_cell(r.get(c), ftypes[c]) for c in cols} for r in rows]


def seed_import(base_token: str, table_name: str, seed_rows: list[dict], key: str, write: bool, lark_cli: str, prune: bool = False) -> dict:
    """Idempotently upsert reference rows into a target table, matched by the ``key`` column.

    Re-runnable: existing rows (by key) get only their changed simple cells updated, new
    keys are created, keys absent from the seed are reported (deleted only with ``prune``).
    Only simple writable fields are touched; formula/lookup/link are never written. An
    empty seed cell is left unset (it does not clear an existing value).
    """
    tid = _resolve_table_id(base_token, table_name, lark_cli)
    plan: dict = {"table_id": tid, "create": [], "update": [], "skip": [], "extras": [], "dup_keys": [], "pruned": [], "write": bool(write)}
    if not tid:
        plan["error"] = f"table not found: {table_name}"
        return plan
    ftypes = _field_types(base_token, tid, lark_cli)
    write_cols = [c for c in (seed_rows[0].keys() if seed_rows else []) if ftypes.get(c) in SIMPLE_TYPES]
    key_cols = [key] if isinstance(key, str) else list(key)

    def _kv(row: dict) -> tuple:
        return tuple(_norm_cell(row.get(c)) for c in key_cols)

    def _disp(kv: tuple) -> str:
        return " | ".join(kv)

    rows, rids = _read_records(base_token, tid, lark_cli)
    existing: dict = {}
    for r, rid in zip(rows, rids):
        kv = _kv(r)
        if kv in existing:
            plan["dup_keys"].append(_disp(kv))
        else:
            existing[kv] = (rid, r)
    seen: set = set()
    for row in seed_rows:
        kv = _kv(row)
        if not any(kv) or kv in seen:  # wholly-empty key -> skip; intra-seed dup -> first wins
            continue
        seen.add(kv)
        payload = {c: _coerce_cell(row.get(c), ftypes[c]) for c in write_cols}
        payload = {c: v for c, v in payload.items() if v is not None}
        if kv in existing:
            rid, trec = existing[kv]
            diffs = [c for c in write_cols if c in payload and _norm_cell(trec.get(c)) != _norm_cell(payload[c])]
            if diffs:
                plan["update"].append({"key": _disp(kv), "fields": diffs})
                if write:
                    _lark(["base", "+record-upsert", "--base-token", base_token, "--table-id", tid, "--record-id", rid,
                           "--json", json.dumps({c: payload[c] for c in diffs}, ensure_ascii=False), "--format", "json", "--as", "bot"], lark_cli)
            else:
                plan["skip"].append(_disp(kv))
        else:
            plan["create"].append(_disp(kv))
            if write:
                _lark(["base", "+record-upsert", "--base-token", base_token, "--table-id", tid,
                       "--json", json.dumps(payload, ensure_ascii=False), "--format", "json", "--as", "bot"], lark_cli)
    extra_kvs = [k for k in existing if k not in seen]
    plan["extras"] = sorted(_disp(k) for k in extra_kvs)
    if prune and write and extra_kvs:
        ids = [existing[k][0] for k in extra_kvs]
        for i in range(0, len(ids), 100):
            _lark(["base", "+record-delete", "--base-token", base_token, "--table-id", tid,
                   "--json", json.dumps({"record_id_list": ids[i:i + 100]}), "--yes", "--format", "json", "--as", "bot"], lark_cli)
        plan["pruned"] = list(plan["extras"])
    return plan


def promote(manifest: dict, seeds: list[dict], base_token: str, write: bool, lark_cli: str, prune: bool = False) -> dict:
    """One dev→prod step (Gap A): structure (``apply``) + reference data (``seed_import``)
    + the env delta, self-gated by a re-applied structure check. Dry-run unless ``write``.

    ``seeds`` is ``[{"table": str, "key": list[str], "rows": list[dict]}]`` (CSVs are
    loaded by the caller). Composes the finished apply/seed-import pieces; business data
    is never touched. Returns a report dict for the CLI to print.
    """
    result: dict = {"write": bool(write), "new_table_ids": {}, "seeds": [], "post_missing": {"tables": [], "fields": []}}
    first = apply(manifest, base_token, write=write, lark_cli=lark_cli)
    result["structure"] = first  # the original gap (what was missing / created on pass 1)
    new_ids = dict(first.get("new_table_ids") or {})
    if write:
        plan = first
        for _ in range(2):  # a freshly-created table may need a 2nd pass to add its fields
            if not plan["create_tables"] and not plan["create_fields"]:
                break
            plan = apply(manifest, base_token, write=True, lark_cli=lark_cli)
            new_ids.update(plan.get("new_table_ids") or {})
    result["new_table_ids"] = new_ids
    for s in seeds:
        sp = seed_import(base_token, s["table"], s["rows"], s["key"], write, lark_cli, prune=prune)
        result["seeds"].append({"table": s["table"], "plan": sp})
    if write:
        post = apply(manifest, base_token, write=False, lark_cli=lark_cli)
        result["post_missing"] = {"tables": post["create_tables"], "fields": post["create_fields"]}
    return result


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
    pa.add_argument("--ignore-table-prefix", action="append", default=[], metavar="PREFIX",
                    help="drop SOURCE tables whose name starts with PREFIX (repeatable; e.g. dev scratch '99_')")
    pa.add_argument("--ignore-table", action="append", default=[], metavar="NAME",
                    help="drop a SOURCE table by exact name (repeatable; e.g. 'QC_Report')")
    pa.add_argument("--fail-on", choices=["any", "missing"], default="any",
                    help="exit 1 on 'any' divergence (default) or only on 'missing' tables/fields "
                         "(drift still reported but not failed — for a prod-lag alert where dev may carry extra/dirty options)")
    pa.add_argument("--lark-cli", default="lark-cli")
    _add_routing(pa)

    se = sub.add_parser("seed-export", description="Snapshot a reference table's rows to a committed seed CSV (simple fields only).")
    se.add_argument("--base-token", default=os.environ.get("FEISHU_PHASE2_BASE_TOKEN"), help="source base token (default: $FEISHU_PHASE2_BASE_TOKEN)")
    se.add_argument("--table", required=True, help="reference table name to export")
    se.add_argument("--out", required=True, help="seed CSV output path (committed; rides the code mirror)")
    se.add_argument("--lark-cli", default="lark-cli")
    _add_routing(se)

    si = sub.add_parser("seed-import", description="Idempotently upsert a seed CSV into a TARGET table's rows, matched by --key. Dry-run unless --write.")
    si.add_argument("--base-token", required=True, help="TARGET (e.g. prod) base token")
    si.add_argument("--table", required=True, help="reference table name")
    si.add_argument("--seed", required=True, help="seed CSV path (e.g. bitable_schema/seed/<table>.csv)")
    si.add_argument("--key", required=True, help="business-key column(s) to match rows by; comma-separated for a composite key (e.g. 'Row_key,规格书字段')")
    si.add_argument("--write", action="store_true", help="apply the upserts (else dry-run plan)")
    si.add_argument("--yes", action="store_true", help="confirm the TARGET base is correct; REQUIRED together with --write")
    si.add_argument("--prune", action="store_true", help="also DELETE target rows whose key is absent from the seed (destructive)")
    si.add_argument("--lark-cli", default="lark-cli")
    _add_routing(si)

    pr = sub.add_parser("promote", description="One dev->prod step: apply structure + seed reference data + print the env delta, self-gated by a re-check. Dry-run unless --write.")
    pr.add_argument("--manifest", required=True, help="structure manifest (bitable_schema/manifest.json)")
    pr.add_argument("--seeds", default="bitable_schema/seeds.json", help="seed registry JSON listing reference tables/csv/key (default: bitable_schema/seeds.json)")
    pr.add_argument("--base-token", required=True, help="TARGET (e.g. prod) base token")
    pr.add_argument("--write", action="store_true", help="apply structure + seeds (else dry-run plan)")
    pr.add_argument("--yes", action="store_true", help="confirm the TARGET base is correct; REQUIRED together with --write")
    pr.add_argument("--prune", action="store_true", help="seed-import: delete target rows whose key is absent from the seed (destructive)")
    pr.add_argument("--lark-cli", default="lark-cli")
    _add_routing(pr)
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
        res = parity(args.source_base, args.target_base, tables, args.lark_cli,
                     ignore_prefixes=args.ignore_table_prefix, ignore_names=args.ignore_table)
        missing = bool(res["missing_tables"] or res["missing_fields"])
        fail = (not res["in_parity"]) if args.fail_on == "any" else missing
        if res["in_parity"]:
            print("PARITY ✅ — target has every table/field the source defines")
        elif not fail:
            print(f"PARITY ⚠ — 0 missing table/field; {len(res['drift'])} drift reported below "
                  f"(informational under --fail-on missing)")
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
        return 1 if fail else 0
    if args.command == "seed-export":
        if not args.base_token:
            print("bitable-schema: --base-token or $FEISHU_PHASE2_BASE_TOKEN required", file=sys.stderr)
            return 2
        cols, rows = seed_export(args.base_token, args.table, args.lark_cli)
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8-sig", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=cols)
            writer.writeheader()
            writer.writerows(rows)
        print(f"WROTE {out}  ({len(rows)} rows, {len(cols)} cols)")
        return 0
    if args.command == "seed-import":
        with open(args.seed, encoding="utf-8-sig") as fh:
            seed_rows = list(csv.DictReader(fh))
        key = [c.strip() for c in args.key.split(",") if c.strip()]
        write = bool(args.write and args.yes)
        plan = seed_import(args.base_token, args.table, seed_rows, key, write, args.lark_cli, prune=args.prune)
        if plan.get("error"):
            print(f"seed-import: {plan['error']}", file=sys.stderr)
            return 2
        if args.write and not args.yes:
            print("⚠ --write ignored: re-run with --write --yes once you've confirmed the TARGET base.")
        mode = "WRITE" if plan["write"] else "dry-run"
        line = (f"SEED-IMPORT ({mode}) {args.table} by {args.key}: "
                f"create {len(plan['create'])}, update {len(plan['update'])}, skip {len(plan['skip'])}, extras {len(plan['extras'])}")
        if plan.get("pruned"):
            line += f", pruned {len(plan['pruned'])}"
        print(line)
        for k in plan["create"]:
            print(f"  + CREATE {k}")
        for u in plan["update"]:
            print(f"  ~ UPDATE {u['key']}: {', '.join(u['fields'])}")
        if plan["extras"]:
            tail = " — pruned" if plan.get("pruned") else " — left as-is (use --prune to delete)"
            print(f"  ! EXTRAS in target, not in seed{tail}: {', '.join(plan['extras'][:10])}{' …' if len(plan['extras']) > 10 else ''}")
        if plan["dup_keys"]:
            print(f"  ⚠ DUPLICATE {args.key} in target (upsert ambiguous): {', '.join(sorted(set(plan['dup_keys']))[:10])}")
        return 0
    if args.command == "promote":
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        seeds = []
        if args.seeds and Path(args.seeds).exists():
            for s in json.loads(Path(args.seeds).read_text(encoding="utf-8")).get("seeds", []):
                with open(s["csv"], encoding="utf-8-sig") as fh:
                    rows = list(csv.DictReader(fh))
                seeds.append({"table": s["table"], "key": [c.strip() for c in s["key"].split(",")], "rows": rows})
        write = bool(args.write and args.yes)
        res = promote(manifest, seeds, args.base_token, write, args.lark_cli, prune=args.prune)
        st = res["structure"]
        print(f"PROMOTE ({'WRITE' if res['write'] else 'dry-run'}) -> {args.base_token}")
        if args.write and not args.yes:
            print("⚠ --write ignored: re-run with --write --yes once you've confirmed the TARGET base.")
        print(f"  [structure] tables +{len(st['create_tables'])}, fields +{len(st['create_fields'])}, "
              f"drift {len(st['drift'])}, complex/manual {len(st['manual_complex'])}")
        for t in st["create_tables"]:
            print(f"     + TABLE {t}")
        for f in st["create_fields"]:
            print(f"     + FIELD {f['table']}.{f['field']} ({f['type']})")
        for d in st["drift"]:
            print(f"     ⚠ DRIFT {d['table']}.{d['field']}: {d['detail']}")
        for f in st["manual_complex"]:
            print(f"     ! MANUAL {f['table']}.{f['field']} ({f['type']}) — set up by hand")
        print(f"  [reference data] {len(res['seeds'])} table(s):")
        for s in res["seeds"]:
            p = s["plan"]
            pruned = f", pruned {len(p['pruned'])}" if p.get("pruned") else ""
            dup = f"  ⚠ {len(set(p['dup_keys']))} DUP key(s)" if p.get("dup_keys") else ""
            print(f"     - {s['table']}: create {len(p['create'])}, update {len(p['update'])}, "
                  f"skip {len(p['skip'])}, extras {len(p['extras'])}{pruned}{dup}")
        print("  [env delta] add to the target FEISHU_PHASE2_* env:")
        if res["new_table_ids"]:
            for n, i in res["new_table_ids"].items():
                print(f"     # {n} = {i}")
        elif res["write"]:
            print("     (no new tables created)")
        else:
            print("     (dry-run: run --write --yes to create tables and emit their IDs)")
        if res["write"]:
            pm = res["post_missing"]
            if not pm["tables"] and not pm["fields"]:
                print("  [post-check] structure up to date ✅")
            else:
                print(f"  [post-check] ⚠ still missing {len(pm['tables'])} table(s), {len(pm['fields'])} field(s) — re-run promote")
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
