# Approved-PDF InDesign Replica Plan

Status: in progress

Target: `JE-1000F / US / en+fr+es`

Branch: `feat/idml-reference-replica`

Updated: 2026-07-16

## 1. Objective

Produce an InDesign handoff that reproduces the approved 58-page manual while
remaining structurally editable:

- text, tables, headings, callouts, and page components stay native InDesign
  objects;
- illustrations are governed linked PDF/AI-derived assets;
- the approved PDF fixes pagination and visual acceptance;
- the final visible document must not be a stack of placed full-page reference
  PDF pages;
- the deliverable set includes IDML, INDD, InDesign-exported PDF, preflight,
  source/asset trace, and a reference-parity report.

The frozen visual reference is:

- file: `Jackery Explorer 1000 User Manual V2.0-2026-06-05.pdf`
- SHA-256: `e72b1ba01882062e261b17d5ba54a2f7c3099e5ba531a6428be13888641083f2`
- 58 pages, 368.787 x 524.692 pt

The source-art master remains immutable:

- file: `16-0102-000404 说明书 HTE1531000A-US-JAK RoHS REACH.ai`
- SHA-256: `ee1fd9367021c99b3a16e14dc8aa702929c71ac4c98c7132816da05d90ce06ed`
- 59 PDF-compatible pages; page 1 is the engineering overview

## 2. Discovery report

### 2.1 Reproduced user-facing baseline

The real entrypoint was run from a clean branch worktree:

```bash
python3 build.py idml \
  --config configs/config.us.yaml \
  --model JE-1000F \
  --region US \
  --source review-asis \
  --idml-mode production \
  --data-root /Users/pika/Documents/auto-manual2/data/phase2
```

The build produced a 60-page LaTeX PDF and a 52-page production IDML from the
same 52-page IR. The structural IDML checker reported success even though a
real InDesign 2026 open/export found:

- 52 pages instead of the approved 58;
- three overset stories, one per language;
- zero missing fonts;
- zero bad links;
- page-size delta of 0.001 pt from the approved PDF.

The three overset stories are exactly the English, French, and Spanish long
operation-to-troubleshooting flows. Each currently has six linked frames.

### 2.2 Pagination disconnect

`tools/idml/latex_page_plan.py` builds and validates a reference page plan, but
the production exporter currently bypasses it:

- `tools/export_idml.py` constructs `page_plan` and emits it as a sidecar;
- `ReferenceStoryEmitter` receives no plan;
- `ProseFlowBuffer.flush()` is called with `None`;
- `planned_story_pages()` is therefore dead in the production path;
- the final structural check does not compare package page count with an
  effective approved plan.

The generated LaTeX plan asks for 60 pages. Reconnecting it is a useful
regression safety net, but it is not the approved output and must not become
the final target.

### 2.3 Approved 58-page structure

The approved PDF has a deterministic structure:

```text
front matter: 3 pages
English:     18 pages (4-21)
French:      18 pages (22-39)
Spanish:     18 pages (40-57)
back cover:   1 page  (58)
```

Within each language, fixed/composed pages and post-prose pages already occupy
the correct ten pages. The long prose region must occupy eight pages instead
of the current six:

| Language | Operation | UPS + charging | Methods | Storage + trouble | Spec |
| --- | ---: | ---: | ---: | ---: | ---: |
| EN | 10 | 14 | 15 | 17 | 18 |
| FR | 28 | 32 | 33 | 35 | 36 |
| ES | 46 | 50 | 51 | 53 | 54 |

This is `4 + 1 + 2 + 1 = 8` prose pages per language, yielding exactly 58
physical pages and two additional frames for each currently overset story.

The generic fuzzy PDF mapper is not safe for this approval decision. Against
the approved PDF it matches only 33 of 52 IR source pages (63.46%), below the
existing 65% gate, and can mis-anchor English specifications to French page 36.
The approved layout therefore needs an explicit, reviewed plan bound to the
reference PDF digest and the exact manual IR identity.

### 2.4 Asset state

The AI intake and Base archive already provide immutable source provenance,
page previews, semantic exports, and a build snapshot. They do not yet prove
that every visible illustration is the approved V2.0 product artwork.

Known release blockers include:

- operation LED artwork with the wrong product and Japanese burned-in text;
- energy-saving, LCD mode, UPS, and some charging artwork using an older unit;
- App screens with Japanese UI or the wrong product;
- product-overview fidelity currently achieved mainly by a placed full page;
- the back cover still quarantined pending QR/legal/contact verification;
- a temporary warning lockup.

These are asset-governance blockers, not reasons to flatten text or tables.

## 3. Invariants and non-goals

1. The approved plan must match model, region, language scope, manual content
   SHA, style-contract SHA, reference PDF SHA, page count, and page geometry.
2. A stale or ambiguous approved plan fails loudly; it never silently falls
   back after partial use.
3. Without a matching approved plan, existing targets keep the measured LaTeX
   plan behavior.
4. Full-page reference placement may be used as a non-printing comparison
   layer, but not as final visible content.
5. Governed content stays in templates/phase2; governed artwork stays in the
   asset registry/snapshot; InDesign is not a second source of truth.
6. No new `build.py` public CLI flag, phase2 schema, dependency, or GitHub
   workflow is introduced by this work.
