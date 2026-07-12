# LaTeX to InDesign Same-Source Handoff Plan

Status: implementation in progress

Branch: `feat/latex-indesign-same-source`

Updated: 2026-07-12

## 1. Objective

Make the production IDML an editable projection of the same reviewed content,
semantic components, layout tokens, assets, and page plan used by the LaTeX
reference PDF. InDesign owns final-mile layout adjustments after content
freeze; it does not become a second content source or a second independent
layout system.

## 2. Discovery Report

The repository already has useful foundations:

- both render paths start from a prepared RST bundle;
- `data/layout_params.csv` is intended to be the shared design-token source;
- LaTeX has a 31-style public registry and stable component entrypoints;
- production IDML has a component registry, deterministic golden fixtures,
  template resource merging, source trace, asset packaging, and a reference
  PDF in the publish handoff.

The current seam is not yet same-source:

- production IDML reparses RST and raw LaTeX with a hand-written parser instead
  of consuming the semantic state used by Sphinx;
- data pages can be loaded from phase2 a second time and appended independently
  of the prepared review bundle;
- the IDML path estimates page counts from text height, while LaTeX owns the
  actual pagination;
- the two renderers have separate style maps, fallbacks, locale behavior, and
  visible geometry constants;
- structural IDML validation cannot detect overset text, missing fonts, broken
  links, page-count drift, or content drift.

The JE-1000F US characterization build demonstrates the gap: the LaTeX PDF has
61 pages, the InDesign export has 52 pages, InDesign reports overset text on six
pages, and the IDML exporter reports skipped raw blocks.

## 3. Architectural Decision

The target pipeline is:

```text
review bundle + frozen snapshot
  -> one semantic manual IR + resolved style/token contract
  -> LaTeX reference PDF + measured page plan
  -> production IDML generated from the same IR/tokens/page plan
  -> InDesign final-mile adjustment
  -> final IDML/INDD + InDesign PDF + preflight/design delta
```

LaTeX public component macros remain stable. Shared transforms own semantic
classification; the LaTeX visitor renders those semantics through the existing
macros, while the IDML renderer consumes their serialized IR representation.

## 4. Invariants

1. One target build has one config identity, git SHA, frozen snapshot, bundle
   hash, semantic IR hash, style-contract hash, and asset set.
2. Production IDML never re-reads governed content behind the prepared bundle.
3. Every visible `HB-*` style has a machine-checked LaTeX binding, InDesign
   binding, token dependency, and final-mile edit policy.
4. Unknown components, skipped raw content, missing assets, missing fonts,
   modified links, and overset text are publish failures.
5. The initial IDML follows the measured LaTeX logical-page plan. Deliberate
   final pagination changes are recorded, not silently accepted.
6. Text, translation, specifications, legal copy, table structure, and asset
   identity are corrected at their source. InDesign edits never become content
   truth.

## 5. Phases

### Phase 0 - Contract and safety net

Files:

- `docs/renderers/contracts/manual_style.yaml`
- `tools/render_contract.py`
- `tests/test_render_contract.py`
- existing LaTeX and IDML style registries

Deliverables:

- machine-readable style contract for all 31 public LaTeX style IDs;
- typed layout-token parsing and locale resolution contract;
- coverage tests that expose missing tokens or renderer bindings;
- no production artifact change.

Safety net:

- style-registry ID set equals contract ID set;
- every required token exists in `layout_params.csv`;
- every style forbids content edits in InDesign;
- contract serialization and SHA are deterministic.

### Phase 1 - Semantic manual IR

Files:

- new focused `tools/manual_ir/` package;
- shared semantic transforms extracted from the LaTeX-only transforms;
- `docs/conf_base.py` sidecar emitter;
- `tools/export_idml.py` compatibility facade;
- IR fixtures and parity tests.

Deliverables:

- deterministic `manual.ir.json` with stable document/page/block/source IDs;
- normalized content, component, table, asset, break-policy, and source hashes;
- production IDML can consume the IR behind a config feature switch;
- legacy IDML remains byte-identical until the new renderer is selected.

### Phase 2 - Shared tokens and production IDML renderer

Files:

- `tools/idml/ir_renderer.py`
- `tools/idml/layout_tokens.py`
- existing IDML component/page/style modules;
- config-aware IDML dispatch and export paths.

Deliverables:

- production IDML reads only the IR and resolved tokens;
- visible hardcoded geometry moves into the shared contract/token surface;
- all 31 public styles and specialized tables/components have explicit IDML
  bindings;
- flow IDML remains a diagnostic semantic attachment, not the visual baseline.

### Phase 3 - LaTeX page plan and InDesign proof

Files:

- LaTeX page-anchor emitter and page-plan parser;
- IDML stable labels/layers/reference-page support;
- an InDesign runtime preflight/export script;
- parity-report and proof tests.

Deliverables:

- `latex_page_map.json` with logical page/component anchors;
- IDML frame chains follow the measured plan instead of character estimates;
- locked non-printing LaTeX reference layer;
- machine-readable InDesign preflight covering overset, fonts, links, pages,
  and exported PDF status.

### Phase 4 - Final-mile trace and publish integration

Files:

- IDML delivery and source-trace modules;
- release-manifest integration;
- designer checklist and operator documentation;
- optional stable-ID layout-delta extraction/replay.

Deliverables:

- engineering baseline package and designer-return package;
- hashes for source, bundle, IR, contract, reference PDF, baseline IDML,
  preflight, final IDML/INDD, InDesign PDF, and design delta;
- final-mile edits are auditable and reusable layout fixes are routed back to
  shared components/tokens.

## 6. Non-goals

- Do not replace the existing LaTeX visual implementation.
- Do not make flow IDML the production baseline.
- Do not promise arbitrary InDesign edits survive regeneration in the first
  implementation. Version 1 freezes content before design handoff.
- Do not require Adobe InDesign on normal CI workers. Structural and semantic
  parity runs in CI; real InDesign preflight runs on a provisioned design host.
- Do not back-port edited IDML text into source tables or templates.

## 7. Verification Ladder

Run in order for each phase:

1. `python -m ruff check build.py integrations tools tests scripts`
2. targeted contract/IR/IDML tests
3. `python -m unittest`
4. `python -m mypy tools/utils`
5. `python tools/check_maintainability_guardrails.py`
6. `python tools/check_doc_link_integrity.py`
7. JE-1000F US build and cross-renderer parity checks
8. real InDesign preflight and exported-PDF comparison on the design host

The publish acceptance target is: identical build identity and block/asset
hashes, zero skipped/unknown content, zero missing assets/fonts/links, zero
overset, equal initial page size/order/count, and approved visual differences
only.
