# JE-5000A US — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- 「【Jackery Explorer 5000 Plus】说明书-EN.pdf」 from 发布文档管理 record `reczz28SlRGJhXPM`
  (子物料编码 16-0102-000447, 项目号 HTE119, SKU 21-0001-000550, 21-0001-000614), read-only;
  10,853,970 bytes, SHA-256 `804ebe784c84a698800b2c1cc0f4d28ec692057b1600c48fcc3604e27c86f013`
  (stored as `JE-5000A-US-EN.pdf`).
- 27 portrait pages, 130 × 185 mm, real text layer (Gilroy fonts). Outlined exceptions: the five in-box
  card labels (p6) and the first package-list panel labels (p26). App screenshots on p15, p16, p18, p20 and
  p21 are raster images; everything else is vector.
- p1 cover (Model :JE-5000A, USER MANUAL, Jackery Explorer 5000 Plus), p2 IMPORTANT (US tab), p3 TABLE OF
  CONTENTS (US English 01-23), p4–p26 printed 01–23, p27 back cover (JACKERY INC. address and contact).
  The body includes the SMART HOME BACKUP SYSTEM (AC ESS) INSTALLATION GUIDE (printed 20–23) with the
  Explorer 5000 Plus specifications repeated (printed 21), the JBP-5000A Battery Pack and JA-TS02A Smart
  Transfer Switch specifications (printed 22–23) and the PACKAGE LIST (printed 23).
- Print master 「16-0102-000447 说明书 HTE1195000A-US-JAK RoHS REACH-s.pdf」 (88,728,021 bytes, SHA-256
  `bfc25e01905a5c881fce80d22f40065f6fc4a01a67026bef1ecafeb529ab030d`) was used for identity only; it is not
  committed and no script reads it.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `data/manual_sources/JE-5000A/JP/git-20261010-26cccfe2-reviewed/assets` (same model, JP, shared reference edition) | 24 LCD icons, buttons, every panel, LCD map, in-box and App art |
| `data/manual_sources/JHP-5000C/US/git-20261010-051169dd-web-layout/assets` (HomePower 5000 Plus, same Explorer unit, English) | 26 LCD icons, buttons (incl. `button-dc-bottom.svg`), overview/operation/charging/App/package art |
| `manual_sources/JE-1500D/US/en/git-20261027-772c3698`, `manual_sources/JE-1000D/US/en/git-20261027-10d15090` | same-generation US/en idiom, buttons, LCD icons |
| `docs/renderers/web/assets/shared/symbols/manifest.json` (81 variants) | the 8 safety symbols, the FCC mark and the INGESTION HAZARD glyph, fixed 2% admission comparison |
| `docs/renderers/web/assets/shared/buttons/` | POWER, USB, AC (labels below) and DC for the key-combination table |

LCD icons on this PDF are clip-path fills; MuPDF's SVG renderer does not honour those clips, so the raster
2% comparison is not meaningful for them. Identity is proved on the vector data instead: every path of the
reused file equals the printed path (same order, same coordinates), with the flat grey within 24/255 per
channel (`source_manifest.json:artwork_reuse_comparison`).

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| 22 LCD description icons (①–⑫ sub-rows, ⑮–㉑, ㉓) | reuse JE-5000A JP `lcd-01…24.svg` byte-identical | identical path data to this PDF's glyphs | transparent SVG |
| LCD ⑬ AC Expansion (Charging), ⑭ Smart Transfer Switch | reuse JHP-5000C `lcd-native-14.svg`, `lcd-native-16.svg` byte-identical | identical path data; no JP equivalent | transparent SVG |
| LCD ⑬ AC Expansion (Discharging), ㉒ Output Power | native vector extraction | no inventoried glyph has the same paths | transparent SVG |
| DC Power Button (key combinations) | reuse JHP-5000C `button-dc-bottom.svg` byte-identical | identical path data | transparent SVG |
| POWER / USB / AC buttons (key combinations) | native vector extraction | shared `*-bottom` buttons draw a shorter toggle (0.086–0.115) | transparent SVG |
| LCD map ①–㉓, overview views, operation, UPS, connection, charging, App, AC ESS and package panels | new complete panels at 3× | JP art carries Japanese labels and JP outlets; JHP-5000C bases are text-free with caption overlays that the shared reference figure does not take | complete panel, leader lines, labels and phone frames kept; grey bubbles/pills/sentences omitted (text and vector objects removed, no overpainting) and set as native text |
| in-box cards ①–⑤ | new crops | no US Explorer 5000 Plus card art in the inventory | card art |
| FCC mark | reuse `fcc/nested-c-native-dark` | passes admission (0.0171) | transparent |
| 7 safety symbols | reuse shared catalog variants | pass the fixed 2% admission (0.0076–0.0139) | transparent |
| Non-smoking / Open Flame symbol | staged native variant `no-open-flame/fire-match-prohibited-dark-804ebe78` (package only) | closest `no-open-flame/fire-match-prohibited` 0.0253 fails 2% | transparent |
| INGESTION HAZARD glyph (p22, p24, p25) | staged native variant `ingestion-hazard/coin-battery-triangle-dark-804ebe78` (package only) | no catalog variant (closest 0.2263) | transparent |

The shared symbol catalog is not changed by this package; the two staged rows are reported for the
coordinator's shared-symbol PR. No body text or table is an image: all copy is native HTML from
`transcription.json` (figure labels are also in the alt text and IR metadata).
