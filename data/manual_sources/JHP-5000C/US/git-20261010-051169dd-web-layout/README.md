# JHP-5000C / US — Web-layout edition (EN, FR, ES)

Operator instructions, 2026-10-10: 「继续调一下 这个的版面」 for the published JHP-5000C US manual, with the PDF from the Feishu record. Scope: 「英法西一起改」. Standing instructions: 「全部修，一次做完」, 「封面和目录 不用体现在web版面上」.

This edition fixes the Web layout of the [approved edition](../git-20261009-051169dd/README.md) (MA-279) against the same PDF: `Jackery HomePower 5000 Plus.pdf`, SHA-256 `051169dd15831f5670ada665146c3499e71e415c092a379fd782578bb517c26a`. English uses physical pages 4–27, French 28–51 and Spanish 52–75; p2 holds the three prefaces and p76 the shared back cover. The approved edition, its PDF and its release evidence remain immutable.

**Status: `operator-approved-git-only-release`.** The operator reviewed candidate `79797bb` with its chapter-by-chapter comparison sheets (print PDF beside the desktop and phone Web, all three languages). On 2026-10-10 they instructed 「上线提交发布」 with one correction, applied in `7728246`: the safety lists use the existing two-column layout (「不对 这个你要改两列的啊」「线上有很多现成的 都是双栏的啊」「不需要你重新另写」). After reviewing the rendered safety pages (print beside desktop and phone Web), they confirmed 「提交发布」.
- `source/approval.json` binds the hash of every package input except `web/` and itself.
- The rebuilt IR is publication-eligible.
- The engineering PR is merged by operator review (AGENTS.md §8.6), not by an agent grant.
- Any later input change invalidates the acceptance: `rebuild.py` then refuses until a new acceptance is recorded.

## What changed

The full table, with the PDF page and log action for each change, is `source/differences.md`. In short:

- **Cover and TOC:** not part of the Web edition. Navigation has exactly the 14 chapters of the print TOC (p3), under each chapter's own page heading.
- **Chapters:** user maintenance, symbols and FCC are sub-sections of the safety chapter; the HomePower, Battery Pack, Smart Transfer Switch and package sections are sub-sections of the AC ESS guide.
- **Rich-text structure in shared components:**
  - the safety page in the two-column safety section the published template manuals already use
    (risk banner, WARNING lead heading the left column, each item in its print column);
  - pills and the DANGER lockup with the shared triangles;
  - the print's three signal-word rows;
  - circled LCD numbers, with shared number cells where the print shares them;
  - the LCD SCREEN table rebuilt from the print geometry;
  - bold troubleshooting codes;
  - numbered notes and steps as lists;
  - print paragraphs in the warranty cards;
  - model identities in their bands;
  - one specification value per print line, and `®` at its print position;
  - ingestion-hazard notes with the print glyph;
  - the p76 contact card with glyphs and QR code.
- **Artwork:**
  - the overview views are framed whole;
  - French and Spanish figures whose print panel differs from English use their own locale panel;
  - each `web/<language>` carries only its own art.
- **Copy:** visible text is the approved text except the listed copy restorations (EN 9, FR 9, ES 16). Each one restores the PDF where the approved intake disagreed, for example the shifted signal-word meanings, labels read into callout bodies, unprinted `FCC` / `CONTACT US` titles and the ES p69 line taken for the folio. Print-source errors (text in the wrong language, typos) are kept as printed and listed for the source owner.

## Reconstruction

`derive_web_layout.py` regenerates, from the approved edition:
- `source/<language>/content.json` and `web_layout.json`;
- `source/figures.json` and `source/asset_decisions.json`;
- `assets/`.

A second run leaves the tree unchanged. It needs PyMuPDF 1.28.0 / MuPDF 1.29.0 (`requirements.lock`).

Hand-written files are not overwritten: `README.md`, `rebuild.py`, the validators, `source/differences.md`, `source/presentation.css` (approved geometry plus the authored Web-layout section) and `source/refresh_manifest.py`. The other `source/` records (coverage, LCD and symbol provenance) are the approved intake's. Their generators stay in the approved edition and must not be run against this one.

`rebuild.py` checks every inventoried input and the 244 pinned shared repository inputs, then replays one language through the shared Manual IR APIs. Each locale's `assets/` holds only the files that its `content.json` and the source stylesheet reference.

Run from the repository root:

```sh
PKG=data/manual_sources/JHP-5000C/US/git-20261010-051169dd-web-layout
python3 "$PKG/derive_web_layout.py"
python3 "$PKG/source/refresh_manifest.py"
PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/rebuild.py" --language en --output tmp/jhp5000c-layout/en
python3 -m sphinx -n -W --keep-going -b html tmp/jhp5000c-layout/en tmp/jhp5000c-layout-site/en
```

Repeat for `fr` and `es`. To re-freeze, rebuild each language into `web/<language>` and run `source/refresh_manifest.py` again.

## Validation and release boundary

```sh
python3 -m unittest tests.test_jhp5000c_us_web_layout
python3 "$PKG/validate_source.py" --language en --output "$PKG/web/en"
PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/validate_lcd.py" --output "$PKG/web/en" --evidence-dir tmp/jhp5000c-lcd-en
python3 -m http.server 8898 --bind 127.0.0.1 --directory tmp/jhp5000c-layout-site
python3 "$PKG/validate_layout.py" --base-url http://127.0.0.1:8898 --evidence-dir tmp/jhp5000c-browser
PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/validate_replay.py" --evidence-dir tmp/jhp5000c-cold-replay
```

- **Unit tests:**
  - identity, lineage and candidate status;
  - cold replay equals the frozen `web/`;
  - the release admissions;
  - the acceptance gate;
  - tamper rejection;
  - navigation equals the print TOC;
  - visible copy equals the approved copy plus the listed restorations;
  - artwork reuse;
  - derivation reproducibility.

  Tests that rebuild skip with a message once the pinned shared inputs change: this edition is frozen against them.
- **Source gate:** checks every visible native line, the 12 specification grids, 26 LCD entries, 26 reference figures with their live labels, the language badges and the consumed asset hashes.
- **Browser gate:** runs at 1280×900, 768×1024 and 390×844. It checks overflow, broken images and failed requests, labels outside their panel, label overlaps and occlusion.
- **Cold replay:** compares every frozen file and rejects five classes of tampered input.

After the operator merges the engineering PR, the Git-only transaction continues per [web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline.md#22-git-only-transaction):
1. Seal `seal_frozen_web_evidence` per language at the merged `main` commit.
2. Assemble from current Hello-Docs `main`.
3. Open a `docs/publish/**`-only publish PR.
4. Verify the RTD routes, resources and desktop/mobile pages.

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows and dependencies. No phase2 or print target is enrolled.
