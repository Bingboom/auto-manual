# Orchestration module map: cloud-doc backport and source intake modules (§6, §7)

Status: active · Part of the [orchestration module map](../orchestration_module_map.md); its index lists the other
module families. Update this page in the same PR that moves a boundary here; do not add
module notes to the hub.

## 6. Cloud-Doc Backport Modules

The cloud-doc backport closed loop (fetch → diff → classify/route → write-back)
was decomposed from a single 4183-line `cloud_doc_backport.py` into focused
layers (debt-paydown, 2026-06), and since CQ-1.3 (2026-10) those layers live in
the `tools/backport/` package. Import from `tools.backport.<module>` and run
`python -m tools.backport.cloud_doc <command>`. The old `tools/cloud_doc_backport*.py`
compatibility shims were removed in CQ-1.5.

- [`tools/backport/cloud_doc.py`](../../../tools/backport/cloud_doc.py)
  - thin facade (~200 lines): re-exports every public symbol from the modules
    below + the `__main__` guard. Keep it re-export-only.
- [`tools/backport/model.py`](../../../tools/backport/model.py)
  - foundation: `Block` model, document fetch/normalization, markdown→block
    parsing, section selection. Imports only stdlib + `path_utils` (no cycle).
- [`tools/backport/util.py`](../../../tools/backport/util.py)
  - shared constants (schema versions) + scaffolding (counters, git-ref,
    timestamp, source-path resolution).
- [`tools/backport/routing.py`](../../../tools/backport/routing.py)
  - delta classification + routing (Class R / D / T / image / semantic) + `diff_blocks`.
- [`tools/backport/apply.py`](../../../tools/backport/apply.py)
  - guarded Class-R write-back (literal-first + block-fallback RST rewrite) + apply-report builders.
- [`tools/backport/render.py`](../../../tools/backport/render.py)
  - markdown report renderers (pure report-dict → markdown).
- [`tools/backport/transports.py`](../../../tools/backport/transports.py)
  - live Feishu source-table / TM transports + `--table-binding` parsing.
- [`tools/backport/reports.py`](../../../tools/backport/reports.py)
  - report builders (`build_report` + verify / source-table-suggestions / template-sync-proposal / review-run).
- [`tools/backport/pr.py`](../../../tools/backport/pr.py)
  - PR/git helpers (`gh` PR creation + 403 compare-url fallback, branch naming, `open_backport_pr_from_manifest`).
- [`tools/backport/args.py`](../../../tools/backport/args.py)
  - argparse surface + arg-interpretation helpers (`_parse_args`,
    `_value_index_from_args`, `_family_index_from_args`).
- [`tools/backport/commands.py`](../../../tools/backport/commands.py)
  - single-command runners: `_run_diff` / `_run_apply*` / `_run_review` /
    `_run_verify_review` / `_run_open_pr` / `_run_apply_source_table`.
- [`tools/backport/orchestration.py`](../../../tools/backport/orchestration.py)
  - multi-step flows: review-branch resolution, worktree sync, the
    render-baseline diff, sibling scope, the backport-PR flow, and the
    best-effort revision-ledger ingest hook
    (`AUTO_MANUAL_REVISION_LEDGER_PATH`; `off` disables). **Patch seams for
    review-branch tests live here**, not on the cli re-exports.
- [`tools/backport/cli.py`](../../../tools/backport/cli.py)
  - thin dispatcher: `main` + the compatibility re-export hub the facade
    imports from.

Layering (import direction, bottom → top): `model` → `util` → `routing` /
`apply` / `render` / `transports` / `reports` / `pr` → `args` → `commands` /
`orchestration` → `cli` → `cloud_doc` facade. A new extraction must import from the
**leaf modules**, never from the entry file (that would cycle), and the entry
file re-exports it.

Record-resolution + source-table write are in sibling modules:
[`tools/data/source_record_index.py`](../../../tools/data/source_record_index.py) (the
`source_record_index.json` sidecar: business key → Feishu `record_id`),
[`tools/token_resolution_map.py`](../../../tools/token_resolution_map.py) (value →
source_ref), [`tools/data/source_table_sync.py`](../../../tools/data/source_table_sync.py)
(exact-or-abstain F6 write).

Tests: `tests/test_backport_golden_corpus.py` (routing matrix),
`tests/test_source_table_sync_invariants.py` (F6 write-side fuzz),
`tests/test_backport_harness.py` (+ `tools/backport/harness.py`, offline
multi-edit integration), `tests/test_backport_noise_injection.py`,
`tests/test_backport_live_check.py` (+ `tools/backport/live_check.py`, operator
live round-trip).

Sync-env bootstrap (`sync-data` needs `FEISHU_PHASE2_*` + TM env): copy
[`scripts/hello_docs_binding.env.example`](../../../scripts/hello_docs_binding.env.example),
fill values (table/view IDs are discoverable per tenant via `lark-cli base
+table-list` / `+view-list`; a wiki-wrapped base resolves to its app_token via
`lark-cli wiki +node-get`), and check with
[`scripts/validate_required_env.sh`](../../../scripts/validate_required_env.sh).

## 7. Source Intake Modules

The source-intake closed loop converts structured specs/manual-source documents
into reviewable source-table candidates, then hands existing-row changes to the
same approval-gated source-table writer used by cloud-doc backport.

- [`tools/data/source_intake.py`](../../../tools/data/source_intake.py)
  - CLI entrypoint and command orchestration for `run`, `approve`, `apply`, and `verify`.
- [`tools/data/source_intake_extract.py`](../../../tools/data/source_intake_extract.py)
  - input acquisition and Markdown-table parsing from local Markdown, stdin, or Feishu/Lark cloud-doc text.
- [`tools/data/source_intake_model.py`](../../../tools/data/source_intake_model.py)
  - candidate schema constants, target-table names, hash helpers, and text normalization.
- [`tools/data/source_intake_runtime.py`](../../../tools/data/source_intake_runtime.py)
  - candidate extraction, snapshot enrichment, existing-row change-request building, and run/report writing.
- [`tools/data/source_intake_closure.py`](../../../tools/data/source_intake_closure.py)
  - P4-P7 closure reports: approval artifact, apply handoff report, labeled verification command results, and closure checklist.

The write boundary stays in [`tools/data/source_table_sync.py`](../../../tools/data/source_table_sync.py):
source intake may approve and invoke it, but does not own live Feishu write
semantics. Live transports are still constructed through
[`tools/backport/transports.py`](../../../tools/backport/transports.py)
so table-binding parsing and source-table GET/verify behavior stay shared.

Tests: [`tests/test_source_intake.py`](../../../tests/test_source_intake.py)
covers candidate extraction, snapshot enrichment, change-request bridging,
approval artifacts, dry-run/live-transport apply behavior, and CLI-level
P4-P7 closure.
