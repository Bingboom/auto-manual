# JE-3600A / CN — Web-layout edition (zh)

Operator instruction, 2026-10-13: 「再审阅校正一下 这俩文档的版面 文档对应 发布 PR #220」 for the JE-3600A CN and JP manuals that Bingboom/Hello-Docs#220 published. Standing instructions, as for JHP-3000D: 「全部修，一次做完」, 「封面和目录 不用体现在web版面上」, and reuse of the existing shared components.

This edition fixes the Web layout of the [reviewed edition](../git-20261012-caa5370a-reviewed/README.md) (MA-298) against the same PDF: `电小二户外电源 3600 Plus.pdf`, SHA-256 `caa5370acac00f053f8a62b02ea0cd60b5efe4fd5c7e7be56c65cc97493681bb`, 23 pages. The reviewed edition, its PDF and its release evidence remain immutable. The JP edition [`../../JP/git-20261013-fd06cd04-web-layout`](../../JP/git-20261013-fd06cd04-web-layout/README.md) is derived by the same script.

**Status: `operator-approved-git-only-release`.** The operator reviewed candidate `16368b7` on its chapter-by-chapter comparison page (print PDF beside the desktop and phone Web, CN and JP) and instructed 「上线发布」 on 2026-10-13.
- `source/approval.json` binds the hash of every package input except `web/` and itself.
- The rebuilt IR is publication-eligible.
- The engineering PR is merged by operator review (AGENTS.md §8.6), not by an agent grant.
- Any later input change invalidates the acceptance: `rebuild.py` then refuses until a new acceptance is recorded.

## What changed

The full table, with the PDF page and log action for each change, is `source/differences.md`. In short:

- **Navigation:** the 13 dark title bands of the print (it has no TOC page); the printed cover stays out, as in the reviewed edition.
- **LCD glossary (p5–7):** one table with circled numbers; eight glyphs from this print instead of another model's, plus the two temperature glyphs inside the ⑲ descriptions; every glyph at its print height.
- **Tables:** the p10 button table, the p18 troubleshooting table and the p19 specification grids take the print's grey key columns, alignment and row heights.
- **Print structure:** the p12 plain battery-pack title; the p15 first-use warning as a bold line behind the open warning triangle; the p20 App download block.
- **Rich text:** print bold runs (p2 lead lines, figure and operation labels); line breaks where the print breaks lines; no spaces at print line wraps; titles in their print case; V<sub>oc</sub> with its subscript.
- **Artwork:** the p20 button-panel art without the sliver its crop took from the 备注 box above.
- **Copy:** the visible text is the reviewed text minus one painted-over figure label (p13). The only other text edits are the logged restorations (`source/zh/web_layout.json`).

## Reconstruction

`derive_web_layout.py` regenerates, from the reviewed edition:
- `source/zh/content.json` and `web_layout.json`;
- `assets/` and `assets_manifest.json` (the reviewed pool and records, then the added assets and their records);
- byte copies of the PDF and the reviewed source records.

A second run leaves the tree unchanged. It needs PyMuPDF 1.28.0 / MuPDF 1.29.0 (`requirements.lock`).

Hand-written files are not overwritten: `README.md`, `rebuild.py`, `source/differences.md`, `source/presentation.css` (reviewed geometry plus the authored Web-layout section), `source/refresh_manifest.py` and `validation/`.

`rebuild.py` checks every inventoried input and the pinned shared repository inputs, then replays the language through the shared Manual IR APIs. `assets/` in `web/zh` holds only the files that `content.json` and the stylesheet reference.

Run from the repository root:

```sh
PKG=data/manual_sources/JE-3600A/CN/git-20261013-caa5370a-web-layout
python3 "$PKG/derive_web_layout.py"
python3 "$PKG/source/refresh_manifest.py"
PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/rebuild.py" --language zh --output tmp/je3600a-cn-layout
python3 -m sphinx -n -W --keep-going -b html tmp/je3600a-cn-layout tmp/je3600a-cn-layout-site
```

To re-freeze, rebuild into `web/zh` and run `source/refresh_manifest.py` again.

## Validation and release boundary

- **Unit tests:** `python3 -m unittest tests.test_je3600a_cn_jp_web_layout` covers both editions (see the JP README for the list).
- **Evidence:** `validation/layout-checks.json` records strict Sphinx, cold-replay byte parity and the browser gate at 1280×900, 768×1024 and 390×844 CSS pixels.

After the operator merges the engineering PR, the Git-only transaction continues per [web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline.md#22-git-only-transaction):
1. Seal `seal_frozen_web_evidence` at the merged `main` commit.
2. Assemble from current Hello-Docs `main`.
3. Open a `docs/publish/**`-only publish PR.
4. Verify the RTD routes, resources and desktop/mobile pages.

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows and dependencies. No phase2 or print target is enrolled.
