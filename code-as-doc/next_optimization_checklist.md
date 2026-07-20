# Next Optimization Checklist

Updated: 2026-07-17

This file tracks the next optimization wave after the completed maintainability refactor campaign.
Use it as the active execution checklist for the upcoming maintainability and stability work.

Do not use this file as:

- the long-term architecture document
- the repo-level roadmap
- the completed optimization history log
- the maintainer command reference

Use these documents for those topics:

- [`architecture/System Evolution Strategy.md`](architecture/System%20Evolution%20Strategy.md)
- [`../optimization_project.md`](optimization_project.md)
- [`code_optimization_log.md`](code_optimization_log.md)
- [`maintainability_refactor_tracker.md`](maintainability_refactor_tracker.md)
- [`build_doc_guide.md`](build_doc_guide.md)

## 1. Update Rules

When one item starts:

- change its status from `pending` to `in_progress`
- keep one PR scoped to one checklist item whenever possible
- add a short note if the planned scope changed

When one item is blocked:

- change its status to `blocked`
- add one short note describing the blocker
- decide whether the item should stay active or move to `deferred`

When one item is finished:

- change its status from `in_progress` to `done`
- add the completion date
- add one short note describing the actual outcome

When a whole milestone is finished:

- append a short historical entry to [`code_optimization_log.md`](code_optimization_log.md)
- update [`../optimization_project.md`](optimization_project.md) if the active workstream status changed materially

Status vocabulary:

- `pending`
- `in_progress`
- `blocked`
- `done`
- `deferred`

## 2. Current Baseline

This checklist assumes the 2026-05-07 baseline below:

- repo evaluation focus: maintainability and stability
- local repo test baseline: `python3 -m unittest`
- local quality-gate baseline:
  - `python3 -m ruff check build.py integrations tools tests scripts`
  - `python3 scripts/local_build.py check --config configs/config.us-en.yaml --model JE-1000F --region US`
  - `python3 scripts/local_build.py check --config configs/config.ja.yaml --model JE-1000F --region JP`
- short-term baseline PRs already absorbed:
  - phase2 snapshot manifest completeness validation
  - CLI action registry
  - config contract validation
  - queue `RUNNING` status writeback
- highest-leverage current hotspots identified in:
  - [`../tests/test_process_build_queue.py`](../tests/test_process_build_queue.py)
  - [`../tools/queue_query.py`](../tools/queue_query.py)
  - [`../tools/word_bundle_docx_styles.py`](../tools/word_bundle_docx_styles.py)
  - [`../tools/csv_pages/renderers_symbols.py`](../tools/csv_pages/renderers_symbols.py)
  - [`../tools/check_docs_generated.py`](../tools/check_docs_generated.py)
