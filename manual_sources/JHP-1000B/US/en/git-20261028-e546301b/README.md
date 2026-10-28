# JHP-1000B / US / en — Git-only Web manual (V2)

Operator instruction, 2026-10-28: 「继续转 剩下的美规说明书 为单语 网页版 仅选等于Y的 待转」 (发布文档管理 table `tbljbjaXaTD6V9PO`, 是否要转网页文档 = Y, 是否已转网页版 unticked). This package is the Jackery HomePower 1000 Plus English manual of record `reczz28SlRGJi0KB` (子物料编码 16-0102-000489, 项目号 HTE159). Route `JHP-1000B/US/en/md`; there is no earlier US Web edition of this model, so it is the legacy default.

**Status: `candidate-pending-operator-review`.** No approval is written; `manual.ir.json` is not publication-eligible. The approval is written only after the operator says 「上线提交发布」 for this package in its engineering session.

## Source authority

- 单语言说明书 「【Jackery HomePower 1000 Plus】说明书-EN.pdf」, stored byte-exact as `JHP-1000B-US-en-V2.pdf`, SHA-256 `e546301b5cba7a6774418544a74c689f69712fd0fac6189df016f8020c0d98b1`. Cover: Model JHP-1000B/JHP-1000B-WH, V2.
- 22 pages, 130 × 185 mm. Every glyph is outlined (no text layer). `source/transcription.json` is the line-by-line transcription, checked against an independent OCR pass; wording, punctuation and spellings are kept as printed and `source_manifest.json:source_concerns` lists suspected source errors for the source owner.
- The print master 「16-0102-000489 说明书A1 HTE1591000A-US-JAK RoHS REACH-q.pdf」 (说明书文件) is recorded by name and SHA-256 only.
- Model facts come only from this PDF. The JHP-1000B-RC US package (same platform; the Red Cross edition) supplies structure, shared-component bindings and the artwork that is identical in both PDFs.

## Differences from JHP-1000B-RC

Same text on 17 of 18 body pages. This edition has no Red Cross trademark note in the preface, a shorter FCC panel (no RF exposure statement, no ISED panel), four in-box cards (adds a USB-C cable; the tip label reads TIPS), and Model No. JHP-1000B/JHP-1000B-WH. Product art shows the HomePower 1000 Plus nameplate where the RC edition prints the Red Cross mark.

## Layout

The Web body is the IMPORTANT preface (physical 2) and printed pages 01–18 (physical 4–21); cover, paper TOC and back cover stay in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); no plain table is needed (`shared_component_exceptions` is empty). `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. Thirty files (LCD map and icons, App frames, battery accessories, safety symbols) reproduce the JHP-1000B-RC files byte for byte; the in-box AC cable and documents, the App result frames and the AC 1/LIGHT buttons are copied from JHP-1000B-RC (same vector art, moved on the page); product views and operation/charging panels that carry the nameplate are new complete-panel extractions, as is the USB-C cable card. All seven safety symbols pass the fixed 2% admission with existing shared variants; no catalog file is added.

## Rebuild

From the repository root (`requirements.lock`):

```sh
PKG=manual_sources/JHP-1000B/US/en/git-20261028-e546301b
python "$PKG/derive_assets.py"        # artwork + symbol admission rows
python "$PKG/build_content.py"        # transcription -> source/en/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/jhp1000b-us
python -m sphinx -n -W --keep-going -b html tmp/jhp1000b-us tmp/jhp1000b-us-html
python -m unittest tests.test_jhp1000b_us_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/en` after any source change, then run `refresh_manifest.py frozen`.

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows and dependencies.