7. The source AI and approved PDF are never overwritten.
8. The current LaTeX renderer is not redesigned as part of this task.

## 4. Implementation phases

### Phase 0 - Contract and characterization

Files:

- this plan;
- targeted regression tests and baseline reports under `tmp/pdfs/` only.

Safety net:

- preserve the reproduced 52-page/three-overset evidence;
- pin both supplied file hashes and PDF geometry;
- do not stage generated `docs/_build/**` output.

### Phase 1 - Restore measured-plan wiring

Files:

- `tools/export_idml.py`;
- `tools/idml/reference_story_flow.py`;
- `tools/idml/prose_flow.py`;
- `tools/idml/latex_page_plan.py` and `tools/idml/ir_projection.py` only where
  validation needs strengthening;
- `tests/test_export_idml.py`;
- `tests/test_export_idml_cli.py`;
- `tests/test_latex_page_plan.py`;
- a focused emitter test module if the existing files become unclear.

Deliverables:

- page-plan grouping and planned story spans drive production frames again;
- the existing 60-page LaTeX plan produces 60 IDML pages;
- production export fails if effective plan page count and IDML page count
  disagree;
- real InDesign opens/exports with zero overset stories.

This phase proves the wiring only; its 60-page artifact is not deliverable.

### Phase 2 - Approved, hash-bound 58-page plan

Files:

- a versioned approved-plan JSON under a renderer-neutral data directory;
- a small focused loader/validator in `tools/idml/`;
- `tools/idml/ir_projection.py` and exporter integration;
- plan contract and integration tests.

Deliverables:

- deterministic target lookup without a model-specific CLI default;
- exact approved source-page anchors for all 52 IR pages;
- hard gates for IR/style/reference identity, monotonic anchors, page bounds,
  geometry, coverage, and final package page count;
- 58-page IDML, zero overset, zero missing fonts, zero bad links.

### Phase 3 - Governed asset closure

Files:

- `data/asset_recipes/` and asset registry snapshot inputs as needed;
- shared templates/recipes that migrate remaining raw paths to `asset:`;
- IDML asset resolution/link packaging;
- asset usage and release-trace tests.

Deliverables:

- every printed illustration resolves to an approved semantic export with a
  verified content hash;
- V2.0 product artwork replaces known old-model/Japanese-UI assets;
- product overview is native text/components plus linked art, not a visible
  full-page placement;
- QR/legal/back-cover scope is explicitly verified before quarantine removal;
- release fails on missing, quarantined, stale, or modified used assets.

### Phase 4 - Visual convergence and real InDesign proof

Files:

- focused IDML component/layout modules and shared layout tokens;
- `tools/idml_pdf_parity.py` and its tests if acceptance gates need extension;
- InDesign finalizer/preflight scripts only where real-runtime evidence exposes
  a defect.

Deliverables:

- per-page rendered comparison against the frozen 58-page PDF;
- native-object inspection proving text/tables/components remain editable;
- no clipping, overlap, blank spill pages, wrong links, font substitution, or
  overset;
- explicit hard thresholds for structural and visual acceptance, with any
  intentional delta recorded rather than hidden.

### Phase 5 - Operator workflow and publish trace

Files:

- `README.md`;
- `code-as-doc/build_doc_guide.md`;
- `user-guide/hello_auto-doc.md`;
- `user-guide/quick_start_guide.md` if the happy path changes;
- release/handoff trace code and tests.

Deliverables:

- reproducible operator commands;
- final IDML/INDD/PDF/preflight/parity/source-asset trace bundle;
- owning documentation updated in the same change.

## 5. Verification ladder

Run from cheap to expensive after each applicable phase:

```bash
python3 -m ruff check build.py integrations tools tests scripts
python3 -m unittest <targeted IDML and page-plan modules>
python3 -m unittest
python3 -m mypy tools/utils
python3 tools/check_maintainability_guardrails.py
python3 tools/check_doc_link_integrity.py
python3 build.py check --config configs/config.us-en.yaml --model JE-1000F --region US \
  --data-root /Users/pika/Documents/auto-manual2/data/phase2
python3 build.py check --config configs/config.ja.yaml --model JE-1000F --region JP \
  --data-root /Users/pika/Documents/auto-manual2/data/phase2
python3 build.py idml --config configs/config.us.yaml --model JE-1000F --region US \
  --source review-asis --idml-mode production \
  --data-root /Users/pika/Documents/auto-manual2/data/phase2
python3 tools/indesign_finalize.py <approved output arguments>
python3 tools/idml_pdf_parity.py <approved PDF and InDesign PDF arguments>
```

Final acceptance is all of the following, on the latest artifact:

- 58 pages at approved geometry;
- zero overset stories, missing fonts, and bad links;
- zero unresolved or quarantined assets actually used;
- exact approved-plan and reference-PDF digests in the handoff trace;
- page-by-page visual inspection complete;
- no visible whole-page reference-PDF shortcut;
- relevant local checks and PR CI green.

## 6. Follow-up ledger

- Do not treat the existing 60-page LaTeX output as the approved visual master.
- Do not loosen the fuzzy mapper's match-rate gate to make the 58-page PDF pass.
- Do not release the back cover until its QR destination and regional legal
  copy are confirmed.
- Any source-content mismatch discovered during visual convergence routes back
  to the review/template/phase2 workflow instead of being typed into InDesign.
