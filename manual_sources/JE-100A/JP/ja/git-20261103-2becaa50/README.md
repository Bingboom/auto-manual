# JE-100A / JP / ja — Git-only Web manual candidate

Operator instruction, 2026-11-03: 「继续 转日语说明书」 (发布文档管理, 日规视图 vew0f8smjz), relayed by the coordination window: the Japanese single-language manuals with a customer model and a PDF that are not yet on the Web. This package is the Jackery Explorer 100 Plus (JE-100A) Japanese manual from that table.

**Status: `operator-authorized-git-only-release`.** The operator reviewed the 1280/390 renders beside the JE-100A US/en Web (published, same model) and the `source_manifest.json:source_concerns` list (PR #1652), then authorized release on 2026-11-04 (「上线提交发布：JE-100A、JE-100C、JE-240A、JE-76A」). `source/approval.json` binds every reviewed `source/` and `assets/` input; the IR is publication-eligible. The source copy goes live as printed; the listed source concerns go back to the source owner. Merge still needs explicit operator authorization (AGENTS.md §8.6). Hello-Docs/RTD publication follows [web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline/input-paths.md#22-git-only-transaction).

## Source authority

- 发布文档管理 record `reczz28SfbsHdgHw`: 子物料编码 38-0001-000541, 项目号 HTE106, SKU 21-0001-000167. Field 单语言说明书 「【Jackery Explorer 100 Plus】说明书-JP.pdf」, stored byte-exact as `JE-100A-JP-JA.pdf`, SHA-256 `2becaa507bbfd8d051888ac85d96a5399f0959224e9e6acb85211599baa06262`; printed version JAK-UM-V1. The 说明书文件 print master is recorded in `source_manifest.json:design_original` (name, SHA-256) and not committed.
- 12 pages, 89.4 × 129.4 mm. Every glyph is outlined (no text layer). `source/transcription.json` is the line-by-line transcription from 330 dpi renders, re-checked on 500–600 dpi clips. Wording, punctuation and spelling are kept as printed; `source_manifest.json:source_concerns` lists suspected source errors for the source owner.
- Model facts come only from this PDF. JE-1000D JP V2 supplies the JP structure and shared components; the same-model US/en package is the review reference and supplies reused textless art.

## Layout

The Web body is printed pages 1–11 (physical 2–12); the cover stays in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); the one plain table (recycling notice) is declared in `shared_component_exceptions`. `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. Panels with Japanese labels are new complete panels at 3×. The cable card art (US/en), the low-battery and temperature icons (JE-1000D JP) and the F8 icon (shared-lcd) are reused byte-identically; the battery ring, always-on, 12H and Li-ion 32 marks are original PDF vector paths (transparent). All six 絵表示の説明 symbols pass the fixed 2% admission against existing shared symbols; no new shared variant is needed.

## Rebuild

From the repository root (`requirements.lock`, Pandoc 3.9.0.2):

```sh
PKG=manual_sources/JE-100A/JP/ja/git-20261103-2becaa50
python "$PKG/derive_assets.py"        # artwork + symbol admission rows
python "$PKG/build_content.py"        # transcription -> source/ja/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/je100a-jp
python -m sphinx -n -W --keep-going -b html tmp/je100a-jp tmp/je100a-jp-html
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/ja` after any source change, then run `refresh_manifest.py frozen`. The JE-1000F JP `build.py check` is a repository regression gate only.

Not touched: live Base, queue, source tables, HTML_link, asset registry, shared symbol library, workflows and dependencies.
