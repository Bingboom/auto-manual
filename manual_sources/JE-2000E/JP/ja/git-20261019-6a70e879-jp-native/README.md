# JE-2000E 日本語 Web candidate

This is a Git-only conversion candidate for operator review. It does not enroll a phase2 target, create queue records, merge engineering changes, or publish to Read the Docs.

## Source authority

- Product: Jackery ポータブル電源 2000 Plus; cover model **JE-2000E**; JP / ja.
- Supplied filename: `Jackery ポータブル電源 2000 Plus取扱説明書V2.0-2026-06-29.pdf`.
- Original PDF: `source/original.pdf`, 28 pages, SHA-256 `6a70e879d65c14741462d0107e45c22f3ce1507b8835a4de1b5647cc4087c661`.
- Printed cover: `V2`. Filename version: `V2.0-2026-06-29`. The technical snapshot version is independent of these.
- Printed body p01–25 maps to PDF physical p3–27; p28's App reminder is retained. The printed cover artwork and paper TOC are omitted from Web flow; opening copy and identity remain native text.

## Reference and component map

Reference: `manual_sources/JE-1000F/JP/ja/git-20260930-d88b32fe-jp-reviewed`. Reuse its shared Web structure, never its product specifications or operating instructions.

| Printed content | Shared presentation |
| --- | --- |
| Safety signal definitions | HB-TABLE-SYMBOL-SIGNAL |
| Pictograms and recycling | HB-TABLE-SYMBOL-ICON |
| Warning / caution / App notes | HB-CALLOUT-STRIP |
| Inbox | HB-SPECIAL-INBOX |
| Front / left / right diagrams | HB-SPECIAL-REFERENCE-FIGURE with native positioned labels |
| LCD glossary | HB-TABLE-LCD-ICON, 27 rows; source number 23 spans two temperature rows |
| Power / AC / DC / LED operation | HB-SPECIAL-OPERATION; native footer instructions |
| Screen modes | HB-TABLE-LCD-MODE |
| Button combinations | HB-TABLE-KEY-COMBINATIONS, including native AC1 artwork |
| Output auto-resume | HB-TABLE-AUTO-RESUME |
| UPS / expansion / charging / App illustrations | HB-SPECIAL-REFERENCE-FIGURE |
| Fault codes | HB-TABLE-TROUBLESHOOTING |
| Specifications | Four HB-TABLE-SPEC groups |
| Warranty | HB-WARRANTY-LEAD / SECTION / YEARS |
| App add button | HB-SPECIAL-APP |
| Energy-saving thresholds | Declared plain semantic table; no registered power-threshold matrix fits |

The source's maximum five battery packs, independent AC1/AC2 controls, 2400W total output, 2048Wh capacity, 800W solar limit and Japanese 100V output come exclusively from this PDF.

## Frozen inputs and artwork

`source/document.json` holds the reviewed source flow. `native_pages.json`, `text_bindings.json`, `lcd_rows.json`, `text_coverage_review.json` and `asset_decisions.json` retain source coordinates and decisions. Shared symbols, LCD icons and matching buttons are byte-identical copies. AC1 is extracted from its native source button because generic AC has different silk.

Source-specific illustration crops use 3× direct PDF rendering: SVG export from this Illustrator PDF loses nested clipping and reveals unrelated hidden geometry. This affects illustration regions only; prose, labels, warnings and tables remain native HTML. The untouched original vector PDF is archived. Complete phone frames are retained. Independent empty caption frames are removed with fully-covered graphics removal and recreated by the shared caption carrier. `source/geometry.css` contains label geometry/typography only; the shared theme owns all paint.

## Rebuild and validation

Run from the repository root; output must be a new directory:

```bash
python3 manual_sources/JE-2000E/JP/ja/git-20261019-6a70e879-jp-native/rebuild.py --output tmp/je2000e-jp-replay
python3 -m sphinx -W -b html tmp/je2000e-jp-replay tmp/je2000e-jp-html
```

The adapter verifies frozen source/assets and pinned shared libraries before replaying with the existing Manual IR and Web consumers. It makes no network or online-table calls. `web/ja/` is the stored MyST/IR/CSS/assets candidate, and `validation/acceptance.json` records local verification.

The existing JP family check uses `JE-1000F` and fixture data as a repository regression gate only. The native JE-2000E body is validated separately through source parity, shared-style admission, strict Sphinx, cold replay, source/asset tamper rejection, and 1280px/390px browser checks. This is local candidate evidence; production and deployment acceptance remain pending operator review.
