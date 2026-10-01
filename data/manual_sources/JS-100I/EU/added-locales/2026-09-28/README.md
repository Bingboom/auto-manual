# JS-100I EU native language candidates

`fr/es/de/it/uk/pt/nl/pl` are copied from the PDF-compatible native master
`HTS006-EU-9国语言-0928(1).ai` (SHA-256
`6fd4533fd713b25d95547afa0d839d7a52c74e6e6e40ebf2228c6c8218cbc92f`).
No OCR, machine translation or generative artwork was used. These are Git-only
review candidates, not published versions or promoted asset-registry rows.

Each `phase2/<language>` directory owns its 21 specification rows and localized
notes. `Source_lang` declares source copy; it does not filter duplicate rows in
Spec_Master. Always pair `--lang` with the matching `--data-root`:

```bash
AUTO_MANUAL_PRESENTATION_PROFILE=web python3 build.py md \
  --config configs/config.solar-eu-multilingual.yaml \
  --model JS-100I --region EU --lang fr \
  --data-root data/manual_sources/JS-100I/EU/added-locales/2026-09-28/phase2/fr \
  --staging-root .tmp/js100i-locales
python3 tools/readthedocs_source.py \
  --build-root .tmp/js100i-locales/docs/_build \
  --output-dir .tmp/js100i-locales/docs/_build/rtd
python3 -m sphinx -b html .tmp/js100i-locales/docs/_build/rtd .tmp/js100i-locales/html
```

Repeat the first command for each language into the same staging root before
assembling the combined preview. The family config is shared; these separate
source snapshots are not a merged-language data root. Existing English keeps
`config.solar-eu-en.yaml` and `en/2.0/phase2`.

`source/*.json` retains extracted wording, including original device-label
errors. `positioned_copy.json` records each field's native text, physical page,
selection rectangle and glyph IDs. German page 35 duplicates page 34 and is
excluded. Native line wrapping and ligatures are normalized; text is not
retranslated. STC/BNPI values remain individually labelled in the two-column
Web table. The source-authored design-load sentence follows those notes.
The shared English CE/manufacturer copy from page 87 is appended unchanged to
the eight warranties. Its identity remains SHENZHEN HELLO TECH ENERGY CO., LTD.;
source typography uses `CO.,LTD.`. Source errata and review boundaries are in
[the review record](../../../../../../code-as-doc/reviews/js100i_eu_nine_language_2026-09.md).

## Reproduce native derivatives

The master is operator-provided and is not checked into Git. Run from repository
root; choose a new scratch directory. Dependencies are the existing PyMuPDF /
lxml Python environment and Node with Playwright Chromium. No dependency upgrade
is required. `PLAYWRIGHT_MODULE` can point to an existing installation.

```bash
python3 tools/asset_intake.py \
  --asset-source-key source/manual_js100i_eu_nine_language_master \
  --asset-source-file "$MASTER" \
  --asset-recipe data/asset_recipes/manual_js100i_eu_shared_web.json \
  --asset-output-root .tmp/js100i-assets/package
python3 data/manual_sources/JS-100I/EU/added-locales/2026-09-28/reproduce/export_artwork.py \
  --master "$MASTER" --package .tmp/js100i-assets/package \
  --recipe data/asset_recipes/manual_js100i_eu_shared_web.json \
  --scratch .tmp/js100i-assets/svg --output .tmp/js100i-assets/rendered
node data/manual_sources/JS-100I/EU/added-locales/2026-09-28/reproduce/rasterize.cjs \
  .tmp/js100i-assets/svg .tmp/js100i-assets/rendered .tmp/js100i-assets/qa
```

The strict recipe packages 24 native PDF crops. The derivative stage removes
only the exact backdrop paths recorded in `backdrop_paths.json`, then rasterizes
16 native SVGs with Chromium to preserve their clipping paths. The eight dense
product views retain native labels and use direct native-page clips at 4x alpha.
`export_receipt.json` records both recipe PDF and final PNG hashes. The optional
QA directory gets 12x white/gray exports. Do not rasterize these SVGs with MuPDF:
its SVG importer loses the clipped magnification bubbles.

The original five Inbox PNGs are reused byte-for-byte from the older approved
master. English additionally retains its original product-view PNG. Each
illustration entry declares its own source master; the manifest does not claim
that old assets came from the new master. The original approved recipe stays
byte-identical; the new recipe remains quarantined and is not a registry
promotion.

`reproduce/extract_copy.py --master "$MASTER"` regenerates the locale JSON, RST
and CSV carriers from native spans. It overwrites those candidates; use only
when intentionally repeating intake and review the diff afterwards.