- the long-term content assembly pilot (Milestone D) was rolled back to
  template-driven rendering (#295/#296); the live data-driven primitives are now
  `csv_pages` + `page_registry` + `content_blocks` + `Manual_Copy_Source`
  short-copy tokens, and prose-assembly re-launch is tracked as Workstream N in
  [`optimization_project.md`](optimization_project.md)

## 3. Milestone A: 2 Weeks

Milestone status: `done`
Milestone completed: `2026-04-07`
Milestone note: completed the first quality-gate hardening wave across preview target loading, Spec_Master/runtime/generated-page rule splits, a low-noise Ruff CI gate, and shared orchestration-test helpers while keeping the end-to-end suite green.

- [x] PR 1: Remove import-time config loading from review-preview target resolution
  - Status: `done`
  - Target files:
    - [`../tools/process_docs/build_review_preview_targets.py`](../tools/process_docs/build_review_preview_targets.py)
    - [`../tools/process_docs/build_review_preview.py`](../tools/process_docs/build_review_preview.py)
  - Guard tests:
    - [`../tests/test_build_review_preview.py`](../tests/test_build_review_preview.py)
    - [`../tests/test_vercel_build_review_preview.py`](../tests/test_vercel_build_review_preview.py)
  - Done when:
    - importing review-preview modules no longer reads config files immediately
    - target template loading happens lazily or through an explicit factory/cache
    - behavior remains unchanged for current preview commands
  - Completed: `2026-04-07`
  - Note: replaced eager config-backed template loading with a lazy cached proxy while keeping the public `WORKSPACE_TARGET_TEMPLATES` iterable surface intact and adding an import-time regression test

- [x] PR 2: Split Spec_Master validation into explicit rule units
  - Status: `done`
  - Target files:
    - [`../tools/validate_spec_master_runtime.py`](../tools/validate_spec_master_runtime.py)
    - [`../tools/validate_spec_master_shared.py`](../tools/validate_spec_master_shared.py)
  - Guard tests:
    - [`../tests/test_validate_spec_master.py`](../tests/test_validate_spec_master.py)
    - [`../tests/test_build_script.py`](../tests/test_build_script.py)
  - Done when:
    - rule collection is split into smaller helpers or a rule registry
    - adding one validation rule no longer requires editing one giant function
    - CLI output and error codes remain stable
  - Completed: `2026-04-07`
  - Note: split the runtime validator into focused row/header/footnote/note/selector issue collectors so future rule additions can land in isolated helpers while preserving existing validation output

- [x] PR 3: Split generated-page checks by responsibility
  - Status: `done`
  - Target files:
    - [`../tools/check_docs_generated.py`](../tools/check_docs_generated.py)
    - [`../tools/check_docs.py`](../tools/check_docs.py)
  - Guard tests:
    - [`../tests/test_check_docs.py`](../tests/test_check_docs.py)
    - [`../tests/test_page_contracts.py`](../tests/test_page_contracts.py)
  - Done when:
    - recipe validation, template/snippet validation, contract checks, and spec-binding checks are separated
    - `build.py check` behavior is preserved
    - issue messages stay at least as specific as today
  - Completed: `2026-04-07`
  - Note: reworked the generated-page checker into focused loader, recipe, binding, snippet, placeholder, contract, and orphan-snippet helpers while preserving the existing facade signature and issue ordering

- [x] PR 4: Add a minimal static quality gate
  - Status: `done`
  - Target files:
    - [`../pyproject.toml`](../pyproject.toml)
    - [`.github/workflows/manual-validation.yml`](../.github/workflows/manual-validation.yml)
    - [`build_doc_guide.md`](build_doc_guide.md)
  - Guard tests:
    - [`../tests/test_build_script.py`](../tests/test_build_script.py)
  - Done when:
    - the repo has one committed static-check configuration
    - CI runs a minimal lint gate before or alongside unit tests
    - the first rule set stays intentionally small and low-noise
  - Completed: `2026-04-07`
  - Note: added a repo-level Ruff config with the intentionally small `E722/F821/F841` rule set, wired it into `Manual Validation`, documented the local command, and cleared the two existing low-noise violations

- [x] PR 5: Extract reusable test helpers for orchestration-heavy suites
  - Status: `done`
  - Target files:
    - [`../tests/test_helpers.py`](../tests/test_helpers.py)
    - [`../tests/test_build_script.py`](../tests/test_build_script.py)
    - [`../tests/test_process_build_queue.py`](../tests/test_process_build_queue.py)
    - [`../tests/test_target_resolution.py`](../tests/test_target_resolution.py)
    - [`../tests/test_check_docs.py`](../tests/test_check_docs.py)
    - [`../tests/README.md`](../tests/README.md)
  - Guard tests:
    - full `.\.venv\Scripts\python.exe -m unittest`
  - Done when:
    - repeated temp-dir and patch scaffolding is moved into shared helpers
    - hot-path tests remain easy to read
    - refactor support gets better without changing test intent
  - Completed: `2026-04-07`
  - Note: added shared `temp_test_root`, `write_text`, `write_lines`, and `patch_module_attrs` helpers, migrated representative build/check/queue/target-resolution tests onto the shared scaffolding, documented the helper usage in `tests/README.md`, and kept the full `361`-test suite green

## 4. Milestone B: 1 Month

Milestone status: `done`
Milestone completed: `2026-04-08`
Milestone note: closed the second stability wave by fixing diff-report regression fixtures, expanding CI smoke coverage across diff-report/release-manifest/review-preview, centralizing shared GitHub-hosted Feishu worker setup, and finishing a wrapper-focused boundary pass across the remaining medium orchestration files without breaking patchable compatibility points.

- [x] PR 6: Harden diff-report heuristics with fixed fixtures
  - Status: `done`
  - Target files:
    - [`../tools/diff_report.py`](../tools/diff_report.py)
    - [`../tools/diff_report_fields.py`](../tools/diff_report_fields.py)
    - [`../tools/diff_report_render.py`](../tools/diff_report_render.py)
    - [`../tools/diff_report_reports.py`](../tools/diff_report_reports.py)
  - Guard tests:
    - [`../tests/test_diff_report.py`](../tests/test_diff_report.py)
  - Done when:
    - heuristic field matching is covered by fixed sample fixtures
    - high-value diff cases have stable expected outputs
    - future refactors can detect report drift early
  - Completed: `2026-04-08`
  - Note: added committed fixture repos for template back-mapping, placeholder label renames, section-order fallback, and fixture-driven `generate_diff_report` coverage so heuristic/report drift is caught without relying only on ad hoc temp-repo tests

- [x] PR 7: Expand CI coverage for critical non-unit workflow surfaces
  - Status: `done`
  - Target files:
    - [`.github/workflows/manual-validation.yml`](../.github/workflows/manual-validation.yml)
    - [`.github/workflows/review-preview.yml`](../.github/workflows/review-preview.yml)
  - Guard tests:
    - CI workflow runs
  - Done when:
    - CI covers at least one smoke path for `diff-report`
    - CI covers at least one smoke path for `release-manifest`
    - CI covers review-preview packaging at a stable smoke level
  - Completed: `2026-04-08`
  - Note: added a dedicated `workflow-smoke` job for `diff-report` and `release-manifest`, then converted `Review Preview Package` into a stable smoke packaging path with `--skip-word` and explicit packaged-file checks before artifact upload

- [x] PR 8: Deduplicate shared GitHub Actions setup logic
  - Status: `done`
  - Target files:
    - [`.github/workflows/feishu-build-queue.yml`](../.github/workflows/feishu-build-queue.yml)
    - [`.github/workflows/feishu-draft-build-queue.yml`](../.github/workflows/feishu-draft-build-queue.yml)
    - [`.github/workflows/feishu-start-review.yml`](../.github/workflows/feishu-start-review.yml)
  - Guard tests:
    - workflow syntax validation
    - one dry-run or smoke dispatch per affected workflow if practical
  - Done when:
    - repeated Python/Node/pandoc/lark setup is centralized
    - repeated secret-validation shell logic is reduced
    - workflow intent remains easy to read
  - Completed: `2026-04-08`
  - Note: centralized shared GitHub-hosted worker bootstrap in `.github/actions/feishu-common-setup/action.yml` and moved repeated required-env checks into `scripts/validate_required_env.sh` while keeping checkout/dispatch/trigger flow readable in each worker

- [x] PR 9: Strengthen package boundaries around build, quality, queue, and release concerns
  - Status: `done`
  - Target files:
    - [`../tools/`](../tools)
    - [`dev/orchestration_module_map.md`](dev/orchestration_module_map.md)
    - [`architecture/Hello_Docs_Architecture.md`](architecture/Hello_Docs_Architecture.md)
  - Guard tests:
    - [`../tests/test_build_script.py`](../tests/test_build_script.py)
    - [`../tests/test_process_build_queue.py`](../tests/test_process_build_queue.py)
    - [`../tests/test_release_manifest.py`](../tests/test_release_manifest.py)
  - Done when:
    - new logic placement is driven by stable domain boundaries instead of filename prefixes alone
    - orchestration files stay orchestration-first
    - the ownership map is updated in the same change
  - Completed: `2026-04-08`
  - Note: documented explicit build/quality/release/queue ownership boundaries in the module map and component map, and extracted top-level CLI bootstrap helpers so the main entry files stay orchestration-first instead of reabsorbing concern-specific setup logic

- [x] PR 10: Revisit medium-sized orchestration wrappers after the quality gate hardening wave
  - Status: `done`
  - Target files:
    - [`../build.py`](../build.py)
    - [`../tools/build_docs.py`](../tools/build_docs.py)
    - [`../tools/build_docs_export.py`](../tools/build_docs_export.py)
    - [`../tools/process_build_queue.py`](../tools/process_build_queue.py)
  - Guard tests:
    - [`../tests/test_build_script.py`](../tests/test_build_script.py)
    - [`../tests/test_target_resolution.py`](../tests/test_target_resolution.py)
    - [`../tests/test_process_build_queue.py`](../tests/test_process_build_queue.py)
  - Done when:
    - remaining wrappers are reviewed only after the earlier hotspot splits land
    - helper boundaries are clarified without breaking patchable compatibility points
    - no low-level logic drifts back into entry files
  - Completed: `2026-04-08`
  - Note: kept `build.py`, `tools/build_docs.py`, and `tools/process_build_queue.py` as wrapper-compatible facades while moving CLI bootstrap and build-export artifact planning/output steps into focused helpers, then added regression tests around the new bootstrap/artifact-plan surfaces

## 5. Milestone C: Short-Term Contract Baseline

Milestone status: `done`
Milestone completed: `2026-05-08`
Milestone target: `2026-05`
Milestone note: closed the contract baseline and midterm hardening pass by
adding an explicit queue transition layer, offline external integration smoke
fixtures, schema drift gates, a queue-contract CI job, and another domain split
of the largest queue test hotspot.

- [x] PR 11: Absorb short-term hardening PRs into the active baseline
  - Status: `done`
  - Completed: `2026-05-07`
  - Note: current `main` includes phase2 snapshot completeness validation, CLI action registry, config contract validation, and queue `RUNNING` state writeback

- [x] PR 12: Document external table contract v1
  - Status: `done`
  - Target files:
    - [`dev/external_table_contracts.md`](dev/external_table_contracts.md)
    - [`dev/orchestration_module_map.md`](dev/orchestration_module_map.md)
  - Done when:
    - phase2 tables, `Document_link`, and Review Init have explicit read/write field contracts
    - compatible aliases and drift rules are documented
  - Completed: `2026-05-07`
  - Note: added the first repo-owned external table contract for snapshot, queue, and review-init fields

- [x] PR 13: Document queue state model
  - Status: `done`
  - Target files:
    - [`dev/queue_state_model.md`](dev/queue_state_model.md)
    - [`dev/orchestration_module_map.md`](dev/orchestration_module_map.md)
  - Done when:
    - `pending -> running -> success/failed` is documented
    - fields written in each phase are explicit
    - writeback-failed handling is called out
  - Completed: `2026-05-07`
  - Note: documented running/success/failure/writeback-failed behavior and linked it from the orchestration map

- [x] PR 14: Split the first queue writeback tests out of the largest test hotspot
  - Status: `done`
  - Target files:
    - [`../tests/test_process_build_queue.py`](../tests/test_process_build_queue.py)
    - [`../tests/test_process_build_queue_writeback.py`](../tests/test_process_build_queue_writeback.py)
  - Done when:
    - writeback field construction tests live in a domain-named test file
    - `tests/test_process_build_queue.py` remains behavior-compatible
  - Completed: `2026-05-07`
  - Note: moved started/success/failure writeback field tests into `test_process_build_queue_writeback.py`

- [x] PR 15: Centralize queue state transitions
  - Status: `done`
  - Target files:
    - [`../tools/queue_transitions.py`](../tools/queue_transitions.py)
    - [`../tools/queue_writeback.py`](../tools/queue_writeback.py)
    - [`../tools/queue_group_processing.py`](../tools/queue_group_processing.py)
    - [`../tests/test_queue_transitions.py`](../tests/test_queue_transitions.py)
  - Done when:
    - result formatting, start/success/failure writeback, trigger clearing, and `data_sync` rules are testable as transition behavior
    - tests cover running, success, failure, and writeback-failed
  - Completed: `2026-05-08`
  - Note: added `queue_transitions.py` as the explicit payload layer while keeping `queue_writeback.py` wrapper-compatible

- [x] PR 16: Add external integration fixture smoke tests
  - Status: `done`
  - Target files:
    - [`../tests/test_external_integration_contracts.py`](../tests/test_external_integration_contracts.py)
    - [`../tests/fixtures/external_integrations/`](../tests/fixtures/external_integrations)
  - Done when:
    - fixture tests cover missing fields, permission failure, duplicate dispatch, publish confirmation, and DingTalk fallback without real network access
  - Completed: `2026-05-08`
  - Note: added offline fixtures covering Review Init missing fields, Feishu writeback permission failure, duplicate Start Review dispatch, Publish confirmation guard, and DingTalk fallback

- [x] PR 17: Add schema drift checks
  - Status: `done`
  - Target files:
    - [`../tools/schema_drift.py`](../tools/schema_drift.py)
    - [`../tests/fixtures/`](../tests/fixtures)
    - [`.github/workflows/manual-validation.yml`](../.github/workflows/manual-validation.yml)
  - Done when:
    - phase2 snapshot manifest, CSV headers, and queue writable fields can be validated from fixed fixtures or dry-run payloads
  - Completed: `2026-05-08`
  - Note: added a local schema drift gate with fixture payload support plus a real `data/phase2` dry-run-style check in the queue-contract CI job

- [x] PR 18: Split queue routing tests from the largest queue test hotspot
  - Status: `done`
  - Target files:
    - [`../tests/test_process_build_queue.py`](../tests/test_process_build_queue.py)
    - [`../tests/test_process_build_queue_routing.py`](../tests/test_process_build_queue_routing.py)
    - [`../tests/README.md`](../tests/README.md)
  - Done when:
    - routing/config/grouping tests live in a domain-named test file
    - the original queue orchestration test remains behavior-compatible
  - Completed: `2026-05-08`
  - Note: moved 18 routing/config/grouping tests into `test_process_build_queue_routing.py`

## 6. Milestone D: Long-Term Content Assembly Pilot Preparation

Milestone status: `done`
Milestone completed: `2026-05-08`
Milestone target: `2026-05`
Milestone note: completed the pre-template-splitting safety net and the first
page-level `03_product_overview` pilot switch without rewriting the repo-wide
template system.

> **Rolled back (2026-05-30, option B):** this content-assembly pilot was reverted to a pure template-driven overview. The `assembly_pilot` switch, the `content_assembly` / `content_assembly_contract` / `product_overview_renderer` modules, `assembly_blocks/` / `assembly_contracts/`, and their fixtures/tests were removed (PR #295 disabled the pilot + authored the US templates; PR #296 deleted the dead code). The file references below are historical — those paths no longer exist. Overview part names now live only in `page_<lang>/03_product_overview_placeholder.rst`.

- [x] Long-term PR 1: Document the pilot inventory and block taxonomy
  - Status: `done`
  - Target files:
    - [`dev/content_assembly_pilot_plan.md`](dev/content_assembly_pilot_plan.md)
  - Done when:
    - `03_product_overview` templates, recipes, contract, renderer, assets, and data surfaces are inventoried
    - the first functional block taxonomy is documented with repeatability, applicability, and missing-field policy
  - Completed: `2026-05-08`
  - Note: documented the pilot boundary and confirmed preparation work does not change the current HTML/PDF build path

- [x] Long-term PR 2: Add multidimensional-table-style fixtures
  - Status: `done`
  - Target files:
    - `../tests/fixtures/content_assembly/`
  - Done when:
    - fixture tables exist for page assembly, content blocks, block fields, assets, and block rules
    - schema drift tests catch missing fixture headers before any live Feishu integration is introduced
  - Completed: `2026-05-08`
  - Note: added CSV fixtures that simulate the first page assembly contract without depending on live network data

- [x] Long-term PR 3: Add the assembly contract validator
  - Status: `done`
  - Target files:
    - `../tools/content_assembly_contract.py`
    - `../docs/templates/assembly_contracts/03_product_overview.yaml`
    - `../tests/test_content_assembly_contract.py`
  - Done when:
    - unknown blocks, missing required fields, missing assets, and missing fallback declarations fail locally
  - Completed: `2026-05-08`
  - Note: added a fixture-backed validator and CLI for the pilot assembly contract

- [x] Long-term PR 4: Add the no-op assembler
  - Status: `done`
  - Target files:
    - `../tools/content_assembly.py`
    - `../tests/test_content_assembly.py`
  - Done when:
    - US/en and JP/ja no-op RST can be rendered to a temporary path
    - managed build/template output directories are rejected
    - the existing build path remains unchanged
  - Completed: `2026-05-08`
  - Note: added deterministic fixture rendering for the pilot page while keeping official template rendering untouched

- [x] Long-term PR 5: Connect `03_product_overview` behind a page-level pilot switch
  - Status: `done`
  - Target files:
    - [`../tools/draft_engine.py`](../tools/draft_engine.py)
    - `../tools/content_assembly.py`
    - `../docs/templates/assembly_blocks/03_product_overview/`
  - Done when:
    - configured pilot targets render through fixture-backed assembly
    - non-configured targets keep the old template fallback path
    - pilot failures raise clear errors instead of partial output
  - Completed: `2026-05-08`
  - Note: enabled the product overview pilot for `US/en` and `JP/ja`, added block templates, and kept the switch target-scoped

## 6b. Milestone E: Stage-3 Path — Lock Stage 2 + Safe Prose Cut

Milestone status: `pending`
Milestone target: `next wave`
Milestone note: this is the active wave for the path to Stage 3 — the
deliberate-hybrid end state. E1+E2 lock Stage 2 traceability; E3+E4 take the safe
first cut into prose without moving body prose. E4 (page_registry authority) is
the main lever for eliminating template forks, which is the real Stage 3 win and
is independent of structuralizing prose bodies. What gets structured vs
deliberately kept in templates/config follows the content-truth allocation rule
(§3.1) in [`architecture/Long_Form_Content_Block_Design.md`](architecture/Long_Form_Content_Block_Design.md).
The long-form prose assembly re-launch (Workstream N) stays out of this milestone,
gated on the same design.

- [ ] PR E1: Freeze release snapshots (Workstream J)
  - Status: `pending`
  - Target files:
    - [`../tools/release_manifest.py`](../tools/release_manifest.py)
    - [`../tools/utils/path_utils.py`](../tools/utils/path_utils.py)
    - [`../tools/sync_data.py`](../tools/sync_data.py)
  - Done when:
    - a timestamped snapshot (source revision, exported files, target matrix) is archived at release time
    - `release-manifest` binds to that frozen snapshot through `path_utils`, not a re-pulled live snapshot
    - rebuilding from the archived snapshot reproduces the release output

- [ ] PR E2: QC closed-loop tail — sync-time `record_id` sidecar (Workstream I)
  - Status: `pending`
  - Note: touches `sync-data` and the phase2 source contract → operator-gated per `AGENTS.md` §8.7
  - Target files:
    - [`../tools/sync_data.py`](../tools/sync_data.py)
    - [`../tools/content_lint.py`](../tools/content_lint.py)
    - [`dev/closed_loop_qc_implementation_plan.md`](dev/closed_loop_qc_implementation_plan.md)
  - Done when:
    - `sync-data` emits a `source_record_index` sidecar without adding `record_id` columns to existing CSV contracts
    - `content_lint` findings resolve to an exact live `record_id` or abstain (`unresolved`/`ambiguous`)
    - the optional Feishu `QC_Report` writer stays dry-run/operator-gated

- [ ] PR E3: Extend short-copy to operation-guide and app-setup chrome (Workstream L)
  - Status: `pending`
  - Target files:
    - [`dev/content_block_migration_assessment.md`](dev/content_block_migration_assessment.md)
    - [`../tools/check_docs_generated.py`](../tools/check_docs_generated.py)
  - Done when:
    - operation-guide and app-setup section headings, button/UI labels, table labels, and image alt text resolve from `Manual_Copy_Source` via `{{ copy:<copy_key> }}`
    - missing copy keys fail in `build.py check`
    - no body prose is moved, and app-market/support/manufacturer/URL text is routed to config, not the copy table

- [ ] PR E4: Make `page_registry` the single composition authority (Workstream M)
  - Status: `pending`
  - Note: touches the phase2 source contract → operator-gated per `AGENTS.md` §8.7
  - Target files:
    - [`../tools/check_docs_generated.py`](../tools/check_docs_generated.py)
    - [`../tools/gen_index_bundle.py`](../tools/gen_index_bundle.py)
  - Done when:
    - every shipped page (including prose pages) is declared in `page_registry` with explicit applicability (`sku_scope`, `langs`, region/model)
    - page composition and applicability are read from data, not inferred from per-language folder layout
    - RST rendering output is unchanged for prose pages (fallback path preserved)

## 6d. Milestone F: Backport Reverse-Sync & QC Writeback Enablement

Milestone status: `pending`
Milestone target: `after the Milestone E baseline`
Milestone note: PR-level breakdown of Workstream I's remaining tail (the
`record_id` sidecar + QC report writeback) and Workstream Q (backport
layer-routing, template-sync, and approval-gated source-table writes). The rules
are already codified in
[`architecture/Feishu_Cloud_Doc_Backport_Design.md`](architecture/Feishu_Cloud_Doc_Backport_Design.md)
§5.1. Suggested order: F1 → (F2, F3) → F4 → F5 → F6 → F7; F8 may run in parallel
once F1 lands. **F1 is the shared prerequisite for F6 and F8.** Items touching
`sync-data`, `data/phase2` contracts, `build.py` behavior, or Feishu schema are
operator-gated (`AGENTS.md` §8.7). **Status: F1–F8 all merged.** F6/F8 are at the
dry-run boundary; live activation is the operator's, per
[`dev/backport_live_activation_checklist.md`](dev/backport_live_activation_checklist.md).

- [x] PR F1: Sync-time `record_id` sidecar (Workstream I — shared prerequisite)
  - Status: `done`
  - Note: touches `sync-data` + the phase2 contract → operator-gated; this is the detailed form of Milestone E PR E2. Delivered by `tools/source_record_index.py` (builder/resolver, exact-or-abstain), the `sync_data_runtime` sidecar emission, and `content_lint` resolution (lcd_icons indexed; coverage expands in follow-ups). Live population needs an operator `sync-data`; logic is covered by `tests/test_source_record_index.py`. **Correctness fix:** `normalize_records` sorts rows, so pairing the *sorted* normalized list with the *unsorted* raw records mapped each business key to the WRONG `record_id` (live-verified: a `JE-1000F_CN/dc12_port` key resolved to a `JE-1000F_US/dc8020` row, across the two-table `Spec_Master` merge). Now each row's source `record_id` is threaded onto it (`SOURCE_RECORD_ID_KEY`) so it survives the sort; `collect_index_rows` reads it (positional fallback only for legacy/no-id rows).
  - Target files:
    - [`../tools/sync_data.py`](../tools/sync_data.py)
    - [`../tools/content_lint.py`](../tools/content_lint.py)
    - `data/phase2/source_record_index.json` (new derived sidecar)
    - [`dev/closed_loop_qc_implementation_plan.md`](dev/closed_loop_qc_implementation_plan.md)
  - Done when:
    - `sync-data` emits a `source_record_index` sidecar mapping source keys to live `record_id`s, without adding `record_id` columns to existing CSV contracts
    - resolution is exact-or-abstain: zero or multiple matches yield `record_id: null` plus `resolution_status: unresolved`/`ambiguous`
    - `content_lint` and backport can resolve an exact `record_id` from the sidecar
    - the sidecar is listed under manifest `derived_files` and is reproducible from a snapshot

- [x] PR F2: Build-time token/copy resolution map (Workstream Q — Class `D` detection)
  - Status: `done`
  - Note: implemented as a snapshot-based value index (`tools/token_resolution_map.py`: `build_value_index` over `Spec_Master`/`Localized_Copy` per-lang columns + `classify_data_origin`), wired into `cloud_doc_backport` `_classify_route`/`diff_blocks` behind `--lang`/`--data-root` so a reviewer span that resolves to a data value is classified Class `D` (`source_table_suggestion`) with its `source_ref` — no build-engine change needed. `classify_data_origin` matches the whole normalized span **and** each table cell / `<br/>`-joined sub-value, so a real cloud-doc delta (a whole table ROW like `\| 12V⎓最大10A <br/> … \| label \|`, not a bare cell) resolves to its source row deterministically. When an index is present it is **authoritative**: a non-matching prose delta routes to `repo_review_text` instead of the `_looks_data_like` guess (which over-flagged unit/number-bearing prose as Class D); table rows stay Class `D` structurally. A value that maps to **more than one source row** (e.g. a port's `front.label` and `front.spec` both holding `12V⎓最大10A`) is marked `ambiguous` by `build_value_index` and **abstains** (no `source_ref`) — it never auto-resolves the arbitrary first slot, so `apply-source-table` skips it and a human picks the slot (live incident: it had written the wrong `front.spec`). Behavior preserved when no value index is supplied. Tests in `tests/test_token_resolution_map.py`.
  - Target files:
    - [`../tools/draft_engine.py`](../tools/draft_engine.py)
    - [`../tools/gen_index_bundle.py`](../tools/gen_index_bundle.py)
    - [`../tools/cloud_doc_backport.py`](../tools/cloud_doc_backport.py)
  - Done when:
    - the build emits a per-target map of resolved token / copy / csv values back to their source key (the lightweight provenance of §5.1 R8)
    - backport uses it to classify a delta as Class `D` (data-origin) instead of guessing
    - a data-origin delta is never routed to `docs/_review/...` or a template

- [x] PR F3: Family-identical classification (Workstream Q — `R` vs `T` plus scope)
  - Status: `done`
  - Note: `tools/family_scope.py` (`build_family_index` over sibling sources + `classify_family_scope`) wired into `cloud_doc_backport` alongside the F2 value index. A review-doc prose span identical across the family is routed `needs_human_mapping` with its blast radius (`family_scope.targets`) — the §5.1 R5 intentional-divergence gate — instead of auto-routing; target-local spans stay `repo_review_text`. Explicit siblings via repeatable `--sibling`; **`run-review-branch` now auto-resolves the `page_shared/<lang>` shared templates as siblings** so the blessed path fires Class T with no manual flags (`--no-auto-sibling` disables; single-region `ja`/`zh` have no shared surface). Tests in `tests/test_family_scope.py`, `tests/test_cloud_doc_backport.py::RunReviewBranchFamilyScopeTests`.
  - Target files:
    - [`../tools/cloud_doc_backport.py`](../tools/cloud_doc_backport.py)
    - [`../.agents/skills/manual-revision-backport/scripts/scan_residuals.py`](../.agents/skills/manual-revision-backport/scripts/scan_residuals.py)
  - Done when:
    - backport derives `R` (target-local) vs `T` (shared) from whether the span is identical across the family, reusing the residual scanner
    - the sibling / blast-radius scope of a `T` or `D` delta is computed, not guessed
    - template-origin spans changed by the reviewer are flagged `needs_decision` (the §5.1 R5 intentional-divergence gate), not auto-classified

- [x] PR F4: Emit `template_sync_proposal` for Class `T` (Workstream Q)
  - Status: `done`
  - Note: `cloud_doc_backport` now emits `cloud_doc_backport_template_sync_proposal.json/.md` (report-only, `external_write=false`) from `verify-review`, `run-review`, and the blessed `run-review-branch` baseline path, one entry per Class `T` (shared-across-family) delta with the §5.1 R4 contract: target templates (family scope), old→new, evidence, delta hash, and the post-apply rebuild+sync-review step. Backport still writes only Class `R` to `docs/_review/...`; Class `T` is never written there. Tests in `tests/test_template_sync_proposal.py`.
  - Target files:
    - [`../tools/cloud_doc_backport.py`](../tools/cloud_doc_backport.py)
    - [`architecture/Feishu_Cloud_Doc_Backport_Design.md`](architecture/Feishu_Cloud_Doc_Backport_Design.md)
  - Done when:
    - a review-backport run emits `template_sync_proposal.json/.md` for Class `T` deltas with the §5.1 R4 contract (target template(s), family scope, old→new, evidence, post-apply rebuild step, delta hash)
    - backport still writes only Class `R` to `docs/_review/...`; it never writes templates
    - Class `T` deltas are not written to `_review` (strict)

- [x] PR F5: `rebuild + rediff` idempotency gate (Workstream Q — §5.1 R7)
  - Status: `done`
  - Note: `_rebuild_rediff_gate` re-diffs the baseline against the edited source and asserts the only changes are the intended `repo_review_text` deltas (no collateral `unexpected`, none `missing`); `build_review_verify_report` attaches the result and `build_review_run_report` requires it for `PR_READY` (verify PASS **and** gate pass). It runs against a distinct baseline snapshot, and now also against an **in-memory pre-edit baseline** — `run-review` passes the source it read before applying in place, so the prior in-place skip is closed. It is also wired into the blessed **`run-review-branch` baseline path**: each changed page's source pre→post diff must equal exactly the Class R deltas applied to it, else the seed-cursor advance **and** the PR push are blocked and the run exits non-zero. Tests in `tests/test_rebuild_rediff_gate.py`, `tests/test_cloud_doc_backport.py::RebuildRediffBlessedGateTests`.
  - Target files:
    - [`../tools/cloud_doc_backport.py`](../tools/cloud_doc_backport.py)
  - Done when:
    - `verify-review` is extended to rebuild from edited sources and re-diff against the accepted doc
    - the gate passes only when residuals are zero AND no diff appears outside the intended spans (recorded intentional overrides excepted)
    - a `PR_READY` review run requires the gate to pass

- [x] PR F6: Approval-gated source-table-sync (Workstream Q — §5.1 R9; depends on F1)
  - Status: `done` (to the dry-run/fixture boundary; live activation operator-gated)
  - Note: `tools/source_table_sync.py` — `build_change_requests` turns Class D deltas into change requests (record_id resolved via the F1 sidecar, exact-or-abstain); `plan_apply`/`apply_change_requests` enforce the R9 gates (human approval required, exact-or-abstain skip, content-field only, delta-hash idempotency, GET-verify-after-write) with an injected transport — dry-run by default. The request carries the precise `old_value`/`new_value`: for a table-ROW delta the **changed cell** value is extracted (e.g. `IN1 (DC 12V点烟口)`) so the write targets the cell field, not the whole row markup; `plan_apply` writes `new_value` and abstains when the cell can't be aligned (a row-vs-row write would corrupt the cell). Each live write **GET-checks the cell first** (drift guard): idempotent-skip (`already_applied`) if it already holds the new value, **abstain** (`drift_abstained`) if it holds neither the expected `old_value` nor the new value (never clobber an externally-changed/stale cell), else upsert + GET-verify-after. `run-review` now emits `cloud_doc_backport_source_table_change_request.json`. **Operator follow-up (live):** wire `lark-cli --as bot` as the transport and a populated `record_id` sidecar; the operator approves by deliberately running `apply-source-table --write` (the cloud-doc-backport IM trigger was removed 2026-06-21, #453 — backport is CLI-only). An agent may propose/execute but never approve. Tests in `tests/test_source_table_sync.py`.
  - Target files:
    - [`../tools/cloud_doc_backport.py`](../tools/cloud_doc_backport.py)
    - `tools/source_table_sync.py` (new executor)
  - Done when:
    - backport emits a `source_table_change_request` for Class `D` deltas (table, exact `record_id` from F1, field, old→new, scope, blast radius, evidence, delta hash)
    - a human approves by deliberately running `apply-source-table --write` with explicit `--table-binding`s; an agent may propose/execute but never approve
    - the executor applies only approved requests via `lark-cli --as bot`, with GET-verify-after-write and delta-hash idempotency; ambiguous/duplicate matches abstain
    - content fields only; table schema stays a separate operator-gated action; the change-request plus approval log is retained as the audit trail

- [x] PR F7: Template-sync operator runbook (Workstream Q)
  - Status: `done`
  - Note: added [`dev/template_sync_runbook.md`](dev/template_sync_runbook.md) — the operator procedure to consume a `template_sync_proposal` (F4) and apply Class T changes to `docs/templates/...` via a normal PR, passing the F5 rebuild+rediff gate; with the R6 boundaries (templates-only, untrusted input, no self-merge) and the dedicated agent kept as an explicit deferred follow-up. Cross-referenced from `Feishu_Cloud_Doc_Backport_Design.md` §5.1 R6.
  - Target files:
    - `dev/template_sync_runbook.md` (new)
    - [`../user-guide/hello_auto-doc.md`](../user-guide/hello_auto-doc.md)
  - Done when:
    - a documented operator procedure consumes a `template_sync_proposal` and applies it to `docs/templates/...` via a normal PR, passing the F5 gate
    - the dedicated template-sync agent remains an explicit, deferred follow-up

- [x] PR F8: Feishu `QC_Report` table writeback (Workstream I — M4; depends on F1)
  - Status: `done` (to the dry-run/fixture boundary; table creation + live write operator-gated)
  - Note: `tools/qc_report.py` — `build_qc_report_rows` maps `content_lint` findings to QC_Report rows (run_id, finding_hash, severity, rule, source_ref, resolved record_id, suggested_action); `upsert_qc_report` is idempotent by `finding_hash`, dry-run by default, with a transport-injected live path that skips finding hashes already in the table. **Operator follow-up (live):** create the `QC_Report` Feishu table (schema) and wire a `lark-cli --as bot` transport. Content-row QC status fields stay out of scope. Tests in `tests/test_qc_report.py`.
  - Target files:
    - [`dev/external_table_contracts.md`](dev/external_table_contracts.md)
    - [`../tools/content_lint.py`](../tools/content_lint.py)
  - Done when:
    - `content_lint` findings can be appended/upserted to a `QC_Report` table in dry-run and live modes, idempotent by `finding_hash`
    - rows carry `run_id`, `finding_hash`, severity, rule, source ref, resolved `record_id` (from F1) when available, and suggested action
    - content-row QC status fields stay out of scope

## 6e. Milestone G: Business Closed-Loop Engineering

Milestone status: `done`
Milestone completed: `2026-07-02`
Milestone target: `2026-07`
Milestone note: PR-level breakdown of the 2026-07-02 business closed-loop
analysis (main line: spec intake → source tables → build → revision →
**reflow**; capability lines: TM pre-translation hit rate, PDF review
annotation). The central finding: revision reflow (G1/G2) and TM corpus growth
are one loop — `revision_ledger` records reviewer corrections but nothing
reconciles them (`verdict` stays `PENDING`) and no route feeds accepted
sentence pairs into `Translation_Memory`. Suggested order: G1 → G3 → G7 → G0 →
G2 → G6 → G4 → G5; G0 is the prerequisite for G2 (route-layer changes land in
the split modules, not the 1380-line CLI). G2's live apply and G4 need operator
decisions where marked.
**Operator grant (2026-07-02):** PRs in this milestone may be merged by the
executing agent when the full matching validation set is green; the grant
expires when G1–G7 are done. Each PR updates its item status here in the same
change.

- [x] PR G0: Split `cloud_doc_backport_cli.py` (args / commands / orchestration)
  - Status: `done`
  - Completed: `2026-07-02`
  - Note: 1380-line conductor → `args` (422, argparse + arg-interpretation
    helpers) / `commands` (497, single-command runners) / `orchestration`
    (802, review-branch + baseline + PR flow) / `cli` (222, `main` + the
    compatibility re-export hub). One-way imports (`args` ← `commands` /
    `orchestration` ← `cli`); facade unchanged. One deviation from "tests pass
    unchanged": 39 test patches targeted `cloud_doc_backport_cli.*` seams
    whose call sites moved — retargeted to `cloud_doc_backport_orchestration.*`
    (patching a re-export never intercepted the real call). Also lands the G1
    tail: the orchestration baseline flow feeds the revision ledger
    best-effort (`AUTO_MANUAL_REVISION_LEDGER_PATH`; `off` disables; tests
    isolated via setUpModule).
  - Target files:
    - [`../tools/cloud_doc_backport_cli.py`](../tools/cloud_doc_backport_cli.py)
    - [`../tools/check_maintainability_guardrails.py`](../tools/check_maintainability_guardrails.py)
  - Done when:
    - argparse definitions, per-command run functions, and multi-step orchestration (review-branch / baseline / PR opening) live in separate modules with one-way imports
    - `cloud_doc_backport.py` facade re-exports stay compatible (existing tests pass unchanged)
    - each new module enters the guardrail list; the old 1400-line threshold is replaced by per-module thresholds

- [x] PR G1: Ledger reconcile trigger + similarity verdict (工程①)
  - Status: `done`
  - Completed: `2026-07-02`
  - Note: the trigger is a local piggyback, not CI — the ledger is a local
    artifact under `reports/revision_ledger/` that no workflow can see, so
    every `ingest` (each backport round) now auto-reconciles the previous
    rounds' pending rows (`--no-reconcile` opts out), and `reconcile --auto`
    resolves merge metadata (commit / date / author / `(#PR)`) from git.
    Verdicts gained a similarity layer (best-window partial ratio, threshold
    0.90, min needle 12 chars) over exact containment; `stats` now reports
    `reflow_rate`. Auto-ingest wiring into the backport orchestration lands
    with G0.
  - Target files:
    - [`../tools/revision_ledger.py`](../tools/revision_ledger.py)
  - Done when:
    - reconcile runs automatically each backport round, so ledger rows leave `PENDING` without a human remembering
    - `classify_verdict` uses similarity matching; punctuation/line-break edits no longer misclassify
    - reflow rate (non-PENDING rows / total) is computable from the ledger

- [x] PR G2: Ledger → TM route (工程②)
  - Status: `done`
  - Completed: `2026-07-02`
  - Note: no new write path was built — `tm-candidates` projects accepted
    review-route rows into the suggestion shape the **existing** gated TM
    write path already consumes, and `tm-apply` drives
    `translation_memory_sync.apply_translation_suggestions` (human-approval
    hashes, exact-or-abstain resolution by old target text, GET-verified
    idempotent writes; dry-run unless `--write --tm-binding`). Candidates
    whose old translation is not in the TM abstain and stay visible for the
    manual `bilingual-tm-maintenance` flow. Which base `--tm-binding` names is
    the G4 decision.
  - Target files:
    - [`../tools/revision_ledger.py`](../tools/revision_ledger.py)
  - Done when:
    - accepted revision deltas that rewrite translated prose emit TM pair candidates (source sentence, target sentence, provenance, confidence)
    - candidates are reviewable and only reach live `Translation_Memory` after operator approval
    - reviewer-corrected sentence pairs stop being lost after each review round

- [x] PR G3: TM hit-rate ledger (工程③)
  - Status: `done`
  - Completed: `2026-07-02`
  - Note: `Matcher` counts sentence-level units attempted vs matched (tiny
    texts excluded); the run report gains `units_total` / `units_matched` /
    `hit_rate`, and every run best-effort appends to
    `reports/tm_hit_rate/ledger.jsonl` via the new stdlib-only
    `tools/tm_hit_rate.py` (`ingest` idempotent by run fingerprint; `stats`
    reports overall + per-language-pair rates; legacy counter-less reports are
    reported separately, never averaged in). The baseline number materializes
    with the first operator preprocess run after merge.
  - Target files:
    - [`../.agents/skills/lark-tm-translation-preprocess/scripts/preprocess_lark_docx_with_tm.py`](../.agents/skills/lark-tm-translation-preprocess/scripts/preprocess_lark_docx_with_tm.py)
    - [`../tools/tm_hit_rate.py`](../tools/tm_hit_rate.py)
  - Done when:
    - each preprocess run appends its per-run stats (matched units / total units, by language pair and document) to a cumulative hit-rate ledger under `reports/`
    - a baseline hit-rate number exists so G2/G4 improvements are measurable

- [x] PR G4: TM base convergence (工程④)
  - Status: `done`
  - Completed: `2026-07-02`
  - Note: operator decision (2026-07-02): **B — the env-token base — is the
    canonical write base**; the A/wiki mirror (`X3O8…`/`LUIc…`/`tbl6gK…`) is a
    read-only archive. One config point: `$FEISHU_TRANSLATION_MEMORY_BASE_TOKEN`,
    tables resolved by NAME inside it. Converged: the TM query script no longer
    silently falls back to the A wiki token (missing binding now fails loudly;
    `--wiki-token` remains for explicit archive reads), the docx-preprocess
    script's TM defaults switched from hardcoded A coordinates to env-first +
    by-name table resolution, `bilingual-tm-maintenance` (the write skill) now
    targets the canonical base with an explicit do-not-write archive note, and
    the four docs describing A as live carry convergence banners. Data
    migration/backfill of any rows unique to A is operator work outside this PR.
  - Done when:
    - exactly one TM base accepts writes; skills and scripts resolve it from one config point
    - the retired mirror is marked read-only/archived and no skill defaults to it

- [x] PR G5: PDF annotation renderer MVP (工程⑤)
  - Status: `done`
  - Completed: `2026-07-02`
  - Note: `tools/pdf_annotate.py` (PyMuPDF, new `requirements.txt` dependency)
    searches each finding's evidence text on the built PDF and writes a
    highlight + note (severity / rule / message / `source_ref` / suggested
    action / fix-at-the-source pointer); unlocatable findings degrade to a
    page-1 summary note — no misplaced highlights. `content_lint` itself was
    untouched (its findings.json is consumed as-is). New skill
    `pdf-annotate-qc` registered in AGENTS.md §7 as the PDF counterpart of
    `docx-highlight-changes`. Known limitation: two-column layouts can defeat
    text search; those findings degrade to the summary note.
  - Target files:
    - [`../tools/pdf_annotate.py`](../tools/pdf_annotate.py)
    - [`../.agents/skills/pdf-annotate-qc/SKILL.md`](../.agents/skills/pdf-annotate-qc/SKILL.md)
  - Done when:
    - `content_lint` findings render as highlight + comment annotations on the built PDF (pymupdf text search; page-level fallback when text location fails)
    - each annotation names the source location (table/slot or template) so the reviewer can route the fix
    - output is a sidecar `*_annotated.pdf`; the shipped PDF is untouched

- [x] PR G6: Backport reminder sentinel (工程⑥)
  - Status: `done`
  - Completed: `2026-07-02`
  - Note: content comparison instead of timestamps — `tools/backport_reminder.py`
    compares every InReview doc's live text (lark-cli fetch) against the
    committed render baseline on its review branch (read via `git show`, no
    worktree), in the same normalized text space the backport diffs in. Any
    difference (or a missing baseline) means un-backported edits, and the
    alert clears exactly when a backport advances the baseline — no N-day
    heuristic needed, and no dependency on an unverified doc-meta API.
    Daily workflow `backport-reminder.yml` (02:00 UTC) opens/updates/closes
    the `[backport-reminder]` issue, same pattern as schema-parity; reuses
    the build-queue secrets and `feishu-common-setup`. 2026-07-02 follow-up:
    the repo guard copied from parity was wrong for this workflow — reviews
    happen on the business plane (Hello-Docs mirror), so the sentinel now runs
    in both repos, each against its own bound base.
  - Target files:
    - [`../tools/backport_reminder.py`](../tools/backport_reminder.py)
    - `.github/workflows/backport-reminder.yml`
  - Done when:
    - a review cloud doc with un-backported edits opens/updates a reminder issue (report-only, no auto-backport)
    - the issue closes itself once the backport lands

- [x] PR G7: Intake completeness gate default-on (工程⑦)
  - Status: `done`
  - Completed: `2026-07-02`
  - Note: `spec-extract` now errors (exit 2, no outputs written) when
    `--reference` is absent unless `--skip-completeness` is passed explicitly.
    The second done-when was verified already true in current code — no change
    needed: `enrich_candidates_with_snapshot` escalates multi-match business
    keys to `needs_review` (operation + status + warning), and extract-side
    warnings already force `needs_review` status; the original screening claim
    ("ambiguous only warns") was stale.
  - Target files:
    - [`../tools/source_intake.py`](../tools/source_intake.py)
  - Done when:
    - `spec-extract` without `--reference` fails loudly unless `--skip-completeness` is passed explicitly (no silent skip)
    - ambiguous snapshot keys require review instead of warning

## 6f. Milestone H: Corpus-Driven Template Optimization + Three-Flow Dashboards

Milestone status: `pending`
Milestone target: `after 2-3 live review rounds`
Milestone note: registers the Milestone H proposal from the 2026-07-02
three-flows analysis (operator-approved 2026-07-03). The template flow is the
last one-way leg — templates feed every build but nothing feeds templates.
Suggested order: H1 → H2 → H3. H1 needs no live-round data and can start any
time; H2 waits for the revision ledger to accumulate 2–3 real review rounds;
H3 closes with the dashboards.
**Scope note (2026-07-03):** the "查客服答案" capability (manual-content Q&A
with cited sources, plus its two metrics 客服问题命中率 / 带来源答案比例) is
deliberately **NOT** part of this milestone — it is recorded below as a
separate workstream candidate, to be sized after live rounds and the
stock-manual-onboarding evaluation.

- [ ] PR H1: Template-sentence ↔ corpus reconciliation lint (工程 H1)
  - Status: `pending`
  - Target files:
    - new `tools/template_corpus_lint.py` (or a `content_lint` extension)
    - [`../tools/revision_ledger.py`](../tools/revision_ledger.py) (candidate emission reuses the G2 shape)
  - Done when:
    - translatable template sentences are scanned against the live TM: missing translations emit TM intake candidates (same approval shape as `tm-candidates`); drifted wording emits a flag report
    - the 模板句语料覆盖率 metric has a baseline number
    - first missing-translation candidates reach the human approval queue

- [ ] PR H2: Ledger recurrence miner → template proposals (工程 H2)
  - Status: `pending`
  - Note: needs 2–3 live review rounds of ledger data before results are meaningful
  - Target files:
    - [`../tools/revision_ledger.py`](../tools/revision_ledger.py) (`template-candidates` subcommand)
  - Done when:
    - accepted/edited rows cluster by normalized machine text; the same-direction correction hitting ≥N targets with template-origin source (reuse the family-identical check) projects a `template_sync_proposal` draft
    - the first corpus-driven template fix is applied by a human through the existing Workstream Q runbook
    - the 模板复发修正率 metric is computable

- [x] PR H3: Three-flow dashboards — ops face + value face (工程 H3, scope expanded 2026-07-03; done 2026-07-03)
  - Status: `done` — `tools/flow_dashboard.py report` emits both faces
    (markdown + json under `reports/flow_dashboard/`) with monthly buckets;
    `pdf_annotate` appends a run ledger (`--backfill-summary` for history);
    the two template-flow metrics correctly show `no_data` until H1/H2 land.
    First real run immediately surfaced an actionable signal: reflow rate 0%
    because landed deltas were never stamped `accepted` in the ledger.
  - Note: expanded from the original five-metric health report into a
    **two-face dashboard**. Ops face (system health, for the operator):
    reflow rate, TM hit rate, second-revision rate, template recurrence rate,
    template-sentence corpus coverage. Value face (output proof, for
    stakeholders): audited-PDF count, model/region/language coverage counts,
    stale/duplicate/drift findings count, revision-reflow counts, TM candidate
    counts, and the time-saved-per-manual narrative metric (needs an operator
    baseline estimate of the pre-system manual effort). Start recording
    immediately even where today's value is zero — a metric without history
    cannot show a trend. Includes a small run ledger for `pdf_annotate`
    (mirroring `tools/tm_hit_rate.py`) so the audited-PDF count has a data
    source.
  - Target files:
    - new aggregator tool under `tools/`
    - [`../tools/pdf_annotate.py`](../tools/pdf_annotate.py) (run-ledger append)
  - Done when:
    - one command emits both dashboard faces from existing artifacts (ledger / hit-rate ledger / content_qc reports / configs / catalog)
    - monthly trend review is possible for every metric that has history

### Workstream candidate (recorded, not scheduled): 查客服答案

Manual-content Q&A with cited sources — answer product questions from the
built manuals (catalog + TM + built HTML/PDF), always with a source reference.
Carries its own two metrics: 客服问题命中率 and 带来源答案比例. Natural
downstream of stock-manual onboarding (content must be in the system before it
can be cited). Size it as its own workstream after Milestone H and the
stock-onboarding pilot; do not let it slip into an "entry-point polish" PR.

## 6g. Milestone I: Unknown-Unknown Probes + Handover Assurance

Registered 2026-07-12 (operator-approved) from the workspace census ×
esp-docs comparison (see the espressif/esp-docs defensive-subsystem
inventory). Theme: auto-manual's defenses concentrate on **content
correctness**; the blind spots concentrate on **publication
sustainability** (links, language parity, environment drift, warning
debt) and **maintainer hand-over**. These are sensors first, fixes
second — each probe converts an unknown-unknown into a measured known.

- [x] PR I1: Language-tree parity check (探针·跨语言结构漂移; done 2026-07-13, #657)
  - Status: `done` — `tools/check_docs_lang_parity.py` wired into check:
    foreign-shell (script ratio), foreign lang-tag blocks, per-lang page-set
    completeness; known-exceptions CSV keeps pre-existing debt green. All
    three historical incident classes replicated in tests and tripped.
    First run caught live debt: the us-en line inherits the trilingual
    page_shared/en preface — trim decision pending with the operator.
- [x] PR I2: Build-warning ratchet (探针·警告债棘轮; done 2026-07-13, #658)
  - Status: `done` — `tools/warning_ratchet.py` + `-w` capture on every
    Sphinx run; staged enforcement (in-build hook reports by default,
    `AUTO_MANUAL_WARNING_RATCHET=strict` fails; standalone CLI always
    strict, missing baseline exits 2). sphinx-html baseline seeded; flip
    the in-build default to strict after 2–3 stable queue rounds. xelatex /
    extractor streams reuse the same engine when attached.
- [x] PR I3: Environment pinning + version provenance (探针·环境漂移; done 2026-07-13, #656; priority raised after #648)
  - Status: `done` — requirements.lock; `tools/toolchain_provenance.py`
    single collector (python/packages/xelatex/pandoc/InDesign/lock sha);
    doctor prints the block; release manifest embeds it (JSON + CSV).
    Probe caught real drift on day one (venv rebuilt on Python 3.14).
- [x] PR I4: Printed-URL inventory (探针·印刷外链; done 2026-07-13)
  - Status: `done` — `tools/printed_url_inventory.py` scan/check/liveness;
    tracked `data/printed_url_inventory.csv` (first scan: 6 targets — 4
    warranty mailboxes, jackery.jp, jp mailbox; liveness clean); QR targets
    register by hand in `data/printed_url_manual_entries.csv`; monthly ops
    rhythm updated (ops guide §4.8).
- [x] PR I5: Feishu base rebuild drill (探针·灾备演练; first drill run 2026-07-13)
  - Status: `done` — drill protocol + first measured run in ops guide §4.7:
    scratch base + 2 tables + fields + 25 seed rows restored from repo
    artifacts alone in **86s** (read-back verified). Headline finding: the
    schema mirror covers only 2/20 business tables — the other 18 tables'
    field structures live only in Feishu. Follow-up CLOSED same day:
    whole-base export committed (`bitable_schema/business_base_manifest.json`
    21 tables/366 fields + `tm_base_manifest.json` 2/58), complex fields
    carry rebuild detail (lookup source, link target, formula property);
    re-export rhythm documented in ops guide §4.7.
- [x] PR I0: ONBOARDING.md + cold-start drill protocol (接手保障)
  - Status: `done` — repo-root ONBOARDING.md is the single first-hour
    entrypoint (two-plane map, bus-factor register, golden-path drill);
    its quality is enforced by the quarterly cold-start drill (§7 of the
    file): a fresh maintainer or memory-less agent runs the golden path
    from repo docs alone; every blocker is a doc bug fixed same-day and
    logged in code_optimization_log.md.
- [x] PR I6: Repo-health metrics on the ops dashboard (接手保障·复杂度可见; done 2026-07-13)
  - Status: `done` — `repo_health_metric` on the ops face: worktree count,
    dirty files, tracked `docs/_build` files, tools module count and the
    largest module — complexity growth is now a monthly number; a rising
    trend is the signal to open a simplification workstream.

## 6h. Milestone J: Asset Loop — 图片与 .ai 源的单一真相

Registered 2026-07-13 (operator-approved decisions: .ai lives in the Feishu
attachment column; existing text-burned illustrations get scheduled textless
rework; temporary crops/placeholders register as explicit debt when the
publish gate lands; the maintainer registers on designers' behalf). Extends
the single-source principle to assets: the .ai file is the source, exports
are projections, and a textless base image + data-layer text makes an asset
language-neutral (the LCD-hero precedent).

- [x] PR J0: Asset census + registry (P0; done 2026-07-13)
  - Status: `done` — the initial Feishu census is retained as historical input,
    while the build-facing mirror is `data/asset_registry.csv`; the legacy table
    is not consumed by the new asset pipeline. After the registered vector
    harvest in the stacked asset PRs, the current mirror is
    **63 成品 / 3 临时替代 / 4 缺失 / 1 隔离** (the missing list IS the
    design-side request list); repo mirror `data/asset_registry.csv`;
    naming contract `<asset_key>[-<lang>].{pdf,png}`; ops guide §4.9.
- [ ] PR J1: Asset resolver + publish gate (P1)
  - Status: `in progress` — `build.py asset-check` validates registry exports,
    and final bundle assembly now resolves semantic `asset:` references after
    review overlay with target/status gates, frozen usage/registry sidecars,
    review round-trip provenance, and legacy-path accounting. Current templates
    are not yet bulk-migrated, and the registry mirror is not yet synced from
    the new Base tables.
  - Done when: current templates resolve assets through the registry (missing
    asset → check error instead of silent placeholder); semantic bundle
    consumption always refuses `🔧临时替代`, `❌缺失`, and `⛔隔离` rows;
    registry mirror joins sync-data (the capability-gate integration pattern).
- [ ] PR J2: .ai sources into the pipeline (P2)
  - Status: `in progress` — deterministic `asset-intake` now freezes and splits
    the JE-1000F US PDF-compatible `.ai` master into verified archive/previews,
    recipe exports, manifest/CSV, and a reproducible ZIP; its full source hash
    and verified Base record pointer are recorded in `data/asset_sources.csv`.
    The three dedicated `04_资产*` tables now exist, their live bindings are
    frozen in `data/asset_base_bindings.json`, and the AI/ZIP/manifest attachment
    round trip plus 10 definition / 142 export rows have been verified. The
    registry mirror still needs to join `sync-data`, and later native-artboard
    automation needs evidence from more than this PDF-compatible master.
  - Done when: designers' .ai files live in the registry's attachment
    column with content hashes; the one-page designer workflow (deliver →
    register → sync) is documented; optional ExtendScript batch export
    (the indesign_finalize.jsx precedent) evaluated.
- [ ] PR J3: Publish full assembly (P3)
  - Status: `pending`
  - Done when: the release bundle includes the InDesign package (INDD +
    IDML + Links/ + font manifest + parity report; delivery.py reused);
    the release manifest gains an `assets` section (key + hash + status +
    .ai pointer — the I3 toolchain-provenance pattern); QR asset targets
    cross-check the printed-URL inventory (I4).

## 6i. Milestone K: Enterprise Ops Hardening + Platform Consolidation

Milestone status: `pending`
Milestone target: `tier-driven, no calendar — Tier 1 = current real execution (4 items); Tier 2 = on business-pain trigger; Tier 3 = requires dedicated capacity`
Milestone note: registered 2026-07-17 as the PR-level breakdown of Workstreams
T (Phase 0), U (Phase 1), and the Workstream V design gate (Phase 2) from the
production-readiness review
([`reviews/production_readiness_review_2026-07-17.md`](reviews/production_readiness_review_2026-07-17.md)).
Theme: the review found the code plane enterprise-grade but the operating plane
not. V implementation is deliberately **not** broken down here — only its
design doc (K15); implementation PRs get registered after the design is
approved, mirroring the Workstream N gating. Items touching
`.github/workflows/**`, `requirements.txt`, git history, or queue semantics are
operator-gated per `AGENTS.md` §8.7 and are marked below.
**Execution tiers (operator triage 2026-07-17):** so the list reads as "4 in
flight", not "15 pending", the items are grouped into three tiers below.
Tier assignment governs execution order only; the T/U/V phase mapping and each
item's technical scope are unchanged. Tier 1 items are `pending`; Tier 2/3
items are `deferred` with an explicit `Trigger:` line and flip to `pending`
when their trigger fires (per §1 update rules). The operator's triage named 12
items; **K3, K14 (→ Tier 2) and K6 (→ Tier 3) are provisional placements by
the same logic — re-tier in review if wrong.**

### Tier 1 — 当前真实执行 (current real execution)

Entry rule: no trigger needed. These are the next platform slices between
business deliveries, in this order: K4 → K5 → K7 → K1.

- [ ] PR K4: Scheduled versioned export of the phase2 source tables + restore runbook (T4)
  - Status: `in_progress` (implementation and scratch restore drill merged;
    first nightly artifact verification failed on 2026-07-19)
  - Delivery merged: `2026-07-17`
  - Note: delivered as `tools/bitable_content_backup.py` (export / restore /
    verify, reusing the `bitable_schema` primitives; restore is dry-run by
    default, requires an explicit target token, refuses non-empty tables, and
    never writes formula/lookup/link columns), the nightly
    `phase2-content-backup.yml` workflow (00:30 UTC + dispatch, 90-day
    artifact retention, sentinel Issue on failure), the
    `phase2-content-backup` env preset, and ops guide §4.7b (restore runbook
    + drill record). **Live drill 2026-07-17:** TM base full export 10s /
    business base 21 tables 58s; scratch-base restore 888/888 rows verified
    (~25s). The drill caught real drift on day one: select options added to
    the live base after the schema snapshot made batch-create reject the
    whole table (800030005) — restore now pre-syncs missing select options
    via field-update. Known limitation (recorded in the runbook): multi-select
    cells restore as one concatenated option; fidelity fix is a follow-up.
    **First-nightly verification 2026-07-19:** Actions run
    [`29672759849`](https://github.com/Bingboom/auto-manual/actions/runs/29672759849)
    was green, and every included CSV passed manifest row-count and SHA-256
    checks, but the artifact was incomplete: business exported 18 tables /
    850 rows and missed `01_数据入库`, `02_文档构建`, and
    `能力→章节映射规则`; TM exported 0 tables and missed
    `Translation_Memory` and `Terms`. The exporter returns non-zero for
    missing tables, but the workflow pipes it through `tee` without
    `pipefail`, so the shell reports `tee`'s zero exit code. K4 is reopened
    until the workflow failure is propagated and a subsequent artifact
    contains the complete 21 + 2 table set. The restore scratch Base
    `演练-K4内容恢复-20260717` was moved to the Feishu recycle bin on
    2026-07-20 after its exact token and owner were rechecked; an exact-name
    search then returned no result.
    **Exit-propagation fix landed 2026-07-20:** both export steps now declare
    `shell: bash` explicitly (GitHub's DEFAULT run shell is `bash -e {0}`
    without pipefail; the explicit form is `bash --noprofile --norc -eo
    pipefail {0}`) — verified by local simulation of both shells (0 vs 1).
    Review of the false-green run also found it had executed the
    "Close tracking issue on recovery" step, so a false green would silence
    an already-open sentinel too.
    **Root cause proven 2026-07-20 (plane mismatch, NOT bot permissions):**
    the same bot reads both canonical bases fully from the operator machine;
    the CI failure signature matches the OLD engineering-plane base exactly
    (18/21 manifest names present; `数据入库表`/`文档构建表` are the old
    names of the two missing `0x_` tables; `能力→章节映射规则` absent), and
    auto-manual's `FEISHU_PHASE2_BASE_TOKEN` secret predates the 06-11 base
    migration — it is the ENGINEERING-plane binding, correct for
    parity/promote, wrong for this backup; the TM secret is invalid for the
    base API (→ 0 tables, mechanism reproduced). Fix: the workflow guard is
    flipped to run ONLY in Hello-Docs (business plane), whose secrets bind
    the new bases the manifests describe; sentinel Issues open there (the
    backport-reminder precedent). Remaining to close K4: one complete 21 + 2
    artifact from a Hello-Docs run (dispatch once after merge, or wait for
    the nightly).
  - Original note: the I5 drill proved schema restore works (86s from repo
    artifacts) but covers structure only — table CONTENT had no point-in-time
    backup; a destructive Bitable edit was unrecoverable. Read-only export, no
    source-table writes.
  - Target files:
    - [`../tools/data_snapshot.py`](../tools/data_snapshot.py)
    - [`../tools/bitable_schema.py`](../tools/bitable_schema.py)
    - [`../user-guide/closed_loop_ops_guide.md`](../user-guide/closed_loop_ops_guide.md)
  - Done when:
    - a scheduled workflow exports full phase2 table content to a dated, retained artifact (retention window recorded)
    - a written restore runbook extends ops guide §4.7 from schema-rebuild to content-restore
    - one content-restore drill has been run and timed against a scratch base
    - one scheduled artifact has been opened and verified to contain all 21 business + 2 TM tables, with a non-zero export exit code reaching the job result

- [x] PR K5: Queue-failure alerting via the sentinel Issue pattern (T5)
  - Status: `done`
  - Completed: `2026-07-17`
  - Note: delivered as the reusable composite action
    `.github/actions/queue-sentinel-issue/` (open-on-failure / close-on-
    success via github-script; cancelled runs open nothing) wired as the
    final `if: always()` step of all three queue workflows with per-workflow
    labels (`queue-failure-build` / `-draft` / `-start-review`).
    **Issue titles carry the record_id**, so the open/close lifecycle is
    per-record: the next successful run of the same record closes its own
    issue (batch runs use a `batch` title). The failure body names the
    writeback silent-divergence case (build succeeded, Bitable row stale) —
    exit-code propagation was verified: writeback failures join the queue
    runner's `failures` list, so the job fails and the sentinel fires.
    Wiring is pinned by `tests/test_queue_failure_sentinel.py` (permissions,
    last-step position, `always()`, distinct labels). Operator-facing doc:
    ops guide §3b. First live firing will be observed on the next real
    queue failure — nothing to pre-verify beyond a dispatch test.
  - Original note: touches `.github/workflows/**` → operator-gated. Today
    `cred-health-check` / `feishu-schema-parity` / `backport-reminder` open and
    close Issues, but a failed build-queue run only writes `FAILED …` to the
    Bitable row and fails the Actions run — nobody is notified unless watching.
  - Target files:
    - [`.github/workflows/feishu-build-queue.yml`](../.github/workflows/feishu-build-queue.yml)
    - [`.github/workflows/feishu-draft-build-queue.yml`](../.github/workflows/feishu-draft-build-queue.yml)
    - [`.github/workflows/feishu-start-review.yml`](../.github/workflows/feishu-start-review.yml)
  - Done when:
    - a failed queue/draft/start-review run opens or updates a tracking Issue (same open/close lifecycle as the sentinels), carrying record_id, target, and the failure summary
    - the Issue closes when a subsequent run of the same record succeeds
    - writeback-failure (build succeeded, Bitable write failed) alerts too — it is the silent-divergence case

- [ ] PR K7: InDesign finalize — version lock + second host (T7)
  - Status: `in_progress` (code/doc legs merged; remaining = the operator's
    one-time second-host verification run, tracked in the runbook §3 table and
    the ONBOARDING §3 register row)
  - Note (2026-07-17 delivery): version pin committed at
    `tools/idml/indesign_version_pin.json` (seeded live from the operator Mac:
    `Adobe InDesign 2026 21.0.1.6`); `tools/indesign_finalize.py` now checks
    the pin at finalize time via the I3 collector — **mismatch refuses to run**
    (`--allow-version-mismatch` overrides, recorded in the report's
    `toolchain` block), plus `--check-host` (runbook step) and `--write-pin`
    (deliberate-upgrade re-seed). Exact-match policy: even patch-level drift
    makes finalize output non-comparable, so upgrades re-pin instead of
    loosening. Second-host procedure:
    [`dev/indesign_second_host_runbook.md`](dev/indesign_second_host_runbook.md)
    (prereqs incl. fonts from the handoff manifest, five verification steps,
    upgrade discipline: all hosts together). ONBOARDING §3 register row
    updated from "无版本锁（已知风险）" to the documented recovery path.
    `--check-host` verified live on the operator Mac (match). **Second-host
    preflight 2026-07-20:** `ArriettyMac-mini.local` also reported an exact
    match for `Adobe InDesign 2026 21.0.1.6`. No known-good IDML was present
    in the downloaded-main checkout, so finalize steps 3-5 were not run and
    this is deliberately not recorded as the one-time end-to-end verification.
    11 unit tests.
  - Original note: the top delivery SPOF: the IDML→final-PDF leg runs only on
    the operator's Mac, no CI, no version lock (ONBOARDING §3 known risk). This
    PR is documentation + provenance binding, not automation.
  - Target files:
    - [`../tools/idml/indesign_finalize.jsx`](../tools/idml/indesign_finalize.jsx)
    - [`../tools/toolchain_provenance.py`](../tools/toolchain_provenance.py)
    - [`../ONBOARDING.md`](../ONBOARDING.md)
  - Done when:
    - the expected InDesign version is pinned in provenance (a mismatch at finalize time warns loudly, reusing the I3 collector)
    - a second-host setup procedure is documented and verified once end-to-end on a machine that is not the operator's
    - the bus-factor register entry for this leg is updated from "known risk" to "documented recovery path"

- [x] PR K1: Make `requirements.lock` the CI/RTD install source (T1)
  - Status: `done`
  - Completed: `2026-07-17`
  - Note: all 10 `pip install -r requirements.txt` sites switched to the lock
    (manual-validation ×7 jobs, review-preview, feishu-common-setup — which
    also covers the queue/backup/sentinel workflows — and .readthedocs.yaml),
    plus the pip cache key (`cache-dependency-path`) moved to the lock so
    caches invalidate on pin changes. Lock coverage of every requirements.txt
    top-level dep pre-verified; the PR's own CI run is the on-Linux install
    proof. requirements.lock header now carries the refresh WHEN/HOW
    (clean 3.12 venv, freeze, commit lock+txt together); requirements.txt
    header states it is human-facing ranges only and fixes the stale
    "Python >= 3.9"; ONBOARDING §8 "构建环境未锁定" line corrected.
    Deliberate cut: the standalone ruff/mypy tool installs in CI stay
    unpinned (lint toolchain, not build deps).
  - Original note: touches `.github/workflows/**` → operator-gated. The lock
    exists (Milestone I3) but no workflow installs from it, so CI drifts from
    the pinned snapshot silently.
  - Target files:
    - [`.github/workflows/manual-validation.yml`](../.github/workflows/manual-validation.yml)
    - [`../.github/actions/feishu-common-setup/action.yml`](../.github/actions/feishu-common-setup/action.yml)
    - [`../.readthedocs.yaml`](../.readthedocs.yaml)
    - [`../requirements.txt`](../requirements.txt)
    - [`../ONBOARDING.md`](../ONBOARDING.md)
  - Done when:
    - every CI python-setup path and ReadTheDocs install from `requirements.lock`; `requirements.txt` stays the human-facing range file
    - a documented lock-refresh procedure exists (when and how to regenerate)
    - the stale "Python >= 3.9" comment in `requirements.txt` and the stale "no lock file" note in `ONBOARDING.md` §3 are corrected

### Tier 2 — 业务痛点触发后执行 (execute when the business pain fires)

Entry rule: each item starts only when its named trigger is observed in real
production (the discovery-engine rule, roadmap §5) — then it legitimately
jumps the queue. Until then it stays `deferred` and exerts no pressure.

- [ ] PR K2: Pin and cache the TeXLive install in queue workflows (T2)
  - Status: `deferred`
  - Trigger: queue wall-time or Actions-quota pain observed again (dashboard
    queue metrics, or a quota warning/bill).
  - Note: touches `.github/workflows/**` → operator-gated. Today the full TeX
    stack is apt-installed unpinned on every dispatch (~minutes per run,
    multiplied by every queue build; the org Actions quota has been exhausted
    once already).
  - Target files:
    - [`.github/workflows/feishu-build-queue.yml`](../.github/workflows/feishu-build-queue.yml)
    - [`.github/workflows/feishu-draft-build-queue.yml`](../.github/workflows/feishu-draft-build-queue.yml)
  - Done when:
    - the TeX package set is version-pinned (or moved into a prebuilt container image) and cached, so a warm run skips the apt install
    - cold/warm run times are recorded once in the PR body as the baseline
    - build output is byte-identical before/after (release-manifest sha256 comparison on one target)

- [ ] PR K3: Route new binary artifacts to Git LFS (T3)
  - Status: `deferred`
  - Trigger: repo-size / clone-time / CI-checkout pain becomes visible (the
    repo-health metric on the ops dashboard), or the operator makes the
    storage-policy call proactively. **Provisional Tier 2 placement** (not in
    the operator's 2026-07-17 triage): the new-binaries-only half is cheap,
    but the policy decision and the LFS interaction with the Hello-Docs
    mirror / CI checkout make it more than a filler slice — re-tier if wrong.
    Caveat: history grows every week this waits; the trigger should be read
    generously.
  - Note: operator-gated twice over — it changes `.gitattributes` storage
    policy for `docs/_build` (adjacent to Deferred 5, but storage-only: no
    workflow-semantics change), and the history-rewrite question (pack already
    ~148 MiB with two 18.9 MB PDFs) is an explicit operator decision this PR
    only records, never executes. CI runners and contributor docs must gain
    `git lfs install`.
  - Target files:
    - [`../.gitattributes`](../.gitattributes)
    - [`../ONBOARDING.md`](../ONBOARDING.md)
  - Done when:
    - new PNG/PDF/DOCX blobs under `docs/_build/**` and `docs/templates/word_template/**` enter LFS instead of raw history
    - CI checkout and local onboarding steps handle LFS transparently
    - the history-rewrite decision (do it / defer it / never) is recorded with the size evidence, as its own operator call

- [ ] PR K8: Single Feishu transport client (U1)
  - Status: `deferred`
  - Trigger: a live sync/backport failure attributable to the transport gap —
    rate-limit (429) errors, a concurrent-sync race on `data/phase2/*.csv`,
    or another divergence bug between the duplicated runners.
  - Note: five-plus independent `run_lark_cli_json` implementations exist; the
    sync path has zero retry/backoff/rate-limit and no file locking. May land
    in slices (consolidate first, then retry/lock), but one module owns the
    boundary at the end.
  - Target files:
    - [`../tools/feishu_record_transport.py`](../tools/feishu_record_transport.py)
    - [`../tools/queue_lark_ops.py`](../tools/queue_lark_ops.py)
    - [`../tools/queue_bound_lark_ops.py`](../tools/queue_bound_lark_ops.py)
    - [`../tools/listen_build_queue_lark.py`](../tools/listen_build_queue_lark.py)
    - [`../tools/spec_master_rebuild.py`](../tools/spec_master_rebuild.py)
    - [`../tools/bitable_schema.py`](../tools/bitable_schema.py)
  - Done when:
    - exactly one module builds and runs `lark-cli` invocations, with tested retry/backoff and rate-limit handling (Feishu ~20 QPS, 429 responses)
    - the listed call sites (plus sync/backport/intake `lark-cli` argv builders) route through it; no independent JSON-runner remains
    - `data/phase2/*.csv` snapshot writes take a file lock so concurrent syncs cannot interleave

- [ ] PR K11: Structured logging baseline in queue and build orchestration (U4)
  - Status: `deferred`
  - Trigger: after K5 alerting lands, the first time diagnosing a queue
    failure from print output costs real time — the alert tells you THAT it
    failed; this item fires when finding out WHY hurts.
  - Note: zero `logging` imports and 423 `print()` calls today. Scope is the
    baseline, not a repo-wide sweep: queue orchestration and build entry paths
    first; user-facing CLI output stays `print`.
  - Target files:
    - [`../tools/queue_orchestration.py`](../tools/queue_orchestration.py)
    - [`../tools/build_runtime.py`](../tools/build_runtime.py)
  - Done when:
    - queue and build orchestration emit leveled `logging` records (level via env), with run/record correlation ids on queue paths
    - Actions logs keep at least today's readability; `$GITHUB_STEP_SUMMARY` output is unchanged
    - a short convention note documents what logs vs what prints, so the sweep can continue incrementally

- [ ] PR K13: Data-driven language onboarding (U6)
  - Status: `deferred`
  - Trigger: the next new-language/region onboarding request lands (the
    natural moment: do K13 first, then onboard the language through the new
    data-driven path as its live proof).
  - Note: adding a language today edits four hardcoded Python enumerations
    plus paired golden-test expectations (`setup-map.md` §code registration) —
    a data problem solved with code edits, which fails at 50 lines.
  - Target files:
    - [`../tools/signal_words.py`](../tools/signal_words.py)
    - [`../tools/sync_data_models.py`](../tools/sync_data_models.py)
    - [`../tools/localized_copy.py`](../tools/localized_copy.py)
    - [`../tools/manual_copy_source.py`](../tools/manual_copy_source.py)
  - Done when:
    - language registration is data/config-driven (declared once, consumed by all four surfaces); an unknown language fails with a clear message, not a KeyError
    - adding a test language in fixtures requires zero Python edits, proven by a test
    - [`../.agents/skills/new-region-line/SKILL.md`](../.agents/skills/new-region-line/SKILL.md) and its setup-map drop the code-registration step

- [ ] PR K14: Release labeling + rollback runbook (U7)
  - Status: `deferred`
  - Trigger: the first real rollback need (a shipped manual must be reverted
    or re-delivered from a prior state), or the business asks for turnaround
    commitments. **Provisional Tier 2 placement** (not in the operator's
    2026-07-17 triage) — re-tier in review if wrong.
  - Note: manifests already carry git SHA, toolchain provenance, and per-output
    sha256 — traceability exists, labeling and the recovery procedure don't.
    Complements (does not replace) E1 snapshot freezing.
  - Target files:
    - [`../tools/release_manifest_service.py`](../tools/release_manifest_service.py)
    - [`../user-guide/closed_loop_ops_guide.md`](../user-guide/closed_loop_ops_guide.md)
  - Done when:
    - each publish gets a stable release identifier (git tag or release record) bound to its manifest
    - a written rollback runbook covers: re-deploy a prior Vercel build, re-deliver a prior Word/PDF from its manifest, and rebuild from a prior `Git_ref`
    - one rollback drill has been executed and timed

### Tier 3 — 必须有工程资源或专门窗口 (requires dedicated capacity or a protected window)

Entry rule: do NOT start these as between-delivery filler — each needs either
a second maintainer, formally allocated platform time, or a consciously shaped
low-delivery window (the Workstream U/V organizational triggers). Starting
them without that capacity risks a half-moved subsystem or an unfinished
semantic change sitting in the tree while business work resumes.

- [ ] PR K9: Package the flat `tools/` namespace, one subsystem per PR (U2)
  - Status: `deferred`
  - Trigger: dedicated capacity (second maintainer or allocated platform
    time). Each subsystem move is individually small, but the wave only pays
    off completed — partial packaging leaves two import styles coexisting.
  - Note: consistent with Deferred 3's rationale — this is the gradual
    boundary cleanup it calls for, explicitly NOT a big-bang rename: one
    subsystem per PR, behavior-preserving moves, import-compatible facades,
    guardrail entries updated per move. Queue first (largest family, ~37
    files), then word / backport / intake / sync / checks, following the
    proven `tools/idml/` pattern.
  - Target files:
    - [`../tools/`](../tools)
    - [`../tools/check_maintainability_guardrails.py`](../tools/check_maintainability_guardrails.py)
    - [`dev/orchestration_module_map.md`](dev/orchestration_module_map.md)
  - Done when:
    - queue/word/backport/intake/sync/check subsystems live under packages with `__init__` facades keeping existing import paths working
    - guardrail thresholds move to the new paths in the same PR as each move
    - the ownership map reflects the package boundaries, and no prefix-family flat modules remain at `tools/` root for the moved subsystems

- [ ] PR K10: Extract target/config resolution out of the `build_docs` facade (U3)
  - Status: `deferred`
  - Trigger: dedicated capacity; natural window = alongside or just before
    the K9 queue-subsystem move (same import surfaces).
  - Note: 8 non-build modules (including queue code) import the 838-line
    facade just for `load_config` / `resolve_build_targets` /
    `build_root_for_target`, dragging Sphinx/export imports into queue and
    check paths.
  - Target files:
    - [`../tools/build_docs.py`](../tools/build_docs.py)
    - [`../tools/utils/path_utils.py`](../tools/utils/path_utils.py)
  - Done when:
    - target/config resolution lives in a lightweight `tools/utils/` module with no Sphinx-side imports
    - queue/check/sync-review/release importers stop importing `build_docs`; the facade re-exports for compatibility
    - importing a queue module no longer transitively imports the export stack (guarded by an import-time test, the Milestone A PR 1 pattern)

- [ ] PR K12: Atomic queue claim + cross-workflow concurrency contract (U5)
  - Status: `deferred`
  - Trigger: dedicated capacity, or the concurrency assumption breaks (cron
    re-enabled, a second dispatcher appears, or a double-claim near-miss is
    observed). Semantic change to the queue contract — needs a protected
    window and operator attention, not filler time.
  - Note: operator-gated — touches queue semantics, `.github/workflows/**`,
    and [`dev/external_table_contracts.md`](dev/external_table_contracts.md) /
    [`dev/queue_state_model.md`](dev/queue_state_model.md). Today the RUNNING
    write is a soft claim (no compare-and-swap) and the three queue workflows
    share no concurrency group — safe only because cron is disabled and
    dispatch is single-operator. The parallel build matrix is a recorded
    follow-up AFTER the claim lands, not part of this PR.
  - Target files:
    - [`../tools/queue_transitions.py`](../tools/queue_transitions.py)
    - [`../tools/queue_orchestration.py`](../tools/queue_orchestration.py)
    - [`dev/queue_state_model.md`](dev/queue_state_model.md)
  - Done when:
    - claiming a row is atomic (claim token + TTL, or re-read-and-verify CAS) so two concurrent dispatches cannot both process the same record — covered by a fixture test
    - stale claims (worker died mid-run) expire and become re-claimable, with the expiry documented in the queue state model
    - the three queue workflows share an explicit concurrency contract, and the external-table contract doc gains the claim fields

- [ ] PR K15: Review-branch propagation design doc (V — design gate only)
  - Status: `deferred`
  - Trigger: dedicated capacity for sustained design + review attention
    (roadmap Phase 2 entry: Workstream T exit criteria passed). Business pain
    accelerates it: when the dashboard shows template-fix propagation
    measurably eating delivery capacity, this jumps the queue.
  - Note: the frozen-copy review-branch model is the review's #1 scale wall
    (a shared-template fix reaches zero open branches;
    [`../tools/check_review_branch_sync.py`](../tools/check_review_branch_sync.py)
    is advisory by design). Implementation is deliberately not scheduled here:
    this PR delivers the design doc; implementation PRs get registered only
    after operator approval — the same gating as Workstream N. Touches
    `docs/_review` semantics conceptually, which is exactly why Deferred 5
    applies to the implementation and not to the design.
  - Target files:
    - `architecture/Review_Branch_Propagation_Design.md` (new)
  - Done when:
    - the design covers: per-target-derivative-only review branches, a pinned-but-advanceable shared-template reference, automated per-branch bump PRs showing the rendered diff, authored-edit protection (classify-or-abstain, reusing the `sync-review` merge_params discipline), and migration of the existing open branches
    - blast radius, failure modes, and the propagation-lag metric are specified
    - the operator has approved or amended the design, recorded in the doc header

- [ ] PR K6: Governance floor — CODEOWNERS, secret scanning, dependabot (T6)
  - Status: `deferred` (severable slice delivered 2026-07-17; remainder waits
    on the trigger below)
  - Slice delivered (2026-07-17): the pre-authorized secret-scanning +
    dependabot half. `secret-scan` job in `manual-validation.yml` (gitleaks
    v8.30.1 pinned + checksum-verified, working-tree scan) with
    `.gitleaks.toml` encoding the repo policy — Feishu RESOURCE tokens and
    business-key vocabulary are allowlisted BY LINE SHAPE, credentials are
    not; tuned against a full local scan (31 findings triaged: all resource
    tokens/fixtures, zero credentials) and canary-verified both ways (clean
    tree = 0, planted ghp_/FEISHU_APP_SECRET shapes = caught).
    `.github/dependabot.yml`: github-actions weekly grouped bumps; pip and
    npm in security-only mode (routine Python pins go through the K1
    lock-refresh procedure, not per-package bumps). Remaining for the full
    K6: CODEOWNERS + server-side branch-protection verification.
  - Trigger (remainder): a second reviewer/maintainer exists (CODEOWNERS
    routing is mostly symbolic while one person reviews everything — its
    value activates with the Workstream U organizational trigger).
    **Provisional Tier 3 placement** (not in the operator's 2026-07-17
    triage) — re-tier if wrong.
  - Note: touches `.github/**` governance surfaces → operator-gated. CODEOWNERS
    is also the enabler for Workstream V's distributed-review model (K15).
  - Target files:
    - `.github/CODEOWNERS` (new)
    - `.github/dependabot.yml` (new)
    - [`.github/workflows/manual-validation.yml`](../.github/workflows/manual-validation.yml)
  - Done when:
    - CODEOWNERS routes review by area (tools/queue vs docs/templates vs workflows), with the operator as owner of the compliance-sensitive surfaces
    - a push/PR secret-scanning gate runs in CI; dependabot files version-bump PRs (grouped, low noise)
    - server-side branch protection settings are verified against `AGENTS.md` §8 and the verification is recorded

## 7. Deferred: Do Not Touch Yet

- [ ] Deferred 1: large multi-target conditional-content redesign
  - Status: `deferred`
  - Why deferred:
    - the `03_product_overview` pilot was rolled back (#295/#296); a repo-wide prose rewrite is still too broad
    - re-launch is tracked as Workstream N in [`optimization_project.md`](optimization_project.md), gated on the schema and review workflow in [`architecture/Long_Form_Content_Block_Design.md`](architecture/Long_Form_Content_Block_Design.md)
    - the safe near-term steps are short-copy coverage (Workstream L) and page_registry authority (Workstream M), not a full template rewrite

- [ ] Deferred 2: Word/PDF backend replacement or export-stack rewrite
  - Status: `deferred`
  - Why deferred:
    - export flow is a delivery-critical surface
    - quality-gate and traceability hardening should happen first

- [ ] Deferred 3: repo-wide package rename or one-shot directory reorganization
  - Status: `deferred`
  - Why deferred:
    - large moves would add churn before the next hotspot wave stabilizes
    - gradual boundary cleanup is safer than a big-bang rename

- [ ] Deferred 4: whole-repo strict typing rollout
  - Status: `deferred`
  - Why deferred:
    - a small lint gate is the higher-leverage first step
    - typing should follow boundary cleanup, not precede it

- [ ] Deferred 5: changes to `docs/_review`, `docs/_build`, or release-path workflow semantics
  - Status: `deferred`
  - Why deferred:
    - these are the most workflow-sensitive surfaces in the repo
    - stability is currently more valuable than surface redesign

## 8. Success Criteria

This checklist is successful when:

1. `build.py check` remains the clear local and CI quality gate.
2. The next hotspot refactors reduce change risk without changing user-facing command semantics.
3. Diff and release outputs become easier to trust and easier to regression-test.
4. CI covers more of the workflow surfaces the repo actually depends on.
5. Future logic placement follows clearer build/quality/queue/release boundaries.
