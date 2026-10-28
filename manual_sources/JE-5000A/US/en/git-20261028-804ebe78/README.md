# JE-5000A / US / en — Git-only Web manual (candidate)

Operator instruction, 2026-10-28: 「继续转 剩下的美规说明书 为单语 网页版 仅选等于Y的 待转」 (发布文档管理 Base). This package is the Jackery Explorer 5000 Plus (JE-5000A) US English manual from that table: record `reczz28SlRGJhXPM`, 子物料编码 16-0102-000447, 项目号 HTE119, SKU 21-0001-000550, 21-0001-000614.

**Status: `candidate-pending-operator-review`.** The IR is not publication-eligible and there is no `source/approval.json`. Open before release: operator review against the shared reference edition (JE-5000A JP reviewed), the `source_manifest.json:source_concerns` for the source owner, and two printed symbols that have no shared catalog variant and are staged package-only (`staged_shared_symbols`) until the shared-symbol PR adds them. The package is not registered in `data/frozen_package_registry.json` until approval.

## Source authority

- 「【Jackery Explorer 5000 Plus】说明书-EN.pdf」, stored byte-exact as `JE-5000A-US-EN.pdf` (10,853,970 bytes, SHA-256 `804ebe784c84a698800b2c1cc0f4d28ec692057b1600c48fcc3604e27c86f013`). Cover: Model :JE-5000A, USER MANUAL, Jackery Explorer 5000 Plus. No printed manual version.
- 27 pages, 130 × 185 mm, real text layer. `source/transcription.json` is the line-by-line transcription taken from it and checked against 300 dpi renders; ligature code points are written as letters, everything else as encoded. Wording, spelling, punctuation and capitalisation are as printed, even suspected errors (listed for the source owner).
- The print master 「16-0102-000447 说明书 HTE1195000A-US-JAK RoHS REACH-s.pdf」 (88,728,021 bytes, SHA-256 `bfc25e01905a5c881fce80d22f40065f6fc4a01a67026bef1ecafeb529ab030d`) was an identity reference only and is not committed.
- Model facts come only from this PDF. JE-5000A JP (reviewed, the shared reference edition for review) and JHP-5000C US supply structure and byte-identical LCD icons / the DC button.

## Layout

The Web body is physical pages 2 and 4–26 (IMPORTANT and printed 01–23), including the SMART HOME BACKUP SYSTEM (AC ESS) INSTALLATION GUIDE with the repeated Explorer 5000 Plus, the JBP-5000A Battery Pack and the JA-TS02A Smart Transfer Switch specifications and the PACKAGE LIST; cover, paper TOC and back cover stay in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); the three-column troubleshooting table is the one declared plain table (`shared_component_exceptions`). `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. 22 LCD icons are the JE-5000A JP SVGs and two are JHP-5000C SVGs, byte-identical and bound to this PDF by identical vector path data (`artwork_reuse_comparison`); the DC button is the JHP-5000C SVG on the same evidence. Seven safety symbols and the FCC mark are shared catalog files that pass the fixed 2% admission. Two LCD icons and the POWER/USB/AC buttons are the original PDF vector paths. Panels are complete 3× renders; grey bubbles, pills and sentences inside them are removed (text and vector objects deleted, nothing painted over) and set as native text.

**Staged symbols (package only, shared catalog untouched).** The Non-smoking / Open Flame symbol (p5, closest `no-open-flame/fire-match-prohibited` 0.0253) and the INGESTION HAZARD glyph (p22/p24/p25, no catalog variant) are the native PDF paths, listed with their proposed catalog rows in `staged_shared_symbols`. `rebuild.py` admits them against those rows; after the shared PR, bind the catalog files instead.

## Rebuild

From the repository root (`requirements.lock`, Pandoc 3.9.0.2):

```sh
PKG=manual_sources/JE-5000A/US/en/git-20261028-804ebe78
python "$PKG/derive_assets.py"        # artwork, reuse evidence, symbol admission rows
python "$PKG/build_content.py"        # transcription -> source/en/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/je5000a-us
python -m sphinx -n -W --keep-going -b html tmp/je5000a-us tmp/je5000a-us-html
python -m unittest tests.test_je5000a_us_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/en` after any source change. `refresh_manifest.py frozen` runs only after approval.

Not touched: live Base, queue, source tables, HTML_link, asset registry, shared catalogs, frozen-package registry, workflows and dependencies.
