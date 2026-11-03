# JE-76A / JP / ja — Git-only Web manual candidate

Operator instruction, 2026-11-03: 「继续 转日语说明书」 (发布文档管理, 日规 view vew0f8smjz), relayed by the coordination window: the 24 Japanese single-language manuals with a 客户型号 and a PDF not yet on the Web. This package is the Jackery Power Bank (JE-76A / JE-76A-WH) Japanese manual from that table.

**Status: `candidate-pending-operator-review`.** No `source/approval.json` exists and the IR is not publication-eligible. Approval is written only after the operator reviews the 1280/390 renders beside the shared reference edition and says 「上线提交发布：…」 in the working session.

## Source authority

- 发布文档管理 record `reczz28SfbsHcnhM`: 子物料编码 38-0001-000723, 项目号 HTE125, SKU 21-0001-000310 / 21-0001-000309. Field 单语言说明书 「【Jackery Power Bank】说明书-JP.pdf」, stored byte-exact as `JE-76A-JP-JA.pdf`, SHA-256 `d8f7d338fd208af056c0dda9991422227627ab771245e791858e1480978b013c`; no printed version mark. The 说明书文件 print master is recorded in `source_manifest.json:design_original` (name, SHA-256) and not committed.
- 14 pages, 89 × 130 mm. Every glyph is outlined (no text layer). `source/transcription.json` is the line-by-line transcription from 450 dpi renders, re-checked on 500–600 dpi clips. Wording, punctuation and spelling are kept as printed; `source_manifest.json:source_concerns` lists suspected source errors for the source owner.
- Model facts come only from this PDF. No earlier Web edition of the Power Bank exists. JE-1000D JP V2 supplies the JP structure and components; JE-100A US/en is the same-period small-product edition shown beside this candidate for review.

## Layout

The Web body is printed pages 1–13 (physical 2–14); the cover stays in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); four plain tables are declared in `shared_component_exceptions`. `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every extract decision. All drawings are new complete panels at 3× (no Power Bank art existed). The % and charging-lamp LCD glyphs and the Li-ion recycling mark are the original PDF vector paths (transparent). The print has no symbol table; the 警告/注意 pictograms are not repeated, so there are no symbol admission rows and nothing is added to the shared symbol library.

## Rebuild

From the repository root (`requirements.lock`, Pandoc 3.9.0.2):

```sh
PKG=manual_sources/JE-76A/JP/ja/git-20261103-d8f7d338
python "$PKG/derive_assets.py"        # artwork
python "$PKG/build_content.py"        # transcription -> source/ja/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/je76a-jp
python -m sphinx -n -W --keep-going -b html tmp/je76a-jp tmp/je76a-jp-html
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline and enforces the prepared-document shared-style gate. Copy a fresh render to `web/ja` after any source change, then run `refresh_manifest.py frozen`. The JE-1000F JP `build.py check` is a repository regression gate only.

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows and dependencies.
