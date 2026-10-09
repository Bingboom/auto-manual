# Reusable Web symbols

`manifest.json` is the Web selection entrypoint. Choose a semantic key **and**
an explicit glyph variant, then copy the selected bytes unchanged into the
frozen package. Asset hashes and native source comparison are checked at fresh
sealing. `withdrawn` hashes identify obsolete Web files independently of their
names and paths. Historical sealed packages retain their own evidence.

The current candidate library reuses two repaired existing SVGs (warning and
book/information) and the existing shared WEEE PNG. Eight remaining variants
repair the missing suitable transparent artwork once using the asset-intake
recipe; they are shared across subsequent targets/locales whose native glyphs
match. They are local review candidates, without live registry promotion.

Do not re-extract an admitted matching variant for a new model, page or language.
When the authoritative glyph differs, document the difference and add a named
variant to this common library. Preserve native tint and group opacity; remove
only identified page/cell backgrounds. Full panels and App frames use their
own background policy.

[Artwork selection and admission contract](../../../../contracts/STYLE_DEFINITION.md#共用图标优先web-插图选材规则).

JBP-1000B-SIL adds five source-matched variants: a person reading inside a
circle, crossed flame, adult/child panel, and native dark screwdriver and Li-ion
glyphs. The old screwdriver/Li-ion variants have different native tint/lettering;
they remain valid for their original sources. These variants are bound to the
English, French and Spanish native rows by source-pixel captions and the fixed
glyph-comparison gate, then reused unchanged by all three locales.

`fcc/nested-c-native-dark` is the transparent original FCC glyph from JBP-1000B-SIL US p5, shared by all three locales. The legacy latex FCC raster contains a pale matte and is not used for this Web glyph. This entry is Git-local; no live promotion is performed.
