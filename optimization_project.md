# Optimization Project

Updated: 2026-04-12

## 1. Role

This file is the repo-level execution roadmap.

Use it to track:

- current baseline
- recently completed optimization work
- open repo-level gaps
- active workstreams
- deferred work
- next execution order

The active execution checklist for the current optimization wave lives in:

- [`code-as-doc/next_optimization_checklist.md`](/Users/pika/Documents/GitHub/auto-manual/code-as-doc/next_optimization_checklist.md)

The completed execution tracker for the earlier maintainability refactor campaign remains here:

- [`code-as-doc/maintainability_refactor_tracker.md`](/Users/pika/Documents/GitHub/auto-manual/code-as-doc/maintainability_refactor_tracker.md)

Do not use this file as the long-term architecture document.

For long-term direction and stable architecture boundaries, use:

- [`code-as-doc/architecture/System Evolution Strategy.md`](/Users/pika/Documents/GitHub/auto-manual/code-as-doc/architecture/System%20Evolution%20Strategy.md)

## 2. Maintenance Rules

Update this file when one of these happens:

1. a workstream is completed
2. a major new gap is discovered
3. the priority order changes
4. a deferred item becomes active
5. a new command or workflow becomes part of the supported baseline

Keep this file maintainable:

- keep `Current Baseline` factual
- keep `Recently Completed` short and dated
- keep `Open Gaps` limited to current repo problems, not abstract future ideas
- keep `Active Workstreams` to the few items that actually deserve attention next
- move stable long-term thinking out of this file and into the strategy document

Suggested workstream statuses:

- `active`
- `next`
- `deferred`
- `done`

## 3. Current Baseline

As of 2026-04-11, the repo has working baselines for:

- [`build.py`](/Users/pika/Documents/GitHub/auto-manual/build.py) as the primary cross-platform entrypoint
- target-scoped runtime outputs under [`docs/_build/<model>/<region>/`](/Users/pika/Documents/GitHub/auto-manual/docs/_build)
- review bundles under [`docs/_review/<model>/<region>/`](/Users/pika/Documents/GitHub/auto-manual/docs/_review)
- `sync-data`
- `check`
- page contracts
- diff-report file/page/field reporting
- `release-manifest`
- `preview`
- `fast`
- `message-control-dry-run` as a maintainer-only Phase 0 natural-language control resolver that returns structured JSON without dispatching real workflows
- explicit `--data-root` snapshot selection for build, check, diff-report, and release-manifest
- CI baseline for `lint`, `unit`, `doctor`, `check`, `diff-report` smoke, `release-manifest` smoke, and review-preview packaging smoke
- OpenClaw Phase 2 repo-local control surfaces through `queue-query`, `queue-resolve-action`, and `queue-execute`
- repo-owned OpenClaw integration packages under [`integrations/openclaw/`](integrations/openclaw)

## 4. Recently Completed

Use this section for short milestone-style updates.

### 2026-03-15 to 2026-03-16

- stabilized review-first workflow around `_review`
- added `check` hardening, including stale identity detection and contract validation
- added `release-manifest`
- added `preview` and `fast`
- added CI baseline workflow
- clarified deferred direction for table-driven multi-target content

### 2026-03-31

- added phase2 snapshot path resolution through `--data-root`
- added `build.py sync-data` for explicit Feishu/Lark snapshot refresh into `data/phase2/`
- aligned `check`, `diff-report`, and `release-manifest` with the same snapshot-resolution rules

### 2026-04-05

- normalized queue semantics around `Workflow_action` while keeping `Doc_phase` as a deprecated compatibility fallback
- added staging-first local validation wrappers and cross-platform branch freshness guardrails
- started the core file decomposition wave by splitting `build.py` and `tools/process_build_queue.py` into dedicated helper modules for paths, reports, command assembly, doctor checks, queue contract types, queue parsing, queue runtime, queue build execution, per-group queue processing, dry-run formatting, queue-session bootstrap, Lark transport, output staging, and writeback
- added [`code-as-doc/dev/orchestration_module_map.md`](/Users/pika/Documents/GitHub/auto-manual/code-as-doc/dev/orchestration_module_map.md) as the living ownership map for those extracted boundaries
- continued the queue decomposition wave by moving top-level queue-session flow into [`tools/queue_orchestration.py`](/Users/pika/Documents/GitHub/auto-manual/tools/queue_orchestration.py) and repo-root-aware release/output adapters into [`tools/queue_bound_outputs.py`](/Users/pika/Documents/GitHub/auto-manual/tools/queue_bound_outputs.py)
- continued the same queue workstream with repo-root-aware runtime adapters in [`tools/queue_bound_runtime.py`](/Users/pika/Documents/GitHub/auto-manual/tools/queue_bound_runtime.py) and Lark transport adapters in [`tools/queue_bound_lark_ops.py`](/Users/pika/Documents/GitHub/auto-manual/tools/queue_bound_lark_ops.py)
- continued the same queue workstream with [`tools/queue_bound_binding.py`](/Users/pika/Documents/GitHub/auto-manual/tools/queue_bound_binding.py) and [`tools/queue_bound_records.py`](/Users/pika/Documents/GitHub/auto-manual/tools/queue_bound_records.py) so preflight/binding and record/config/grouping logic no longer sit inline in the entry file
- completed the foundation/entrypoint maintainability milestone by adding shared config/bootstrap helpers plus `build.py` parser, doctor, publish, diff, cleanup, and dispatch modules
- started the next build-pipeline pass by extracting `tools/build_docs.py` CLI parsing and top-level entry orchestration into dedicated helper modules

