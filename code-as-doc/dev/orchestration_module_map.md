# Orchestration Module Map

Updated: 2026-06-25

This file records the current module boundaries for the repo's main workflow entrypoints.
Use it as the living map for "where should this logic go?" after the build, quality, release, and queue decomposition waves.

This is not the user workflow guide.
For day-to-day commands, use:

- [`code-as-doc/build_doc_guide.md`](../build_doc_guide.md)
- [`user-guide/hello_auto-doc.md`](../../user-guide/hello_auto-doc.md)

For external table and queue-state contracts, use:

- [`code-as-doc/dev/external_table_contracts.md`](external_table_contracts.md)
- [`code-as-doc/dev/queue_state_model.md`](queue_state_model.md)

## 1. Entrypoint Rule

Keep these files orchestration-first:

- [`build.py`](../../build.py)
- [`tools/build_docs.py`](../../tools/build_docs.py)
- [`tools/process_build_queue.py`](../../tools/process_build_queue.py)

That means:

- parse and validate high-level entry arguments
- call stable helper modules
- keep compatibility wrappers when tests or external callers depend on existing names

Do not move new low-level implementation back into these files unless the behavior is truly entrypoint-specific.

## 2. Build Entrypoint Modules

[`build.py`](../../build.py) should stay thin and delegate to these helper modules:

- [`tools/build_main.py`](../../tools/build_main.py)
  - CLI bootstrap and top-level error boundary for `build.py`
- [`tools/build_cli.py`](../../tools/build_cli.py)
  - argument parsing
- [`tools/build_dispatch.py`](../../tools/build_dispatch.py)
  - registered top-level action routing for explicit non-build actions
  - fallback routing for standard build actions such as `rst`, `word`, `pdf`, `preview`, and `fast`
- [`tools/build_paths.py`](../../tools/build_paths.py)
  - config loading
  - config-driven docs_dir / layout-params resolution
  - staging-root resolution (CLI arg / env coupling)
  - review/build/release root selection
  - thin adapter: delegates all path-segment construction to [`tools/utils/path_utils.py`](../../tools/utils/path_utils.py)
- [`tools/utils/path_utils.py`](../../tools/utils/path_utils.py)
  - single source of truth for repo-relative path segments (`PathSegments`)
  - repo-root-anchored and config-anchored `Paths`, plus `*_of(base)` suffix helpers
  - consumed by `build_paths.py` and path-building sites across `tools/`
- [`tools/build_entry_commands.py`](../../tools/build_entry_commands.py)
  - CLI command assembly for build/check/review/sync/release/queue entrypoints
- [`tools/build_runtime.py`](../../tools/build_runtime.py)
  - validate/check/pre-build runtime helpers
  - review auto-sync and cleanup helpers
- [`tools/build_reports.py`](../../tools/build_reports.py)
  - diff-report target resolution
  - tracked-root/report-dir helpers
  - diff-report command assembly
- [`tools/build_publish.py`](../../tools/build_publish.py)
  - publish orchestration over `check -> diff-report -> word -> release-manifest`
- [`tools/build_doctor.py`](../../tools/build_doctor.py)
  - environment and dependency diagnostics
  - doctor target/pdf/reference-doc resolution
  - doctor finding collection

## 3. Build Bundle And Export Modules

[`tools/build_docs.py`](../../tools/build_docs.py) should stay a wrapper-compatible facade and delegate to:

- [`tools/build_docs_main.py`](../../tools/build_docs_main.py)
  - CLI bootstrap for the low-level build entrypoint
- [`tools/build_docs_entry.py`](../../tools/build_docs_entry.py)
  - top-level build session orchestration
- [`tools/build_docs_targets.py`](../../tools/build_docs_targets.py)
  - build target resolution and configured target expansion
- [`tools/build_docs_bundle.py`](../../tools/build_docs_bundle.py)
  - runtime bundle preparation and review overlay entry helpers
- [`tools/build_docs_export.py`](../../tools/build_docs_export.py)
  - export orchestration shell for one build target
