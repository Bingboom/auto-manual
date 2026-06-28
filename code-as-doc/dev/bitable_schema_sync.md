# Bitable Schema Sync (dev → prod tenant)

Updated: 2026-06-28

The repo's **code** already mirrors dev → prod (`auto-manual` →
[`Hello-Docs`](https://github.com/Bingboom/Hello-Docs)). This runbook does the same
for the Feishu **Bitable structure** so that adding a table or field in the dev tenant
becomes a recorded, replayable change instead of a manual one.

Tool: [`tools/bitable_schema.py`](../../tools/bitable_schema.py). Tests:
[`tests/test_bitable_schema.py`](../../tests/test_bitable_schema.py).

## Model

| concern | where it lives | shared or per-tenant |
| --- | --- | --- |
| **structure** (tables + fields, name-keyed, no IDs) | committed manifest `bitable_schema/manifest.json` | shared (one file, rides the code mirror) |
| **reference data** (e.g. the rule library rows) | committed seed `bitable_schema/seed/<table>.csv` | shared |
| **table/view IDs** | `FEISHU_PHASE2_*` env / GitHub Secrets | per-tenant (dev vs prod), never in git |
| **business data** (spec rows, etc.) | the Bitable itself | per-tenant, independent |

Two safety rules baked into `apply`:

- **Only-increment**: it creates missing tables/fields; it never deletes or alters
  existing ones. Dropping a table/field stays a deliberate manual act.
- **Complex fields are manual**: `link` / `formula` / `lookup` reference other
  tables/fields whose IDs differ per tenant, so `apply` reports them for manual setup
  instead of guessing. The current intake tables (`数据入库表`, `规格书字段映射规则`)
  are all simple types, so they apply fully.

## Flow

### 1. Dev — record the change (in `auto-manual`)

After adding/changing tables in the dev tenant:

```bash
set -a; source ~/.auto-manual-phase2.env; set +a
python3 tools/bitable_schema.py export \
  --tables "数据入库表,规格书字段映射规则" \
  --out bitable_schema/manifest.json
```

Omit `--tables` to snapshot the whole base. Commit the manifest (+ any seed CSV); the
git diff **is** the change record. Add a one-line note to
[`code_optimization_log.md`](../code_optimization_log.md). Open a PR to `auto-manual`.

For a reference table whose rows the prod tenant also needs (e.g. the rule library),
also commit a seed under `bitable_schema/seed/`.

### 2. Mirror — carry it to prod

The normal `auto-manual` → `Hello-Docs` mirror brings the manifest, seed, and tool to
the production repo. No extra step.

### 3. Prod — apply structure to the prod tenant

On the prod side, with the **prod** tenant's base token:

```bash
# dry-run first — prints "Target base: <token> (N tables)" so you can confirm the
# tenant, plus what would be created and any DRIFT (see below)
python3 tools/bitable_schema.py apply \
  --manifest bitable_schema/manifest.json --base-token <PROD_BASE_TOKEN>

# apply — --write is REFUSED without --yes (guards against pointing at the wrong base)
python3 tools/bitable_schema.py apply \
  --manifest bitable_schema/manifest.json --base-token <PROD_BASE_TOKEN> --write --yes
```

Two guards in `apply`:

- **base confirmation** — `--write` is ignored unless `--yes` is also passed; the run
  always prints `Target base: <token> (N existing tables)` first, so you verify the
  tenant before writing.
- **drift report** — if a field already exists in the target but with a different
  type / select-options / multiple flag than the manifest, it is reported as
  `⚠ DRIFT ... — NOT changed, reconcile by hand`. `apply` only ever *adds*; it never
  alters an existing field, so a real divergence is surfaced, not silently overwritten.

`apply --write --yes` prints the new prod table IDs. Add them to the prod
`FEISHU_PHASE2_*` env / GitHub Secrets if the code reads them by env (the intake tables
currently take their id as a CLI arg, so recording the id is enough). Re-running
`apply` is safe (idempotent: 0 created).

#### Cross-tenant from one machine (when you can't grant the bot edit rights)

A cross-tenant external share is **read-only**: the dev bot (and even the dev *user*
token) can read the prod base but `table-create` / `field-create` return
`code 91403 "you don't have permission"`. If you can't grant the bot edit rights on the
prod base, run the prod side through a **separate lark-cli profile** authed to the prod
tenant as its owner — the dev default profile is never touched:

```bash
# one-time: add a prod profile (the PROD tenant's own self-built app id+secret)
pbpaste | lark-cli profile add --name prod --app-id <PROD_APP_ID> --app-secret-stdin   # secret via stdin, not echoed
lark-cli --profile prod auth login --no-wait --json --domain base,wiki   # device flow -> open the URL, authorize
lark-cli --profile prod auth login --device-code <code>                  # complete after authorizing

# apply through that profile as the owner's USER token (the prod app's bot is usually
# not a base collaborator, so --identity user is the reliable choice)
python3 tools/bitable_schema.py apply \
  --manifest bitable_schema/manifest.json --base-token <PROD_BASE_TOKEN> \
  --profile prod --identity user --write --yes
```

`--profile` / `--identity` are accepted by `export`, `apply`, and `parity`. Never use
`lark-cli profile use` (it switches the global default); always pass `--profile prod`
per-command. Remove the profile with `lark-cli profile remove prod` when finished.

### 4. Prod — seed reference data

Import the committed seed rows with `+record-upsert`. Two gotchas the tooling already
handles or that you must mirror by hand:

- the payload is a **raw field map**, NOT wrapped in `{"fields": ...}`;
- convert checkbox columns to bool and number columns to int; an empty cell is `null`.

```bash
python3 - <<'PY'
import csv, json, subprocess, os
env={**os.environ, "LARK_CLI_NO_PROXY": "1"}
PROD="<PROD_BASE_TOKEN>"; TID="<prod rule-map table id>"
def conv(c, v):
    v = (v or "").strip()
    if c == "manual_facing": return v == "True"   # checkbox -> bool
    if c == "Line_order":    return int(v) if v else None   # number -> int
    return v or None
for r in csv.DictReader(open("bitable_schema/seed/规格书字段映射规则.csv", encoding="utf-8-sig")):
    m = {c: conv(c, r.get(c)) for c in r if conv(c, r.get(c)) is not None}
    subprocess.run(["lark-cli", "--profile", "prod", "base", "+record-upsert",
        "--base-token", PROD, "--table-id", TID,
        "--json", json.dumps(m, ensure_ascii=False), "--as", "user"], env=env)
PY
```

`upsert` with no record-id always **creates**, so re-running duplicates rows. To redo
cleanly, delete first — `+record-delete --json '{"record_id_list":[...]}' --yes` (the
`--yes` is required for this high-risk write; `record-list` returns the ids under
`data.record_id_list`, not `data.records`).

> **select fields:** a `select` field's options are stored in the manifest as a name
> list but must be written to lark-cli as objects `[{"name": ...}]`. `apply` converts
> this for you (`_field_for_write`); if you ever hand-write a select via `field-create`,
> use the object form or the field is silently dropped and the table is created with
> only a default `ID` column.

### 5. Prod — verify

```bash
python3 build.py sync-data --config configs/config.us.yaml --data-root data/phase2 --dry-run
python3 tools/schema_drift.py   # snapshot header parity (see REQUIRED_CSV_HEADERS)
```

## Tenant parity check (catch silent drift)

`apply` answers "is the target up to the *committed manifest*". `parity` answers the
sharper question "does the **prod tenant** still match the **dev tenant** live" — it
exports both and reports what prod lacks or has differently. Read-only; exits non-zero
when prod lags, so it can run as a scheduled / CI parity gate.

```bash
python3 tools/bitable_schema.py parity \
  --source-base <DEV_BASE_TOKEN> --target-base <PROD_BASE_TOKEN>
# PARITY ✅            -> prod has every table/field dev defines (extra prod tables are OK)
# PARITY ✗ + a list   -> MISSING TABLE / MISSING FIELD / ⚠ DRIFT  (exit 1)
```

Run it after a promotion, and on a schedule, so divergence between the two tenants is
surfaced instead of accumulating unseen.

## When you add a new table going forward

1. Create it in the **dev** tenant.
2. `export` → commit manifest (+ seed if reference data) → PR → log.
3. On prod: `apply` (dry-run → `--write`) → wire the new ID into the prod env → seed → verify.

Structure changes now ride the code mirror; the only prod-side action is one `apply`.
