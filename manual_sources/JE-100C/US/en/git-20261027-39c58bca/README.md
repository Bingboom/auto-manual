# JE-100C / US / en — Git-only Web manual candidate

Operator instruction, 2026-10-27: 「把这个表中 未转网页版的说明书 走git only进行单语网页文档的转换」 (发布文档管理, view vewF9saLXo). This package is the Jackery Explorer 100D (JE-100C) US English manual from that table.

**Status: `operator-authorized-git-only-release`.** The operator reviewed the 1280/390 renders beside the shared reference edition (PR #1630) and released this manual on 2026-10-28: 「上线提交发布：JE-100A、JE-100C、JE-240A、JE-240B；授权合入 #1630 及其 Hello-Docs 发布 PR」 (merge authority MA-365). `source/approval.json` binds every reviewed `source/` and `assets/` input; the IR is publication-eligible. Source copy goes live as printed; `source_manifest.json:source_concerns` go to the source owner, and the operator checks the published layout after release. Hello-Docs/RTD publication follows [web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline/input-paths.md#22-git-only-transaction).

## Source authority

- 发布文档管理 record `reczz28SPRx9p8Z3`: 物料号 16-0102-000466, 项目号 HTE162, SKU 21-0001-000472 / 21-0001-000471. Field 单语言说明书 「【Jackery Explorer 100D】说明书-EN.pdf」, stored byte-exact as `JE-100C-US-EN.pdf`, SHA-256 `39c58bca661f635fc9d500bc9362317b62b5da6f007589fbf8e4ebfcc8e0bad0`. The 查找引用 Illustrator master is recorded in `source_manifest.json:design_original` (name, SHA-256) and not committed.
- 15 pages, 90 × 130 mm, with a text layer. `source/transcription.json` is the line-by-line transcription, checked against the text layer and 300 dpi renders. Wording, punctuation and spelling are kept as printed; `source_manifest.json:source_concerns` lists suspected source errors for the source owner.
- Model facts come only from this PDF. The JE-100C EU English Web edition supplies reused artwork and is the review reference; JE-1000D JP V2 supplies the method.

## Layout

The Web body is printed pages 01–12 (physical 3–14) plus the back-cover contact text; cover, paper TOC and the back-cover QR stay in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); no plain table is declared. `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. Eleven panels and the 18 LCD icons reuse the JE-100C EU English Web bytes (`evidence/reuse-compare.png`); three drawings are new crops because the EU files bake body text or a cell outline into the image. Safety symbols pass the fixed 2% symbol admission: four reuse shared variants, three are new shared native variants extracted from this PDF and added by PR #1632 (`warning/outline-triangle-dark-hte162`, `do-not-dismantle/screwdriver-prohibited-dark-hte162`, `li-ion/recycle-li-ion-label-hte162`).

## Rebuild

From the repository root (`requirements.lock`):

```sh
PKG=manual_sources/JE-100C/US/en/git-20261027-39c58bca
python "$PKG/derive_assets.py"        # artwork + symbol admission rows
python "$PKG/build_content.py"        # transcription -> source/en/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/je100c-us
python -m sphinx -n -W --keep-going -b html tmp/je100c-us tmp/je100c-us-html
python -m unittest tests.test_explorer_us_en_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/en` after any source change. The JE-1000F US `build.py check` is a repository regression gate only.

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows and dependencies.
