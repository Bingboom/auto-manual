# JE-100A JP Japanese — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- 发布文档管理 record `reczz28SfbsHdgHw` (子物料编码 38-0001-000541, 项目号 HTE106, SKU 21-0001-000167),
  field 单语言说明书 「【Jackery Explorer 100 Plus】说明书-JP.pdf」, read-only bot download; 1,745,957 bytes,
  SHA-256 `2becaa507bbfd8d051888ac85d96a5399f0959224e9e6acb85211599baa06262` (stored as `JE-100A-JP-JA.pdf`).
- 12 pages, 89.4 × 129.4 mm, "Manual portrait export" of one artboard. No text layer: all copy is outlined.
  p1 cover (JAK-UM-V1, 国内専用/For use only in Japan, support e-mail, QR), p2–p12 printed 1–11. No back cover, warranty or contact page.
  Each page holds the whole artboard's drawings, but their coordinates are page coordinates, so the shared native-SVG selector maps icons and symbols.
- Field 说明书文件: print master 「38-0001-000541 HTE106100A-JP-JAK 说明书 20240419 Q.pdf」, 7,064,111 bytes,
  SHA-256 `bc8b964f57737113a0808e6d254406c12fe834ffc98daf1759b0b4ae1b8b1a11`. Recorded only; not committed, not an extraction source.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/JE-100A/US/en/git-20261027-18058b6b/assets/` (same model) | package-list art, LCD icons, F8 fault icon; every panel with printed words |
| `manual_sources/JE-1000D/JP/ja/git-20261026-00c43a89-v2/assets/` | LCD icons (low battery, high / low temperature, 88H), Li-ion recycle mark |
| `docs/renderers/web/assets/shared/symbols/manifest.json` (95 rows, incl. #1632 / #1640 / #1641 variants) | the six 絵表示の説明 glyphs at the fixed 2% admission |
| `docs/renderers/web/assets/shared/lcd/`, JE-1000F JP `shared-lcd/` | battery ring, F8 |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| overview, LCD map, AC / SolarSaga 100 / 80 / 40 Mini / car charging | new complete panels at 3× | Japanese labels and captions | complete panel, leader lines and captions kept |
| 同梱物 unit and manual card art | new at 3× | JP drawing of the unit differs from US; JP manual cover | white page |
| 同梱物 cable | reuse US bytes | same textless drawing | unchanged |
| low battery, high / low temperature | reuse JE-1000D JP native SVG bytes | same glyph within 2% | transparent |
| F8 fault code | reuse JE-1000F shared-lcd bytes (as the US package) | shared glyph | unchanged |
| battery ring, always-on, 12H, Li-ion 32 recycle mark | new native vector SVG | no matching glyph within 2% | transparent (original paths) |
| six safety symbols | reuse shared symbols | all pass 2% admission | transparent shared files |

No body text or table is an image: all copy is native HTML from `transcription.json`.
No symbol is missing from the shared library, so no new shared variant is requested.
