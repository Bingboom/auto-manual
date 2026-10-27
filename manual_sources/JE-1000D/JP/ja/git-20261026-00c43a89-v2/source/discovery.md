# JE-1000D JP V2 — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- Feishu wiki file 「Jackery ポータブル電源 1000说明书.pdf」, node `Twlbwt4gGiGVE6k5hqBcDezanKg`,
  obj_token `XlavbKiqToHuIox0xTPcjdQKnhd`, read-only bot download; 3,861,611 bytes,
  SHA-256 `00c43a89bd07babbea3a82b6bfbbc4a1c7b52f7a72cb8030b0dbfb349de601a4` (stored as `JE-1000D-JP-V2.pdf`).
- 18 portrait pages, 130 × 185 mm, exported from one Illustrator artboard (every page shares the
  same 18,957-path content stream, clipped per page). No text layer and no fonts: all copy is outlined.
- p1 cover (JE-1000D, V2, 国内専用), p2 目次, p3–p17 printed 01–15, p18 back cover (QR only).

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/JE-1500D/JP/ja/git-20261019-6ddeef54-v2/assets` | every panel, in-box art, App art, LCD icons |
| `manual_sources/JE-1000F/JP/ja/git-20260930-d88b32fe-jp-reviewed/web/ja/assets` | overview, LCD, charging, App, symbols |
| `docs/renderers/web/assets/shared/symbols/manifest.json` (71 variants) | all six safety symbols and the Li-ion mark, fixed 2% admission comparison |
| `docs/renderers/web/assets/shared/buttons/` | not needed: no key-combination table is printed |
| `shared-lcd/` icon set (JE-1000F/JE-1500D) | inked-shape comparison of the nine LCD description icons |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| overview, lcd-map, ac/solar/car charging, App control | new complete panels | JE-1000D chassis, ports, LCD layout and captions differ from both references | complete panel, leader lines and captions kept |
| App phone screenshots (2.1–2.5) | new complete phone frames | target crop with 2.x captions; JE-1500D crops differ in scale and show 1500 New | phone frame kept |
| App badges, QR | new complete crops | printed target art; QR not assumed equal | badge pair / QR frame kept |
| in-box unit, manual | new | JE-1000D front and cover | card art |
| in-box AC cable | reuse JE-1500D `inbox-cable.svg` byte-identical | same JP cable drawing | transparent |
| LCD battery ring, F8 fault | reuse shared-lcd bytes | same glyph (ring 0.011 mean difference; F8 triangle) | transparent |
| LCD low battery, 88H, high/low temperature, quiet charging, battery saving | native vector extraction | no shared glyph matches (≥0.12 mean difference) | transparent, PDF paths only |
| Li-ion 32 recycling mark | native vector extraction | no shared variant passes 2% | transparent |
| 行為を指示する記号 | reuse `mandatory/h1-jp-native` | passes admission (0.0152) | transparent |
| other five symbols | new shared native variants `native/je1000d-jp-00c43a89-0N` (append-only) | closest existing 5.0%–14.3% | transparent |

No body text or table is an image: all copy is native HTML from `transcription.json`.
