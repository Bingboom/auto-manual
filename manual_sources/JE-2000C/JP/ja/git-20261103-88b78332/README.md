# JE-2000C / JP / ja — Git-only Web manual

Operator instruction, 2026-11-03: 「继续 转日语说明书」 (relayed by the coordination window): convert the Japanese single-language manuals of the 发布文档管理 Base that have a customer model and a single-language PDF and are not yet on the Web. This package is the Jackery ポータブル電源 2000 Plus (JE-2000C) Japanese manual.

**Status: `operator-authorized-git-only-release`.** The operator reviewed the 1280/390 renders beside the shared reference edition (Draft PR #1656) and replied 「按建议做，上线提交发布」 on 2026-11-03 in the owning session. Source copy goes live as printed; `source_manifest.json:source_concerns` go back to the source owner. `source/approval.json` binds every reviewed `source/` and `assets/` input; the IR is publication-eligible. Merge still needs the operator's own authorization (AGENTS.md §8.6).

## Source authority

- Base record `reczz28SfbsHdjSC`: 子物料编码 38-0001-000384, 项目号 HTE099, sku 21-0001-000211.
- 「单语言说明书」 「【Jackery ポータブル電源 2000 Plus】说明书-JP.pdf」, stored byte-exact as `JE-2000C-JP.pdf`, SHA-256 `88b78332342866ccd994cfa054a8a63a5fe30fa41131de5c7d53f16cd590690b`. Cover: Jackery ポータブル電源 JE-2000C, Jackery-UM-002, 取扱説明書, 国内専用/For use only in Japan.
- 「说明书文件」 print master 「38-0001-000384 说明书 HTE0992000A-JP-JAK  RoHS REACH-竖版.pdf」, SHA-256 `bc5898aa…dda7b23`, recorded in `source_manifest.json:source_record` for identity only (not an extraction source, not committed).
- 16 pages, 130 × 185 mm, with a real text layer. `build_transcription.py` derives `source/transcription.json` from it through `source/line_map.json`, which binds every native line to a Web line id or excludes it with a reason (cover, page numbers, art lettering, badge digits). Wording, punctuation and model spellings are kept as printed; `source_manifest.json:source_concerns` lists suspected source errors for the source owner.
- Model facts come only from this PDF. JE-2000C US/en (same model) and JE-1000D JP V2 supply structure, component mapping and reusable artwork. Review reference edition: JE-2000C US/en.

## Layout

The Web body is physical pages 2–16 (printed 1–14 and the back-cover App download). Every printed block maps to a shared component (`source_manifest.json:component_map`); the two plain tables are declared in `shared_component_exceptions`. `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry and type size only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. Product, LCD, charging and App art are complete source panels at 3×, keeping frames, leader lines, captions and phone frames. Two LCD icons are the JE-2000C US/en files byte-identically; five LCD icons and the recycle arrows are original PDF vector paths (transparent). All six safety symbols reuse existing shared catalog variants that pass the fixed 2% symbol admission; nothing was added to the shared catalog.

## Rebuild

From the repository root (`requirements.lock`):

```sh
PKG=manual_sources/JE-2000C/JP/ja/git-20261103-88b78332
python "$PKG/build_transcription.py"  # PDF text layer + line_map -> source/transcription.json
python "$PKG/derive_assets.py"        # artwork + symbol admission rows
python "$PKG/build_content.py"        # transcription -> source/ja/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/je2000c-jp
python -m sphinx -n -W --keep-going -b html tmp/je2000c-jp tmp/je2000c-jp-html
python -m unittest tests.test_je2000c_jp_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/ja` after any source change.

Not touched: live Base, queue, source tables, HTML_link, asset registry, shared symbol catalog, workflows and dependencies.
