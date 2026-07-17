# Platform Evolution Roadmap

Registered: 2026-07-17
Derived from: [`../reviews/production_readiness_review_2026-07-17.md`](../reviews/production_readiness_review_2026-07-17.md)

## 0. Role and Boundary

This document is the **multi-year platform evolution view**: maturity assessment, phased roadmap, phase gates, and KPIs for evolving auto-manual from a single-operator production system into an enterprise platform maintained by multiple engineers.

Document boundary:

- [`System Evolution Strategy.md`](System%20Evolution%20Strategy.md) owns the **content-architecture direction** (Stage 1→3, the deliberate hybrid, content-truth allocation). This roadmap does not restate or override it; Phase 2/4 below consume its Stage-3 tiers as-is.
- [`../optimization_project.md`](../optimization_project.md) owns the **current execution roadmap** (workstreams). Phases 0–2 below are already executable there as Workstreams T/U/V.
- [`../next_optimization_checklist.md`](../next_optimization_checklist.md) Milestone K owns the **PR-level breakdown** of Phases 0–2.

Update this file when a phase gate passes, a phase's scope changes materially, or the maturity assessment is re-scored (re-score at most quarterly).

## 1. Operating Premises

Three facts drive the plan:

1. The **code plane is already enterprise-grade** (no import cycles, behavior-level tests, enforced size ratchets, release provenance); the binding constraints are operational and organizational.
2. The platform's product is **compliance-grade manual production at near-zero marginal cost**, and its system of record is the **Feishu data plane**, not the git repo.
3. The scarcest resource is **one operator's judgment**. The north star is converting operator judgment into governed automation one flow at a time — never betting the delivery pipeline on a rewrite.

Principles applied throughout:

- **Evolve in place.** Every phase ships through the existing PR/queue/review machinery. No big-bang rename, no service extraction until a boundary has proven it needs one (the standing Deferred rules in [`../next_optimization_checklist.md`](../next_optimization_checklist.md) §7 remain binding).
- **Protect the irreplaceable first.** Data with no backup, history that cannot be rewritten later, knowledge in one head — these get investment before anything merely inefficient.
- **Judgment last.** Automate mechanical toil before judgment-bearing flows; when judgment is automated, it ships propose-then-approve with audit trails (the pattern the backport / TM / source-table write paths already established).
- **Every phase pays for itself** with a measurable outcome on the [`flow_dashboard`](../../tools/flow_dashboard.py) value face, not just an engineering outcome.

## 2. Platform Maturity Assessment

Scale: 1 = ad hoc · 2 = repeatable but manual · 3 = defined, partially automated · 4 = managed, measured, multi-person · 5 = optimizing, self-service.

| Dimension | Current | Target | Gap |
| --- | :---: | :---: | --- |
| Architecture | 3 | 4 | Modular monolith with clean one-way DAGs and enforced ratchets; gap = flat `tools/` namespace, 5× duplicated Feishu transport, facade-as-library. Packaging + one transport, not a rewrite. |
| Platform Engineering | 2 | 4 | Strong 13-job CI gate, but the environment is a procedure, not an artifact: lockfile unused in CI, no container, TeX unpinned per run, binaries raw in git, serial single-runner queue. |
| Operations | 2 | 4 | Excellent sentinels (cred / schema-parity / backport Issues) but the core queue fails silently, logging is print-based, rotation manual, two delivery legs on personal machines. |
| Developer Experience | 3 | 4 | `doctor`, credential-free fixture builds, golden-path drill are genuinely good; undermined by a 158-env-var surface and one unreproducible delivery leg. Target: a second engineer productive in under a week, verified by the quarterly drill. |
| Documentation | 4 | 4 | Already a strength (ONBOARDING, bus-factor register, two-plane map). Gap is drift control on the two 100 KB+ guides, not more writing. |
| Deployment | 2 | 4 | Operator-dispatched publish with excellent manifests, but no version labels, no rollback runbook, no promotion story, InDesign finalize off-CI. |
| Data Governance | 2 | 4 | Structural governance near best-in-class (daily schema parity, contract gates, exact-or-abstain writes); but the system of record has **no point-in-time content backup**, no semantic validation, asset lineage (Milestone J3) unfinished. The backup gap alone caps the score. |
| AI Workflow | 3 | 4 | Governance unusually mature (deterministic backport, propose-then-approve writes, dry-run boundaries, delta-hash idempotency). Gap: standing QC agent deferred, hit-rate/reflow baselines just started, no consolidated agent audit ledger. |
| Security | 2 | 4 | Hygiene clean (nothing committed, stdin secrets, daily live probes). Missing the floor: secret scanning, dependency alerts, CODEOWNERS, rotation automation; DingTalk browser-session tokens fragile; one OAuth holder. |
| Scalability | 2 | 4 | Four walls before 50 lines: frozen-copy review-branch propagation, single-operator gating, serial queue + per-run TeX install, git binary growth. Known fixes, none started. |
| Business Readiness | 3 | 5 | Value proven and measured (value-face dashboard, shipped-manual catalog). Gap to 5: throughput capped at one human, no SLA possible yet, stock-manual onboarding and manual-Q&A remain unscheduled candidates. |

