# JE-1800A JP — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- 发布文档管理 record `reczz28SfbsHfSTa` (子物料编码 38-0001-000702, 项目号 HTE131), 「单语言说明书」 column:
  「【Jackery ポータブル電源 1800】说明书-JP.pdf」, read-only bot download; 3,650,317 bytes,
  SHA-256 `ccd8ebe25b3e5ab0a429ce0c4c4ffbe0fe47a34cee8bff3566228b3a9152ca91` (stored as `JE-1800A-JP.pdf`).
- 12 portrait pages, 130 × 185 mm (PDF creator "Manual portrait export"); every page shares one
  17,235-path content stream clipped per page. No text layer and no fonts: all copy is outlined.
- p1 cover (JE-1800A, 国内専用, no printed version mark), p2–p12 printed 1–11. No paper TOC or back cover.
- The 「说明书文件」 column holds the one-artboard Illustrator print master
  (「38-0001-000702 HTE1311800A-JP-JAK 说明书 RoHS REACHq.pdf」, SHA-256 `6960a73b…`); it is
  recorded for identity only and is not an extraction source.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/JE-1000D/JP/ja/git-20261026-00c43a89-v2/assets` (same layout generation) | every panel, in-box art, App art, LCD icons, Li-ion mark |
| `manual_sources/JE-1500D/JP/ja/git-20261019-6ddeef54-v2/assets` | in-box art, LCD icons, App art |
| `manual_sources/JE-1000F/JP/ja/git-20260930-d88b32fe-jp-reviewed/web/ja/assets/shared-lcd` | battery ring, fault code and the other LCD icons |
| `docs/renderers/web/assets/shared/symbols/manifest.json` (95 variants, incl. #1632/#1640 additions) | all six safety symbols, fixed 2% admission comparison |
| `docs/renderers/web/assets/shared/buttons/` | not needed: no key-combination table is printed |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| overview front, overview right side, lcd-map, AC/solar/car charging, App control | new complete panels | JE-1800A chassis, 2200W AC ports and captions differ from JE-1000D/JE-1500D | complete panel, leader lines and captions kept |
| overview | two panels (front, right-side circle) | the printed 4.液晶画面 heading shares the print band of the right-side circle, so one rectangle would cut into the heading | each panel complete |
| App phone screenshots (2.1–2.5) | new complete phone frames | Explorer 1800 device screens differ from the references | phone frame kept |
| App badges (two places), QR | new complete crops | printed target art; QR not assumed equal | badge pair / QR frame kept |
| in-box unit, cable, manual, warranty card | new | JE-1800A front, cover and 保証案内書 art; the four-card set differs from the three-card references | card art |
| LCD low battery, 88H, high/low temperature, battery saving | reuse JE-1000D JP native SVG bytes | pass the fixed 2% glyph comparison against this PDF's own paths (0.0084–0.0160) | transparent |
| LCD battery ring, F8 fault, quiet charging | native vector extraction | shared-lcd ring 0.214, shared F8 PNG has an opaque backdrop, JE-1000D quiet icon 0.0274 | transparent, PDF paths only |
| Li-ion 32 recycling mark | native vector extraction | no existing mark passes 2% (closest 0.137; the print tints the arrows) | transparent |
| six safety symbols | reuse shared variants (`native/je1000d-jp-00c43a89-01/02/03/05/06`, `mandatory/h1-jp-native`) | each passes fixed 2% admission (0.0049–0.0130); no new shared variant needed | transparent |

No body text or table is an image: all copy is native HTML from `transcription.json`.
