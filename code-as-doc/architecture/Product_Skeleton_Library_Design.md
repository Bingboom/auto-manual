# Product Skeleton Library Design

Status: draft — pending workstream approval · Owner: 夏冰 · Created: 2026-08-20

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
  beside it. If approved, it should merge into M's slot in the recommended
  order — after the Workstream T Tier-1 items, never before them.
- It stays inside the allocation rule of
  [`Long_Form_Content_Block_Design.md`](Long_Form_Content_Block_Design.md):
  *"Layout, directives, page skeleton → repository RST template → always."*
  This design governs **composition** (which pages, in what order, under which
  applicability); prose content migration remains Workstream N's problem.
- It builds directly on the family-manifest diff carrier
  ([`family_manifest_diff.md`](family_manifest_diff.md),
  [`../../tools/manifest_family.py`](../../tools/manifest_family.py)).

Related documents: strategy boundaries in
[`System Evolution Strategy.md`](System%20Evolution%20Strategy.md); canonical
entity model in [`Content_Data_Model.md`](Content_Data_Model.md); review-branch
propagation in
[`Review_Branch_Propagation_Design.md`](Review_Branch_Propagation_Design.md);
program requirements, phase gates, and the corpus-audit plan in
[`product_skeleton_library_requirements.md`](product_skeleton_library_requirements.md).

## 2. Definitions

- **Skeleton**: the declared page composition of a manual line — page list,
  page order, per-page generation mechanism, per-page languages, applicability
  annotations. Today this object exists as a page manifest
  (`docs/manifests/manual_*.yaml`).
- **Skeleton anchor**: a base manifest that a family of manifests folds to.
  Today: the `anchors` entries of
  [`../../docs/manifests/family/index.yaml`](../../docs/manifests/family/index.yaml).
- **Module**: a reusable content unit referenced by a skeleton — a shared page
  template, a section-level snippet, a structured content block, a copy key.
- **Category** (品类): a product family whose chapter system differs
  structurally from another's (not merely by capability presence/absence).

## 3. Current State

### 3.1 What already exists

The skeleton concept is implemented but unnamed:

- Each of the 17 `docs/manifests/manual_*.yaml` files is a skeleton instance:
  an ordered `pages` list over five category-neutral page types
  (`cover_pdf`, `csv_page`, `generated_page`, `pdf_insert`, `rst_include` —
  the closed enum in [`../../tools/config_pages.py`](../../tools/config_pages.py)),
  with `capability`, `lang_blocks`, and `ordinal_neutral` annotations.
- [`../../docs/manifests/family/index.yaml`](../../docs/manifests/family/index.yaml)
  is already a skeleton lineage: 2 anchors (`manual_us-single-en`,
  `manual_eu-single-de`) plus 15 JSON-Pointer diff entries, guarded by a
  byte-exact fold test (`tests/test_manifest_family.py`). **Multi-anchor is a
  live mechanism, not a proposal.**
- Model-level variation inside a skeleton works by subtraction: page-level
  capability gates
  ([`../../tools/capability_pages.py`](../../tools/capability_pages.py) over
  [`../../data/model_capabilities.csv`](../../data/model_capabilities.csv)),
  section-level sentinel stripping, per-model language trims, and per-model
  data rows in phase2 tables.
- `build.py new-line`
  ([`../../tools/new_line_scaffold.py`](../../tools/new_line_scaffold.py))
  already scaffolds config + manifest clones; page contracts already support
  `allowed_models` (the JE-300E overview contract,
  [`../../docs/templates/contracts/03_product_overview_je300e.yaml`](../../docs/templates/contracts/03_product_overview_je300e.yaml),
  is a per-model skeleton-variation precedent).

### 3.2 The single-skeleton reality

Despite 17 manifest files, the library holds **one chapter skeleton**: 15 of 17
fold to `manual_us-single-en`, and the second anchor is its near sibling. All
of them express the power-station manual (preface → safety → box contents →
overview → operation → UPS → charging → storage → troubleshooting → spec).
Every existing variation mechanism shares one semantic: **superset skeleton +
boolean subtraction**. Page order is deliberately immovable (physicalized
`pNN_` names are pinned by review branches and the reference-layout contract).

### 3.3 The three real bottlenecks

The scaling limit the operator feels is not "only one manifest allowed". It is:

1. **The module layer does not exist yet.** Measured on `page_shared/en` +
   `page_us-en` (1032 template lines): ~92% is hardcoded prose; only ~70 lines
   carry `|PIPE|` placeholders and ~9 carry copy keys. The designed
   section-level reuse layer is an empty shell —
   [`../../docs/templates/snippets/registry.yaml`](../../docs/templates/snippets/registry.yaml)
   is literally `snippets: []` and every recipe's `snippet_slots` is `{}`.
   The only working reuse unit is the whole page, so a structural product
   difference forces whole-page forks multiplied by language count (JE-300E's
   overview page is forked five times across EU languages).
