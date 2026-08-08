# Style Component Contract v2 — discovery, PR plan, and completion ledger

Date: 2026-08-07

Status: PR 0 complete; PR 1 in progress

Owner: renderer contract maintainers
Canonical style definition: [`STYLE_DEFINITION.md`](../../docs/renderers/contracts/STYLE_DEFINITION.md)

## 1. Outcome

Complete the remaining cross-renderer style debt without turning Web, LaTeX,
IDML, and Word into one renderer. The final architecture shares component
semantics, slots, asset roles, page roles, and theme-token roles, while every
renderer keeps its own output adapter and geometry.

The work is intentionally split into serial PRs. Each implementation PR starts
from the previous PR's merged `main`; no stacked implementation branches are
allowed because the style contract, reference-layout pin, and adapter registry
are common hot spots.

The target flow is:

```text
RST / source tables / templates
              |
              v
          Manual IR
              |
              v
        ComponentSpec
  component_id / variant / slots
  asset roles / token roles / source_ref
      |          |          |          |
      v          v          v          v
  Web adapter  LaTeX     IDML       Word
               adapter   adapter     adapter

Web composite manifest --------> approved asset roles in ComponentSpec
Reference layout / PagePlan ---> fixed-page adapters only
```

## 2. Discovery baseline

This section is the pre-implementation discovery report required by the
repository's phased-execution policy. Every implementation PR must re-check the
facts it depends on against its fresh `origin/main`; these counts are not a
substitute for that re-check.

### 2.1 Existing contracts that must be preserved

- `manual_style.yaml` schema v1 has 31 stable `HB-*` semantics.
- 22 semantics are `aligned`; 9 are formally `partial`.
- 10 entries contain `debt`, but `HB-TABLE-LCD-ICON` is an approved,
  model-specific reference-layout variant rather than an unresolved defect.
- [`STYLE_DEFINITION.md`](../../docs/renderers/contracts/STYLE_DEFINITION.md) is
  the only human-readable normative style specification.
- `web-composite-manifest/v1` already freezes asset provenance, locale,
  definition/export record IDs, source-fragment hash, and content hash. The
  committed JE-1000F/US fixture contains 25 physical assets: eight localized
  logical groups times three languages, plus one shared asset.
- Read the Docs consumes the frozen local snapshot and must not contact Feishu
  during a build.
- The approved JE-1000F/US reference-layout contract pins content, assembly,
  style, and provenance separately. Style-only work must not alter source
  order, language mapping, physical composition, reference PDF, or
  `skipped_raw` acceptance.

### 2.2 Formal partial semantics

| Group | Semantics | Current gap |
|---|---|---|
| Type | `HB-TYPE-LEAD`, `HB-TYPE-FOOTER`, `HB-TYPE-PAGE-NUMBER` | IDML borrows styles or lacks dedicated shared tokens |
| Special components | `HB-SPECIAL-FCC`, `HB-SPECIAL-INBOX`, `HB-SPECIAL-OVERVIEW` | Renderer-local composition and target geometry are not represented as shared component instances |
| Page roles | `HB-PAGE-STANDARD`, `HB-PAGE-NO-FOOTER`, `HB-PAGE-COVER` | Page-template choice is not represented by one renderer-neutral PagePlan |

### 2.3 Structural debt behind the status count

1. [`HTML_PDF_Component_Convergence.md`](../architecture/HTML_PDF_Component_Convergence.md)
   still overlaps the canonical style definition and uses an older HTML/PDF/
   Word-only vocabulary that omits IDML.
2. `manual_style.yaml` validates LaTeX, IDML, and layout-token references, but
   Web and Word bindings are prose plus direct tests rather than schema fields.
3. `status` and `debt` currently mix three different concepts: unresolved
   conformance debt, platform constraints, and approved variants.
4. Manual IR exists, but no renderer-neutral `ComponentSpec` exists. IDML
   consumes IR semantics while Web reconstructs components after HTML
   generation from source patterns and document shape.