- [`tools/build_docs_artifacts.py`](../../tools/build_docs_artifacts.py)
  - export-plan derivation
  - word/pdf/html artifact steps
  - HTML postprocess handoff
- [`tools/build_docs_html.py`](../../tools/build_docs_html.py)
  - manual HTML metadata and switcher helpers
- [`tools/build_docs_io.py`](../../tools/build_docs_io.py)
  - Sphinx, cleanup, Word/PDF I/O helpers
- [`tools/build_docs_validation.py`](../../tools/build_docs_validation.py)
  - config/layout validation helpers for the build tool
- [`tools/word_bundle_docx.py`](../../tools/word_bundle_docx.py)
  - DOCX export assembly and Word post-processing orchestration
- [`tools/word_bundle_docx_styles.py`](../../tools/word_bundle_docx_styles.py)
  - DOCX heading/style remapping and outline-level normalization
- [`tools/word_bundle_docx_images.py`](../../tools/word_bundle_docx_images.py)
  - DOCX external image embedding and content-type updates
- [`tools/word_bundle_docx_pandoc.py`](../../tools/word_bundle_docx_pandoc.py)
  - pandoc version guardrails for reference-template DOCX exports
- [`tools/word_bundle_docx_xml.py`](../../tools/word_bundle_docx_xml.py)
  - namespace-preserving XML serialization helpers for DOCX package rewrites

## 4. Quality And Release Modules

Quality and release logic should follow concern-specific modules instead of drifting back into entry files:

- [`tools/check_docs.py`](../../tools/check_docs.py)
  - quality gate facade over bundle/reference/contract/generated-page checks
- [`tools/check_docs_generated.py`](../../tools/check_docs_generated.py)
  - generated-page rule helpers
- [`tools/validate_spec_master_runtime.py`](../../tools/validate_spec_master_runtime.py)
  - runtime Spec_Master validation rules
- [`tools/page_contracts.py`](../../tools/page_contracts.py)
  - page contract enforcement
- [`tools/diff_report.py`](../../tools/diff_report.py)
  - compatibility facade for diff-report CLI
- [`tools/diff_report_git.py`](../../tools/diff_report_git.py)
  - git/path extraction helpers
- [`tools/diff_report_fields.py`](../../tools/diff_report_fields.py)
  - field and page diff extraction heuristics
- [`tools/diff_report_render.py`](../../tools/diff_report_render.py)
  - report rendering
- [`tools/diff_report_reports.py`](../../tools/diff_report_reports.py)
  - report assembly
- [`tools/release_manifest.py`](../../tools/release_manifest.py)
  - release-manifest CLI facade
- [`tools/release_manifest_service.py`](../../tools/release_manifest_service.py)
  - release traceability assembly

## 5. Document Link Queue Modules

[`tools/process_build_queue.py`](../../tools/process_build_queue.py) should stay orchestration-first and delegate to:

- [`tools/process_build_queue_main.py`](../../tools/process_build_queue_main.py)
  - CLI bootstrap and data-root normalization for the queue entrypoint
- [`tools/process_build_queue_services.py`](../../tools/process_build_queue_services.py)
  - wrapper-compatible service grouping for queue entrypoint helpers
- [`tools/queue_contract.py`](../../tools/queue_contract.py)
  - canonical queue contract constants
  - shared queue dataclasses
  - binding / record / wiki destination type definitions
- [`tools/document_link_actions.py`](../../tools/document_link_actions.py)
  - normalized queue action vocabulary
  - legacy `Doc_phase` compatibility mapping
- [`tools/document_link_queue.py`](../../tools/document_link_queue.py)
  - row parsing
  - row filtering
  - record binding
  - queue preflight helpers
- [`tools/queue_bound_binding.py`](../../tools/queue_bound_binding.py)
  - queue preflight and Document_link binding adapters
  - repo entrypoint-facing access to environment-backed binding resolution
- [`tools/queue_bound_records.py`](../../tools/queue_bound_records.py)
  - queue record/action facade adapters
  - repo-root-aware config resolution and grouping helpers used by the queue entrypoint