Reading: the profile is lopsided — Documentation 4, Architecture/DX/AI 3, everything operational 2 — exactly the profile of an excellent prototype-turned-production system built by one strong person. The roadmap front-loads the 2s that are irreversible or existential, then raises the operational floor, then spends on scale.

## 3. Phased Roadmap

Dates assume the current operating model (one operator + AI agents) for Phase 0 and **+1 engineer from Phase 1 onward** — that hire is itself a Phase 1 deliverable.

### Phase 0 — Stabilization: protect the irreplaceable (now → ~6 weeks, Q3 2026)

- **Goals:** eliminate the four unrecoverable-loss scenarios: destroyed source tables, unrepairable git history, silent queue failure, single-Mac InDesign leg. No behavior or architecture changes.
- **Expected outcome:** any Bitable content edit restorable from a dated export via a drilled runbook; new binaries stop entering raw history; a failed queue run opens a tracked Issue on its own; IDML→PDF reproducible on a second documented host; CI installs from the lockfile on pinned TeX.
- **Required changes:** exactly Milestone K1–K7 (already scoped, operator gates marked).
- **Risk:** low — items independent and reversible except the explicitly deferred history-rewrite decision. Real risk is deprioritization: these ship no visible feature, which is why they run first.
- **Estimated time:** 4–6 weeks alongside production; K3/K4/K5 in the first two weeks.
- **Priority:** **P0.** Cost of delay is compounding (git history) or catastrophic (source tables).
- **Business value:** insurance — converts "one bad afternoon could end the platform" into "recoverable incident"; the precondition for any delivery commitment.

### Phase 1 — Maintainability & Team Enablement: from one brain to a team (Q3–Q4 2026, ~1 quarter)

- **Goals:** make the platform maintainable by engineers who didn't build it; get the second engineer in and productive. The bus-factor phase.
- **Expected outcome:** exactly one code path talks to Feishu (retry/rate-limit/locking); flat `tools/` becomes packaged subsystems; queue/build paths emit leveled correlated logs; a new language lands with zero Python edits; releases labeled with a drilled rollback path; **a second engineer has merged 10+ PRs and passed the cold-start drill without the operator present**.
- **Required changes:** Milestone K8–K14; the hire/allocation itself; CODEOWNERS-scoped review so the operator stops reviewing everything; freshness checks on the two oversized guides.
- **Risk:** medium — transport/packaging moves touch everything but follow the proven pattern (idml decomposition, guardrails, one subsystem per PR). Biggest real risk: the hire doesn't happen and Phase 1 silently becomes "operator does more" — the phase gate exists to catch that.
- **Estimated time:** one quarter; K8 and the hire first.
- **Priority:** **P1.** Everything after assumes more than one pair of hands.
- **Business value:** removes the largest hidden liability (key-person risk); cuts onboarding from "months, maybe never for the InDesign leg" to "days" — what makes headcount investment rational.

### Phase 2 — Platformization: make scale mechanically possible (Q4 2026 – Q1 2027, 1–2 quarters)

- **Goals:** remove the two structural walls between ~6 live models and 50 lines: template propagation and build throughput. Land the content Stage-3 safe tiers (Workstreams L, M) in the same window.
- **Expected outcome:** a shared-template fix reaches every open review branch as automated, reviewable bump-PRs (zero manual merges, measured propagation lag); independent targets build in parallel on a containerized cached toolchain; every shipped page declared in `page_registry` with explicit applicability; Workstream V implemented behind its approved design doc.
- **Required changes:** K15 design doc → V implementation (per-target-derivative branches + pinned template reference + authored-edit protection); parallel build matrix atop Phase 1's atomic claims; a build container image; Workstreams L and M; release-snapshot freezing (Workstream J / E1) so scale never outruns traceability.
- **Risk:** **high — the phase with real design risk.** V touches the most workflow-sensitive surface (`docs/_review` semantics, reviewer experience); authored edits must never be silently clobbered. Mitigations encoded: design gate first (K15), migration plan required, Deferred 5 stays binding until the gate passes, pilot on one model family before fleet cutover.
- **Estimated time:** 1–2 quarters; design ≤ 3 weeks, one-family pilot ~1 month, migration incremental.
- **Priority:** **P1, hard-gated:** V's design must be approved before any many-model scale-out (Workstream O), because O multiplies exactly the propagation cost V removes.
- **Business value:** where marginal cost per product line actually drops — a new line becomes data entry plus an automatically-maintained derivative. Converts the 50-line ambition from headcount math into queue math.

