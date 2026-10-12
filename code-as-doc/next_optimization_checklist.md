# Next Optimization Checklist

本轮说明书盘活的 34 项任务在[执行台账](dev/manual_revitalization_execution.md)维护唯一状态，
以 REV-ID 关联方案、依赖、验收和 PR；本清单保留既有工程工作，不复制该批次勾选项。

Updated: 2026-10-12

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
  - [`../tools/queue_query.py`](../tools/build_queue/query.py)
  - [`../tools/word_bundle_docx_styles.py`](../tools/word/bundle_docx_styles.py)
  - [`../tools/csv_pages/renderers_symbols.py`](../tools/csv_pages/renderers_symbols.py)
  - [`../tools/check_docs_generated.py`](../tools/check/docs_generated.py)
- the long-term content assembly pilot (Milestone D) was rolled back to
  template-driven rendering (#295/#296); the live data-driven primitives are now
  `csv_pages` + `page_registry` + `content_blocks` + `Manual_Copy_Source`
  short-copy tokens, and prose-assembly re-launch is tracked as Workstream N in
  [`optimization_project.md`](optimization_project.md)

## Milestone pages

This file holds the rules every milestone shares (§1, §2, §7, §8) and this index.
Each milestone's items live on its own page: open only the one your task needs.
Update an item on its page; add a new milestone as a new page plus a row here.

| Milestone page | Read it when |
| --- | --- |
| [`milestone-a-d.md`](next_optimization_checklist/milestone-a-d.md) | you trace a Milestone A–D item: the 2-week and 1-month maintainability work, the short-term contract baseline, or the content-assembly pilot preparation |
| [`milestone-e-stage3-path.md`](next_optimization_checklist/milestone-e-stage3-path.md) | you work on locking Stage 2 and the safe prose cut on the Stage-3 path |
| [`milestone-f-backport-sync.md`](next_optimization_checklist/milestone-f-backport-sync.md) | you work on cloud-doc backport reverse-sync or QC writeback enablement |
| [`milestone-g-closed-loop.md`](next_optimization_checklist/milestone-g-closed-loop.md) | you work on the business closed-loop engineering items |
| [`milestone-h-corpus-dashboards.md`](next_optimization_checklist/milestone-h-corpus-dashboards.md) | you work on corpus-driven template optimization, the three-flow dashboards, or the recorded 查客服答案 candidate |
| [`milestone-i-probes-handover.md`](next_optimization_checklist/milestone-i-probes-handover.md) | you work on unknown-unknown probes or handover assurance |
| [`milestone-j-asset-loop.md`](next_optimization_checklist/milestone-j-asset-loop.md) | you work on the asset loop: one source of truth for images and `.ai` sources |
| [`milestone-k-enterprise-ops.md`](next_optimization_checklist/milestone-k-enterprise-ops.md) | you pick or work on a Milestone K tier item (Tier 1 current execution, Tier 2 pain-triggered, Tier 3 dedicated capacity) |
| [`milestone-l-product-line-scaling.md`](next_optimization_checklist/milestone-l-product-line-scaling.md) | you trace product-line scaling execution (Workstream W) |
| [`milestone-m-skeleton-library.md`](next_optimization_checklist/milestone-m-skeleton-library.md) | you work on the skeleton library: Milestone M scope, the cross-cutting rules every PR follows, the post-S6 backlog or the exit criteria |
| [`milestone-m-slices.md`](next_optimization_checklist/milestone-m-slices.md) | you need the record of a Milestone M vertical slice (S1–S6): scope, gates, evidence and rollback |

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

- [x] Done: protect hand-curated print-only review pages across reseed (2026-08-14)
  - Status: `done` — resolved via the second "done when" option: `manual_us.yaml` declares `00_toc.rst` / `99_back_cover.rst` as `rst_include` entries with the new `ordinal_neutral: true` annotation (`tools/config_pages.py` parse, `tools/gen_index_bundle_plan.py` skip), so reseeds regenerate them deterministically while every later duplicate page keeps its pinned positional `pNN_` name (`tests/test_gen_index_bundle_plan.py`)
  - Incident: the 2026-08-13/14 Start Review reseeds of `JE-1000F/US` regenerated the review index from the manifest and silently dropped the hand-added `00_toc.rst` / `99_back_cover.rst` includes (files kept, references lost); Publish then failed the same-source IDML gate three times (runs 31767694706, 31775580957, 31779053321) — the interim manual index restore (mirror PR #54) was itself wiped by the next reseed, which is what forced the manifest-level fix
  - Not built (still open as a cheap future guard): a check-stage flag for orphan review page files that exist under `page/` but are absent from the review index

- [ ] Pending: recalibrate the web-presentation suite against the reseeded JE-1000F/US review content
  - Status: `pending`
  - Incident: the 2026-08-13 reseed regenerated the review pages from live data, but `tests/test_web_presentation.py` still pins expectations written against main's older committed review copy. The seeded review PR auto-approves its checks (trusted worker), so the drift stayed invisible until an ordinary backport PR against `review/JE-1000F-US` ran the full gate (Hello-Docs PR #54): ~4 failures + ~19 errors across `test_app_add_device*`, `test_auto_resume_table*`, `test_lcd_mode*`, `test_charging_car*`, `test_operation_panels*` in en/fr/es
  - Operator-confirmed content truth (2026-08-14, 夏冰): JE-1000F's button is named **"POWER Button"** — the current test expectation `Main Power Button` is the outdated side, the review content is correct
  - Done when:
    - the suite's hardcoded expectations are updated to the review-content truth **in the same change that lands the review content on main** (the review PR merge), so neither side goes red alone
    - a decision is recorded for the exemption mechanism: either ordinary PRs against review branches skip content-coupled suites, or reseeds must include a suite recalibration step
  - Note: unrelated PRs against the review branch may merge past this known-red unit check until recalibration lands (verified pre-existing on the review branch base without the PR's changes)

## 8. Success Criteria

This checklist is successful when:

1. `build.py check` remains the clear local and CI quality gate.
2. The next hotspot refactors reduce change risk without changing user-facing command semantics.
3. Diff and release outputs become easier to trust and easier to regression-test.
4. CI covers more of the workflow surfaces the repo actually depends on.
5. Future logic placement follows clearer build/quality/queue/release boundaries.
