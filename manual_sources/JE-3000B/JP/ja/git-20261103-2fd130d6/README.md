# JE-3000B / JP / ja — Git-only Web manual (V2)

Coordinator brief, 2026-11-03: build the Japanese single-language Web candidate for the 发布文档管理 Base record `reczz28SfbsHfOgb` (Jackery ポータブル電源 3000, 子物料编码 38-0001-000822, 项目号 HTE116, SKU 21-0001-000294; the Base 客户型号 carries a trailing space, 「JE-3000B 」; `JE-3000B` is used everywhere here). Route `JE-3000B/JP/ja/md`.

**Status: `operator-authorized-git-only-release`.** The operator reviewed the 1280/390 renders beside the shared reference edition (manual_sources/JE-3000B/US/en/git-20261028-bd8a8296) in PR #1655 and instructed 「上线提交发布」 on 2026-11-03 in this package's engineering session. `source/approval.json` binds every reviewed `source/`, `assets/` and script input; the IR is publication-eligible. Source copy goes live as printed; `source_manifest.json:source_concerns` go back to the source owner. Merge needs a separate operator grant (AGENTS.md §8.6).

## Source authority

- 「【Jackery ポータブル電源 3000】说明书-JP.pdf」 (read-only download), stored byte-exact as `JE-3000B-JP-JA.pdf`, 4,428,230 bytes, SHA-256 `2fd130d6cde89728d43492a90f4616a31c2066d65f13ccdc99fcd702ef11374c`. Cover: Jackery ポータブル電源 / JE-3000B / V2 / 取扱説明書 / 国内専用. The print master 「38-0001-000822 HTE1163000A-JP-JAK  说明书 RoHS REACH-q.pdf」 is recorded only and not committed.
- 12 single pages, 130 × 185 mm, every glyph outlined except one paragraph on physical page 6. `source/transcription.json` is the line-by-line transcription, checked on 300 dpi renders with 500–600 dpi clips for ambiguous glyphs. Wording, punctuation and model spellings are kept as printed.
- Model facts (ratings, ports, 5ポート合計3000W, UPS 20ms, self-powered and pass-through limits, temperatures) come only from this PDF. JE-1000D JP V2 (same print template) and JE-3000B US/en supply structure, shared components and reusable glyphs.

## Layout

The Web body is printed pages 1–11 (physical 2–12); the cover stays in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); the two plain tables (recycling box, 省エネモード port table) are declared in `shared_component_exceptions`. `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry and type size only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. Panels are complete 3× source renders keeping leader lines, captions and phone frames. Eight LCD glyphs are reused byte-identically (seven from JE-3000B US/en, one from JE-1500D US/en) after the fixed 2% comparison (`source_manifest.json:artwork_reuse_comparison`); the 88H, charging-plan and Li-ion 32 marks keep this PDF's native vector paths. The six safety symbols pass the fixed 2% admission against existing shared variants; nothing is added to the shared catalog.

## Rebuild

From the repository root (`requirements.lock`, Pandoc 3.9.0.2):

```sh
PKG=manual_sources/JE-3000B/JP/ja/git-20261103-2fd130d6
python -I "$PKG/derive_assets.py"        # artwork + reuse comparison + symbol admission rows
python -I "$PKG/build_content.py"        # transcription -> source/ja/content.json
python -I "$PKG/refresh_manifest.py"     # input inventory
python -I "$PKG/rebuild.py" --output tmp/je3000b-jp
python -m sphinx -n -W --keep-going -b html tmp/je3000b-jp tmp/je3000b-jp-html
python -m unittest tests.test_je3000b_jp_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, and enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/ja` after any source change. `refresh_manifest.py frozen` runs only after approval.

Not touched: live Base, queue, source tables, HTML_link, asset registry, shared catalogs, frozen package registry, workflows and dependencies.
