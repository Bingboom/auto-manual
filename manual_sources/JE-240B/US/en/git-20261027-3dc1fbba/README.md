# JE-240B / US / en — Git-only Web manual candidate

Operator instruction, 2026-10-27: 「把这个表中 未转网页版的说明书 走git only进行单语网页文档的转换」 (发布文档管理, view vewF9saLXo). This package is the Jackery Explorer 240D (JE-240B) US English manual from that table.

**Status: `operator-authorized-git-only-release`.** The operator reviewed the 1280/390 renders beside the shared reference edition (PR #1630) and released this manual on 2026-10-28: 「上线提交发布：JE-100A、JE-100C、JE-240A、JE-240B；授权合入 #1630 及其 Hello-Docs 发布 PR」 (merge authority MA-365). `source/approval.json` binds every reviewed `source/` and `assets/` input; the IR is publication-eligible. Source copy goes live as printed; `source_manifest.json:source_concerns` go to the source owner, and the operator checks the published layout after release. Hello-Docs/RTD publication follows [web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline/input-paths.md#22-git-only-transaction).

## Source authority

- 发布文档管理 record `reczz28SPRx9noYZ`: 物料号 38-0001-000947, 项目号 HTE148, SKU 21-0001-000362 / 21-0001-000492 / 21-0001-000393. Field 单语言说明书 「【Jackery Explorer 240D】说明书-EN.pdf」, stored byte-exact as `JE-240B-US-EN.pdf`, SHA-256 `3dc1fbbaf28908f216955e32de05b88dc9b0477854e8c0b5df7926a542572521`. The 查找引用 Illustrator master is recorded in `source_manifest.json:design_original` (name, SHA-256) and not committed.
- 15 pages, 90 × 130 mm. Every glyph is outlined (no text layer): `source/transcription.json` is the line-by-line transcription, read from 300–400 dpi renders with 600–700 dpi clips for ambiguous glyphs. Wording, punctuation and spelling are kept as printed; `source_manifest.json:source_concerns` lists suspected source errors for the source owner.
- Model facts come only from this PDF. JE-100C US English (same template family) supplies structure and components; JE-300E EU English supplies the troubleshooting, warranty and LCD-screen component patterns.

## Layout

The Web body is the IMPORTANT front matter (physical 2) and printed pages 01–11 (physical 4–14) plus the back-cover contact text; cover, paper TOC and the back-cover QR stay in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); no plain table is declared. `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. No earlier Explorer 240D artwork exists, so the product drawings are new complete crops; three panels lose only their printed text pill (removed from an in-memory copy of the PDF, copy set as native text). The eleven LCD icons are transparent rasterisations of their own source drawings. The cart mark, FC mark and all ten safety symbols reuse existing files byte-identically.

## Rebuild

From the repository root (`requirements.lock`):

```sh
PKG=manual_sources/JE-240B/US/en/git-20261027-3dc1fbba
python "$PKG/derive_assets.py"        # artwork + symbol admission rows
python "$PKG/build_content.py"        # transcription -> source/en/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/je240b-us
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/en` after any source change; `tests/test_explorer_us_en_web.py` checks the stored render. The JE-1000F US `build.py check` is a repository regression gate only.

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows and dependencies.
