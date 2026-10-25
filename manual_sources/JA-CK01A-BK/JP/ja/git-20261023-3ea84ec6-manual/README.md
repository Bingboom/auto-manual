# JA-CK01A-BK / JP / ja — Git-only manual candidate

Operator instruction, 2026-10-23: 「开两个窗口 把这俩说明书 走git only转网页文档」.
This window converts the full instruction manual; the quick operation guide
(38-0001-000845) is a separate document converted elsewhere and is not part of
this package. The operator confirmed on 2026-10-23 that the package and route use
the printed model **JA-CK01A-BK**, and that this manual takes the default
(`legacy_default`) `JA-CK01A-BK/JP/ja` route.

**Status: `operator-approved-git-only-release`.** The operator reviewed the
1280/390 renders of candidate `5a23d4e` and instructed 「上线提交发布」 on
2026-10-23. `source/approval.json` binds every reviewed `source/` and `assets/`
input; the IR is publication-eligible. The engineering PR is merged by the
operator (AGENTS.md §8.6), not by an agent grant; Hello-Docs/RTD publication
follows the Git-only transaction below.

## Source authority

- Product: Jackery Power Output Cable Kit(L14-30); printed cover/spec model JA-CK01A-BK; JP / ja (国内専用).
- Supplied file: `38-0001-000777 HTO862A-JP-JAK 说明书 RoHS REACH.pdf` (Feishu wiki, read-only download).
- `source/original.pdf`, byte-exact, SHA-256 `3ea84ec63b20a4e65c4d2f5d34a45ce715133b6b6f29a424bd95393d131cd113`.
- One Illustrator artboard: four printed 130×185 mm panels (cover; safety, specs and step 1; steps 2–4; step 5 and QR) inside a print-production title block.
- No printed manual version. The title block reads 版本 V0.1 / 第一次发行, 2025-04-22, 料号 38-0001-000707 and 产品名称 HTE1181500A; the filename says 38-0001-000777 / HTO862A-JP-JAK. These are recorded in `source_manifest.json:source_concerns`, not resolved.
- Every glyph is outlined, so there is no text layer. `source/transcription.json` is the line-by-line transcription the Web copy is tested against.

## Layout

The JBP-1000B-WH / JA-AD500A-SIL JP rules apply: the cover and paper TOC (none here) are not on the Web page, the shared JE-1000F JP Web edition is the structural reference, and no Japanese wording is edited. The page opens with the cover's welcome lead; the navigation is the three printed chapter strips. Every printed block maps to a shared component (`source_manifest.json:component_map`); the one plain table is declared in `shared_component_exceptions`. `source/differences.md` lists each deliberate layout difference; `source/presentation.css` is geometry and typography only.

The PDF prints no symbol table, so no symbol admission applies.

## Artwork

`source/discovery.md` records the inventory before extraction: the repository holds no artwork for this product. `derive_assets.py` writes `source/asset_recipe.json` and runs the shared asset pipeline: each figure is the native PDF crop just inside its step frame, with `whiteout` clearing the frame corners and the outlined label glyphs. Vector replay was tried and rejected because this master relies on clipping paths and dashes. The step-5 wiring drawing is a base-art-live-copy ReferenceFigure whose ten labels are native text on the source coordinates (`source/figure_labels.json`).

## Rebuild

From the repository root (`requirements.lock`, PyMuPDF 1.28.0 / MuPDF 1.29.0):

```sh
PKG=manual_sources/JA-CK01A-BK/JP/ja/git-20261023-3ea84ec6-manual
python "$PKG/derive_assets.py"
python "$PKG/refresh_manifest.py" inputs
python "$PKG/render.py" tmp/ja-ck01a-bk-jp
python -m sphinx -n -W --keep-going -b html tmp/ja-ck01a-bk-jp tmp/ja-ck01a-bk-jp-html
python -m unittest tests.test_ja_ck01a_bk_jp_web
```

Replace `web/ja` with a fresh render after any source change, then run `refresh_manifest.py frozen`. `render.py` checks every input hash, runs the existing prepared RST → manual-ir/v2 → shared Web/MyST pipeline, checks the component counts, carries `source/presentation.css` as the IR source stylesheet and enforces the prepared-document shared-style gate. The JE-1000F JP `build.py check` is a repository regression gate only; it does not validate this body (no phase2 target is registered).

## Release boundary

After the engineering PR is merged by the operator, the Git-only transaction continues per [web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline.md#22-git-only-transaction): seal at the merged `main` commit, assemble from Hello-Docs `main`, open a `docs/publish/**`-only PR, then verify RTD.

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows and dependencies.
