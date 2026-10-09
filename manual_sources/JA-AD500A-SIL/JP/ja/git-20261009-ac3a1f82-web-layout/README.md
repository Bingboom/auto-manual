# JA-AD500A-SIL / JP / ja — Web-layout edition

Operator instruction, 2026-10-09: “开新窗口 把这个的版面也调整了”, applying the JBP-1000B-WH JP rules “全部修，一次做完”, “封面和目录 不用体现在web版面上” and “你参考 资料库里 现有的je-1000f的日语网页说明书”.
This edition fixes the Web layout of the [approved package](../git-20261008-ac3a1f82-reviewed/README.md) (MA-272) against the same PDF.
The approved package, its PDF and its release evidence remain immutable.

**Status: `review-candidate-no-release-authorization`.** The IR is not publication-eligible and there is no `source/approval.json` until the operator accepts the candidate.

## What changed

The full table, with the PDF page and reason for each change, is `source/differences.md`. In short:

- **Cover:** the printed cover identity lines are not part of the Web edition. The page opens with the welcome lead「お買い上げありがとうございます。」; the navigation is the five printed chapters.
- **Rich text and print lines:** bold leads and part names, print line breaks, hanging ※ notes, centred LED table, “・” bullets.
- **Panels:** the car-charging precautions, the whole warranty introduction and 免責事項 are grey panels; warranty notes and contact lines are grey capsules.
- **Artwork:** only `assets/inbox-manual.png` is re-cropped by the shared asset pipeline so the booklet's right frame is no longer cut; every other image is byte-identical to the approved package.
- **Copy:** no Japanese wording is edited. `tests/test_jaad500a_sil_jp_web_layout.py` proves the visible text, in order, equals the approved text minus only the cover lines listed in `derive_web_layout.py` (`COVER_LINES`).

## Reconstruction

`derive_web_layout.py` derives the PDF, page map, recipe, artwork and prepared RST pages from the approved package and refreshes `source_manifest.json`. A second run leaves the tree unchanged. Hand-written files are not overwritten: `README.md`, `render.py`, `source/differences.md`, `source/presentation.css` and (after acceptance) `source/approval.json`.

`render.py` checks every input hash, runs the existing prepared RST → manual-ir/v2 → shared Web/MyST pipeline, checks the shared component counts and carries `source/presentation.css` as the IR source stylesheet.

Run from the repository root with `requirements.lock` (PyMuPDF 1.28.0 / MuPDF 1.29.0):

```sh
PKG=manual_sources/JA-AD500A-SIL/JP/ja/git-20261009-ac3a1f82-web-layout
python "$PKG/derive_web_layout.py"
python "$PKG/render.py" tmp/jaad500a-jp-layout
python -m sphinx -n -W --keep-going -b html tmp/jaad500a-jp-layout tmp/jaad500a-jp-layout-html
```

Replace `web/ja` with a fresh render after any source change.

## Validation and release boundary

```sh
python -m unittest tests.test_jaad500a_sil_jp_web_layout
```

After the operator accepts the candidate (“上线提交发布”), `source/approval.json` binds every reviewed input, the status becomes `operator-approved-git-only-release`, `web/ja` is re-rendered and release evidence is recorded. The operator merges the engineering PR (AGENTS.md §8.6); the Git-only transaction then follows [web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline.md#22-git-only-transaction).

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows and dependencies.
