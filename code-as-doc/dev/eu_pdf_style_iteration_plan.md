# EU PDF Style Iteration Plan

This plan tracks the work needed to make the current JE-1000F EU LaTeX PDF output closer to the attached Jackery-style reference PDF, while keeping template maintenance cost under control.

The cover is out of scope for this plan. The focus is text style, component density, page structure, table behavior, and build stability.

## Maintenance Principles

- [ ] Do not add one config per model just for visual style changes.
- [ ] Keep the shared EU family config pattern.
- [ ] Prefer `data/layout_params.csv` for tunable layout values.
- [ ] Regenerate `docs/renderers/latex/params.tex` from `data/layout_params.csv`.
- [ ] Prefer reusable LaTeX components under `docs/renderers/latex/`.
- [ ] Prefer Python renderers that output shared LaTeX macros for structured pages.
- [ ] Add `only:: latex` blocks in RST templates only when regular RST cannot express the needed layout.
- [ ] Avoid duplicating the same raw LaTeX layout across language-specific templates.
- [ ] Keep HTML and Word output from being obviously broken by PDF-specific work.
- [ ] Add focused tests when renderer behavior changes.

## Phase 1: Text Style Closer To Reference

Goal: Make the existing EU PDF look closer to the reference at the typography and base component level, without trying to match pagination yet.

Estimated effort: 2-3 days.

- [x] Capture the current JE-1000F EU PDF as the visual baseline.
- [x] Export before screenshots for at least the first 20 pages.
- [x] Identify reference typography levels: body text, H1 title bars, subbars, table headers, table body, warning text, note/caution labels.
- [x] Extend `docs/renderers/latex/fonts.tex` to support the needed Gilroy weight levels with safe fallbacks.
- [x] Tune base page parameters in `data/layout_params.csv`: page margins, body font size, body leading, title bar height, list spacing, table cell padding, and footer style.
- [x] Regenerate `docs/renderers/latex/params.tex`.
- [x] Tune shared H1, subsection, list, and base table behavior in `docs/renderers/latex/components_base.tex`.
- [x] Tune warning and safety component typography and spacing in `docs/renderers/latex/components_safety.tex`.
- [x] Build JE-1000F EU PDF from `configs/config.eu.yaml`.
- [x] Compare the first 10 pages against the reference and note remaining style gaps.
- [x] Run `python3 build.py doctor --config configs/config.eu.yaml --model JE-1000F --region EU`.
- [x] Run `python3 -m unittest` if renderer code changed.

Acceptance criteria:

- [x] Paper size remains aligned with the reference.
- [x] The PDF builds successfully through the LaTeX backend.
- [x] Fonts, title bars, body text, lists, and base table density are visibly closer to the reference.
- [x] Pagination is allowed to remain different.
- [x] Most changes are concentrated in renderer files and layout parameters.

Phase 1 completion notes:

- Completed on 2026-05-01 on branch `codex/eu-pdf-style-analysis`.
- Before screenshots and after screenshots were generated under `.tmp/pdf_style_phase1/`.
- JE-1000F EU PDF page count changed from 170 pages to 110 pages after the compact typography pass.
- Remaining visual gaps are concentrated in symbols tables, LCD tables, product/operation page structure, and long-table pagination. These are Phase 2 and Phase 3 concerns.
- Validation run: `python3 build.py doctor --config configs/config.eu.yaml --model JE-1000F --region EU`.
- Validation run: `python3 build.py pdf --config configs/config.eu.yaml --model JE-1000F --region EU`.
- Validation run: `python3 build.py check --config configs/config.us.yaml --model JE-1000F --region US`.
- Validation run: `python3 -m unittest`.

## Phase 2: First Pages And High-Impact Components

Goal: Make the first 10-16 pages visibly closer to the reference, especially safety, symbols, what's in the box, product overview, LCD display, and operation pages.

Estimated effort: 5-8 days.

