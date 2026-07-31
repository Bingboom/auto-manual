# IDML CJK Fallback Runs Discovery — 2026-07-31

## Decision

Stage 5 item 10 is implemented as explicit editable character runs, using the
renderer token `idml_font_family_cjk`. The token is represented by
`tools.idml.font_family.CJK_FONT_FAMILY_TOKEN` and currently resolves to the
already-declared `Arial Unicode MS` resource.

This is deliberately not a `data/layout_params.csv` token. Font fallback does
not change page geometry by itself, and adding a global layout row would
invalidate approved reference-layout identities for Latin-only targets.

## Character Routing

`tools/idml/inline_text.py` retains the existing exact symbol-fallback map as
the first authority, then routes these script/presentation blocks to the CJK
family:

- Han ideographs and compatibility/extension blocks;
- Hiragana, Katakana, Bopomofo, and their extensions;
- Hangul Jamo, compatibility Jamo, and syllables;
- CJK punctuation, radicals, strokes, enclosed forms, vertical forms, and
  fullwidth/halfwidth forms.

The implementation does not use East Asian Width for font selection because
emoji can also be classified as wide. Width-aware line estimation remains the
separate Stage 5 item 11.

## Compatibility Evidence

- Existing `Fonts.xml` and delivery manifest bytes are unchanged: the CJK
  family was already present as the general symbol fallback.
- English and French golden packages retain every part byte-for-byte.
- Japanese and Korean packages each change only 18 localized Story XML parts;
  their resource and spread parts remain unchanged.
- Both localized packages pass exporter self-check after component font-style
  overrides were made composable with explicit fallback runs.
- The approved layout-parameter hash and reference-layout contract are not
  modified, so no reference layout rebind is required.

## Follow-up Boundary

This change guarantees that CJK source characters do not inherit the Gilroy
paragraph family. It does not claim line-fit parity. Item 11 must update line
estimation from the Latin `0.52 × point size` assumption to Unicode
East-Asian-width-aware measurement, using the CJK golden packages as its byte
safety net.