2. **Product category is not a dimension anywhere.** Template directories
   encode only (region, language);
   [`../../tools/lang_registry.py`](../../tools/lang_registry.py) maps each
   language to exactly one template directory;
   [`../../tools/target_defaults.py`](../../tools/target_defaults.py) literally
   defines family = region;
   [`../../tools/queue_config_resolution.py`](../../tools/queue_config_resolution.py)
   scores configs on (region, languages) only. `page_shared/` is the single
   shared prose plane — and 7 of its 14 English pages hardcode brand or
   power-station wording in body prose (10 of 14 mention the brand at all;
   the other 3 only in support URLs / the back-cover address), so a second
   category's shared prose has nowhere to live without colliding.
3. **The skeleton is implicit and parasitic on sibling live data.** Onboarding
   is clone-and-mutate, not instantiate-and-fill: the only reliable creation
   path for new targets is cloning a sibling's live Feishu rows; the intake
   completeness gate has no reference without a sibling; the field-mapping
   operators
   ([`../../tools/source_intake_rules.py`](../../tools/source_intake_rules.py))
   and the `Row_key`/`Slot_key` vocabularies are power-station-specific; the
   `document_key` grain is `Model_Region`, so a "model known, region undecided"
   R&D-time skeleton cannot be represented. Structure creation is bound to the
   region-compliance event (final spec sheet arrives), not the product-birth
   event.

## 4. Design Principles

1. **A skeleton is data; modules are shared.** A new product/category gets a
   new composition declaration (manifest anchor + registry rows), never a
   cloned template tree. This is strategy Principles 1 and 6 ("the enemy is
   template forks, not templates") and Workstream O's exit criterion (no
   per-model template clones). The 118 substantive divergences found by the
   language-asset governance sweep are the standing bill for copy-based reuse.
2. **Within a category: subtraction. Across categories: a new anchor.** The
   capability-gate path holds exactly while (i) chapter sets are subsets of a
   shared superset, (ii) chapter order is uniform, (iii) differences are
   boolean, (iv) shared passages are byte-identical when enabled. When a
   difference violates these, it belongs in a new anchor, not in more gates.
3. **Promotion has a quantitative signal.** The family diff carrier already
   measures skeleton distance. When a target's diff approaches the size of the
   anchor itself (the US→EU carrier is 600+ lines today), promote the target
   to a new anchor instead of growing the diff.
4. **Authoring direction flips in stages.** Today the diff carrier is
   verification-only (`manifest_family.py` never writes repository manifests;
   the 17 YAML files are the compatibility source of truth). Multi-skeleton at
   scale requires the fold to become generative — anchors + diffs as source,
   expanded YAML as build product — but the flip must keep the YAML surface
   byte-stable first, exactly like the original carrier migration.
5. **Skeletons are seeded at R&D time; values arrive later.** Structure first,
   `⚠️需确认` placeholder values second, diff-based revision as the spec sheet
   iterates. The KR line proved placeholder values pass `build.py check`; the
   missing piece is an entry point not gated on final-spec hard inputs.

## 5. Target Architecture

### 5.1 Skeleton registry (promote the anchor list)

`family/index.yaml` `anchors` becomes the **skeleton library index**: each
anchor carries a skeleton ID and category metadata. Category-internal lines
remain diff entries against their anchor. The fold test generalizes from
"17/2/15" constants to per-anchor family assertions.

### 5.2 Category as a first-class axis

- Config/queue routing gains a category axis: `target_defaults` and
  `queue_config_resolution` stop equating family with region.
- Shared prose is layered by category: `page_shared/<category>/<lang>/` (or an
  equivalent explicit mapping), with `lang_registry` template-directory
  resolution parameterized by category. Naming-convention consumers
  ([`../../tools/queue_asset_preflight.py`](../../tools/queue_asset_preflight.py),
  [`../../tools/check_review_branch_sync.py`](../../tools/check_review_branch_sync.py),
  `review_propagation_ledger`,
  [`../../tools/cloud_doc_backport_orchestration.py`](../../tools/cloud_doc_backport_orchestration.py))
  read the mapping instead of the `page_` prefix convention.
- Structure vocabularies become per-category assets: `Row_key`/`Slot_key`
  dictionaries, required-placeholder-row checklists, capability vocabularies,
  and intake field-mapping rule sets are instantiated per category rather than
  hardcoded to the power-station set.

### 5.3 The module layer gets built (prerequisite, not follow-up)

"Reusable parts are modules" is currently aspiration: activate the snippets /
section-module layer so that cross-category reuse (safety clauses, warranty
legal text, FCC, storage guidance) is expressed as module references, not
whole-page copies. This work must follow the Workstream H rollback lessons —
start from the most stable, least divergent prose, extend the proven
`csv_pages` pattern, and never pilot on the hardest page.

### 5.4 R&D-time seeding

- A skeleton can be instantiated at product birth: category anchor + capability
  matrix row + placeholder value slots, before region/compliance decisions.
- `document_key` gains a model-without-region form (a data-model change, so
  operator-approved and sequenced with
  [`Content_Data_Model.md`](Content_Data_Model.md) applicability
  normalization).
