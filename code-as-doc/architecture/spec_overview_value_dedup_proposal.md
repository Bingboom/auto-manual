# Proposal: De-duplicate spec values across `Spec_Master` and `page_placeholders`

Status: **design decided — Option A (夏冰, 2026-06-07)**; implementation pending · Trigger: 夏冰 ("这俩表要确保数据没有重复维护")

## 1. Problem

Two phase2 source tables redundantly maintain the **same per-port electrical spec value, per language**:

- `03_内容源_规格参数明细` = **Spec_Master** (`tblTw54UzV4ry5VD`) — the spec-table rows (`Page = specifications`).
- `03_内容源_页面占位参数` = **page_placeholders** (`tblhckTT7PfVBsuG`) — the product-overview callouts (`Page = Product overview`).

For each physical port/output, **both** tables store its localized value. Editing a value means editing two tables in lockstep; miss one → drift or wrong output. This is **active, not theoretical**:

- V2 changed `DC8020-Ports`→`DC8020-Anschlüsse` in Spec_Master, but the same term lived again in page_placeholders (`DC-Eingang (2×DC8020-Ports)`) and was missed — only `scan_residuals.py` caught it.
- Independent **drift already exists** (JE-2000F_EU, `Value_de`):
  - `ac_output`: Spec_Master `… 2200 W Nennleistung insgesamt` vs ph `… 2200 W Nennleistung`
  - `ac_input`: Spec_Master `220-240 V~ 50 Hz …` vs ph `220 V-240 V~ 50 Hz …`

## 2. Scope (measured)

JE-2000F_EU: **5 Row_keys appear in both tables** — `ac_input`, `ac_output`, `dc12_port`, `usb_a`, `usb_c`. By `Value_de`: **3 identical** (`usb_c` 30W+100W, `dc12_port`, `usb_a`), **2 already drifted** (`ac_input`, `ac_output`). Multiply by the EU family (JE-1000F / JE-2000E / JE-2000F) × 6 languages. Labels (e.g. `2 × DC8020-Anschlüsse`, `Véhicule`) overlap too.

## 3. Goal

Single source of truth: each port's spec **value** is maintained **once** (in Spec_Master); the overview callout **derives** it — no second copy to keep in sync.

## 4. What to de-duplicate (and what not)

- **VALUE** (electrical spec, e.g. `100 W max., 5 V⎓3 A, 9 V⎓3 A, …`) — verified **identical** across the two tables → de-duplicate. This is the win.
- **LABEL** (spec `1 × USB-C-Ausgang 100 W` vs overview `USB-C 100 W-Ausgang`) — differs by format/context; **not** a pure duplicate. Out of scope for v1 (leave per-table, or template-derive later).

## 5. Design options

### Option A — Feishu lookup (recommended)
page_placeholders callout `Value_<lang>` becomes a **lookup** of the matching Spec_Master row's `Value_<lang>`, matched by `document_key` + `Row_key` + `Slot_key` — the exact mechanism just shipped for `Row_key` / `Slot_key` (`lark-cli base +field-create` with a `{type: lookup, from, select, aggregate, where}` payload).
- Single source = Spec_Master; ph reflects automatically.
- No values hard-coded in code (the reason Option B was rolled back).
- Reuses a proven, verified pattern; value stays editable in Spec_Master and visible (derived) in ph.

### Option B — Build-time composition
The overview recipe pulls each callout value from Spec_Master at build; page_placeholders declares only structural intent (which Row_keys + the overview-specific label).
- ⚠️ **History**: this used to exist (`assembly_pilot` / `_LAYOUTS`) and was rolled back in PR #295/#296 — *because the part names/values were hard-coded in Python*, not because composition is wrong. A clean, data-driven composition is viable but is a larger build change.

**Decision: Option A** (夏冰, 2026-06-07) — lower risk, data-driven, reuses the shipped lookup machinery. Option B is **rejected** for v1: build-time composition was already rolled back once (#295/#296) due to hard-coded values; Option A keeps the source data-driven and avoids re-introducing that debt.

## 6. Prerequisite — already in place

The controlled `Slot_key` field (shipped 2026-06-07) is the enabler: `usb_c` has two ports (30W/100W) under one `Row_key`, so a per-port lookup **must** match on `Slot_key` to pull the correct value for each. Without distinct Slot_keys this dedup would be impossible. ✓ Done.

## 7. Migration plan

1. **Reconcile drifted values first** (`ac_input`, `ac_output`, …): choose the correct value, make both tables agree — so the lookup source is correct before switching.
2. **Quantify all-model overlap**: scan every EU model for shared Row_keys; classify value-identical vs label-only.
3. **Add `Value_<lang>_ref` lookups** in page_placeholders referencing Spec_Master (`document_key` + `Row_key` + `Slot_key`); verify each returns the Spec_Master value.
4. **Swap** (mirror the Slot_key swap): rename text `Value_<lang>` → `Value_<lang>_legacy`, promote the lookup to `Value_<lang>`; keep legacy as backup.
5. **Verify**: build the overview (callouts render the Spec_Master value) + `sync-data` (reads the lookup the same way it already reads `Row_key`).

## 8. Risks / considerations

- Lookup match key **must include `Slot_key`** (usb_c per-port) — enabled.
- **Label vs value**: v1 dedupes values only; labels stay per-table.
- **Sync**: ph `Value`-as-lookup is read identically to the existing `Row_key` lookup — proven this session (sync + build verified).
- **Field volume**: 6 languages × N shared Row_keys × ref fields — script the field creation (as done for `Slot_key`).
- Keep `*_legacy` text backups through the migration; delete only after a clean build.

## 9. Recommendation

Adopt **Option A**, **EU family + values first**. Register as a workstream in `code-as-doc/optimization_project.md`; effort is modeled on the just-completed `Slot_key` dictionary+lookup work (schema via `lark-cli base +field-create`, a migration script, then build/sync verification). Labels and non-EU regions are a possible v2.
