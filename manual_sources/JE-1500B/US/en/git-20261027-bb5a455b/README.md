# JE-1500B / US / en — Git-only Web manual (Explorer 1500 Pro)

Operator instruction, 2026-10-27: 「把这个表中 未转网页版的说明书 走git only进行单语网页文档的转换」, with the decision 「JE-1500B 用 38-0001-000307，000208 不出网页」. This package is the JE-1500B US English manual of Feishu record `reczz28SPLqH7mCa` (物料号文本 38-0001-000307, 项目号 HTE080, SKU 21-0001-000130).

**Status: `operator-authorized-git-only-release`.** The operator authorized release on 2026-10-28 (「上线提交发布：JE-1000D、JE-1500B、JE-1500D、JE-2000A；授权合入 #1629 及其 Hello-Docs 发布 PR」) and checks each page's layout after it goes live. `source/approval.json` binds every reviewed `source/` and `assets/` input; the IR is publication-eligible. The source copy goes live as printed; `source_manifest.json:source_concerns` goes back to the source owner.

## Source authority

- 「【Jackery Explorer 1500 Pro】说明书-EN.pdf」, stored byte-exact as `JE-1500B-US-EN.pdf`, SHA-256 `bb5a455b5c3e03b70ee95d6d6ceb74a9c98b671addc1d30d9637f9bb974a7dbb`, 3,868,124 bytes. Cover: Model: JE-1500B, USER MANUAL, Jackery Explorer 1500 Pro, printed version "Version: JAK-UM-V1.0".
- 11 pages, 130 × 185 mm. Every glyph is outlined (no text layer). `source/transcription.json` is the line-by-line transcription (tesseract draft, each line checked on 300 dpi renders and high-zoom clips). Wording, spelling, punctuation and spacing are kept as printed; `source_manifest.json:source_concerns` lists suspected source errors for the source owner.
- The original artwork 「38-0001-000307 说明书  HTE0801500B-US-JAK 说明书  ROHS REACH Q.pdf」 (SHA-256 `5437c53265ec585e98623df371c7f733c050d3117cc87d53d9bc886e8bc47c9a`) is recorded as reference only and not committed.
- Model facts (ratings, ports, inputs, temperatures, warranty) come only from this PDF. JE-1000D JP V2 supplies the package structure and three reused LCD icon files.

## Layout

The Web body is printed pages 01–09 (physical 2–10); cover and back cover stay in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); the one plain table (Low Power Mode) is declared in `shared_component_exceptions`. `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. Product, LCD, charging, certification and package-list art are complete source crops at 3×, keeping frames, leader lines and captions. Three LCD icons are reused byte-identically from JE-1000D JP V2; three are the original PDF vector paths (transparent). No symbol table is printed, so the symbol admission locale is empty.

## Rebuild

From the repository root (`requirements.lock`, Pandoc 3.9.0.2):

```sh
PKG=manual_sources/JE-1500B/US/en/git-20261027-bb5a455b
python "$PKG/derive_assets.py"        # artwork + (empty) symbol admission rows
python "$PKG/build_content.py"        # transcription -> source/en/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/je1500b-us
python -m sphinx -n -W --keep-going -b html tmp/je1500b-us tmp/je1500b-us-html
python -m unittest tests.test_je1500b_us_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, and enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/en` after any source change.

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows and dependencies.
