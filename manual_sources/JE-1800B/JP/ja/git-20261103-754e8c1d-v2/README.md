# JE-1800B / JP / ja — Git-only Web manual candidate (V2)

Operator instruction, 2026-11-03: 「继续 转日语说明书」 (relayed by the coordinator window): convert the JP single-language manuals that have a customer model and a single-language PDF. This package is the JE-1800B manual from the 发布文档管理 Base, 日规 view.

**Status: `candidate-pending-operator-review`.** No operator approval exists; `source/approval.json` is absent and the IR is not publication-eligible.

**Shared symbol dependency.** On 2026-11-03 the operator fixed one canonical shared icon per symbol group (no new variants; relayed by the coordination window). Seven symbols already bind to a canonical under the fixed 2% admission: warning triangle, read manual, keep away from children, mandatory, prohibited, WEEE and the battery bin. Six (no open flame, no disassembly, unplug, no wet hands, no wetting, Li-ion 32) are 2.1–39.5% from their operator canonicals; they keep interim proposed native variants (`native/je1800b-jp-754e8c1d-03/05/06/07/08/11`, not in the catalog) and are rebound once the shared icon de-duplication PR admits operator-confirmed same-group canonicals. Until then `derive_assets.py`, `rebuild.py` and the two replay tests stop or skip at the missing catalog entries.

## Source authority

- Base `WGVwb2HctauRi7sEiKqcIzTRn1c`, table `tbljbjaXaTD6V9PO`, record `reczz28SfbsHfHUZ` (客户型号 JE-1800B, 子物料编码 16-0102-000418, 项目号 HTE2611, sku 21-0001-000548 , 21-0014-000571).
- 单语言说明书 「【Jackery ポータブル電源 1800】说明书-JP.pdf」 (read-only download), stored byte-exact as `JE-1800B-JP-V2.pdf`, SHA-256 `754e8c1d076b7d5fd9d84ac76ce9447dccec4a9351c7b7d756a3225255b4da52`. It is the authoritative Web and symbol-admission source.
- 说明书文件 (print master, recorded only) 「16-0102-000418 竖版说明书 HTE26111800A-JP-JAK.pdf」, SHA-256 `97a33a6da34bf1fc67f804b1405b3af11cc579f3a88837417234769269ff0099`: same 27 pages; the text layer is identical and all pages render pixel-identical at 150 dpi.
- 27 pages, 130 × 185 mm, live text layer. `extract_text.py` freezes every text line unmodified in `source/transcription.json`; `build_content.py` binds the Web copy to those line ids and accounts for every Web-page line in `source/line_dispositions.json`. Suspected source errors are kept verbatim and listed in `source_manifest.json:source_concerns`.
- Model facts come only from this PDF. JE-1500D JP V2 (same V2 layout) and JE-1000D JP V2 supply structure, shared components and scripts.

## Layout

The Web body is printed pages 01–24 (physical 3–26); cover, paper TOC and back cover stay in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); the one plain table is declared in `shared_component_exceptions`. `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry and type size only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. Product, LCD, operation, charging, UPS and App art are complete source panels at 3×, keeping leader lines, captions and phone frames. The in-box cable, 24 LCD icons and 4 buttons are reused byte-identically; LCD ⑪ is a native vector glyph. Symbols: seven reuse shared canonicals (see `source/asset_decisions.json`); six wait for the de-duplication PR.

## Rebuild

From the repository root (`requirements.lock`, Pandoc 3.9.0.2), once every recipe symbol is in the catalog:

```sh
PKG=manual_sources/JE-1800B/JP/ja/git-20261103-754e8c1d-v2
python "$PKG/extract_text.py"        # text layer -> source/transcription.json
python "$PKG/derive_assets.py"       # artwork + symbol admission rows
python "$PKG/build_content.py"       # line ids -> source/ja/content.json
python "$PKG/refresh_manifest.py"    # input inventory
python "$PKG/rebuild.py" --output tmp/je1800b-jp
python -m sphinx -n -W --keep-going -b html tmp/je1800b-jp tmp/je1800b-jp-html
python -m unittest tests.test_je1800b_jp_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/ja` after any source change.

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows, dependencies and the shared symbol catalog.
