# Platform Evolution Roadmap

Registered: 2026-07-17 · Revised: 2026-07-17 (v2 — rewritten from the Platform Owner perspective under real organizational constraints; technical scope unchanged from v1)
Derived from: [`../reviews/production_readiness_review_2026-07-17.md`](../reviews/production_readiness_review_2026-07-17.md)

## 0. Role and Boundary

This document is the **long-term platform evolution view**: maturity assessment, capacity-driven phases, exit criteria, and KPIs for evolving auto-manual into a platform that survives for years under the organization it actually has — not the organization an ideal roadmap would wish for.

Document boundary:

- [`System Evolution Strategy.md`](System%20Evolution%20Strategy.md) owns the **content-architecture direction** (Stage 1→3, the deliberate hybrid, content-truth allocation). Phases here consume its Stage-3 tiers as-is.
- [`../optimization_project.md`](../optimization_project.md) owns the **current execution roadmap** (workstreams). Phases 0–2 below are executable there as Workstreams T/U/V.
- [`../next_optimization_checklist.md`](../next_optimization_checklist.md) Milestone K owns the **PR-level breakdown** of Phases 0–2.

Update this file when a phase's exit criteria are met, an organizational trigger fires (or visibly won't), or the maturity assessment is re-scored (at most quarterly).

## 1. Operating Reality (first-class design constraint)

This roadmap is written for the organization that exists:

- The platform is built and maintained by **one documentation engineer whose primary responsibility is business delivery**. There is no platform team, no dedicated engineering capacity, no dedicated operations team; data governance is owned elsewhere in the organization.
- The de-facto engineering capacity is **the operator plus AI agents** working inside the repo's governed flows (propose → validate → operator reviews → merge). Capacity growth means better agent leverage first, additional humans only when the organization provides them.
- **Business delivery cannot stop, and does not wait.** Platform work happens in the gaps between deliveries, as single-PR slices that are individually abandonable.
- Business work is **not an interruption to platform work — it is the platform's discovery engine** (§5). Nearly every defense this repo has was built in response to a real production event, not a planning exercise. The roadmap deliberately continues that pattern rather than fighting it.

Consequently this roadmap optimizes for one variable above all others: **reducing what depends on the operator**. A phase is judged not by what the platform gains but by what responsibility the operator sheds. Capabilities that add operator load are mis-scoped regardless of their engineering merit.

## 2. Platform Maturity Assessment

Scale: 1 = ad hoc · 2 = repeatable but manual · 3 = defined, partially automated · 4 = managed, measured, multi-person · 5 = optimizing, self-service.

Target levels are **capacity-gated, not calendar-gated**: a target is reached when its phase's exit criteria pass, whenever that is. Several 4s are honestly unreachable while the organization provides no second person — those are flagged as org-dependent below, and the roadmap treats surfacing that dependency to management as a deliverable, not a footnote.

| Dimension | Current | Target | Gap |
| --- | :---: | :---: | --- |
| Architecture | 3 | 4 | Modular monolith with clean one-way DAGs and enforced ratchets; gap = flat `tools/` namespace, 5× duplicated Feishu transport, facade-as-library. Packaging + one transport, not a rewrite. Agent-executable. |
| Platform Engineering | 2 | 4 | Strong 13-job CI gate, but the environment is a procedure, not an artifact: lockfile unused in CI, no container, TeX unpinned per run, binaries raw in git, serial single-runner queue. Agent-executable. |
| Operations | 2 | 4 | Excellent sentinels (cred / schema-parity / backport Issues) but the core queue fails silently, logging is print-based, rotation manual, two delivery legs on personal machines. Partly **org-dependent** (rotation/tenancy ownership sits elsewhere). |
| Developer Experience | 3 | 4 | `doctor`, credential-free fixture builds, golden-path drill are genuinely good; undermined by a 158-env-var surface and one unreproducible delivery leg. Full 4 is **org-dependent**: it requires a second human to onboard against. |
| Documentation | 4 | 4 | Already a strength (ONBOARDING, bus-factor register, two-plane map). Gap is drift control on the two 100 KB+ guides, not more writing. |
| Deployment | 2 | 4 | Operator-dispatched publish with excellent manifests, but no version labels, no rollback runbook, no promotion story, InDesign finalize off-CI. |
| Data Governance | 2 | 4 | Structural governance near best-in-class (daily schema parity, contract gates, exact-or-abstain writes); but the system of record has **no point-in-time content backup**, no semantic validation, asset lineage (Milestone J3) unfinished. Backup is operator-buildable; long-term custody is **org-dependent** (governance is owned elsewhere — hand it a working export/restore mechanism, not a request for one). |
| AI Workflow | 3 | 4 | Governance unusually mature (deterministic backport, propose-then-approve writes, dry-run boundaries, delta-hash idempotency). Gap: standing QC agent deferred, hit-rate/reflow baselines just started, no consolidated agent audit ledger. |
| Security | 2 | 4 | Hygiene clean (nothing committed, stdin secrets, daily live probes). Missing the floor: secret scanning, dependency alerts, CODEOWNERS, rotation automation; DingTalk browser-session tokens fragile; one OAuth holder. Rotation/second-holder is **org-dependent**. |
| Scalability | 2 | 4 | Four walls before 50 lines: frozen-copy review-branch propagation, single-operator gating, serial queue + per-run TeX install, git binary growth. Known fixes; the propagation fix (Workstream V) is the only one with real design risk. |
| Business Readiness | 3 | 5 | Value proven and measured (value-face dashboard, shipped-manual catalog). Gap to 5: throughput capped at one human, no SLA possible yet, stock-manual onboarding and manual-Q&A remain unscheduled candidates. |

