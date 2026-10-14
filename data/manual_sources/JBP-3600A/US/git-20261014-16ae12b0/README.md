# JBP-3600A / US / EN · FR · ES — Git-only PDF intake

This package freezes the supplied US Jackery Battery Pack 3600 User Manual (model JBP-3600A, 28 pages, no printed manual-version string). It converts the three printed bodies of the same booklet into three Web editions:

| Language | Printed pages | PDF pages | Web root |
| --- | --- | --- | --- |
| English | 01–08 | 4–11 | `web/en` |
| French | 09–16 | 12–19 | `web/fr` |
| Spanish | 17–24 | 20–27 | `web/es` |

The printed cover, the US/FR/ES preface, the global contents and the back cover stay in the archived PDF and are not repeated in any Web body (「封面和目录 不用体现在web版面上」).

**Status: Git-only source candidate for the operator's layout review.** There is no `source/approval.json`; every replayed IR is `publication_eligible: false`. Acceptance, merge and any release need separate operator decisions.

## Operator decisions (2026-10-14)

- **Layout reference: JBP-2000B** (「用JBP-2000B的参考」). Chapter set, heading treatment, components and figure style follow the published JBP-2000B and JBP-3600A EU Web manuals. JA-TS02A remains the method reference for the frozen intake. Wording stays as printed in this booklet: US contact, FCC text, the US warranty.
- **Chapter order: print order** (「按印刷顺序」). TROUBLESHOOTING stays before CONNECTIONS, as printed; the references put CONNECTIONS first. The package test pins this order.
- **Languages: add French and Spanish** (「加法语和西语」), as for the US JHP-5000C and JHP-3000D manuals.

## Package shape

One US-level package with `web_roots` en/fr/es, like `JHP-5000C/US/git-20261010-051169dd-web-layout` and `JHP-3000D/US/git-20261013-cebe4aab-web-layout`. The three bodies come from one PDF (one SHA-256, one technical version) and share one layout, artwork policy and symbol set. One package keeps a single source identity, one intake with a per-language geometry table, and one review. The add-on shape (`JHP-3600C/US/added-locales`) suits locales that arrive from a separate source; that is not the case here. The package moved from `US/en/` to `US/` in the same PR, before review.

## Print fidelity

| Print feature | Web |
| --- | --- |
| Line breaks | A line the print ends while the next word would still have fitted is a print break; every other line end is a wrap. Logged per language in `source/<lang>/coverage.json`. |
| Outlined text | Some visible lines are vector outlines with no text layer: EN 48, FR 59, ES 61. They cover the safety list, the FCC measures (and FR/ES FCC right column), the NOTE/CAUTION/NOTES bodies, STORAGE and the warranty exclusions. `source/text-recovery.json` restores them from source pixels with their glyph-path boxes; statement starts are reviewed, because the lines share one indent. FR apostrophes are kept as printed (straight or curly per line). |
| Hyphen splits | Rejoined and logged: FR conformé-/ment; ES comunica-/ciones, completa-/mente (twice). |
| Bold, headings | Bold print runs are `strong` (including the outlined FR/ES MODIFICATION labels); chapter titles and subheadings keep print case. |
| Lists | Only printed bullet marks become lists: EN and ES STORAGE, FR warranty exclusions. Unmarked printed statements stay lines. |
| Tables | The LCD table is the shared LCD description table (as on the EU Web), with no header row, as printed. Troubleshooting codes keep their printed line (F6-F9, / FA, FC, FE). All two-column tables fit the phone at 390 px. |
| Callouts | Print labels as printed: EN NOTE / CAUTION / NOTES / Warning; FR Remarques / Important / Remarques / Avertissement; ES NOTA / PRECAUCIÓN / Observaciones / Advertencia. The p8 NOTES sentence keeps its inline LCD icon. |
| Figures | Complete panels with no visible caption; the caption is the alt text, and words printed in the art stay in the art. |

Printed source wording is kept, including evident print slips: FR "Mlise en garde!", ES "botón de encendido Principa", "oponerse en contacto", "laduración", "garantia,debe".

