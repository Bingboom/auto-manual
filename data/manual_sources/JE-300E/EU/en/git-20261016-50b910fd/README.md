# JE-300E / EU / English — Git-only booklet intake

This package freezes the supplied Jackery Explorer 300 EU booklet (model JE-300E, project HTE147, part 55060100007, printed version HTE147300A-EU-JAK-A0) and converts its English edition. The file is the Adobe Illustrator master `55060100007 HTE147300A-EU-JAK-A0 说明书 RoHS REACH_修正.ai` (PDF-compatible, 97 pages, 130 × 185 mm), read once from Feishu wiki node `KEnIwtwxqiqdj0kMiCLcd9plnne`.

**Status: operator-accepted Git-only release.** The operator answered the layout items D1–D13 on 2026-10-16 (「1. 保留为第一章 2. 保留为最后一章 3. 可以 4. 可以 5. 可以 6. 拆成4行 7. 可以 8. 可以 9. 可以 10. 可以 11. 可以 12. 准入 13.」), recorded in [`audit/review.zh.md`](audit/review.zh.md): defaults kept, except D6 (troubleshooting F0–F3 as one row per code) and D12 (this source enrolled for fresh EU admission). D13 stays open for the product owner. The candidate was merged as PR #1558 (`10699536`), and the operator asked for the release (「做完直接发布」, 2026-10-16). `source/approval.json` binds that acceptance to these exact source inputs, D12 enrolled this source in `docs/renderers/contracts/prepared_component_admission.json`, and the replayed IR is `publication_eligible: true`. Merge and release run under MA-313 in `code-as-doc/dev/merge_authorizations.md`.

## Scope

| Web chapter | PDF page | Print |
| --- | --- | --- |
| IMPORTANT | 3 (English half, y < 170 pt) | front matter |
| IMPORTANT SAFETY INFORMATION … HOW TO READ YOUR SERIAL NUMBER | 7–24 | printed 01–18 |
| EU Regulations (declaration, manufacturer) | 97 | back cover |

Not in the Web body (「封面和目录 不用体现在web版面上」): the printer's spec sheet (p1), the cover (p2), the German front matter (p4), the contents (p5–6) and the FR/ES/DE/IT bodies (p25–96). The other four languages follow as an added-locales package, which pins this package's archived file through `original_source.archive_parts` (a repository path) instead of copying it, as `JA-TS02A/US/added-locales` does.

## Shared components only

Every printed block maps to a shared component or plain shared flow; [`audit/component-map.json`](audit/component-map.json) records the map. The package has no package class, inline style or plain table, so it passes the prepared-document shared-style gate without a baseline entry or a `shared_component_exceptions` declaration. `source/presentation.css` holds geometry only: figure widths selected by `data-reference-id`, inline glyph size and print heading case.

Components: HB-CALLOUT-STRIP 11, HB-SPECIAL-INBOX 1, HB-SPECIAL-REFERENCE-FIGURE 15, HB-TABLE-LCD-ICON 1, HB-TABLE-LCD-MODE 1, HB-TABLE-REFERENCE 1, HB-TABLE-SPEC 4, HB-TABLE-SYMBOL-ICON 1, HB-TABLE-SYMBOL-SIGNAL 1, HB-TABLE-TROUBLESHOOTING 1, HB-WARRANTY-LEAD 1, HB-WARRANTY-SECTION 5, HB-WARRANTY-YEARS 1.

Layout reference: the JE-3600A EU English Web edition (the same EU Explorer chapter set and components) and the live JE-300D EU Web manual. Method references: `JA-TS02A/US/en/git-20261013-11ce66b1` and `JBP-3600A/US/git-20261014-16ae12b0`.

## Print fidelity

| Print feature | Web |
| --- | --- |
| Line breaks | A line the print ends while the next word would still have fitted is a print break; every other line end is a wrap. 31 breaks are logged in `source/en/coverage.json`. |
| Bold, headings | Bold and semibold print runs are `strong`. Headings keep print case and level: chapter bars, ● subheadings, and the recycling guide's two subheading sizes. |
| Lists | Printed bullet and number marks become lists; the p7 hollow-bullet items nest under their item. |
| Joins and marks | Ligatures are expanded; organiza-/tions is rejoined. The two ® on p18 are overprinted on placeholder spaces; they are spliced in at their character position (logged). |
| Figures | Complete print panels with no visible caption. The caption is the alt text, and words printed in the art stay in the art; sentences printed in a panel are read out in its alt text. The p12 sentence under the DC 12V drawing is redacted from the crop (text only) and set as live text. |

Print wording is kept as printed, including source slips that the review lists for the source owner (D11).

## Artwork reuse

Inventory first, per the Web artwork reuse order. Every decision, with the paths checked, is in [`audit/asset-decisions.json`](audit/asset-decisions.json), `source/figures.json`, `source/symbols.json` and `source/glyphs.json`.

- **Symbols.** All 8 symbol rows reuse shared native-v1 symbols unchanged. Each passes the fixed glyph comparison against this print's p8 drawings; `symbol_asset_admission` in `source_manifest.json` binds every row.
- **Panels.** No JE-300E EU artwork exists on main. The JE-300D EU Web art shows a different product, and the unmerged JE-300E-SG US draft (#1525) shows US outlets and the sand-gold housing. The 20 panels are cut from this print at 4x as complete panels.
- **LCD and contact icons.** The shared LCD library has no glyph for these icons; the shared fault-code PNG fails the fixed comparison against this print's F8 mark (recorded). 12 LCD icons and 4 contact pictograms are this print's native vector paths, transparent.

## Reconstruction

```sh
PKG=data/manual_sources/JE-300E/EU/en/git-20261016-50b910fd
python3 "$PKG/source/extract_assets.py"
python3 "$PKG/source/intake.py"
python3 "$PKG/source/refresh_manifest.py"
PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/rebuild.py" --output tmp/je300e-eu/en
python3 -m sphinx -n -W --keep-going -b html tmp/je300e-eu/en tmp/je300e-eu-site/en
```

PyMuPDF 1.28.0 / MuPDF 1.29.0 (`requirements.lock`). The coverage gate in `intake.py` refuses any unclassified English word in scope, duplicate live copy or unused split. To re-freeze: remove `web/en`, run `source/refresh_manifest.py`, rebuild into `web/en`, and run `source/refresh_manifest.py` again.

Test: `python3 -m unittest tests.test_je300e_eu_en_web`.

## Admission

Strict Sphinx, the shared-style gate and the caption-frame admission pass on `web/en`. Fresh EU publication additionally requires enrolment of this source in the shared `docs/renderers/contracts/prepared_component_admission.json`. That contract stays unchanged here. [`audit/proposed-component-admission.json`](audit/proposed-component-admission.json) holds the proposed source profile, and the package test proves that a temporary accepted copy passes fresh component admission, symbol admission, caption-frame admission and the publishable-IR gate under it (D12).

## Boundaries

Git-only: no Feishu/Base/source-table, queue, asset-registry, build/link or HTML_link writes. The only Feishu call was the read-only download. No phase2 or print target is registered, and no shared renderer, component, contract, template or workflow changed. The build.py JE-1000F/US check is a repository regression gate only.
