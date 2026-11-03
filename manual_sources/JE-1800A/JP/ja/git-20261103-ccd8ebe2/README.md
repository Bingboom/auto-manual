# JE-1800A / JP / ja — Git-only Web manual

Operator instruction, 2026-11-03: 「继续 转日语说明书」 (relayed by the coordinator window: the JP single-language manuals of the 发布文档管理 日规 view that have a customer model and a single-language PDF). This package is the JE-1800A Japanese manual.

**Status: `operator-authorized-git-only-release`.** The operator reviewed the 1280/390 renders beside the shared reference edition (Draft PR #1656) and replied 「按建议做，上线提交发布」 on 2026-11-03 in the owning session. Source copy goes live as printed; `source_manifest.json:source_concerns` go back to the source owner. `source/approval.json` binds every reviewed `source/` and `assets/` input; the IR is publication-eligible. Merge still needs the operator's own authorization (AGENTS.md §8.6).

## Source authority

- 发布文档管理 record `reczz28SfbsHfSTa` (子物料编码 38-0001-000702, 项目号 HTE131, SKU 21-0001-000311 / 21-0014-000255), 「单语言说明书」 column 「【Jackery ポータブル電源 1800】说明书-JP.pdf」, stored byte-exact as `JE-1800A-JP.pdf`, SHA-256 `ccd8ebe25b3e5ab0a429ce0c4c4ffbe0fe47a34cee8bff3566228b3a9152ca91`. Cover: Jackery ポータブル電源 1800, JE-1800A, 取扱説明書, 国内専用/For use only in Japan; no printed version mark.
- The 「说明书文件」 print master (「38-0001-000702 HTE1311800A-JP-JAK 说明书 RoHS REACHq.pdf」, SHA-256 `6960a73bff3d94e761387077dd3c62441f08d50454996122de76695b914d5be5`) is recorded in `source_manifest.json` for identity only; it is not committed or read.
- 12 pages, 130 × 185 mm. Every glyph is outlined (no text layer). `source/transcription.json` is the line-by-line transcription, read on 300 dpi renders with 500 dpi clips for ambiguous glyphs. Wording, punctuation and model spellings are kept as printed; `source_manifest.json:source_concerns` lists suspected source errors for the source owner.
- Model facts (ratings, ports, 2200W AC output, UPS 20ms, emergency charge mode, energy-saving defaults, temperatures) come only from this PDF. JE-1000D JP V2 (same layout generation) and JE-1500D JP V2 supply structure and shared components.

## Layout

The Web body is printed pages 1–11 (physical 2–12); the cover stays in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); the two plain tables are declared in `shared_component_exceptions`. `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry and type size only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. Product, LCD, charging and App art are complete source panels at 3×, keeping leader lines, captions and phone frames. Five LCD icons reuse the JE-1000D JP SVG bytes (each passes the fixed 2% glyph comparison against this PDF); the battery ring, F8 fault, quiet-charging icons and the Li-ion mark are original PDF vector paths (transparent). All six safety symbols reuse existing shared catalog variants that pass the fixed 2% symbol admission; no shared catalog file is added.

## Rebuild

From the repository root (`requirements.lock`, Pandoc 3.9.0.2):

```sh
PKG=manual_sources/JE-1800A/JP/ja/git-20261103-ccd8ebe2
python "$PKG/derive_assets.py"        # artwork + symbol admission rows
python "$PKG/build_content.py"        # transcription -> source/ja/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/je1800a-jp
python -m sphinx -n -W --keep-going -b html tmp/je1800a-jp tmp/je1800a-jp-html
python -m unittest tests.test_je1800a_jp_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/ja` after any source change.

Not touched: live Base, queue, source tables, HTML_link, asset registry, shared symbol catalog, workflows and dependencies.
