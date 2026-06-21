# Optimization Project

Updated: 2026-06-18

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

- [`code-as-doc/next_optimization_checklist.md`](next_optimization_checklist.md)

The completed execution tracker for the earlier maintainability refactor campaign remains here:

- [`code-as-doc/maintainability_refactor_tracker.md`](maintainability_refactor_tracker.md)

Do not use this file as the long-term architecture document.

For long-term direction and stable architecture boundaries, use:

- [`code-as-doc/architecture/System Evolution Strategy.md`](architecture/System%20Evolution%20Strategy.md)

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

As of 2026-05-07, the repo has working baselines for:

- [`build.py`](../build.py) as the primary cross-platform entrypoint
- target-scoped runtime outputs under [`docs/_build/<model>/<region>/`](../docs/_build)
- review bundles under [`docs/_review/<model>/<region>/`](../docs/_review)
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
- repo-owned OpenClaw integration packages under [`integrations/openclaw/`](../integrations/openclaw)
- phase2 snapshot completeness validation for required synced tables and derived files
- registered `build.py` action dispatch for explicit non-build actions
- config contract validation for phase2 table bindings and declared build languages
- queue `RUNNING` writeback before success/failure completion
- first repo-owned external table contract and queue-state model docs under [`code-as-doc/dev/`](dev)
- data-driven rendering for reference/tabular/safety pages (`symbols`, `lcd_icons`, `troubleshooting`, `spec`, safety blocks) through [`tools/csv_pages/`](../tools/csv_pages) renderers, `page_registry.csv` composition, and `content_blocks.csv`
- structured short-copy through `Manual_Copy_Source` plus Translation Memory tags, resolved into RST via `{{ copy:<copy_key> }}` while templates keep layout
- snapshot-based content linting through [`tools/content_lint.py`](../tools/content_lint.py), with machine-readable `--json` output and local QC reports
- closed-loop QC requirements under [`code-as-doc/architecture/closed_loop_qc_agent_requirements.md`](architecture/closed_loop_qc_agent_requirements.md)
- deterministic reviewer-diff backport through [`tools/cloud_doc_backport.py`](../tools/cloud_doc_backport.py), routing accepted Feishu-doc changes into templates/source as draft PRs

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
- added [`code-as-doc/dev/orchestration_module_map.md`](dev/orchestration_module_map.md) as the living ownership map for those extracted boundaries
- continued the queue decomposition wave by moving top-level queue-session flow into [`tools/queue_orchestration.py`](../tools/queue_orchestration.py) and repo-root-aware release/output adapters into [`tools/queue_bound_outputs.py`](../tools/queue_bound_outputs.py)
- continued the same queue workstream with repo-root-aware runtime adapters in [`tools/queue_bound_runtime.py`](../tools/queue_bound_runtime.py) and Lark transport adapters in [`tools/queue_bound_lark_ops.py`](../tools/queue_bound_lark_ops.py)
- continued the same queue workstream with [`tools/queue_bound_binding.py`](../tools/queue_bound_binding.py) and [`tools/queue_bound_records.py`](../tools/queue_bound_records.py) so preflight/binding and record/config/grouping logic no longer sit inline in the entry file
- completed the foundation/entrypoint maintainability milestone by adding shared config/bootstrap helpers plus `build.py` parser, doctor, publish, diff, cleanup, and dispatch modules
- started the next build-pipeline pass by extracting `tools/build_docs.py` CLI parsing and top-level entry orchestration into dedicated helper modules

### 2026-04-06

