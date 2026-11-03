# JE-1000C / JP / ja — Git-only Web manual candidate

Coordinator batch, 2026-11-03: JP/ja monolingual manuals JE-1000C, JE-1000G, JE-1000H and JE-1500B to Git-only Web candidates. This package is the JE-1000C (Jackery ポータブル電源 1000 Plus) Japanese manual.

**Status: `candidate-pending-operator-review`.** No `source/approval.json`; the IR is not publication-eligible. The operator reviews the 1280/390 renders and the `source_concerns` list before any release decision (AGENTS.md §8.6).

## Source authority

- 「【Jackery ポータブル電源 1000 Plus】说明书-JP.pdf」 (record `reczz28SfbsHeXKZ`, 子物料编码 38-0001-000371, 项目号 HTE103, sku 21-0001-000210), stored byte-exact as `JE-1000C-JP-JA.pdf`, SHA-256 `a369a8d0ac33d7f6d7843d404796f7eacfc69c221948318f81f6ca9d2311d9d3`. Cover: Jackery ポータブル電源, JE-1000C, Jackery-UM-003, 取扱説明書, 国内専用/For use only in Japan.
- 14 pages, 130 × 185 mm. Every glyph is outlined (no text layer). `source/transcription.json` is the line-by-line transcription, checked on 300 dpi renders with 700 dpi clips for ambiguous glyphs. Wording, punctuation and model spellings are kept as printed; `source_manifest.json:source_concerns` lists suspected source errors for the source owner.
- The print master 「38-0001-000371 HTE1031000A-JP-JAK 说明书 RoHS REACH-Q.pdf」 is recorded by name, size and SHA-256 only; it is not committed or extracted.
- Model facts (1264.64Wh, 2000W/4000W, DC 拡張ポート, EPS 20ms, 12H energy saving) come only from this PDF. JE-1000D JP V2 supplies structure and shared components.

## Layout

The Web body is printed pages 1–12 (physical 2–13); cover and back cover stay in the PDF (there is no paper TOC). Every printed block maps to a shared component (`source_manifest.json:component_map`); the two plain tables are declared in `shared_component_exceptions`. `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry and type size only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. Product, LCD, charging, in-box and App art are complete source panels at 3×, keeping leader lines, captions and phone frames. Four small LCD icons are the original PDF vector paths (transparent). Four files are reused byte-identically from JE-1000D JP V2. All six safety symbols reuse existing shared variants that pass the fixed 2% admission against this PDF; no shared catalog file is added.

## Rebuild

From the repository root (`requirements.lock`, Pandoc 3.9.0.2):

```sh
PKG=manual_sources/JE-1000C/JP/ja/git-20261103-a369a8d0
python "$PKG/derive_assets.py"        # artwork + symbol admission rows
python "$PKG/build_content.py"        # transcription -> source/ja/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/je1000c-jp
python -m sphinx -n -W --keep-going -b html tmp/je1000c-jp tmp/je1000c-jp-html
python -m unittest tests.test_je1000c_jp_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/ja` after any source change.

Not touched: live Base, queue, source tables, HTML_link, asset registry, shared symbol catalog, workflows and dependencies.
