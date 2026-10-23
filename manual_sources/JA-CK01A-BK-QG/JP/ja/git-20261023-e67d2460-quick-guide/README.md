# JA-CK01A-BK-QG / JP / ja — quick guide (クイックガイド) Web candidate

Operator instruction, 2026-10-23: 「开两个窗口 把这俩说明书 走git only转网页文档」. This window converts the quick guide only; the full JA-CK01A-BK JP manual (38-0001-000777) is a separate target converted in parallel. The JBP-1000B-WH / JA-AD500A-SIL rules apply: the cover and contents are not on the Web, the existing JE-1000F JP Web manual is the reference, and no Japanese wording is changed.

**Status: `operator-approved-git-only-release`.** The operator reviewed the renamed candidate `8e39af0` (PR #1597, 1280/390 renders against the PDF) and instructed 「上线提交发布」 on 2026-10-23. The acceptance given earlier for the HTO862A-QG naming was withdrawn at the rename and does not apply. The engineering PR is merged by operator review (AGENTS.md §8.6), not by an agent grant. `source/approval.json` binds every reviewed `source/` and `assets/` input hash; the rendered IR is publication-eligible. Changing a reviewed input invalidates the acceptance: `render.py` then refuses until a new operator acceptance is recorded.

## Source

`source/original.pdf` is the Feishu wiki file `38-0001-000845 快速操作指南 HTO862A-JP-JAK RoHS Reach.pdf`, byte-exact, SHA-256 `e67d2460eff018f0f8cae0be53e404604d1d3bff620d3c69c8cd8396ccce3d7a`. It is one production artboard (Illustrator, 2025-06-13) holding both printed sides of a 130×185 mm accordion-folded sheet: 正面 (cover panel, サイトスペース要件, steps 1–3) and 反面 (3-③, step 4, step 5), framed by the drawing title block (part 38-0001-000845, drawing V0.2, 2025-06-12). The drawing version is not a printed manual version; `printed_manual_version` stays unknown. HTO862A-JP-JAK is the material code and 38-0001-000845 the part number; the quick guide prints no model, so the Web identity follows the full manual's printed model JA-CK01A-BK (`identity` in `source_manifest.json`).

The type is outlined, so the PDF has no text layer. `source/transcription.json` records every printed line verbatim, in Web reading order, with its disposition: `live` (Web text), `in-art` (kept inside a named artwork file) or `web-excluded` (cover panel, production furniture).

## Web structure and shared components

Navigation is the six print chapter tabs: サイトスペース要件 and steps 1–5. The cover panel's two lines form the Web title. `component_map` in `source_manifest.json` maps every printed block:

- **Live copy:** chapter and step titles, the four サイトスペース要件 labels, packing-list and 必要品 item names, the 2-① subtitle, the 2-② note, the two warnings, the six App step captions and the 100v サーキット pill.
- **Shared components:** HB-SPECIAL-REFERENCE-FIGURE ×4 (site figure, 2-② wiring, two App screen rows, all base-art-live-copy), the shared package panel for the three item groups (as JHP-3600C US), `hb-text-panel` for the grey note and `hb-source-safety-heading` for the warnings.
- **In the art:** wire legends, the 2-① switching-detail notes, product markings and App UI text. The legends and the switching detail are separate images shown at 0.15 rem per printed pt so their printed labels stay legible.
- **No shared fit:** HB-SPECIAL-APP download needs two column copy lines that the print does not have, so the store badges and QR are plain images. HB-SPECIAL-INBOX takes one single-row group with a tip, so the three item groups use the package panel.

`source/presentation.css` holds geometry only: printed relative item sizes, image widths and note-panel spacing.

## Artwork

`derive_assets.py` derives every file in `assets/` from the PDF and writes `source/asset_decisions.json` with the reuse inventory, each clip and every painted-out region. A second run leaves the tree unchanged.

- Figure panels are clipped inside their dashed print frames, which are found by drawing index.
- Heading glyphs and boxes whose copy is set live are painted out with the paper colour; nothing else in the art changes.
- The yellow warning triangle is rebuilt from its original vector paths, because the shared library has no yellow-filled glyph of this drawing.

No existing asset matched; the decisions record what was checked.

## Source concerns kept verbatim

- Both warnings and the 2-① title end without 。 / する.
- 「ジャクリアプリ」, 「100v」 and the half-width 「;」 in the fourth App caption are as printed.
- 3-③ repeats the chapter 3 title 「蓄電池に接続する」.

These are listed for the source owner and not corrected here.

## Route

Hello-Docs identity is `(model, region, lang)`. The full manual keeps `JA-CK01A-BK/JP/ja` and the `JA-CK01A-BK/JP` legacy default, so this package uses the model segment `JA-CK01A-BK-QG` (route `JA-CK01A-BK-QG/JP/ja/md`), as the operator decided on 2026-10-23 (「改用 JA-CK01A-BK-QG」).

## Rebuild

Run from the repository root (`requirements.lock`: PyMuPDF 1.28.0 / MuPDF 1.29.0; Pandoc 3.9.0.2 as in CI):

```sh
PKG=manual_sources/JA-CK01A-BK-QG/JP/ja/git-20261023-e67d2460-quick-guide
python "$PKG/derive_assets.py"
python "$PKG/refresh_manifest.py"
python "$PKG/render.py" tmp/ja-ck01a-bk-qg-jp
python -m sphinx -n -W --keep-going -b html tmp/ja-ck01a-bk-qg-jp tmp/ja-ck01a-bk-qg-jp-html
```

After any source change, replace `web/ja` with a fresh render, then run `refresh_manifest.py` again: `frozen_source_manifest.json` inventories every package file, including `web/ja` and `evidence/`. `render.py` checks every input hash and the shared component count before writing output.

## Validation and release boundary

```sh
python -m unittest tests.test_ja_ck01a_bk_qg_jp_web tests.test_prepared_document_shared_styles
```

`evidence/` holds the 1280/390 browser acceptance (`browser-acceptance.json`, full-page screenshots) and the validation logs.

After the operator merges the engineering PR, the Git-only transaction continues per [web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline.md#22-git-only-transaction):

1. Seal `seal_frozen_web_evidence` at the merged `main` commit.
2. Assemble from current Hello-Docs `main`.
3. Open a `docs/publish/**`-only PR.
4. Verify the RTD routes, aliases, resources and desktop/mobile pages.

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows and dependencies.