- completed the entrypoint-and-tooling parity workstream by removing hardcoded low-level `JE-1000F` diff-report defaults, centralizing shared target/config defaults, and aligning review-preview/matrix scripts with shared family config metadata
- continued Workstream A by moving [`scripts/build_us_jp_manuals.py`](../scripts/build_us_jp_manuals.py) and [`tools/process_docs/build_review_preview.py`](../tools/process_docs/build_review_preview.py) to config-derived target metadata instead of hardcoded per-language output rules
- finished the remaining `scripts/` bootstrap cleanup so [`scripts/build_us_jp_manuals.py`](../scripts/build_us_jp_manuals.py) and [`scripts/local_build.py`](../scripts/local_build.py) now share the repo-root bootstrap path used across `tools/`
- collapsed [`scripts/build_us_manuals.ps1`](../scripts/build_us_manuals.ps1) into a thin compatibility wrapper over [`scripts/build_us_jp_manuals.py`](../scripts/build_us_jp_manuals.py), removing its duplicate per-language matrix loop and hardcoded default model
- updated maintainer and user-facing docs so script examples and preview defaults match the current supported baseline

### 2026-04-06

- completed the core maintainability refactor campaign across build entrypoints, build pipeline helpers, reporting, queue orchestration, preview/export/sync hotspots, and `spec_master`
- split `build_review_preview.py` into target, data, render, page, postprocess, and workspace helpers
- reduced `spec_master.py` to a facade over dedicated shared, lookup, auditing, mapping, row-helper, and repairs modules
- split `word_bundle_html.py` into models, HTML-only, render, images, and rewrite helpers
- split `sync_data.py` into config, records, runtime, and CLI-output helpers while preserving the existing patch/test surface
- completed the active tracker in [`code-as-doc/maintainability_refactor_tracker.md`](maintainability_refactor_tracker.md) and logged the closed milestone in [`code-as-doc/code_optimization_log.md`](code_optimization_log.md)
- finished the remaining shared bootstrap rollout across low-level entry scripts and queue-adjacent tools

### 2026-04-07

- completed Milestone A in [`code-as-doc/next_optimization_checklist.md`](next_optimization_checklist.md) by removing preview-target import side effects, splitting the Spec_Master/runtime/generated-page quality hotspots, adding a minimal Ruff gate, and introducing shared orchestration-test helpers
- kept Workstream C active, but moved its baseline forward so the local/CI quality gate now includes a deliberate low-noise static check before the heavier unit/build validation layers run

### 2026-04-08

- completed Milestone B in [`code-as-doc/next_optimization_checklist.md`](next_optimization_checklist.md) by fixing `diff-report` regression fixtures, adding CI smoke coverage for `diff-report`, `release-manifest`, and review-preview packaging, centralizing shared GitHub-hosted Feishu worker setup, and finishing a wrapper-focused boundary pass across `build.py`, `tools/build_docs.py`, `tools/build_docs_export.py`, and `tools/process_build_queue.py`

### 2026-04-11

- started Workstream F by adding `build.py message-control-dry-run` plus `tools/message_control_*` as the Phase 0 dry-run resolver for the planned Feishu message plus OpenClaw control layer
- kept the Phase 0 scope intentionally narrow: resolve one raw message into structured JSON, required fields, guardrails, and the target GitHub workflow without dispatching or mutating Feishu state

### 2026-04-12

- added the repo-external Feishu IM webhook adapter under [`integrations/openclaw/feishu-im-webhook-adapter/`](../integrations/openclaw/feishu-im-webhook-adapter), keeping Feishu IM ingress outside the Python build plane while reusing `queue-query`, `queue-resolve-action`, and `queue-execute`
- hardened the adapter with explicit publish-confirmation state, event-id dedupe, same-thread Feishu replies, encrypted callback support, and ECS-oriented deployment assets
- aligned the architecture, maintainer docs, and user workflow docs with the new ingress layer so the control-layer plan no longer drifts from the supported baseline
- added low-noise maintainability guardrails: a hotspot size check in `Manual Validation`, a refreshed anti-debt PR checklist, and synced baseline docs for the current `468`-test suite

### 2026-05-07

- absorbed the four short-term hardening PRs into the active baseline: phase2 snapshot manifest validation, build action dispatch registry, config contract validation, and queue `RUNNING` state writeback
- added [`code-as-doc/dev/external_table_contracts.md`](dev/external_table_contracts.md) as the first explicit field contract for phase2 tables, `Document_link`, and Review Init
- added [`code-as-doc/dev/queue_state_model.md`](dev/queue_state_model.md) to document `pending -> running -> success/failed` writeback semantics
- started the test-hotspot split by moving build-queue writeback field tests into [`tests/test_process_build_queue_writeback.py`](../tests/test_process_build_queue_writeback.py)

