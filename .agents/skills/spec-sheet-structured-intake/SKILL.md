---
name: spec-sheet-structured-intake
description: Turn a product spec sheet (产品规格书, PDF/Markdown) into reviewable structured rows and ingest them into the Feishu phase2 source tables (规格参数明细 specs + 页面占位参数 placeholders), per region/language. Use when onboarding a NEW model or region (e.g. JE-2000E US/JP) end to end — extract via the field-mapping rule library, gate completeness against a sibling target, get human confirmation, clone-ingest into both source tables, then sync-data + build. Forward/entry counterpart of cloud-doc backport (the return path). NOT for routine reviewed-wording edits, translation memory, or single-value tweaks.
---

# Spec Sheet → Structured Data Intake

The closed loop that fills the build's structured source from a 产品规格书:

```
规格书(PDF/MD) → 规则抽取(region-aware) → 完整性前置门(对照姊妹机) → 人审确认
             → 入库到两张源表(规格参数明细 + 页面占位参数) → sync-data → check → build
```

This is the **entry** half; `tools/cloud_doc_backport.py` is the **return** half. Both
share the same spine: `data/phase2/source_record_index.json` sidecar, the
`source-table-change-request/v1` contract, and the drift-guarded
`tools/source_table_sync.py` writer.

## Tools (committed)

- `tools/source_intake.py` — CLI. Subcommands: `spec-extract` (PDF/MD → candidates via rules,
  + completeness gate), `run`/`approve`/`apply`/`verify` (Markdown candidate → approval-gated write).
- `tools/source_intake_rules.py` — the rule engine: `FieldRule`, region-aware `apply_op`
  (capacity / weight / dims / temp / cycle_life / dc12 / passthrough / default / manual / exclude),
  `extract_candidates`, `display_width` (East-Asian width).
- `tools/source_intake_completeness.py` — `check_completeness` (field / logical-row / region gate).
- Rule library: Feishu Base table **`规格书字段映射规则`** (the durable, operator-editable rule set).
  Export it to JSON (a list of rule dicts) for `spec-extract --rules`.

## Default workflow

1. **Identify the canonical model + region.** A marketing model name (e.g. `JHP-2000A`, US) maps to
   a **canonical** model (e.g. `JE-2000E`). `document_key` MUST use the canonical model + region
   (`JE-2000E_US`), or the build's symbols/recipes/config won't match. The marketing name goes in
   the `Model No.` **value**, not the key.
2. **Extract candidates** (region-aware: US → dual imperial/metric, JP/EU → metric):
   ```bash
   python tools/source_intake.py spec-extract \
     --input <规格书.pdf|.md|cloud-doc-url> --rules <rules.json> \
     --document-key JE-2000E_JP --region JP \
     --reference <sibling_rows.json> --out reports/source_intake/<run>
   ```
   `--reference` runs the **completeness gate** (see below). Unmatched/abstained fields land as
   `needs_review` — never guessed.
3. **Completeness pre-gate (BOTH tables).** A spec sheet only yields the SPECIFICATIONS rows.
   A full manual also needs **页面占位参数** placeholders (Product overview port/button labels,
   operation-guide values, storage temps). Gate the candidate set against the same product's
   already-ingested sibling (`JE-2000E_US` for `JE-2000E_JP`, or the JP sibling for a new JP manual):
   missing logical rows = a real gap to fill before ingest.
4. **Human confirmation.** The operator reviews the candidates (especially `needs_review`) in the
   staging table and ticks a confirm field. Only confirmed rows are eligible to ingest.
5. **Ingest into BOTH source tables (CREATE = clone a sibling):** `规格参数明细` (Page=specifications)
   + `页面占位参数` (Page≠specifications). See "Ingest by cloning" below.
6. **Close + verify:** `python build.py sync-data --config <cfg> --sync-scope params`, then
   `python build.py check --config <cfg> --model <CANONICAL> --region <REGION>`, then a `rst`/`html`
   build to eyeball.