5. `web_manual.json` mixes presentation profile, reusable component contract,
   and JE-1000F/US target geometry. It currently contains 43 source-pattern
   entries and its figure upgrade is registered for only JE-1000F/US.
6. Web has CSS custom properties, but the four renderers do not share an
   explicit `theme_id` and semantic token-role projection.
7. The plain-Markdown intermediate has three known limitations: escaped pipes
   are not parsed, troubleshooting headers are read but not registered as an
   option, and `:class:` is accepted without changing output.

### 2.4 Hot spots and safety-net surfaces

At discovery time the main hot spots are:

- `tools/web_presentation.py`: 2,129 lines;
- `docs/renderers/contracts/web_manual.json`: 420 lines;
- assembled Web CSS source modules: about 1,900 lines in the primary module,
  plus specialized modules;
- `tools/word_bundle_docx_styles.py`: 1,044 lines;
- `tools/render_contract.py` and `tests/test_render_contract.py`: the current
  schema and parity gate;
- `tools/manual_ir/`: deterministic shared input to fixed-page rendering;
- `tools/idml/latex_page_plan.py` and reference-layout helpers: current
  fixed-page planning surface.

These are ratchets, not invitations to make the files larger. New component
code belongs in bounded modules with registry-parity tests and compatibility
facades where necessary.

## 3. Decisions and non-goals

### 3.1 Stable decisions

1. Share semantics, slots, asset roles, token roles, and page roles; do not
   share IDML XML, LaTeX source, DOCX XML, or CSS coordinates.
2. Fixed-page absolute positioning is not debt when it is target-scoped,
   parameterized, registered, and regression-tested.
3. Web remains responsive. It converges on information hierarchy and visual
   language, not PDF pagination.
4. A placed finished-art front cover is an approved platform constraint, not a
   fake editable component.
5. The LCD model-specific row-height note moves from `debt` to an approved
   variant; the renderer behavior does not change.
6. `web-composite-manifest/v1` remains the approved asset input. ComponentSpec
   consumes it; this program does not replace or redesign the asset pipeline.
7. Style/layout contracts stay versioned in Git. They are not moved into
   Feishu.
8. Long-form prose remains deliberately hybrid. This program does not
   structuralize every paragraph or revive the rolled-back bespoke page
   assembly pilot.
9. Unknown arbitrary CSS classes are not part of the authoring contract. The
   plain-Markdown lane will use typed/allowlisted variants.

### 3.2 Explicit non-goals

- no pixel-perfect Web/PDF pagination parity;
- no change to the approved reference PDF as part of a pure refactor;
- no automatic golden update when a comparison differs;
- no IDML consumption of Web raster composites;
- no ordinary RST image migration into `04_资产导出物`;
- no live Feishu dependency in Read the Docs;
- no public CLI flag removal in this workstream;
- no cleanup of `docs/_build`, `reports/version_tracking`,
  `reports/releases`, or user-owned generated artifacts;
- no unrelated content, queue, publish, or Base-schema work in these PRs.

## 4. Execution and checklist protocol

### 4.1 Serial branch rule

For PR 1 onward:

1. wait until the previous PR is merged;
2. fetch `origin` and verify a clean tree;
3. create the listed branch from current `origin/main` with
   `scripts/start_branch.sh`;
4. run the phase's characterization checks before production edits;
5. implement only that PR's listed scope;
6. run the cheap-to-expensive verification ladder;
7. update this ledger in the same PR;
8. open a ready PR only when every local required check is green;
9. merge only under the repository's authorization protocol;
10. after merge, record the merge commit and `main` verification in the next
    PR's first ledger update.

No two PRs in this workstream may edit the contract concurrently.

### 4.2 Meaning of the checkboxes

- **Submitted** is checked only after the implementation commit is pushed and
  the PR exists.
- **Complete** is checked only after the PR is merged and its required
  post-merge checks pass on `main`.
