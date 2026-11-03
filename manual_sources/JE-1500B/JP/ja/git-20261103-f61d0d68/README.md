# JE-1500B / JP / ja — Git-only Web manual candidate (ポータブル電源 1500 Pro)

This package is the JE-1500B Japanese manual of Feishu record `reczz28SfbsHeofK` (子物料编码 38-0001-000276, 项目号 HTE080, SKU 21-0001-000003, 区域 日规), built as one of the JP/ja Git-only Web candidates (JE-1000C, JE-1000G, JE-1000H, JE-1500B).

**Status: `candidate-pending-operator-review`.** There is no `source/approval.json`; the IR is not publication-eligible. The operator reviews the 1280/390 renders (`evidence/`) beside the JE-1500B US/en Web edition and the source correction list (`source_manifest.json:source_concerns`) before any release.

## Source authority

- 「【Jackery ポータブル電源 1500 Pro】说明书-JP.pdf」, stored byte-exact as `JE-1500B-JP-JA.pdf`, SHA-256 `f61d0d68f37c32ceb7441d0853da40ad1087e7241a4bf925089d86f8074b0a65`, 3,029,337 bytes. Cover: Jackery ポータブル電源, JE-1500B, Jackery-UM-002, Jackery ポータブル電源 1500 Pro 取扱説明書, 国内専用/For use only in Japan.
- 14 pages, 130 × 185 mm. Every glyph is outlined (no text layer). `source/transcription.json` is the line-by-line transcription (tesseract jpn draft, each line checked on 300 dpi renders and 600–900 dpi clips). Wording, punctuation and full/half width are kept as printed; `source_manifest.json:source_concerns` lists suspected source errors for the source owner.
- The print master 「38-0001-000276 说明书 HTE0801500B-JP-JAK  RoHS REACH.ai」 (SHA-256 `cbc0fd6400dd1451a01596a16820b3c9749a25248b5a90552c8d4877be0c8927`, 12,975,431 bytes) is recorded as reference only; it is not committed and not extracted.
- Model facts (ratings, ports, temperatures, 1800W, 12-hour low power mode) come only from this PDF. JE-1000D JP V2 supplies the package structure; JE-1500B US/en supplies five reused LCD icon files.

## Layout

The Web body is physical pages 2–14 (printed 1–12; the last page prints no number); the cover stays in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); the recycling notice and the 低電力モード table are declared plain tables in `shared_component_exceptions`. `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry and type size only.

**Pending:** the 絵表示の説明 symbol table (six rows, physical page 9) is not on the page yet. Symbol admission rebuilds each row's reference with the shared `native_symbol_svg` selector, which refuses every page of this single-artboard PDF. `source/asset_recipe.json:pending_symbols` holds the binding data (drawing indices, glyph and caption boxes, caption pixel hashes, closest shared variants) for the shared fix.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. Product, LCD, charging and package-list art are complete source crops at 3×, keeping frames, leader lines, X marks and captions; Japanese captions and the JP print's line weights need JP crops. Five LCD icons are reused byte-identically from JE-1500B US/en (each within the fixed 2% of its JP vector paths); the high-temperature icon and the Li-ion 20 recycling mark are the original PDF vector paths.

## Rebuild

From the repository root (`requirements.lock`, Pandoc 3.9.0.2):

```sh
PKG=manual_sources/JE-1500B/JP/ja/git-20261103-f61d0d68
python "$PKG/derive_assets.py"        # artwork + (empty) symbol admission rows
python "$PKG/build_content.py"        # transcription -> source/ja/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/je1500b-jp
python -m sphinx -n -W --keep-going -b html tmp/je1500b-jp tmp/je1500b-jp-html
python -m unittest tests.test_je1500b_jp_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, and enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/ja` after any source change.

Not touched: live Base, queue, source tables, HTML_link, asset registry, shared symbols, workflows and dependencies.
