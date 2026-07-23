# IDML maintenance and symbols geometry discovery (2026-07-23)

## Scope

Continue the approved JE-1000F US V2.0 editable-IDML parity work after the LCD
continuation phase.  This phase owns the reusable combined maintenance and
symbols composition on English page 5, French page 23, and Spanish page 41.
It must not weaken visual-parity thresholds, rewrite phase2 source copy, or
change unrelated page families.

## Baseline

Geometry22 is the accepted starting artifact:

- overall MAD: `0.060204`
- overall changed-pixel ratio: `0.195544`
- native InDesign 2026 `21.0.1.6`: 58 pages, 0 overset stories, 0 missing
  fonts, and 0 bad links
- English page 5: MAD `0.074847`, changed ratio `0.238052`
- French page 23: MAD `0.081277`, changed ratio `0.231273`
- Spanish page 41: MAD `0.081670`, changed ratio `0.233539`

The strict approved-reference thresholds remain MAD `<= 0.008` and changed
ratio `<= 0.04`.

## Read-only findings

The reference and geometry22 pages were rendered from both PDFs at 180 dpi and
inspected page by page.

1. The two safety-tail panels use an outlined warning triangle in geometry22;
   the reference uses the dark filled triangle with a white exclamation mark.
   This is a shared semantic-asset binding error, not a per-page placement fix.
2. The signal-word table's dark badges lose the white warning triangle for all
   French and Spanish rows and for some English rows.  The current fallback
   creates text-only paragraph shading when a label-named raster asset does not
   exist.  The badge must instead compose the shared editable label with the
   governed warning asset.
3. Symbol-table icons are materially smaller than the reference even though
   the source icons resolve.  `_symbols_icon_table` hard-codes an 18 pt image
   box instead of using the existing `comp_symbol_icon_width` and
   `comp_symbol_icon_height` contract tokens.
4. The signal and icon tables already have fixed row-height tokens, but visible
   constants remain in `tools/idml/symbols_page.py`: proportional column widths,
   a 6 pt table gap, fixed cell insets, and special frame padding.  These bypass
   the existing symbol component tokens and make the rounded table shells and
   content geometry drift together.
5. The generated French and Spanish safety labels and maintenance paragraphs
   do not always match the approved PDF copy.  That is source-content debt and
   is deliberately excluded from this geometry phase; geometry corrections
   must not hide it by editing `data/phase2` or review derivatives.

## Load-bearing entrypoints

- `tools/idml/symbols_page.py`: combined page composition plus signal/icon
  table stories
- `tools/idml/components/callout.py`: semantic safety-tail notice renderer and
  warning-asset binding
- `tools/idml/params.py` and `data/layout_params.csv`: governed component and
  locale tokens
- `docs/renderers/contracts/manual_style.yaml`: public style ownership
- `tests/test_export_idml.py`: editable story, row, asset, and placement
  contracts

## Implementation plan

1. Add characterization tests for the reference asset bindings, token-driven
   icon frames, and token-driven symbol columns/gap before changing production
   code.
2. Bind both safety-tail and signal badges to the shared approved warning
   triangle while preserving label text as editable top-layer text.
3. Replace visible symbol-table constants with existing contract tokens; add a
   locale token only where measurements prove that a shared value cannot fit
   all three languages.
4. Export a new IDML through the public build entrypoint, run native InDesign
   preflight, render the three pages, and compare them against geometry22 and
   the approved PDF.
5. Keep the phase only if all icons and editable labels remain present, native
   preflight stays clean, and aggregate plus focused-page parity does not
   regress.  Commit it separately so the whole phase can be reverted.

## Verification ladder

1. `python3 -m ruff check tools/idml/symbols_page.py tests/test_export_idml.py`
2. targeted symbol-page and component tests
3. `python3 -m unittest`
4. `python3 tools/check_maintainability_guardrails.py`
5. `python3 tools/check_doc_link_integrity.py`
6. `python3 build.py check --config configs/config.us-en.yaml --model JE-1000F --region US ...`
7. IDML structural validation, native InDesign preflight, 180 dpi PNG review,
   and strict approved-PDF parity

## Non-goals

- no phase2 source-copy or schema changes
- no generated `_build`, `_review`, `output`, `reports`, or `tmp` artifacts in
  the commit
- no threshold relaxation, rasterized whole-page replacement, or per-page
  one-off overlays
- no changes to LCD, troubleshooting, charging, warranty, or app components
