# JE-2000F US V2 — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- 发布文档管理 record `reczz28SlRGJiJNd` (子物料编码 16-0102-000409, 项目号 HTE154, SKU 21-0001-000575 / 21-0001-000625),
  单语言说明书 「【Jackery Explorer 2000】说明书-EN.pdf」, read-only download; 4,422,433 bytes,
  SHA-256 `c8ace563cc4575909156b4bcd224016fbd30cf9f8f077cd97738638f67e509e4` (stored as `JE-2000F-US-EN.pdf`).
- 22 portrait pages, 130 × 185 mm (368.8 × 524.7 pt). No text layer and no fonts: all copy is outlined vector paths;
  pages 20–22 also embed App screenshots and QR rasters.
- p1 cover (Model: JE-2000F, V2), p2 IMPORTANT preface, p3 paper TOC, p4–p21 printed 01–18, p22 back cover
  (Jackery Inc. address, phone, mail, web, QR).
- Print master 「16-0102-000409 说明书 A1 HTE1542000A-US-JAK RoHS REACH-转曲.pdf」 (39,454,027 bytes,
  SHA-256 `10a32677109540589a499da2afe59c8e9db3346756886d4a0094b1f7cf06e091`, 59 pages, outlined):
  identity reference only; not stored and not a Web input.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `data/manual_sources/JE-2000F/JP/ja/git-20261019-d10ae5e0/assets` (same model, JP) | overview, LCD icons and map, operation/charging panels, App frames, buttons, in-box art, symbols |
| `manual_sources/JE-2000F/EU/en/2.0/phase2/_attachments`, `manual_sources/JE-2000F/EU/nine-language/*/three-language/web/*/assets` (same model, EU; the shared review reference is the EU English Web) | LCD icons, symbols, panels |
| `manual_sources/*/US/en/git-20261027-*/assets` and their recorded origins (`data/manual_sources/JE-1500C/TW`, `JHP-5000C/US`, `JE-1000D`) | LCD icons, buttons, in-box art |
| `docs/renderers/web/assets/shared/symbols/manifest.json` | all twelve safety symbols and the FCC mark, fixed 2% comparison |
| `docs/renderers/web/assets/shared/buttons/` | POWER, AC, DC/USB, LIGHT buttons (none within 2% of this print) |

Every small icon was compared with every candidate file (332 unique LCD candidates) through
`tools.web.symbol_asset_admission.compare_symbol` against this PDF's own glyph paths.

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| front/right views, LCD map, operation, UPS, charging panels, in-box unit | new complete panels | JP/EU panels carry other plugs, ratings and label languages | complete panel, leader lines and labels kept; printed body copy inside five panels removed by vector strip and set as native Web text |
| App frames 2.1–2.5, control panel, QR | new crops | JP App screens are Japanese UI; the US print shows English UI | phone frames kept |
| App Store / Google Play badges | reuse JHP-3600A `shared-app-store.png` byte-identical | same badge pair (JHP-1000B-RC precedent) | badge art |
| POWER, AC, DC/USB buttons | reuse same-model JP `button-*.svg` | 0.003 / 0.008 / 0.009 mean error | transparent |
| LIGHT button | native vector extraction | no file within 2% (shared `led.svg` and JP `button-led.svg` fail) | transparent |
| AC cable, documents cards | reuse JE-1500D US `inbox-cable.svg`, JP `inbox-documents.svg` | 0.0195 / 0.0144 mean error | transparent |
| USB-C cable card | native vector extraction | no file within 2% | transparent |
| 23 LCD icons | reuse existing files byte-identical | each within 2% (0.002–0.017) | transparent |
| UPS, high- and low-temperature LCD icons | native vector extraction | no file within 2% | transparent |
| FCC mark | reuse shared `fcc/nested-c-native-dark` | 0.018 mean error | transparent |
| twelve safety symbols | reuse existing shared variants byte-identical | all pass the fixed 2% admission; no catalog file added | transparent |

No body text or table is an image: all copy is native HTML from `transcription.json`.
