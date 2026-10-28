# JHP-2000A / US / en — Git-only Web manual (V2)

Operator instruction, 2026-10-28: 「继续转 剩下的美规说明书 为单语 网页版 仅选等于Y的 待转」 for the 发布文档管理 table (是否要转网页文档 = Y, 是否已转网页版 unchecked). This package is the Jackery HomePower 2000 Plus English manual of record `reczz28SlRGJkKmO` (子物料编码 16-0102-000349, 项目号 HTE152, sku 21-0001-000402 / 21-0001-000511). Route `JHP-2000A/US/en/md`; there is no earlier US Web edition of this model, so it is the legacy default.

**Status: `candidate-pending-operator-review`.** No `source/approval.json`; the IR is not publication-eligible. Release needs the operator's own 「上线提交发布」 in the engineering session.

## Source authority

- The record's 单语言说明书 attachment 「【Jackery HomePower 2000 Plus】说明书-EN.pdf」 (read-only download), stored byte-exact as `JHP-2000A-US-en-V2.pdf`, SHA-256 `5b60448e69a76d5a8386227bc800ffc83309c837dfc32f5b3fb1f0901bd3d738`. Cover: Model JHP-2000A, V2, USER MANUAL, Jackery HomePower 2000 Plus.
- 24 pages, 368.79 × 524.69 pt, with a text layer (embedded Gilroy fonts). `source/transcription.json` is the line-by-line transcription taken from that text layer, read against page renders and cross-checked with an independent Tesseract OCR pass. Wording, punctuation and model spellings are kept as printed; `source_manifest.json:source_concerns` lists suspected source errors for the source owner.
- The record's 说明书文件 「16-0102-000349 Jackery HomePower 2000 Plus V2 Portable Power Station User Manual 电子版说明书.pdf」 is the V2 electronic trilingual edition (EN/FR/ES, 64 pages), not the print master. It is recorded by name and SHA-256 only; its English text matches the authoritative PDF line for line.
- Model facts come only from this PDF. The JHP-2000A-RC US V2 package (same platform, Red Cross edition) supplies structure, line ids and shared components. This edition does not print the RC edition's ISED/RF panel, Red Cross trademark note, Energy Saving WARNING, fourth UPS caution or UPS WARNING; nothing is carried over from the RC edition.

## Layout

The Web body is the IMPORTANT preface (physical 2) and printed pages 01–20 (physical 4–23); cover, paper TOC and back cover stay in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); there are no plain-table exceptions. `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. Panels whose product drawing differs from the RC edition (HomePower 2000 Plus badge instead of the Red Cross mark, LCD map icons) are complete source crops at 3×; body copy inside a panel is removed by redaction of its text and text box and set as native text. Panels with the same drawing as the RC edition (left/right views, two in-box cards, accessory strip, App art) 25 of the 27 LCD icons, the four key-combination buttons and the FCC mark are reused byte-identically; the two thermometer LCD icons are native PDF vector paths. The eleven safety symbols are existing shared catalog variants that pass the fixed 2% symbol admission; no catalog file is added.

## Rebuild

From the repository root (`requirements.lock`):

```sh
PKG=manual_sources/JHP-2000A/US/en/git-20261028-5b60448e
python "$PKG/derive_assets.py"        # artwork + symbol admission rows
python "$PKG/build_content.py"        # transcription -> source/en/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/jhp2000a-us
python -m sphinx -n -W --keep-going -b html tmp/jhp2000a-us tmp/jhp2000a-us-html
python -m unittest tests.test_jhp2000a_us_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/en` after any source change, then run `refresh_manifest.py frozen`.

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows and dependencies.
