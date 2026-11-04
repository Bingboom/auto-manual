# JE-3000B JP V2 — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- 发布文档管理 Base record `reczz28SfbsHfOgb` (子物料编码 38-0001-000822, 项目号 HTE116, SKU 21-0001-000294;
  客户型号 「JE-3000B 」 with a trailing space, used here as `JE-3000B`). Single-language PDF
  「【Jackery ポータブル電源 3000】说明书-JP.pdf」, 4,428,230 bytes,
  SHA-256 `2fd130d6cde89728d43492a90f4616a31c2066d65f13ccdc99fcd702ef11374c` (stored as `JE-3000B-JP-JA.pdf`).
  The print master 「38-0001-000822 HTE1163000A-JP-JAK  说明书 RoHS REACH-q.pdf」 (SHA-256 `2e48a1f8…2921`,
  19,071,068 bytes) is recorded only; it is not an extraction source and is not committed.
- 12 single portrait pages, 130 × 185 mm (not 2-up spreads). Every glyph is outlined except the ソーラー充電 block
  on physical page 6 (163 characters, NotoSansJP), which agrees with the render.
- p1 cover (JE-3000B, V2, 取扱説明書, 国内専用, support address, preface, QR); p2–p12 printed 1–11. No paper TOC,
  no back cover, no warranty chapter.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/JE-3000B/US/en/git-20261028-bd8a8296/assets` (same model) | every panel, in-box art, App art, 21 LCD glyphs |
| `manual_sources/JE-1000D/JP/ja/git-20261026-00c43a89-v2/assets` (same JP V2 template) | in-box, App badges/QR (1px offset search), LCD glyphs, Li-ion mark, symbols |
| `manual_sources/JE-1500D/JP/ja/git-20261019-6ddeef54-v2/assets` | in-box cable SVG, symbols |
| every committed `manual_sources/*/*/*/*/assets` SVG/PNG | fixed 2% glyph comparison for the ten LCD description icons and the Li-ion mark |
| `docs/renderers/web/assets/shared/symbols/manifest.json` | all six safety symbols, fixed 2% admission |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| overview, lcd-map, self-powered, AC/solar/car charging, App control | new complete panels | Japanese leader labels and captions; the US LCD map has a grey bezel, the JP print a line frame | complete panel, leader lines and captions kept |
| App phone screenshots (2.1–2.5) | new complete phone frames | Japanese screenshots with 2.x captions | phone frame kept |
| App badges (two crops), QR | new complete crops | printed target art; JE-1000D JP crop not reproducible at any 1px offset | badge pair / QR frame kept |
| in-box unit, cable, manual, warranty | new card crops | cable differs 4.1% from JE-1500D JP SVG; manual/warranty art is Japanese | card art |
| LCD battery ring, low battery, F8 fault, low temperature, quiet charging, self-powered, battery saving | reuse JE-3000B US glyph bytes | pass 2% (0.0062–0.0144) | transparent |
| LCD high temperature | reuse JE-1500D US `lcd-20a-high-temperature.svg` | passes (0.0165); the JE-3000B US file fails (0.0221) | transparent |
| LCD 88H energy saving, charging plan; Li-ion 32 mark | native vector extraction | no committed glyph within 2% | transparent, PDF paths only |
| six safety symbols | reuse shared `native/je1000d-jp-00c43a89-01/02/03/05/06` and `mandatory/h1-jp-native` | admission passes (0.0043–0.0147) | transparent |

Nothing was added to the shared catalog. No body text or table is an image: all copy is native HTML from
`transcription.json`.
