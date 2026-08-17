---
name: spec-sheet-structured-intake
description: Turn a product spec sheet (产品规格书, PDF/Markdown) into reviewable structured rows and ingest them into the Feishu phase2 source tables (规格参数明细 specs + 页面占位参数 placeholders), per region/language. Use for the repeated structured-intake lane when onboarding a model/region (e.g. JE-2000E KR), and for a revised spec that must be diffed against an existing target. Extract via rules, gate against a sibling, generate one staging batch, get human confirmation, then clone-create or diff-update both source tables followed by sync-data + build. Forward/entry counterpart of cloud-doc backport (the return path). NOT for routine reviewed-wording edits, translation memory, or single-value tweaks.
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
  + completeness gate), `stage-plan` (sibling rows + target differences → one review/payload batch),
  and `run`/`approve`/`apply`/`verify` (Markdown candidate → approval-gated update).
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
   `--reference` runs the **completeness gate** (see below), and the gate is **mandatory by
   default**: running spec-extract without `--reference` is an error unless you pass
   `--skip-completeness` explicitly (a silent skip is exactly the QC gap that once let a
   candidate set look complete while missing sibling rows). Unmatched/abstained fields land as
   `needs_review` — never guessed.
3. **Completeness pre-gate (BOTH tables).** A spec sheet only yields the SPECIFICATIONS rows.
   A full manual also needs **页面占位参数** placeholders (Product overview port/button labels,
   operation-guide values, storage temps). Gate the candidate set against the same product's
   already-ingested sibling (`JE-2000E_US` for `JE-2000E_JP`, or the JP sibling for a new JP manual):
   missing logical rows = a real gap to fill before ingest.
4. **Generate one repeatable staging batch.** Do not hand-compose rows. Run `stage-plan` with
   the complete chosen sibling exports and a small override file containing
   only target differences. It clones the sibling's spec + placeholder structure, requires exact
   `Page + Section + Row_key + Slot_key + Line_order` coverage, carries localized columns together,
   marks unproven inherited values `⚠️需确认`, and emits:
   `spec_intake_staging_plan.json`, `spec_intake_staging_payload.json`, and
   `spec_intake_staging_review.md`. It never writes Feishu.
5. **Stage, then STOP for human confirmation (hard gate).** Batch-create the generated payload in
   the 入库暂存表 (`tblIi0BEufjvGLIU`), report the read-back count + filtered view, and wait.
   Only rows the operator explicitly confirms (「确认」/「入库」, per row or per batch — numbered
   picks count) are eligible to ingest. Jumping from extraction straight to formal source tables
   is forbidden.
6. **Ingest into BOTH source tables (CREATE = clone a sibling):** `规格参数明细` (Page=specifications)
   + `页面占位参数` (Page≠specifications). See "Ingest by cloning" below.
7. **Close + verify:** `python build.py sync-data --config <cfg> --sync-scope params`, then
   `python build.py check --config <cfg> --model <CANONICAL> --region <REGION>`, then a `rst`/`html`
   build to eyeball.

## Repeated-intake fast path (default)

Once the rule export and sibling JSON are available, the mechanical portion should take about
**3–5 minutes before human review**. Schema creation, new-language registration, translation, and
formal-table approval are outside that repeat-run timing.

```bash
python tools/source_intake.py spec-extract \
  --input <spec.pdf> --rules <rules.json> \
  --document-key JE-2000E_KR --region KR \
  --reference <sibling-spec.json> --out reports/source_intake/JE-2000E_KR

python tools/source_intake.py stage-plan \
  --spec-candidates reports/source_intake/JE-2000E_KR/spec_intake_candidates.json \
  --spec-sibling <sibling-spec.json> \
  --placeholder-sibling <sibling-placeholders.json> \
  --overrides <target-differences.json> \
  --document-key JE-2000E_KR --localized-lang ko \
  --out reports/source_intake/JE-2000E_KR
```

Minimal override shape (use only rows that differ from the sibling):

```json
{
  "schema_version": "source-intake-staging-overrides/v1",
  "rows": [{
    "key": {
      "Page": "specifications",
      "Section": "INPUT PORTS",
      "Row_key": "ac_input",
      "Slot_key": "",
      "Line_order": 1
    },
    "fields": {
      "Value_source": "220 V~240 V, 60 Hz, 10 A Max",
      "Value_ko": "220 V~240 V, 60 Hz, 10 A 최대",
      "note": "confirmed from KR spec"
    }
  }]
}
```

