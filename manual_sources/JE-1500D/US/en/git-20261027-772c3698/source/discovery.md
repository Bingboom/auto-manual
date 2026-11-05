# JE-1500D US V2 — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- 「【Jackery Explorer 1500】说明书-EN.pdf」 from 发布文档管理 record `reczz28SPRx9ntZO`
  (物料号「文本」38-0001-000943, 项目号 HTE140), read-only; 6,071,419 bytes,
  SHA-256 `772c36987b4233c2c243d64cf0a2e9c8a3fd1f37ad87ad739600cbf474977a79` (stored as `JE-1500D-US-EN.pdf`).
- 21 portrait pages, 130 × 185 mm, one Illustrator artboard: every page carries the same
  187,134-path content stream, clipped per page. No text layer and no fonts: all copy is outlined.
- p1 cover (Model: JE-1500D, V2, USER MANUAL, Jackery Explorer 1500), p2 IMPORTANT (EN), p3 TABLE OF CONTENTS,
  p4–p20 printed 01–17, p21 back cover (JACKERY INC. address, contact, QR).
- The original print artwork 「38-0001-000943 说明书 HTE1401500A-US CA-JAK  RoHS REACH.pdf」
  (30,322,591 bytes, SHA-256 `07dcaa43cb2707334a3dcd086be6011cec528f02a6776c86f3d1c1872598c709`) was used only as a reference; it is not committed.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/JE-1500D/JP/ja/git-20261019-6ddeef54-v2/assets` (same product, JP) | every panel, LCD map, in-box art, App art, shared LCD icons and buttons; aligned 3x raster comparison against this PDF |
| `manual_sources/JE-1000D/JP/ja/git-20261026-00c43a89-v2/assets`, `manual_sources/JE-1000F/JP/…/shared-lcd` | LCD icons, in-box cable |
| `manual_sources/**/shared-lcd/*.png`, `docs/renderers/web/assets/shared/lcd/` (35 files) | the 24 LCD description icons, fixed 2% glyph comparison against the native paths |
| `docs/renderers/web/assets/shared/symbols/manifest.json` (76 variants) | all 11 safety symbols and the FCC mark, fixed 2% symbol admission comparison |
| `docs/renderers/web/assets/shared/buttons/` | POWER (label above), DC/USB and AC (labels below) for the key-combination table |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| LCD map (numbered ①–㉓) | reuse JE-1500D JP `lcd-map.png` byte-identical | same LCD and numbering; aligned difference 0.0102 mean, 0.7% pixels (antialiasing) | complete panel |
| front / right overview, operation panels, UPS, charging panels | new complete panels | English leader labels and ratings, US outlets; JP panels carry Japanese labels or text boxes (mean difference 0.03–0.20) | complete panel, leader lines and labels kept; grey text pills/bubbles omitted (vector objects removed) and set as native text |
| LCD SCREEN artwork | new | JP `lcd-button.png` is the same drawing at a different scale/crop; not reusable bytes | as printed |
| App phone screenshots 2.1–2.5, App button map | new complete phone frames / panel | English UI and labels (JP crops show Japanese UI) | phone frames kept |
| App badges, QR | new complete crops | JP crops are clipped and bleed neighbouring Japanese text | badge pair / QR frame kept |
| in-box unit, manual | new | US manual cover; JP unit crop does not align (0.17 mean) | card art |
| in-box AC cable | native vector extraction | US three-prong plug; the JP shared cable is a two-prong JP plug | transparent |
| 24 LCD description icons | native vector extraction | no shared LCD glyph within 2% (closest 0.08–0.53): the shared set differs in outline (rounded frames, triangles, 8.8 H vs 88H) | transparent, PDF paths only |
| FCC mark | reuse `fcc/nested-c-native-dark` | passes admission (0.0176) | transparent |
| key-combination buttons | reuse shared `button/power`, `button/dc_usb`, `button/ac` | same label placement as printed | transparent |
| 10 safety symbols | reuse shared catalog variants (see `source_manifest.json:symbol_asset_admission`) | pass the fixed 2% admission (0.0066–0.0161) | transparent |
| Heavy object symbol | reuse shared `heavy-object/person-load-triangle-dark-772c3698` (added by #1632 from this PDF's native paths) | closest pre-existing `heavy-object/person-load-triangle-tinted` 0.0244 failed 2% | transparent |

No body text or table is an image: all copy is native HTML from `transcription.json`.