### 2026-05-08

- completed the midterm queue contract hardening pass with an explicit queue transition layer, external integration fixtures, schema drift gates, a queue-contract CI surface, and another split of the queue test hotspot
- started the long-term content direction safely by adding a `03_product_overview` assembly pilot plan, multidimensional-table-style fixtures, an assembly contract validator, a no-op assembler, and a page-level pilot switch for `US/en` and `JP/ja`

### 2026-06-07

- added snapshot-based content QC through [`tools/content_lint.py`](../tools/content_lint.py) and the rule inventory in [`code-as-doc/content_quality_rules.md`](content_quality_rules.md)
- added the closed-loop QC agent requirements baseline in [`code-as-doc/architecture/closed_loop_qc_agent_requirements.md`](architecture/closed_loop_qc_agent_requirements.md)
- activated the implementation rollout in [`code-as-doc/dev/closed_loop_qc_implementation_plan.md`](dev/closed_loop_qc_implementation_plan.md): first make rule QC machine-readable and reportable, then connect the standing agent

### 2026-06-18

- re-assessed the strategy stage against [`architecture/System Evolution Strategy.md`](architecture/System%20Evolution%20Strategy.md): the repo is mid/late Stage 2, with governance, snapshot, build/render, and release/traceability near Stage 3, but page assembly is split between data-driven reference pages and template-forked prose pages
- corrected the stale Workstream H record: the generalized `03_product_overview` content-assembly pilot was rolled back to template-driven rendering in PRs #295/#296; the `assembly_pilot` switch and the `content_assembly*` / `product_overview_renderer` modules no longer exist
- re-scoped the path to Stage 3 into tiered Workstreams J–Q below, and added Milestone E to [`next_optimization_checklist.md`](next_optimization_checklist.md)
- added the prose-assembly re-launch design in [`architecture/Long_Form_Content_Block_Design.md`](architecture/Long_Form_Content_Block_Design.md)
- clarified the Stage 3 end state as a **deliberate hybrid** in [`architecture/System Evolution Strategy.md`](architecture/System%20Evolution%20Strategy.md) (new Principle 6 plus a Stage 3 note): the CMS governs reusable content while layout, stable long-form/compliance prose, and environment differences stay repository/config-owned, allocated by an explicit content-truth rule; the target is to eliminate template forks, not to structuralize every paragraph
- recorded the backport scope decision in [`architecture/Feishu_Cloud_Doc_Backport_Design.md`](architecture/Feishu_Cloud_Doc_Backport_Design.md) §5.1 (rules R1–R8): backport is a single writer to `docs/_review/...`, template changes go through a template-sync proposal applied by a separate role (operator now, agent later); tracked as Workstream Q below

## 5. Open Gaps

Keep this section short and current.

