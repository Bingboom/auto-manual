# Product Skeleton Library Design

Status: **Phase B design — pending operator approval** · Owner: 夏冰 · Created 2026-08-20, revised same day after the Phase A corpus audit and the Phase B remeasure round

## 1. Role

This is the design for elevating the manual **skeleton** (骨架) — the per-line,
data-declared page composition of a manual — to a first-class object, so the
system scales past a single product category. It captures the operator's
2026-08-20 framing: *the template is really the skeleton of a manual; every
product can get a skeleton at R&D time; the reusable parts are modules; there
can be many skeletons.*

Positioning inside the existing document set:

- It is a **superset restatement of Workstream M** ("`page_registry` becomes
  the only composition authority") in
  [`../optimization_project.md`](../optimization_project.md), not a new layer
  beside it.
- It stays inside the allocation rule of
  [`Long_Form_Content_Block_Design.md`](Long_Form_Content_Block_Design.md):
  *"Layout, directives, page skeleton → repository RST template → always."*
  This design governs **composition**; prose migration remains Workstream N's.
- It builds on the family-manifest diff carrier
  ([`family_manifest_diff.md`](family_manifest_diff.md),
  [`../../tools/manifest_family.py`](../../tools/manifest_family.py)).

Evidence base — read these before reviewing this design:

- corpus audit: [`manual_ia_audit_2026-08.md`](manual_ia_audit_2026-08.md)
- program requirements and phase gates:
  [`product_skeleton_library_requirements.md`](product_skeleton_library_requirements.md)
- strategy boundaries: [`System Evolution Strategy.md`](System%20Evolution%20Strategy.md)
- canonical entity model: [`Content_Data_Model.md`](Content_Data_Model.md)
- review-branch propagation: [`Review_Branch_Propagation_Design.md`](Review_Branch_Propagation_Design.md)

## 2. Operator decisions already settled

| # | Decision | Date | Rationale |
| --- | --- | --- | --- |
| D1 | Adopt the DITA **information model**, not the DITA XML toolchain | 2026-08-20 | RST + manifests + Feishu tables + four renderers are the accumulated capital; changing carrier is a rewrite, adopting the model is a refactor |
| D2 | **CN is its own skeleton** (`MAIN@CN`) | 2026-08-20 | Not sequence distance (it is only 1 reorder + 1 insert from `MAIN@INTL`) but a **house-style signature**: the opening, warranty and tail slot are independently authored, there is no TOC, the symbol table is deleted outright, and the back cover merges into the conformity certificate |

> **D2's stated rationale was corrected on 2026-08-20.** It was first recorded
> as "the 7 CN manuals are independently authored, not translated". Measured at
> topic granularity on HTE152, that is **half wrong**: only 3 topics are CN-
> authored (`preface_important`, `warranty`, `cn_conformity_certificate`), while
> **12 share lineage with `MAIN@INTL`** — CN safety bullets 1–7 and 10 map
> one-to-one, in order, onto the EU chapter's 8 bullets; storage is
> sentence-for-sentence identical; the fault-code table is the same 12 codes in
> all four regions; the LCD icon set maps item-for-item. **The decision stands**
> — the signature above is a stronger and checkable reason — but the original
> wording would have produced the wrong answer next time it was applied.

**D2 generalizes into a rule this design encodes as a field**: skeleton
boundaries follow content lineage, not diff size. See `body_lineage` in §5.2.
The same ruler, applied to the JP battery packs in §4.2, gives the *opposite*
answer — and applied to HTE153 KR it routes that manual **into** `MAIN@INTL`
(§4.2b). Three applications, three different destinations: the ruler is doing
work, not rubber-stamping.

## 3. What changed after Phase A/B (corrections to the v1 draft)

The first draft of this design was written before the corpus was read. Four of
its claims did not survive:

1. **"Category as a first-class axis" was the wrong headline.** Measured
   attribution: regional convention **43%**, model capability 19%, category
   **12%**, regional compliance 8%. Category matters, but it is not the main
   scaling bottleneck.
2. **The v1 promotion signal does not exist.** §4 Principle 3 proposed using
   diff size ("the US→EU carrier is 600+ lines today") as a skeleton-distance
   signal. Mechanically re-measured: that 714-line diff is **one operation** —
   `replace /pages` with a 91-element verbatim list. It is a backup, not a
   difference description. Meanwhile `jp`/`zh`, which are genuinely further
   away, produce only 114 lines. Diff size is a function of accidental
   page-count equality, not similarity. **Promotion must be keyed on semantic
   operation count** (`jp`=14 > `kr`=7 > `us-single-fr`=2 matches intuition;
   line count does not).
3. **A one-dimensional anchor list cannot express the corpus.** Two Phase A
   lenses gave opposite answers for the JP battery packs; that conflict was a
   symptom of a missing schema dimension, not noise (§4.2).
4. **The biggest win is not the category axis — it is language-block
   parameterization.** Language arrangement explains **82%** of page-count
   variance, requires zero judgement, and is the least mechanised part of the
   pipeline: [`manual_eu.yaml`](../../docs/manifests/manual_eu.yaml) is 429
   lines / 91 page entries — a 15-page language block hand-copied six times —
   while [`../../data/model_languages.csv`](../../data/model_languages.csv) has
   6 rows against 4 distinct EU language sets in the corpus.

## 4. The skeleton library, as measured

### 4.1 Anchors are a sparse 2-D matrix, not a list

The anchor key is **(`skeleton_family` × `house_style`)**. Five cells are
populated; the matrix is sparse and no Cartesian product is implied.

| Cell | Members | Was (Phase A) |
| --- | --- | --- |
| `MAIN@INTL` | **28** | A1-INTL-MAIN (+HTE153 AU/KR/BR) |
| `MAIN@JP` | 12 | A2 minus the 2 battery packs |
| `MAIN@CN` | 7 | A3-CN-MAIN (operator-decided, D2) |
| `BP@INTL` | 4 | A4-INTL-BP |
| `BP@JP` | 3 | **new cell** — absorbs A5's `HTP007` plus the 2 JP battery packs |

**Five cells, and the seven-region test says five is right** — see §4.2b. No
cell is added for AU / KR / BR / MX / PH: every one of their differences is
absorbed by the fragment layer, the language axis, or `region_profile` below.

Axis ownership, corrected against the HTE152 and HTE153 factorials:

- **`skeleton_family` ∈ {MAIN, BP}** owns the **topic universe and capability
  slots** (not per-book topic existence — that is
  `family universe ∩ house_style absorption ∩ capability gate ∩ optional
  slots`), the **semantic same-page pairing** (e.g. the storage+troubleshooting
  tail cluster, 6/6 in HTE153's INTL members with y-coordinates matching to the
  point), and the body module skeleton.
  *Typographic-slack co-page* is explicitly **not** a constraint and is not
  stored as one.
- **`house_style` ∈ {INTL, JP, CN}** owns chapter label vocabulary, opening
  composition, absorption rules, and the warranty/legal **convention**.
  It does **not** own compliance carrier, language set, legal entity, or unit
  system — those diverged *inside* the INTL cell (§4.2b) and moved to
  `region_profile`.
- **`region_profile`** (new; an overlay key space, **not** a third anchor key)
  owns the compliance fragment mounting row, safety-module regional variant,
  unit system, legal-entity/contact module, brand display name, language-set
  reference, TOC on/off, back-cover form, and cover module.
  Keeping region out of the anchor key is deliberate: promoting it would split
  the 28 `MAIN@INTL` manuals into seven cells — precisely the "8+ phantom
  skeletons" §4.2 already rejected. The mechanism is §6.3's existing
  `fragment + (region, host_page, repeat_per_language)`, generalized from
  compliance-only to region-keyed module variants.
- **`house_style_version` ∈ {v1, v2}** is an *attribute* of `house_style`, not
  a fourth key. It owns the order profile and safety-block placement.

**A5 dissolves.** Its three members shared a signature (specifications first,
safety blocks last, `保証サービス` instead of `保証について`, `認証` row instead
of a compliance chapter) that spans *two categories* — a cross-category
"skeleton" is not a skeleton, it is a house-style version. Under the 2-D key
they land automatically: `HTE119 日规 → MAIN@JP@v1`, `HTP007 日规 → BP@JP@v1`,
with zero extra overlays (both need the identical 5 rules).

### 4.2 The decisive evidence: a full 2×2 factorial

One SKU pair populates all four cells with real data:

| | INTL | JP |
| --- | --- | --- |
| **MAIN** | HTE151 美加规 (FridgeGuard) | HTE151 日规 (SlimPower H1) |
| **BP** | HTP015 美加规 | HTP015 日规 |

Both factors vary independently and every cell is occupied. A 1-D key must
pick one axis as primary and re-encode the other inside overlays — which is
exactly the failure mode of `manual_eu.yaml` (a language block written six
times), promoted to the anchor layer.

The JP battery packs go to **`BP@JP`**, not `MAIN@JP`:

- Their `body_lineage` is `translated_from: BP@INTL` (11/11 safety items,
  7/7 symbols, 11/13 page-grid slots align).
- Routing them to `MAIN@JP` would need 2 *insertions* (`connections`,
  `placement` — both 0/14 in `MAIN@JP`) plus a safety-module *replacement*.
  By the same acceptance line that kept `MAIN@JP` separate from `MAIN@INTL`,
  that fails.

**Decision rule, reusable:** if the difference is topic existence or page grid,
it can only be expressed by insertion → that layer defines the anchor base.
If it is labels, chapter order, absorption position, legal module, or language
set → that is the overlay domain. **Category sets the base; house style is the
overlay.**

> **The rule applies at *topic* granularity only.** At *block* granularity it
> would split `MAIN@INTL`, because the US safety chapter is five inserted
> blocks relative to the EU one (§4.2b). Block-level insertions go to
> `region_profile` module variants and never promote an anchor. Without this
> clause §6's module layer contradicts §4.2 on its first day.

One count that supported this rule needs repair: §4.2's claim that
`connections` is 0/14 in `MAIN@JP` is **false** — it is 3/13 (HTE139 日规,
HTE159 日规, HTE152 日规), recorded under two different ids (`connections` vs
`extra_battery`) across six manuals. That is a W3-class normalization defect,
not a topic gap. The *conclusion* for the JP battery packs is unaffected — it
rests on the safety-module replacement, not the count — but the arithmetic
behind it must be recomputed before it is quoted again.

### 4.2b The dual factorial: HTE152 and HTE153

§4.2 varies `skeleton_family`; two later intakes vary `house_style` under a
fixed family, giving each axis its own controlled experiment.

**HTE152 (4 manuals, 1×3 house-style row with INTL double-occupied).** This is
the only sample where one cell holds two manuals of the same SKU, so it can ask
whether `house_style` is a *function*. It is not. Of 23 structural differences:
house_style accounts for 48%, **region for 43%**, model capability 4%, and 4%
has no key at all. Four items the v1 design assigned to `house_style` took two
different values inside `MAIN@INTL`: language set (US 3 languages vs EU 6),
compliance carrier (US untitled FCC block on the box-contents page repeated per
language vs EU RED DoC on a shared single-language back cover), legal entity,
and unit system. Two more diverged in the *family* domain: `safety_info` is two
different modules (US ~30 items over 2 printed pages including grounding
clauses; EU 8 items on 1 page) and block length is 20 vs 19. Hence
`region_profile` and the axis-ownership rewrite in §4.1.

**HTE153 (7 regions, 1 SKU — the decisive test).** Same family, same model, so
capability variance is zero by construction. Six of the seven are INTL members.
Result: **INTL holds for seven regions; no split.** All four house_style
definition items are invariant across 6/6 — one label vocabulary translated per
language, the same `safety → UMI (demoted bar) → symbols` opening cluster with
UMI never in a TOC, the same INTL limited-warranty module (3+2 years,
item-for-item, KR and BR being structural translations), and a 13-chapter body
sequence with **zero reorders**. **Zero family-domain violations.** KR was the
one candidate for splitting out — it shares two signals with JP (a
domestic-only cover, no in-book compliance carrier) — but both proved to be
cross-style *region* parameters rather than JP essence (HTE153 JP also carries
no in-book compliance), while all four genuine JP signals are absent from KR,
which keeps the INTL preface block and limited-warranty. Two KR manuals across
two SKUs and two eras agree.

Consequences worth recording:

- The Phase A "US/EU symbol-first swap" was a **phantom** — geometry shows UMI
  first in both; it only looked swapped because UMI never enters the TOC. Even
  that overlay disappears, leaving the seven manuals with no slot-pair swap at
  all.
- Front-matter and cover modules cross house-style boundaries: JP and KR use
  the *same* domestic-only cover module, and JP's TOC language band is the INTL
  multi-language band degenerated to one. The module layer must therefore allow
  front-matter to mount by **region**, not by style.
- HTE153 is designated the skeleton library's **regression baseline SKU** — the
  only one with all seven regions in the corpus *and* all seven targets filed
  in the repo, so corpus and pipeline can be reconciled in both directions.

### 4.3 Measurement caliber (settled in Phase B)

**Canonical order = layout order at printed-page granularity. Same-page order
is a non-contractual attribute. Text-extraction order is forbidden as a
caliber.**

Why this matters and what it fixed:

- The Phase A report claimed the TOC order and layout order conflict. Measured
  on 6 manuals: they agree **6/6**. The real culprit was a *third* caliber —
  PyMuPDF extraction order — used by one decomposition batch without visual
  verification.
- Extraction order fails in two forms, both reproduced: **(A)** whole-title
  inversion (only 2 of 16 same-page books — so the report's "systematically
  inverted" claim is false and is being corrected); **(B)** body text extracted
  *above* the preceding title, which defeats any "first occurrence" heuristic
  and was not recorded at all. → Tooling must derive order from **block bbox
  (y, x) geometry** or visual verification, never from character offsets.
- Layout order is the only caliber with **55/55 coverage**: all 7 CN manuals
  have no TOC page at all, and it works on the 8 outlined files (rendering does
  not need a text layer). A primary key cannot rest on an attribute missing
  from 13% of the corpus.
- **TOC order is still stored**, as a checkable second column: a
  `toc_order ⊑ layout_order` gate turns TOC/layout mismatch into a *defect
  report* rather than a fork. Live example: `HTP011 欧英规` lists storage before
  spec in its fr/es/it TOC blocks while all five body blocks put spec first —
  the TOC is the wrong side.

### 4.4 Reconstruction, recomputed

| Cell | Pure deletion | Notes |
| --- | --- | --- |
| `MAIN@INTL` | **22/28 = 78.6%** | was 16/25 → 19/25 (3 extraction-order false forks removed) → +3 new HTE153 manuals, all pure-deletion passes (BR is a zero-operation identity match) |
| `MAIN@JP` | 13/14 = 92.9% | unchanged |
| `MAIN@CN` | **7/7 = 100%** | was 4/7; under printed-page granularity the 3 same-page books are ties, **0 overlays needed** |
| `BP@INTL` | 3/4 = 75.0% | unchanged |
| `BP@JP` | pending | new cell, needs its own canonical sequence |

**Whole corpus: pure deletion 37/55 → 43/55 → 46/58 = 79.3%; ≤1 overlay
55/58 = 94.8%.** If the operator sets the Phase A threshold (requirements §5),
the numbers to use are **79.3% / 94.8%**.

`T2` (storage↔troubleshooting swap) goes from "the biggest single overlay load,
7 books" to **1 book** (`HTE157 美加规`, a genuine fork on different printed
pages). It should be reclassified as a **per-book slot-pair parameter**, merged
with `BP@INTL`'s storage↔spec pair.

> **Why CN reaches 100%** — the causal finding, not just a recount: `storage`
> is a 6-line page-footer filler block in **all 7** CN manuals (y = 62–78% of
> page height, never at page top), while `troubleshooting` is a full-page fault
> table. Which one lands first is decided by how much room the preceding
> `充电方式` chapter left — a typesetting artifact, not editorial intent. In
> `HTE156 中规` three blocks share one page, which settles it. So the CN
> canonical sequence writes storage and troubleshooting as an **unordered tail
> cluster** between charging and specifications, with troubleshooting optional.
>
> A second Phase B agent, measuring under strict y-order, reported CN as a
> 3-3 tie needing an operator decision. Both are right under their own caliber;
> the caliber choice in §4.3 — itself backed by the page-filling mechanism
> above — is what dissolves the tie.

## 5. Schema

### 5.1 Three tables, not one

`docs/manifests/family/index.yaml` currently holds `anchors` = 2 *repository
fold bases*. Phase A's "anchors" are *corpus skeletons* with no repository
file. Merging them conflates "what can be built today" with "what the corpus
proves exists". The registry (`family-manifest-index/v2`) therefore keeps
three tables in one file: **skeletons** (the library), **members** (corpus
evidence), **realized_by** (the bridge to repository manifests, with an
explicit `status: exact | partial | none` and a `gap` note).

This immediately records a fact worth knowing:
`manual_us-single-en.yaml`, today's fold base, is a **legacy leaf** — 13 of 17
manifests carry `03_product_overview`/`05_operation_guide` as `generated_page`
while the base still uses `rst_include` placeholder pages. The base is in the
minority, and every diff pays two `slot_retype` operations for it.

### 5.2 Fields the corpus forced

- **`body_lineage`**: `authored | translated_from:<ref> | cloned_from:<ref> |
  alias_of:<file>`, stored per (cell, topic); `<ref>` may name a language block,
  and template lineage is stored separately from body lineage. This is the
  machine-checkable form of decision D2 — without it the operator's reasoning
  cannot be recomputed next time. It also satisfies the audit's standing caveat
  that 78–90% is a *slot* reuse ceiling, not a text reuse rate.

  Two findings shaped the value space. **Direction is not always decidable**:
  for CN the calque signals point CN→EN (the English "Risk of electric shock may
  occur if using accessories that are not recommended or sold by professional
  product manufacturers" mis-scopes *professional*) while the version dates
  point EN→CN (CN is a V0.5 draft from 2026-06-02; US was already V2.0 on
  05-28). The field must therefore permit an undirected "shared lineage"
  assertion rather than forcing a parent. **`cloned_from` is separately
  evidenced**: HTE153 AU is a clone of the EU EN block, not of US — 87.1% vs
  72.2% normalized block containment, and decisively it **inherits a defect**,
  the LCD-display TOC entry reading folio 05 where the body prints 04, exactly
  as in the EU V2.0 master.
- **`order_profile`**: `host_order | pack_order | spec_first`, stored as a
  reference rather than inlined, because it drifts across families and regions
  (international main = host, international BP = pack, JP BP = host,
  HTE132/HTE119 JP main = pack). Inlining it into the anchor reproduces the
  lens error.
- **Page grid as a first-class slot table** `(printed_page, [topic…])` instead
  of `(chapter, start_page)`. 7 of 10 remeasured books put two chapters on one
  printed page; with only `start_page`, their order is inexpressible because
  both chapters share a number.
- **`presentation`** — four states on the manifest entry
  (`chapter | subsection | titled_not_in_toc | untitled_block`), plus a
  separate `toc` boolean. Absence is expressed by *the entry not existing*, so
  `slot_drop` and "absent" never become two ways to say one thing; the skeleton
  side carries `requirement: required | optional | capability:<name>`.

  **All four states already exist in the repo, unnamed** — verified:
  `page_shared/en/charging.rst` (chapter), `page_shared/en/08_charging_methods.rst`
  (a standalone manifest page that renders as the previous chapter's
  subsection), `page_shared/en/01_user_maintenance_instructions.rst`
  (`\safetysubbar` style bar, never in any toctree),
  `page_us-en/01_fcc.rst` (`\HBFccBlock`, no title at all).
  `presentation_level` names four existing facts; it does not invent a concept.

### 5.3 Overlays: semantic layer above JSON-Pointer

Keep `family-manifest-diff/v1` as the **compile target**; add a semantic
overlay layer above it. The closed operation set is
`slot_move | slot_insert | slot_drop | slot_retype | presentation_set`, plus
`lang_swap` and `lang_block_expand` for the language axis.

Justification from measurement: the 15 current diffs total **277 pointer
operations / 3130 lines** but only **≈86 semantic operations**. Two failure
forms, one root cause (index-based alignment with no slot identity):
index slip produces phantom operations (KR: 271 lines, ~65% alignment residue,
8 operations to express one page replacement), and unequal length collapses to
whole-list replacement (8 of 15 diffs — information content zero).

### 5.4 Authoring flip: five stages, YAML stays

The 17 manifest YAML files are read by four renderers, review derivatives,
reference-layout pins, `tools/manifest_lint.py`, and
`page_manifest.resolve_config_pages_or_raise`. Deleting them touches four
downstream contracts at once. Terminal state: **YAML stays in the repo
permanently as the compatibility surface**, generated by an emitter and
byte-compared; the skeleton source becomes the only editing surface.

| Stage | Content | YAML written? | Rollback |
| --- | --- | --- | --- |
| S0 | today: YAML is truth, diff verifies | never | — |
| S1 | overlay files + `--check-overlay`; **both** the existing pointer diff and the new overlay compilation must pass | never | delete overlay dir |
| S2 | shadow emitter; CI asserts `emitted == committed` **raw bytes** | never (scratch only) | delete emitter |
| S3 | per-file flip of `mastered_by: yaml → skeleton`, guarded by a `check_manifest_authority` gate | by emitter | flip the field back |
| S4 | all 17 flipped | by emitter | as S3 |

S0–S2 change zero YAML bytes, so their rollback cost is exactly zero. The only
irreversible point is S3, and S3 is per-file (groupable into 4–6 PRs) — never a
big bang. This follows the original carrier migration verbatim, and the
standing feedback that fixes must be proven on a branch rather than patched
serially on `main`.

## 6. Module layer

### 6.1 Shared plane: no directory re-layering

**Decision: explicit mapping file + the 2-D sparse key. Zero file moves, zero
manifest edits.** Rejected alternatives and why:

- `page_shared/<category>/<lang>/` — spends the most expensive refactor
  available on the axis that explains **12%** of variance, while the 43% axis
  (house style) still has no first-class expression.
- `page_house/<style>/<lang>/` — right axis, but the largest one-shot cost
  (every `page_jp`/`page_zh`/`page_us-*`/`page_eu-*` directory rearranged) and
  it is *still* 1-D.

Migration cost measured: ~10 `page_shared/<lang>/…` references per manifest ×
17 manifests, **55 `page_shared` sites across 18 test files**, 5 tool sites —
and a move would simultaneously break backport sibling resolution
([`../../tools/cloud_doc_backport_orchestration.py`](../../tools/cloud_doc_backport_orchestration.py)),
asset preflight ([`../../tools/queue_asset_preflight.py`](../../tools/queue_asset_preflight.py)),
and review-branch sync classification
([`../../tools/check_review_branch_sync.py`](../../tools/check_review_branch_sync.py)),
while review derivatives are frozen per (model, region).

Note the directory convention is *already* fighting two axes:
[`../../tools/lang_registry.py`](../../tools/lang_registry.py) maps en/fr/es/de/it/uk/ko/pt-BR
to `page_shared/<lang>` but `zh → page_zh` and `ja → page_jp`, because JP and
CN are single-region house styles whose "shared" directory got named after the
style. A mapping file lets both axes be explicit without moving anything.

### 6.2 First cut: `user_maintenance_instructions`

Not product overview — that page is Workstream H's grave. The chosen module is
`page_shared/{en,fr,es,de,it,ko,pt-BR,uk}/01_user_maintenance_instructions.rst`
(13 lines), and it avoids every one of H's failure factors: no bespoke
renderer (reuses `draft_engine` slot expansion), no naive chunking of long
prose (8 lines of wrapper + 1 line of body, split on an existing physical
boundary), no prose moved into data tables, and byte conservation on the
TRUE side is assertable.

Six quantified reasons: the body/wrapper split needs no editorial judgement;
zero placeholders, brand names, category nouns, or capabilities (one of only
4 category-neutral files in `page_shared/en`); zero TOC and zero pagination
impact (25 corpus manuals have it, **0 ever list it in a TOC**); it *is* a
subsection, so it exercises precisely the empty section-module layer; no
regional forks exist for it (compare: `safety_en` US-vs-EU overlap is 40%,
`03_product_overview` only 22% — which is why H died there); and its coverage
gap (`MAIN@INTL` 24/27, `MAIN@CN` 1/7, `MAIN@JP` 0/14) makes it the minimum
probe for how the registry resolves a house style with no `page_shared/ja|zh`
directory.

### 6.3 Compliance as mountable fragments

One schema — `fragment + (region, host_page, repeat_per_language)` — over
**six measured forms plus one missing fragment**:

| Region | Carrier | Evidence |
| --- | --- | --- |
| US / CA / MX | untitled block parasitic on the box-contents or overview page, repeated per language block | HTE153 US at EN p6 / FR p24 / ES p42 |
| EU / UK | shared single-language DoC on the back cover, not repeated | 8 manuals |
| BR | FCC block as US/CA **plus** a titled `REGULAMENTAÇÃO ANATEL` back-cover block | HTE153 BR printed p03; ANATEL cert 05561-26-18577 |
| JP | `認証：` row inside the spec table — **v1 only** | HTE154 日规, HTE119 日规 |
| AU | **nothing mounted** (explicit empty row, 3/3 across 2 SKUs and 3 generations) | HTE118, HTE133, HTE153 AU |
| KR | **nothing mounted**; the statutory product name is lexicalized into the product-name string instead (2/2) | HTE118 KR, HTE153 KR |

Three constraints this table encodes:

1. **The carrier is a per-book mounting fact, not a house-style constant.**
   HTE153 日规 carries no `認証` row at all (whole spec table verified), and
   neither do HTE139 日规 or HTE159 日规. "JP = `認証` row" is a
   `house_style_version = v1` property and must not be defaulted for `MAIN@JP`.
2. **Absence must be recorded as an explicit empty row**, distinguishable from
   "not yet surveyed", and flagged for legal sign-off. Per the audit's rule that
   regional compliance (8% of variance) is never data-driven, an empty row is
   evidence, not authorization.
3. **`anatel@back_cover` is a real production gap**, not a modelling nicety:
   it is zero-hit across `docs/templates` and `data/`, and
   `manual_pt-br.yaml` has no back-cover entry at all — so the legally required
   ANATEL statement **cannot currently be produced**. It joins B8's first batch,
   reusing the EU-DoC back-cover carrier form.

Note the pipeline currently renders FCC as a standalone page (`p22_01_fcc`),
which matches **none** of the corpus. That form change is gated on operator
decision (§8), so the first delivery builds the carrier and leaves both forms
selectable rather than silently switching.

### 6.4 Contract tiering removes the fork escape hatch

`contracts/03_product_overview.yaml` hardcodes `SIDE_AC_INPUT_*` /
`FRONT_AC_OUTPUT_*` as required placeholders, so any model without AC input
fails the gate and **the only escape is forking the whole contract**. JE-300E
already paid that bill (1 contract + 5 forked RST files); 9 more manuals are
queued to pay it (HTE150 日规, HTE162, 7 battery packs). Tiering the key to
`default | <lang> | capability:<cap> | category:<cat> | region:<region>` plus a
`requires_capability` group flag removes the mechanism — this is the one place
in the repo that *structurally compels* template forking.

## 7. Retrofit phases

Each phase is independently shippable with CI green and golden conservation.
Full file-level mapping lives in the workflow artifact (§10); the ordering
constraints below are the load-bearing part.

| Phase | Content | Unlocks |
| --- | --- | --- |
| **B0** | **Ordinal decoupling** — explicit `ordinal` on page entries, page-name lock, contract `source_ref` gate | 0 manuals; **absolute prerequisite for B1–B9** |
| B1 | Language-block parameterization + registry `v2` | 0 directly; gives the 82%-of-variance axis its first carrier |
| B2 | `app_setup` capability gate + `App/联网` column | stops 13 manuals printing a non-existent App chapter |
| B3 | `MAIN@JP` anchor repair (three-part opening) | 12 JP manuals structurally |
| B4 | `MAIN@CN` anchor repair + conformity-certificate tail slot | 7 CN manuals |
| B5 | `BP` family anchor (+ `target_defaults` fix first) | battery packs 0 → 7; SKU coverage 5/22 → 8/22 |
| B6 | `page_registry` becomes composition authority (+ scope columns) | 0 new manuals; collapses the *marginal* cost of new lines — Workstream M's exit criterion |
| B7 | Contract tiering; reclaim the JE-300E fork | structurally unblocks 9 queued forks |
| B8 | Compliance fragments + `Row_key`/`Variant_key` split | EU/UK DoC carrier; prerequisite for scaling to 22 SKUs |
| B9 | Data-quality closeout + reverse-gap registration | PH 1 manual; 12 unreferenced targets explicitly classified |

### 7.1 Why B0 is an absolute prerequisite (verified in code)

[`../../tools/gen_index_bundle_plan.py`](../../tools/gen_index_bundle_plan.py)
calls `filter_pages_by_capability` at line 117, but the ordinal loop starts at
line 130 — so **dropping a page by capability shifts every subsequent `pNN_`
name**, while language trimming (`continue` after the ordinal increment) does
**not**. That asymmetry means B2, B3, B4 and B5 all carry silent page-rename
risk, and the only gate that would catch it
(`validate_approved_reference_plan`) runs only in IDML production builds —
precisely the blind spot behind the reference-layout pin drift incident, where
a decoupled contract pin went through three PRs unnoticed. **No manifest is
touched before B0.**

### 7.2 B5 must first repair a latent CLI-wide blocker (verified)

[`../../tools/target_defaults.py`](../../tools/target_defaults.py) raises
`Default config resolution is ambiguous for family …` when two configs tie on
`_family_config_score`, and `_DEFAULTS = discover_target_defaults()` executes
at **module import** (line 148). A new `config.bp-jp.yaml` would tie with
`config.ja.yaml` — so adding the battery-pack config would make the **entire
`build.py` CLI fail to start**, not just that target. B5 therefore lands an
explicit `build.family_default: true` marker before any new family config.

### 7.3 Workstream wiring

- **Hard serial**: B0 → everything. B0 → Workstream **V** (page-name stability
  is what lets per-branch bump PRs classify authored-vs-placeholder edits by
  filename). B3/B4/B5 → B6 — if **M** lands first it freezes *today's wrong* JP
  and CN composition into the data tables, and correcting it then means a
  mirror schema change instead of a one-file YAML edit. **Make the manifests
  tell the truth first, then let data take over.** T-K4 (source-table backup)
  → B6/B8, both of which change `data/phase2/**` schema. B7 → B8 (tier keys
  and `Variant_key` are two projections of one tiering semantics).
- **Parallel**: Workstream T Tier-1 (K4/K5/K7/K1) ∥ B0–B5, zero shared files.
  Workstream Q ∥ B0–B2, but Q must lead or accompany B3 (JP is a live publish
  line; new pages change what backport's Class-T classification sees).
- **Workstream O** stays deferred; its V design gate passed 2026-07-31, so the
  remaining dependency is V's implementation.

### 7.4 Out of scope for v1

Same-page constraints and page-budget solving (the reference-layout contract's
`composition_id` already groups same-page chapters — v1 adds only a
`printed_page_offset` field rather than four new ones; page-budget solving is a
layout-engine problem and belongs to Workstream X); **TOC auto-generation**
(needs page budget, and generating a TOC before `presentation_level` is in the
data would systematically mis-render the "titled but not in TOC" state — 25
manuals' `user_maintenance_instructions` and 12 manuals' `fcc` are exactly
that state); DITA XML/DITA-OT (decision D1).

## 8. Open questions for the operator

Settled: D1 (model not toolchain), D2 (CN independent), the anchor key
dimensionality, the measurement caliber, the shared-plane approach, and the
first module cut. Still needing a decision:

1. **One compliance gap left, plus one new production gap.** The original three
   resolved as follows: HTE153 美加规/墨西哥规 "no FCC" was **a decomposition
   miss, not a gap** — the block is in the very file the audit registered
   (EN p6 / FR p24 / ES p42), missed because of the same "FCC never enters a
   TOC" trap the audit itself warned about; pt-BR carrying FCC is **a correct
   decision**, confirmed on a physical manual and consistent across two SKUs.
   **Still open: HTE162 欧英规 with no DoC.** **Newly open: the ANATEL
   back-cover statement cannot be produced at all** (§6.3.3) — a legal
   requirement with no carrier, which outranks the DoC question.
2. **FCC form**: pipeline standalone page vs the corpus's untitled parasitic
   block. B8 builds both carriers and waits.
3. **Two filing defects** (§7.1 of the audit): HTE153 墨西哥规 sharing the US
   file — intentional reuse or mis-binding? HTE152 日规 mis-filed as HTE154?
   Both need a live-Base check before anything is written.
4. **9 repository targets with no reference skeleton** (was 12; `JE-1000F_AU`,
   `JE-1000F_KR` and `JE-1000F_pt-BR` are now closed by the HTE153 intake) —
   supply corpus, or mark them explicitly as new lines?
5. **HTE140 日规's three variants** and the two already-printed QC defects on
   the SG file (an `F6` rendered as a tofu box, one residual red editing mark)
   — reprint or accept? **Two more printed defects joined this queue**: the
   LCD-display TOC entry reads folio 05 where the body prints 04, in both the
   EU V2.0 master and the AU manual that inherited it. Note the
   `toc_order ⊑ layout_order` gate checks *order*, not *page numbers*, so it
   cannot catch this — the gate needs a second column comparing the TOC's
   printed folio against the actual one.
6. **Reconstruction threshold X%** — measured **79.3%** pure deletion /
   **94.8%** with one overlay. Acceptable?
7. **`document_key` grain**: adding a model-without-region form is a Feishu
   schema change (approve, defer, or keep R&D-time skeletons repo-side only).
8. **Where the skeleton registry is mastered**: repo with a Feishu mirror, or
   Feishu-first like the capability matrix?

## 9. Non-goals

No per-product template directory clones, no per-model configs, no one-step
rewrite of the manifest YAML surface. No prose-content migration (Workstream N
owns it). No second rendering stack. No relaxation of live-table write gates.

## 10. Revision log

- 2026-08-20: initial draft from the six-perspective repo assessment.
- 2026-08-20 (Phase B intake round 2): three HTE153 manuals (AU/KR/BR) and the
  corrected HTE152 JP manual folded in. `MAIN@INTL` 25 → 28; corpus reconstruction
  79.3% / 94.8%. **The 2-D key's structure passed both factorials; its axis
  ownership did not** — compliance carrier, language set, legal entity and unit
  system moved out of `house_style` into a new `region_profile` overlay key
  space, `topic existence` narrowed to `topic universe + capability slots`, and
  same-page constraints split into semantic (family-owned) vs typographic slack
  (non-contractual). The §4.2 decision rule is now explicitly topic-granularity
  only. D2's stated rationale corrected (CN shares lineage with INTL on 12 of
  15 topics; the decision stands on a house-style signature instead).
  Compliance open questions 3 → 1, plus a new one: the ANATEL statement has no
  carrier and cannot be produced. Workflow artifacts: `wf_bdeee803-3c6`,
  `wf_64a76562-1f6`.
- 2026-08-20 (Phase B): rewritten against corpus evidence. Anchor key became
  2-D sparse `(skeleton_family × house_style)`; A5 dissolved into
  `house_style_version`; measurement caliber settled as printed-page layout
  order; `body_lineage`, `order_profile`, page-grid slots and `presentation`
  added; overlay semantics layered over JSON-Pointer; shared-plane directory
  re-layering rejected in favour of a mapping file; retrofit phases B0–B9 with
  B0 as an absolute prerequisite. **Four v1 claims corrected** — see §3, in
  particular the withdrawal of diff line count as a skeleton-distance signal.
  Workflow artifact: `wf_23177ec3-b4c` (7 agents, 1.25M tokens, 388 tool calls).
