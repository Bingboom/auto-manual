# Content Quality Rules

> The invariants that keep the manual's **content** correct — across the Feishu
> source tables, the Translation Memory, and the per-language templates — and the
> lint that enforces them. Companion to the data-model reference
> ([`architecture/phase2_source_tables_reference.md`](architecture/phase2_source_tables_reference.md)).
> Enforced by [`tools/content_lint.py`](../tools/content_lint.py).

## 1. Why this exists

Content bugs in this repo were historically caught **late and by eye** — a reviewer
opening the built `.docx` and noticing a wrong word (e.g. status words not bold, an
Italian line still reading `On:`). That is reactive and expensive, and it misses
edits made **directly in Feishu** (the source of truth), which never pass through a
repo PR.

A healthy loop **shifts the checks left** — into the Snapshot and Page-Assembly
layers (System Evolution Strategy [§4](architecture/System%20Evolution%20Strategy.md)) —
and runs them **continuously**, so a defect is caught at `sync`/`build` time rather
than at release. The principle:

```
define invariant → detect (automated) → locate the source row → fix AT SOURCE
        → verify (sync + build + re-lint) → capture (escaped bug → new rule)
                              ▲
        run the same lint against the LIVE source on a schedule ┘
```

Two standing disciplines make the loop close:

- **Fix at source, never the output.** Edit the online Feishu table / TM / template,
  never the synced CSV or the built file (the CSV is a sync artifact — re-edited
  values are clobbered on the next sync).
- **Capture-as-check.** Every defect a human finds becomes a standing lint rule, so
  it cannot recur. The rules below were each seeded by a real 2026-06-07 bug.

## 2. The lint

```bash
python tools/content_lint.py --data-root data/phase2 [--langs fr,es,de,it,uk]
```

It runs against the **exported snapshot** (`data/phase2/*.csv`) — the same inputs
the build consumes — so it is deterministic and CI-friendly. `FAIL`-level findings
set exit code `1`; `WARN`-level findings are surfaced but do not fail the gate.
Use `--json` when another tool or report writer needs the machine-readable
`content-qc-report/v1` output. JSON findings include a best-effort `source_ref`
from snapshot keys; `record_id` remains `null` until a later exact resolver lands.

For a local operator artifact, add `--write-report`:

```bash
python tools/content_lint.py --data-root data/phase2 --json --write-report
```

This writes `findings.json` and `report.md` under `reports/content_qc/<run-id>/`.
Use `--report-dir <path>` when the report should go to a specific directory.
Report writing is local-only and does not write Feishu rows or block Word
delivery beyond the lint's existing `FAIL` exit code.

## 3. Rules

Each rule maps to a quality dimension and a source location to fix.

### R1 — Status-word consistency · `FAIL` · dimension: TM + source table
- **Rule:** every line-leading state word in an LCD description (`On:` / `Off:` /
  `Blink:` and localized forms) must match the canonical status word for that
  language — the per-language column of the `是否为 status word = Y` rows in
  `Translation_Memory` (see reference §3, §4.7). The lint uses the renderer's own
  matcher (`_match_status_prefix`), so it checks exactly what the build will bold.
- **Catches:** content using a word not in the table → silently un-bolded
  (fr `Allumé` vs an old table value `Activé`; de `Blinkt` vs `Blinken`).
- **Fix at source:** conform the LCD `icon_desc_<lang>` to the canonical word, or —
  when the table holds the worse term — correct the table (the authority) and keep
  content in step. Never leave the two diverged.

### R2 — English residue · `FAIL` · dimension: source table
- **Rule:** no English state word (`On:` / `Off:` / `Blinking` / `Flashing`) may
  appear in a non-English localized column (LCD, troubleshooting, footnotes, notes).
- **Catches:** untranslated leftovers (Italian LCD lines that still read `On:`/`Off:`).
- **Fix at source:** translate the prefix in the online table (e.g. it `On:`→`Acceso:`).

