# JE-240B US English — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- 发布文档管理 record `reczz28SPRx9noYZ` (物料号 38-0001-000947, 项目号 HTE148, SKU 21-0001-000362 / 21-0001-000492 / 21-0001-000393),
  field 单语言说明书 「【Jackery Explorer 240D】说明书-EN.pdf」, read-only bot download; 3,212,164 bytes,
  SHA-256 `3dc1fbbaf28908f216955e32de05b88dc9b0477854e8c0b5df7926a542572521` (stored as `JE-240B-US-EN.pdf`).
- 15 pages, 90 × 130 mm, "Manual English PDF export" of one Illustrator artboard (every page shares one ~99k-drawing
  content stream, clipped per page). No text layer and no raster images except the back-cover QR.
  p1 cover, p2 IMPORTANT front matter, p3 TOC, p4–p14 printed 01–11, p15 back cover.
- Field 查找引用: Illustrator master 「38-0001-000947 HTE148240A-USCA-JAK 说明书 RoHS REACH-Q.pdf」, 22,826,160 bytes,
  SHA-256 `933f25528e3b37b1316883f0f769c3f0b18ba0e757d06b247bf990fb7f45005a` (one artboard). Recorded only.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/JE-100C/US/en/git-20261027-39c58bca` and `docs/renderers/web/assets/je100c_eu_*` (same template family) | cart mark, FC mark, in-box and product drawings, LCD icons |
| `data/manual_sources/JE-300E/EU/en/git-20261016-50b910fd/assets` (Explorer 300D, HTE147) | LCD icons (11 candidates), operation and charging drawings |
| `docs/renderers/web/assets/shared/lcd/`, `shared/symbols/manifest.json` (79 variants), `shared/buttons/` | LCD icons, all ten safety symbols, FC mark; no key-combination table is printed |
| `grep -ril "240D\|HTE148\|JE-240B"` over `manual_sources/`, `data/manual_sources/`, `docs/renderers/web/assets/` | no earlier JE-240B artwork |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| in-box cards, overview, strap, LCD map, POWER ON/OFF, LCD SCREEN, solar charging | new complete crops at 3× | Explorer 240D drawings; no existing 240D art | complete panel kept (white page) |
| USB OUTPUT, USB-C charging, car charging panels | new complete crops at 3× after removing only the line art inside the text pill | the pills carry body copy that is native Web text | complete panel kept, pill removed |
| LCD icons (11) | new transparent PNGs rasterised from the glyph's own drawings and clip groups | closest JE-300E / JE-100C icons differ by ≥ 6.8% (different car, solar, temperature, percentage glyphs) | transparent |
| cart mark | reuse `je100c_eu_shared/symbol_purchase.png` | same cart pill mark (JE-100C precedent) | transparent |
| FC mark | reuse `fcc/nested-c-native-dark` | shared compliance mark | transparent |
| ten safety symbols | reuse shared variants (two are `warning/outline-triangle-dark-hte162` and `do-not-dismantle/screwdriver-prohibited-dark-hte162`, added by PR #1632) | each within 2% of the source paths read with the shared native_svg (PR #1632) (0.2%–1.9%) | transparent |

This PDF's paths (an off-page path closes a subpath with `Z` while its fill/stroke twin closes with an explicit line
to the origin) needed the `tools/asset_pipeline/native_svg.py` closure fix of PR #1632; symbol admission reads the
source paths with it.

No body text or table is an image: all copy is native HTML from `transcription.json`.
