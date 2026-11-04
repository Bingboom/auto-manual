# JE-3000A / JP / ja — Git-only Web manual

Jackery ポータブル電源 3000 Pro (JE-3000A, project HTE097), Japanese single-language manual.

**Status: `operator-authorized-git-only-release`.** The operator reviewed the 1280/390 renders beside the shared reference edition (manual_sources/JE-2000A/US/en/git-20261027-a8ec2be7) in PR #1662 and instructed 「上线提交发布：JE-3000A」 on 2026-11-04 in this package's engineering session. `source/approval.json` binds every reviewed `source/`, `assets/` and script input; the IR is publication-eligible. Source copy goes live as printed; `source_manifest.json:source_concerns` go back to the source owner. Merge needs a separate operator grant (AGENTS.md §8.6).

## Source authority

- Feishu record `reczz28SfbsHdQ1I` (子物料编码 38-0001-000153, sku 21-0001-000049): the single-language PDF 「【Jackery ポータブル電源 3000 Pro】说明书-JP.pdf」, stored byte-exact as `JE-3000A-JP-JA.pdf`, SHA-256 `002fde5a36f8dfc4192a8534e8f43a98e249bfbc491027b7c1b0c819d75e2002`. The print master `.ai` is recorded in `source_manifest.json:feishu_source` only.
- 14 pages, 129.5 × 184.5 mm. Every glyph is outlined (no text layer). `source/transcription.json` is the line-by-line transcription from 300 dpi renders with 400–500 dpi clips for ambiguous glyphs. Wording, punctuation and model spellings are kept as printed; `source_manifest.json:source_concerns` lists suspected source errors for the source owner.
- Model facts (ratings, ports, EPS 20ms, low-temperature mode, SolarSaga wiring) come only from this PDF. JE-1000D JP V2 supplies JP structure and component idiom; JE-2000A / JE-1500B US (same Pro generation) were the artwork inventory.

## Layout

The Web body is printed pages 1–12 (physical 2–13) followed by the back-cover App notice (physical 14); the cover stays in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); the two plain tables are declared in `shared_component_exceptions`. `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry and type size only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. Product, LCD-map, charging and in-box art are complete source panels at 3×. Six LCD icons are existing repository SVGs reused byte-identically after the fixed 2% comparison; the Li-ion 20 mark is the original PDF vector paths (shared `native_symbol_svg` selector). All six safety symbols reuse shared-catalog variants and pass the standard symbol asset admission within the fixed 2% tolerance; 製品に濡れた手で触れることを禁止する記号 binds `native/je1000d-jp-00c43a89-03`, the canonical of the operator-confirmed no-wet-hands group, per the operator decision. Nothing was added to the shared library.

## Rebuild

From the repository root (`requirements.lock`, Pandoc):

```sh
PKG=manual_sources/JE-3000A/JP/ja/git-20261103-002fde5a
python "$PKG/derive_assets.py"        # artwork, reuse checks, symbol admission rows
python "$PKG/build_content.py"        # transcription -> source/ja/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/je3000a-jp
python -m sphinx -n -W --keep-going -b html tmp/je3000a-jp tmp/je3000a-jp-html
python -m unittest tests.test_je3000a_jp_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, enforces the prepared-document shared-style gate, and runs the standard symbol asset admission. Copy a fresh render to `web/ja` after any source change.

Not touched: live Base, queue, source tables, HTML_link, asset registry, shared symbol library, frozen package registry, workflows and dependencies.
