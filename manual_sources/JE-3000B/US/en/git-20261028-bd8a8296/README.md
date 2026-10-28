# JE-3000B / US / en — Git-only Web manual (candidate)

Operator instruction, 2026-10-28: 「继续转 剩下的美规说明书 为单语 网页版 仅选等于Y的 待转」. This package is the Jackery Explorer 3000 (JE-3000B) US English manual from the 发布文档管理 Base: record `reczz28SlRGJim2Y`, 子物料编码 16-0102-000056, 项目号 HTE116, SKU 21-0001-000343 (the Base 客户型号 carries a trailing space, 「JE-3000B 」; `JE-3000B` is used everywhere here). Route `JE-3000B/US/en/md`.

**Status: `candidate-pending-operator-review`.** The IR is not publication-eligible and there is no `source/approval.json`. Release needs the operator's review of source parity, the 1280/390 renders and `source_manifest.json:source_concerns`; registration in `data/frozen_package_registry.json` follows approval.

## Source authority

- 「【Jackery Explorer 3000】说明书-EN.pdf」 (read-only download), stored byte-exact as `JE-3000B-US-EN.pdf`, 4,152,802 bytes, SHA-256 `bd8a82962865ae64cd52e9c6ebf9a20d8495652773ba09806d1911cb0f360294`. No version string is printed. The print master 「16-0102-000056 说明书 HTE1163000A-US CA-JAK  RoHS REACH-Q.pdf」 (SHA-256 `53664d66…f93e5`, 51 MB) is an identity reference only and is not committed.
- 19 pages, 130 × 185 mm, every glyph outlined (no text layer). `source/transcription.json` is the line-by-line transcription, drafted with Tesseract and checked word by word on 300 dpi renders with 6× clips. Wording, spelling, spacing and punctuation are kept as printed; `source_manifest.json:source_concerns` lists suspected source errors for the source owner.
- Model facts come only from this PDF. JE-1500D US/en is the structural and review reference edition; same-generation US/en packages supply the reused LCD glyphs.

## Layout

The Web body is physical pages 2 and 4–18 (preface and printed 01–15); cover, paper TOC and back cover stay in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); the three-column troubleshooting table is the one declared plain table (`shared_component_exceptions`). `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. All 21 LCD glyphs are reused byte-identically from approved same-generation US/en packages and the FCC mark from the shared catalog, each after the fixed 2% comparison against this PDF's native paths (`source_manifest.json:artwork_reuse_comparison`). The vertical POWER, DC/USB and AC buttons match no shared or package variant within 2% and keep this PDF's native vector paths. Overview, LCD map, operation, charging and App art are complete source panels at 3×; grey pills and bubbles printed inside them are removed by deleting their vector objects and set as native text. No safety-symbol table is printed: symbol admission covers zero rows and nothing is added to the shared catalog.

## Rebuild

From the repository root (`requirements.lock`, Pandoc 3.9.0.2):

```sh
PKG=manual_sources/JE-3000B/US/en/git-20261028-bd8a8296
python -I "$PKG/derive_assets.py"        # artwork + reuse comparison rows
python -I "$PKG/build_content.py"        # transcription -> source/en/content.json
python -I "$PKG/refresh_manifest.py"     # input inventory
python -I "$PKG/rebuild.py" --output tmp/je3000b-us
python -m sphinx -n -W --keep-going -b html tmp/je3000b-us tmp/je3000b-us-html
python -m unittest tests.test_je3000b_us_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, and enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/en` after any source change. `refresh_manifest.py frozen` runs only after approval.

Not touched: live Base, queue, source tables, HTML_link, asset registry, shared catalogs, workflows and dependencies.
