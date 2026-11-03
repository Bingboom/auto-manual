# JE-1000H JP — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- Operator-provided monolingual PDF 「【Jackery ポータブル電源 1000 Plus】说明书-JP.pdf」 (单语言说明书 of
  Feishu record `reczz28SfbsHcGfU`, 子物料编码 16-0102-000431, 项目号 HTE159, SKU 21-0001-000451);
  3,054,920 bytes, SHA-256 `717c813db4c64d57f90072da6f40081162131979cc181a440c589e70d9947da4`
  (stored as `JE-1000H-JP-JA.pdf`). Producer pypdf; subject "original artwork and printed page numbers retained".
- 28 portrait pages, 130 × 185 mm, with a text layer (Noto Sans JP / Source Han / Gilroy). Only the cover
  型番 badge "V2" and some button markings are outlined. Two troubleshooting digits map to private-use code points.
- p1 cover (型番：JE-1000H, V2, 国内専用/For use only in Japan), p2 目次, p3–p27 printed 01–25, p28 back cover
  (App reminder, store badges, QR).
- Print master 「16-0102-000431 说明书 HTE1591000A-JP-JAK  RoHS REACH-s.pdf」 (11,341,108 bytes, SHA-256
  `3af3339b…5c94`) is recorded in `source_manifest.json:original_artwork` only: not committed, not extracted.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/JE-1000H/EU/en/2.0` (phase2 `_attachments/lcd_icons`, `lcd_icon_provenance.json`) | all 26 numbered LCD icons, by approved callout number and visual contact sheet |
| `manual_sources/JE-1000H/EU/three-language/*` incl. `git-20261026-8bcb378f-shared-symbols` (MA-361 / Hello-Docs #257) | symbol variants used for the EU symbol rows; in-box, overview, LCD map, App art |
| `manual_sources/JE-2000E/JP/ja/git-20261019-6a70e879-jp-native/web/ja/assets` | same Plus-generation JP page set: panels, buttons (ac1-native.svg), App art, symbols |
| `manual_sources/JE-1000D/JP/ja/git-20261026-00c43a89-v2/assets`, `manual_sources/JE-1500D/JP/ja/git-20261019-6ddeef54-v2/assets` | App badges/QR, in-box art, symbols |
| `docs/renderers/web/assets/shared/symbols/manifest.json` | every variant against the 13 printed symbol glyphs, fixed 2% `compare_symbol` |
| `docs/renderers/web/assets/shared/lcd/`, `docs/renderers/web/assets/shared/buttons/` | connected-batteries icon; POWER, DC/USB, AC, LIGHT buttons |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| 27 LCD icon rows | reuse byte-identical: 26 from JE-1000H EU en 2.0, connected batteries from shared `lcd/` | same model and numbering; JP and EU glyphs match on the contact sheet; the EU row-21 file is a degraded crop | shared transparent icons |
| POWER, DC/USB buttons | reuse shared `buttons/power.svg`, `buttons/dc_usb.svg` | marking and position match the print | transparent |
| AC1 button | native PDF vector paths | print reads 「AC1」; shared `ac.svg` reads AC, JE-2000E `ac1-native.svg` reads AC 1 | transparent |
| LIGHT button | 6× render of the button circle, outside made transparent | bulb glyph absent from shared `led.svg`; LIGHT is a text-layer span the vector selector cannot keep | transparent outside the circle |
| 10 symbols | reuse admitted shared variants (errors 0.0057–0.0168) | fixed 2% admission | shared glyphs |
| 3 symbols (read manual, keep dry, Li-ion 32) | **pending**: left out of the Web tables | no shared variant within 0.02 (0.0257, 0.0244, 0.1724) | — |
| overview front/left/right, LCD map, operation panels, UPS, battery pack, charging, App screens and button map, in-box cards | new complete 3× panels | JE-1000H JP labels and ratings are part of the art; no JP asset of this model existed; JE-2000E JP shows the 2000 Plus chassis | complete panel, leader lines, captions, phone frames kept |
| App store badges, QR | new crops of this page | same art as JE-1000D/JE-2000E JP but those files are different crops/scales; no byte-identical candidate | badge column / QR frame kept |
