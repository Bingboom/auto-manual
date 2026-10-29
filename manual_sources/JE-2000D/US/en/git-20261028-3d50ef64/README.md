# JE-2000D / US / en — Git-only Web manual candidate (V2)

Operator instruction, 2026-10-28: 「继续转 剩下的美规说明书 为单语 网页版 仅选等于Y的 待转」. This package is the Jackery Explorer 2000 (JE-2000D) US English manual of 发布文档管理 record `reczz28SlRGJhr8p` (子物料编码 16-0102-000055, 项目号 HTE117, six SKUs in `source_manifest.json:base_record`). Route `JE-2000D/US/en/md`; there is no earlier Web edition of this model, so it is the legacy default.

**Status: `candidate-pending-operator-review`.** No `source/approval.json` exists, so the IR is not publication-eligible. Approval is written only after the operator reviews the 1280/390 renders beside the reference edition (JE-1000D US en, the published Explorer 1000 v2 Web of the same V2 manual family) and the source concern list.

## Source authority

- 「【Jackery Explorer 2000】说明书-EN.pdf」, stored byte-exact as `JE-2000D-US-EN.pdf`, SHA-256 `3d50ef6490217a0893119567ef0d276f40b23d45e52e51560e97f724b6ca8c77`, 14 pages, 130 × 185 mm. Cover: Jackery, V2, USER MANUAL, Jackery Explorer 2000, Model: JE-2000D.
- The print master 「16-0102-000055 HTE1172000A-US-JAK 说明书 RoSH REACH-Q.pdf」 (SHA-256 `a06040ef…6dd96b2`, 48 pages, 34 MB) is identity reference only: not committed and not read by any script.
- Every glyph is outlined (no text layer). `source/transcription.json` is the line-by-line transcription, drafted with tesseract and checked word by word and number by number on 300 dpi renders with 5–8× clips (`source_manifest.json:transcription_cross_check`). Wording, spelling and punctuation are kept as printed; suspected source errors are listed in `source_manifest.json:source_concerns` for the source owner.
- Model facts (ratings, ports, UPS, Bypass Mode, DC input, temperatures, warranty) come only from this PDF. The JE-1000D US edition supplies structure, component idiom and byte-identical artwork only where the printed art is the same.

## Layout

The Web body is printed pages 01–11 (physical 3–13); cover, CONTENTS and back cover stay in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); the one plain table (Energy Saving Mode, spanning Defaults cell) is declared in `shared_component_exceptions`. `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. The LCD map, App Store/Google Play badges, App phone frames and App button map are the JE-1000D US files (same art; render comparison ≤ 0.0016). Overview, in-box, LED and charging art are new complete panels at 3×. The eight LCD icons, the FCC/WEEE catalog marks and the BC mark are reused byte-identical, each within the fixed 2% of the native paths; the p08 FCC mark is native paths (the catalog variant measures 0.0222). Every comparison is in `source_manifest.json:artwork_reuse_comparison`. The manual prints no symbol table, so symbol admission has no rows.

## Rebuild

From the repository root (`requirements.lock`, Pandoc 3.9.0.2):

```sh
PKG=manual_sources/JE-2000D/US/en/git-20261028-3d50ef64
python "$PKG/derive_assets.py"        # artwork + reuse comparison
python "$PKG/build_content.py"        # transcription -> source/en/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/je2000d-us
python -m sphinx -n -W --keep-going -b html tmp/je2000d-us tmp/je2000d-us-html
python -m unittest tests.test_je2000d_us_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, and enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/en` after any source change.

Not touched: live Base, queue, source tables, HTML_link, asset registry, frozen package registry, workflows and dependencies.
