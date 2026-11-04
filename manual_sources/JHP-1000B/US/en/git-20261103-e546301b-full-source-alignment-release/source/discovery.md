# JHP-1000B US V2 — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- 发布文档管理 record `reczz28SlRGJi0KB` (子物料编码 16-0102-000489, 项目号 HTE159), 单语言说明书
  「【Jackery HomePower 1000 Plus】说明书-EN.pdf」, read-only bot download; 4,881,012 bytes,
  SHA-256 `e546301b5cba7a6774418544a74c689f69712fd0fac6189df016f8020c0d98b1` (stored as `JHP-1000B-US-en-V2.pdf`).
- 22 portrait pages, 130 × 185 mm (368.8 × 524.7 pt). No text layer and no fonts: all copy is outlined vector paths;
  pages 20–21 also embed App screenshots and QR rasters.
- p1 cover (Model: JHP-1000B/JHP-1000B-WH, V2), p2 IMPORTANT preface, p3 paper TOC, p4–p21 printed 01–18, p22 back cover.
- Print master 「16-0102-000489 说明书A1 HTE1591000A-US-JAK RoHS REACH-q.pdf」 (说明书文件, 58,428,645 bytes,
  SHA-256 `f5b9502defb9ec9d62de0fd78e27d3e849f4813670f76800e5086cb529873477`, 59 large multi-language artboards):
  identity reference only; not stored and not a Web input.
- Same platform and layout as JHP-1000B-RC (`manual_sources/JHP-1000B-RC/US/en/git-20261027-af8a0775`): vector geometry
  of pages 5, 8, 9 and 20 is identical; other pages differ by the nameplate (HomePower 1000 Plus badge instead of the
  American Red Cross mark), the p6 FCC/in-box layout, the p13 key-combination table position and a 7 pt shift of p16.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/JHP-1000B-RC/US/en/git-20261027-af8a0775/assets` (same platform, searched first) | every slot; byte comparison of the recipe output and pixel comparison of panels |
| `data/manual_sources/JHP-3600A/US/git-20261012-541ca8a5-reviewed/assets` (reference edition) | overview, LCD icons and map, operation/charging panels, App badges/QR/frames, inbox art, buttons, FCC mark, symbols |
| `data/manual_sources/JHP-3000D/US/*/assets`, `data/manual_sources/JHP-5000C/US/*/assets`, `data/manual_sources/JHP-3600C/US` | LCD icon sets (`lcd-*`, `lcd-native-*`), panels |
| `manual_sources/*/*/*/*/assets/shared-lcd/` (26 unique files) | LCD icons |
| `docs/renderers/web/assets/shared/symbols/manifest.json` (76 variants) | all seven safety symbols, fixed 2% symbol admission |
| `docs/renderers/web/assets/shared/buttons/` | POWER, DC/USB, AC 1, LIGHT key-combination buttons |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| front view, LCD SCREEN art, POWER/AC/DC-USB/LED/energy-saving panels, UPS, battery stack, AC/solar/car charging panels, in-box unit | new complete panels from this PDF | the drawn unit carries the HomePower 1000 Plus nameplate where JHP-1000B-RC prints the American Red Cross mark | complete panel, leader lines and labels kept; printed body copy inside five panels removed by vector strip and set as native Web text |
| in-box USB-C cable | new card art | only this edition ships the USB-C cable; no existing card matches (JE-1500C TW `inbox-usbc.svg` is a different drawing) | card art |
| left/right views, LCD map, App QR, App 2.1/2.2 frames, control panel, 24 LCD icons | derived by the recipe; byte-identical to the JHP-1000B-RC files | same vector art at the same position | as JHP-1000B-RC |
| in-box AC cable and documents, App 2.3–2.5 frames, battery accessories, AC 1 and LIGHT buttons | reuse JHP-1000B-RC files byte-identical | same vector art, only moved on the page (or sub-pixel anti-aliasing) | as JHP-1000B-RC |
| App Store / Google Play badges, FCC mark, battery ring, F8 fault, 888V 88Hz readout, POWER and DC/USB buttons | reuse the same files JHP-1000B-RC reuses | unchanged art | transparent / badge art |
| seven safety symbols | reuse existing shared variants byte-identical | all pass the fixed 2% admission (max 0.0183); no catalog file added | transparent |

No body text or table is an image: all copy is native HTML from `transcription.json`.