Shared components per language: HB-CALLOUT-STRIP 4, HB-SPECIAL-FCC 1, HB-SPECIAL-INBOX 1, HB-SPECIAL-REFERENCE-FIGURE 10, HB-TABLE-REFERENCE 1, HB-TABLE-SPEC 3, HB-TABLE-SYMBOL-ICON 1, HB-TABLE-SYMBOL-SIGNAL 1, HB-TABLE-TROUBLESHOOTING 1, HB-WARRANTY-LEAD 1, HB-WARRANTY-SECTION 5, HB-WARRANTY-YEARS 1. `source/presentation.css` holds only this source's geometry and serves all three languages.

Known shared-component behaviour, kept rather than changed in the shared renderer:
- The FCC component runs the two left-column paragraphs into one paragraph. The four measures are its list; the source stylesheet hides list marks, which the print does not show.
- The specification table component prints dimensions with "×" for the print's "x".

The ES p22 page carries a white, invisible leftover "OPERACIONES" layer text behind the POWER panel. Coverage classifies it as `invisible-print-text`; it is not Web copy.

## Artwork reuse

Inventory first, per the Web artwork reuse order. Decisions are in `source/figures.json`, `source/symbols.json`, `source/glyphs.json` and `audit/asset-decisions.json`.
- **EU reuse (English).** Reused unchanged from the published JBP-3600A EU English Web manual, pixel-identical to this print (template match NCC ≥ 0.9999): the LCD display, POWER ON/OFF and LCD DISPLAY ON/OFF art.
- **English extractions.** Cut from this PDF as complete panels at 4x: the in-box items, both overview views, clearance, stacking, locking, AC and solar charging. The EU art shows the EU host product (Explorer 3600 Plus) or other label geometry.
- **French and Spanish.** A panel shares the English file when its crop matches the English panel within antialiasing (at most 0.1% of pixels differ by more than 60/255): FR LCD DISPLAY ON/OFF, ES stacking and ES solar charging. All other FR/ES panels are cut from their own pages, because their labels are translated or their art is set at a sub-point offset.
- **Symbols.** 11 shared native-v1 symbols and the shared FCC mark serve all three languages. Each passes the fixed glyph-comparison gate against that language's own drawings. The symbol tables are admitted per locale through `symbol_asset_admission` in `source_manifest.json`.
- **Inline icon.** One native vector, the p8 battery-pack connection icon, shared by FR and ES after a printed-pixel comparison.

## Reconstruction

- `source/native.py` reads the archived PDF (word geometry, font weight, line junctions) and the outlined-line recoveries for one language.
- `source/intake.py` maps each page region (`GEOMETRY`, per language) to shared flow nodes and components. It writes `source/<lang>/content.json` and `source/<lang>/coverage.json`. The coverage gate refuses any unclassified body word, duplicate live copy, or unused recovery or split.
- `source/extract_assets.py` materializes the artwork decisions and pins their hashes.
- `rebuild.py --language <lang>` verifies the PDF, every inventoried input and the pinned shared repository inputs. It then replays one language through the shared Manual IR APIs.

Run from the repository root (PyMuPDF 1.28.0 / MuPDF 1.29.0, `requirements.lock`):

```sh
PKG=data/manual_sources/JBP-3600A/US/git-20261014-16ae12b0
python3 "$PKG/source/intake.py"
python3 "$PKG/source/refresh_manifest.py"
for lang in en fr es; do
  PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/rebuild.py" --language "$lang" --output "tmp/jbp3600a/$lang"
  python3 -m sphinx -n -W --keep-going -b html "tmp/jbp3600a/$lang" "tmp/jbp3600a-site/$lang"
done
```

To re-freeze: remove `web/`, run `source/refresh_manifest.py`, rebuild each language into `web/<lang>`, and run `source/refresh_manifest.py` again.

## Boundaries and source archive

Git-only boundary: no Feishu/Base/source table, queue, online asset, build/link or HTML_link writes. The only Feishu call was the read-only download of the supplied file. The package does not register a phase2 or print-build target, and it changes no template or shared renderer. JBP-3600A is already in the portal navigation's battery group.

The unchanged 7,257,682-byte original, `Jackery Battery Pack 3600 User Manual.pdf` (SHA-256 `16ae12b0426828b921694a496ce699386d92165d5476a10dded83be1a893a91c`), is committed at the package root, under the 32 MiB per-file budget. `intake.py`, `extract_assets.py` and `rebuild.py` verify it before they run.
