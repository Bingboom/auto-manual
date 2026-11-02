# JE-3000B US en — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- 「【Jackery Explorer 3000】说明书-EN.pdf」 from 发布文档管理 record `reczz28SlRGJim2Y`
  (子物料编码 16-0102-000056, 项目号 HTE116, SKU 21-0001-000343; 客户型号 printed in the Base as 「JE-3000B 」 with a
  trailing space), read-only; 4,152,802 bytes, SHA-256 `bd8a82962865ae64cd52e9c6ebf9a20d8495652773ba09806d1911cb0f360294`
  (stored as `JE-3000B-US-EN.pdf`). PDF metadata: "English section; original vector artwork and printed page numbers".
- 19 portrait pages, 130 × 185 mm, one small vector page each (107–4,839 paths); no text layer and no fonts:
  all copy is outlined. Rasters: the App screenshots, the QR and two solar-panel images.
- p1 cover (Model: JE-3000B, USER MANUAL, Jackery Explorer 3000, contact; no version string), p2 preface (US badge),
  p3 TABLE OF CONTENTS, p4–p18 printed 01–15, p19 back cover (JACKERY INC. address, contact, QR).
- Print master 「16-0102-000056 说明书 HTE1163000A-US CA-JAK  RoHS REACH-Q.pdf」 (51,232,792 bytes, 50 pages,
  SHA-256 `53664d66583710ce824b8bfbc74123419eb0203a841e5f6f1c283a6733bf93e5`): identity reference only; not committed
  and not read by any script.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/JE-3000B/**` | none exists (no same-model edition in any region) |
| `manual_sources/JE-3000C/{EU,JP,KR}`, `manual_sources/JE-3600A/EU` | overview, LCD map, operation, charging and App art: different chassis, port layout and screens |
| `manual_sources/JE-1500D/US/en`, `JE-2000A/US/en`, `JHP-3600A-RC/US/en`, `JHP-2000A-RC/US/en`, `JE-1000D/US/en` (same generation) | panels by inspection; LCD glyphs by the fixed 2% comparison |
| every `lcd*` / `button*` / `fcc*` SVG/PNG under `manual_sources/`, `data/manual_sources/`, `docs/renderers/web/assets/` (732 unique files) | the 21 LCD description glyphs, 3 key-combination buttons and the FCC mark against this PDF's native paths, fixed 2% comparison |
| `docs/renderers/web/assets/shared/buttons/` | POWER, DC/USB, AC buttons (shared set is horizontal switches; printed ones are vertical) |
| `docs/renderers/web/assets/shared/symbols/manifest.json` | FCC mark; no safety-symbol table is printed |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| 21 LCD description glyphs | reuse byte-identical from JHP-3600A-RC, JHP-2000A-RC, JE-1500D, JE-1000D US/en | each passes the fixed 2% comparison (0.0021–0.0191) | transparent |
| FCC mark | reuse shared `fcc/nested-c-native-dark` | passes 2% (0.0190) | transparent |
| POWER / DC/USB / AC buttons | native PDF vector extraction | no variant within 2% (closest 0.023–0.029; shared `button/*` 0.12–0.17: horizontal switches) | transparent |
| LCD map, front / right overview | new complete panels | JE-3000B chassis, ①–⑲ numbering, US English labels | complete panel, leader lines, labels |
| operation, UPS, charging panels | new complete panels | JE-3000B drawings, US outlets | grey pills/bubbles, the car-cable note and the AC charging instruction omitted (vector objects removed) and set as native text |
| LCD SCREEN artwork | new | JE-3000B drawing | as printed |
| in-box unit, cable, manual | new card art | JE-3000B unit and manual cover | card art |
| App badges, QR, phone screenshots 2.1–2.5, button map | new complete crops | this manual's App art | badge pair / QR frame / phone frames kept |
| safety symbols | not applicable | no symbol table printed | — |

No body text or table is an image: all copy is native HTML from `transcription.json`.
