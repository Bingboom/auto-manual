# Requirements: Product Skeleton Library (说明书骨架库 · 类 DITA 产线改造)

Status: draft requirements — pending operator finalization · Owner: 夏冰 · Drafted 2026-08-20

Scope of this file: *what* the skeleton-library program must deliver and *why*,
the phase gates, the operator inputs, and the acceptance criteria. The
mechanism design lives in
[`Product_Skeleton_Library_Design.md`](Product_Skeleton_Library_Design.md).

## 0. One-liner

Upgrade the manual production line from "one superset template + boolean
subtraction" to a **DITA-like information model** — a skeleton library (maps),
a module library (topics), applicability filtering (DITAVAL-like) — grounded
in a **full audit of the existing manual corpus**, and executed as a staged
retrofit that keeps the existing RST / manifest / four-renderer stack. The
DITA **concept model** is adopted; the DITA **XML toolchain is not**.

## 1. Background & motivation

- Operator insight (2026-08-20): the current template is really the manual's
  *skeleton*; every product can get a skeleton at R&D time; reusable parts are
  modules; there can be many skeletons. The single-template system is the
  multi-product scaling bottleneck.
- The six-perspective repo assessment behind
  [`Product_Skeleton_Library_Design.md`](Product_Skeleton_Library_Design.md)
  confirmed: the skeleton concept is already implemented but unnamed (page
  manifests + family anchors), and the real bottlenecks are (1) a missing
  module layer, (2) no product-category axis, (3) an implicit skeleton
  parasitic on sibling live data.
  > **Corrected by the Phase A corpus audit**: bottleneck (2) was mis-stated.
  > Measured attribution is regional convention **43%** vs category **12%**, and
  > language arrangement alone explains **82%** of page-count variance while
  > being the least mechanised part of the pipeline. The axis that was missing
  > is not category alone — it is the pair `(skeleton_family × house_style)`,
  > and the highest-value first cut is language-block parameterization.
- DITA is the industry prior art for exactly this shape of problem. Naming the
  correspondence gives the program a shared vocabulary and a tested reference
  model — while the strategy boundary ("the enemy is template forks, not
  templates") decides what we take and what we refuse.

## 2. Concept mapping (Decision D1: adopt the model, not the toolchain)

| DITA concept | This repo's counterpart | Status today |
| --- | --- | --- |
| map (topic sequence + hierarchy) | page manifest `docs/manifests/manual_*.yaml` (the skeleton) | 17 files, effectively **one** chapter skeleton |
| map family / branch reuse | [`family/index.yaml`](../../docs/manifests/family/index.yaml) anchors + JSON-Pointer diffs | live mechanism, 2 anchors, verification-only |
| topic (reusable content unit) | page template / section module | whole-page granularity only; the section-module layer is an empty shell |
| conref / keyref (transclusion, key indirection) | snippets registry, `{{ copy:* }}` keys, `\|PIPE\|` placeholders | placeholders and copy keys live; snippets registry literally empty |
| props + DITAVAL (conditional filtering) | capability gates, `lang_blocks`, per-model language trims | live; boolean subtraction only |
| specialization (domain vocabularies) | per-category structure vocabularies: `Row_key`/`Slot_key` dictionaries, capability vocabulary, intake field-mapping rule sets | hardcoded to the power-station category |

**D1 rationale:** the four-renderer stack (LaTeX/IDML/Word/HTML), the review-
branch propagation contract, the Feishu source tables, and the golden baselines
are the accumulated capital of this system; DITA-OT/XML would replace all of it
for concepts we can express in the carriers we already govern. Migrating the
carrier is a rewrite; adopting the model is a refactor.

## 3. Goals

1. **A skeleton library derived from evidence, not speculation**: ≥2 real
   category anchors whose page sequences come from the corpus audit.
2. **A module layer** such that cross-category shared content (safety clauses,
   warranty legal text, FCC, storage guidance, …) exists once per language and
   is referenced, not copied.
3. **A 2-D anchor key `(skeleton_family × house_style)` as a first-class axis**
   in config/queue routing, shared content planes, and structure vocabularies
   — category alone is insufficient (see the note in §1).
4. **Onboarding becomes instantiate-and-fill**: a new product gets its skeleton
   seeded at R&D time (structure first, `⚠️需确认` values later, diff-based
   revisions), replacing clone-a-sibling-and-mutate.

## 4. Phases

### Phase A — Corpus audit & information-architecture analysis (read-only)

The operator supplies the full set of typical manuals (§5); the analysis
produces the evidence base for every later decision.

- **A1 corpus register**: every manual logged — category, model, region,
  language, layout family, carrier, source location. Suggested spine: the
  `发布文档管理` catalog
  ([`product-manual-catalog`](../../.agents/skills/product-manual-catalog/SKILL.md))
  plus in-flight lines.
- **A2 structural decomposition**: per manual, extract the chapter tree and
  normalize it into a **topic inventory** (topic id, title, granularity,
  occurrence count). Reuses the decomposition muscle of
  [`markdown-rst-template-intake`](../../.agents/skills/markdown-rst-template-intake/SKILL.md).
- **A3 reuse analysis**: cross-manual clustering; classify every topic as
  *universal* / *category-common* / *product-specific*; output a reuse matrix.
  **Normalize before comparing** — the 118 substantive divergences found by
  the language-asset governance sweep will make identical content look
  different; this step coordinates with that effort.
- **A4 skeleton induction**: propose the candidate anchor set (one per
  category) with page sequences and divergence points; validate by
  **reconstruction** — candidate skeletons + modules must reproduce ≥ X% of
  the corpus structures (X set by the operator, §5).
- **A5 vocabulary delta**: per-category differences in `Row_key`/`Slot_key`
  rows, required placeholder rows, and capability vocabulary.

Deliverable: **Manual Information-Architecture Audit** — topic ledger, reuse
matrix, candidate skeleton library, vocabulary deltas, retrofit priority
recommendation.

Acceptance: every corpus item traceable in the register; reconstruction
coverage ≥ X%; the operator confirms the category split (the split is a
business adjudication — the report supplies evidence only).

Method gate: pilot the decomposition on ~10 representative manuals first;
only run the full corpus after the method survives the pilot.

> **Status 2026-08-20: first round executed** — see
> [`manual_ia_audit_2026-08.md`](manual_ia_audit_2026-08.md). The operator
> supplied the full corpus at once (56 PDFs, 便携主机 + 便携加电包), so the
> full run replaced the 10-manual pilot and the method risk moved to result
> review; the report records the two execution deviations found and corrected.
> Measured reconstruction coverage: **79.3%** by pure deletion (67.3% first pass,
> 78.2% after the caliber fix), **94.8%** allowing ≤1 overlay per manual. Threshold X%
> is now an operator decision against real numbers rather than a guess.

### Phase B — Design finalization

Revise [`Product_Skeleton_Library_Design.md`](Product_Skeleton_Library_Design.md)
with Phase A evidence: the category split, the first new anchor, the
shared-plane layering choice, and the §9 open questions — all resolved.

Acceptance: design approved by the operator; every §9 question has a recorded
decision.

> **Status 2026-08-20: executed, awaiting approval.** The operator decided CN is
> its own skeleton (design D2). The revised design settles the anchor key
> (2-D sparse `skeleton_family × house_style`, 5 cells), the measurement caliber
> (printed-page layout order), the shared-plane approach (mapping file, no
> directory re-layering), the first module cut
> (`user_maintenance_instructions`), and retrofit phases B0–B9. It also
> withdraws four v1 claims — notably diff line count as a skeleton-distance
> signal, which measurement showed does not exist. Eight questions remain open,
> of which three are compliance/filing adjudications that must precede any
> automatic chapter insertion.

### Phase C — Production-line retrofit

> **Execution plan drafted 2026-08-21**:
> [`../dev/skeleton_library_expansion_plan.md`](../dev/skeleton_library_expansion_plan.md)
> (three waves over B0–B9, per-phase unlock counts, operator gates, and the
> "pipeline output + InDesign finishing layer" premise).

Execute the design's §6 phasing (P0 registry naming → P1 category axis →
P2 generative fold → P3 module layer → P4 R&D-time seeding). Each phase is
independently shippable with CI green and golden conservation; live-table
schema steps stay operator-gated.

