# JE-100C / JP / ja — Git-only Web manual candidate

Operator instruction, 2026-11-03: 「继续 转日语说明书」 (发布文档管理, 日规 view vew0f8smjz), relayed by the coordination window: the 24 Japanese single-language manuals with a customer model and a PDF that are not yet on the Web. This package is the Jackery Explorer 100D (JE-100C) Japanese manual from that table.

**Status: `candidate-pending-operator-review`.** `source/approval.json` does not exist and the IR is not publication-eligible. The operator reviews the 1280/390 renders beside the shared reference edition (JE-100C US English Web) before any release instruction.

## Source authority

- 发布文档管理 record `reczz28SfbsHcvJI`: 子物料编码 16-0102-000468, 项目号 HTE162, SKU 21-0001-000473 / 21-0001-000474. Field 单语言说明书 「【Jackery Explorer 100D】说明书-JP.pdf」, stored byte-exact as `JE-100C-JP-JA.pdf`, SHA-256 `64dd5f5336e40426277bd217a555194461ab2b66f396e4a23308fac43d0203c3`; no printed version. The 说明书文件 print master is recorded in `source_manifest.json:design_original` (name, SHA-256) and not committed.
- 16 pages, 90 × 130 mm. Every glyph is outlined (no text layer). `source/transcription.json` is the line-by-line transcription from 5× renders, with 12× clips for ambiguous punctuation. Wording, punctuation, half-width katakana and spacing are kept as printed; `source_manifest.json:source_concerns` lists suspected source errors for the source owner.
- Model facts come only from this PDF. The JE-100C US English and EU English Web editions supply the component map and textless artwork; JE-1000D JP V2 supplies the Japanese safety-chapter map.

## Layout

The Web body is printed pages 01–14 (physical 2–15); the cover and the back-cover QR page stay in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); no plain table is declared. `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. 28 files are reused byte-identically from the same-model EU/US Web editions (in-box cards, LCD drawings and glyphs, charger/solar panels, output and DISPLAY drawings). Three panels with Japanese labels are new complete 5× renders. All 11 printed symbols reuse shared catalog files and pass the fixed 2% symbol admission; no new shared variant is needed.

## Rebuild

From the repository root (`requirements.lock`, Pandoc 3.9.0.2):

```sh
PKG=manual_sources/JE-100C/JP/ja/git-20261103-64dd5f53
python "$PKG/derive_assets.py"        # artwork + symbol admission rows
python "$PKG/build_content.py"        # transcription -> source/ja/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/je100c-jp
python -m sphinx -n -W --keep-going -b html tmp/je100c-jp tmp/je100c-jp-html
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, and enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/ja` after any source change and run `refresh_manifest.py frozen` last. The JE-1000F JP `build.py check` is a repository regression gate only.

Not touched: live Base, queue, source tables, HTML_link, asset registry, shared symbol catalog, workflows and dependencies.
