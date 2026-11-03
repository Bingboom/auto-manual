# JE-1800B JP V2 — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- 发布文档管理 Base record `reczz28SfbsHfHUZ` (日规 view), field 单语言说明书:
  「【Jackery ポータブル電源 1800】说明书-JP.pdf」, 2,461,187 bytes,
  SHA-256 `754e8c1d076b7d5fd9d84ac76ce9447dccec4a9351c7b7d756a3225255b4da52` (stored as `JE-1800B-JP-V2.pdf`).
- Print master (field 说明书文件, recorded only): 「16-0102-000418 竖版说明书 HTE26111800A-JP-JAK.pdf」,
  6,810,775 bytes, SHA-256 `97a33a6da34bf1fc67f804b1405b3af11cc579f3a88837417234769269ff0099`.
  The single-language PDF is a pypdf re-save of this Illustrator export: identical text layer and
  pixel-identical 150 dpi renders of all 27 pages.
- 27 portrait pages, 130 × 185 mm, live text layer. p1 cover (JE-1800B, V2, 国内専用), p2 目次,
  p3–p26 printed 01–24, p27 back cover (App text, store badges, QR).
- Poppler cannot draw the KozGoPr6N spans (missing Adobe-Japan1 pack); MuPDF renders them. All review
  renders use MuPDF.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/JE-1500D/JP/ja/git-20261019-6ddeef54-v2/assets` | every panel, in-box art, App art, shared LCD icons and buttons |
| `manual_sources/JE-1000D/JP/ja/git-20261026-00c43a89-v2/assets` | overview, LCD, charging, App panels |
| `manual_sources/JE-1000F/JP/ja/git-20260930-d88b32fe-jp-reviewed/web/ja/assets` | in-box cable, shared LCD/buttons provenance |
| `docs/renderers/web/assets/shared/symbols/manifest.json` (95 variants, incl. #1632/#1640) | all 13 safety/disposal symbols, fixed 2% admission comparison |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| overview front/right, LCD map, operation, charging, UPS, App panels | new complete panels | JE-1800B chassis, ports, ratings, LCD layout and captions differ from all references | complete panel, leader lines, captions and phone frames kept |
| in-box unit, manual | new | JE-1800B front; generic document icon | card art |
| in-box AC cable | reuse JE-1500D `inbox-cable.svg` byte-identical | same JP cable drawing | transparent |
| 25 LCD description icons | reuse shared-lcd bytes (24) | same glyphs as the JE-1500D JP V2 set | transparent |
| LCD ⑪ 充電残り時間 | native vector extraction | prints 8.8 H; the shared file draws 88H | transparent, PDF paths only |
| ボタン操作 buttons | reuse shared-buttons (power, ac, dc_usb, led) | same button drawings | transparent |
| battery bin (電池および蓄電池) | reuse `battery_disposal/je2000e-eu-nl-batch1465-native` | passes admission (0.0066) | transparent |
| symbols 01/02/04/09/10/12 | operator canonicals warning/outline-triangle-tinted, read-manual/book-information, keep-away-from-children/adult-child-prohibited, mandatory/h1-jp-native, prohibited/h1-jp-native, native/je3000c-kr-78316033-07 | 0.0051–0.0164 | reuse (2026-11-03 operator standard-icon decision) |
| symbols 03/05/06/07/08/11 | operator canonicals no-open-flame/fire-match-prohibited, native/je1000d-jp-00c43a89-02/03/05, unplug/h1-jp-native, native/je3000c-kr-78316033-06 | 0.021–0.395 | interim proposed native variants, **not added here**; rebind after the shared icon de-duplication PR |

No body text or table is an image: all copy is native HTML bound to `transcription.json`.
