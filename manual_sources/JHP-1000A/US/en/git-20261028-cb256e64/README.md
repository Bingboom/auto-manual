# JHP-1000A / US / en — Git-only Web manual (V2)

Operator instruction, 2026-10-28: 「继续转 剩下的美规说明书 为单语 网页版 仅选等于Y的 待转」 (发布文档管理 table `tbljbjaXaTD6V9PO`, 是否要转网页文档 = Y). This package is the Jackery HomePower 1000 English manual of record `reczz28SlRGJh40c` (子物料编码 16-0102-000344, 项目号 HTE158; SKU list in `source_manifest.json`). Route `JHP-1000A/US/en/md`; there is no earlier US Web edition of this model, so it is the legacy default.

**Status: `candidate-pending-operator-review`.** No approval is written and the IR is not publication-eligible. The Li-ion safety symbol has no shared catalog variant within the fixed 2% admission (closest 0.0233); its binding was handed to the coordination window for a shared-symbol PR, and `rebuild.py` fails symbol admission until `source/asset_recipe.json` binds that row to the new variant.

## Source authority

- 单语言说明书 「【Jackery HomePower 1000】说明书-EN.pdf」, stored byte-exact as `JHP-1000A-US-en-V2.pdf`, SHA-256 `cb256e64ddf9a998f4717e3ec2b038b9ef7711572f7d9b752667f1d6e64077c1`. Cover: Model JHP-1000A/JHP-1000A-WH, V2.
- 21 pages, 130 × 185 mm. Every glyph is outlined (no text layer). `source/transcription.json` is the line-by-line transcription, checked against an independent OCR pass; wording, punctuation and spellings are kept as printed and `source_manifest.json:source_concerns` lists suspected source errors for the source owner.
- The 说明书文件 「16-0102-000344 HTE1581000A-US-JAK 说明书A1 RoHS REACH Q.pdf」 is recorded by name and SHA-256 only.
- Model facts come only from this PDF. The JHP-1000B-RC US/en package supplies structure and the shared-component bindings.

## Layout

The Web body is the IMPORTANT preface (physical 2) and printed pages 01–17 (physical 4–20); cover, paper TOC and back cover stay in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); no plain table is needed (`shared_component_exceptions` is empty). `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. Product, LCD map, operation, charging and App art are complete source panels at 3×; body copy printed inside six panels is removed by vector strip and set as native text. 23 LCD icons and the POWER, DC/USB and LIGHT buttons reuse existing files within the fixed 2% comparison; three LCD icons and the AC1 button are original PDF vector paths. Six safety symbols pass the fixed 2% admission with existing shared variants; no catalog file is added.

## Rebuild

From the repository root (`requirements.lock`):

```sh
PKG=manual_sources/JHP-1000A/US/en/git-20261028-cb256e64
python "$PKG/derive_assets.py"        # artwork + symbol admission rows
python "$PKG/build_content.py"        # transcription -> source/en/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/jhp1000a-us
python -m sphinx -n -W --keep-going -b html tmp/jhp1000a-us tmp/jhp1000a-us-html
python -m unittest tests.test_jhp1000a_us_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/en` after any source change, then run `refresh_manifest.py frozen`.

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows and dependencies.
