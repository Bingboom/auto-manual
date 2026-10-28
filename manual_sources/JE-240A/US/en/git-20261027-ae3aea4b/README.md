# JE-240A / US / en — Git-only Web manual candidate

Operator instruction, 2026-10-27: 「把这个表中 未转网页版的说明书 走git only进行单语网页文档的转换」 (发布文档管理, view vewF9saLXo). This package is the Jackery Explorer 240 (JE-240A) US English manual from that table.

**Status: `operator-authorized-git-only-release`.** The operator reviewed the 1280/390 renders beside the shared reference edition (PR #1630) and released this manual on 2026-10-28: 「上线提交发布：JE-100A、JE-100C、JE-240A、JE-240B；授权合入 #1630 及其 Hello-Docs 发布 PR」 (merge authority MA-365). `source/approval.json` binds every reviewed `source/` and `assets/` input; the IR is publication-eligible. Source copy goes live as printed; `source_manifest.json:source_concerns` go to the source owner, and the operator checks the published layout after release. Hello-Docs/RTD publication follows [web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline/input-paths.md#22-git-only-transaction).

## Source authority

- 发布文档管理 record `reczz28SPRx9mSKQ`: 物料号 38-0001-000443, 项目号 HTE110, SKU 21-0001-000212 / 21-0001-000493. Field 单语言说明书 「【Jackery Explorer 240】说明书-EN.pdf」, stored byte-exact as `JE-240A-US-EN.pdf`, SHA-256 `ae3aea4bcffa1c87f2de01cbe5c84792713a70eded1716039beb442e38a0a27f`. The 查找引用 Illustrator master is recorded in `source_manifest.json:design_original` (name, SHA-256) and not committed.
- 14 pages, 130 × 185 mm, one outlined artboard (no text layer). `source/transcription.json` is the line-by-line transcription read from 300 dpi renders, with doubtful glyphs re-checked on zoomed clips. Wording, punctuation and spelling are kept as printed; `source_manifest.json:source_concerns` lists suspected source errors for the source owner.
- Model facts come only from this PDF. JE-100C US English and JE-1000D JP V2 supply structure and shared components.

## Layout

The Web body is printed pages 01–12 (physical 2–13) plus the back-cover contact text; the cover and the back-cover QR stay in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); the Energy Saving output table is the one declared plain table (`shared_component_exceptions`). `source/differences.md` lists each deliberate layout difference; `source/geometry.css` holds figure widths and print heading case only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. The battery ring and F8 fault icons and the FC mark reuse shared bytes; the other four LCD glyphs are transparent crops; every panel is a complete 3× crop, App screenshots with their phone frames. The print has no symbol table, so symbol admission has no rows.

## Rebuild

From the repository root (`requirements.lock`):

```sh
PKG=manual_sources/JE-240A/US/en/git-20261027-ae3aea4b
python "$PKG/derive_assets.py"        # artwork
python "$PKG/build_content.py"        # transcription -> source/en/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/je240a-us
python -m sphinx -n -W --keep-going -b html tmp/je240a-us tmp/je240a-us-html
python -m unittest tests.test_explorer_us_en_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline and enforces the prepared-document shared-style gate. Copy a fresh render to `web/en` after any source change. The JE-1000F US `build.py check` is a repository regression gate only.

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows and dependencies.
