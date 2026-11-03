# JE-2000D / JP / ja — Git-only Web manual candidate (print model JE-2000D-SG)

Coordinator brief, 2026-11-03: build the Japanese single-language Web candidate of 发布文档管理 record `reczz28SfbsHec2z` (子物料编码 38-0001-000766, 项目号 HTE117, sku 21-0001-000339; `source_manifest.json:feishu_source`).

**Status: `candidate-pending-operator-review`.** There is no `source/approval.json`; the IR is not publication-eligible. Operator review compares the 1280/390 renders in `evidence/` with the same-model JE-2000D US en Web edition and decides the `source_concerns`.

**Route.** `JE-2000D/JP/ja/md`: route JE-2000D per operator decision 2026-11-03 (JE-2000D-SG is the colour variant of JE-2000D; route JE-2000D covers both colours). The 发布文档管理 customer model is JE-2000D-SG (`source_manifest.json:feishu_source`), and the print names JE-2000D-SG on the cover and in the specification table (型番：JE-2000D-SG, 色：サンドゴールド); that printed text stays verbatim on the Web.

## Source authority

- 「【Jackery ポータブル電源 2000】说明书-JP.pdf」 from the record, stored byte-exact as `JE-2000D-JP-JA.pdf`, SHA-256 `62605f215fe45b9ab600b44be336e217d854292e14921833b0d26e51a665709f`, 3,664,234 bytes. 12 single portrait pages of 129.5 × 184.5 mm (cover + printed pages 1–11; not 2-up spreads), no TOC, no back cover, no warranty chapter.
- The print master 「38-0001-000766 HTE1172000A-JP-JAK 沙金色 说明书 RoHS REACHq.pdf」 (SHA-256 `53abd4ee…40ea921348`, 14,463,688 bytes) is recorded only: not committed and not read by any script.
- Every glyph is outlined (no text layer). `source/transcription.json` is the line-by-line transcription, checked on 300 dpi renders with 450–600 dpi clips for ambiguous glyphs. Wording, punctuation and model spellings are kept as printed; `source_manifest.json:source_concerns` lists suspected source errors for the source owner.
- Model facts (2042Wh, 2200W/4400W, UPS 20ms and bypass 1500W, DC inputs, temperatures) come only from this PDF. JE-1000D JP V2 supplies the block-to-component idiom; JE-2000D US en supplies byte-identical LCD icons.

## Layout

The Web body is printed pages 1–11 (physical 2–12); the cover stays in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); the two plain tables (recycling box, 省エネモード table) are declared in `shared_component_exceptions`. `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry and type size only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. Seven LCD icons are the JE-2000D US files and the 88H mark the JE-1000D JP V2 file, byte-identical and within the fixed 2% of the native paths (`source_manifest.json:artwork_reuse_comparison`). Product, LCD map, in-box, charging and App art are new complete panels at 3× (no earlier package carries the same JP art: the JE-1000D JP App panels measure 0.015–0.08 and show Explorer 1000 screens). The Li-ion 32 mark is native PDF paths. Safety symbols are shared catalog files only (`source_manifest.json:symbol_asset_admission`); nothing was added to the shared library.

## Rebuild

From the repository root (`requirements.lock`, Pandoc 3.9.0.2):

```sh
PKG=manual_sources/JE-2000D/JP/ja/git-20261103-62605f21
python "$PKG/derive_assets.py"        # artwork, reuse comparison, symbol admission rows
python "$PKG/build_content.py"        # transcription -> source/ja/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/je2000d-jp
python -m sphinx -n -W --keep-going -b html tmp/je2000d-jp tmp/je2000d-jp-html
python -m unittest tests.test_je2000d_jp_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, and enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/ja` after any source change.

Not touched: live Base, queue, source tables, HTML_link, asset registry, frozen package registry, shared symbol library, workflows and dependencies.
