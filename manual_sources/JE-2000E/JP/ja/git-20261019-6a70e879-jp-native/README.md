# JE-2000E / JP / ja — Git-only Web manual candidate

**Status: `candidate-pending-operator-review`.** Not publication-eligible: there is no `source/approval.json`. Approval is written only after the operator reviews the 1280/390 renders beside the reference edition and says 「上线提交发布」 in the owning session. No phase2 target, queue record, live Base write or Read the Docs publication is involved.

## Source authority

- 发布文档管理 (日规) record `reczz28SfbsHbvLy`: 客户型号 JE-2000E, 子物料编码 16-0102-000389, 项目号 HTE152, sku 21-0001-000403 (`source_manifest.json:source_record`).
- Authority: the record's 单语言说明书 「【Jackery ポータブル電源 2000 Plus】说明书-JP.pdf」, stored byte-exact as `JE-2000E-JP-V2.pdf`, 28 pages, SHA-256 `f1829cd35ffe05079fe4b04f6c62fef3ca6adfd64270c47d64f7b2203af9780a`. Cover: Jackery ポータブル電源 2000 Plus, JE-2000E, V2, 国内専用.
- Operator decision 2026-11-03 (「按建议做」): continue on this 2026-10-19 candidate and rebind it to the table PDF. The package path keeps its intake identity (`6a70e879`, the record's 说明书文件 print master 「16-0102-000389 Jackery ポータブル電源 2000PlusV2 电子版取扱説明書.pdf」, 9178453 bytes, recorded only). The two files have identical text layers and drawing lists and render pixel-identically on all 28 pages (poppler 200 dpi, MuPDF 3×), so every coordinate, crop and binding carries over unchanged.
- Web body: physical pages 3–28. The printed cover (p1) and paper TOC (p2) stay in the PDF; the back-cover App reminder (p28) closes the App chapter. Japanese copy is kept as printed; `source_manifest.json:source_concerns` lists suspected source errors for the source owner, including the 出カポート specification heading that the earlier candidate had normalized (reverted).

## Reference and component map

Structure follows JE-1000F JP; all model facts come from this PDF. No JE-2000E English or Japanese Web edition exists (EU Web covers nl/pl/pt), so the review reference is the published JE-1500D JP V2 Web edition of the same layout generation. Every printed block maps to a shared component (`source_manifest.json:component_map`); the 省エネモード threshold table is the one declared plain table (`shared_component_exceptions`).

## Artwork and symbols

`source/document.json` holds the reviewed source flow; `native_pages.json`, `text_bindings.json`, `lcd_rows.json`, `text_coverage_review.json` and `asset_decisions.json` retain source coordinates and decisions. Shared LCD icons and matching buttons are byte-identical copies; illustration crops are complete 3× source panels with phone frames kept. `source/geometry.css` is label geometry/typography only.

Safety symbols follow the operator's 2026-11-03 standard-icon decision (one canonical shared icon per group, no new variants). `derive_symbols.py` binds every printed symbol to its group canonical from the shared catalog's `canonical_groups` (decision SCG-20261103, shared PR #1659; `source/symbol_recipe.json`). Seven pass the fixed 2% admission. Five (no open flame 2.1%, unplug 3.8%, no wet hands 5.2%, no wetting 5.4%, Li-ion 32 27.6%) are released to the canonical on their source-verified caption, which the operator-confirmed group lists; the admission report names the group and decision. No variant is added to the shared catalog.

## Rebuild

From the repository root (`requirements.lock`), once every recipe symbol is in the catalog:

```sh
PKG=manual_sources/JE-2000E/JP/ja/git-20261019-6a70e879-jp-native
python "$PKG/derive_symbols.py"      # symbol bindings + admission rows
python "$PKG/refresh_manifest.py"    # input inventory
python "$PKG/rebuild.py" --output tmp/je2000e-jp
python -m sphinx -n -W --keep-going -b html tmp/je2000e-jp tmp/je2000e-jp-html
python -m unittest tests.test_je2000e_jp_web
```

`rebuild.py` checks every input hash and the pinned shared files, replays the source flow through manual-ir/v2 and the shared Web/MyST pipeline, and enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/ja` and refresh the manifest after any source change.

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows, dependencies and the shared symbol catalog.