### 2026-04-06

- completed the entrypoint-and-tooling parity workstream by removing hardcoded low-level `JE-1000F` diff-report defaults, centralizing shared target/config defaults, and aligning review-preview/matrix scripts with shared family config metadata
- continued Workstream A by moving [`scripts/build_us_jp_manuals.py`](/Users/pika/Documents/GitHub/auto-manual/scripts/build_us_jp_manuals.py) and [`tools/process_docs/build_review_preview.py`](/Users/pika/Documents/GitHub/auto-manual/tools/process_docs/build_review_preview.py) to config-derived target metadata instead of hardcoded per-language output rules
- finished the remaining `scripts/` bootstrap cleanup so [`scripts/build_us_jp_manuals.py`](/Users/pika/Documents/GitHub/auto-manual/scripts/build_us_jp_manuals.py) and [`scripts/local_build.py`](/Users/pika/Documents/GitHub/auto-manual/scripts/local_build.py) now share the repo-root bootstrap path used across `tools/`
- collapsed [`scripts/build_us_manuals.ps1`](/Users/pika/Documents/GitHub/auto-manual/scripts/build_us_manuals.ps1) into a thin compatibility wrapper over [`scripts/build_us_jp_manuals.py`](/Users/pika/Documents/GitHub/auto-manual/scripts/build_us_jp_manuals.py), removing its duplicate per-language matrix loop and hardcoded default model
- updated maintainer and user-facing docs so script examples and preview defaults match the current supported baseline

### 2026-04-06

- completed the core maintainability refactor campaign across build entrypoints, build pipeline helpers, reporting, queue orchestration, preview/export/sync hotspots, and `spec_master`
- split `build_review_preview.py` into target, data, render, page, postprocess, and workspace helpers
- reduced `spec_master.py` to a facade over dedicated shared, lookup, auditing, mapping, row-helper, and repairs modules
- split `word_bundle_html.py` into models, HTML-only, render, images, and rewrite helpers
- split `sync_data.py` into config, records, runtime, and CLI-output helpers while preserving the existing patch/test surface
- completed the active tracker in [`code-as-doc/maintainability_refactor_tracker.md`](/Users/pika/Documents/GitHub/auto-manual/code-as-doc/maintainability_refactor_tracker.md) and logged the closed milestone in [`code-as-doc/code_optimization_log.md`](/Users/pika/Documents/GitHub/auto-manual/code-as-doc/code_optimization_log.md)
- finished the remaining shared bootstrap rollout across low-level entry scripts and queue-adjacent tools

### 2026-04-07

- completed Milestone A in [`code-as-doc/next_optimization_checklist.md`](/Users/pika/Documents/GitHub/auto-manual/code-as-doc/next_optimization_checklist.md) by removing preview-target import side effects, splitting the Spec_Master/runtime/generated-page quality hotspots, adding a minimal Ruff gate, and introducing shared orchestration-test helpers
- kept Workstream C active, but moved its baseline forward so the local/CI quality gate now includes a deliberate low-noise static check before the heavier unit/build validation layers run

### 2026-04-08

- completed Milestone B in [`code-as-doc/next_optimization_checklist.md`](/Users/pika/Documents/GitHub/auto-manual/code-as-doc/next_optimization_checklist.md) by fixing `diff-report` regression fixtures, adding CI smoke coverage for `diff-report`, `release-manifest`, and review-preview packaging, centralizing shared GitHub-hosted Feishu worker setup, and finishing a wrapper-focused boundary pass across `build.py`, `tools/build_docs.py`, `tools/build_docs_export.py`, and `tools/process_build_queue.py`

### 2026-04-11

- started Workstream F by adding `build.py message-control-dry-run` plus `tools/message_control_*` as the Phase 0 dry-run resolver for the planned Feishu message plus OpenClaw control layer
- kept the Phase 0 scope intentionally narrow: resolve one raw message into structured JSON, required fields, guardrails, and the target GitHub workflow without dispatching or mutating Feishu state

### 2026-04-12

- added the repo-external Feishu IM webhook adapter under [`integrations/openclaw/feishu-im-webhook-adapter/`](integrations/openclaw/feishu-im-webhook-adapter), keeping Feishu IM ingress outside the Python build plane while reusing `queue-query`, `queue-resolve-action`, and `queue-execute`
- hardened the adapter with explicit publish-confirmation state, event-id dedupe, clear rejection for unsupported encrypted callbacks, and same-thread Feishu replies
- aligned the architecture, maintainer docs, and user workflow docs with the new ingress layer so the control-layer plan no longer drifts from the supported baseline

## 5. Open Gaps

Keep this section short and current.

