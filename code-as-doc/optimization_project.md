# Optimization Project

## 说明书产线盘活：下一批工作（2026-09-17）

[盘活与演进方案 v3.1](manual_production_revitalization_plan.md)登记本轮增量规划。
已有 OPS-00–07、公共 IR 与 Milestone M 的验收事实和操作者后置决定继续有效；
下面的任务不把已有回滚、健康、部署回执、反馈渠道重新立项，也不恢复 #1186 已撤回的 sideload 产线。

| 工作包 | 优先级 | 下一步及依赖 |
|---|---|---|
| WP1 发布现状、入口整合与对账基线 | 首批 | 完成 HT-Manuals → HT-Doc 整合：REV-01/02 对账与旧链接核查，REV-08 目标站点检查，REV-03 获批迁移及停止旧站独立更新；只做调查不算完成 |
| WP2 发布登记与恢复闭环 | 基线后 | WP1 确认差异后，复用已有生命周期/回执，只补登记幂等、失败重试及对账缺口；在线写入独立确认 |
| WP3 运营与译文首轮维护 | 条件满足后 | 数据访问及审核责任明确后可与 WP1 并行；复用 D1–D4 决策，验证统计口径和实际 TM 复用 |

本表只维护优先级；**逐项状态唯一维护在[执行台账](dev/manual_revitalization_execution.md)**。
方案 34 项已逐项对应 REV-01–34，前置依赖、阶段门、证据和续接点均在台账中。
下一候选 REV-01；每次“继续”先核对主线与在审 PR，再按依赖续接。交付、验收、失败处理和责任分工由方案第十章定义。
0–90 天为规划窗口，3–6 / 6–12 个月触发条件在[平台路线](architecture/platform_evolution_roadmap.md)维护。
第八节的既有工程排序保留其历史上下文；本批先核实增量缺口，未来实施切片仍遵守相应 workstream 门槛。
方案文档提交不是实施完成，不登记工作包完成记录。

