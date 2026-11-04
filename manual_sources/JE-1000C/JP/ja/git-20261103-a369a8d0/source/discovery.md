# JE-1000C JP — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- Monolingual JP manual 「【Jackery ポータブル電源 1000 Plus】说明书-JP.pdf」 of record `reczz28SfbsHeXKZ`
  (子物料编码 38-0001-000371, 项目号 HTE103, sku 21-0001-000210); 3,609,066 bytes,
  SHA-256 `a369a8d0ac33d7f6d7843d404796f7eacfc69c221948318f81f6ca9d2311d9d3` (stored as `JE-1000C-JP-JA.pdf`).
- 14 portrait pages, 130 × 185 mm (367.1 × 523.0 pt), one shared Illustrator content stream clipped per page
  (~18,900 paths). No text layer and no fonts: all copy is outlined.
- p1 cover (JE-1000C, Jackery-UM-003, 国内専用), p2–p13 printed 1–12, p14 back cover (App text + store badges).
  There is no paper TOC and no warranty section (unlike JE-1000D JP V2).
- The print master 「38-0001-000371 HTE1031000A-JP-JAK 说明书 RoHS REACH-Q.pdf」 (14,686,431 bytes,
  SHA-256 `17deedc6…69cf3d`) is a reference only: not committed, not extracted.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/JE-1000D/JP/ja/git-20261026-00c43a89-v2/assets` | every panel, App art, LCD icons, recycle mark |
| `manual_sources/JE-1500D/JP/ja/git-20261019-6ddeef54-v2/assets` | in-box art, App art |
| `manual_sources/JE-1000F/JP/ja/git-20260930-d88b32fe-jp-reviewed/web/ja/assets` (shared-lcd set) | LCD ring and F8 glyphs |
| `docs/renderers/web/assets/shared/symbols/manifest.json` (95 variants, incl. #1632/#1640/#1641) | all six safety symbols, fixed 2% admission |
| `docs/renderers/web/assets/shared/buttons/` | not needed: no key-combination table is printed |

No other JE-1000C package exists in the repository.

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| overview, lcd-map, AC / SolarSaga / SolarSaga 80 / car charging, App button map | new complete panels | 1000 Plus chassis (DC 拡張ポート, 2× USB-C, シガーソケット出力ボタン), 18-position LCD and 1000 Plus captions differ from all references | complete panel, leader lines and captions kept |
| App 2.1/2.2 phone frames | reuse JE-1000D `app-add.png` byte-identical | same screenshots and captions | phone frames kept |
| App 2.3–2.5 phone frames | new complete phone frames | 2.5 shows Explorer 3000Pro here (JE-1000D: Explorer 1000) | phone frames kept |
| in-box unit, car adapter, pouch, manual, warranty card | new card crops | JE-1000C items not in the reference editions | card art |
| in-box AC cable | reuse JE-1500D `inbox-cable.svg` byte-identical | same JP cable drawing | transparent |
| LCD low battery, high temperature, Li-ion 32 mark | reuse JE-1000D SVG byte-identical | same glyphs (0.9–1.3% mean difference to this PDF's paths) | transparent |
| LCD battery ring, 12H, F8, low temperature | native vector extraction | no shared/reference glyph within 2% | transparent, PDF paths only |
| six safety symbols | reuse shared `native/je1000d-jp-00c43a89-01/02/03/05/06` and `mandatory/h1-jp-native` | all pass the fixed 2% admission (0.50%–1.42%) | transparent |

No body text or table is an image: all copy is native HTML from `transcription.json`.
No symbol is missing from the shared library; no shared catalog file is added.
