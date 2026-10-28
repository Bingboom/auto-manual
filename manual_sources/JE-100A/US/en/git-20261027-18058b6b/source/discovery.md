# JE-100A US English — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- 发布文档管理 record `reczz28SPRx9qFmY` (物料号 38-0001-000552, 项目号 HTE106, SKU 21-0001-000289 / 21-0001-000171 / 21-0001-000495),
  field 单语言说明书 「【Jackery Explorer 100 Plus】说明书-EN.pdf」, read-only bot download; 2,740,985 bytes,
  SHA-256 `18058b6bb7e83041fce1798f3baf98a018d079fa5caa6fd8dceec934df02c0b5` (stored as `JE-100A-US-EN.pdf`).
- 10 pages, 90 × 130 mm, exported from one Illustrator artboard ("Manual English PDF export"). No text layer: all copy is outlined.
  p1 cover, p2–p9 printed 01–08, p10 contact page (JACKERY INC., JACKERY MEXICO S.A. DE C.V., QR).
- Field 查找引用: Illustrator master 「38-0001-000552 HTE106100A-US-JAK 说明书 20240428 Q.pdf」, 20,264,889 bytes,
  SHA-256 `395501d356f3f30e3a421e2d5bb4eb4ba8f99acafa8462eebe2a9eb62df75ed1` (one artboard). Recorded only.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/**`, `data/manual_sources/**`, `docs/renderers/web/assets/**` (grep `100 Plus`, `JE-100A`, `HTE106`) | no Explorer 100 Plus artwork exists |
| `docs/renderers/web/assets/je100c_eu_shared/lcd_*.png`, JE-1000F / JE-1500D / JE-1000D `shared-lcd/` | the seven LCD icons, side by side |
| `docs/renderers/web/assets/shared/lcd/`, `shared/buttons/` | no matching slot (no key-combination table) |
| `docs/renderers/web/assets/shared/symbols/manifest.json` | FC mark; no symbol table is printed |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| certifications, package-list art, product appearance, LCD map, wall / solar ×3 / car charging | new complete panels at 3× | no Explorer 100 Plus art in the repository | complete panel, leader lines and captions kept |
| F8 fault code icon | reuse JE-1000F shared-lcd bytes | same glyph | transparent |
| battery ring, low battery, always-on, 12H, high / low temperature | new transparent 6× glyph renders | no shared glyph matches | transparent (alpha render; nothing keyed out) |
| FC mark | reuse `fcc/nested-c-native-dark` | shared compliance mark | transparent |

Native vector extraction is not used: the shared native-SVG selector cannot map this single-artboard export.
No body text or table is an image: all copy is native HTML from `transcription.json`.
