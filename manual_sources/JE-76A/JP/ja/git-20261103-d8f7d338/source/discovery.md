# JE-76A JP — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- 发布文档管理 record `reczz28SfbsHcnhM` (子物料编码 38-0001-000723, 项目号 HTE125, SKU 21-0001-000310 / 21-0001-000309),
  field 单语言说明书 「【Jackery Power Bank】说明书-JP.pdf」, read-only bot download; 1,421,229 bytes,
  SHA-256 `d8f7d338fd208af056c0dda9991422227627ab771245e791858e1480978b013c` (stored as `JE-76A-JP-JA.pdf`).
- 14 pages, 89 × 130 mm, "Manual portrait export". No text layer: all copy is outlined.
  p1 cover (models JE-76A / JE-76A-WH, support address, greeting, QR), p2–p14 printed 1–13. There is no paper TOC and no back cover.
- Field 说明书文件: print master 「38-0001-000723 说明书 HTE12576A-JP-JAK RoHS REACH Q.pdf」, 6,803,590 bytes,
  SHA-256 `21b709ed680790ccaec98da922b49f970ec28e45aebbd80e939f0953f7a1a222`. Recorded only; not an extraction source.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/**`, `data/manual_sources/**`, `docs/renderers/web/assets/**` (grep `JE-76A`, `HTE125`, `Power Bank`) | no Jackery Power Bank artwork exists in the repository |
| `docs/renderers/web/assets/shared/symbols/**` (every SVG, fixed 2% glyph comparison) | Li-ion recycling mark: best 0.0975 (no match); warning triangle: best 0.196 (no match) |
| `manual_sources/*/*/*/*/assets/*lcd*/*battery*/*recycle*` SVGs | % glyph best 0.28, charging-lamp glyph best 0.18 (no match) |
| `docs/renderers/web/assets/shared/lcd/`, `shared/buttons/` | no matching slot |
| JE-1000D JP V2 `recycle-li-ion.svg` | different mark (Li-ion 32) |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| 認証 marks, 同梱品 card art ①–④, 使用製品 drawing, LCD display, charging station, USB-C charging, FF panel | new complete panels at 3× | no Power Bank art in the repository | complete panel, leader lines and letters kept |
| % and charging-lamp LCD glyphs, Li-ion recycling mark | new native PDF vector paths (shared `native_symbol_svg`) | no shared or package glyph matches | transparent |
| 警告/注意 item pictograms, FF warning triangle | not used on the Web | the print has no symbol table; each item's bold title carries its meaning | — |

No symbol table is printed, so the package has no symbol admission rows and adds nothing to the shared symbol library.
No body text or table is an image: all copy is native HTML from `transcription.json`.
