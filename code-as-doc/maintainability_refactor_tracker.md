# Maintainability Refactor Tracker

Updated: 2026-04-05

This file tracks the active maintainability refactor campaign for this repository.
Use it as the in-progress execution record.

Do not use this file as:

- the long-term architecture document
- the repo-level roadmap
- the completed optimization history log

Use these documents for those topics:

- [`architecture/System Evolution Strategy.md`](architecture/System%20Evolution%20Strategy.md)
- [`../optimization_project.md`](../optimization_project.md)
- [`code_optimization_log.md`](code_optimization_log.md)

## 1. Update Rules

When one refactor item starts:

- change its status from `pending` to `in_progress`
- keep the scope narrow to one checklist item per PR

When one refactor item is finished:

- change its status from `in_progress` to `done`
- add the completion date
- add one short note describing the actual outcome

When a whole milestone is finished:

- append a short historical entry to [`code_optimization_log.md`](code_optimization_log.md)
- update [`../optimization_project.md`](../optimization_project.md) if the workstream status changed materially

Status vocabulary:

- `pending`
- `in_progress`
- `done`

## 2. Campaign Setup

- [x] Create the dedicated refactor branch and execution tracker
  - Status: `done`
  - Completed: `2026-04-05`
  - Note: created branch `codex/maintainability-refactor-tracker` and added this tracker file

## 3. Milestone 1: Foundation And Entrypoint

Milestone status: `done`

- [ ] PR 1: Shared config and path foundation
  - Status: `done`
  - Target files:
    - [`../build.py`](../build.py)
    - [`../tools/build_docs.py`](../tools/build_docs.py)
    - [`../tools/gen_index_bundle.py`](../tools/gen_index_bundle.py)
    - [`../tools/diff_report.py`](../tools/diff_report.py)
    - [`../tools/sync_data.py`](../tools/sync_data.py)
  - Guard tests:
    - [`../tests/test_build_script.py`](../tests/test_build_script.py)
    - [`../tests/test_sync_data.py`](../tests/test_sync_data.py)
    - [`../tests/test_diff_report.py`](../tests/test_diff_report.py)
  - Done when:
    - one shared config-loading path exists
    - root/path bootstrap logic is centralized
    - behavior is unchanged
  - Completed: `2026-04-05`
  - Note: extracted shared config-loading and script-bootstrap helpers and switched the targeted build/report/sync modules to the shared foundation

- [x] PR 2: Make `build.py` a thin dispatcher
  - Status: `done`
  - Target files:
    - [`../build.py`](../build.py)
  - Guard tests:
    - [`../tests/test_build_script.py`](../tests/test_build_script.py)
    - [`../tests/test_release_manifest.py`](../tests/test_release_manifest.py)
    - [`../tests/test_target_resolution.py`](../tests/test_target_resolution.py)
  - Done when:
    - `build.py` mainly handles args and action routing
    - publish/doctor/diff orchestration is moved out of the entry file
  - Completed: `2026-04-05`
  - Note: extracted validation, review-sync, diff-report, publish, cleanup, argument parsing, doctor runner, and action dispatch into shared helper modules; `build.py` dropped from 779 to 661 lines while keeping wrapper compatibility for tests

## 4. Milestone 2: Build Pipeline Decomposition

Milestone status: `in_progress`

- [ ] PR 3: Split `tools/build_docs.py` into target, bundle, and export layers
  - Status: `in_progress`
  - Target files:
    - [`../tools/build_docs.py`](../tools/build_docs.py)
    - [`../tools/word_bundle.py`](../tools/word_bundle.py)
    - [`../tools/word_bundle_html.py`](../tools/word_bundle_html.py)
    - [`../tools/word_bundle_docx.py`](../tools/word_bundle_docx.py)
  - Guard tests:
    - [`../tests/test_target_resolution.py`](../tests/test_target_resolution.py)
    - [`../tests/test_build_docs_review_compat.py`](../tests/test_build_docs_review_compat.py)
    - [`../tests/test_word_bundle.py`](../tests/test_word_bundle.py)
    - [`../tests/test_word_bundle_docx.py`](../tests/test_word_bundle_docx.py)
    - [`../tests/test_manual_html_assets.py`](../tests/test_manual_html_assets.py)
  - Done when:
    - target resolution, bundle preparation, and export backends are separated
    - `tools/build_docs.py` becomes a thin orchestration shell
  - Completed:
  - Note: extracted CLI parsing, entry orchestration, target resolution, validation, csv/root-index generation, HTML metadata helpers, bundle preparation, output resolution, I/O/export flow, path/theme/sphinx helpers, shared types/constants, and additional misc support modules; `tools/build_docs.py` dropped from 1409 to 678 lines while preserving current test-facing wrappers

