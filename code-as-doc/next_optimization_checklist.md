# Next Optimization Checklist

Updated: 2026-06-18

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

Milestone status: `in_progress`
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

- [ ] PR G0: Split `cloud_doc_backport_cli.py` (args / commands / orchestration)
  - Status: `pending`
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

- [ ] PR G2: Ledger → TM route (`tm_pair_suggestion`) (工程②)
  - Status: `pending`
  - Note: live TM writes stay operator-approved (candidate → approve → apply,
    the same pattern as source intake); apply targets the converged base from G4
  - Target files:
    - [`../tools/revision_ledger.py`](../tools/revision_ledger.py)
    - [`../tools/translation_memory.py`](../tools/translation_memory.py)
  - Done when:
    - accepted revision deltas that rewrite translated prose emit TM pair candidates (source sentence, target sentence, provenance, confidence)
    - candidates are reviewable and only reach live `Translation_Memory` after operator approval
    - reviewer-corrected sentence pairs stop being lost after each review round

- [ ] PR G3: TM hit-rate ledger (工程③)
  - Status: `pending`
  - Target files:
    - [`../.agents/skills/lark-tm-translation-preprocess/scripts/preprocess_lark_docx_with_tm.py`](../.agents/skills/lark-tm-translation-preprocess/scripts/preprocess_lark_docx_with_tm.py)
    - `reports/` (new hit-rate ledger location via `path_utils`)
  - Done when:
    - each preprocess run appends its per-run stats (matched units / total units, by language pair and document) to a cumulative hit-rate ledger under `reports/`
    - a baseline hit-rate number exists so G2/G4 improvements are measurable

- [ ] PR G4: TM base convergence (工程④)
  - Status: `pending`
  - Note: **operator decision required** — pick the canonical write base between
    the A (wiki) and B (env-token) mirrors; the other becomes read-only archive
  - Done when:
    - exactly one TM base accepts writes; skills and scripts resolve it from one config point
    - the retired mirror is marked read-only/archived and no skill defaults to it

- [ ] PR G5: PDF annotation renderer MVP (工程⑤)
  - Status: `pending`
  - Note: annotate on the PDF, correct at the source — the renderer is a
    read-only presentation of QC findings; fixes flow through the existing
    docx/cloud-doc backport path
  - Target files:
    - [`../tools/content_lint.py`](../tools/content_lint.py) (findings input)
    - new renderer module + skill entry
  - Done when:
    - `content_lint` findings render as highlight + comment annotations on the built PDF (pymupdf text search; page-level fallback when text location fails)
    - each annotation names the source location (table/slot or template) so the reviewer can route the fix
    - output is a sidecar `*_annotated.pdf`; the shipped PDF is untouched

- [ ] PR G6: Backport reminder sentinel (工程⑥)
  - Status: `pending`
  - Target files:
    - `.github/workflows/` (daily sentinel, same pattern as `feishu-schema-parity.yml`)
  - Done when:
    - a review cloud doc with edits newer than its last backport for N days opens/updates a reminder issue (report-only, no auto-backport)
    - the issue closes itself once the backport lands

- [ ] PR G7: Intake completeness gate default-on (工程⑦)
  - Status: `pending`
  - Target files:
    - [`../tools/source_intake_runtime.py`](../tools/source_intake_runtime.py)
    - [`../tools/source_intake_completeness.py`](../tools/source_intake_completeness.py)
  - Done when:
    - `spec-extract` without `--reference` fails loudly unless `--skip-completeness` is passed explicitly (no silent skip)
    - ambiguous snapshot keys require review instead of warning

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
