# JE-2000C JP — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- 发布文档管理 Base record `reczz28SfbsHdjSC` (子物料编码 38-0001-000384, 项目号 HTE099,
  sku 21-0001-000211). 「单语言说明书」 「【Jackery ポータブル電源 2000 Plus】说明书-JP.pdf」,
  2,331,963 bytes, SHA-256 `88b78332342866ccd994cfa054a8a63a5fe30fa41131de5c7d53f16cd590690b`,
  stored byte-exact as `JE-2000C-JP.pdf`. Print master 「说明书文件」 recorded by name and hash only.
- 16 portrait pages, 130 × 185 mm, pypdf export of the Illustrator layout, with a real text layer
  (Noto Sans JP DemiLight/Medium/Bold, Segoe UI Symbol for ⎓). 545 native text lines; every one is
  bound or excluded in `line_map.json`.
- p1 cover (JE-2000C, Jackery-UM-002, 国内専用); no paper TOC; p2–p15 printed 1–14; p16 back cover
  (App download copy, store badges, QR).

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/JE-2000C/US/en/git-20261027-c357f54d/assets` (same model) | every panel, in-box card and the seven LCD description icons |
| `manual_sources/JE-1000D/JP/ja/git-20261026-00c43a89-v2/assets` | structure, symbols, recycle mark, App art |
| `manual_sources/JE-1500D/JP/ja/git-20261019-6ddeef54-v2/assets` | in-box cable, App art |
| `docs/renderers/web/assets/shared/symbols/manifest.json` (all SVG variants, incl. #1632/#1640/#1641) | all six safety symbols, fixed 2% admission comparison |
| `docs/renderers/web/assets/shared/buttons/` | not needed: no key-combination table is printed |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| overview, lcd-map, charging/solar/car panels, certifications | new complete panels | the US/en panels of the same chassis carry English labels/captions; JP LCD numbering differs | complete panel, frames, leader lines and captions kept |
| App screenshots (2.1–2.5), App button map, store badges, QR | new complete crops | JP screenshots and labels; QR not assumed equal | phone frames kept |
| in-box cards ①–⑥ | new | JP cable/pouch/manual/warranty art; one source and scale for the set | card art |
| LCD fault code, low temperature | reuse JE-2000C US/en files byte-identical | pass the fixed 2% comparison (0.0086, 0.0120) | transparent |
| LCD battery ring, low battery, 88H, high temperature, AC expansion | native vector extraction | US/en files differ (0.021–0.415) or show a different glyph (12H) | transparent, PDF paths only |
| recycle arrows | native vector extraction | the Li-ion 32 label is real text here | transparent |
| six safety symbols | reuse shared variants (`native/je1000d-jp-00c43a89-01/02/03/05/06`, `mandatory/h1-jp-native`) | each passes the fixed 2% admission (0.0046–0.0168) | transparent |

No shared catalog file was added or changed. No body text or table is an image.