- [ ] PR 4: Split bundle materialization and check logic
  - Status: `in_progress`
  - Target files:
    - [`../tools/gen_index_bundle.py`](../tools/gen_index_bundle.py)
    - [`../tools/check_docs.py`](../tools/check_docs.py)
    - [`../tools/page_contracts.py`](../tools/page_contracts.py)
  - Guard tests:
    - [`../tests/test_check_docs.py`](../tests/test_check_docs.py)
    - [`../tests/test_page_contracts.py`](../tests/test_page_contracts.py)
    - [`../tests/test_pilot_configs.py`](../tests/test_pilot_configs.py)
  - Done when:
    - bundle planning/materialization and validation are separated cleanly
    - page-contract behavior is preserved
  - Completed:
  - Note: extracted CLI parsing, top-level entry execution, page planning/index helpers, contract-asset preflight/materialization scaffolding, bundle manifest assembly, RST asset rewrite helpers, and single-page materialization/render helpers from `tools/gen_index_bundle.py` into dedicated support modules; `tools/gen_index_bundle.py` dropped from 1008 to 726 lines while keeping bundle behavior unchanged

- [ ] PR 5: Reduce config-family duplication
  - Status: `pending`
  - Target files:
    - [`../config.us.yaml`](../config.us.yaml)
    - [`../config.us-en.yaml`](../config.us-en.yaml)
    - [`../config.us-es.yaml`](../config.us-es.yaml)
    - [`../config.us-fr.yaml`](../config.us-fr.yaml)
  - Guard tests:
    - [`../tests/test_target_resolution.py`](../tests/test_target_resolution.py)
    - [`../tests/test_pilot_configs.py`](../tests/test_pilot_configs.py)
    - [`../tests/test_build_review_preview.py`](../tests/test_build_review_preview.py)
  - Done when:
    - family-level behavior stays stable
    - language-specific config duplication is reduced without changing command semantics
  - Completed:
  - Note:

## 5. Milestone 3: Reporting, Queue Flow, And Domain Split

Milestone status: `pending`

- [ ] PR 6: Split diff-report and release-manifest services
  - Status: `pending`
  - Target files:
    - [`../tools/diff_report.py`](../tools/diff_report.py)
    - [`../tools/release_manifest.py`](../tools/release_manifest.py)
  - Guard tests:
    - [`../tests/test_diff_report.py`](../tests/test_diff_report.py)
    - [`../tests/test_release_manifest.py`](../tests/test_release_manifest.py)
    - [`../tests/test_build_script.py`](../tests/test_build_script.py)
  - Done when:
    - report extraction, diff logic, and output rendering are separated
    - release-manifest path semantics remain unchanged
  - Completed:
  - Note:

- [ ] PR 7: Split queue flow and external integrations
  - Status: `pending`
  - Target files:
    - [`../tools/process_build_queue.py`](../tools/process_build_queue.py)
    - [`../tools/process_review_start_queue.py`](../tools/process_review_start_queue.py)
    - [`../tools/listen_build_queue.py`](../tools/listen_build_queue.py)
    - [`../tools/sync_data.py`](../tools/sync_data.py)
  - Guard tests:
    - [`../tests/test_process_build_queue.py`](../tests/test_process_build_queue.py)
    - [`../tests/test_process_review_start_queue.py`](../tests/test_process_review_start_queue.py)
    - [`../tests/test_listen_build_queue.py`](../tests/test_listen_build_queue.py)
    - [`../tests/test_sync_data.py`](../tests/test_sync_data.py)
  - Done when:
    - queue parsing, routing, build execution, and writeback are separated
    - external system adapters stop importing private helpers across modules
  - Completed:
  - Note:

- [ ] PR 8: Split `spec_master` domain logic
  - Status: `pending`
  - Target files:
    - [`../tools/utils/spec_master.py`](../tools/utils/spec_master.py)
  - Guard tests:
    - [`../tests/test_spec_master_lookup.py`](../tests/test_spec_master_lookup.py)
    - [`../tests/test_spec_master_audit.py`](../tests/test_spec_master_audit.py)
    - [`../tests/test_spec_master_repairs.py`](../tests/test_spec_master_repairs.py)
    - [`../tests/test_phase1_builder.py`](../tests/test_phase1_builder.py)
    - [`../tests/test_phase1_renderers.py`](../tests/test_phase1_renderers.py)
  - Done when:
    - lookup, normalize, audit, repair, and legacy bindings are separated
    - downstream build/report behavior is unchanged
  - Completed:
  - Note:

## 6. Completion Rule

This campaign is complete only when:

- every checklist item in this file is marked `[x]`
- the milestone statuses are all `done`
- the completed milestones are summarized in [`code_optimization_log.md`](code_optimization_log.md)