Review the generated Markdown, then write the staging payload and read it back. The current CLI
contract is `create_records`; use the business-plane bot explicitly and keep `@file` relative to
the repo cwd:

```bash
lark-cli --profile prod base +record-batch-create --as bot \
  --base-token LD3lb4G1ua4GOVs1vxAc9W2enje --table-id tblIi0BEufjvGLIU \
  --json @reports/source_intake/JE-2000E_KR/spec_intake_staging_payload.json

lark-cli --profile prod base +record-list --as bot \
  --base-token LD3lb4G1ua4GOVs1vxAc9W2enje --table-id tblIi0BEufjvGLIU \
  --filter-json '{"logic":"and","conditions":[["document_key","==","JE-2000E_KR"]]}' \
  --limit 200 --format json
```

Any `stage-plan` structure mismatch, missing localized counterpart, or ambiguous extractor match is
an intentional stop, not a prompt to repair dozens of rows by hand.

## Hard gates (each QC'd in by the operator after a real miss)

1. **Staging-write-first.** Candidates go into the staging table and get operator confirmation
   BEFORE any source-table write — never extraction → ingest directly (workflow step 5).
2. **Sibling reference = real structure.** `spec-extract` always runs with `--reference`, and the
   sibling is chosen by target: single-language-English regions (AU-style) → the EU sibling's
   confirmed English rows; JP → the JP sibling (phrasing + structure); KR → the KR sibling
   (it carries the `_ko` localized columns). When the generic rule table (`规格书字段映射规则`)
   and the real sibling diverge on Slot_key / Line_order / filler rows, the **sibling wins** —
   align the staged rows to it (real divergences caught this way: usb_c slot 140w/LO1 in the
   rules vs 100w/LO2 in EU reality; a dc_expansion_port filler row EU never had).
3. **Value language = `Source_lang`.** From a Chinese spec sheet, manual/needs_review rows keep
   the Chinese ONLY in 规格书原值 — 手册值 stays empty for the approver. English manual values
   are written by copying the sibling's confirmed wording (EU `Value_source`), not by
   transforming the Chinese; deviate only where the spec sheet genuinely differs, and mark
   those ⚠️需确认 with the evidence.
4. **Cloned residuals get an explicit list.** After clone-ingest, every value inherited from the
   sibling that the spec sheet did not confirm (energy-saving/standby timings, …) is reported
   as "inherited, unconfirmed" — cloned ≠ confirmed. Regional electrical rows
   (ac_input / ac_output / bypass: voltage, frequency, rated current) are per-region facts —
   verify each against the spec sheet, never trust the clone (a 50 Hz AU row cloned into a
   60 Hz KR target is a printed defect). Close the batch by tidying the staging table
   (fill 入库结果; only pending batches stay staged).
5. **Localized value columns move together.** KR/JP/CN rows carry `Value_<lang>` /
   `Row_label_<lang>` beside `Value_source`, and the localized manual renders the localized
   column. ANY spec correction on such a target updates BOTH columns — localized formatting
   included (정격, not "max", in Korean) — then the review branch is re-seeded (Start Review)
   so the build picks the new values up. `Value_source` alone leaves the localized spec page
   printing the old value (JE-1000H_KR, 2026-07-27).
6. **Re-ingest and revisions are diffs, not rewrites.** Before ANY ingest, check whether the
   target `document_key` already has rows (`record-list --filter-json` on BOTH source tables) —
   a blind clone onto an existing target doubles the row set (JE-1800B_JP, 2026-07-06). Zero rows
   means CREATE by sibling clone; a complete existing target means diff-update only. A half-failed
   target requires an explicit operator-approved cleanup/rebuild decision — never infer deletion
   from a partial query. A revised spec sheet (rev A0 → A1) is diffed against the ingested rows
   and applied incrementally — never re-cloned over live rows.

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

- `python3 -m unittest tests.test_source_intake_rules tests.test_source_intake_completeness tests.test_source_intake_staging`
- `python3 -m ruff check tools/source_intake_rules.py tools/source_intake_completeness.py tools/source_intake_staging.py tools/source_intake.py`
- End to end: `spec-extract` → `stage-plan` → review → ingest → `python build.py check --config <cfg> --model <CANONICAL> --region <REGION>` → `python build.py html ...`
