# JE-240A / JP / ja — Git-only Web manual candidate

Operator instruction, 2026-11-03: 「继续 转日语说明书」 (发布文档管理, 日规 view `vew0f8smjz`), relayed by the coordination window. This package is the Jackery ポータブル電源 240 (JE-240A) Japanese manual from that table, one of the 24 JP single-language manuals of the batch.

**Status: `candidate-pending-operator-review`.** No `source/approval.json` exists and the IR is not publication-eligible. The operator reviews the 1280/390 renders beside the shared reference edition (the same-model JE-240A US/en Web edition) first; approval is written only after the operator's own 「上线提交发布：…」 in this window. Hello-Docs/RTD publication follows [web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline/input-paths.md#22-git-only-transaction).

## Source authority

- 发布文档管理 record `reczz28SfbsHdX6k`: 子物料编码 38-0001-000445, 项目号 HTE110, SKU 21-0001-000215. Field 单语言说明书 「【Jackery ポータブル電源 240】说明书-JP.pdf」, stored byte-exact as `JE-240A-JP-JA.pdf`, SHA-256 `e227d165efcd389a260bb1b3f1a234c365c81465c01492c7e86d674afd8af2cf`; printed version V2. The 说明书文件 print master is recorded in `source_manifest.json:design_original` (name, SHA-256) and not committed.
- 14 pages, 130 × 185 mm. Every glyph is outlined (no text layer). `source/transcription.json` is the line-by-line transcription from 300 dpi renders, re-checked on 600 dpi clips. Wording, punctuation and spelling are kept as printed; `source_manifest.json:source_concerns` lists suspected source errors for the source owner.
- Model facts come only from this PDF. JE-240A US/en supplies same-model artwork and the component map; JE-1000D JP V2 supplies the Japanese structure, component chrome and shared symbol variants.

## Layout

The Web body is printed pages 1–13 (physical 2–14); the cover stays in the PDF (there is no paper TOC or back cover). Every printed block maps to a shared component (`source_manifest.json:component_map`); the two plain tables are declared in `shared_component_exceptions`. `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry and type size only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. Product, LCD, charging, badge and App art are complete source panels at 3×, keeping leader lines, captions and phone frames. Six LCD icons are reused byte-identically: the battery ring and F8 icons (JE-1000F JP shared-lcd), the 88H mark (JE-240A US) and the low-battery and two temperature vectors (JE-1000D JP); the Li-ion 32 recycling mark is the original PDF vector paths. All six 絵表示の説明 symbols pass the fixed 2% admission against existing shared variants (`native/je1000d-jp-00c43a89-01/02/03/05/06`, `mandatory/h1-jp-native`); no new shared symbol is needed.

## Rebuild

From the repository root (`requirements.lock`, Pandoc 3.9.0.2):

```sh
PKG=manual_sources/JE-240A/JP/ja/git-20261103-e227d165
python "$PKG/derive_assets.py"        # artwork + symbol admission rows
python "$PKG/build_content.py"        # transcription -> source/ja/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/je240a-jp
python -m sphinx -n -W --keep-going -b html tmp/je240a-jp tmp/je240a-jp-html
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/ja` after any source change. The JE-1000F JP `build.py check` is a repository regression gate only.

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows and dependencies.