Reading: the profile is lopsided — Documentation 4, Architecture/DX/AI 3, everything operational 2 — the signature of an excellent production system built by one strong person. The roadmap front-loads the 2s that are irreversible or existential, then sheds operator load, and treats scale as a consequence, not a goal.

## 3. The Evolution Model: Capacity-Driven, Not Calendar-Driven

Phases below are **not scheduled**. Each defines:

- **Removes from the operator** — the phase's real objective, stated first.
- **Current operating capacity** — the state the phase starts from.
- **Organizational trigger** — what allows the phase to begin (or complete). Triggers the operator cannot fire alone are explicit asks to the organization; making them visible is part of the roadmap.
- **Technical scope** — unchanged from v1; references Milestone K and the workstreams.
- **Exit criteria** — observable facts, not dates. The next phase begins when they pass.

Inside a phase, work advances as **single-PR slices absorbed between business deliveries**: agent-prepared, validation-gated, operator-approved, individually abandonable. A slice that would block a delivery is deferred by rule, not by negotiation. Rough sizing is therefore given in slices, not weeks — throughput depends on business load, and that is by design.

## 4. Phases

### Phase 0 — Stabilization

- **Removes from the operator:** being the platform's only recovery mechanism. After this phase the operator no longer has to remember to watch queue runs, personally reconstruct lost table data, or be the one machine that can finish a delivery.
- **Current operating capacity:** one operator + agents, business-first. Sufficient — every item is agent-preparable and none needs an org decision.
- **Organizational trigger:** none. Entry condition is "today." This is the only phase with no external dependency, which is exactly why it runs first.
- **Technical scope:** Milestone K1–K7 (lockfile into CI, TeX pin+cache, LFS routing, scheduled content exports + restore drill, queue-failure sentinel, CODEOWNERS/secret-scanning/dependabot, InDesign version pin + second host). ~7 slices; K3/K4/K5 first — their cost of delay compounds (git history) or is catastrophic (source tables).
- **Alongside business:** K4's restore drill piggybacks the existing I5 drill rhythm; the K5 sentinel reuses the existing Issue-bot pattern; nothing touches delivery paths.
- **Exit criteria:** a content-restore drill executed and timed; the queue-failure Issue observed firing on a real failure; LFS live for new binaries; the IDML→PDF leg verified once on a second documented host.
- **Next phase:** Phase 1 starts immediately for its agent-executable scope; its *completion* waits on an org trigger.

### Phase 1 — De-concentration (knowledge and review load)

- **Removes from the operator:** knowledge concentration and the "operator reviews everything" bottleneck. After this phase, losing the operator for a month degrades throughput — it no longer stops the platform.
- **Current operating capacity:** one operator + agents. The technical scope is exactly the kind of behavior-preserving, test-guarded work agents execute well under review.
- **Organizational trigger:** *to start* — none; *to complete* — one of: a second maintainer joins (even part-time or borrowed), OR dedicated platform time is formally allocated, OR IT/security takes ownership of credentials and tenancy. **Surfacing this ask, with the bus-factor register as evidence, is itself a Phase 1 deliverable.** Until it fires, the fallback second maintainer is the documented-agent path: the quarterly cold-start drill run by a memory-less agent from repo docs alone (the ONBOARDING §7 mechanism), which keeps recovery honest but does not substitute for a human on judgment surfaces.
- **Technical scope:** Milestone K8–K14 (single Feishu transport with retry/rate-limit/locking; gradual `tools/` packaging, one subsystem per PR; facade extraction; logging baseline; atomic queue claims; data-driven language onboarding; release labeling + rollback runbook); CODEOWNERS-scoped review so operator judgment is reserved for compliance/content surfaces; freshness checks on the two oversized guides. ~10–14 slices.
- **Alongside business:** transport consolidation (K8) is prioritized because it also removes a live production pain (sync retries/races). Packaging PRs are ideal low-stakes filler between deliveries and are abandonable mid-stream by design.
- **Exit criteria:** exactly one code path talks to Feishu; queue claims are atomic (fixture-proven); a new language lands with zero Python edits; **someone who is not the operator — human, or agent via drill for the recovery path — has independently exercised build, publish, and restore**; the operator's review queue visibly narrows to compliance/content decisions.
- **Next phase:** Phase 2, gated on the V design doc.

