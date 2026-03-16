# Optimization Project

Updated: 2026-03-17

## 1. Role

This file is the repo-level execution roadmap.

Use it to track:

- current baseline
- recently completed optimization work
- open repo-level gaps
- active workstreams
- deferred work
- next execution order

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

As of 2026-03-17, the repo has working baselines for:

- [`build.py`](/Users/pika/Documents/GitHub/auto-manual/build.py) as the primary cross-platform entrypoint
- target-scoped runtime outputs under [`docs/_build/<model>/<region>/`](/Users/pika/Documents/GitHub/auto-manual/docs/_build)
- review bundles under [`docs/_review/<model>/<region>/`](/Users/pika/Documents/GitHub/auto-manual/docs/_review)
- `check`
- page contracts
- diff-report file/page/field reporting
- `release-manifest`
- `preview`
- `fast`
- CI baseline for `unit`, `doctor`, and `check`

## 4. Recently Completed

Use this section for short milestone-style updates.

### 2026-03-15 to 2026-03-16

- stabilized review-first workflow around `_review`
- added `check` hardening, including stale identity detection and contract validation
- added `release-manifest`
- added `preview` and `fast`
- added CI baseline workflow
- clarified deferred direction for table-driven multi-target content

## 5. Open Gaps

Keep this section short and current.

1. High-level CLI behavior and low-level script defaults can still drift.
2. Several core files are large enough to slow safe refactoring.
3. Diff-report extraction still contains heuristic parts.
4. CI does not yet validate every important workflow surface.
5. Multi-target conditional content is still deferred.

## 6. Active Workstreams

Use the template below for each workstream:

```text
### Workstream X: Name
Status: active | next | deferred | done
Why now:
- one or two concrete reasons
Scope:
- what is included
- what is explicitly excluded
Exit criteria:
- what must be true before this workstream can be considered done
```

### Workstream A: Entrypoint And Tooling Parity

Status: active

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

Status: next

Why now:

- several core files are already large enough to make safe changes expensive

Scope:

- split responsibilities inside:
  - [`build.py`](/Users/pika/Documents/GitHub/auto-manual/build.py)
  - [`tools/build_docs.py`](/Users/pika/Documents/GitHub/auto-manual/tools/build_docs.py)
  - [`tools/gen_index_bundle.py`](/Users/pika/Documents/GitHub/auto-manual/tools/gen_index_bundle.py)
  - [`tools/diff_report.py`](/Users/pika/Documents/GitHub/auto-manual/tools/diff_report.py)
- improve ownership boundaries for routing, bundle assembly, reporting, and export flow

Exit criteria:

- large orchestration files are broken into smaller units with lower regression risk

### Workstream C: Quality Gate Hardening

Status: next

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

Status: next

Why now:

- reviewers and release owners now depend on diff-report and release-manifest outputs

Scope:

- reduce heuristic ambiguity in field-level diff extraction
- keep release-manifest aligned with publish behavior
- preserve target-scoped report defaults

Exit criteria:

- review and release outputs are trustworthy enough for routine audit and comparison work

### Workstream E: CI Expansion

Status: next

Why now:

- current CI proves baseline health, but not full workflow coverage

Scope:

- add smoke coverage where practical for:
  - diff-report
  - release-manifest
  - preview
  - publish-adjacent workflows where platform dependencies allow it

Exit criteria:

- CI covers the workflow surfaces the repo actually depends on day to day

## 7. Deferred Work

Use this section for valid future work that should not yet be active.

### Deferred D1: Multi-Target Content Pilot

Reason deferred:

- current review, check, and traceability foundations should stay stable before adding a new content strategy layer

Preferred direction:

- table-driven filtering in phase1 data
- normalized applicability fields such as `regions`, `models`, `langs`, and `feature_flags`
- page-level and block-level filtering before RST emission

Pilot recommendation:

- start with `03_product_overview`
- first support `enabled + regions + langs`
- add `models` and `feature_flags` later

Promotion rule:

- move this item into `Active Workstreams` only after the current baseline stops shifting materially

## 8. Recommended Order

Re-evaluate this order whenever a workstream closes.

1. Entrypoint and tooling parity
2. Core file decomposition
3. Quality gate hardening
4. Diff and traceability hardening
5. CI expansion
6. Multi-target content pilot

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