Final acceptance: **the next real new-category product onboards by
instantiate-and-fill** within the operator-day target — which also field-tests
Workstream W's "new line in ≤2 operator days" exit criterion in the same
event.

## 5. Operator inputs (blocking, requested up front)

1. **Corpus scope**: which manuals count as "typical" — suggested: the entire
   `发布文档管理` catalog, in-flight lines, plus any external benchmark manuals
   worth mirroring.
2. **Carriers**: Feishu doc links / PDF / docx per item; mark scanned PDFs
   (OCR needed) vs text PDFs.
3. **Prior category taxonomy**: the operator's initial category split, to be
   validated (not replaced) by the evidence.
4. **First pilot category**: which non-power-station category becomes the
   second real anchor.
5. **Thresholds**: reconstruction coverage X% (Phase A) and the operator-day
   target (Phase C final acceptance).

## 6. Boundaries & non-goals

- No DITA XML, no DITA-OT, no new authoring format: RST + manifests + Feishu
  tables remain the carriers.
- No renderer-stack or style-contract changes.
- Prose-body migration stays Workstream N's, under the allocation rule
  ("layout, directives, page skeleton → repository RST template → always").
- Phase A is strictly read-only; no production-line or live-table changes
  before Phase C's gated steps.
- Does not queue-jump the Workstream T Tier-1 operational items.

## 7. Relationship to existing workstreams

Per [`../optimization_project.md`](../optimization_project.md): merges with
**M** (composition authority); requires **Q** first (template-sync
propagation); co-requisite with **V** (review-branch propagation keeps
multi-skeleton cost sub-linear); bounded by **N**'s allocation rule; **O**
remains deferred pending V's implementation (its design gate passed
2026-07-31); **W**'s untested exit criterion becomes part of Phase C
acceptance; the language-asset governance effort feeds Phase A3 normalization.

## 8. Risks

- **Analysis ≠ adjudication**: the category split and module boundaries are
  business decisions; the audit provides evidence, the operator decides
  (the standing lesson that adjudication direction is the governance core).
- **Corpus contamination**: historical divergences masquerade as intentional
  differences; A3 must normalize first or the reuse matrix understates reuse.
- **Scale control**: full-corpus decomposition with an unproven method burns
  effort — hence the 10-manual method gate.
- **Rollback lesson (Workstream H)**: never pilot modularity on the most
  divergent page; start from the most stable shared prose.

## 9. Revision log

- 2026-08-20: initial draft, from the operator's DITA-map framing plus the
  six-perspective repo assessment.
