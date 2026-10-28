# JHP-2000A-RC / US / en — Git-only Web manual candidate (V2)

Operator instruction, 2026-10-27: 「把这个表中 未转网页版的说明书 走git only进行单语网页文档的转换」 for the 发布文档管理 table. This package is the Jackery HomePower 2000 Plus English manual of record `reczz28SPRx9pzTt` (物料号 16-0102-000417, 项目号 HTE2606, sku 21-0001-000518 / 21-0001-000623). Route `JHP-2000A-RC/US/en/md`; there is no earlier US Web edition of this model, so it is the legacy default.

**Status: `candidate-pending-operator-review`.** There is no `source/approval.json`; the IR is not publication-eligible until the operator accepts the 1280/390 renders beside the JHP-3600A US reference edition and an approval is bound to these inputs.

## Source authority

- The record's 单语言说明书 attachment 「【Jackery HomePower 2000 Plus】说明书-EN.pdf」 (read-only download), stored byte-exact as `JHP-2000A-RC-US-en-V2.pdf`, SHA-256 `e27d4db5606c140439dd32b7d17ab4ed428a62fbfbb5567c7664d8ac22032d51`. Cover: Model JHP-2000A-RC, V2, USER MANUAL, Jackery HomePower 2000 Plus.
- 24 pages, 368.79 × 524.69 pt. Every glyph is outlined (no text layer). `source/transcription.json` is the line-by-line transcription, read on 300 dpi renders, cross-checked sentence by sentence against the JHP-3600A US reference PDF text layer, with every difference re-read on this PDF. Wording, punctuation and model spellings are kept as printed; `source_manifest.json:source_concerns` lists suspected source errors for the source owner.
- The record's design original 「16-0102-000417 HTE26062000A-US-JAK 说明书A1 RoHS REACH Q.pdf」 (SHA-256 `1be17195…571a`) is recorded by name and hash only; it is not stored and is not a Web input.
- Model facts come only from this PDF. The JHP-3600A US reviewed edition supplies structure and shared components.

## Layout

The Web body is the IMPORTANT preface (physical 2) and printed pages 01–20 (physical 4–23); cover, paper TOC and back cover stay in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); there are no plain-table exceptions. `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. Panels are complete source crops at 3×, keeping leader lines, labels and phone frames; body copy printed inside a panel is removed from the art by vector redaction and set as native text. Fourteen LCD icons, the POWER and DC/USB buttons and the FCC mark are reused byte-identically; thirteen LCD icons and the AC 1 / LIGHT buttons are original PDF vector paths. The eleven safety symbols are existing shared catalog variants that pass the fixed 2% symbol admission; no catalog file is added.

## Rebuild

From the repository root (`requirements.lock`):

```sh
PKG=manual_sources/JHP-2000A-RC/US/en/git-20261027-e27d4db5
python "$PKG/derive_assets.py"        # artwork + symbol admission rows
python "$PKG/build_content.py"        # transcription -> source/en/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/jhp2000arc-us
python -m sphinx -n -W --keep-going -b html tmp/jhp2000arc-us tmp/jhp2000arc-us-html
python -m unittest tests.test_jhp2000arc_us_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/en` after any source change.

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows and dependencies.