### R3 — Slot-key collision · `FAIL` · dimension: source table
- **Rule:** every `spec_row_key` in `Spec_Master.csv` must be unique. Two rows that
  collapse to one key clobber each other (a blank `Slot_key` defaults to `main`).
- **Catches:** the usb_c 100W row dropping because both usb_c rows had a blank
  `Slot_key` → identical `…usb_c__main`.
- **Fix at source:** assign a distinct controlled `Slot_key` (30w/100w/…) from the
  `02_主数据_Slot` dictionary (reference §1.2).

### R4 — Spec ↔ overview drift · `WARN` · dimension: source table
- **Rule (heuristic):** when the same `(document_key, Row_key)` carries a value on
  both the specifications page and the product-overview page, the two should share a
  value. No shared value = drift candidate (the two tables are maintained separately).
- **Catches:** the overview callout holding a stale or abbreviated copy of a spec
  value (e.g. EU `ac_output` overview `…1500 W Rated` vs spec `…1500 W in Total, 3000 W Surge`).
- **Fix at source / structural:** reconcile the values; the durable fix is the
  value-dedup project ([`architecture/spec_overview_value_dedup_proposal.md`](architecture/spec_overview_value_dedup_proposal.md)),
  which makes the overview *derive* the spec value so it cannot drift. `WARN`-level
  because the match is approximate (label callouts share a `Row_key` with values).

### R5 — Translation-Memory duplicate · `FAIL` · dimension: TM
- **Rule:** the status-word snapshot must have a unique `en` key. A duplicate row can
  win the sync's TM index and re-introduce a stale translation.
- **Catches:** the `ENVIRONMENTAL OPERATING TEMPERATURE` duplicate that re-surfaced an
  old title after the correct row was already fixed.
- **Fix at source:** reconcile and delete the duplicate TM row.
- **Limitation:** the snapshot only carries the status-word TM rows; full live-TM
  duplicate detection is the scheduled online extension (§4).

## 4. Running the loop (where the lint should fire)

1. **Build gate** — call `content_lint` from `build.py check` so no release bundle is
   produced over failing content.
2. **CI / PR** — run it (it is already CI-friendly) alongside `unittest` and
   `check_doc_link_integrity`, so template/data changes are gated.
3. **Scheduled against the live source** — the highest-value addition: editors change
   Feishu directly, bypassing PRs, so a scheduled job (via the build queue or cron)
   that syncs and lints the **live** tables turns "edited in Feishu" → "caught" from
   *next release* into *same day*. This is where full live-TM duplicate detection
   (R5's extension) belongs.

## 5. Roadmap — checks to add

- **Template multilingual lint** (quality dimension ③, not yet covered here):
  per-language `.rst` parity against `page_shared/en/`, `|TOKEN|` placeholder
  resolution for every language, and the reviewer rules (uk Cyrillic units, accents,
  casing) as lint rules.
- **Controlled-vocabulary & referential integrity:** every `Row_key`/`Slot_key` in
  content exists in its dictionary; every `*_footnote_refs` resolves.
- **Translation coverage:** every source string used in `Manual_Copy_Source` has a
  complete TM translation for each shipped language (no silent fallback to English).
- **Full live-TM duplicate detection** (online mode of R5).

Register new checks here and in
[`optimization_project.md`](optimization_project.md) as they land; add a maintenance
record to [`code_optimization_log.md`](code_optimization_log.md) when a workstream
completes.

The active rollout plan is
[`dev/closed_loop_qc_implementation_plan.md`](dev/closed_loop_qc_implementation_plan.md).

## 6. References

- Data model & fields: [`architecture/phase2_source_tables_reference.md`](architecture/phase2_source_tables_reference.md)
- Long-term layers & stages: [`architecture/System Evolution Strategy.md`](architecture/System%20Evolution%20Strategy.md)
- Drift's structural fix: [`architecture/spec_overview_value_dedup_proposal.md`](architecture/spec_overview_value_dedup_proposal.md)
- The lint: [`tools/content_lint.py`](../tools/content_lint.py)
