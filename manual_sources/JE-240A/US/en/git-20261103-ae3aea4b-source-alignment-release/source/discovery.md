# JE-240A US English — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- 发布文档管理 record `reczz28SPRx9mSKQ` (物料号 38-0001-000443, 项目号 HTE110, SKU 21-0001-000212 / 21-0001-000493),
  field 单语言说明书 「【Jackery Explorer 240】说明书-EN.pdf」, read-only bot download; 4,694,209 bytes,
  SHA-256 `ae3aea4bcffa1c87f2de01cbe5c84792713a70eded1716039beb442e38a0a27f` (stored as `JE-240A-US-EN.pdf`).
- 14 pages, 130 × 185 mm, exported from one Illustrator artboard; no text layer (all copy outlined).
  p1 cover (V2), p2–p13 printed 01–12, p14 back cover (contact block, QR).
- Field 查找引用: Illustrator master 「38-0001-000443 HTE110256A-US-JAK 说明书 RoSH REACH 0312 Q.pdf」, 33,363,967 bytes,
  SHA-256 `407c638e27892ca1715a16ceda75fde83cfe5aa1c2b946ac10358bb4a751d464`. Recorded only (over the 32 MiB per-file limit).
- The shared native-SVG selector (`tools/asset_pipeline/native_svg.py`) cannot map this artboard's path stream
  (a fill/stroke pair closes one subpath with Z and the other with an explicit L to the origin), so no native
  vector extraction is used.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| repository-wide search for Explorer 240 / JE-240A / HTE110 assets | none exist (no other edition of this product) |
| `manual_sources/JE-1000F/JP/ja/git-20260930-d88b32fe-jp-reviewed/web/ja/assets/shared-lcd/` (27 icons) | the six LCD block icons, by semantic key and glyph |
| `docs/renderers/web/assets/je100c_eu_shared/lcd_*` | the six LCD block icons |
| `docs/renderers/web/assets/shared/lcd/`, `shared/buttons/` | no matching slot (special-mode icons; no key-combination table) |
| `docs/renderers/web/assets/shared/symbols/manifest.json` | FC mark; no symbol table is printed |
| App Store / Google Play crops in JE-1000D JP, JE-1500D JP, JE-2000E/F EU | same badges stacked vertically; the US print sets them side by side, so not reused |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| Battery Power Indicator ring, F8 fault code | reuse JE-1000F JP shared-lcd bytes | same glyph design (dashed ring; rounded triangle F8), as in JE-1000D JP | transparent |
| Low Battery, 88H Energy Saving, high/low temperature | new transparent crops (page rendered with alpha, no repaint) | different glyph designs: 88H in an oval, thick battery outline, thermometers inside a triangle | transparent |
| FC mark | reuse `fcc/nested-c-native-dark` | shared compliance mark | transparent |
| certification marks, package cards, product appearance, LCD map, AC/solar/car charging, App badges, App screenshots, App button map | new complete crops at 3× | no existing Explorer 240 art | complete panel; App phone frames kept; package-card ordinals cropped out |

No body text or table is an image: all copy is native HTML from `transcription.json`.
