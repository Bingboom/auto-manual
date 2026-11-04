# JE-1000G JP V3 — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- 发布文档管理 record `reczz28SfbsHbQU5` (子物料编码 16-0102-000396, 项目号 HTE158, SKU 21-0001-000447 / 21-0001-000448,
  区域 日规), 单语言说明书 attachment 「【Jackery ポータブル電源 1000 New】说明书-JP.pdf」, read-only download:
  2,804,108 bytes, SHA-256 `6cf120136d8366ad37f590610d739e09754ddc38d4c8cd3123d9dca0de132aad` (stored as `JE-1000G-JP-JA.pdf`).
- Print master 「16-0102-000396 HTE1581000A-JP-JAK 说明书 RoHS REACH.pdf」 (10,323,615 bytes,
  SHA-256 `a573754e…0c869c00`) is recorded in `source_manifest.json:design_original` only; it is not committed or extracted.
- 28 pages, 130 × 185 mm (page 2 is a 369.07 × 524.97 pt TOC page). Real text layer (NotoSansJP / Gilroy); artwork is
  vector. p1 cover (Jackery ポータブル電源 1000 New 取扱説明書, 型番: JE-1000G / JE-1000G-WH, V3, 国内専用/For use only in Japan),
  p2 目次 (JP 日本語 01-25), p3–p27 printed 01–25, p28 back cover (App badges and QR).
- Layout generation: the 1000 New layout of JE-1000F JP (same chapter order, 25-position LCD), with the key-combination,
  auto-resume, LCD-screen and UPS blocks of the JE-2000F US/en V2 generation.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/JE-1000F/JP/ja/git-20260930-d88b32fe-jp-reviewed/web/ja/assets` (reference edition) | every panel (content-cropped 4x raster comparison), LCD map, in-box art, symbols |
| `manual_sources/JE-1000D/JP/ja/git-20261026-00c43a89-v2/assets`, `manual_sources/JE-1500D/JP/ja/git-20261019-6ddeef54-v2/assets` | in-box cable, Li-ion mark, LCD icons |
| every tracked SVG/PNG under `manual_sources/`, `data/manual_sources/`, `docs/renderers/web/assets/shared/` (551 distinct transparent files) | each LCD icon, button, in-box and recycling glyph with the fixed 2% glyph metric of `tools/web/symbol_asset_admission.py` |
| `docs/renderers/web/assets/shared/symbols/manifest.json` (95 variants incl. #1632/#1640/#1641) | the ten 絵表示の説明 symbols, `compare_symbol` 2% admission |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| LCD map | reuse JE-1000F JP `pdf-lcd-overview.svg` byte-identical | same 1000 New LCD art (1.41% content raster difference, same 25 positions) | complete map |
| front / right overview, operation panels (POWER, AC, 50/60Hz, USB/car, energy saving, LED, LCD screen art), UPS, AC/solar/car charging, App art | new complete panels at 3x | JE-1000F composites differ 2.6%–11.8% (AC1/AC2 buttons, labels, crop bounds) | panel, leader lines, captions, phone frames kept; in-panel body copy (text pills, bubbles) removed by `strip` and carried as native text |
| 26 LCD icons, inline 88H | reuse existing package files byte-identical | each passes the fixed 2% comparison against this PDF's paths (0.28%–1.53%); the inline 88H of p14 reuses `lcd-energy-saving.svg` (0.70%) | transparent |
| key-combination buttons (POWER, AC1, DC/USB, LIGHT) | reuse JE-2000F JP / JHP-1000A US buttons byte-identical | 0.66%–1.04% | transparent; the plus sign and clock are shared component chrome |
| in-box unit, documents | reuse JE-1000F JP `inbox-unit.svg` (1.44%), JE-2000F JP `inbox-documents.svg` (1.27%) | same drawings | transparent |
| in-box AC cable | native vector extraction | existing JP cable files 2.27% | transparent |
| Li-ion 32 and crossed-bin marks of the recycling box | native vector extraction | closest existing 15.2% / 2.36% | transparent |
| nine safety symbols | reuse existing shared variants (admission 0.39%–1.66%) | see `source_manifest.json:symbol_asset_admission` | transparent |
| 本製品を火気の近くに置かないでください。 symbol | **withheld** | closest `no-open-flame/fire-match-prohibited` 2.11% > 2%; reported to the coordinator as a missing shared symbol, no shared file added | — |

No body text or table is an image: all copy is native HTML from `transcription.json`.
