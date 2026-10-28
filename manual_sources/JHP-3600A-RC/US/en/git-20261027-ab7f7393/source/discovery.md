# JHP-3600A-RC US — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- 发布文档管理 record `reczz28SPRx9mcml` (物料号 16-0102-000415, 项目号 HTE2608,
  sku 21-0001-000517 / 21-0001-000544), attachment 「【Jackery HomePower 3600 Plus】说明书-EN.pdf」,
  read-only bot download; 4,894,475 bytes, SHA-256
  `ab7f7393ed6fd1e08656f19a48bdc7fce8f827ee9be629f8aebfd95b7d5cf857` (stored as `JHP-3600A-RC-US-EN.pdf`).
- Design original 「16-0102-000415 HTE26083600A-US-JAK 说明书 A1 RoHS REACH Q.pdf」 (39,955,630 bytes,
  SHA-256 `07b8adfc7dfc76ab4c8b301446b570b85a129c868a604fcc3f462a44c9ab79f3`): identity only, not stored.
- 24 portrait pages, 130 × 185 mm. No text layer: every glyph is outlined.
- p1 cover (Model: JHP-3600A-RC), p2 IMPORTANT, p3 paper TOC, p4–p23 printed 01–20, p24 back cover.

## Relation to the published JHP-3600A US edition

The template matches `data/manual_sources/JHP-3600A/US/git-20261012-541ca8a5-reviewed`, but the copy is a
later revision: HP3600Plus short name, a new IMPORTANT preface, DANGER/maintenance block, ISED Canada panel
and RF exposure statements, rewritten UPS/LCD/warranty copy and model number JHP-3600A-RC. Every Web
string is transcribed from this PDF; the reference text layer served only as a reading aid.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `data/manual_sources/JHP-3600A/US/git-20261012-541ca8a5-reviewed/assets` | every panel, LCD icons, key buttons, FCC mark, symbols |
| `data/manual_sources/JHP-5000C/US/git-20261010-051169dd-web-layout/assets` | LCD icons (`lcd-native-*`) |
| `data/manual_sources/JHP-3000D/US/*/assets`, `data/manual_sources/JHP-3600C` | LCD icons |
| `docs/renderers/web/assets/shared/symbols/manifest.json` | all 11 safety symbols, fixed 2% admission comparison |
| `docs/renderers/web/assets/shared/lcd`, `manual_sources/*/*/*/*/assets/shared-lcd` | LCD icons |
| `docs/renderers/web/assets/shared/buttons/` | key-combination buttons (shapes differ: horizontal JE-1000F faces) |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| overview, LCD map, operation, UPS, connection, charging, App panels | new complete panels | reference art is label-redacted base art positioned by package CSS, which the shared-style gate forbids; copy and layout also changed | complete panel; in-panel body copy (UPS text, AC charging note, car pill, standby callout, USB prerequisite corner) blanked to the panel colour and rendered natively |
| in-box card art, App badges, QR, phone frames | new complete crops | target art | card/badge/phone frame kept |
| 12 LCD icons | reuse JHP-5000C `lcd-native-*` / JHP-3600A `lcd-solar-charging-pill.svg` byte-identical | same glyph within 2% | transparent |
| 12 LCD icons | native vector extraction | best candidate ≥2% | transparent, PDF paths only |
| key-combination buttons, FCC mark | reuse JHP-3600A reference files byte-identical | same HomePower 3600 Plus template | transparent |
| 11 safety symbols | reuse shared variants (no new variants) | each passes admission ≤1.7% | transparent |

No body text or table is an image: all copy is native HTML from `transcription.json`.