## Region & language (critical)

- **US** manuals: dual unit (`About 41.45 lbs/18.8 kg`, `14.4 × 10.0 × 10.7 in / 36.6 × 25.5 × 27.2 cm`),
  English. `--region US`.
- **JP** manuals: `Source_lang=ja`, **Japanese values AND labels**, and a JP-specific structure
  (size+weight combined into one `サイズ＆重量` row; Japanese port labels like `シガーソケット出力ポート`).
  Do NOT translate the US English clone. **Clone the JP sibling** (`JE-1000F_JP`) for phrasing +
  structure, then substitute the target model's values. `--region JP` gives metric units; the
  Japanese phrasing comes from the sibling, not the rule engine.
- EU: metric, per-language `Value_<lang>` columns.

## Ingest by cloning (the CREATE path)

`source_intake.py apply` only **updates** existing rows. To create a NEW model/region, **clone the
sibling's formal rows** (which already carry the correct structure + links), flip the document link,
and substitute values:

- For each sibling row in `规格参数明细` / `页面占位参数`: copy the writable columns + link fields,
  set `Document_key_link` → the target's `Document_key` dimension record, set `Value_source` /
  `Row_label_source` from the confirmed candidate, `Source_lang` to the target lang.
- Choose the sibling by what you need: **same product, other region** (e.g. `JE-2000E_US`) gives the
  exact row set; **same region/language** (`JE-1000F_JP`) gives JP phrasing + JP structure. For a JP
  manual, clone the JP sibling.

## Gotchas (hard-won — read before touching Bitable)

- **record-list caps at 200 rows.** Reading a large table unfiltered silently truncates → use
  `--filter-json '{"logic":"and","conditions":[["document_key","==","JE-2000E_JP"]]}'`. A delete/verify
  built on a truncated read will miss rows.
- **`document_key` and `source_row_key` are FORMULA fields; `Row_key`/`Slot_key` are LOOKUPS.** You
  cannot write them directly. Set the **link** fields (`Document_key_link`, `Row_key_link`,
  `Slot_key_link`) — the formula/lookup columns recompute. (This is why cloning a sibling row, which
  already has the links, is the reliable CREATE path.)
- **A `Document_key` dimension record must exist** for the target (`02_主数据_Document_key`,
  formula = Model link + Region link). Create it (operator-gated) before the spec rows if missing;
  find the Region/Model link ids by reading an existing sibling doc-key.
- **Model identity:** marketing name ≠ canonical model. Use the canonical model in `document_key`
  (build matches it); marketing name → `Model No.` value only.
- **Footnotes / symbols / LCD `Model` is a multi-select.** Enrolling a new model = adding it to the
  `Model` option of the shared rows. `Spec_Footnotes.Footnote_order` must be unique per target but is
  shared across models via the multi-select → a generic footnote (e.g. `max_charge_power`) can collide
  on order with another (`ac_bypass`); give the new model a dedicated footnote+order, or drop the
  optional ref.
- **RST title underlines use East-Asian DISPLAY width** (full-width CJK = 2 columns). A JP title's
  underline must be ≥ its display width (`source_intake_rules.display_width`), or Sphinx warns
  "Title underline too short". Underlines may be over-long safely.
- **Completeness must cover BOTH tables.** Checking only `规格参数明细` misses the ~29 `页面占位参数`
  placeholder rows; the build then fails with `MISSING_REQUIRED_SPEC_ROW` for product-overview slots.
- **Exact-or-abstain everywhere.** A value the rules can't transform, a row whose footnote/link can't
  resolve, an ambiguous match → `needs_review` / skip, never a guess.

## Validation

- `python3 -m unittest tests.test_source_intake_rules tests.test_source_intake_completeness`
- `python3 -m ruff check tools/source_intake_rules.py tools/source_intake_completeness.py tools/source_intake.py`
- End to end: `spec-extract` → review → ingest → `python build.py check --config <cfg> --model <CANONICAL> --region <REGION>` → `python build.py html ...`
