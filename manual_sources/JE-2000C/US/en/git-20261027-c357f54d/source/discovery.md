# JE-2000C US/en — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- 发布文档管理 Base, record `reczz28SPLqH8n46` (物料号 38-0001-000110, 项目号 HTE099, sku 21-0001-000036,
  客户型号 JE-2000C). 「单语言说明书」 attachment 「【Jackery Explorer 2000 Plus】说明书-EN.pdf」, read-only
  bot download; 2,769,777 bytes, SHA-256 `c357f54dfed27d11d72a2a4893e485450a49c1b562e21f0f272708857f1510ab`
  (stored as `JE-2000C-US-EN.pdf`).
- 「查找引用」 original 「38-0001-000110 说明书 HTE0992000A-US-JAK  ROSH REACH-2-q.ai」, 21,693,996 bytes,
  SHA-256 `9ff2337adbac8870c1574b9282f75f7698b894113e5e723e35c0d5eb5d93462d`: one 4870 × 3460 pt outlined
  Illustrator artboard. Recorded for identity only; not committed and not used for copy or art.
- 14 portrait pages, 368.5 × 524.4 pt (130 × 185 mm), all clipped from one shared content stream
  (69,451 drawings). No text layer and no fonts: all copy is outlined.
- p1 cover (Model: JE-2000C, Version: JAK-UM-V1.0), p2–p13 printed 01–12, p14 back cover
  (JACKERY INC. address and QR). There is no paper TOC.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/JE-2000E/EU/en/2.0/phase2/_attachments/` (lcd_icons, symbols) | LCD description icons |
| `manual_sources/JE-2000E/JP/ja/git-20261019-6a70e879-jp-native` and `.../EU/nine-language/*` | product, LCD, charging and App art of the 2000 Plus EU/JP editions |
| `manual_sources/JE-2000F/EU/nine-language/*` | App badges, charging art |
| `manual_sources/*/*/*/*/assets/shared-lcd/`, `docs/renderers/web/assets/shared/lcd/` | every shared LCD glyph (57 unique files) |
| `docs/renderers/web/assets/shared/symbols/manifest.json` | FCC mark (`fcc/nested-c-native-dark`) |
| `docs/renderers/web/assets/shared/buttons/` | not needed: no key-combination table is printed |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| certifications row, front/rear overview, LCD map, all charging and connection drawings | new complete panels | US JE-2000C chassis (NEMA 5-20 ×4 + TT-30 outlet, US labels); EU/JP 2000 Plus art shows other sockets and languages | complete panel, frames, ✕ marks, leader lines and captions kept |
| package-list card art (6) | new | JE-2000C items (car cable, AC cable, DC7909/DC8020 adaptor, accessories bag) as printed | card art |
| App Store / Google Play badges | new complete crop | the repository's badge crops are Japanese or localized EU badges | badge pair kept |
| LCD description icons (7) | native transparent render | no shared glyph matches: ring, outline battery, pill 88H, triangle-framed F8/thermometers and the two-socket AC expansion icon all differ in shape or ink colour (closest mean difference ≥ 0.13) | transparent PNG, 8× |
| FCC mark | reuse `fcc/nested-c-native-dark` byte-identical | same nested-C FCC glyph | transparent SVG |

No body text or table is an image: all copy is native HTML from `transcription.json`. The manual prints no
symbol-meaning table, so no symbol admission applies.