- [`tools/queue_config_resolution.py`](../../tools/queue_config_resolution.py)
  - config-family routing
  - target/config resolution for queue rows
- [`tools/queue_runtime.py`](../../tools/queue_runtime.py)
  - worktree/runtime helpers
  - generated path and review/runtime input helpers
- [`tools/queue_build_execution.py`](../../tools/queue_build_execution.py)
  - queue-triggered `build.py` command assembly
  - phase2 sync-before-build execution
  - worktree-scoped draft/publish build orchestration
- [`tools/queue_orchestration.py`](../../tools/queue_orchestration.py)
  - top-level queue session flow
  - dry-run vs real-run branch control
  - post-sync pending-state reload
- [`tools/queue_group_processing.py`](../../tools/queue_group_processing.py)
  - per-group queue processing
  - started/success/failure writeback orchestration
  - drive upload and wiki attach flow for one grouped build task
- [`tools/queue_dry_run.py`](../../tools/queue_dry_run.py)
  - dry-run preview payload assembly
  - grouped queue preview output formatting
- [`tools/queue_grouping.py`](../../tools/queue_grouping.py)
  - grouped record bucketing rules
  - document-key vs record-id grouping strategy
- [`tools/queue_session.py`](../../tools/queue_session.py)
  - queue-session bootstrap and preflight
  - pending-record fetch/select/group state
  - wiki destination reporting for a processing session
- [`tools/queue_lark_ops.py`](../../tools/queue_lark_ops.py)
  - Lark/Drive/Wiki transport and remote I/O helpers
- [`tools/queue_bound_lark_ops.py`](../../tools/queue_bound_lark_ops.py)
  - repo-root-aware Lark transport adapters used by queue entrypoints
  - bound CLI upload/node lookup helpers that still allow entrypoint-level patching
- [`tools/queue_outputs.py`](../../tools/queue_outputs.py)
  - generic publish asset staging
  - generic release/output path helpers
  - generic publish metadata assembly
- [`tools/queue_bound_outputs.py`](../../tools/queue_bound_outputs.py)
  - repo-root-aware queue output adapters
  - bound output/release helpers that keep `process_build_queue.ROOT` patchable
- [`tools/queue_bound_runtime.py`](../../tools/queue_bound_runtime.py)
  - repo-root-aware command/worktree adapters for queue entrypoints
  - bound `build.py` command builders and worktree helpers that keep entrypoint compatibility names stable
- [`tools/queue_writeback.py`](../../tools/queue_writeback.py)
  - queue result formatting
  - row writeback payload assembly
  - `pending -> running -> success/failed` payload expectations documented in
    [`queue_state_model.md`](queue_state_model.md)
- [`tools/queue_transitions.py`](../../tools/queue_transitions.py)
  - explicit queue transition payload model for running, success, failure, and writeback-failed states
  - focused test target for queue writeback semantics before live Feishu/Lark transport is involved

## 6. Cloud-Doc Backport Modules

The cloud-doc backport closed loop (fetch → diff → classify/route → write-back)
was decomposed from a single 4183-line `cloud_doc_backport.py` into focused
layers (debt-paydown, 2026-06). The entry path is unchanged: every
`from tools.cloud_doc_backport import X` and `python3 tools/cloud_doc_backport.py …`
still works because the entry file re-exports all public symbols.

- [`tools/cloud_doc_backport.py`](../../tools/cloud_doc_backport.py)
  - thin entry shim (~200 lines): re-exports every public symbol from the modules
    below + the `__main__` guard. Keep it shim-only.
- [`tools/cloud_doc_backport_model.py`](../../tools/cloud_doc_backport_model.py)
  - foundation: `Block` model, document fetch/normalization, markdown→block
    parsing, section selection. Imports only stdlib + `path_utils` (no cycle).
- [`tools/cloud_doc_backport_util.py`](../../tools/cloud_doc_backport_util.py)
  - shared constants (schema versions) + scaffolding (counters, git-ref,
    timestamp, source-path resolution).
