# JE-2000A US en — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- Feishu record `reczz28SPLqH8cvK` (物料号「文本」38-0001-000200, 项目号 HTE078, SKU 21-0001-000099):
  「【Jackery Explorer 2000 Pro】说明书-EN.pdf」, read-only download; 5,437,332 bytes,
  SHA-256 `a8ec2be735be6483d340f2f35c7bc13a9300bf7d9499f60099ed8d5ef5cf689f` (stored as `JE-2000A-US-EN.pdf`).
  PDF metadata: "English section extracted from the original source; original artwork and printed page
  numbers retained".
- Original artwork (reference only, not committed, not read by any script):
  「38-0001-000200 说明书 HTE0782000A-US-JAK 说明书 ROHS REACH.pdf」, 41,389,092 bytes,
  SHA-256 `2a7450bb2e320d364b4a86a9313b1bfcaf27c574dcbb2e8218f982b6506486a8`.
- 19 portrait pages, 130 × 185 mm. Every page repeats one 142,099-path content stream clipped per page;
  no text layer and no fonts (all copy outlined). The only raster is the back-cover QR.
- p1 cover (Model: JE-2000A, USER MANUAL, Jackery Explorer 2000 Pro, contact, Version: JAK-UM-V1.0),
  p2–p18 printed 01–17, p19 back cover (JACKERY INC. address and QR).

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/**/assets` (JE-1000D JP V2, JE-1500D JP V2, JE-2000E/JE-2000F, JS-100I, JS-CONNECTION-GUIDE) and `data/manual_sources/JE-1500C` | product, in-box, LCD, charging, connector and adaptor art |
| `docs/renderers/web/assets/` (`shared/lcd`, `shared/buttons`, `ja_ca05b_eu_en`, `js100f_eu_en`, `js100i_eu_shared`) | LCD glyphs, buttons, DC7909/DC8020 and connector art |
| `docs/renderers/web/assets/shared/symbols/manifest.json` | not needed: no safety-symbol table is printed |
| `docs/templates/word_template/common_assets/`, `docs/renderers/latex/assets/` | no Explorer 2000 Pro art |
| JE-1000D JP V2 `assets/shared-lcd/` | battery ring (3.35% mean, > 2%) and F8 (opaque backdrop) — not reusable |

No same-model Web exists. JE-1500B (Explorer 1500 Pro, same generation) is being built in parallel and
has no committed art to compare against yet.

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| certification marks, overview front/rear, LCD map, operations callout, wall/solar/connector/examples/prohibited/car/adaptor drawings | new complete panels (3×) | Explorer 2000 Pro chassis, ports, captions and connection drawings exist in no inventory | complete panel, frames, leader lines, X marks, OR badge, insets and captions kept |
| Solar Generator Connector panel | new complete panel with `omit_native_copy` | the outlined 「Functions of Main Ports」 heading sits inside the panel rectangle and is native HTML | heading glyphs removed on an in-memory copy only |
| in-box cards ①–⑤ | new card art | JE-2000A unit, cables, adaptor and guide cover | card art |
| LCD legend ①–⑮, inline LCD glyphs, F0–F9 and temperature glyphs | native PDF glyph renders (transparent PNG, 8×) | no shared glyph with the same semantic key passes 2%; the shared `native_symbol_svg` selector cannot map this PDF's SVG export (clip paths outside `<defs>`) | PDF alpha, no cell/page backdrop |
| p05 Low Battery inline glyph, second FAQ 12H glyph | reuse in-package asset | same glyph (< 1% mean difference) | — |
| safety symbols | not applicable | no symbol table printed | — |

No body text or table is an image: all copy is native HTML from `transcription.json`.
