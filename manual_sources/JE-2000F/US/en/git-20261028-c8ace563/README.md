# JE-2000F / US / en — Git-only Web manual candidate (V2)

Operator instruction, 2026-10-28: 「继续转 剩下的美规说明书 为单语 网页版 仅选等于Y的 待转」 (发布文档管理). This package is the Jackery Explorer 2000 English manual of record `reczz28SlRGJiJNd` (子物料编码 16-0102-000409, 项目号 HTE154, SKU 21-0001-000575 / 21-0001-000625). Route `JE-2000F/US/en/md`; there is no earlier US Web edition of this model, so it is the legacy default. The shared reference edition for review is the JE-2000F EU English Web.

**Status: `candidate-pending-operator-review`.** No `source/approval.json` exists, so the IR is not publication-eligible. Approval is written only after the operator reviews the 1280/390 renders beside the reference edition and says 「上线提交发布」; registration in `data/frozen_package_registry.json` follows that approval.

## Source authority

- 单语言说明书 「【Jackery Explorer 2000】说明书-EN.pdf」, stored byte-exact as `JE-2000F-US-EN.pdf`, SHA-256 `c8ace563cc4575909156b4bcd224016fbd30cf9f8f077cd97738638f67e509e4`. Cover: Model JE-2000F, V2.
- 22 pages, 130 × 185 mm. Every glyph is outlined (no text layer). `source/transcription.json` is the line-by-line transcription, drafted with Tesseract and checked word by word and number by number on 300 dpi renders and 4×–8× clips; wording, punctuation and spellings are kept as printed and `source_manifest.json:source_concerns` lists suspected source errors (among them the 「HomePower 2000 Plus」 name in the UPS text) for the source owner.
- The print master 「16-0102-000409 说明书 A1 HTE1542000A-US-JAK RoHS REACH-转曲.pdf」 is recorded by name, size and SHA-256 only.
- Model facts come only from this PDF. The JE-2000F JP and EU editions supply reusable artwork; JHP-1000B-RC and JE-1500D US/en supply structure and the shared-component vocabulary.

## Layout

The Web body is the IMPORTANT preface (physical 2) and printed pages 01–18 (physical 4–21); cover, paper TOC and back cover stay in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); no plain table is needed (`shared_component_exceptions` is empty). `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. Product, LCD map, operation, charging and App art are complete source panels at 3×; body copy printed inside five panels is removed by vector strip and set as native text. 23 LCD icons, the POWER/AC/DC/USB buttons, two in-box cards and the FCC mark are existing files reused byte-identically after the fixed 2% comparison against this PDF's glyph paths; the UPS and temperature LCD icons, the LIGHT button and the USB-C cable card are original PDF vector paths. All twelve safety symbols pass the fixed 2% admission with existing shared variants; no catalog file is added.

## Rebuild

From the repository root (`requirements.lock`):

```sh
PKG=manual_sources/JE-2000F/US/en/git-20261028-c8ace563
python "$PKG/derive_assets.py"        # artwork + symbol admission rows
python "$PKG/build_content.py"        # transcription -> source/en/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/je2000f-us
python -m sphinx -n -W --keep-going -b html tmp/je2000f-us tmp/je2000f-us-html
python -m unittest tests.test_je2000f_us_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/en` after any source change; `refresh_manifest.py frozen` runs only at release sealing.

Not touched: live Base, queue, source tables, HTML_link, asset registry, frozen package registry, workflows and dependencies.