1. A few workflow facades are still medium-sized, but the largest hotspot files are no longer blocking routine maintenance work.
2. GitHub-hosted queue/publish flows now share setup and smoke coverage, but still rely on workflow-level validation more than full remote end-to-end execution.
3. Multi-target conditional content is still deferred.
4. The Feishu IM ingress adapter is now repo-local, but deployment hardening, shared state for multi-instance use, and encrypted callback support are still open.

## 6. Active Workstreams

### Workstream A: Entrypoint And Tooling Parity

Status: done

Why now:

- entrypoint drift creates silent behavioral mismatches
- this problem leaks directly into review, diff-report, and release flow

Scope:

- remove hardcoded target defaults from low-level tools
- align path-resolution and default-output rules with [`build.py`](/Users/pika/Documents/GitHub/auto-manual/build.py)
- reduce duplicated CLI semantics between entrypoint code and `tools/*.py`

Exit criteria:

- `build.py` and low-level tools no longer disagree on target defaults or report/output roots

### Workstream B: Core File Decomposition

Status: done

Why now:

- the main hotspot files needed to be split before quality-gate and traceability hardening could proceed safely
- the earlier queue/build decomposition wave proved that behavior-preserving modularization could reduce risk without changing the command surface

Scope:

- split responsibilities inside:
  - [`build.py`](/Users/pika/Documents/GitHub/auto-manual/build.py)
  - [`tools/build_docs.py`](/Users/pika/Documents/GitHub/auto-manual/tools/build_docs.py)
  - [`tools/gen_index_bundle.py`](/Users/pika/Documents/GitHub/auto-manual/tools/gen_index_bundle.py)
  - [`tools/diff_report.py`](/Users/pika/Documents/GitHub/auto-manual/tools/diff_report.py)
- improve ownership boundaries for routing, bundle assembly, reporting, and export flow
- keep public wrappers stable while moving implementation into dedicated modules
- record each completed decomposition milestone in [`code-as-doc/code_optimization_log.md`](/Users/pika/Documents/GitHub/auto-manual/code-as-doc/code_optimization_log.md)
- keep [`code-as-doc/dev/orchestration_module_map.md`](/Users/pika/Documents/GitHub/auto-manual/code-as-doc/dev/orchestration_module_map.md) aligned with the extracted module boundaries

Exit criteria:

- large orchestration files are broken into smaller units with lower regression risk
- core entry files act primarily as orchestration layers rather than carrying most low-level implementation themselves
- module ownership stays documented after each decomposition step instead of drifting back into tribal knowledge

### Workstream C: Quality Gate Hardening

Status: done

Why now:

- `check` is now central to the repo workflow and should stay authoritative

Scope:

- preserve stale identity detection
- preserve placeholder, asset, include, and contract checks
- improve error specificity where needed
- avoid duplicated validation logic across build stages

Exit criteria:

- `check` remains the clear local and CI gate before export and publish

### Workstream D: Diff And Traceability Hardening

Status: done

### Workstream E: CI Expansion

Status: done

### Workstream F: Feishu IM Ingress Hardening

Status: active

Why now:

- the repo now owns a real Feishu IM ingress package, so deployment and callback-mode boundaries need to stay explicit
- without a small hardening pass, operator-facing behavior can drift between local testing and real webhook use

Scope:

- keep the Feishu IM adapter outside the Python execution plane
- keep reply semantics aligned with `queue-resolve-action`, `queue-execute`, and structured failure summaries
- keep `message-control-dry-run` as a maintainer-only offline parser probe so intent normalization can still be debugged without live Feishu ingress
- make callback security mode explicit
- make runtime-state expectations explicit before any multi-instance deployment

Exit criteria:

- the adapter can be deployed without ambiguity about callback mode, runtime state, and required env
- operator replies stay deterministic for query, review-start, draft build, and publish confirmation
- remaining gaps are clearly documented instead of being hidden in local-only assumptions

## 8. Recommended Order

Re-evaluate this order whenever a workstream closes.

1. Preserve the current `check` + smoke-CI baseline
2. Finish Feishu IM ingress hardening around deployment contract, callback mode, and runtime state
3. Revisit remaining medium wrappers only when a concrete hotspot reappears
4. Multi-target content pilot when the deferred work becomes active


## 9. Success Criteria

This roadmap is successful when:

1. [`build.py`](/Users/pika/Documents/GitHub/auto-manual/build.py) and low-level tools no longer disagree on target defaults and output paths.
2. Core workflow code is easier to change without touching thousand-line files.
3. `check` remains the clear pre-export quality gate.
4. Diff and release outputs are trustworthy enough for review and audit use.
5. CI covers the critical workflow surfaces that the repo depends on.
6. One shared content source can eventually emit correct regional variants without cloning page templates.

## 10. Next Review Trigger

Review this file again when:

- a workstream reaches `done`
- a new command becomes part of the supported baseline
- a major workflow regression or architecture gap is discovered
- deferred multi-target content work becomes active

## 11. One-Sentence Summary

This file should stay a living repo roadmap: small, current, execution-focused, and easy to revise after each optimization wave.
