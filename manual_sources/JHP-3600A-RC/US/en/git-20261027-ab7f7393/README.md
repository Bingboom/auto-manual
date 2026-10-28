# JHP-3600A-RC / US / en — Git-only Web manual candidate

Operator instruction, 2026-10-27: 「把这个表中 未转网页版的说明书 走git only进行单语网页文档的转换」
(发布文档管理, record `reczz28SPRx9mcml`). This package is the English single-language manual of the
Jackery HomePower 3600 Plus, customer model JHP-3600A-RC.

**Status: `candidate-pending-operator-review`.** No operator acceptance is recorded; `rebuild.py` marks the IR not publication-eligible
until `source/approval.json` binds the reviewed inputs after the operator's 「上线提交发布」.
Route `JHP-3600A-RC/US/en/md`; there is no earlier US Web edition of this model, so it is the legacy default.

## Source authority

- 「【Jackery HomePower 3600 Plus】说明书-EN.pdf」, stored byte-exact as `JHP-3600A-RC-US-EN.pdf`,
  SHA-256 `ab7f7393ed6fd1e08656f19a48bdc7fce8f827ee9be629f8aebfd95b7d5cf857`; 24 pages, 130 × 185 mm, outlined.
- The design original (`source_manifest.json:design_original`) is recorded by name and hash only.
- `source/transcription.json` is the line-by-line transcription the Web copy is bound to. Wording,
  punctuation and spellings are kept as printed; `source_manifest.json:source_concerns` lists suspected
  source errors for the source owner.
- The JHP-3600A US reviewed Web edition is the shared reference edition; it supplies structure and reused
  artwork only.

## Layout

The Web body is the IMPORTANT preface (physical 2) and printed pages 01–20 (physical 4–23). Every printed
block maps to a shared component (`source_manifest.json:component_map`); no plain-table exception is needed.
`source/differences.md` lists each deliberate difference; `source/geometry.css` is geometry only.

## Artwork

`source/discovery.md` and `source/asset_decisions.json` record the inventory and every decision. Panels are
complete 3× source renders; 16 files (12 LCD icons, 3 key buttons, FCC mark) are reused byte-identically,
12 LCD icons are native vector extractions, and all 11 safety symbols reuse existing shared variants under
the fixed 2% admission. No shared catalog entry is added.

## Rebuild

From the repository root:

```sh
PKG=manual_sources/JHP-3600A-RC/US/en/git-20261027-ab7f7393
python "$PKG/derive_assets.py"        # artwork + symbol admission rows
python "$PKG/build_content.py"        # transcription -> source/en/content.json
python "$PKG/refresh_manifest.py"     # input inventory
python "$PKG/rebuild.py" --output tmp/jhp3600arc-us
python -m sphinx -n -W --keep-going -b html tmp/jhp3600arc-us tmp/jhp3600arc-us-html
python -m unittest tests.test_jhp3600arc_us_web
```

`rebuild.py` checks every input hash, replays the ComponentSpecs through manual-ir/v2 and the shared
Web/MyST pipeline, and enforces the prepared-document shared-style gate and symbol admission. Copy a fresh
render to `web/en` after any source change.

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows and dependencies.
