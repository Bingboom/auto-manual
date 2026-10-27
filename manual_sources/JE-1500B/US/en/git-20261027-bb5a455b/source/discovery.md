# JE-1500B US (Explorer 1500 Pro) — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- Feishu record `reczz28SPLqH7mCa`: 物料号「文本」38-0001-000307, 项目号 HTE080, SKU 21-0001-000130.
  Operator decision 「JE-1500B 用 38-0001-000307，000208 不出网页」: 38-0001-000208 is not converted.
- Authoritative PDF 「【Jackery Explorer 1500 Pro】说明书-EN.pdf」, 3,868,124 bytes,
  SHA-256 `bb5a455b5c3e03b70ee95d6d6ceb74a9c98b671addc1d30d9637f9bb974a7dbb` (stored as `JE-1500B-US-EN.pdf`).
- 11 portrait pages, 130 × 185 mm (368.5 × 524.4 pt), exported from one Illustrator artboard: every page
  shares the same 100,022-drawing content stream, clipped per page. No text layer and no fonts.
- p1 cover (Model: JE-1500B, USER MANUAL, Jackery Explorer 1500 Pro, Version: JAK-UM-V1.0), p2–p10 printed
  01–09, p11 back cover (JACKERY INC. address and QR).
- Original artwork 「38-0001-000307 说明书  HTE0801500B-US-JAK 说明书  ROHS REACH Q.pdf」 (28,862,996 bytes,
  SHA-256 `5437c53265ec585e98623df371c7f733c050d3117cc87d53d9bc886e8bc47c9a`): one 5888 × 4138 pt artboard,
  outlined, no text layer. Reference only; not committed (size) and not needed, because the PDF holds the same
  vector art.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/JE-1000D/JP/ja/git-20261026-00c43a89-v2/assets` | LCD icons (native SVG), panels |
| `manual_sources/JE-1500D/JP/ja/git-20261019-6ddeef54-v2/assets` | in-box art (JP two-prong cable), LCD, charging panels |
| `manual_sources/JE-1000F/JP/ja/git-20260930-d88b32fe-jp-reviewed/web/ja/assets/shared-lcd` (26 icons) | all six LCD description icons |
| `docs/renderers/web/assets/shared/lcd`, `shared/buttons`, `shared/symbols/manifest.json` | LCD icons; no key-combination or symbol table is printed |
| `manual_sources/JE-2000E/**`, `manual_sources/JBP-3600A/**` in-box art | EU plugs / other products |
| `docs/templates/word_template/common_assets/`, `docs/renderers/latex/assets/` | no Explorer Pro, FCC or certification-row art |

No Explorer 1500 Pro (or other Explorer Pro) Web edition exists in the repository; the sibling JE-2000A
package was in progress in parallel and is not a reuse source.

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| overview, lcd-map, AC / solar (5) / car charging panels | new complete panels | Explorer 1500 Pro chassis, ports, LCD and English captions differ from all references | complete panel, frames, leader lines and captions kept |
| certification-mark row, FCC logo | new complete crops | no committed asset | panel kept |
| five package-list cards | new | Explorer 1500 Pro unit and guide; US three-prong cable; car cable and DC7909 adaptor not in the repository | card art |
| LCD low battery, high / low temperature | reuse JE-1000D JP V2 native SVGs byte-identical | same glyph and tint (0.0107 / 0.0086 / 0.0122 mean error at the fixed 2% tolerance) | transparent |
| LCD battery ring, 12H Low Power Mode, F8 fault code | native vector extraction | no committed glyph within 2% (closest 0.13 / 0.22 / 0.10) | transparent, PDF paths only |

No body text or table is an image: all copy is native HTML from `transcription.json`.

## Shared native SVG selector

`tools.asset_pipeline.native_svg.native_symbol_svg` refuses every page of this PDF: the page SVG holds
17 zero-length `M x yZ` paths that `get_drawings()` omits, and 36 off-page fill/stroke pairs whose two SVG
paths close differently. `derive_assets.py` therefore writes the selected `get_drawings()` paths directly
(same completeness rule: every drawing inside the glyph box). No symbol table is printed, so symbol
admission (which uses that selector) has no rows here. A future symbol-bearing manual from the same
artboard would need the shared selector to tolerate these paths.
