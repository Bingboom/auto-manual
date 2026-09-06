# ManualIR v2: LCD, Troubleshooting, and Symbols ComponentSpec Plan

Status: implementation plan for the fourth cross-renderer IR cut.

## Discovery

The whole-document Web package already serializes renderer-neutral flow and ten
registered component families. Four mature style families still enter the
package as ordinary flow and are recognized again by Web-only DOM projectors:

- `HB-TABLE-LCD-ICON`
- `HB-TABLE-TROUBLESHOOTING`
- `HB-TABLE-SYMBOL-SIGNAL`
- `HB-TABLE-SYMBOL-ICON`

Their existing source adapters live in `tools/manual_ir/web_tables.py` and
`tools/manual_ir/web_symbols.py`. Their Web renderers already produce native,
editable HTML tables; no raster replacement is needed or allowed.

The current `ComponentSpec` registry assumes one asset per role. LCD and symbol
icon tables instead contain an ordered, variable-length asset collection. The
whole-document rebinder also collapses role bindings into a dictionary, so a
repeated role would silently retain only one image. The contract must therefore
make repeatability explicit and rebind same-role assets in stable order.

Real source shapes used as characterization targets:

| Target | LCD rows/icons | Troubleshooting | Signal rows | Symbol panels |
| --- | ---: | --- | ---: | --- |
| JE-1000F US | 26/26 | 1 header + 11 rows | 1 header + 4 rows | 6 left + 5 right |
| JE-3000C KR | 26/26 | 1 header + 11 rows | 1 header + 4 rows | 5 left + 2 right |

The legacy symbol-pair decoder hard-codes the US 6+5 geometry. The component
source adapter must accept variable non-empty left/right panels while retaining
strict four-cell, unspanned, paired icon/meaning validation.

`load_web_document()` already receives page declarations from the materialized
manifest, but discovery receives only the path. Passing the declaration into
component discovery lets renamed page slots retain their declared semantics
without filename heuristics.

## Implementation phases

1. Add characterization and fail-closed tests for registry repeatable assets,
   ordered rebinding, US/KR structural variants, declared renamed pages, and
   cold Web replay without legacy projectors.
2. Extend registry asset-role declarations with optional `multiple: true`.
   Preserve the existing one-per-role default and reject duplicate roles unless
   explicitly repeatable.
3. Add renderer-neutral constructors and HTML source adapters for the four
   component families. Store rich and plain text where appropriate; rows refer
   to the ordered `assets` tuple by `asset_index`.
4. Add Web, LaTeX, IDML, and Word projections. Web renders the existing native
   compositions directly from the embedded spec. Non-Web projections expose
   renderer-owned payloads without moving geometry into the shared IR.
5. Integrate the four claim types into whole-document discovery and ordered
   asset packaging. Pass the manifest page declaration through discovery.
6. Dispatch embedded Web components directly and skip the corresponding legacy
   LCD, troubleshooting, and symbol source projectors when those components are
   resolved.
7. Update the owning component/style and operator documentation, then run the
   verification ladder and real cold-replay builds.

## Safety net

- Registry validation rejects undeclared repetition, missing required roles,
  malformed slots, unknown adapters, and locale-policy drift.
- Source adapters require one governed table of the declared kind, complete
  unspanned rows, non-empty text, valid images, and matching semantic/markup
  content.
- Asset ordering is checked from source tag through packaged `ComponentSpec`
  and renderer projection; missing or changed packaged files fail before replay.
- Embedded replay tests patch the legacy DOM projectors to raise if invoked.
- Existing public compatibility functions remain available for non-whole-
  document callers during this cut.
- US and KR variants prove that no model-specific row count is introduced.
- The separate `review/JE-1000F-EU` worktree remains read-only; its DE/IT pages
  are copied only into an isolated verification worktree/output directory.

## Non-goals

- Do not alter PDF/AI artwork or convert these tables to screenshots.
- Do not add model-specific Python, CSS, or per-target component definitions.
- Do not change public CLI flags, phase2 schemas, dependencies, workflows, or
  approved reference-layout composition.
- Do not retire the compatibility source projectors until the final cut.
- App/reference figures and presentation overlay inheritance belong to cuts 5
  and 6 respectively.

## Verification ladder

1. `python3 -m ruff check` on touched Python modules and tests.
2. Targeted component, whole-document, Web table, and symbol tests.
3. `python3 -m unittest`.
4. `python3 tools/check_maintainability_guardrails.py`.
5. `python3 tools/check_doc_link_integrity.py`.
6. `python3 build.py check --config configs/config.us-en.yaml --model JE-1000F --region US --data-root tests/fixtures/phase2`.
7. Whole-document cold replay for JE-1000F US EN/FR/ES, JE-3000C KR KO,
   and the copied JE-1000F EU DE/IT review pages, with source-table reads
   forbidden and packaged asset hashes verified.
