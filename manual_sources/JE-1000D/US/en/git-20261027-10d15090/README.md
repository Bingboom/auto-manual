# JE-1000D / US / en — Git-only Web manual

Operator instruction, 2026-10-27: 「把这个表中 未转网页版的说明书 走git only进行单语网页文档的转换」. This package is the Jackery Explorer 1000 v2 (JE-1000D) US English manual from that table (record `reczz28SPRx9pE14`, 物料号「文本」38-0001-000612, 项目号 HTE109).

**Status: `operator-authorized-git-only-release`.** The operator authorized release on 2026-10-28 (「上线提交发布：JE-1000D、JE-1500B、JE-1500D、JE-2000A；授权合入 #1629 及其 Hello-Docs 发布 PR」) and checks each page's layout after it goes live. `source/approval.json` binds every reviewed `source/` and `assets/` input; the IR is publication-eligible. The source copy goes live as printed; `source_manifest.json:source_concerns` goes back to the source owner.

## Source authority

- 「【Jackery Explorer 1000 v2】说明书-EN.pdf」, stored byte-exact as `JE-1000D-US-EN.pdf`, SHA-256 `10d15090f944d3a0a1518e495dca4cf5cad15252220990c1b0e324564519316f`, 14 pages, 130 × 185 mm. Cover: Jackery, V2, USER MANUAL, Jackery Explorer 1000, Model: JE-1000D.
- It is the US section (plus cover and back cover) of the 52-page artwork 「38-0001-000612 Jackery Explorer 1000 v2 (1).pdf」 (SHA-256 `572b54ea…`, not committed): EN 1 = original 1, EN 2–13 = original 3–14, EN 14 = original 52.
- The PDF has a real text layer. `source/transcription.json` is the line-by-line transcription taken from it and checked against 300 dpi renders; wording, spelling, punctuation and capitalisation are as printed (ligature code points written as letters, see `source/differences.md`). Suspected source errors are listed for the source owner, not corrected.
- Model facts (ratings, ports, UPS 20ms, emergency charging, energy-saving defaults, temperatures, warranty) come only from this PDF. JE-1000D JP V2 supplies structure, shared components and byte-identical LCD icons.

## Layout

The Web body is printed pages 01–12 (physical 2–13); cover and back cover stay in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); the one plain table (Energy Saving Mode, spanning Defaults cell) is declared in `shared_component_exceptions`. `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. Product, LCD, LED, charging, badge and App art are complete source panels at 3×, keeping leader lines, captions and phone frames. Four LCD icons are the JE-1000D JP SVGs and the FCC/WEEE marks are shared catalog files, all byte-identical and each passing the fixed 2% comparison with the EN native paths (`source_manifest.json:artwork_reuse_comparison`). The battery ring, 88H, F8, quiet-charging icons and the BC mark are the original PDF vector paths (transparent). The manual prints no symbol table, so symbol admission has no rows.

## Rebuild

From the repository root (`requirements.lock`, Pandoc 3.9.0.2):

```sh
PKG=manual_sources/JE-1000D/US/en/git-20261027-10d15090
python "$PKG/derive_assets.py"        # artwork + reuse comparison
python "$PKG/build_content.py"        # transcription -> source/en/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/je1000d-us
python -m sphinx -n -W --keep-going -b html tmp/je1000d-us tmp/je1000d-us-html
python -m unittest tests.test_je1000d_us_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/en` after any source change.

Not touched: live Base, queue, source tables, HTML_link, asset registry, shared symbol catalog, workflows and dependencies.