### Phase 2 — De-repetition (propagation and throughput)

- **Removes from the operator:** repetitive maintenance — the O(N) manual `sync-review` propagation of every shared-template fix, and babysitting serial build waves. This is the phase that stops platform toil from growing linearly with business success.
- **Current operating capacity:** operator + agents, with whatever Phase 1's trigger produced. The V pilot needs sustained review attention: either a second maintainer shares it, or business load must be consciously shaped around the pilot window — an explicit operator decision, made visible, not absorbed silently.
- **Organizational trigger:** Phase 0 exit passed AND the Workstream V design doc (K15) is approved by the operator. A business trigger legitimately accelerates it: when the dashboard shows template-fix propagation or queue wall-time measurably eating delivery capacity, this phase jumps the queue — that is the discovery engine working, not scope creep.
- **Technical scope:** K15 design → Workstream V implementation (per-target-derivative review branches + pinned template reference + authored-edit protection, piloted on one model family); parallel build matrix atop Phase 1's atomic claims; build container image; content Stage-3 safe tiers (Workstreams L, M); release-snapshot freezing (Workstream J / E1).
- **Alongside business:** V migrates one family at a time; every open review branch keeps working unmigrated. The pilot family is chosen from live production so every propagation event is a real one.
- **Exit criteria:** the V pilot family survives 3 consecutive real template changes propagated as auto-PRs with zero clobbered reviewer edits; independent targets build in parallel; propagation lag is on the dashboard; L/M shipped (all pages registry-declared, chrome copy data-driven).
- **Next phase:** Phase 3 — but only if its org trigger fires; otherwise the platform legitimately *stays* in post-Phase-2 steady state, which is already sustainable.

### Phase 3 — De-operationalization (the service handoff)

- **Removes from the operator:** daily operational overhead — dispatch babysitting, credential care, stakeholder reporting, being the human SLA. After this phase the operator owns editorial and compliance judgment; the organization owns operations.
- **Current operating capacity:** post-Phase-2 platform (parallel, alerting, recoverable) still operated by one person. That is the ceiling of what one person should carry.
- **Organizational trigger:** this phase **cannot be entered unilaterally.** It requires the organization to accept ownership: IT/ops takes credentials, rotation, and tenancy (they own data governance already — hand them the working export/restore and schema-parity mechanisms Phase 0 built), OR the business demands turnaround commitments (an SLA request is an ownership request, and should be answered with "yes — here is what the organization must staff"). If neither fires, Phase 3 work is limited to what reduces the operator's own load (scheduled dashboard publication, the consolidated agent-audit ledger) and the rest waits without penalty.
- **Technical scope:** SLO definition from measured Phase-2 queue data; hardened IM intake surface for the doc-ops team (Workstream P: named ingress, shared state); scheduled dashboard publication; rotation runbooks + eliminating browser-session-token dependencies; consolidating the per-flow ledgers (revision, TM hit-rate, QC, releases) into one audit view; standing QC agent activation behind its existing dry-run boundary (Workstream I tail).
- **Exit criteria:** one quarter of green SLO data; credential rotation executed by someone other than the operator; the dashboard reaches stakeholders without the operator sending it; "what did agents write last month" answerable in one query.
- **Next phase:** Phase 4, gated on Phase 2's propagation gate (hard) and this phase's alerting/ownership floor.

### Phase 4 — Leverage (scale-out as a consequence)