1. GitHub-hosted queue/publish flows now share setup and smoke coverage, but still rely on workflow-level validation more than full remote end-to-end execution.
2. Page assembly is split: reference/tabular/safety pages are data-driven, but prose pages (product overview, operation guide, app setup, and most long-form pages) are still template-forked per language family. The generalized assembly pilot was rolled back (#295/#296). The goal is to eliminate the per-language template forks and structure reusable content per the content-truth allocation rule — not to structuralize all prose; long-form/compliance prose is deliberately repository-owned. See [`architecture/Long_Form_Content_Block_Design.md`](architecture/Long_Form_Content_Block_Design.md).
3. The Feishu IM ingress adapter is now repo-local and has explicit ECS deployment assets plus encrypted callback support, but shared state for multi-instance use and stable named-ingress rollout are still open. The current server-side follow-up is provisioning one Cloudflare-managed domain plus one named tunnel hostname so Feishu no longer depends on a temporary `trycloudflare.com` URL.
4. Rule-based content QC is now machine-readable and locally reportable (`content_lint --json`, local reports, lightweight `source_ref`), but Feishu `QC_Report` writeback and exact live-row `record_id` resolution are still deferred until the source/report contracts stabilize.
5. Release snapshots are not yet frozen or archived per release: `release-manifest` records build metadata but does not bind each release to an immutable, timestamped snapshot, so the Stage 3 invariant "every release is traceable to a frozen snapshot" is not yet met.

## 6. Active Workstreams

### Workstream A: Entrypoint And Tooling Parity

Status: done

Why now:

- entrypoint drift creates silent behavioral mismatches
- this problem leaks directly into review, diff-report, and release flow

Scope:

- remove hardcoded target defaults from low-level tools
- align path-resolution and default-output rules with [`build.py`](../build.py)
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
  - [`build.py`](../build.py)
  - [`tools/build_docs.py`](../tools/build_docs.py)
  - [`tools/gen_index_bundle.py`](../tools/gen_index_bundle.py)
  - [`tools/diff_report.py`](../tools/diff_report.py)
- improve ownership boundaries for routing, bundle assembly, reporting, and export flow
- keep public wrappers stable while moving implementation into dedicated modules
- record each completed decomposition milestone in [`code-as-doc/code_optimization_log.md`](code_optimization_log.md)
- keep [`code-as-doc/dev/orchestration_module_map.md`](dev/orchestration_module_map.md) aligned with the extracted module boundaries

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

Status: done

Why now:

- the repo now owns a real Feishu IM ingress package, so deployment and callback-mode boundaries need to stay explicit
- without a small hardening pass, operator-facing behavior can drift between local testing and real webhook use

Scope:

- keep the Feishu IM adapter outside the Python execution plane
- keep reply semantics aligned with `queue-resolve-action`, `queue-execute`, and structured failure summaries
- keep `message-control-dry-run` as a maintainer-only offline parser probe so intent normalization can still be debugged without live Feishu ingress
- make callback security mode explicit
- make runtime-state expectations explicit before any multi-instance deployment
- ship one repeatable ECS deployment contract instead of relying on ad hoc `nohup` steps
- keep the remaining stable-ingress rollout as an explicit ops checklist rather than tribal knowledge, including Cloudflare DNS ownership, named tunnel creation, `/etc/cloudflared/config.yml`, and the Feishu callback cutover step

Exit criteria:

- the adapter can be deployed without ambiguity about callback mode, runtime state, required env, and restart contract on a long-lived host
- operator replies stay deterministic for query, review-start, draft build, and publish confirmation
- remaining gaps are clearly documented instead of being hidden in local-only assumptions

### Workstream G: Contract And Queue Baseline Hardening

Status: done

Why now:

- phase2 data, Review Init, and `Document_link` are now core runtime contracts rather than incidental integrations
- queue `RUNNING` writeback makes state more observable, but the transition rules should become testable as one layer
- future OpenClaw, DingTalk, and multi-region work will be lower-risk if field drift is caught before live queue runs

Scope:

- keep the four merged hardening PRs as the short-term baseline
- maintain explicit external table and queue-state docs
- split the largest queue test hotspot by domain
- add queue transition tests for running, success, failure, and writeback failure
- add fixture-based smoke tests for Feishu/OpenClaw/DingTalk contract surfaces
- introduce schema drift checks for snapshot manifests, CSV headers, and writable queue fields

Exit criteria:

- queue state transitions can be tested without running a live Feishu queue
- external table field drift fails locally or in CI before breaking a production worker
- future table/field changes have one documented update path instead of spreading through README snippets, queue code, and integration adapters

### Workstream H: Content Assembly Pilot

Status: rolled back (2026-05-30) — superseded by Workstream N

Outcome:

- the fixture-backed `03_product_overview` assembly pilot (assembly contract validator, no-op assembler, page-level pilot switch, `assembly_blocks/` templates) was built, then reverted to pure template-driven rendering in PRs #295/#296; the `assembly_pilot` switch and the `content_assembly*` / `content_assembly_contract` / `product_overview_renderer` modules no longer exist
- lesson: a bespoke per-page renderer plus naive layout machinery, attempted first on the hardest page (product overview, which has intentional EU raw-LaTeX divergence), is the wrong entry point; long-form translated prose with compliance formatting cannot be naively block-split without a dedicated schema and a block-level review workflow
- the proven data-driven pattern that survived is `csv_pages` + `page_registry` + `content_blocks` + `Manual_Copy_Source` short-copy tokens; Workstream N re-launches prose assembly on that pattern instead of a bespoke renderer

See [`next_optimization_checklist.md`](next_optimization_checklist.md) Milestone D for the historical pilot record and [`architecture/Long_Form_Content_Block_Design.md`](architecture/Long_Form_Content_Block_Design.md) for the re-launch design.

### Workstream I: Closed-Loop QC Rollout

Status: active

Progress (2026-06-18): M1 (`content_lint --json`), M2 lightweight `source_ref`, M3 local reports, and M5 docs/command shipped (#338-#341); the B2 reviewer-diff channel shipped as the deterministic [`tools/cloud_doc_backport.py`](../tools/cloud_doc_backport.py) CLI (#342-#354), not a standing LLM agent. Remaining tail: M4 Feishu `QC_Report` table and the sync-time `record_id` sidecar, both deferred until the source/report contracts stabilize.

Why now:

- `content_lint` has created the first deterministic QC base, but it still prints human text only
- QC must become machine-readable and reportable before a standing agent can safely consume it
- report-only QC improves manual production immediately without blocking Word delivery

Scope:

- implement [`code-as-doc/dev/closed_loop_qc_implementation_plan.md`](dev/closed_loop_qc_implementation_plan.md)
- add stable `content_lint --json` output
- produce local QC reports before any Feishu writeback
- attach lightweight `source_ref` values only for the current lint rules while
  source tables are still evolving
- keep sync-time `record_id` sidecars, Feishu `QC_Report`, B2 diff mapping, and
  the standing QC agent deferred until the source/report contracts are stable

Exit criteria:

- rule-QC findings have a stable JSON schema
- operators can generate local QC reports from a snapshot
- every current-rule finding has a lightweight source reference, with
  `record_id` remaining nullable
- the next sidecar/report-table slice has a stable local finding/report contract
  to consume

The workstreams below are the tiered path from the current Stage 2.5 baseline to
Stage 3 ("fully structured content-driven production"). Tier 1 (J + the QC tail
of I) locks Stage 2 traceability; Tier 2 (L, M) takes the safe first cut into
prose; Tier 3 (N, O) is the Stage 3 gate and is deferred until its design and
source-model dependencies clear; Tier 4 (P) is operational hardening.

### Workstream J: Release Snapshot Freezing And Traceability

Status: next

Why now:

- Stage 3 requires every release to be traceable to an immutable snapshot
- today snapshots are sync-on-demand and are not archived per release, so a past release cannot be rebuilt byte-for-byte from a frozen input

Scope:

- archive a timestamped snapshot (source revision, exported data files, target matrix) at release time
- bind `release-manifest` to that frozen snapshot, resolving the archive path through [`tools/utils/path_utils.py`](../tools/utils/path_utils.py)
- record snapshot identity (timestamp + source revision + target matrix) in the manifest
- keep `--data-root` rebuilds reproducible from the archived snapshot

Exit criteria:

- a release-manifest references an immutable archived snapshot
- rebuilding from the archived snapshot reproduces the release output
- the manifest carries snapshot timestamp, source revision, and target matrix

### Workstream L: Short-Copy Coverage Extension

Status: next

Why now:

- the `Manual_Copy_Source` + `{{ copy:<copy_key> }}` primitive already covers page titles, table headers, labels, and symbols signals
- extending it to operation-guide and app-setup chrome is the safe first cut into prose pages without touching long bodies

Scope:

- follow the migration list in [`dev/content_block_migration_assessment.md`](dev/content_block_migration_assessment.md): add copy keys plus TM tags for operation-guide and app-setup section headings, button/UI labels, table labels, and image alt text only
- keep body paragraphs in RST
- add a per-page/language required-copy-key check before any long-prose move
- route app-market, support, manufacturer, and URL text to config ownership, not a content table

Exit criteria:

- operation-guide and app-setup chrome resolves from `Manual_Copy_Source`
- missing copy keys fail in `check`
- no body prose is moved, and config-owned environment text is not in the copy table

### Workstream M: Page Registry As Single Composition Authority

Status: next

Why now:

- today `page_registry.csv` declares only csv_pages; prose-page composition is implicit in which per-language RST files happen to exist
- that keeps applicability encoded in folder names instead of structured data, which is the driver of template forking

Scope:

- declare every shipped page — including prose pages — in `page_registry` with explicit applicability (`sku_scope`, `langs`, region/model), page order, template family, and contract reference
- keep the current RST render path as the prose-page fallback (no behavior change)
- normalize applicability across `region`, `language`, and `model` per [`architecture/Content_Data_Model.md`](architecture/Content_Data_Model.md)

Exit criteria:

- all shipped pages appear in `page_registry` with explicit applicability
- page composition and applicability are read from data, not inferred from folder layout
- RST rendering output is unchanged for prose pages

### Workstream N: Long-Form Prose Assembly Re-Launch

Status: deferred (gated on the design doc and Feishu source-model stability)

Why now:

- the core Stage 3 move is eliminating per-language template forks and governing reusable content — not structuralizing every paragraph; the content-truth allocation rule in [`architecture/Long_Form_Content_Block_Design.md`](architecture/Long_Form_Content_Block_Design.md) §3.1 decides what is structured vs deliberately repository-owned
- the first pilot was rolled back, so it must restart on the proven data-driven pattern with a long-form schema and a block-level review workflow

Scope:

- implement [`architecture/Long_Form_Content_Block_Design.md`](architecture/Long_Form_Content_Block_Design.md): a structure-preserving, paragraph/section-grained long-form content-block schema (not sentence-split), per-block-type render templates including per-region variants (EU raw-LaTeX), block-level review via the existing `cloud_doc_backport` flow, a parity-gated per-page pilot switch with RST fallback, and content_lint block rules
- structure only the content the allocation rule assigns to the CMS; keep long-form/compliance prose repository-owned by default
- collapse template forks for migrated pages via one shared definition (structured blocks plus a shared template where bodies stay RST), starting on the lowest-risk prose page (not product overview, not compliance-heavy)

Exit criteria:

- at least one prose page has its per-language forks eliminated, rendering from one shared definition plus structured data/config with parity to the current output for every target
- structured blocks cover the content the allocation rule assigns to the CMS; long-form/compliance prose stays repository-owned by default
- missing-field, missing-asset, and missing-fallback cases fail in tests
- compliance prose is block-split only as a reviewed, recorded exception

### Workstream O: Multi-Model Online-First Scale-Out

Status: deferred

Why now:

- Stage 3 means the CMS is the source of truth for all models; today only JE-2000F EU is built online-first with data sync-only

Scope:

- bring two to three more product lines to online-first / data-sync-only through the queue
- prove zero hand-committed snapshots for those lines
- confirm one shared content source emits correct regional variants without cloning page templates

Exit criteria:

- two to three more lines build online-first with no committed snapshot rows
- regional variants are produced from shared structured content plus applicability, not per-model template clones

### Workstream P: Control-Plane Consolidation

Status: deferred

Why now:

- IM-triggered production (OpenClaw, DingTalk, Feishu IM) is advanced but not yet hands-off for multi-instance use

Scope:

- add shared runtime state for multi-instance adapters
- provision a stable named ingress (Cloudflare-managed domain plus named tunnel hostname) to replace temporary `trycloudflare.com` URLs
- keep adapters outside the Python build plane

Exit criteria:

- adapters run multi-instance without state collisions
- Feishu/DingTalk ingress uses a stable named hostname
- the restart/runtime contract is documented

### Workstream Q: Backport Layer-Routing And Template-Sync

Status: next

PR-level breakdown (with Workstream I's tail): [`next_optimization_checklist.md`](next_optimization_checklist.md) Milestone F.

Why now:

- the 2026-06-18 scope decision made backport a single writer to `docs/_review/...`, with template changes emitted as a proposal applied by a separate template-sync role (operator now, agent later); the rules R1–R8 are defined in [`architecture/Feishu_Cloud_Doc_Backport_Design.md`](architecture/Feishu_Cloud_Doc_Backport_Design.md) §5.1 but are not yet enforced in code
- this is what keeps reverse-sync safe as models grow, and it is the precondition the deliberate hybrid relies on (template-owned prose must stay safely backportable)

Scope:

- emit a `template_sync_proposal.json/.md` artifact from review-backport runs for Class `T` (shared-template) deltas, which are only flagged today
- add a build-time per-target token/copy resolution map so Class `D` (data-origin) spans are detected, not guessed
- wire a family-identical check (reuse `scan_residuals`) into delta classification so `R` vs `T` and sibling scope are derived, not guessed
- add a `rebuild + rediff` idempotency gate extending `verify-review`: a rebuild from edited sources must reproduce the accepted doc and change nothing else
- write the template-sync role as a documented operator runbook first; defer the dedicated template-sync agent until the runbook and the rules prove stable
- add an approval-gated source-table-sync role: backport emits a `source_table_change_request` for Class `D` deltas (with blast radius); a human approves by deliberately running the `apply-source-table` CLI (an agent may propose/execute but never approve — backport is CLI-only as of #453, not an IM command); the executor applies via `lark-cli --as bot` with GET-verify and delta-hash idempotency; content fields only, with table schema staying operator-gated. Depends on the `record_id` sidecar (Workstream I) for exact-or-abstain resolution

Exit criteria:

- backport never writes `docs/templates/...` or Feishu source tables; a review run writes only Class `R` to `docs/_review/...`, emits a template-sync proposal for Class `T`, and emits an approval-gated change request for Class `D`
- Class `D`/`T` classification is backed by the token/copy map and the family check, not heuristics
- the `rebuild + rediff` gate passes for a real review backport before its PR is marked ready
- the template-sync runbook exists; the dedicated agent remains a documented, deferred follow-up
- Class `D` deltas reach Bitable only via the source-table-sync role after explicit human approval and exact `record_id` resolution; no guessed or unapproved writes

## 8. Recommended Order

Re-evaluate this order whenever a workstream closes.

1. Keep the current `check` + smoke-CI baseline green.
2. Lock Stage 2 traceability and safe reverse-sync: finish the QC tail (Workstream I), enforce the backport layer-routing rules (Workstream Q), and freeze release snapshots (Workstream J).
3. Take the safe first cut into prose: extend short-copy coverage (Workstream L) and make `page_registry` the single composition authority (Workstream M).
4. Re-launch long-form prose assembly (Workstream N) only after the design in [`architecture/Long_Form_Content_Block_Design.md`](architecture/Long_Form_Content_Block_Design.md) is approved and the Feishu source model is stable.
5. Scale online-first to more models (Workstream O) and consolidate the control plane (Workstream P) as those dependencies clear.


## 9. Success Criteria

This roadmap is successful when:

1. [`build.py`](../build.py) and low-level tools no longer disagree on target defaults and output paths.
2. Core workflow code is easier to change without touching thousand-line files.
3. `check` remains the clear pre-export quality gate.
4. Diff and release outputs are trustworthy enough for review and audit use.
5. CI covers the critical workflow surfaces that the repo depends on.
6. Rule-based content QC is machine-readable, reportable, and safe for a future standing agent to consume.
7. One shared content source can eventually emit correct regional variants without cloning page templates.
8. Release snapshots are frozen, and every release is traceable to an immutable snapshot.
9. The CMS / template / config boundary follows the explicit content-truth allocation rule, with long-form and compliance prose deliberately repository-owned.

## 10. Next Review Trigger

Review this file again when:

- a workstream reaches `done`
- a new command becomes part of the supported baseline
- a major workflow regression or architecture gap is discovered
- deferred multi-target content work becomes active

## 11. One-Sentence Summary

This file should stay a living repo roadmap: small, current, execution-focused, and easy to revise after each optimization wave.
