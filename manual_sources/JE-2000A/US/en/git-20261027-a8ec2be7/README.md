# JE-2000A / US / en — Git-only Web manual

Operator instruction, 2026-10-27: 「把这个表中 未转网页版的说明书 走git only进行单语网页文档的转换」. This package is the Jackery Explorer 2000 Pro (JE-2000A) US English manual from that table: Feishu record `reczz28SPLqH8cvK`, 物料号「文本」38-0001-000200, 项目号 HTE078, SKU 21-0001-000099. Route `JE-2000A/US/en/md`.

**Status: `operator-authorized-git-only-release`.** The operator authorized release on 2026-10-28 (「上线提交发布：JE-1000D、JE-1500B、JE-1500D、JE-2000A；授权合入 #1629 及其 Hello-Docs 发布 PR」) and checks each page's layout after it goes live. `source/approval.json` binds every reviewed `source/` and `assets/` input; the IR is publication-eligible. The source copy goes live as printed; `source_manifest.json:source_concerns` goes back to the source owner.

## Source authority

- 「【Jackery Explorer 2000 Pro】说明书-EN.pdf」 (read-only download), stored byte-exact as `JE-2000A-US-EN.pdf`, SHA-256 `a8ec2be735be6483d340f2f35c7bc13a9300bf7d9499f60099ed8d5ef5cf689f`, printed `Version: JAK-UM-V1.0`. The original artwork 「38-0001-000200 说明书 HTE0782000A-US-JAK 说明书 ROHS REACH.pdf」 (SHA-256 `2a7450bb…6486a8`, 41 MB) is reference only and is not committed.
- 19 pages, 130 × 185 mm. Every glyph is outlined (no text layer). `source/transcription.json` is the line-by-line transcription, drafted with tesseract and checked word by word on 300 dpi renders with 6× clips for punctuation and suspected typos. Wording, spelling and punctuation are kept as printed; `source_manifest.json:source_concerns` lists suspected source errors for the source owner.
- Model facts (ratings, ports, temperatures, warranty) come only from this PDF. JE-1000D JP V2 supplies the package structure and code idiom.

## Layout

The Web body is printed pages 01–17 (physical 2–18); cover and back cover stay in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); the LCD legend, the Low Power Mode table and the troubleshooting table are declared plain tables in `shared_component_exceptions`. `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry and type size only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. Product, LCD map, operations and charging/connection art are complete source panels at 3×, keeping frames, leader lines, captions, X marks and insets. LCD legend, inline LCD and troubleshooting glyphs are 8× transparent renders of the native PDF glyph paths. No safety-symbol table is printed, so symbol admission covers zero rows; `derive_assets.py` still supports staged symbol variants (`--proposed-dir`, `--write-shared` after operator approval).

## Rebuild

From the repository root (`requirements.lock`, Pandoc 3.9.0.2):

```sh
PKG=manual_sources/JE-2000A/US/en/git-20261027-a8ec2be7
python -I "$PKG/derive_assets.py"        # artwork + symbol admission rows
python -I "$PKG/build_content.py"        # transcription -> source/en/content.json
python -I "$PKG/refresh_manifest.py"     # input inventory
python -I "$PKG/rebuild.py" --output tmp/je2000a-us
python -m sphinx -n -W --keep-going -b html tmp/je2000a-us tmp/je2000a-us-html
python -m unittest tests.test_je2000a_us_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/en` after any source change.

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows and dependencies.
