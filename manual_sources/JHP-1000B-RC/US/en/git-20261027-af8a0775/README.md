# JHP-1000B-RC / US / en — Git-only Web manual (V2)

Operator instruction, 2026-10-27: 「把这个表中 未转网页版的说明书 走git only进行单语网页文档的转换」 (发布文档管理 table `tbljbjaXaTD6V9PO`). This package is the Jackery HomePower 1000 Plus English manual of record `reczz28SPRx9mkta` (物料号 16-0102-000416, 项目号 HTE2607, SKU 21-0001-000519 / 21-0001-000624). Route `JHP-1000B-RC/US/en/md`; there is no earlier US Web edition of this model, so it is the legacy default.

**Status: `operator-authorized-git-only-release`.** On 2026-10-28 the operator authorized release (「授权全部合入上线 上线之后 我再一个个核对版面」 in the coordination session, then 「上线提交发布」 for this package in its engineering session). `source/approval.json` binds every reviewed `source/` and `assets/` input and the IR is publication-eligible. The operator checks the layout after go-live; corrections enter only through a new package. The candidate was merged as PR #1628; the approval landed in a follow-up PR.

## Source authority

- 单语言说明书 「【Jackery HomePower 1000 Plus】说明书-EN.pdf」, stored byte-exact as `JHP-1000B-RC-US-en-V2.pdf`, SHA-256 `af8a0775d0ba23a137fe024ae961c8b77f35797e1c8838a943ddbf8d418d9251`. Cover: Model JHP-1000B-RC, V2.
- 22 pages, 130 × 185 mm. Every glyph is outlined (no text layer). `source/transcription.json` is the line-by-line transcription, checked against an independent OCR pass; wording, punctuation and spellings are kept as printed and `source_manifest.json:source_concerns` lists suspected source errors for the source owner.
- The design original 「16-0102-000416 说明书A1 HTE26071000A-US-JAK  RoHS REACH Q.pdf」 is recorded by name and SHA-256 only.
- Model facts come only from this PDF. The JHP-3600A US reviewed edition supplies structure and the shared-component vocabulary.

## Layout

The Web body is the IMPORTANT preface (physical 2) and printed pages 01–18 (physical 4–21); cover, paper TOC and back cover stay in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); no plain table is needed (`shared_component_exceptions` is empty). `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. Product, LCD map, operation, charging and App art are complete source panels at 3×; body copy printed inside five panels is removed by vector strip and set as native text. LCD icons and the AC 1/LIGHT buttons are original PDF vector paths (transparent); the battery ring, F8 fault and 888V 88Hz readout, the POWER and DC/USB buttons, the FCC mark and the store badges are reused byte-identically. All seven safety symbols pass the fixed 2% admission with existing shared variants; no catalog file is added.

## Rebuild

From the repository root (`requirements.lock`):

```sh
PKG=manual_sources/JHP-1000B-RC/US/en/git-20261027-af8a0775
python "$PKG/derive_assets.py"        # artwork + symbol admission rows
python "$PKG/build_content.py"        # transcription -> source/en/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/jhp1000brc-us
python -m sphinx -n -W --keep-going -b html tmp/jhp1000brc-us tmp/jhp1000brc-us-html
python -m unittest tests.test_jhp1000brc_us_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/en` after any source change, then run `refresh_manifest.py frozen`.

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows and dependencies.
