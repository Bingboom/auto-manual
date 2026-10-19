# Jackery SlimPower H1 — JE-1000E-WH / JP / ja

Git-only engineering **candidate**, `publication_eligible=false`. This package
uses only the supplied Japanese PDF. Filename version V2.0 / 2026-07-29 is
provenance; printed version is unknown. Physical pages 1–27 are retained:
cover 1, printed TOC 2, Japanese body 3–26 (printed 01–24), back-cover QR 27.

Source SHA256:
`efb663e3b22fec90bb8d4f602cb830471360034d9ead9293168f708ce937c3be`.

## Editable source and replay

`source/chapters.json` owns the 17 semantic chapters as neutral Manual IR flow
and shared ComponentSpecs. Text, tables, warnings and external figure labels
remain editable; complete product panels and native phone UI stay artwork.
Four finished localized illustrations (UPS, AC/solar/car charging) retain native
non-empty captions and diagram numbers, with exact semantic companions. These
visible caption edits require a new source-local asset; see provenance.
`source/native-text.json` records all source blocks, lines and geometry.
`source/dispositions.json` accounts for every native block. Native line coverage
is independently checked against rendered HTML, with explicit glyph/plus rules.
`source/reading-order.json` records the native safety panel ordering. The
recycling heading and body share their original icon row; warnings retain
separate instructions, explanations and abnormal-condition lists.
`source/presentation.css` bounds the cover figure and gives chapter targets
block geometry. It travels through the shared frozen source-stylesheet contract;
no shared renderer or theme preference is changed. Repeated cover names are
represented once in the title, while every native cover sentence is retained.

From the repository root (use new output directories):

```sh
PKG=manual_sources/JE-1000E-WH/JP/ja/git-20261008-efb663e3
PYTHONPATH=. python3 "$PKG/rebuild.py" --output /tmp/h1-cold \
  --pdf '/Users/pika/Downloads/Jackery SlimPower H1取扱説明書V2.0-2026-07-29.pdf'
python3 -m sphinx -W --keep-going -b html /tmp/h1-cold /tmp/h1-html
PYTHONPATH=. python3 "$PKG/verify.py" --html /tmp/h1-html/manual.html
python3 -m http.server 8817 --bind 127.0.0.1 --directory /tmp/h1-html
```

Follow-up edits belong in semantic source, not generated `web/ja/manual.md` or
IR. After reviewing a source change, run `python3 "$PKG/seal.py"`, rebuild into
new directories, rerun verification/Sphinx/browser checks, and replace `web/ja`
with that verified bundle. `validation/output-inventory.json` independently
pins generated outputs; it is not embedded in its own IR (avoids hash cycles).
Shared renderer changes require a fresh replay; no target HTML renderer fork.

## Assets and boundaries

`asset_provenance.json` records reuse decisions, native geometry and SHA256.
Mechanical US JE-1000E-SIL panels were compared to the JP originals before
byte-identical reuse; no US prose/specifications are imported. Shared symbols were inspected against the native source; none passed the
fixed glyph/tint/transparency comparison. The twelve safety icons use unchanged
native vector paths, with cell backdrops excluded by geometry. Rejected old
candidates stay under `validation/rejected-symbols/` and are absent from Web. The grouped JP Wi-Fi/Bluetooth row uses its exact
native pictograms; all 12 original indicator numbers remain intact.

`source/asset-recipe.json` is the strict source-local extraction recipe (19
illustration/QR crops plus 12 native vector symbols):

```sh
python3 build.py asset-intake \
  --asset-source-key source/je1000e-wh-jp-efb663e3 \
  --asset-source-file '/Users/pika/Downloads/Jackery SlimPower H1取扱説明書V2.0-2026-07-29.pdf' \
  --asset-recipe "$PKG/source/asset-recipe.json" \
  --asset-output-root /tmp/h1-assets
```

All new assets are quarantine, build-ineligible for global reuse and require
visual review. Candidate-local inclusion is not registry approval/promotion.
QR pixels are preserved; no destination is inferred or substituted. The App
store badges and QR are separate assets in the shared download component;
its decorative QR is intentionally hidden from accessibility text.

`source/differences.json` records original technical wording and the F2/F6
font-glyph recoveries. No translation or technical correction was performed.
See `validation/REVIEW.md` for actual evidence and limits. Production admission
and operator review are pending. No Base, source table, queue, HTML_link or asset
registry writes; no merge, mirror or RTD publication.