- [x] Add or extend shared compact table components in `docs/renderers/latex/`.
- [x] Add or extend notice, caution, note, and tip components in `docs/renderers/latex/`.
- [x] Update `tools/csv_pages/renderers_symbols.py` to emit LaTeX through shared macros instead of relying mainly on Sphinx `list-table`.
- [x] Update `tools/csv_pages/renderers_lcd_icons.py` to emit a compact LaTeX LCD icon table through shared macros.
- [x] Add tests for symbols renderer LaTeX output.
- [x] Add tests for LCD icons renderer LaTeX output.
- [x] Add a LaTeX-specific `WHAT'S IN THE BOX` layout that calls shared macros and avoids duplicated language layout logic.
- [x] Improve product overview LaTeX layout through renderer/component changes before editing language templates.
- [x] Improve early operation page layouts using shared operation/card/notice macros.
- [x] Keep any RST `only:: latex` additions small and macro-based.
- [x] Build EU English single-language PDF.
- [x] Build EU multilingual PDF.
- [x] Compare screenshots for pages 1-16 against the reference.
- [x] Record remaining differences page by page.
- [x] Run `python3 -m unittest`.
- [x] Run a JE-1000F EU PDF build.

Acceptance criteria:

- [x] Safety, symbols, what's in the box, product overview, LCD display, and early operation pages are visibly closer to the reference.
- [x] Symbol and LCD tables are compact enough to reduce the current loose Sphinx-table appearance.
- [x] Reusable macros carry the layout, not duplicated raw LaTeX in each language template.
- [x] English single-language and EU multilingual builds both complete.

Phase 2 completion notes:

- Completed on 2026-05-01 with shared raw-LaTeX component coverage for notices, symbols, LCD icon tables, WHAT'S IN THE BOX, product overview panels, and the LCD mode table in operation pages.
- The symbols renderer now emits `\HBNoticeBlock`, `\HBSymbolTable`, `\HBSymbolSignalRow`, and `\HBSymbolIconRow` under `only:: latex`, while preserving the previous list-table output under `only:: not latex`.
- The LCD icons renderer now emits `\begin{HBLcdIconTable}` and `\HBLcdIconRow` under `only:: latex`, with basename-only image arguments, while preserving the previous list-table output under `only:: not latex`.
- The EU shared WHAT'S IN THE BOX templates for en, fr, es, de, it, and uk now call `\HBInBoxThree` and `\HBTipBlock` for PDF output.
- The EU product overview templates for en, fr, es, de, it, and uk now call `\HBOverviewPanel`, `\HBOverviewPair`, and `\HBOverviewFull` for PDF output.
- The EU operation templates for en, fr, es, de, it, and uk now call `\begin{HBLcdModeTable}`, `\HBLcdModeFirstGroup`, and `\HBLcdModeSecondGroup` for the LCD screen mode table.
- Screenshot comparison artifacts were generated under `.tmp/pdf_style_phase2/`: current pages 1-16 under `current/` and a contact sheet at `.tmp/pdf_style_phase2/pages_001_016_contact.png`.
- Pixel-diff spot metrics against the Phase 1 reference PNGs, after resizing current screenshots to the reference raster size, remain high because content flow and pagination still differ:
  - p001: MAE 23.3, changed area 21.6%
  - p002: MAE 31.0, changed area 24.7%
  - p003: MAE 26.3, changed area 19.6%
  - p004: MAE 42.8, changed area 30.8%
  - p005: MAE 23.7, changed area 27.6%
  - p006: MAE 29.5, changed area 28.0%
  - p007: MAE 32.1, changed area 38.8%
  - p008: MAE 29.2, changed area 43.8%
  - p009: MAE 28.6, changed area 28.5%
  - p010: MAE 27.3, changed area 33.9%
  - p011: MAE 22.2, changed area 40.8%
  - p012: MAE 31.0, changed area 45.5%
  - p013: MAE 36.1, changed area 49.0%
  - p014: MAE 26.8, changed area 39.7%
  - p015: MAE 38.2, changed area 55.1%
  - p016: MAE 37.1, changed area 30.3%
