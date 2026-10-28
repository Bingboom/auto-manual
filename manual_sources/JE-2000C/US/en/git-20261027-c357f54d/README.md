# JE-2000C / US / en — Git-only Web manual candidate

Operator instruction, 2026-10-27: 「把这个表中 未转网页版的说明书 走git only进行单语网页文档的转换」 (发布文档管理 Base). This package is the Jackery Explorer 2000 Plus (JE-2000C) English manual from that table.

**Status: `candidate-pending-operator-review`.** No operator acceptance is recorded: there is no `source/approval.json` and the IR is not publication-eligible. The 1280/390 renders in `evidence/` go to the operator beside the shared reference edition; release follows only after the operator says 「上线提交发布」 for this package.

## Source authority

- Base record `reczz28SPLqH8n46`: 物料号 38-0001-000110, 项目号 HTE099, sku 21-0001-000036.
- 「单语言说明书」 「【Jackery Explorer 2000 Plus】说明书-EN.pdf」, stored byte-exact as `JE-2000C-US-EN.pdf`, SHA-256 `c357f54dfed27d11d72a2a4893e485450a49c1b562e21f0f272708857f1510ab`. Cover: Model JE-2000C, USER MANUAL, Version JAK-UM-V1.0.
- 「查找引用」 original 「38-0001-000110 说明书 HTE0992000A-US-JAK  ROSH REACH-2-q.ai」, SHA-256 `9ff2337a…d5eb5d93462d`, recorded in `source_manifest.json` for identity only (not committed).
- 14 pages, 130 × 185 mm. Every glyph is outlined (no text layer). `source/transcription.json` is the line-by-line transcription; wording, punctuation and spelling are kept as printed, and `source_manifest.json:source_concerns` lists suspected source errors for the source owner.

## Layout

The Web body is printed pages 01–12 (physical 2–13); cover and back cover stay in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); the one plain table (Energy Saving Mode) is declared in `shared_component_exceptions`. `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry only. Shared reference edition for review: JE-2000E EU/en (the 2000 Plus EU edition), listed in `reference_editions`.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. Product, LCD, charging and badge art are complete source panels at 3×, keeping frames, leader lines and captions. The seven LCD description icons are transparent 8× renders of their own glyph rectangle. The FCC mark reuses the shared `fcc/nested-c-native-dark` file byte-identically. The manual prints no symbol-meaning table, so no symbol admission applies.

## Rebuild

From the repository root (`requirements.lock`):

```sh
PKG=manual_sources/JE-2000C/US/en/git-20261027-c357f54d
python "$PKG/derive_assets.py"        # artwork
python "$PKG/build_content.py"        # transcription -> source/en/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/je2000c-us
python -m sphinx -n -W --keep-going -b html tmp/je2000c-us tmp/je2000c-us-html
python -m unittest tests.test_je2000c_us_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline and enforces the prepared-document shared-style gate. Copy a fresh render to `web/en` after any source change.

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows and dependencies.
