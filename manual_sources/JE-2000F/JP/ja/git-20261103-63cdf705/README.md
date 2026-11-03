# JE-2000F / JP / ja — Git-only Web manual candidate

Coordinator brief, 2026-11-03: build the Japanese single-language Web candidate of 发布文档管理 record `reczz28SfbsHbLFx` (Jackery ポータブル電源 2000 New, 子物料编码 16-0102-000408, 项目号 HTE154, SKU 21-0001-000489 / 21-0001-000441 / 21-0001-000442; the record's customer model is JE-2000F-WH). Operator decision, 2026-11-03: route it as JE-2000F (`JE-2000F/JP/ja/md`); the cover lists JE-2000F / JE-2000F-SG / JE-2000F-WH. The earlier unreleased candidate git-20261019-d10ae5e0 was voided by the operator the same day.

**Status: `candidate-pending-operator-review`.** No `source/approval.json`; the IR is not publication-eligible. Review beside the shared reference edition, the JE-2000F US English Web (`manual_sources/JE-2000F/US/en/git-20261028-c8ace563`).

## Source authority

- The record's single-language PDF 「【Jackery ポータブル電源 2000 New】说明书-JP.pdf」, stored byte-exact as `JE-2000F-JP-JA.pdf`, SHA-256 `63cdf705e41a1680ca974cc69e5f233cd0e5e4d278d5cc5302dcb3389b361393`, 27 pages, 130 × 185 mm. The print master 「16-0102-000408 竖版说明书 HTE1542000A-JP-JAK.pdf」 is recorded by name, size and hash only (`source_manifest.json:feishu_source`).
- The PDF has a real text layer. `source/transcription.json` is the text-layer transcription, checked against renders; for every page the character multiset of the transcription equals the text layer. Wording, punctuation and numbers are kept as printed; `source_manifest.json:source_concerns` lists suspected source errors for the source owner.
- Model facts come only from this PDF; the JE-2000F US/en package supplies reusable artwork and component idiom, JE-1000D JP V2 the JP pipeline.

## Layout

The Web body is printed pages 01–24 (physical 3–26); cover, paper TOC and back cover stay in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); two plain tables are declared in `shared_component_exceptions` (Li-ion 32 recycling notice, 省エネモード port table). `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. 26 files are reused byte-identically (19 LCD icons, 4 buttons and the in-box documents card from JE-2000F US/en, the in-box cable from JE-1500D JP V2, the App badge pair), each LCD/button/in-box file re-checked by the fixed 2% comparison against this PDF. Seven LCD icons and the Li-ion 32 mark are original PDF vector paths; product, operation, charging and App art are complete 3× source panels. All twelve symbol-table marks pass the fixed 2% symbol admission with existing shared variants; no catalog file is added. **Pending:** the Li-ion 32 recycling mark has no admitted shared variant (`source_manifest.json:pending_shared_symbols`).

## Rebuild

From the repository root (`requirements.lock`):

```sh
PKG=manual_sources/JE-2000F/JP/ja/git-20261103-63cdf705
python "$PKG/derive_assets.py"        # artwork + symbol admission rows
python "$PKG/build_content.py"        # transcription -> source/ja/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/je2000f-jp
python -m sphinx -n -W --keep-going -b html tmp/je2000f-jp tmp/je2000f-jp-html
python -m unittest tests.test_je2000f_jp_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/ja` after any source change; `refresh_manifest.py frozen` runs only at release sealing.

Not touched: live Base, queue, source tables, HTML_link, asset registry, frozen package registry, shared symbol catalog, the voided earlier candidate, workflows and dependencies.