- Remaining differences by page group:
  - p001-p002: preface and safety are closer in base type density, but warning text line breaks and exact vertical rhythm still differ.
  - p003: WHAT'S IN THE BOX now uses the shared compact macro; image size and label spacing still need visual tuning.
  - p004-p005: product overview now uses shared compact panels; source overview artwork and annotation density still differ from the reference.
  - p006-p010: operation pages now use the shared LCD mode macro, but long prose, caution list-tables, and resume-condition tables still create overfull/underfull LaTeX warnings.
  - p011-p016: later early-book sections inherit the Phase 1 typography, but pagination and long translated headings still need Phase 3 multilingual tuning.
- Validation run: `python3 -m py_compile tools/csv_pages/renderers_symbols.py tools/csv_pages/renderers_lcd_icons.py`.
- Validation run: `python3 -m unittest`.
- Validation run: `python3 build.py pdf --config configs/config.eu-en.yaml --model JE-1000F --region EU --no-clean`.
- Validation run: `python3 build.py pdf --config configs/config.eu.yaml --model JE-1000F --region EU --no-clean`.
- Validation run: `python3 build.py check --config configs/config.us.yaml --model JE-1000F --region US`.
- Build outputs:
  - `docs/_build/JE-1000F/EU/en/pdf/manual_je1000f_eu_en.pdf`
  - `docs/_build/JE-1000F/EU/pdf/manual_je1000f_eu.pdf`
- Known residual warnings: existing docutils line-block/title-underlines in several multilingual templates, a malformed French resume-condition grid table warning, missing glyph warnings for some Unicode dash characters, and LaTeX overfull/underfull boxes on long multilingual rows. These are build-stable but remain Phase 3 QA/pagination work.

## Phase 3: Multilingual Full-Book Stability And QA

Goal: Extend the improved style across the EU multilingual manual and make pagination, table breaks, and QA stable enough for regular use.

Estimated effort: 2-3 weeks.

- [ ] Build a multilingual screenshot baseline for en, fr, es, de, it, and uk.
- [ ] Sample at least safety, symbols, LCD, operation, spec, troubleshooting, warranty, and app setup pages for each language.
- [ ] Add or tune language density parameters in `data/layout_params.csv`.
- [ ] Avoid language-template-specific layout forks unless there is no reusable alternative.
- [ ] Handle long words and long translated phrases in title bars and compact tables.
- [ ] Tune image scaling rules for dense operation pages.
- [ ] Define breakable long-table behavior separately from non-breakable card/table components.
- [ ] Apply compact long-table behavior to spec, troubleshooting, warranty, and similar dense sections.
- [ ] Add PDF QA checks for successful build, expected page size, font embedding, obvious blank pages, and key-page screenshot generation.
- [ ] Run a full EU multilingual PDF build.
- [ ] Run EU single-language spot builds for at least en, fr, and es.
- [ ] Document the style/component boundaries so future contributors know where to change layout.
- [ ] Document the rule against scattering raw LaTeX through language templates.
- [ ] Run `python3 -m unittest`.
- [ ] Run `python3 build.py check --config configs/config.eu.yaml --model JE-1000F --region EU` or the closest available quality gate.
- [ ] Produce a before/after comparison package.
- [ ] Record residual gaps and lower-priority follow-up items.

Acceptance criteria:

- [ ] EU multilingual PDF builds reliably.
- [ ] Key multilingual pages have no obvious overflow, broken tables, or accidental blank pages.
- [ ] Pagination and density are broadly close to the reference.
- [ ] Future style changes can mostly be made through layout parameters, LaTeX components, or structured renderers.
- [ ] RST template maintenance remains manageable.

## Recommended Execution Order

1. Phase 1 should land first as the typography and base component foundation.
2. Phase 2 should focus on the highest-visibility pages and renderer-owned structured tables.
3. Phase 3 should stabilize multilingual pagination, long tables, and repeatable QA.

Do not start broad template rewrites before the renderer/component layer is in place.
