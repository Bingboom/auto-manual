# JE-1000H / JP / ja — Git-only Web manual candidate (Jackery ポータブル電源 1000 Plus, V2)

Coordinator batch (JE-1000C, JE-1000G, JE-1000H, JE-1500B JP/ja): convert the operator-provided monolingual JP manuals to Git-only Web candidates. This package is the JE-1000H Japanese manual of Feishu record `reczz28SfbsHcGfU` (子物料编码 16-0102-000431, 项目号 HTE159, SKU 21-0001-000451).

**Status: `operator-authorized-git-only-release`.** The operator reviewed the 1280/390 renders beside the JE-1000H/EU/en (published EU English Web) Web and the `source_manifest.json:source_concerns` list (PR #1653), then authorized release on 2026-11-03 (「上‘线提交发布：JE-1000C、JE-1000G、JE-1000H、JE-1500B」). `source/approval.json` binds every reviewed `source/` and `assets/` input; the IR is publication-eligible. The source copy goes live as printed; the listed source concerns go back to the source owner. Merge still needs explicit operator authorization (AGENTS.md §8.6). The read-manual and keep-dry symbol rows stay withheld until the shared symbol dedupe PR binds them to the operator-chosen canonicals (`pending_symbols`).

## Source authority

- 「【Jackery ポータブル電源 1000 Plus】说明书-JP.pdf」, stored byte-exact as `JE-1000H-JP-JA.pdf`, SHA-256 `717c813db4c64d57f90072da6f40081162131979cc181a440c589e70d9947da4`, 3,054,920 bytes. Cover: Jackery ポータブル電源 1000 Plus, 型番：JE-1000H, V2, 取扱説明書, 国内専用/For use only in Japan.
- 28 pages, 130 × 185 mm, with a text layer. `source/transcription.json` is the line-by-line transcription taken from that layer and checked against renders (method in the file). Wording, punctuation and width are kept as printed; `source_manifest.json:source_concerns` lists suspected source errors for the source owner.
- The print master 「16-0102-000431 说明书 HTE1591000A-JP-JAK  RoHS REACH-s.pdf」 (SHA-256 `3af3339ba2bcc80e139d9c44f6141d2fcd2380d5a99e3846bb3193598e065c94`, 11,341,108 bytes) is recorded as reference only, not committed and not extracted.
- Model facts (1024Wh, 1800W, UPS 10 ms, 400W solar, five battery packs, temperatures, warranty) come only from this PDF. JE-1000D JP V2 supplies the package flow, JE-2000E JP the component choices of the shared Plus page set, JE-1000H EU en 2.0 the LCD icon files.

## Layout

The Web body is printed pages 01–25 (physical 3–27); cover, paper TOC and back cover stay in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); the two plain tables (Li-ion 32 recycling notice, 省エネモード) are declared in `shared_component_exceptions`. `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry and type size only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. 27 LCD icons and the POWER / DC/USB buttons are reused byte-identically; 10 safety symbols reuse admitted shared variants (fixed 2% admission); the Li-ion 32 notice uses the operator-chosen canonical shared icon `native/je3000c-kr-78316033-06` in a declared plain table. Product, operation, charging and App art are complete source panels at 3×; the AC1 button keeps its PDF vector paths and the LIGHT button is its source circle on a transparent ground.

## Rebuild

From the repository root (`requirements.lock`, Pandoc 3.9.0.2):

```sh
PKG=manual_sources/JE-1000H/JP/ja/git-20261103-717c813d
python "$PKG/derive_assets.py"        # artwork + symbol admission rows
python "$PKG/build_content.py"        # transcription -> source/ja/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/je1000h-jp
python -m sphinx -n -W --keep-going -b html tmp/je1000h-jp tmp/je1000h-jp-html
python -m unittest tests.test_je1000h_jp_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, and enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/ja` after any source change.

Not touched: live Base, queue, source tables, HTML_link, asset registry, shared symbol catalog, workflows and dependencies.
