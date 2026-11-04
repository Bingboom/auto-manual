# JHP-2000A US V2 — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- 发布文档管理 record `reczz28SlRGJkKmO` (子物料编码 16-0102-000349, 项目号 HTE152, 客户型号 JHP-2000A,
  sku 21-0001-000402 / 21-0001-000511), field 单语言说明书: 「【Jackery HomePower 2000 Plus】说明书-EN.pdf」,
  read-only bot download; 1,465,449 bytes, SHA-256 `5b60448e69a76d5a8386227bc800ffc83309c837dfc32f5b3fb1f0901bd3d738`
  (stored as `JHP-2000A-US-en-V2.pdf`).
- 24 portrait pages, 368.79 × 524.69 pt, written by pypdf as the English section of the electronic edition. It has a
  text layer (embedded Gilroy fonts; one full-width colon in AdobeSongStd-Light); product art and most button labels
  are vector paths; App screenshots on pages 22–23 are embedded raster images.
- p1 cover (Model: JHP-2000A, V2), p2 IMPORTANT, p3 paper table of contents, p4–p23 printed 01–20, p24 back cover.
- Field 说明书文件: 「16-0102-000349 Jackery HomePower 2000 Plus V2 Portable Power Station User Manual 电子版说明书.pdf」
  (Adobe Illustrator 30.4, 64 pages EN/FR/ES, 21,430,104 bytes, SHA-256
  `08bccf09606e37698d88bbe353843b99741fbe80858cf907d94021fc8330a82d`). It is the V2 electronic edition, not the print
  master. Identity reference only; not stored and no Web input is taken from it. Its English pages carry the same text
  as the authoritative PDF.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/JHP-2000A-RC/US/en/git-20261027-e27d4db5` (HomePower 2000 Plus Red Cross edition, same platform) | every panel (pixel difference of the same crop), LCD icon, button and symbol; its transcription for the line ids |
| `data/manual_sources/JHP-3600A/US/git-20261012-541ca8a5-reviewed`, `JHP-3000D`, `JHP-3600C`, `JHP-5000C` US | overview, LCD, operation, charging and App art |
| `docs/renderers/web/assets/shared/symbols/manifest.json` | all eleven safety symbols and the FCC mark, fixed 2% admission comparison |
| `docs/renderers/web/assets/shared/buttons/` | the four key-combination buttons |
| every `*lcd*` file under `data/manual_sources/` and `manual_sources/` and the shared SVGs (659 unique files) | the three LCD icons that differ from the RC edition |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| front view, LCD map, LCD screen, operation, UPS, battery stack, charging panels, in-box unit card | new complete panels from this PDF | the product drawing carries the HomePower 2000 Plus badge where the RC art shows the Red Cross mark; the LCD map prints different ⑮/㉓ icons | complete panel, leader lines and labels kept; body copy inside a panel is removed (text and text box) and set as native text |
| left/right views, in-box cable and documents cards, accessory strip, App badges, QR, screenshots, control-panel diagram | reuse the JHP-2000A-RC crops byte-identical | same drawing; the only pixel difference is label glyph rasterization (text layer vs outlined) | as the RC crops |
| 24 LCD icons, POWER / DC/USB / AC 1 / LIGHT buttons | reuse existing files byte-identical | ≤ 0.02 mean difference against this PDF's paths (LIGHT: live-text label, compared on 4× renders, 0.021) | transparent |
| battery-saving LCD icon | reuse `data/manual_sources/JE-3600A/JP/…/lcd-battery-saving-native.svg` | this edition's icon differs from the RC icon; 0.0038 against this PDF | transparent |
| high / low temperature LCD icons | native vector extraction | this edition prints a plain thermometer; closest existing file 0.12–0.14 | transparent, PDF paths only |
| eleven safety symbols, FCC mark | reuse existing shared catalog variants | each passes the fixed 2% admission; no catalog file added | transparent |

No body text or table is an image: all copy is native HTML from `transcription.json`.
