# JE-3000A JP — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- Feishu record `reczz28SfbsHdQ1I` (子物料编码 38-0001-000153, 项目号 HTE097, sku 21-0001-000049),
  field 单语言说明书: 「【Jackery ポータブル電源 3000 Pro】说明书-JP.pdf」, 3,106,894 bytes,
  SHA-256 `002fde5a36f8dfc4192a8534e8f43a98e249bfbc491027b7c1b0c819d75e2002` (stored as `JE-3000A-JP-JA.pdf`).
  The print master 「38-0001-000153 说明书 HTE0973000A-JP-JAK  RoHS REACH.ai」 (14,533,995 bytes,
  SHA-256 `bb65c897…a77e7`) is recorded only; nothing is extracted from it.
- 14 single portrait pages, 367.1 × 523.0 pt (129.5 × 184.5 mm), exported from one Illustrator artboard:
  every page carries the same 23,397-path content stream, clipped per page. No text layer: all copy is outlined.
- p1 cover (JE-3000A, Jackery-UM-001, 取扱説明書, 国内専用, support address and greeting, QR), p2–p13 printed 1–12,
  p14 back cover (App notice + store badges, no QR). There is no printed table of contents.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/JE-2000A/US/en/git-20261027-a8ec2be7/assets`, `manual_sources/JE-1500B/US/en/git-20261027-bb5a455b/assets` | same Pro generation: overview, LCD map, charging, in-box, LCD icons |
| `manual_sources/JE-1000D/JP/ja/git-20261026-00c43a89-v2/assets`, `manual_sources/JE-1500D/JP/ja/git-20261019-6ddeef54-v2/assets` | JP precedents: in-box AC cable, LCD icons, Li-ion mark, badges |
| every `manual_sources/**/assets` SVG/PNG (2,967 files) | fixed 2% glyph comparison for each LCD icon and the Li-ion mark |
| `docs/renderers/web/assets/shared/symbols/manifest.json` (95 variants) | all six safety symbols, fixed 2% comparison |
| `docs/renderers/web/assets/shared/buttons/` | not needed: no key-combination table is printed |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| overview, LCD map, AC / solar / prohibited / SolarSaga 80 / trans-jack / car panels | new complete panels | JE-3000A chassis, ports, LCD layout and Japanese captions differ from every reference | complete panel, frames, leader lines, cross marks and captions kept |
| in-box cards (7) | new | JE-3000A unit, cables, pouch, trans-jack, JP manual and warranty leaflet; the JE-2000A car-cable and AC-cable cards and the JE-1500D JP cable are different drawings | card art |
| QC 3.0 logo, App badges | new crops | printed target art | complete logo / badge pair |
| LCD battery ring, low battery, 88H, F8, high / low temperature | reuse existing SVG bytes (JE-3000B US, JE-1000D JP, JHP-3600A-RC US, JE-1500D US) | each passes the fixed 2% comparison against the JE-3000A vector paths (0.0045–0.0155) | transparent |
| inline 88H (省エネ table) and thermometer (低温モード) marks | same reused files | same glyphs at text size | transparent |
| Li-ion 20 recycling mark | native vector extraction | closest file (JE-1000D JP Li-ion 32) differs 0.036 | transparent, PDF paths only |
| 5 safety symbols | reuse shared variants `native/je1000d-jp-00c43a89-01/02/05/06`, `mandatory/h1-jp-native` | pass the fixed 2% comparison (0.0103–0.0192) | transparent |
| 製品に濡れた手で触れることを禁止する記号 | **pending**: package-local source vector paths | closest shared variant differs 0.0264 (> 0.02); nothing added to the shared library | transparent |

## Symbol admission blocker

`tools/web/symbol_asset_admission.py` re-reads the PDF through `native_symbol_svg`, which maps
`get_drawings()` to MuPDF's whole-page SVG. On this PDF every page refuses with
「native PDF fill/stroke SVG mapping is unsupported」 (the whole-artboard stream holds fill/stroke pairs whose
SVG closures differ — the same failure the JE-1500B US package records). The comparisons above therefore use
the package-local `drawing_svg` writer (original paths, own fill/stroke) with the fixed `compare_symbol`
tolerance; `rebuild.py` requires the recorded refusal and re-runs every row. See
`source_manifest.json:symbol_admission_blocker`.

No body text or table is an image: all copy is native HTML from `transcription.json`.
