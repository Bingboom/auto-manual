# JHP-1000B-RC US V2 — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- 发布文档管理 record `reczz28SPRx9mkta` (物料号 16-0102-000416, 项目号 HTE2607, SKU 21-0001-000519 / 21-0001-000624),
  单语言说明书 「【Jackery HomePower 1000 Plus】说明书-EN.pdf」, read-only bot download; 9,189,510 bytes,
  SHA-256 `af8a0775d0ba23a137fe024ae961c8b77f35797e1c8838a943ddbf8d418d9251` (stored as `JHP-1000B-RC-US-en-V2.pdf`).
- 22 portrait pages, 130 × 185 mm (368.8 × 524.7 pt). No text layer and no fonts: all copy is outlined vector paths;
  pages 20–22 also embed App screenshots and QR rasters.
- p1 cover (Model: JHP-1000B-RC, V2), p2 IMPORTANT preface, p3 paper TOC, p4–p21 printed 01–18, p22 back cover
  (Jackery Inc. address, phone, mail, web, QR).
- Design original 「16-0102-000416 说明书A1 HTE26071000A-US-JAK  RoHS REACH Q.pdf」 (查找引用, 39,217,681 bytes,
  SHA-256 `7c02cdfbe3329572d51ee7db8dfee5c251b5ed55839135e1847f4798a1957fd8`, 41 Illustrator artboard pages, outlined):
  identity reference only; not stored and not a Web input.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `data/manual_sources/JHP-3600A/US/git-20261012-541ca8a5-reviewed/assets` (reference edition) | overview, LCD icons and map, operation/charging panels, App badges/QR/frames, inbox art, buttons, FCC mark, symbols |
| `data/manual_sources/JHP-3000D/US/*/assets`, `data/manual_sources/JHP-5000C/US/*/assets`, `data/manual_sources/JHP-3600C/US` | LCD icon sets (`lcd-*`, `lcd-native-*`), panels |
| `manual_sources/*/*/*/*/assets/shared-lcd/` (26 unique files) | LCD icons |
| `docs/renderers/web/assets/shared/symbols/manifest.json` (76 variants) | all seven safety symbols, fixed 2% symbol admission |
| `docs/renderers/web/assets/shared/buttons/` | POWER, DC/USB, AC 1, LIGHT key-combination buttons |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| front/left/right views, LCD map, operation, UPS, battery-pack, charging panels | new complete panels | JHP-1000B-RC chassis, ports, ratings and numbering differ from every HomePower reference | complete panel, leader lines and labels kept; printed body copy inside five panels removed by vector strip and set as native Web text |
| App frames 2.1–2.5, control panel | new complete frames | HomePower 1000 Plus screens and step numbers | phone frames kept |
| App Store / Google Play badges | reuse JHP-3600A `shared-app-store.png` byte-identical | same badge pair | badge art |
| App QR | new crop | QR not assumed equal (10% pixel difference to the reference QR) | QR frame kept |
| in-box unit, cable, documents | new card art | reference is one combined 3600 Plus drawing | card art |
| FCC mark | reuse shared `fcc/nested-c-native-dark` | 0.018 mean error | transparent |
| LCD battery ring, F8 fault, 888V 88Hz readout | reuse JHP-5000C `lcd-native-17/21.svg`, JHP-3000D `lcd-24.png` | 0.007 / 0.010 / 0.017 mean error | transparent |
| other 24 LCD icons | native vector extraction | no existing file within 2% | transparent, PDF paths only (six 7-segment readouts keep their clip paths, not the clipped fill rectangles) |
| POWER, DC/USB buttons | reuse `shared/buttons/power.svg`, `dc_usb.svg` | 0.013 / 0.018 mean error | transparent |
| AC 1, LIGHT buttons | native vector extraction | shared `ac.svg` / `led.svg` faces differ (0.118 / 0.159) | transparent |
| seven safety symbols | reuse existing shared variants byte-identical | all pass the fixed 2% admission; no catalog file added | transparent |

No body text or table is an image: all copy is native HTML from `transcription.json`.
