# JE-1500D / US / en — Git-only Web manual (V2)

Operator instruction, 2026-10-27: 「把这个表中 未转网页版的说明书 走git only进行单语网页文档的转换」 (发布文档管理 Base, the table of manuals not yet converted to Web). This package is the Jackery Explorer 1500 (JE-1500D) US English manual from that table: record `reczz28SPRx9ntZO`, 物料号「文本」38-0001-000943, 项目号 HTE140, SKU 21-0001-000368, 21-0001-000382, 21-0014-000312, 21-0014-000340.

**Status: `operator-authorized-git-only-release`.** The operator authorized release on 2026-10-28 (「上线提交发布：JE-1000D、JE-1500B、JE-1500D、JE-2000A；授权合入 #1629 及其 Hello-Docs 发布 PR」) and checks each page's layout after it goes live. `source/approval.json` binds every reviewed `source/` and `assets/` input; the IR is publication-eligible. The source copy goes live as printed; `source_manifest.json:source_concerns` goes back to the source owner.

## Source authority

- 「【Jackery Explorer 1500】说明书-EN.pdf」, stored byte-exact as `JE-1500D-US-EN.pdf` (6,071,419 bytes, SHA-256 `772c36987b4233c2c243d64cf0a2e9c8a3fd1f37ad87ad739600cbf474977a79`). Cover: Model: JE-1500D, V2, USER MANUAL, Jackery Explorer 1500.
- 21 pages, 130 × 185 mm, every glyph outlined (no text layer). `source/transcription.json` is the line-by-line transcription, checked on 300 dpi renders with zoomed clips. Wording, spelling, spacing, punctuation and apostrophe forms are kept as printed, even suspected errors (listed for the source owner).
- The original print artwork 「38-0001-000943 说明书 HTE1401500A-US CA-JAK  RoHS REACH.pdf」 (30,322,591 bytes, SHA-256 `07dcaa43cb2707334a3dcd086be6011cec528f02a6776c86f3d1c1872598c709`) was a reference only and is not committed.
- Model facts come only from this PDF. JE-1500D JP V2 (`manual_sources/JE-1500D/JP/ja/git-20261019-6ddeef54-v2`, the shared reference edition for review) and JE-1000D JP V2 supply structure, components and reusable art.

## Layout

The Web body is physical pages 2 and 4–20 (IMPORTANT and printed 01–17); cover, paper TOC and back cover stay in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); there are no plain-table exceptions. `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. The LCD map, the FCC mark, three shared buttons and all eleven safety symbols are reused byte-identically. Overview, operation, charging and App art are complete source panels at 3×; grey text pills and bubbles printed inside them are removed by deleting their vector objects and set as native text. The 24 LCD icons and the AC cable are the original PDF vector paths (transparent).

**Heavy-object symbol.** No catalog variant was within the fixed 2% (closest `heavy-object/person-load-triangle-tinted`, 0.0244), so its native PDF paths entered the shared catalog through the shared-symbol PR #1632 as `heavy-object/person-load-triangle-dark-772c3698` (append-only; this package's page 5, drawings 116599–116606). `assets/symbol-06.svg` reuses those catalog bytes.

## Rebuild

From the repository root (`requirements.lock`, Pandoc 3.9.0.2):

```sh
PKG=manual_sources/JE-1500D/US/en/git-20261027-772c3698
python "$PKG/derive_assets.py"        # artwork + symbol admission rows (about 3 minutes)
python "$PKG/build_content.py"        # transcription -> source/en/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/je1500d-us
python -m sphinx -n -W --keep-going -b html tmp/je1500d-us tmp/je1500d-us-html
python -m unittest tests.test_je1500d_us_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, enforces the prepared-document shared-style gate and symbol admission (each page carries the 187,134-path artboard, so admission takes about 3 minutes). Copy a fresh render to `web/en` after any source change. `refresh_manifest.py frozen` runs only after approval.

Not touched: live Base, queue, source tables, HTML_link, asset registry, shared catalogs, workflows and dependencies.