- A PR can therefore be submitted but not complete.
- A checkbox update must include the PR URL, branch, implementation commit,
  merged commit when available, and a short evidence link or command summary.
- If a PR is superseded or rolled back, leave it unchecked and record the
  disposition in the Notes column. Do not delete history from the ledger.

### 4.3 Master completion ledger

| Step | Submitted | Complete | Branch | Commit | PR | Merged commit | Required evidence | Notes |
|---|---|---|---|---|---|---|---|---|
| PR 0 — baseline definition and this plan | [x] | [x] | `feat/tools-plain-markdown-site` | `d1fff5c3` (final head `79263495`) | [#874](https://github.com/Bingboom/auto-manual/pull/874) | `ce41d77e` | PR 17/17 green: Actions `31247992063` + `31247992042`; merged-main validation `31248164455`; local links, contract tests, pins green | Submitted and merged 2026-08-08; post-merge main verified before PR 1 edits |
| PR 1 — document convergence and debt vocabulary | [ ] | [ ] | `docs/style-contract-v2-vocabulary` | — | — | — | docs links, contract tests, zero output change | Started from `ce41d77e`; pre-edit characterization green |
| PR 2 — style schema v2 and four-renderer bindings | [ ] | [ ] | `feat/style-contract-schema-v2` | — | — | — | schema tests, full unit, style-only pin rebind proof | — |
| PR 3 — ComponentSpec core and Callout pilot | [ ] | [ ] | `refactor/renderers-component-spec-callout` | — | — | — | adapter parity, Web/LaTeX/IDML/Word callout comparison | — |
| PR 4 — Spec Table and theme-token projection | [ ] | [ ] | `refactor/renderers-component-spec-table` | — | — | — | token projection, four-renderer spec-table comparison | — |
| PR 5 — shared PagePlan and page/type partials | [ ] | [ ] | `refactor/renderers-shared-page-plan` | — | — | — | 52-source/58-physical parity, folio/type checks | — |
| PR 6 — FCC ComponentSpec | [ ] | [ ] | `refactor/renderers-fcc-component` | — | — | — | three-language PDF/IDML/Web/Word checks | — |
| PR 7 — Inbox ComponentSpec | [ ] | [ ] | `refactor/renderers-inbox-component` | — | — | — | three-card desktop/mobile and fixed-page parity | — |
| PR 8 — Overview ComponentSpec and target geometry | [ ] | [ ] | `refactor/renderers-overview-component` | — | — | — | three-language composite/live fallback, mobile completeness | — |
| PR 9 — compatibility cleanup and final acceptance | [ ] | [ ] | `refactor/renderers-style-contract-v2-closeout` | — | — | — | all strict gates, real builds, golden comparison, RTD build | — |

## 5. PR 0 — baseline definition and executable plan

### Purpose

Finish the human documentation baseline before any contract migration. PR #874
already makes `STYLE_DEFINITION.md` the sole human style specification; this
final slice adds the discovery report, serial PR plan, and durable checklist.

### In scope

- this document;
- one roadmap pointer in `code-as-doc/optimization_project.md`;
- one navigation pointer in `code-as-doc/README.md`;
- the already-completed style-definition consolidation in PR #874.

### Out of scope

- schema or renderer code;
- `manual_style.yaml` semantic changes;
- reference-layout rebind;
- generated outputs.

### Required verification

```bash
python3 tools/check_doc_link_integrity.py
python3 -m unittest tests.test_render_contract
python3 tools/check_reference_layout_pins.py
```

PR #874's full existing validation must remain green after the documentation
commit. If the branch is synchronized with a newer `main`, rerun the full suite
instead of relying on the previous check run.

### Rollback point

Revert only the plan/navigation commit. The already-consolidated canonical
definition remains independent.

## 6. PR 1 — converge overlapping docs and define debt vocabulary

### Purpose

Eliminate the second human style specification and define precise language for
conformance, platform constraints, and approved variants before encoding the
taxonomy in schema v2.

### Dependencies

- PR 0 merged;
- fresh inventory of every link to
  `HTML_PDF_Component_Convergence.md`, `STYLE_DEFINITION.md`, and
  `manual_style.yaml`.

### Expected files

- `code-as-doc/architecture/HTML_PDF_Component_Convergence.md` — reduce to a
  short architecture-boundary pointer, or retain only principles not already
  owned by the canonical definition;
- `code-as-doc/architecture/README.md` — mark the ownership boundary;
- `docs/renderers/contracts/STYLE_DEFINITION.md` — define the three terms and
  their lifecycle;
- `code-as-doc/dev/style_debt_execution_status.md` — mark the older execution
  record as historical and point to this active ledger;
- this ledger.

### Required implementation

1. Record `debt` as a fixable conformance gap.
2. Record `constraint` as a renderer/platform limitation that the shared
   semantic contract intentionally accepts.
3. Record `approved_variant` as target/language/model geometry or behavior that
   is reviewed and regression-pinned.
4. State that neither a constraint nor an approved variant makes a semantic
   `partial` by itself.
5. Remove duplicated component lists and migration order from the older
   convergence document.

### Safety net and acceptance

- no production code or machine contract changes;
- no output bytes or reference pins change;
- `rg` shows one human style definition, with all other style docs linking to
  it;
- `python3 tools/check_doc_link_integrity.py` passes;
- `python3 -m unittest tests.test_render_contract` passes.

### Rollback point

One docs-only PR. Revert it without touching renderer output.

## 7. PR 2 — style contract schema v2 and four-renderer bindings

### Purpose

Make the cross-renderer contract machine-check all four projections and encode
the vocabulary from PR 1 without changing visual output.

### Dependencies

- PR 1 merged;
- captured v1 contract digest and current strict-issue set;
- characterization tests proving current LaTeX/IDML/Web/Word binding names.

### Expected files

- `docs/renderers/contracts/manual_style.yaml`;
- a bounded schema/helper module beside `tools/render_contract.py` if needed to
  keep the entry module below its maintainability ratchet;
- `tools/render_contract.py` as the public loader/validator facade;
- `tests/test_render_contract.py` and focused binding tests;
- `docs/renderers/contracts/STYLE_DEFINITION.md`;
- `docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json` for a
  style-identity-only rebind after proof;
- this ledger.

### Required schema

`manual_style.yaml` v2 must validate, per style:

- stable `HB-*` semantic ID and source kinds;
- `conformance.state` and actionable `conformance.debt`;
- separate `constraints` and `approved_variants` records with reason, owner,
  scope, and test/reference evidence;
- LaTeX owner and entrypoints;
- IDML renderer plus paragraph/object/table style binding;
- Web capability (`rendered`, `projection-only`, or `not-applicable`) and
  stable selectors/component adapter;
- Word capability and stable paragraph/table/component binding;
- referenced layout tokens and future theme-token roles;
- final-mile editability rules.

The `HB-TABLE-LCD-ICON` note moves to `approved_variants`. Web page roles,
footer, and page number are explicitly `not-applicable`, not debt.

### Compatibility and migration rules

- the public loader may read v1 during one compatibility window;
- newly committed contract data must be v2;
- strict mode reports only actionable debt, never constraints/approved
  variants;
- every binding key must be schema-validated and have a registry-parity test;
- contract hash changes are expected, but renderer output is not.

### Safety net and acceptance

1. targeted schema, malformed-binding, capability, and migration tests;
2. `python3 -m unittest tests.test_render_contract`;
3. full unit, Ruff, mypy where touched, guardrails, docs links;
4. pre/post Web HTML, LaTeX/PDF, IDML package, and Word structure comparison
   shows no unapproved difference;
5. reference rebind changes only `identity.style.style_contract_sha256` and
   approval metadata required for that style-only operation;
6. content, assembly, page mapping, reference PDF, and composition map remain
   identical;
7. `python3 tools/check_reference_layout_pins.py` passes.

### Rollback point

The v1 read path remains available. Revert contract data, schema helper, tests,
and style-only pin update together.

## 8. PR 3 — ComponentSpec infrastructure and Callout pilot

### Purpose

Introduce a renderer-neutral runtime component instance and prove it on
`HB-CALLOUT-STRIP`, the simplest high-value component already aligned in all
four outputs.

### Dependencies

- PR 2 merged;
- pre-migration callout fixtures for warning, danger, caution, note, and tip;
- list, inline emphasis, locale, and empty/invalid-slot characterization.

### Expected files

- a new bounded `tools/component_specs/` package with model, validation,
  registry, and adapter dispatch modules;
- `docs/renderers/contracts/component_registry.yaml` for component type,
  variants, required/optional slots, asset roles, style IDs, and adapter keys;
- Manual IR projection code and tests;
- `tools/manual_md_directives.py` for the Markdown source adapter;
- Web callout adapter module, LaTeX callout node adapter, IDML notice adapter,
  and Word callout adapter/facade;
- `tests/test_component_specs.py` plus focused renderer tests;
- `STYLE_DEFINITION.md` and this ledger.

### Required ComponentSpec v1 shape

```text
schema_version
component_id
variant
source_ref
language
slots[]: {role, content_kind, content}
assets[]: {role, asset_ref, locale_policy}
token_roles[]
metadata
```

Validation is fail-closed for unknown component IDs, variants, slots, asset
roles, and adapter keys. Registry parity asserts that every registered
component has the declared output adapter capabilities.

### Callout pilot behavior

- signal-word text remains source content; adapters do not translate it;
- warning, danger, caution, note, and tip retain one semantic component with
  explicit variants;
- lists and inline emphasis survive all four adapters;
- current RST tables and plain-Markdown directives remain compatible through
  source adapters; they no longer each hand-build unrelated final markup;
- renderer-specific markup and geometry remain inside adapters.

### Safety net and acceptance

- exact pre/post semantic and normalized output comparison for all variants;
- Pandoc protection/restoration still preserves component identity;
- Web desktop/mobile, real LaTeX/PDF, IDML import/preflight, and Word DOCX
  structure checks pass;
- no reference PDF/golden update on a pure migration;
- full validation ladder passes.

### Rollback point

Keep old public entrypoints as thin facades delegating to the new adapters.
Revert the pilot without affecting the ComponentSpec model only if the model is
independently green; otherwise revert the PR atomically.

## 9. PR 4 — Spec Table pilot and semantic theme-token projection

### Purpose

Prove that ComponentSpec supports structured rows, row spans, references, and
semantic visual roles by migrating `HB-TABLE-SPEC`. Introduce a versioned theme
projection without forcing identical units or coordinates across renderers.

### Dependencies

- PR 3 merged;
- fixtures covering multiline values, blank-label rowspan, circled-reference
  superscripts, four sections, and narrow/mobile overflow;
- frozen normalized outputs for all four renderers.

### Expected files

- `docs/renderers/contracts/component_registry.yaml`;
- `docs/renderers/contracts/manual_theme.yaml` with a stable `theme_id`;
- theme validator/loader kept separate from `manual_style.yaml`;
- ComponentSpec table source and output adapters;
- `tools/csv_pages/renderers_spec.py`, `tools/manual_md_directives.py`,
  Web spec-table module, `docs/renderers/latex/components_spec.tex`,
  `tools/idml/spec_tables.py`, and Word table adapter/facade as needed;
- focused component/theme tests, `STYLE_DEFINITION.md`, and this ledger.

### Required theme contract

The theme file owns semantic roles such as brand surface, muted surface,
strong border, panel radius, label typography, value typography, and component
spacing. Each role maps to renderer-specific bindings: CSS custom property,
LaTeX/layout token, IDML style/token, and Word style/property adapter. It does
not store page-instance coordinates.

### Safety net and acceptance

- every theme role has at least one consumer and no orphan binding;
- existing layout tokens remain the unit-bearing source for PDF/IDML geometry;
- table section count, row order, row spans, superscripts, borders, label/value
  roles, and mobile scrolling match the frozen baseline;
- Web and title/table widths remain aligned at the content-container level;
- normalized four-renderer output comparison and full validation ladder pass;
- reference pin treatment follows PR 2: style-only and evidence-backed.

### Rollback point

The previous spec entrypoints remain facades. Theme projection and table pilot
revert together if any renderer cannot prove parity.

## 10. PR 5 — renderer-neutral PagePlan and page/type debt

### Purpose

Create one semantic page plan for fixed-page renderers and close six related
partials: lead, footer, page number, standard page, no-footer page, and cover.
Web records these page concerns as not applicable rather than emulating PDF
pagination.

### Dependencies

- PR 4 merged;
- approved JE-1000F/US content/assembly/reference baseline re-captured;
- characterization of cover, TOC, standard, footerless, language-transition,
  and back-cover pages.

### Expected files

- a bounded renderer-neutral PagePlan model/validator/serializer;
- `tools/idml/latex_page_plan.py` retained as a compatibility facade;
- reference-layout activation and page-role projection helpers;
- LaTeX page-template adapter, IDML page/master/folio modules, and Word page
  metadata adapter;
- dedicated IDML lead/footer/page-number style definitions and token bindings;
- `manual_style.yaml`, `STYLE_DEFINITION.md`, reference pin, tests, and this
  ledger.

### Required PagePlan semantics

- page role: standard, no-footer, front cover, back cover, TOC, or declared
  extension;
- source reference, language, ordinal, physical span, footer policy, folio
  policy, and renderer capability;
- placed front-cover art recorded as an approved constraint;
- back-cover shared copy remains editable and source-driven;
- Web ignores physical spans through an explicit adapter capability.

### Safety net and acceptance

- old public page-plan calls remain compatible;
- approved target preserves 52 source pages, 58 physical pages, source order,
  language mapping, composition map, and reference PDF;
- no-footer and folio suppression are driven by page role, not localized text;
- lead/footer/page-number use dedicated token/style bindings;
- real US production IDML, PDF, Word, and Web builds pass;
- all six semantics become aligned, with only legitimate constraints/variants
  retained;
- full validation and reference-pin gates pass.

### Rollback point

The compatibility facade can restore the old LaTeX-derived planning path. Do
not delete it until PR 9.

## 11. PR 6 — FCC ComponentSpec

### Purpose

Represent FCC as a shared semantic composition while preserving independent
responsive and fixed-page layouts. Close `HB-SPECIAL-FCC` without rasterizing
editable text or adding a black section-title bar that the approved design does
not have.

### Dependencies

- PR 5 merged;
- EN/FR/ES FCC source and output fixtures;
- frozen paragraph/list order and right-column split markers.

### Expected files

- FCC entry in `component_registry.yaml` and source-to-spec projector;
- Web FCC adapter and CSS module;
- LaTeX `HBFccBlock` adapter;
- `tools/idml/components/fcc.py`, `tools/idml/fcc_fallback.py`, and page
  composer integration;
- Word FCC adapter/facade;
- contract, tests, docs, and this ledger.

### Required component slots

- compliance mark asset;
- opening copy;
- ordered body blocks/lists;
- logical column-break role;
- language and accessibility label.

Column geometry is renderer-specific. Existing absolute IDML placement is
allowed as a registered fixed-page adapter constraint.

### Safety net and acceptance

- EN/FR/ES text stays editable and in source order;
- Web has only the approved FCC frame, no synthetic black H1 band;
- FCC frame, other tables, and content title bands use the same container
  width contract;
- desktop and mobile Web rhythm is stable;
- LaTeX/PDF, IDML, and Word preserve the approved two-column intent;
- `HB-SPECIAL-FCC` becomes aligned and full validation passes.

### Rollback point

Retain the previous FCC parser/composer as a tested facade until PR 9.

## 12. PR 7 — Inbox ComponentSpec

### Purpose

Represent “What's in the Box” as editable labels plus image assets in three
equal semantic cards and one tip strip. Close `HB-SPECIAL-INBOX` without
turning the whole block into a raster composite.

### Dependencies

- PR 6 merged;
- EN/FR/ES fixtures and mobile/desktop snapshots;
- characterization of item numbering, image order, labels, and tip copy.

### Expected files

- Inbox registry definition and source projector;
- Web Inbox adapter/CSS;
- LaTeX `HBInBoxThree` adapter;
- `tools/idml/components/inbox.py` and page composer integration;
- Word Inbox adapter/facade;
- contract, tests, docs, and this ledger.

### Required component slots

- ordered cards, each with number, image asset role, accessible alt, and live
  localized label;
- tip label and tip body;
- layout variant for three-up fixed page and responsive stack.

### Safety net and acceptance

- exactly three ordered cards and one tip strip;
- desktop cards are equal width, edge-aligned, and evenly spaced;
- mobile preserves every image and localized label without horizontal loss;
- all text remains editable/searchable;
- four-renderer normalized comparison passes;
- `HB-SPECIAL-INBOX` becomes aligned and full validation passes.

### Rollback point

Keep the previous page-shape transformer as a thin compatibility adapter until
PR 9.

## 13. PR 8 — Overview ComponentSpec and target-scoped geometry

### Purpose

Separate reusable product-overview semantics from JE-1000F/US instance
geometry and connect approved Web composites through asset roles. Close
`HB-SPECIAL-OVERVIEW` while keeping live HTML fallback and mobile-complete
approved images.

### Dependencies

- PR 7 merged;
- approved 25-file composite manifest unchanged;
- EN/FR/ES front/right view fixtures, source-fragment hashes, callout IDs, and
  mobile screenshots;
- characterization of live annotated and approved-composite variants.

### Expected files

- Overview registry definition and source projector;
- a target-scoped, versioned component-instance contract for JE-1000F/US
  geometry and source bindings;
- generic presentation profile separated from target instance data currently
  mixed in `web_manual.json`;
- Web live/composite adapters and asset-manifest bridge;
- IDML overview adapter and token/instance resolver;
- LaTeX/Word projection where supported;
- contract tests, Web composite tests, docs, and this ledger.

### Required component slots and variants

- views with stable IDs;
- base image role;
- ordered callout label/body slots;
- leader/decorative-line roles;
- geometry reference scoped to target/view, never localized prose;
- `annotated-live` and `approved-composite` variants;
- composite selection by `web_replace_key` plus locale/shared policy.

### Safety net and acceptance

- no static Base token or live URL enters the contract;
- exact locale wins and `shared` remains the only fallback;
- zero manifest match preserves live semantic HTML;
- duplicate/hash mismatch remains fail-closed;
- front/right images are complete on mobile and labels do not fall offscreen;
- EN/FR/ES source-fragment and asset hashes still match;
- IDML absolute geometry is target-scoped, parameterized, registered, and
  tested rather than removed;
- `HB-SPECIAL-OVERVIEW` becomes aligned and full validation passes.

### Rollback point

The previous target block remains readable for one compatibility window; a
rollback restores it together with the adapter bridge, never the asset bytes.

## 14. PR 9 — compatibility cleanup, Markdown closure, and final acceptance

### Purpose

Remove only compatibility paths proven unused after PRs 3–8, close the three
plain-Markdown limitations, enforce zero actionable style debt, and publish the
final evidence record.

### Dependencies

- PRs 1–8 merged and post-merge verified;
- repository-wide search for old adapter/fallback imports;
- full current `main` baseline captured before deletion.

### Expected files

- compatibility facades and old helper paths identified by import/coverage
  evidence;
- `tools/manual_md_directives.py` and focused tests/docs;
- component/style/theme/page-plan strict validators;
- `manual_style.yaml`, `STYLE_DEFINITION.md`, this ledger, and
  `code-as-doc/code_optimization_log.md`;
- maintainer/user docs only where supported authoring behavior changed.

### Plain-Markdown closure

1. Parse escaped `\|` deterministically without breaking existing row-span
   syntax.
2. Register and validate a typed troubleshooting-header option.
3. Replace inert arbitrary `:class:` behavior with allowlisted component
   variants. Preserve a warning compatibility alias only if repository search
   finds real authored use; unknown values fail closed.

### Compatibility deletion rule

A path can be deleted only when:

- repository import/search proves no production caller remains;
- adapter registry parity covers the replacement;
- focused before/after tests pass;
- normalized golden output is unchanged unless the PR explicitly documents a
  reviewed behavior fix;
- the deletion does not remove a public CLI flag or review-branch compatibility
  route.

### Final acceptance ladder

Run in this order and record exact output in the PR:

```bash
python3 -m ruff check build.py integrations tools tests scripts
python3 -m unittest <all focused component/style/page-plan modules>
python3 -m unittest
python3 -m mypy tools/utils
python3 tools/check_maintainability_guardrails.py
python3 tools/check_doc_link_integrity.py
python3 tools/check_reference_layout_pins.py
python3 build.py check --config configs/config.us-en.yaml --model JE-1000F --region US
python3 build.py idml --config configs/config.us.yaml --model JE-1000F --region US --source auto --idml-mode both --no-clean
```

Also required:

- real Web Sphinx/Read the Docs-equivalent build from the frozen fixture;
- desktop and narrow-mobile review of Callout, Spec, FCC, Inbox, and Overview;
- Word DOCX structural/render check;
- PDF/IDML normalized golden comparison;
- strict contract result: 31 registered semantics, zero actionable debt, and
  only explicitly owned/tested constraints or approved variants;
- a post-merge Read the Docs build from the matching `main` commit and live URL
  verification when Web output changed.

### Completion record

After the PR merges:

- mark every row in §4.3 complete;
- add a maintenance record to `code-as-doc/code_optimization_log.md`;
- update the roadmap workstream to `done`;
- keep this file as the audit trail, not as a second style definition.

### Rollback point

Compatibility deletion and Markdown behavior changes should be separate
commits inside the PR so either can be reverted without rolling back the
already-proven ComponentSpec contracts.

## 15. Per-PR pull request checklist

Copy this block into each PR body and keep the source ledger in §4.3 updated:

- [ ] Previous workstream PR is merged; branch starts from current
      `origin/main`.
- [ ] Discovery facts used by this PR were re-verified.
- [ ] Characterization tests were added/run before behavior changes.
- [ ] Scope matches exactly one numbered PR in this plan.
- [ ] No generated/review/release artifacts are staged.
- [ ] Public entrypoints are preserved or explicitly approved.
- [ ] Registry producer/consumer parity is tested.
- [ ] Cheap-to-expensive validation ladder is green.
- [ ] Pure refactor did not update a golden baseline.
- [ ] Any style pin change is style-only; content/assembly/reference identity
      is proven unchanged.
- [ ] `STYLE_DEFINITION.md` remains the only human style specification.
- [ ] This ledger records submitted/complete state and evidence.

## 16. Stop conditions

Stop the active PR and report instead of widening scope when:

- the required change becomes roughly three times larger than this phase;
- a current branch/worktree contains changes from another window;
- content or assembly identity changes during a style-only PR;
- a golden/reference comparison differs during a pure migration;
- the approved asset manifest or source-fragment hash drifts unexpectedly;
- a public CLI change, dependency bump, workflow edit, Base schema change, or
  generated/review artifact deletion becomes necessary;
- a renderer cannot preserve the semantic content with the planned adapter.

The operator then decides whether to split a new PR, approve an expanded scope,
or roll back the phase.