- [`tools/cloud_doc_backport_routing.py`](../../tools/cloud_doc_backport_routing.py)
  - delta classification + routing (Class R / D / T / image / semantic) + `diff_blocks`.
- [`tools/cloud_doc_backport_apply.py`](../../tools/cloud_doc_backport_apply.py)
  - guarded Class-R write-back (literal-first + block-fallback RST rewrite) + apply-report builders.
- [`tools/cloud_doc_backport_render.py`](../../tools/cloud_doc_backport_render.py)
  - markdown report renderers (pure report-dict → markdown).
- [`tools/cloud_doc_backport_transports.py`](../../tools/cloud_doc_backport_transports.py)
  - live Feishu source-table / TM transports + `--table-binding` parsing.
- [`tools/cloud_doc_backport_reports.py`](../../tools/cloud_doc_backport_reports.py)
  - report builders (`build_report` + verify / source-table-suggestions / template-sync-proposal / review-run).
- [`tools/cloud_doc_backport_pr.py`](../../tools/cloud_doc_backport_pr.py)
  - PR/git helpers (`gh` PR creation + 403 compare-url fallback, branch naming, `open_backport_pr_from_manifest`).
- [`tools/cloud_doc_backport_cli.py`](../../tools/cloud_doc_backport_cli.py)
  - CLI + orchestration conductor: argparse, the `_run_*` command handlers, the
    `run-review-branch` / baseline flow, and `main`.

Layering (import direction, bottom → top): `model` → `util` → `routing` /
`apply` / `render` / `transports` / `reports` / `pr` → `cli` → entry shim. A new
extraction must import from the **leaf modules**, never from the entry file
(that would cycle), and the entry file re-exports it.

Record-resolution + source-table write are in sibling modules:
[`tools/source_record_index.py`](../../tools/source_record_index.py) (the
`source_record_index.json` sidecar: business key → Feishu `record_id`),
[`tools/token_resolution_map.py`](../../tools/token_resolution_map.py) (value →
source_ref), [`tools/source_table_sync.py`](../../tools/source_table_sync.py)
(exact-or-abstain F6 write).

Tests: `tests/test_backport_golden_corpus.py` (routing matrix),
`tests/test_source_table_sync_invariants.py` (F6 write-side fuzz),
`tests/test_backport_harness.py` (+ `tools/backport_harness.py`, offline
multi-edit integration), `tests/test_backport_noise_injection.py`,
`tests/test_backport_live_check.py` (+ `tools/backport_live_check.py`, operator
live round-trip).

Sync-env bootstrap (`sync-data` needs `FEISHU_PHASE2_*` + TM env): copy
[`scripts/hello_docs_binding.env.example`](../../scripts/hello_docs_binding.env.example),
fill values (table/view IDs are discoverable per tenant via `lark-cli base
+table-list` / `+view-list`; a wiki-wrapped base resolves to its app_token via
`lark-cli wiki +node-get`), and check with
[`scripts/validate_required_env.sh`](../../scripts/validate_required_env.sh).

## 7. Maintenance Rules

When adding or moving logic in this area:

1. Prefer adding to an existing helper module before expanding an orchestration file.
2. If a new helper module is introduced, update this file in the same change.
3. If a major boundary changes, also update:
   - [`code-as-doc/code_optimization_log.md`](../code_optimization_log.md)
   - [`optimization_project.md`](../optimization_project.md)
4. Keep wrapper names stable in entry files when tests or external scripts patch them directly.
5. If a wrapper stops being needed, remove it only after tests and call sites are updated together.
6. When encoded field names are normalized, prefer unicode-escaped canonical constants in helper modules before deleting old literals from entry files.

## 8. Known Next Decomposition Candidates

These areas still deserve follow-up only when a concrete hotspot reappears:

- [`tools/process_build_queue_services.py`](../../tools/process_build_queue_services.py)
- [`tools/queue_lark_ops.py`](../../tools/queue_lark_ops.py)
- [`tools/gen_index_bundle.py`](../../tools/gen_index_bundle.py)

Keep future extraction notes here once those boundaries stabilize again.
