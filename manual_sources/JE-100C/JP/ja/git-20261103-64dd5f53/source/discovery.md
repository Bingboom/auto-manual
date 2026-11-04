# JE-100C JP Japanese — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- 发布文档管理 record `reczz28SfbsHcvJI` (日规, 子物料编码 16-0102-000468, 项目号 HTE162, SKU 21-0001-000473 / 21-0001-000474),
  field 单语言说明书 「【Jackery Explorer 100D】说明书-JP.pdf」, read-only bot download; 2,681,136 bytes,
  SHA-256 `64dd5f5336e40426277bd217a555194461ab2b66f396e4a23308fac43d0203c3` (stored as `JE-100C-JP-JA.pdf`).
- 16 pages, 90 × 130 mm (pypdf export). No text layer: all copy is outlined. p1 cover (型番 JE-100C / JE-100C-SG, no printed
  version), p2–p15 printed 01–14, p16 back cover (QR only).
- Field 说明书文件: print master 「16-0102-000468 HTE162100A-JP-JAK 说明书 RoHS REACH A0-Q.pdf」, 12,442,512 bytes,
  SHA-256 `3fed7183197dc039b01ec494759be9ada03a9df29f13f483f7164cd3cce606ca`. Recorded only; not an extraction source.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/JE-100C/US/en/git-20261027-39c58bca/assets` | every panel and icon, side by side with the JP pages |
| `docs/renderers/web/assets/je100c_eu_en/`, `je100c_eu_shared/` | in-box cards, LCD interface drawings, charging panels, 18 LCD glyphs |
| `manual_sources/JE-100C/KR/ko/V0.3-Q` | Korean source package; no Web artwork |
| `docs/renderers/web/assets/shared/symbols/manifest.json` | all 11 printed symbols at the fixed 2% admission (incl. #1632/#1640/#1641 variants) |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| in-box cards, LCD interface 1–3, USB-C charger and solar panels, 18 LCD glyphs | reuse EU bytes | same drawing; on-screen LCD text and the solar label 「SolarSaga 40 Air x1」 are printed identically | as committed |
| output and DISPLAY-button drawings | reuse US bytes | same textless drawing | as committed |
| product appearance, 省エネモード drawing, シガーソケット panel | new complete panels at 5× | Japanese labels (leader labels, 「3秒長押しで…」, 「車」) | complete panel kept |
| 11 symbols of 絵表示の説明 | reuse shared catalog files | each passes the 2% admission (max error 0.0193) | transparent |

No new shared symbol variant is needed. No body text or table is an image: all copy is native HTML from `transcription.json`.
The USB-C charger panel of the JP print carries a stray 「)」 glyph; the reused EU panel does not (source_concerns).
