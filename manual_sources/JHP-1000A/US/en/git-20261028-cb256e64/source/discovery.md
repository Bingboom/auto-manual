# JHP-1000A US V2 — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- 发布文档管理 record `reczz28SlRGJh40c` (子物料编码 16-0102-000344, 项目号 HTE158; SKU list in `source_manifest.json`),
  单语言说明书 「【Jackery HomePower 1000】说明书-EN.pdf」, read-only bot download; 4,478,879 bytes,
  SHA-256 `cb256e64ddf9a998f4717e3ec2b038b9ef7711572f7d9b752667f1d6e64077c1` (stored as `JHP-1000A-US-en-V2.pdf`).
- 21 portrait pages, 130 × 185 mm (368.8 × 524.7 pt). No text layer and no fonts: all copy is outlined vector paths;
  pages 19–20 also embed App screenshots and the QR raster.
- p1 cover (Model: JHP-1000A/JHP-1000A-WH, V2), p2 IMPORTANT preface, p3 paper TOC, p4–p20 printed 01–17,
  p21 back cover.
- 说明书文件 「16-0102-000344 HTE1581000A-US-JAK 说明书A1 RoHS REACH Q.pdf」 (52,588,323 bytes,
  SHA-256 `8995a1d58e44801868138feb09054bad110c9532237f0e7c493a59f59357f931`, 56 large Illustrator multi-artboard pages):
  identity reference only; not stored and not a Web input.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/JHP-1000B-RC/US/en/git-20261027-af8a0775/assets` (same-platform reference) | LCD icons, buttons, panels, App art |
| `manual_sources/JHP-2000A-RC/US/en/git-20261027-e27d4db5/assets`, `manual_sources/JHP-3600A-RC/US/en/*/assets` | LCD icons, buttons |
| `data/manual_sources/JHP-3600A/US/git-20261012-541ca8a5-reviewed/assets` (reference edition) | LCD icons, App badges, buttons, inbox, panels |
| `data/manual_sources/JHP-5000C/US/*/assets`, `data/manual_sources/JHP-3000D/US/*/assets` | LCD icon sets |
| `manual_sources/*/*/*/*/assets/shared-lcd/` | LCD icons |
| `docs/renderers/web/assets/shared/symbols/manifest.json` (81 variants, incl. the 2026-10-28 additions) | all seven safety symbols, fixed 2% symbol admission |
| `docs/renderers/web/assets/shared/buttons/` | POWER, DC/USB, AC, LIGHT key-combination buttons |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| front/right views, LCD map, operation, UPS, charging panels | new complete panels | HomePower 1000 chassis, three outlets, USB-C 100W and its ratings differ from every reference (incl. JHP-1000B-RC) | complete panel, leader lines and labels kept; body copy inside six panels removed by vector strip and set as native Web text |
| App frames 2.1–2.5, control panel | new complete frames | HomePower 1000 screens and control labels | phone frames kept |
| App Store / Google Play badges | reuse JHP-3600A `shared-app-store.png` byte-identical | same badge pair (as JHP-1000B-RC) | badge art |
| App QR | new crop | QR not assumed equal | QR frame kept |
| in-box unit, cable, documents | new card art | HomePower 1000 unit | card art |
| FCC mark | reuse shared `fcc/nested-c-native-dark` | same mark | transparent |
| 23 LCD icons | reuse JHP-1000B-RC / JHP-2000A-RC / JHP-5000C files byte-identical | each within the fixed 2% comparison against this PDF's paths (0.002–0.017) | transparent |
| 888V 88Hz readout, solar charging, F8 fault | native vector extraction | nearest existing files measure 0.053 / 0.021 / 0.025 | transparent, PDF paths only (the readout keeps its clip paths, not the clipped fill rectangles) |
| POWER, DC/USB, LIGHT buttons | reuse `shared/buttons/power.svg`, `dc_usb.svg`, `led.svg` | 0.012 / 0.011 / 0.013 mean error | transparent |
| AC1 button | native vector extraction | shared `ac.svg` prints 「AC」, this button 「AC1」 | transparent |
| six safety symbols | reuse existing shared variants byte-identical | pass the fixed 2% admission; no catalog file added | transparent |
| Li-ion symbol | reuse shared `li-ion/recycle-li-ion-label-dark-cb256e64` byte-identical | closest earlier variants `li-ion/recycle-li-ion-native-dark` 0.0233 and `li-ion/recycle-li-ion-label-hte162` 0.0246 exceeded 2%; the coordination window added this source-bound variant from p5 drawings 2194–2202 in PR #1640; no catalog file added here | transparent |

No body text or table is an image: all copy is native HTML from `transcription.json`.