- **Removes from the operator:** per-line onboarding toil. The operator's role in adding a product line shrinks to approving intake candidates and compliance decisions; agents and the doc-ops team execute the rest on rails.
- **Current operating capacity:** whatever Phases 1–3 produced. This phase's *pace* is set by measured marginal cost per line, never by a target date — if onboarding a line still costs more than ~2 operator-days, the fix is more Phase 1–3 work, not more pushing.
- **Organizational trigger:** business demand for fleet coverage (new lines, stock-manual backfill) AND the Phase 2 propagation gate passed. The manual-Q&A knowledge product (查客服答案, already a recorded candidate with its two metrics) additionally requires a named business owner for the answers' quality — the platform supplies cited sources, not accountability.
- **Technical scope:** batch intake campaigns on the existing skills; Workstream O online-first proofs (zero hand-committed snapshots); Workstream N long-form assembly only where its design gate and ROI clear; Q&A as its own workstream; service extraction (e.g., a real queue service replacing Actions) only if measured throughput demands it — the first phase where that conversation is legitimate.
- **Exit criteria:** none — this is steady state. Health is judged by the KPIs: marginal cost per line flat or falling as line count grows, operator interventions per publish falling, every Phase 0–3 mechanism holding at 10× volume.

## 5. Business Work Is the Discovery Engine

This platform's defenses were not designed in the abstract — they were built from production events: probe workstreams fired real signals on day one, backport rules hardened after live mis-writes, the intake completeness gate exists because a real QC round exposed the gap. The roadmap makes that the *method*, not an accident:

- **Every platform backlog item must cite the production event that exposed it.** (The milestone notes already do this; keep it a registration requirement.) An improvement with no production evidence behind it waits.
- **Business pain re-prioritizes phases legitimately.** When delivery work exposes an operational wall, the matching roadmap item jumps the queue — that is the system working. The reverse also holds: platform items that no production event has validated do not jump anything.
- **Deliveries double as drills.** Restore drills, cold-start drills, rollback drills, and V-pilot propagations run against real production artifacts and real review rounds wherever possible, so verification costs no extra capacity.
- **The dashboards close the loop.** The ops face turns production friction into measured backlog evidence; the value face turns platform work into business-legible outcomes. Both must keep recording from zero — a metric without history cannot re-prioritize anything.

## 6. KPIs

All on the existing [`flow_dashboard`](../../tools/flow_dashboard.py), extended. The first two are the roadmap's primary axis:

- **operator interventions per published manual** (dispatches watched, manual merges, hand-holding steps) — must fall phase over phase
- **bus factor ≥ 2 on every flow** (human or documented-agent path; register in [`../../ONBOARDING.md`](../../ONBOARDING.md) §3)
- propagation lag: template fix merged → all open review branches bumped
- queue wall-time per target and per rebuild wave
- marginal onboarding cost per product line
- reflow rate and TM hit rate (already measured)
- content-restore drill time
- % of agent writes carrying a full audit trail

## 7. Operating Under Long-Term Constraints (core philosophy)

Assume the constraints are permanent: one primary operator, business-first, limited engineering capacity, no dedicated platform organization. Under that assumption:

1. **Platform improvements must never block business delivery.** A slice that would delay a manual ships after the manual. No exceptions; the roadmap has no deadline that outranks a delivery.
2. **Every improvement must reduce future workload.** The test for any platform PR is "whose recurring effort does this remove?" If the answer is nobody's, it is scope creep — decline it, whatever its engineering appeal.
3. **Evolve incrementally; never rewrite.** Single-PR slices, behavior-preserving moves, pilots on one family before fleets, abandonable mid-stream. The standing Deferred rules ([`../next_optimization_checklist.md`](../next_optimization_checklist.md) §7) are constitutional.
4. **Agents are the workforce; the operator is the judgment.** Route mechanical work through governed agent flows (propose → validate → review). Spend the operator only where compliance, content truth, or organizational trust genuinely require a human — and keep shrinking that set deliberately.
5. **Make organizational dependencies visible instead of absorbing them.** Where a target needs a second human, IT ownership, or a business decision, the roadmap says so explicitly (§4 triggers) and the evidence (bus-factor register, dashboards, drill timings) is kept current — so that when the organization is ready to invest, the case is already made. Silently working harder hides the very signal management needs.
6. **Steady state is a valid outcome.** If no trigger ever fires, the platform after Phases 0–2 is deliberately sustainable for one operator indefinitely: recoverable, alerting, propagating automatically, with judgment concentrated where it belongs. Later phases are options the organization can exercise, not debts the operator owes.
7. **Business work is the discovery engine** (§5). Platform evolution grounded in production reality is slower on paper and faster in truth, because nothing gets built twice.

## 8. What We Will Explicitly NOT Do

No microservices split, no CMS/Bitable replacement, no export-stack (Word/PDF/IDML) rewrite, no repo-wide big-bang reorg, no structuralizing compliance prose beyond the content-truth allocation rule. Every one of these is a standing Deferred or architecture decision already recorded in this repo; this roadmap keeps them binding. The platform wins by compounding what works, not by re-founding it.
