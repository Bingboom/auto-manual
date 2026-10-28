# JE-100C US English — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- 发布文档管理 record `reczz28SPRx9p8Z3` (物料号 16-0102-000466, 项目号 HTE162, SKU 21-0001-000472 / 21-0001-000471),
  field 单语言说明书 「【Jackery Explorer 100D】说明书-EN.pdf」, read-only bot download; 804,559 bytes,
  SHA-256 `39c58bca661f635fc9d500bc9362317b62b5da6f007589fbf8e4ebfcc8e0bad0` (stored as `JE-100C-US-EN.pdf`).
- 15 pages, 90 × 130 mm, with a text layer and vector art: p1 cover, p2 TOC, p3–p14 printed 01–12, p15 back cover.
- Field 查找引用: Illustrator master 「16-0102-000466 HTE162100A-USCA-JAK 说明书 RoHS REACH A0.pdf」, 14,513,623 bytes,
  SHA-256 `92ca7245442cc819a12961ac3ec8b04d11db64883e4581961e2a5637552aba35` (41 artboards, USCA set). Recorded only.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `docs/renderers/web/assets/je100c_eu_en/` (JE-100C EU English Web, published) | overview, LCD interfaces, operation, charging and in-box art |
| `docs/renderers/web/assets/je100c_eu_shared/` | LCD icons, cart mark, legacy symbols |
| `docs/renderers/web/assets/shared/symbols/manifest.json` (76 variants) | all seven safety symbols, fixed 2% admission comparison; FC mark |
| `docs/renderers/web/assets/shared/buttons/` | not needed: no key-combination table is printed |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| overview, LCD interface 1–3, USB-C / solar / car charging, in-box cards | reuse JE-100C EU English bytes | same product drawing; every label/caption identical to the US print (checked side by side) | complete panel kept |
| LCD icons (18) and cart mark | reuse `je100c_eu_shared` bytes | same LCD glyphs and cart mark | transparent |
| OUTPUT ON/OFF, ENERGY SAVING MODE drawings | new complete crops from the US PDF | the EU files bake body text (bullet pill, three paragraphs) into the image | panel art only; copy is native |
| LCD SCREEN drawing | new crop from the US PDF | the EU file carries the table cell outline | white |
| FC mark | reuse `fcc/nested-c-native-dark` | shared compliance mark | transparent |
| read manual, WEEE, keep from fire, keep from children | reuse shared variants | pass admission (1.9%, 1.4%, 1.3%, 1.3%) | transparent |
| warning triangle, do not dismantle, Li-ion | new shared native variants extracted from this PDF, added by PR #1632 as `warning/outline-triangle-dark-hte162`, `do-not-dismantle/screwdriver-prohibited-dark-hte162`, `li-ion/recycle-li-ion-label-hte162` | closest existing 5.9%, 7.2%, 2.95% | transparent, PDF paths only |

No body text or table is an image: all copy is native HTML from `transcription.json`.
