# JE-2000D JP ja (print model JE-2000D-SG) — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- 发布文档管理 record `reczz28SfbsHec2z` (子物料编码 38-0001-000766, 项目号 HTE117, sku 21-0001-000339,
  customer model JE-2000D-SG, the colour variant of JE-2000D), read-only. Route JE-2000D per operator decision 2026-11-03; it covers both colours.
- Authority: 「【Jackery ポータブル電源 2000】说明书-JP.pdf」, 3,664,234 bytes,
  SHA-256 `62605f215fe45b9ab600b44be336e217d854292e14921833b0d26e51a665709f`, stored as `JE-2000D-JP-JA.pdf`.
  12 single portrait pages, 129.5 × 184.5 mm (PDF metadata: 'Manual portrait export', 'Japanese section only;
  source artwork and printed page numbers retained'); no text layer and no fonts (every glyph outlined). The only
  rasters are the App screenshots (physical 11–12), the QR codes and the badge art.
- Print master (identity only, not committed, not read by any script):
  「38-0001-000766 HTE1172000A-JP-JAK 沙金色 说明书 RoHS REACHq.pdf」, 14,463,688 bytes,
  SHA-256 `53abd4ee70c6a3ca49f0ca6920b8d331473128bb7dd2c9f2792e3f40ea921348`.
- p1 cover (Jackery ポータブル電源 / JE-2000D-SG / V2, product drawing, 取扱説明書, 国内専用, support address,
  reading notes, QR); p2–p12 printed 1–11. No TOC, no back cover, no warranty chapter.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/JE-2000D/US/en/git-20261028-3d50ef64` (same model, US English) | every LCD icon (fixed 2% glyph comparison); panels by rectangle size (all labels English, different rectangles) |
| `manual_sources/JE-1000D/JP/ja/git-20261026-00c43a89-v2` (JP V2 manual family) | App badges, QR, 2.1/2.2 phones, button map and 2.3–2.5 phones by 3× render at the best 0.1–0.5 pt alignment; LCD icons and Li-ion 32 mark (2% glyph comparison); in-box cable SVG |
| every `manual_sources/**/assets` glyph | each LCD icon and the recycling mark against all package glyphs |
| `docs/renderers/web/assets/shared/symbols/manifest.json` | the six 絵表示の説明 symbols, framed like the JE-1000D JP V2 rows |
| `docs/renderers/web/assets/shared/lcd` | no better LCD glyph than the package files |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Measured | Background |
| --- | --- | --- | --- |
| battery ring, low battery, fault code, high/low temperature, quiet charging, battery saving | reuse JE-2000D US files byte-identical | 0.0073–0.0198 | transparent |
| 88H energy saving | reuse JE-1000D JP V2 file byte-identical (JE-2000D US 88H measures 0.143) | 0.0178 | transparent |
| Li-ion 32 recycling mark | native PDF paths, package-local (JE-1000D JP V2 file 0.0214 > 2%) | — | transparent |
| 6 safety symbols | reuse shared catalog files (5 JE-1000D JP V2 variants + `mandatory/h1-jp-native`) | 0.0035–0.0132 | transparent |
| App badges / QR / phones / button map | new complete panels (JE-1000D JP files 0.015–0.131; 2.5 shows Explorer 2000) | — | complete panel, phone frames |
| overview, LCD map, in-box ①–④, AC / solar / car charging, p09 badge pair | new complete panels at 3× | — | complete panel, captions kept |

Nothing was added to the shared symbol library. No body text or table is an image: all copy is native HTML from
`transcription.json`.