### Phase 3 — Enterprise Operations: run it like a service (Q1–Q2 2027, ~1 quarter, overlaps Phase 2 tail)

- **Goals:** turn "a system the operator runs" into "a service the business consumes": commitments, observability, access control, formalized AI governance.
- **Expected outcome:** published turnaround expectations per document type (possible only once the queue is parallel, failures alert, rollback exists); flow dashboard published on schedule to stakeholders; dev/prod tenant separation and credential rotation as owned procedures; every agent-initiated write queryable in one audit ledger; the standing QC agent (Workstream I tail) activated against now-stable contracts.
- **Required changes:** SLO definition + a small intake surface for the doc-ops team (existing IM control plane hardened per Workstream P: named ingress, shared state); scheduled dashboard publication; rotation runbooks + replacing browser-session-token dependencies; consolidating the per-flow ledgers (revision, TM hit-rate, QC, releases) into one audit view; QC-agent activation behind its existing dry-run boundary.
- **Risk:** medium-low technically, medium organizationally — SLAs create expectations; set them from measured Phase-2 queue data, not aspiration. Formalizing AI governance must codify the propose-then-approve paths that already work, not redesign them.
- **Estimated time:** ~1 quarter of engineer time, much of it runbook/process.
- **Priority:** **P2** — after Phases 1/2, because commitments without parallel builds and alerting are promises the platform cannot keep.
- **Business value:** predictability lets other departments plan around the platform — the difference between a tool people like and infrastructure the business depends on. Also makes compliance/security audits passable on demand.

### Phase 4 — Scale-out & Leverage: 50 lines and new products on the same rails (H2 2027, ongoing)

- **Goals:** onboard the fleet (new lines + stock-manual backfill) and harvest the accumulated corpus (TM, ledgers, catalog) as new products.
- **Expected outcome:** 20 → 50 lines at a measured marginal cost per line (target: < 2 operator-days from spec-sheet intake to first published draft, via the existing intake skills); multi-model online-first builds with zero hand-committed snapshots (Workstream O); long-form prose assembly (Workstream N) only where its design gate and ROI clear; the manual-Q&A capability (查客服答案 — answers with cited sources from built manuals, with its two recorded metrics) launched as the first knowledge product on the platform.
- **Required changes:** mostly execution on rails built earlier: batch intake campaigns, per-line capability-gate data, O's online-first proofs; N only after its design doc; Q&A scoped as its own workstream (already a recorded candidate — not smuggled into polish PRs). Service extraction (e.g., a real queue service replacing Actions) only if measured throughput demands it — the first phase where that conversation is legitimate.
- **Risk:** medium, mostly data quality — stock manuals arrive messy; intake gates get stress-tested; onboarding pace follows measured per-line cost, not a deadline. Guard the success-risk: 50 live lines put every Phase 0–3 mechanism under 10× load.
- **Estimated time:** ongoing through H2 2027; Q&A ~1 quarter to first internal users.
- **Priority:** **P2/P3 — strictly gated on Phase 2's propagation gate and Phase 3's alerting floor.**
- **Business value:** the payoff phase — fleet coverage multiplies the proven per-manual savings ~10×, and Q&A turns a cost-center corpus into a reusable knowledge asset. The platform's story changes from "documentation automation" to "the company's product-knowledge system of record."

## 4. Phase Gates

| Gate | Condition to pass |
| --- | --- |
| 0 → 1 | Content-restore drill executed and timed; queue-failure Issue observed firing on a real failure; LFS live for new binaries |
| 1 → 2 | Second engineer merges independently (cold-start drill passed); single transport live; atomic claim proven by fixture test |
| 2 → 3 | V pilot: one model family runs propagation as auto-PRs for 3 consecutive template changes with zero clobbered reviewer edits |
| 3 → 4 | One quarter of green SLO data; audit ledger answers "what did agents write last month" in one query |

## 5. KPIs

All on the existing [`flow_dashboard`](../../tools/flow_dashboard.py), extended:

- bus factor ≥ 2 on every flow (register already exists in [`../../ONBOARDING.md`](../../ONBOARDING.md) §3)
- propagation lag: template fix merged → all open review branches bumped
- queue wall-time per target and per rebuild wave
- marginal onboarding cost per product line
- reflow rate and TM hit rate (already measured)
- content-restore drill time
- % of agent writes carrying a full audit trail

## 6. What We Will Explicitly NOT Do

No microservices split, no CMS/Bitable replacement, no export-stack (Word/PDF/IDML) rewrite, no repo-wide big-bang reorg, no structuralizing compliance prose beyond the content-truth allocation rule. Every one of these is a standing Deferred or architecture decision already recorded in this repo; this roadmap keeps them binding. The platform wins by compounding what works, not by re-founding it.
