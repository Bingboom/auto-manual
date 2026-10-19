# JE-3600A / JP — Web-layout edition (ja)

Operator instruction, 2026-10-13: 「再审阅校正一下 这俩文档的版面 文档对应 发布 PR #220」 for the JE-3600A CN and JP manuals that Bingboom/Hello-Docs#220 published. Standing instructions, as for JHP-3000D: 「全部修，一次做完」, 「封面和目录 不用体现在web版面上」, and reuse of the existing shared components.

This edition fixes the Web layout of the [reviewed edition](../git-20261012-fd06cd04-reviewed/README.md) (MA-298) against the same PDF: `Jackery ポータブル電源 3600 Plus 取扱説明書.pdf`, SHA-256 `fd06cd04653d0c336dfa119ccfb29cbee79fecf4508feee9ccda61df5eeb8dd6`, 30 pages. The reviewed edition, its PDF and its release evidence remain immutable. The CN edition [`../../CN/git-20261013-caa5370a-web-layout`](../../CN/git-20261013-caa5370a-web-layout/README.md) is derived by the same script.

**Status: `operator-approved-git-only-release`.** The operator reviewed candidate `16368b7` on its chapter-by-chapter comparison page (print PDF beside the desktop and phone Web, CN and JP) and instructed 「上线发布」 on 2026-10-13.
- `source/approval.json` binds the hash of every package input except `web/` and itself.
- The rebuilt IR is publication-eligible.
- The engineering PR is merged by operator review (AGENTS.md §8.6), not by an agent grant.
- Any later input change invalidates the acceptance: `rebuild.py` then refuses until a new acceptance is recorded.

## What changed

The full table, with the PDF page and log action for each change, is `source/differences.md`. In short:

- **Cover and TOC:** not part of the Web edition. Navigation has exactly the 14 chapters of the print TOC.
- **Print structure:** the p3 white-on-dark bands and signal label column; the p4–5 警告 / 注意 lockups at print size; the p5 three-column symptom grid; the p6 outlined ご注意 panel; the p8 outlined notes panel; grey panels on p16 and p21; bullets and nested lists where the print has them.
- **LCD glossary (p10–11):** one table with circled numbers; eight glyphs from this print instead of another model's; every glyph at its print height.
- **Tables:** the p15 display-mode and button tables, the p24 troubleshooting table and the p25 specification grids take the print's grey key columns, alignment and row heights.
- **Rich text:** the p14 12H glyph in its text lines; line breaks where the print breaks lines; no spaces at print line wraps; print bold runs; titles in their print case.
- **Artwork:** the p14 energy art without its two in-text glyphs, and the p28 phone art without the line its crop took from the 備考 box below.
- **Copy:** the visible text is the reviewed text minus the printed cover and one painted-over figure label (p18). The only other text edits are the logged restorations (`source/ja/web_layout.json`).

## Reconstruction

`derive_web_layout.py` regenerates, from the reviewed edition:
- `source/ja/content.json` and `web_layout.json`;
- `assets/` and `assets_manifest.json` (the reviewed pool and records, then the added assets and their records);
- byte copies of the PDF and the reviewed source records.

A second run leaves the tree unchanged. It needs PyMuPDF 1.28.0 / MuPDF 1.29.0 (`requirements.lock`).

Hand-written files are not overwritten: `README.md`, `rebuild.py`, `source/differences.md`, `source/presentation.css` (reviewed geometry plus the authored Web-layout section), `source/refresh_manifest.py` and `validation/`.

`rebuild.py` checks every inventoried input and the pinned shared repository inputs, then replays the language through the shared Manual IR APIs. `assets/` in `web/ja` holds only the files that `content.json` and the stylesheet reference.

Run from the repository root:

```sh
PKG=data/manual_sources/JE-3600A/JP/git-20261013-fd06cd04-web-layout
python3 "$PKG/derive_web_layout.py"
python3 "$PKG/source/refresh_manifest.py"
PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/rebuild.py" --language ja --output tmp/je3600a-jp-layout
python3 -m sphinx -n -W --keep-going -b html tmp/je3600a-jp-layout tmp/je3600a-jp-layout-site
```

To re-freeze, rebuild into `web/ja` and run `source/refresh_manifest.py` again.

## Validation and release boundary

- **Unit tests:** `python3 -m unittest tests.test_je3600a_cn_jp_web_layout` covers both editions:
  - identity, lineage and acceptance status;
  - cold replay equals the frozen `web/`;
  - the release admissions and the acceptance gate;
  - tamper rejection;
  - navigation;
  - visible copy equals the reviewed copy minus the listed removals, and the restoration log;
  - the merged glossary at print scale;
  - artwork reuse;
  - one shared derivation;
  - derivation reproducibility.

  Tests that rebuild skip with a message once the pinned shared inputs change: this edition is frozen against them.
- **Evidence:** `validation/layout-checks.json` records strict Sphinx, cold-replay byte parity and the browser gate at 1280×900, 768×1024 and 390×844 CSS pixels. The gate checks page overflow, broken images, live labels outside their art panel, label overlaps and script errors.

After the operator merges the engineering PR, the Git-only transaction continues per [web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline.md#22-git-only-transaction):
1. Seal `seal_frozen_web_evidence` at the merged `main` commit.
2. Assemble from current Hello-Docs `main`.
3. Open a `docs/publish/**`-only publish PR.
4. Verify the RTD routes, resources and desktop/mobile pages.

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows and dependencies. No phase2 or print target is enrolled.