- The eight operator hard inputs (product display name, compliance symbol set,
  warranty/legal, …) become deferred-decision placeholders in the skeleton
  instead of "stop everything" gates; the existing intake approval gate keeps
  guarding live-table writes.

## 6. Known Blocking Assumptions (change inventory seed)

Concrete single-category assumptions confirmed in code, in the order a second
category would hit them:

| Site | Assumption |
| --- | --- |
| [`../../tools/target_defaults.py`](../../tools/target_defaults.py) | `_FAMILY_ORDER` = five regions; `family = default_region`; one best config per region |
| [`../../tools/queue_config_resolution.py`](../../tools/queue_config_resolution.py) | `config_match_score` has only (region, languages) axes; `config.us.yaml` name-based scoring |
| [`../../tools/build_docs_bundle.py`](../../tools/build_docs_bundle.py) | hard `doc_type == "manual_bundle"` gate |
| [`../../tools/lang_registry.py`](../../tools/lang_registry.py) | one template directory per language (`en → page_shared/en`) |
| [`../../tools/config_pages.py`](../../tools/config_pages.py) | closed page-type enum; `csv_page` page ids bound to the four phase2-backed renderers (`symbols`, `lcd_icons`, `troubleshooting`, `spec`) |
| [`../../data/capability_page_rules.csv`](../../data/capability_page_rules.csv) | `page_stem` values bound to power-station page names; per-capability ten-language regex maintenance |
| [`../../docs/manifests/family/index.yaml`](../../docs/manifests/family/index.yaml) + `tests/test_manifest_family.py` | anchors treated as compatibility artifacts; hardcoded 17/2/15 counts |
| `docs/templates/page_*` naming consumers (`queue_asset_preflight`, `check_review_branch_sync`, `review_propagation_ledger`, backport sibling resolution) | directory prefix encodes (region, language) only |
| [`../../tools/source_intake_rules.py`](../../tools/source_intake_rules.py) + intake completeness gate | power-station operator set; sibling row as the only structural reference |
| `document_key` (Feishu 文档构建表) | `Model_Region` grain only |

Phasing intent (each phase independently shippable, ordered by dependency):
**P0** name the registry (anchor metadata + generalized fold test, no behavior
change) → **P1** category axis in routing and shared-plane layering → **P2**
generative fold (authoring flip, YAML byte-stable) → **P3** module layer
activation (merged with M/N sequencing) → **P4** R&D-time seeding
(`document_key` grain, deferred-decision intake). P0–P1 are repo-only; P4
touches live-table schema and is operator-gated end to end.

## 7. Dependencies and Sequencing

- **Merges with Workstream M** (composition authority) — this design is M's
  target shape, extended with the category axis.
- **Requires Workstream Q first** (template-sync role; skeleton/template edits
  must ride the governed propagation path).
- **Co-requisite with Workstream V** (more skeletons ⇒ more review branches;
  V's pinned-derivative + bump-PR contract is what keeps propagation cost
  sub-linear). Workstream O remains deferred in the Stage-3 sequence; its V
  design gate was passed 2026-07-31, so the remaining dependency is V's
  implementation, not its approval.
- **Bounded by Workstream N's allocation rule** (skeletons stop at
  composition; prose bodies belong to the long-form block design).
- **Field-evidence gate before committing scope:** Workstream W's exit
  criterion ("next real product line live in ≤2 operator days") has not been
  field-tested. The next real product line should first run through the
  existing W machinery as-is; where it actually bleeds decides how much of
  P1–P4 is pulled forward.
- **Does not queue-jump** the Workstream T Tier-1 operational items (K4/K5/K7/K1).

## 8. Non-Goals

- No per-product template directory clones, no per-model configs (AGENTS.md
  §3), no rewrite of the manifest YAML surface in one step.
- No prose-content migration in this design (Workstream N owns it).
- No second rendering stack: new categories reuse the four renderers and the
  style component contract; a genuinely new structured page kind is a code
  registration by design, not an accident.
- No relaxation of live-table write gates for R&D-time seeding.

## 9. Open Questions (operator decisions)

1. Category taxonomy and naming: what is the first non-power-station category,
   and what is its skeleton called?
2. Shared-plane layout: `page_shared/<category>/<lang>/` directory layering vs
   an explicit mapping file (affects backport sibling resolution).
3. `document_key` grain change (model-without-region): schema change to the
   Feishu build base — approve, defer, or represent R&D-time skeletons
   repo-side only until the first region lands?
4. Where the skeleton registry is mastered: repo (`family/index.yaml`) with a
   Feishu mirror, or Feishu-first like the capability matrix?
5. Timing: hold P1+ until the next real product line has field-tested the
   Workstream W baseline, or start P0 (naming, no behavior) immediately?

## 10. Revision Log

- 2026-08-20: initial draft from the six-perspective repo assessment
  (manifest anatomy, template coupling, config/build coupling, strategy
  alignment, onboarding cost, capability-gate stretch).
