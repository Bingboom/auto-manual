# Next Optimization Checklist

Updated: 2026-05-07

This file tracks the next optimization wave after the completed maintainability refactor campaign.
Use it as the active execution checklist for the upcoming maintainability and stability work.

Do not use this file as:

- the long-term architecture document
- the repo-level roadmap
- the completed optimization history log
- the maintainer command reference

Use these documents for those topics:

- [`architecture/System Evolution Strategy.md`](architecture/System%20Evolution%20Strategy.md)
- [`../optimization_project.md`](../optimization_project.md)
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
- update [`../optimization_project.md`](../optimization_project.md) if the active workstream status changed materially

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
  - `python3 scripts/local_build.py check --config config.us-en.yaml --model JE-1000F --region US`
  - `python3 scripts/local_build.py check --config config.ja.yaml --model JE-1000F --region JP`
- short-term baseline PRs already absorbed:
  - phase2 snapshot manifest completeness validation
  - CLI action registry
  - config contract validation
  - queue `RUNNING` status writeback
- highest-leverage current hotspots identified in:
  - [`../tests/test_process_build_queue.py`](../tests/test_process_build_queue.py)
  - [`../tools/queue_query.py`](../tools/queue_query.py)
  - [`../tools/word_bundle_docx_styles.py`](../tools/word_bundle_docx_styles.py)
  - [`../tools/phase1/renderers_symbols.py`](../tools/phase1/renderers_symbols.py)
  - [`../tools/check_docs_generated.py`](../tools/check_docs_generated.py)

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

Milestone status: `in_progress`
Milestone target: `2026-05`
Milestone note: stabilize the post-PR baseline around external table contracts,
queue state writeback semantics, and the first queue-test hotspot split before
moving on to larger transition-layer work.

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

- [ ] PR 15: Centralize queue state transitions
  - Status: `pending`
  - Target files:
    - [`../tools/queue_writeback.py`](../tools/queue_writeback.py)
    - [`../tools/queue_group_processing.py`](../tools/queue_group_processing.py)
  - Done when:
    - result formatting, start/success/failure writeback, trigger clearing, and `data_sync` rules are testable as transition behavior
    - tests cover running, success, failure, and writeback-failed

- [ ] PR 16: Add external integration fixture smoke tests
  - Status: `pending`
  - Target files:
    - [`../tests/`](../tests)
    - [`../integrations/openclaw/`](../integrations/openclaw)
  - Done when:
    - fixture tests cover missing fields, permission failure, duplicate dispatch, publish confirmation, and DingTalk fallback without real network access

- [ ] PR 17: Add schema drift checks
  - Status: `pending`
  - Target files:
    - [`../tools/data_snapshot.py`](../tools/data_snapshot.py)
    - [`../tools/queue_contract.py`](../tools/queue_contract.py)
    - [`../tests/fixtures/`](../tests/fixtures)
  - Done when:
    - phase2 snapshot manifest, CSV headers, and queue writable fields can be validated from fixed fixtures or dry-run payloads

## 6. Deferred: Do Not Touch Yet

- [ ] Deferred 1: large multi-target conditional-content redesign
  - Status: `deferred`
  - Why deferred:
    - the repo roadmap already treats this as deferred
    - current maintainability wins are higher-value and lower-risk

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

## 6. Success Criteria

This checklist is successful when:

1. `build.py check` remains the clear local and CI quality gate.
2. The next hotspot refactors reduce change risk without changing user-facing command semantics.
3. Diff and release outputs become easier to trust and easier to regression-test.
4. CI covers more of the workflow surfaces the repo actually depends on.
5. Future logic placement follows clearer build/quality/queue/release boundaries.
