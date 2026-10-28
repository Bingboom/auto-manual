# JE-100A / US / en — Git-only Web manual candidate

Operator instruction, 2026-10-27: 「把这个表中 未转网页版的说明书 走git only进行单语网页文档的转换」 (发布文档管理, view vewF9saLXo). This package is the Jackery Explorer 100 Plus (JE-100A) US English manual from that table.

**Status: `operator-authorized-git-only-release`.** The operator reviewed the 1280/390 renders beside the shared reference edition (PR #1630) and released this manual on 2026-10-28: 「上线提交发布：JE-100A、JE-100C、JE-240A、JE-240B；授权合入 #1630 及其 Hello-Docs 发布 PR」 (merge authority MA-365). `source/approval.json` binds every reviewed `source/` and `assets/` input; the IR is publication-eligible. Source copy goes live as printed; `source_manifest.json:source_concerns` go to the source owner, and the operator checks the published layout after release. Hello-Docs/RTD publication follows [web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline/input-paths.md#22-git-only-transaction).

## Source authority

- 发布文档管理 record `reczz28SPRx9qFmY`: 物料号 38-0001-000552, 项目号 HTE106, SKU 21-0001-000289 / 21-0001-000171 / 21-0001-000495. Field 单语言说明书 「【Jackery Explorer 100 Plus】说明书-EN.pdf」, stored byte-exact as `JE-100A-US-EN.pdf`, SHA-256 `18058b6bb7e83041fce1798f3baf98a018d079fa5caa6fd8dceec934df02c0b5`; printed version JAK-UM-V1. The 查找引用 Illustrator master is recorded in `source_manifest.json:design_original` (name, SHA-256) and not committed.
- 10 pages, 90 × 130 mm. Every glyph is outlined (no text layer). `source/transcription.json` is the line-by-line transcription from 300 dpi renders, re-checked on 600–800 dpi clips. Wording, punctuation and spelling are kept as printed; `source_manifest.json:source_concerns` lists suspected source errors for the source owner.
- Model facts come only from this PDF. No Web edition of the Explorer 100 Plus exists; the JE-100C US English package (same series, same window) is the component and method reference.

## Layout

The Web body is printed pages 01–08 (physical 2–9) and the contact page (physical 10) without its QR code; the cover stays in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); no plain table is declared. `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. All drawings are new complete panels (no Explorer 100 Plus art existed). The F8 fault icon and the FC mark reuse shared bytes; the other six LCD icons are transparent 6× glyph renders because no shared glyph matches. The PDF is a single-artboard export that the shared native-SVG selector cannot map, so no native vector extraction is used. There is no symbol table.

## Rebuild

From the repository root (`requirements.lock`):

```sh
PKG=manual_sources/JE-100A/US/en/git-20261027-18058b6b
python "$PKG/derive_assets.py"        # artwork
python "$PKG/build_content.py"        # transcription -> source/en/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/je100a-us
python -m sphinx -n -W --keep-going -b html tmp/je100a-us tmp/je100a-us-html
python -m unittest tests.test_explorer_us_en_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline and enforces the prepared-document shared-style gate. Copy a fresh render to `web/en` after any source change. The JE-1000F US `build.py check` is a repository regression gate only.

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows and dependencies.
