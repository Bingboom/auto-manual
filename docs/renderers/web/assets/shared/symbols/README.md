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

The gray Japanese variants and the fixed Li-ion32 mark come from the supplied
JBP-1000B-WH JP PDF. Six earlier generic candidates failed source glyph/tint
comparison; the seventh reuses the existing native Li-ion32 bytes. Their
physical-page, drawing-index and same-row caption bindings live in that source
package's `source/symbol_release_admission.json`. All seven retain candidate
status in this Git library, with no live registry promotion.

Before choosing a key, look up its meaning in `canonical_groups`. An
operator-confirmed group has one `canonical`; prefer it. A `legacy_variants`
binding still passes only within the fixed 2% tolerance; beyond it, bind the
canonical, which is released for the group through the listed caption, see
[canonical symbol groups](../../../../../../code-as-doc/build_doc_guide/web-component-admission.md#operator-confirmed-canonical-symbol-groups).
Do not add a new variant for a meaning that already has a confirmed canonical.

Do not re-extract an admitted matching variant for a new model, page or language.
When the authoritative glyph differs, document the difference and add a named
variant to this common library. Preserve native tint and group opacity; remove
only identified page/cell backgrounds. Full panels and App frames use their
own background policy.

[Artwork selection and admission contract](../../../../contracts/STYLE_DEFINITION/web-artwork-reuse.md#共用图标优先web-插图选材规则).

JBP-1000B-SIL adds five source-matched variants: a person reading inside a
circle, crossed flame, adult/child panel, and native dark screwdriver and Li-ion
glyphs. The old screwdriver/Li-ion variants have different native tint/lettering;
they remain valid for their original sources. These variants are bound to the
English, French and Spanish native rows by source-pixel captions and the fixed
glyph-comparison gate, then reused unchanged by all three locales.

`fcc/nested-c-native-dark` is the transparent original FCC glyph from JBP-1000B-SIL US p5, shared by all three locales. The legacy latex FCC raster contains a pale matte and is not used for this Web glyph. This entry is Git-local; no live promotion is performed.

`read-manual/person-circle-jhp3000d-native` retains the JHP-3000D US p5 native person-circle paths and tint. Existing variants were compared first; the fixed glyph/alpha gate rejects them for this source. This one acquisition is reused across EN/FR/ES and remains Git-local with no live registry promotion.

`no-open-flame/crossed-fire-je2000f` is the X-over-flames glyph of the JE-2000F EU batch-1465 source (`JE-2000F_修正版.ai`, pp. 117/135/153). No existing no-open-flame variant passes the fixed glyph comparison against it, so the native paths are retained once and reused by pt, nl and pl. Git-local; no live registry promotion.

Nine label marks have no manual source yet: `ce/label-hte156-ink`, `ukca/label-hte156-ink`, `ua-conformity/label-hte156-ink`, `un38-3/box-label-hte156-ink`, `triman/info-tri-packaging-hte156-ink`, `triman/info-tri-device-hte156-ink`, `ec-rep/label-hte154-ink`, `uk-rep/label-hte154-ink` and `battery-weee/crossed-bin-pb-hte154-ink`. They come from the JE-3000C and JE-2000F EU/UK labels in [`data/label_sources/EU/2kwh-icon-set-20261029`](../../../../../../data/label_sources/EU/2kwh-icon-set-20261029/README.md). The labels are reverse-printed, so these are the one operator-approved exception (2026-11-02) to keeping native tint: native paths, with only the label colours mapped to `#454546` by the recorded `ink_map`. `extract_marks.py --check` in that folder replays them byte for byte. Git-local; no live registry promotion; a manual whose authoritative artwork prints a different glyph or tint still gets its own variant.
