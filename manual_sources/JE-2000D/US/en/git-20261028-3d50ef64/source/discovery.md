# JE-2000D US en — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- 发布文档管理 record `reczz28SlRGJhr8p` (子物料编码 16-0102-000055, 项目号 HTE117; six SKUs in
  `source_manifest.json:base_record`), read-only.
- Authority: 「【Jackery Explorer 2000】说明书-EN.pdf」, 2,088,846 bytes,
  SHA-256 `3d50ef6490217a0893119567ef0d276f40b23d45e52e51560e97f724b6ca8c77`, stored as `JE-2000D-US-EN.pdf`.
  14 pages, 130 × 185 mm, pypdf-cut English section of the print master; no text layer and no fonts
  (every glyph outlined). The only rasters are the five App screenshots (p12–p13) and the back-cover QR.
- Print master (identity only, not committed, not read by any script):
  「16-0102-000055 HTE1172000A-US-JAK 说明书 RoSH REACH-Q.pdf」, 34,132,223 bytes,
  SHA-256 `a06040efc5393111b8aa2c0320ae2d3d1c0f27da5e1ccd0a07f71a6377dd96b2`, 48 pages.
- p1 cover (Jackery, V2, USER MANUAL, Jackery Explorer 2000, contact block, Model: JE-2000D),
  p2 CONTENTS (US English 01-11), p3–p13 printed 01–11, p14 back cover (JACKERY INC. address, contact line, QR).

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/JE-2000D/**` | none: no other region or language of this model has a Web edition |
| `manual_sources/JE-1000D/US/en/git-20261027-10d15090/assets` (Explorer 1000 v2, same V2 manual family) | every panel at the same source rectangle (3× render, mean channel error), every LCD icon and certification mark (fixed 2% glyph comparison) |
| `manual_sources/JE-2000A/US/en`, `JE-1500D/US/en`, `JE-1500B/US/en`, `JE-2000C/US/en`, `JHP-*-RC/US/en` | product, in-box and charging art: other chassis / older LCD; no same-art panel |
| `docs/renderers/web/assets/shared/symbols/manifest.json` | FCC (`fcc/nested-c-native-dark`), WEEE (`weee/crossed-bin-bar`, gray/JP/EU variants), battery-WEEE; no BC variant |
| `docs/renderers/web/assets/shared/lcd`, `shared/buttons` | no matching LCD glyph; no key-combination table is printed |
| every `manual_sources/**/assets/*fcc*` | all package FCC files are the catalog file (0.02219 against the p08 FCC paths) |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| LCD map, App Store/Google Play badges, App 2.1/2.2 phones, App button map, App 2.3–2.5 phones | reuse JE-1000D US files byte-identical | same art at the same rectangle (mean channel error 0.000005–0.0016; the App screenshots are the same embedded rasters) | complete panel / phone frames |
| overview (front + Right Side) | new complete panel | Explorer 2000 face (AC 2200W, model plate), Right Side inset | outlined LCD DISPLAY heading glyphs removed on an in-memory copy; the LCD map's ① stroke grazing the bottom edge painted white |
| in-box unit, cable, manual | new card art | Explorer 2000 unit and manual cover | card art |
| LED modes, AC/solar/car charging | new complete panels | Explorer 2000 chassis and captions | complete panel, captions kept |
| 8 LCD description icons | reuse JE-1000D US files byte-identical | pass fixed 2% (0.0054–0.0167) | transparent |
| FCC / WEEE marks (p01) | reuse shared catalog byte-identical | pass 2% (0.0179, 0.0066) | transparent |
| BC mark (p01) | reuse JE-1000D US native file byte-identical | no catalog variant; passes 2% (0.0100) | transparent |
| FCC mark (p08) | native PDF paths, package-local | catalog variant 0.0222 > 2%; certification mark, not a symbol table | transparent |
| safety symbols | not applicable | no symbol table printed | — |

No body text or table is an image: all copy is native HTML from `transcription.json`.
