# JE-2000F EU nine-language intake candidates

This source-local package uses the native PDF-compatible text and artwork of `HTE154-EU-9国语言-0924.ai`, SHA-256 `eb899f4407517869e1a0405ce2b2ed6daa76196f23197ad03fb0e295d39d84e6` (170 physical pages). The temporary local filename is `je2000f-eu-nine-languages.ai`. No OCR, translation, AI-generated technical artwork, live-table writes, or publication was performed.

- PL: physical pages 152–169; PT: 116–133; NL: 134–151. Each has 18 original body pages and 13 chapter identities.
- UK: 98–115 is **audit evidence only**. Its warranty exclusions are outlined in the source, and several differing App/operation geometries remain intentionally unresolved. Preserve the currently published UK route and the other existing six-language routes.
- All source defects are retained in `source/source_issues.json`. The internal AC nameplate and Dutch AC-button corrections are unapproved candidates in `candidates/errata/review.html`; they are not bound into output.
- Two missing DC glyphs are recovered from same-file Illustrator native text frames, with exact field/coordinate/AI-hash bindings in `source/glyph_recoveries.json`.
- Repeated printed App and Polish UPS segments are mapped in `source/print_duplicate_ledger.json`. The first complete occurrence is retained; the distinct medical, infrastructure and pacemaker warning on PL page161 is retained in full.
- `source/target_layout.json` contains this source's extraction coordinates and structure. It does not alter shared component CSS or introduce product defaults.
- Complex artwork remains source artwork. Overview crops exclude both chapter and view headings; view headings remain native text. LCD icons are bound by semantic identity to the committed, clean **JE-2000F/EU** attachments, with individual hashes.

## Reproduction

With the generalized shared `tools.frozen_pdf_*` adapter available, run from the engineering repository:

```sh
python3 -m tools.frozen_pdf_web --pdf /tmp/je2000f-eu-nine-languages.ai --recipe-root "$F_RECIPE_ROOT" --assets-manifest "$F_RECIPE_ROOT/pl_assets_manifest.json" --output /tmp/je2000f-pl-new-candidate --language pl
python3 -m sphinx -q -W --keep-going -b html /tmp/je2000f-pl-new-candidate /tmp/je2000f-pl-new-html
```

Set `F_RECIPE_ROOT` to this directory. Use a fresh output directory and repeat for `pt` and `nl`. No source PDF is checked into this package. Input files and artwork are pinned by `source_manifest.json`.

## Validation boundary

Iteration13 assembled all three languages through the common `assemble_book`/ComponentSpec pipeline (15 IR chapters each), and strict Sphinx passed for all three. See `source/qa/build_validation.json`. Native Warranty/App text geometry has unique line coverage in all three languages; see `source/qa/native_geometry_coverage.json`. These checks do **not** establish complete visual acceptance or recovery of text absent from the native source.

Browser inspection remains active. Iteration13 separates operation label/instruction lines, includes the complete Dutch LED-light instruction, restores the merged Polish/Portuguese car-charging headings, and renders each solar caption exactly once. Iteration13 widens standby-support geometry to retain every Portuguese/Dutch character and restores all troubleshooting action-number prefixes. Operation/App native artwork is stripped only through the committed extraction pipeline; the clean symbol/LCD assets come from the same JE-2000F/EU source family. `target_layout` explicitly declares pending source review so subsequent builds are **not publication eligible**. All three iteration13 candidates carry `publication_eligible: false`; earlier scratch candidates are superseded.

Post-iteration13 row audit found the first PT F6 line duplicated into F5 by character intersection. The final source recipe uses majority-line selection for every troubleshooting cell. `source/qa/troubleshooting_row_coverage.json` verifies unique membership and complete native action-line coverage in all three locales; the parent integration rebuild must verify the updated recipe.