既有主线记录（2026-09-13 历史时点）：完成 [#1103 全部运营 checklist](dev/manual_operations_acceptance_checklist.md)，不是只做网页发布。六本批准纠错已由 Hello-Docs #73 发布，版本/回滚/撤回、试点部署回执、健康、两条元数据读回和真实反馈闭环已交付。23个正式页面及608/709资源已实证通过；用户明确批准“后置剩余复验，收口合入 #1103”，其余101资源线上复验记录为user-deferred而非通过。总PR进入最终全绿合入门禁。见[实际状态与证据](dev/manual_operations_closeout_20260913.md)。不以前置线上正文抽取为门槛；人工内容/视觉验收和响应SLA由用户后置。后续逐本结构化治理与翻译验收继续归Milestone M，IR-D01–D06保持长期目标。

Public IR workstream checkpoint: [whole-document Web closure and JBP-2000B JP
acceptance](dev/ir_document_closeout.md). Cuts 1–5 now give new whole-document
Web packages a renderer-neutral `manual-ir/v2` flow/rich-text projection and
embed sixteen registered ComponentSpec types in document order. Operation,
hybrid LCD Mode, Warranty Lead/Section/Years, Callout, Spec, FCC, Inbox,
Overview, LCD Icons, Troubleshooting, both Symbols tables, App, and governed
Reference Figures replay from the same semantic instances while historical
`manual-ir/v1` and cut-1 replay remain supported. Cut 5B is complete:
JE-1000F/EU EN/FR/ES/DE/IT Overview, Operation and Charging now use 55/55
locale-matched, hash-registered full panels extracted from the operator-supplied
source PDF, and a target contract rejects fallback or missing required slots.
Cut 6 splits Web presentation into a shared base, skeleton profiles, and small
target overlays, while whole-document IR freezes only the resolved target
contract. Cut 7 is complete: new figure targets must declare a complete
finished-art policy; a non-increasing baseline contains only explicitly known
US/KR debt; shared Web/IR Python and CSS reject model literals; and new
source-normalized v2 replay consumes frozen component registry, theme, Overview
instance, and ComponentSpecs without the old DOM projector. Four representative
packages projected 401 embedded instances through all four registered adapters
(1604 bindings). This proves the shared semantic/adapter entry contract, not
pixel or pagination identity between responsive Web and fixed-page outputs.
See the [neutral-flow
plan](dev/manual_ir_v2_neutral_flow_plan.md), [embedded-component
record](dev/manual_ir_embedded_components_plan.md), [cut-3
record](dev/manual_ir_operation_warranty_lcd_plan.md), and [cut-4
record](dev/manual_ir_lcd_troubleshooting_symbols_plan.md), and [cut-5
record](dev/manual_ir_app_reference_plan.md). The 5B source/crop/hash evidence is
recorded in the [EU finished-panel closeout](dev/je1000f_eu_finished_panels_discovery_2026-09.md).


Updated: 2026-09-05

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

For the multi-year platform maturity view (phases, gates, KPIs), use:

- [`code-as-doc/architecture/platform_evolution_roadmap.md`](architecture/platform_evolution_roadmap.md)

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

Completed milestones before 2026-07-31 now live in
[`code_optimization_log.md`](code_optimization_log.md#archived-roadmap-sections-2026-10-02),
together with the finished workstreams listed under §6.

## 5. Open Gaps

Keep this section short and current.

1. GitHub-hosted queue/publish flows now share setup and smoke coverage, but still rely on workflow-level validation more than full remote end-to-end execution.
2. Page assembly is split: reference/tabular/safety pages are data-driven, but prose pages (product overview, operation guide, app setup, and most long-form pages) are still template-forked per language family. The generalized assembly pilot was rolled back (#295/#296). The goal is to eliminate the per-language template forks and structure reusable content per the content-truth allocation rule — not to structuralize all prose; long-form/compliance prose is deliberately repository-owned. See [`architecture/Long_Form_Content_Block_Design.md`](architecture/Long_Form_Content_Block_Design.md).
3. The Feishu IM ingress adapter is now repo-local and has explicit ECS deployment assets plus encrypted callback support, but shared state for multi-instance use and stable named-ingress rollout are still open. The current server-side follow-up is provisioning one Cloudflare-managed domain plus one named tunnel hostname so Feishu no longer depends on a temporary `trycloudflare.com` URL.
4. Rule-based content QC is now machine-readable and locally reportable (`content_lint --json`, local reports, lightweight `source_ref`), but Feishu `QC_Report` writeback and exact live-row `record_id` resolution are still deferred until the source/report contracts stabilize.
5. Release snapshots are not yet frozen or archived per release: `release-manifest` records build metadata but does not bind each release to an immutable, timestamped snapshot, so the Stage 3 invariant "every release is traceable to a frozen snapshot" is not yet met.
6. Dev→prod **Bitable** structure is now exportable/appliable and parity-checkable (`tools/bitable_schema.py` `export`/`apply`/`parity`), but reference-data sync, a unified one-command promotion, and prod-side CI triggering are still manual. Full loop inventory + remaining gaps (A/C/D/E) are recorded in [`dev/closed_loop_gaps.md`](dev/closed_loop_gaps.md).
7. Milestone J's asset loop has deterministic AI intake, a verified first live archive in the three new `04_资产*` tables, and a post-review bundle finalizer, but remains open on four concrete legs: syncing the Base registry mirror through `sync-data`, migrating current template paths to `asset:`, explicit IDML consumption from the finalized bundle root, and release-manifest asset lineage. Track the exact status in [`next_optimization_checklist.md`](next_optimization_checklist.md) §6h and [`dev/asset_ai_master_intake_plan.md`](dev/asset_ai_master_intake_plan.md).
8. Enterprise ops gaps (2026-07-17 review): CI never installs from `requirements.lock` (loose ranges only), TeXLive is reinstalled unpinned on every queue run, there is no point-in-time backup/restore of the Feishu phase2 source tables, queue-processing failures notify no one (only the sentinel crons open Issues), there is no `CODEOWNERS` / secret scanning / dependabot, and the InDesign finalize leg runs on one Mac with no version lock. Tracked as Workstream T.
9. Scale walls for the 10-dev / 50-line target (2026-07-17 review): frozen-copy review branches make every shared-template fix O(N) manual `sync-review` merges with clobber risk; the build queue is one serialized runner; `docs/_build` binary assets are raw in git (pack already ~148 MiB); the Feishu transport is duplicated across 5+ independent `lark-cli` runners with no retry/rate-limit in the sync path; adding a language requires code and golden-test edits. Tracked as Workstreams U and V.
10. Web finished-figure debt is explicit and ratcheted. `JE-1000F/EU` is clean at 55/55 localized approved composites (including IT 11/11). The versioned baseline records nine US Charging `editable-fallback` rows (three per EN/FR/ES) and nine KR `missing` Overview/Operation/Charging rows. New or worsening debt fails; a repaired row must become a locale-matched `finished-panel` / `approved-composite` and delete its stale baseline entry in the same change. Textless art plus HTML/SVG text or leader lines never closes a row. LCD Mode's editable HTML table is intentionally outside this debt.

## 6. Active Workstreams

Finished workstreams moved to
[`code_optimization_log.md`](code_optimization_log.md#archived-roadmap-sections-2026-10-02) on 2026-10-02:
A (Entrypoint And Tooling Parity), B (Core File Decomposition), C (Quality Gate Hardening), D (Diff And Traceability Hardening), E (CI Expansion), F (Feishu IM Ingress Hardening), G (Contract And Queue Baseline Hardening), H (Content Assembly Pilot), J (Release Snapshot Freezing And Traceability), R (Business Closed-Loop — Revision Reflow, TM Corpus Lifecycle, PDF Annotation), W (Product-Line Scaling Execution (模版+数据 → InDesign)), X (Four-Renderer Style Component Contract v2).


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

### Workstream S: Corpus-Driven Template Optimization + Three-Flow Dashboards

Status: next

PR-level breakdown: [`next_optimization_checklist.md`](next_optimization_checklist.md) Milestone H (H1 lint → H2 recurrence miner → H3 two-face dashboards). The 查客服答案 capability is a recorded candidate under that milestone, not scheduled.

The three workstreams below are the Phase 0/1/2 execution plan from the
2026-07-17 production-readiness review
([`reviews/production_readiness_review_2026-07-17.md`](reviews/production_readiness_review_2026-07-17.md)).
They target the operating plane (reproducibility, alerting, backup, transport,
propagation), not content structure, so they run alongside the Stage 3 tiers
above rather than replacing them.

Sequencing is **capacity-driven, not calendar-driven**: entry/exit conditions,
organizational triggers, and the operator-load objectives live in
[`architecture/platform_evolution_roadmap.md`](architecture/platform_evolution_roadmap.md)
§3–§4; each workstream below carries only the short form (a `Capacity/trigger`
and a `Removes from the operator` line). Work advances as abandonable
single-PR slices between business deliveries and never blocks a delivery.

### Workstream T: Enterprise Ops Hardening (Phase 0)

Status: next

PR-level breakdown: [`next_optimization_checklist.md`](next_optimization_checklist.md) Milestone K (K1–K7).

Capacity/trigger (roadmap Phase 0): no organizational trigger — entry is
"today"; one operator + agents suffices. Per the Milestone K tier triage
(2026-07-17), the current real execution set is **K4 → K5 → K7 → K1**;
K2/K3 wait on business-pain triggers and K6 on the second-reviewer window.

Removes from the operator: being the platform's only recovery mechanism (no
more watching queue runs, hand-reconstructing lost table data, or being the
one machine that can finish a delivery).

Why now:

- three of the review's critical items grow strictly more expensive with delay: git binary history is irreversible without a rewrite, the Feishu source-of-truth has no restore path, and queue failures are silent unless an operator watches the run
- every item is days-not-weeks, independent, and requires no architecture change

Scope (one PR per item where possible):

- T1: make `requirements.lock` the install source for CI and ReadTheDocs (today no workflow references it); fix the stale "Python >= 3.9" comment in [`requirements.txt`](../requirements.txt) and the stale "no lock file" note in [`ONBOARDING.md`](../ONBOARDING.md)
- T2: pin and cache the TeXLive install in [`feishu-build-queue.yml`](../.github/workflows/feishu-build-queue.yml) (currently unpinned apt install on every run)
- T3: move `docs/_build` binary assets (PNG/PDF/DOCX) to Git LFS; the history-rewrite decision (pack ~148 MiB, two 18.9 MB PDFs) is operator-gated and may be deferred, but new binaries stop entering raw history now
- T4: scheduled, versioned export of the phase2 source tables (extend [`tools/data_snapshot.py`](../tools/data_snapshot.py) / `bitable_schema.py` export) plus a written restore runbook — today only structure parity is checked, content has no backup
- T5: route `feishu-build-queue` / draft / start-review failures into the same open/close-Issue sentinel pattern used by `cred-health-check` and `feishu-schema-parity`, so a failed queue run alerts without a watcher
- T6: governance floor: add `CODEOWNERS`, verify server-side branch protection, add secret scanning and dependabot
- T7: InDesign finalize resilience: record the pinned InDesign version and document a second-host setup for [`tools/idml/indesign_finalize.jsx`](../tools/idml/indesign_finalize.jsx) (top delivery SPOF)

Exit criteria:

- CI installs from the lock; a warm TeX cache skips the apt install
- a destructive Bitable edit can be restored from a dated export by following the runbook
- a failed queue run opens a tracked Issue automatically
- new binary artifacts land in LFS, and the IDML→PDF leg is reproducible on a documented second host

### Workstream U: Platform Consolidation (Phase 1)

Status: next (agent-executable scope starts after Workstream T's first wave; completion is gated on an organizational trigger)

PR-level breakdown: [`next_optimization_checklist.md`](next_optimization_checklist.md) Milestone K (K8–K14).

Capacity/trigger (roadmap Phase 1): per the Milestone K tier triage,
K8/K11/K13 (and provisionally K14) fire on business-pain triggers — K8's is
a live sync failure/race/rate-limit hit; K9/K10/K12 need dedicated capacity
or a protected window and must not start as between-delivery filler.
**Completion** requires one of: a second maintainer joins (even part-time),
dedicated platform time is formally allocated, or IT takes credential/tenancy
ownership — surfacing that ask, with the bus-factor register as evidence, is
itself a deliverable. Until it fires, the fallback second maintainer is the
ONBOARDING §7 memory-less-agent cold-start drill (keeps recovery honest; does
not substitute for a human on judgment surfaces).

Removes from the operator: knowledge concentration and the
"operator reviews everything" bottleneck (CODEOWNERS narrows operator review
to compliance/content surfaces).

Why now:

- the review found the Feishu transport duplicated across 5+ independent `lark-cli` runners, the queue claim non-atomic, observability print-based (423 `print()` calls, zero `logging` imports), and language onboarding requiring code edits — each blocks either a second developer or concurrent operation

Scope:

- U1: one Feishu transport client — fold the duplicate `run_lark_cli_json` implementations (`queue_lark_ops`, `queue_bound_lark_ops`, `listen_build_queue*`, `spec_master_rebuild`, `bitable_schema`, sync/backport call sites) into a single module owning retry/backoff/rate-limit, and add file locking around `data/phase2/*.csv` snapshot writes
- Execution note: Workstream W / Stage 4a has completed K8 slices 1–4, centralizing the queue, build-listener, spec-master, and schema command/response boundary plus bounded retry/backoff, pagination, and phase2 snapshot-write locking policy.
- Execution note: Stage 4a items 10–15 now provide review-only reference-layout scaffolding, explicit failure-isolated finalize job manifests, a one-dispatch JSX batch loop per InDesign application group, approved-contract App page ownership, target-neutral page-role assembly coverage warnings, and native page/overset signals in both release JSON and CSV. Item 12's design-Mac two-document evidence was accepted on 2026-07-31 and PR #814 is merged.
- U2: package the flat `tools/` namespace along the proven `tools/idml/` pattern — `queue/`, `backport/`, `word/`, `intake/`, `sync/`, `checks/` — as behavior-preserving mechanical moves with guardrail entries updated per move
- U3: extract target/config resolution (`load_config`, `resolve_build_targets`, `build_root_for_target`) out of the [`tools/build_docs.py`](../tools/build_docs.py) facade into `tools/utils/` so queue/check/release modules stop importing the build orchestrator
- U4: structured logging baseline: introduce `logging` with levels in queue orchestration and build entry paths first, replacing prints incrementally
- U5: atomic queue claim (compare-and-swap or claim token + TTL on the queue row) plus a shared concurrency contract across the three queue workflows; then a parallel build matrix for independent targets
- Execution note: Workstream W / Stage 4b is complete: items 1–3 provide a verified two-hour row lease, shared Draft/Publish Document_link record groups, a separate Start Review identity domain, a global Vercel production mutex, and selective GitHub artifact surfaces with explicit 1/7/14-day retention while preserving the independent 90-day phase2 backup. The independent-target build matrix remains the later U5 expansion.
- U6: data-driven language onboarding: remove the hardcoded language enumerations in `signal_words.py` / `sync_data_models.py` / `localized_copy.py` / `manual_copy_source.py` and the paired golden-test edits, so a new language is data + config only
- U7: release labeling (tags or release IDs) on top of the existing manifests, plus a written rollback/redeploy runbook
- Execution note: Workstream W / Stage 5 item 13 completed U7's machine scope.
  Versioned manifests and publish metadata now share a deterministic target,
  language-set, and version tag. A dry-run-first command creates an annotated
  Git tag whose message binds the release commit plus manifest/snapshot hashes,
  and refuses any rebind. The operator guide covers Vercel routing rollback,
  exact prior-artifact re-delivery, and E1 historical rebuild. Per the approved
  gate, the first timed rollback drill is still performed and recorded by the
  operator rather than fabricated by automation.

Exit criteria:

- exactly one code path talks to `lark-cli`, with tested retry/rate-limit semantics
- no prefix-family flat modules remain in `tools/` root for the queue/word/backport/intake/sync/check subsystems
- two concurrent queue dispatches cannot double-claim a row
- a new language lands with zero Python edits

### Workstream V: Review-Branch Propagation Re-Architecture (Phase 2)

Status: design approved 2026-07-31; bounded implementation slices registered

Design: [`architecture/Review_Branch_Propagation_Design.md`](architecture/Review_Branch_Propagation_Design.md).

PR-level breakdown: [`next_optimization_checklist.md`](next_optimization_checklist.md) Milestone K (K15 = design gate only; implementation PRs are registered after design approval).

Capacity/trigger (roadmap Phase 2): entry = Workstream T exit criteria passed
AND the K15 design doc approved. A business trigger legitimately accelerates
it: when the dashboard shows template-fix propagation or queue wall-time
measurably eating delivery capacity, this jumps the queue (the
discovery-engine rule, roadmap §5). The pilot needs sustained review
attention — either a second maintainer shares it, or business load is
consciously shaped around the pilot window (an explicit, visible operator
decision). Migration is one model family at a time; unmigrated branches keep
working.

Removes from the operator: repetitive maintenance — the O(N) manual
`sync-review` propagation of every shared-template fix, and babysitting
serial build waves.

Why now:

- the frozen-copy review-branch model is the first thing that breaks at scale: a shared-template fix on `main` reaches zero open review branches ([`tools/check_review_branch_sync.py`](../tools/check_review_branch_sync.py) is advisory by design), and the only safe propagation is a human-judgment `sync-review` per branch with clobber risk — infeasible at 50 lines
- this is the forward-propagation complement of Workstream Q (which governs the reverse direction, review → source)

Scope:

- write the design doc first: review branches hold only the per-target derivative (`docs/_review/**` + overrides) and resolve shared templates from a pinned-but-advanceable template version; propagation becomes an automated per-branch bump PR that shows the rendered diff, turning `check_review_branch_sync` from advisory into generative
- protect authored reviewer edits explicitly: the bump PR must classify authored-vs-placeholder lines using the same discipline `sync-review` merge_params already has, and abstain into a flagged conflict rather than clobber
- distribute the review load: CODEOWNERS-scoped second reviewers for code PRs (depends on T6), reserving operator judgment for compliance/content decisions

Exit criteria:

- a shared-template fix reaches every open review branch as a reviewable automated PR, with zero manual merge steps and zero silent drift
- propagation lag (fix merged → all branches bumped) is measured and visible
- reviewer-authored edits survive propagation or surface as explicit conflicts, never silent overwrites

### Workstream Y: Code Quality And Iterability

Status: active — phase 1 done (#1318–#1322 plus follow-ups, 2026-09-29/30); phase 2 (test seams, logging and subprocess contracts, validator rewrites) next

PR-level breakdown and the authoritative checklist:
[`dev/code_quality_iterability_plan.md`](dev/code_quality_iterability_plan.md)
(CQ-1 … CQ-7).

Why now:

- the 2026-09-28 full-repo assessment found that adding a model/region stays
  cheap, but cross-cutting code changes are getting more expensive: a flat
  `tools/` namespace (~330 top-level modules), tests coupled to facade module
  paths (614 `patch` sites), and 31 functions with cyclomatic complexity ≥50;
- the existing guardrails cap file length but not complexity, lint runs only
  three ruff rules, and a few real defects (unclosed file handles, `B023`
  loop-variable closures) already sit below that bar.

Scope:

- CQ-4 lint baseline and real-defect fixes first, then complexity ratchet
  (CQ-3), test seams (CQ-2), logging/exception/subprocess contracts (CQ-5),
  faster and environment-robust tests (CQ-6), document lifecycle (CQ-7), and
  finally package migration of the prefix families (CQ-1);
- every item follows the existing ratchet pattern (baseline, block new debt,
  then pay down) and is behavior-preserving unless the item says otherwise.

Exit criteria: the per-item acceptance lines in the plan are all met and each
completed CQ item has a record in [`code_optimization_log.md`](code_optimization_log.md).

## 8. Recommended Order

Re-evaluate this order whenever a workstream closes.

1. Keep the current `check` + smoke-CI baseline green.
2. Run the Milestone K Tier 1 set immediately and in parallel with everything else: K4 (source-table backup), K5 (queue-failure alerting), K7 (second InDesign host), K1 (lock CI deps) — the 2026-07-17 operator triage. Everything else in K waits for its named trigger or a dedicated window; the task list should read as "4 in flight", not "15 pending".
3. Execute Workstream X in its strict serial PR order. Do not parallelize style-contract, ComponentSpec, PagePlan, or target-geometry migrations; keep the approved Web asset manifest and reference layout frozen while each adapter proves parity.
4. Lock Stage 2 traceability and safe reverse-sync: finish the QC tail (Workstream I), enforce the backport layer-routing rules (Workstream Q), and freeze release snapshots (Workstream J).
5. Take the safe first cut into prose: extend short-copy coverage (Workstream L) and make `page_registry` the single composition authority (Workstream M).
6. Let Workstream U items fire on their tier rules: K8 (transport) when its sync-pain trigger fires; K9/K10/K12 only with dedicated capacity or a protected window — not as filler.
7. Re-launch long-form prose assembly (Workstream N) only after the design in [`architecture/Long_Form_Content_Block_Design.md`](architecture/Long_Form_Content_Block_Design.md) is approved and the Feishu source model is stable.
8. Scale online-first to more models (Workstream O) and consolidate the control plane (Workstream P) as those dependencies clear — but approve the Workstream V design doc before any many-target scale-out, because O multiplies exactly the review-branch propagation cost V removes.


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
10. The operating plane no longer depends on a watcher or a single machine: a failed queue run alerts on its own, the source tables can be restored from a dated export, the build environment installs from a lock, and the IDML→PDF leg runs on more than one documented host.
11. A shared-template fix propagates to every open review branch as reviewable automation, not manual per-branch merges.

## 10. Next Review Trigger

Review this file again when:

- a workstream reaches `done`
- a new command becomes part of the supported baseline
- a major workflow regression or architecture gap is discovered
- deferred multi-target content work becomes active

## 11. One-Sentence Summary

This file should stay a living repo roadmap: small, current, execution-focused, and easy to revise after each optimization wave.


### Manual operations goal clarification — 2026-09-13

The operator reaffirmed completion of all items in the
[manual operations checklist](dev/manual_operations_acceptance_checklist.md)
as the current goal. Git-only Web publication does not require extracting
manual body data into online tables; it does not defer version/rollback,
publication receipts, health reporting or the feedback loop. Repeated manual
content/visual review is operator-deferred. The operator also explicitly
accepted deferral of remaining resource re-verification and authorized #1103
closure after its final all-green merge gates. GitHub Issues is
the confirmed feedback channel and 夏冰 is responsible for acceptance.
