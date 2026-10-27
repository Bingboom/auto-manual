# JE-1000D / JP / ja — Git-only Web manual candidate (V2)

Operator instruction, 2026-10-26: 「分几个窗口把这个目录下面的文档都转成网页文档 https://xcn57j1urbe6.feishu.cn/wiki/Uf4zwUhMYieibhkyrO1cGuCsnye」, then 「韩语文档除外」. This package is the JE-1000D Japanese manual from that folder.

**Status: `operator-authorized-git-only-release`.** The operator reviewed the 1280/390 renders and the source correction list (PR #1612) and instructed 「先提交 再来列纠正清单」, then 「上线提交发布」 on 2026-10-27: the source copy goes live as printed and the listed source errors go back to the source owner. `source/approval.json` binds every reviewed `source/` and `assets/` input; the IR is publication-eligible. The engineering PR is merged by the operator (AGENTS.md §8.6); Hello-Docs/RTD publication follows [web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline/input-paths.md#22-git-only-transaction).

## Source authority

- 「Jackery ポータブル電源 1000说明书.pdf」 from the Feishu wiki (read-only), stored byte-exact as `JE-1000D-JP-V2.pdf`, SHA-256 `00c43a89bd07babbea3a82b6bfbbc4a1c7b52f7a72cb8030b0dbfb349de601a4`. Cover: Jackery ポータブル電源 1000, JE-1000D, V2, 取扱説明書, 国内専用/For use only in Japan.
- 18 pages, 130 × 185 mm. Every glyph is outlined (no text layer). `source/transcription.json` is the line-by-line transcription, checked on 300 dpi renders with 500 dpi clips for ambiguous glyphs. Wording, punctuation and model spellings are kept as printed; `source_manifest.json:source_concerns` lists suspected source errors for the source owner.
- Model facts (ratings, ports, UPS 20ms, emergency charge mode, energy-saving defaults, temperatures) come only from this PDF. JE-1500D JP V2 and JE-1000F JP supply structure and shared components.

## Layout

The Web body is printed pages 01–15 (physical 3–17); cover, paper TOC and back cover stay in the PDF. Every printed block maps to a shared component (`source_manifest.json:component_map`); the two plain tables are declared in `shared_component_exceptions`. `source/differences.md` lists each deliberate layout difference; `source/geometry.css` is geometry and type size only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every reuse/extract decision. Product, LCD, charging and App art are complete source panels at 3×, keeping leader lines, captions and phone frames. Small LCD icons and the Li-ion mark are the original PDF vector paths (transparent). Three files are reused byte-identically. Safety symbols pass the fixed 2% symbol admission; one reuses `mandatory/h1-jp-native`, five are new append-only shared variants `native/je1000d-jp-00c43a89-0N`.

## Rebuild

From the repository root (`requirements.lock`, Pandoc 3.9.0.2):

```sh
PKG=manual_sources/JE-1000D/JP/ja/git-20261026-00c43a89-v2
python "$PKG/derive_assets.py"        # artwork + symbol admission rows
python "$PKG/build_content.py"        # transcription -> source/ja/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/je1000d-jp
python -m sphinx -n -W --keep-going -b html tmp/je1000d-jp tmp/je1000d-jp-html
python -m unittest tests.test_je1000d_jp_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared Web/MyST pipeline, enforces the prepared-document shared-style gate and symbol admission. Copy a fresh render to `web/ja` after any source change. The JE-1000F JP `build.py check` is a repository regression gate only.

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows and dependencies.
