# JS-CONNECTION-GUIDE / JP / ja — solar generator connection guide (接続ガイド) Web candidate

Operator instruction, 2026-10-26: 「分几个窗口把这个目录下面的文档都转成网页文档」, then 「韩语文档除外」. This window converts the connection-guide leaflet only; the JE-1000D JP and JS-100I JP manuals from the same folder are separate targets converted in parallel. The operator decided (2026-10-26) that only the Japanese face goes on the Web, under the route model segment `JS-CONNECTION-GUIDE`. No Japanese wording is changed.

**Status: `operator-approved-git-only-release`.** The operator reviewed candidate `eb61b66` (PR #1610: 1280/390 renders and the comparison against the PDF and the JA-CK01A-BK-QG JP reference edition) and instructed 「上线提交发布」 on 2026-10-27. The engineering PR is merged by operator review (AGENTS.md §8.6), not by an agent grant. `source/approval.json` binds every reviewed `source/` and `assets/` input hash; the rendered IR is publication-eligible. Changing a reviewed input invalidates the acceptance: `render.py` then refuses until a new operator acceptance is recorded.

## Source

`source/original.pdf` is the Feishu wiki file `38-0001-000716 太阳能板连接指南折页 通用 RoHS REACH-Q.pdf` (wiki node `SMatwBk68ifDEwkYJiucwZVsndf`), byte-exact, SHA-256 `bc35fd6518769bd26c88fee088cc3a748c0ef680f4419682bede0f62738f8821`. It is one Illustrator 29.3 production artboard (2190×1531 pt, created 2025-02-11, modified 2025-06-06) holding both printed sides of a 260×185 mm single-fold leaflet: the international face (EN/FR/ES/PT interleaved) on the left and the Japanese face on the right, framed by the drawing title block (part 38-0001-000716, drawing V0.1 第一次发行, 2025-1-6). The drawing version is not a printed manual version; `printed_manual_version` stays unknown. The leaflet prints no product model.

The type is outlined, so the PDF has no text layer. `source/transcription.json` records every printed line of the Japanese face verbatim, in Web reading order, with its disposition: `live` (Web text), `in-art` (kept inside a named artwork file) or `web-excluded` (international face, wordmark, production furniture).

## Web structure and shared components

One page under the printed title. `component_map` in `source_manifest.json` maps every printed block:

- **Live copy:** the title, the introductory sentence, the grey note (lead and ※ note), the whole ポータブル電源の型番 / DC入力 table (model names, 0.9mm / 2.0mm, port names), the two speech bubbles and the two port captions.
- **Shared components:** `hb-text-panel` for the grey note; HB-SPECIAL-REFERENCE-FIGURE ×2 (base-art-live-copy) for the DC7909 and DC8020 connection figures, with the bubbles as live pills and the port captions as live labels.
- **Declared exception:** the compatibility table is a plain native table (`shared_component_exceptions`): no shared ComponentSpec takes a model list with a port per group. It uses the shared table styling only.
- **In the art:** connector tags (DC7909 / DC8020) inside the magnified insets, the numbered markers 1/2 and 「または」 between the two alternatives, as the quick guide kept its wire legends in the art.

`source/presentation.css` holds geometry only: port icon size, column width and alignment, note-panel spacing.

## Artwork

`derive_assets.py` derives every file in `assets/` from the PDF and writes `source/asset_decisions.json` with the reuse inventory, each clip, every painted-out region and the live-label rectangles. A second run leaves the tree unchanged.

- The connection figures are the table's right-hand cells, clipped inside their rules; the bubbles and port captions set live are painted out with the paper colour, found by drawing index, and the table frame's rounded corner is painted out of the last cell.
- The port icons are the placed rasters, with the PDF soft mask where it has one (DC7909, DC8020: transparent), plus the orange dimension marks redrawn from their vectors. The USB-C raster has no soft mask and keeps the white corners it has on the white print cell.

No existing asset matched; the decisions record what was checked (including the JS-100I EU line drawings of the same ports).

## Source concerns kept verbatim

- Title 「Jackery Solar Genarator 接続ガイド」: 「Genarator」 (the international face prints 「Generator」).
- 「Jackeryポータブル電源 240（PTB201）」 has no space after Jackery, unlike every other row.
- 「Jackery ポータブル電源 700」 is the only row without a model code.
- The note lead ends with a half-width 「:」, and announces 「次の解決策」 while the ※ line states an incompatibility.

These are listed for the source owner and not corrected here.

## Route

Hello-Docs identity is `(model, region, lang)`. The leaflet prints no model, so the package uses the model segment `JS-CONNECTION-GUIDE` (route `JS-CONNECTION-GUIDE/JP/ja/md`), as the operator decided on 2026-10-26.

## Rebuild

Run from the repository root (`requirements.lock`: PyMuPDF 1.28.0 / MuPDF 1.29.0; Pandoc 3.9.0.2 as in CI):

```sh
PKG=manual_sources/JS-CONNECTION-GUIDE/JP/ja/git-20261026-bc35fd65-connection-guide
python "$PKG/derive_assets.py"
python "$PKG/refresh_manifest.py"
python "$PKG/render.py" tmp/js-connection-guide-jp
python -m sphinx -n -W --keep-going -b html tmp/js-connection-guide-jp tmp/js-connection-guide-jp-html
```

After any source change, replace `web/ja` with a fresh render, then run `refresh_manifest.py` again: `frozen_source_manifest.json` inventories every package file, including `web/ja` and `evidence/`. `render.py` checks every input hash and the shared component count before writing output.

## Validation and release boundary

```sh
python -m unittest tests.test_js_connection_guide_jp_web tests.test_prepared_document_shared_styles
```

`evidence/` holds the 1280/390 browser acceptance (`browser-acceptance.json`, full-page screenshots), the comparison sheet against the PDF and the JA-CK01A-BK-QG JP reference edition, and the validation logs.

After the operator merges the engineering PR, the Git-only transaction continues per [web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline/input-paths.md#22-git-only-transaction): seal the evidence at the merged `main` commit, assemble from current Hello-Docs `main`, open a `docs/publish/**`-only PR and verify the RTD routes and pages.

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows and dependencies.
