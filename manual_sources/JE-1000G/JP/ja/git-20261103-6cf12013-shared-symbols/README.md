# JE-1000G / JP / ja — Git-only Web manual candidate, shared-symbol follow-up (Jackery ポータブル電源 1000 New, V3)

Coordinator batch, 2026-11-03: JP/ja Git-only Web candidates for the 发布文档管理 records of JE-1000C, JE-1000G, JE-1000H and JE-1500B. This package is the JE-1000G Japanese manual of record `reczz28SfbsHbQU5` (子物料编码 16-0102-000396, 项目号 HTE158, SKU 21-0001-000447 / 21-0001-000448, 区域 日规). This version follows the released `git-20261103-6cf12013` (frozen, unchanged) after the shared symbol dedupe PR #1659 (`canonical_groups`, MA-384).

**Status: `candidate-pending-operator-review`.** The operator must re-approve: there is no `source/approval.json` and the IR is not publication-eligible. Changes from the released version: the withheld 本製品を火気の近くに置かないでください。 row is now in the 絵表示の説明 table, bound to the operator-chosen canonical `no-open-flame/fire-match-prohibited`, and every symbol row binds the canonical of its operator-confirmed group (unplug → `unplug/h1-jp-native`, wet hands → `native/je1000d-jp-00c43a89-03`, keep dry → `native/je1000d-jp-00c43a89-05`; the other six were already canonicals). Same authoritative PDF, same transcription text and the same artwork otherwise.

## Source authority

- 「【Jackery ポータブル電源 1000 New】说明书-JP.pdf」, stored byte-exact as `JE-1000G-JP-JA.pdf`, SHA-256 `6cf120136d8366ad37f590610d739e09754ddc38d4c8cd3123d9dca0de132aad`, 2,804,108 bytes. Cover: Jackery ポータブル電源 1000 New 取扱説明書, 型番: JE-1000G / JE-1000G-WH, V3, 国内専用/For use only in Japan.
- 28 pages, 130 × 185 mm, with a text layer. `source/transcription.json` is the line-by-line transcription taken from that layer and checked against renders; wording, punctuation and full/half width are kept as printed. `source_manifest.json:source_concerns` lists suspected source errors for the source owner.
- The print master 「16-0102-000396 HTE1581000A-JP-JAK 说明书 RoHS REACH.pdf」 (SHA-256 `a573754e3b942e58845aac8f50ec9c262063cc71e4757574300e2f6e0d869c00`) is recorded as reference only and not committed.
- Model facts (ratings, ports, UPS 10ms, temperatures, warranty) come only from this PDF. JE-1000F JP (same 1000 New layout) supplies the reference edition and reused art; JE-1000D JP V2 and JE-2000F US/en supply the package structure and component idiom.

## Layout

The Web body is printed pages 01–25 (physical 3–27); cover, paper TOC and back cover stay in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); the two plain tables (recycling box, 省エネモード port table) are declared in `shared_component_exceptions`. `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry and type size only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. The LCD map, 26 LCD icons, four buttons and two in-box drawings are existing files reused byte-identically (each checked against this PDF); product, operation, charging and App art are complete source panels at 3×, with in-panel body copy carried as native text. The in-box cable and the Li-ion/crossed-bin marks are the original PDF vector paths. All ten safety symbols bind the canonical of their operator-confirmed shared symbol group: six pass the fixed 2% comparison, four (火気, unplug, wet hands, keep dry) are released through their listed captions under decision SCG-20261103 (`source_manifest.json:symbol_asset_admission`); no shared file is added and no glyph waiver is used.

## Rebuild

From the repository root (`requirements.lock`, Pandoc 3.9.0.2):

```sh
PKG=manual_sources/JE-1000G/JP/ja/git-20261103-6cf12013-shared-symbols
python "$PKG/derive_assets.py"        # artwork + symbol admission rows
python "$PKG/build_content.py"        # transcription -> source/ja/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/je1000g-jp
python -m sphinx -n -W --keep-going -b html tmp/je1000g-jp tmp/je1000g-jp-html
python -m unittest tests.test_je1000g_jp_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, and enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/ja` after any source change.

Not touched: live Base, queue, source tables, HTML_link, asset registry, frozen package registry, shared symbols, workflows and dependencies.
