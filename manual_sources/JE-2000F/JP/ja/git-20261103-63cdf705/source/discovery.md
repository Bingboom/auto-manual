# JE-2000F JP — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- 发布文档管理 record `reczz28SfbsHbLFx` (子物料编码 16-0102-000408, 项目号 HTE154, SKU 21-0001-000489 /
  21-0001-000441 / 21-0001-000442): single-language attachment 「【Jackery ポータブル電源 2000 New】说明书-JP.pdf」,
  2,449,451 bytes, SHA-256 `63cdf705e41a1680ca974cc69e5f233cd0e5e4d278d5cc5302dcb3389b361393`, stored as
  `JE-2000F-JP-JA.pdf` (customer model of the record: JE-2000F-WH; route JE-2000F per operator decision
  2026-11-03). The print master 「16-0102-000408 竖版说明书 HTE1542000A-JP-JAK.pdf」 is recorded by name,
  size and hash only.
- 27 single portrait pages, 130 × 185 mm, with a real text layer (NotoSansJP / Gilroy). p1 cover (JE-2000F /
  JE-2000F-SG / JE-2000F-WH, 国内専用), p2 目次, p3–p26 printed 01–24, p27 back cover (App promotion + QR).
- Earlier unreleased candidate git-20261019-d10ae5e0 voided by operator 2026-11-03 (it was built from a 28-page PDF
  with the same text page for page). No file of it is reused.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/JE-2000F/US/en/git-20261028-c8ace563/assets` | 26 LCD icons, 4 buttons, in-box cards, App badges, panels |
| `data/manual_sources/JE-2000F/JP/ja/git-20261019-d10ae5e0/assets` (voided) | compared during inventory only; no file reused |
| `manual_sources/*/*/*/*/assets/*cable*.svg` | in-box AC cable |
| `manual_sources/JE-1500D/JP/ja/git-20261019-6ddeef54-v2/assets/shared-lcd` | LCD icons that the US files do not match |
| `manual_sources/JE-1000D/JP/ja/git-20261026-00c43a89-v2/assets` | Li-ion mark, LCD icons |
| `docs/renderers/web/assets/shared/symbols/manifest.json` (95 variants) | all 13 printed marks, fixed 2% comparison |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| overview, LCD map, operation, frequency, energy-saving, LED, LCD screen, UPS, AC/solar/car charging, App phones, App panel, App QR | new complete panels (3×) | JP leader labels, captions and screenshots; no existing file carries them | complete panel; body copy inside five panels stripped and set as native text |
| in-box unit | new 3× crop | card art of this print | as printed |
| App Store / Google Play badges | reuse byte-identical (`shared-app-store.png`, as JE-2000F US/en) | same standard badge pair, stacked as printed | as printed |
| 19 LCD icons, POWER / AC / DC/USB / LIGHT buttons, in-box documents | reuse JE-2000F US/en files byte-identically | each passes the fixed 2% comparison against this PDF's glyph paths (0.0018–0.0176) | transparent |
| in-box AC cable | reuse JE-1500D JP V2 `inbox-cable.svg` byte-identically (the file the JE-1000D JP precedent reuses) | US/en cable differs (0.128); the JP cable file passes (0.0072) | transparent |
| LCD plan, self-powered, UPS, output V/Hz, AC wall, car, charging power limit | native vector extraction | US/en files differ (0.049–0.669); JP PNG candidates are opaque | transparent, PDF paths only |
| ten 絵表示の説明 symbols, WEEE crossed bin, battery crossed bin | reuse existing shared variants | pass the fixed 2% symbol admission (0.0045–0.0140); no catalog file added | transparent |
| Li-ion 32 recycling mark | byte-identical reuse of shared `native/je3000c-kr-78316033-06` in the declared plain table (operator decision 2026-11-03) | 0.1424 vs this PDF's glyph — same mark, framing differs; outside symbol-table admission | transparent |

The comparison renders depend on the glyph rectangle (anti-aliasing): glyph rectangles are the union of the glyph's
own drawings plus a 0.25–1.0 pt margin, never including another drawing; `derive_assets.py` re-checks every selection.
No body text or table is an image: all copy is native HTML from `transcription.json`.
