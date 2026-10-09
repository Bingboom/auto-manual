# JBP-1000B-WH / JP / ja — Web-layout edition

Operator instructions, 2026-10-09: “全部修，一次做完”, “封面和目录 不用体现在web版面上”, “你参考 资料库里 现有的je-1000f的日语网页说明书”.
This edition fixes the Web layout of the [approved native package](../git-20261008-3aa6c003-native/README.md) (MA-275) against the same PDF.
The native package, its PDF and its release evidence remain immutable.

**Status: `operator-approved-git-only-release`.** After reviewing candidate `4352254` and its page-by-page comparisons the operator instructed “上线提交发布” and chose “B，你先开PR，我来审核合入”: the engineering PR is merged by operator review (AGENTS.md §8.6), not by an agent grant. `source/approval.json` binds every reviewed `source/` input hash; the rebuilt IR is publication-eligible.

## What changed

The full table, with the PDF page and reason for each change, is the 2026-10-09 section of `source/differences.md`. In short:

- **Cover and TOC:** the printed cover and the print TOC are not part of the Web edition. The page starts at 使用上のご注意.
- **Chapters:**
  - The navigation has exactly the 12 chapters of the print TOC.
  - The pictogram bands, the wood/concrete wall installation steps and the specification groups are sub-sections.
  - The contact lines close the warranty without a heading of their own, following the reviewed JE-1000F JP Web manual.
- **Installation steps:** steps the PDF prints side by side are one row figure each: wood 3–4 and concrete 4–5, 6–7, 8–9. This keeps the drill art that crosses two panels intact.
  - Live step text uses the print type size relative to each panel.
  - The `* 455 mm` notes are separate lines.
- **Rich-text structure in shared components:**
  - bold leads and sub-headings, and print line breaks;
  - circled LCD numbers and merged identical LCD descriptions;
  - the on/off clock and “3s” placed on the drawing;
  - the inline LCD icon at text size;
  - warranty notes as grey capsules.
- **Copy:** no Japanese wording is edited, and every `*_text` field keeps its approved value. `tests/test_jbp1000b_wh_jp_web_layout.py` proves the visible text equals the approved text, minus only:
  - the cover;
  - the お問い合わせ heading;
  - four decorative ⚠ glyphs;
  - the two duplicated LCD descriptions now shown once.

## Reconstruction

`derive_web_layout.py` derives every `source/` input from the native package except the hand-written `source/approval.json`. It is the maintenance entrypoint for this edition. Changing a reviewed input invalidates the acceptance: `rebuild.py` then refuses until a new operator acceptance is recorded. It:
- copies unchanged inputs byte-for-byte;
- regenerates `figures.json`, `asset_recipe.json`, `document.json`, `admission.json` and the generated tail of `presentation.css`;
- renders the art with the shared asset pipeline;
- refreshes `source_manifest.json`.

Hand-written files are not overwritten: `README.md`, `source/differences.md`, and the authored part of `source/presentation.css`.

Run from the repository root with `requirements.lock`:

- The asset recipe requires PyMuPDF 1.28.0 / MuPDF 1.29.0.
- A second run must leave the tree unchanged.

```sh
PKG=manual_sources/JBP-1000B-WH/JP/ja/git-20261009-3aa6c003-web-layout
python "$PKG/derive_web_layout.py"
python "$PKG/rebuild.py" --output tmp/jbp1000b-jp-layout
python -m sphinx -n -W --keep-going -b html tmp/jbp1000b-jp-layout tmp/jbp1000b-jp-layout-html
```

Replace `web/ja` with a fresh rebuild after any source change. `rebuild.py` is unchanged from the native package. It checks every input hash, the shared component admission and the base-art label contracts before writing output.

## Validation and release boundary

```sh
python -m unittest tests.test_jbp1000b_wh_jp_web_layout tests.test_jbp1000b_wh_jp_native_web
```

`evidence/validation.json` lists every command run for the accepted edition. The same folder holds:
- the logs;
- desktop and mobile browser acceptance with screenshots;
- byte copies of the Web audit reports.

The release-side `frozen_source_manifest.json` inventories every file of this package except itself and the two Web audit sidecars:
- The sidecars are listed under `release_excluded_files`; byte copies are kept as `evidence/web-*`.
- The inventory is regenerated whenever a file of this package changes.

After the operator merges the engineering PR, the Git-only transaction continues per [web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline.md#22-git-only-transaction):
1. Seal `seal_frozen_web_evidence` at the actual merged `main` commit.
2. Assemble from current Hello-Docs `main`.
3. Open a `docs/publish/**`-only publish PR.
4. Verify the RTD routes, aliases, resources and desktop/mobile pages.

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows and dependencies. All recipe art stays `quarantine` / `build_eligible=false`.
