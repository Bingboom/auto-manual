# JBP-3600A / US / English — Git-only PDF intake

This package freezes the supplied US Jackery Battery Pack 3600 User Manual (model JBP-3600A, 28 pages, no printed manual-version string) and converts only the printed English pages 01–08, physical PDF pages 4–11. The printed cover, the US/FR/ES preface, the global contents, the French and Spanish bodies and the back cover stay in the archived PDF and are not repeated in the Web body (「封面和目录 不用体现在web版面上」).

**Status: Git-only source candidate for the operator's layout review.** There is no `source/approval.json`; the replayed IR is `publication_eligible: false`. Acceptance, merge and any release need separate operator decisions.

## Print fidelity

| Print feature | Web |
| --- | --- |
| Line breaks | A line the print ends while the next word would still have fitted is a print break; every other line end is a wrap. Logged in `source/en/coverage.json`. |
| Outlined text | 48 visible lines are vector outlines with no text layer (the safety list, the FCC measures, the NOTE/CAUTION/NOTES bodies, STORAGE, the warranty exclusions). `source/text-recovery.json` restores them from source pixels with their glyph-path boxes; their statement starts are reviewed, because the lines share one indent. |
| Bold, headings | Bold print runs are `strong`; chapter titles and subheadings keep print case. |
| Lists | Only STORAGE prints bullet marks, so only it is a list. Unmarked printed statements stay lines. |
| Tables | The LCD table has no header row, as printed. Troubleshooting codes keep their printed line (F6-F9, / FA, FC, FE). All two-column tables fit the phone at 390 px. |
| Callouts | NOTE, CAUTION, NOTES and Warning (print case) use the shared callout strip. The p8 NOTES sentence keeps its inline LCD icon as a native vector. |
| Figures | Complete panels with no visible caption; the caption is the alt text and words printed in the art stay in the art. |

Shared components: HB-CALLOUT-STRIP 4, HB-SPECIAL-FCC 1, HB-SPECIAL-INBOX 1, HB-SPECIAL-REFERENCE-FIGURE 10, HB-TABLE-SPEC 3, HB-TABLE-SYMBOL-ICON 1, HB-TABLE-SYMBOL-SIGNAL 1, HB-TABLE-TROUBLESHOOTING 1, HB-WARRANTY-LEAD 1, HB-WARRANTY-SECTION 5, HB-WARRANTY-YEARS 1. `source/presentation.css` holds only this source's geometry.

Known shared-component behaviour, kept rather than changed in the shared renderer:
- The FCC component runs the two left-column paragraphs ("NOTE: … FCC Rules." and "These limits …") into one paragraph. The four measures are its list; the source stylesheet hides list marks, which the print does not show.
- The specification table component prints dimensions with "×" for the print's "x".

## Artwork reuse

Inventory first, per the Web artwork reuse order. Decisions are in `source/figures.json`, `source/symbols.json`, `source/glyphs.json` and `audit/asset-decisions.json`.
- Reused unchanged from the published JBP-3600A EU English Web manual, pixel-identical to this print (template match NCC ≥ 0.9999): the LCD display, POWER ON/OFF and LCD DISPLAY ON/OFF art.
- Extracted from this PDF (complete panels, 4x): the in-box items, both overview views, clearance, stacking, locking, AC and solar charging. The EU art shows the EU host product (Explorer 3600 Plus) or other label geometry, so it does not match this print.
- Symbols: 11 shared native-v1 symbols and the shared FCC mark, each within the fixed glyph-comparison gate against this PDF's own drawings. The symbol table is admitted through `symbol_asset_admission` in `source_manifest.json`.
- One native vector: the p8 battery-pack connection icon.

## Reconstruction

- `source/native.py` reads the archived PDF (word geometry, font weight, line junctions) and the outlined-line recoveries.
- `source/intake.py` maps each page region to shared flow nodes and components and writes `source/en/content.json` and `source/en/coverage.json`. The coverage gate refuses any unclassified English body word, duplicate live copy or unused recovery.
- `source/extract_assets.py` materializes the artwork decisions and pins their hashes.
- `rebuild.py` verifies the PDF, every inventoried input and the pinned shared repository inputs, then replays through the shared Manual IR APIs.

Run from the repository root (PyMuPDF 1.28.0 / MuPDF 1.29.0, `requirements.lock`):

```sh
PKG=data/manual_sources/JBP-3600A/US/en/git-20261014-16ae12b0
python3 "$PKG/source/intake.py"
python3 "$PKG/source/refresh_manifest.py"
PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/rebuild.py" --output tmp/jbp3600a/en
python3 -m sphinx -n -W --keep-going -b html tmp/jbp3600a/en tmp/jbp3600a-site/en
```

To re-freeze: remove `web/en`, run `source/refresh_manifest.py`, rebuild into `web/en`, and run `source/refresh_manifest.py` again.

## Boundaries and source archive

Git-only boundary: no Feishu/Base/source table, queue, online asset, build/link or HTML_link writes. The only Feishu call was the read-only download of the supplied file. The package does not register a phase2 or print-build target; JBP-3600A is already in the portal navigation's battery group.

The unchanged 7,257,682-byte original, `Jackery Battery Pack 3600 User Manual.pdf` (SHA-256 `16ae12b0426828b921694a496ce699386d92165d5476a10dded83be1a893a91c`), is committed at the package root, under the 32 MiB per-file budget. `intake.py`, `extract_assets.py` and `rebuild.py` verify it before they run.
