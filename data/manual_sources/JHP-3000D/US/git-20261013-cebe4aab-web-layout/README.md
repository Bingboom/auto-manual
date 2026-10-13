# JHP-3000D / US — Web-layout edition (EN, FR, ES)

Operator instruction, 2026-10-13: 「把这个版面调整一下」 for the published JHP-3000D US manual. Scope, as for JHP-5000C: 「英法西一起改」. Standing instructions: 「全部修，一次做完」, 「封面和目录 不用体现在web版面上」, and reuse of the existing shared components (「线上有很多现成的 都是双栏的啊」「不需要你重新另写」).

This edition fixes the Web layout of the [approved edition](../git-20261009-cebe4aab/README.md) (MA-278) against the same PDF: `Jackery HomePower 3000 User Manual.pdf`, SHA-256 `cebe4aab0a65d5fb2c36bb1867cdb6497e2a6db5251c46c61a33a530b862cf27`. English uses physical pages 4–21, French 22–39 and Spanish 40–57; p2 holds the three prefaces and p58 the shared back cover. The approved edition, its PDF and its release evidence remain immutable.

**Status: candidate, pending operator review.** `source_manifest.json` has no `publication_status`, so `rebuild.py` marks the replayed IR as not publication-eligible. Publication needs the operator's acceptance of these exact inputs in `source/approval.json` and `publication_status: operator-approved-git-only-release`; any later input change invalidates that acceptance.

## What changed

The full table, with the PDF page and log action for each change, is `source/differences.md`. In short:

- **Cover and TOC:** not part of the Web edition. Navigation has exactly the 13 chapters of the print TOC (p3), under each chapter's own page heading. The FCC statement is a title-less panel in MEANING OF SYMBOLS, and the back-cover contact card closes APP SETUP.
- **Shared components instead of approximations:**
  - the safety page in the two-column safety section the published template manuals already use (risk banner, WARNING lead heading the left column, each item in its print column);
  - the p13 button operations in the shared key-combination table, with the print's vertical buttons, button order and hold times;
  - the p11 auto-resume conditions in the shared auto-resume table.
- **Rich-text structure:**
  - safety pills, the plain grounding title and the p5 WARNING / DANGER lockups with the shared triangle;
  - circled LCD numbers, the shared ㉑ number cell and one print line per state;
  - regular state words, print bold runs and print paragraphs;
  - stacked fault codes F0–F3;
  - one specification value per print line, and `®` at its print position;
  - print paragraphs in the warranty cards;
  - the p58 contact card with glyphs and QR code.
- **Artwork:**
  - the App steps 2.3–2.5 show this product's screens from print p21 (the approved edition reused another model's screens);
  - the p13 button faces are native (the approved table showed the p10 POWER panel as its POWER button, a `power.svg` name collision);
  - the p58 glyphs and QR code are native, and the triangles are the shared ones.
- **Copy:** visible text is the approved text except the listed copy restorations (EN 5, FR 5, ES 5): the unprinted `FCC` title, the EN CAUTION label read together with stray body words, the FR/ES auto-resume row boundary, the button-name order and hold times on p13, and the `F0 / F1 / F2 / F3` separators. Print-source issues are kept as printed and listed for the source owner.

## Reconstruction

`derive_web_layout.py` regenerates, from the approved edition:
- `source/<language>/content.json` and `web_layout.json`;
- `source/figures.json` and `source/asset_decisions.json`;
- `assets/`.

A second run leaves the tree unchanged. It needs PyMuPDF 1.28.0 / MuPDF 1.29.0 (`requirements.lock`).

Hand-written files are not overwritten: `README.md`, `rebuild.py`, the validators, `source/differences.md`, `source/presentation.css` (approved geometry plus the authored Web-layout section) and `source/refresh_manifest.py`. The other `source/` records (coverage, native blocks, LCD references, unmapped words, native exceptions and visual text recovery) are the approved intake's, byte for byte. Their generators stay in the approved edition and must not be run against this one.

`rebuild.py` checks every inventoried input and the pinned shared repository inputs, then replays one language through the shared Manual IR APIs. Each locale's `assets/` holds only the files that its `content.json` and the source stylesheet reference.

Run from the repository root:

```sh
PKG=data/manual_sources/JHP-3000D/US/git-20261013-cebe4aab-web-layout
python3 "$PKG/derive_web_layout.py"
python3 "$PKG/source/refresh_manifest.py"
PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/rebuild.py" --language en --output tmp/jhp3000d-layout/en
python3 -m sphinx -n -W --keep-going -b html tmp/jhp3000d-layout/en tmp/jhp3000d-layout-site/en
```

Repeat for `fr` and `es`. To re-freeze, rebuild each language into `web/<language>` and run `source/refresh_manifest.py` again.

## Validation and release boundary

```sh
python3 -m unittest tests.test_jhp3000d_us_web_layout
python3 "$PKG/validate_source.py" --language en --output tmp/jhp3000d-layout-site/en
python3 -m http.server 8899 --bind 127.0.0.1 --directory tmp/jhp3000d-layout-site
python3 "$PKG/validate_layout.py" --base-url http://127.0.0.1:8899 --evidence-dir tmp/jhp3000d-browser
PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/validate_replay.py" --evidence-dir tmp/jhp3000d-cold-replay
```

- **Unit tests:**
  - identity, lineage and candidate status;
  - cold replay equals the frozen `web/`;
  - the release admissions;
  - tamper rejection;
  - navigation equals the print TOC;
  - visible copy equals the approved copy plus the listed restorations;
  - artwork reuse;
  - derivation reproducibility.

  Tests that rebuild skip with a message once the pinned shared inputs change: this edition is frozen against them.
- **Source gate:** checks every visible native line, the four specification grids (7/4/7/2 rows), 26 LCD entries, 13 reference figures with 61 live labels, the language badges, the consumed asset hashes, the shared safety, key-combination and auto-resume tables, the contact card and the 13 print chapters.
- **Browser gate:** runs at 1280×900, 768×1024 and 390×844. It checks overflow, broken images, labels outside their panel, label overlaps, inbox-card clipping and script errors.
- **Cold replay:** compares every frozen file and rejects five classes of tampered input.

After operator acceptance and the merge of the engineering PR, the Git-only transaction continues per [web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline.md#22-git-only-transaction):
1. Seal `seal_frozen_web_evidence` per language at the merged `main` commit.
2. Assemble from current Hello-Docs `main`.
3. Open a `docs/publish/**`-only publish PR.
4. Verify the RTD routes, resources and desktop/mobile pages.

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows and dependencies. No phase2 or print target is enrolled.
