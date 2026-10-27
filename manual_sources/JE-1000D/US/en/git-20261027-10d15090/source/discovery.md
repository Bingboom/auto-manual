# JE-1000D US en — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- Feishu table record `reczz28SPRx9pE14` (物料号「文本」38-0001-000612, 项目号 HTE109; ten SKUs in
  `source_manifest.json:feishu_record`), read-only download.
- Authority: 「【Jackery Explorer 1000 v2】说明书-EN.pdf」, 1,116,478 bytes,
  SHA-256 `10d15090f944d3a0a1518e495dca4cf5cad15252220990c1b0e324564519316f`, stored as `JE-1000D-US-EN.pdf`.
  14 pages, 130 × 185 mm, pypdf-cut from the multilingual artwork; real text layer (Gilroy).
- Original artwork (reference only, not committed): 「38-0001-000612 Jackery Explorer 1000 v2 (1).pdf」,
  13,400,478 bytes, SHA-256 `572b54ea194e1edca2f3e6a9e57d13bdbbbcbddc5d4efb9c1bef688f4f2653a8`, 52 pages.
  Each EN page's whitespace-free text signature equals exactly one original page:
  EN 1 = original 1 (cover), EN 2–13 = original 3–14 (US section), EN 14 = original 52 (back cover).
  Original 2 is the four-language CONTENTS page; 15–26 FR, 27–38 ES, 39–50 PT (Brasil), 51 blank.
- Cover (EN 1): Jackery, V2, USER MANUAL, Jackery Explorer 1000, Model: JE-1000D, contact block.
  Body EN 2–13 printed 01–12. Back cover EN 14: JACKERY INC. address/contact line and QR.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/JE-1000D/JP/ja/git-20261026-00c43a89-v2/assets` (same model, reference edition) | every panel, in-box art, App art, LCD icons |
| `docs/renderers/web/assets/shared/symbols/manifest.json` | FCC, WEEE, battery-WEEE variants for the certification marks (fixed 2% comparison) |
| `docs/renderers/web/assets/shared/lcd`, `shared/buttons` | no matching LCD glyph; no key-combination table is printed |
| `docs/templates/word_template/common_assets/`, `docs/renderers/latex/assets/` | FCC / WEEE raster marks (catalog SVG/PNG preferred) |
| `manual_sources/*/US/en` | only JA-AD500A-SIL (an accessory): no Explorer art |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| overview, lcd-map, LED modes, AC/solar/car charging, App button map | new complete panels | English labels/captions, US outlets, different LCD numbering layout; no LED panel in JP | complete panel, leader lines and captions kept |
| App phone screenshots (2.1–2.5) | new complete phone frames | English App UI (JP is Japanese UI) | phone frames and 2.x captions kept |
| App Store / Google Play | new complete badge pair | JP stacks the badges vertically | badge pair kept |
| in-box unit, cable, manual | new | US outlets, US three-prong plug, English cover | card art |
| LCD low battery, high/low temperature, battery saving | reuse JE-1000D JP SVG byte-identical | pass fixed 2% (0.0090–0.0141) | transparent |
| LCD battery ring, 88H, F8, quiet charging | native vector extraction | JP candidates differ (0.028–0.214) or carry an opaque backdrop | transparent, PDF paths only |
| FCC mark (p2 and p10) | reuse shared `fcc/nested-c-native-dark` byte-identical | passes 2% (0.0183, 0.0193) | transparent |
| WEEE crossed bin with bar | reuse shared `weee/crossed-bin-bar` byte-identical | passes 2% (0.0146) | transparent |
| BC mark | native vector extraction (package-local) | no catalog variant; certification mark, not a symbol table | transparent |

The overview rectangle also covers the adjacent LCD DISPLAY heading at its lower left; only that
heading's text is removed from an in-memory copy of the page before rendering (the art is untouched).
There is no symbol table, so no symbol admission row and no shared catalog proposal.
No body text or table is an image: all copy is native HTML from `transcription.json`.
