# JE-3600A / CN reviewed Git-only Web source

This package preserves the authoritative PDF and selectable source text, source-local
artwork decisions, recipes, shared glyph copies, Manual IR and MyST Web sources.
Operator accepted the layout and authorized Git-only push, merge and publication on 2026-10-13.
Authorization: MA-298. Reviewed candidate commit: 9275dd39f.
The PDF's printed revision is unconfirmed; the snapshot identifier is technical.

## Preview

- [zh](http://127.0.0.1:8941/CN/zh/manual_je3600a_cn_zh.html)

## Rebuild

From the repository root, use an unused output directory:

```sh
python3 manual_sources/JE-3600A/CN/git-20261012-caa5370a-reviewed/rebuild.py --language zh --output /tmp/je-3600a-cn-candidate
python3 -m sphinx -b html -n -W --keep-going /tmp/je-3600a-cn-candidate /tmp/je-3600a-cn-preview
```

Other languages use the same adapter and their native source page selections.
Shared presentation styles own headings, tables and callouts; source-local CSS
only preserves original figure geometry and table group arrangements.
Small glyphs reuse verified transparent shared assets. Base art retains structural
panels, product markings and complete phone frames; external labels are editable.
Independent caption frames are removed from base art and redrawn with CSS.
`validation/local-checks.json` records local preflight, not user acceptance.

## Original-source layout audit

The complete CN PDF was visually reviewed against the selectable Web candidate.
Source-local repairs restore semantic item lists, table state lines and ordered
troubleshooting steps; native figure labels and table key cells retain original
alignment. Reviewed asset reuse decisions and any new source-native selections
are in `source/layout-review.json` and `source/layout-artwork-recipes.json`.
Historical artwork remains byte-identical and is marked do-not-reuse where retired.
Complete App phone frames, clipped layers and native UI are preserved.
`validation/layout-checks.json` records fresh strict Sphinx, two byte-identical
cold builds, complete selectable text/resource closure and browser checks at
1280 and 390 CSS pixels. Dense native diagrams retain internal horizontal scroll
on narrow screens; App screens and prose fit the reading column.
The operator accepted this layout for Git-only publication on 2026-10-13.
