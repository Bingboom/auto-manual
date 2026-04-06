# Next Optimization Checklist

Updated: 2026-04-07

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

This checklist assumes the 2026-04-07 baseline below:

- repo evaluation focus: maintainability and stability
- local repo test baseline: `.\.venv\Scripts\python.exe -m unittest` -> `360 tests OK`
- local quality-gate baseline:
  - `.\.venv\Scripts\python.exe build.py check --config config.us-en.yaml --model JE-1000F --region US`
  - `.\.venv\Scripts\python.exe build.py check --config config.ja.yaml --model JE-1000F --region JP`
- highest-leverage hotspots identified in:
  - [`../tools/validate_spec_master_runtime.py`](../tools/validate_spec_master_runtime.py)
  - [`../tools/check_docs_generated.py`](../tools/check_docs_generated.py)
  - [`../tools/process_docs/build_review_preview_targets.py`](../tools/process_docs/build_review_preview_targets.py)
  - [`../tools/build_docs_export.py`](../tools/build_docs_export.py)
  - [`.github/workflows/manual-validation.yml`](../.github/workflows/manual-validation.yml)
  - [`.github/workflows/feishu-build-queue.yml`](../.github/workflows/feishu-build-queue.yml)
  - [`.github/workflows/feishu-draft-build-queue.yml`](../.github/workflows/feishu-draft-build-queue.yml)
  - [`.github/workflows/feishu-start-review.yml`](../.github/workflows/feishu-start-review.yml)

## 3. Milestone A: 2 Weeks

Milestone status: `pending`

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

- [ ] PR 3: Split generated-page checks by responsibility
  - Status: `pending`
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

- [ ] PR 4: Add a minimal static quality gate
  - Status: `pending`
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

- [ ] PR 5: Extract reusable test helpers for orchestration-heavy suites
  - Status: `pending`
  - Target files:
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

## 4. Milestone B: 1 Month

Milestone status: `pending`

- [ ] PR 6: Harden diff-report heuristics with fixed fixtures
  - Status: `pending`
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

- [ ] PR 7: Expand CI coverage for critical non-unit workflow surfaces
  - Status: `pending`
  - Target files:
    - [`.github/workflows/manual-validation.yml`](../.github/workflows/manual-validation.yml)
    - [`.github/workflows/review-preview.yml`](../.github/workflows/review-preview.yml)
  - Guard tests:
    - CI workflow runs
  - Done when:
    - CI covers at least one smoke path for `diff-report`
    - CI covers at least one smoke path for `release-manifest`
    - CI covers review-preview packaging at a stable smoke level

- [ ] PR 8: Deduplicate shared GitHub Actions setup logic
  - Status: `pending`
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

- [ ] PR 9: Strengthen package boundaries around build, quality, queue, and release concerns
  - Status: `pending`
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

- [ ] PR 10: Revisit medium-sized orchestration wrappers after the quality gate hardening wave
  - Status: `pending`
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

## 5. Deferred: Do Not Touch Yet

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
