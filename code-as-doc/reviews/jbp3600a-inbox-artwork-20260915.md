# JBP-3600A EU/en packing-list artwork correction

The Web three-card component supplies each border, item number and caption.
The former image crops also included borders and numbers, producing nested
cards. Three target-scoped Web illustration replacements now contain only
the product, expansion cable and manual icon.

## Source and reproduction

Source: operator-provided `Jackery Battery Pack 3600 User Manual (JBP-3000A)
EUUK V2.0-2026-08-04.pdf`, SHA-256
`084dd4517feddcd9b77da10415a2787ec4427f882a7b819160725fdff679ccfe`.
The cover identifies **JBP-3600A**, despite the filename. Extract page 6
(one-based), using top-left PDF-point coordinates and PyMuPDF
`page.get_pixmap(matrix=fitz.Matrix(4, 4), clip=fitz.Rect(bbox), alpha=False)`.
No text removal or redrawing is involved; product markings remain intact.
Each output is 336 x 240 pixels, on the same canvas for consistent scale.

| Output | Crop rectangle | SHA-256 |
| --- | --- | --- |
| inbox_unit_clean.png | [38, 106, 122, 166] | `4f5d7e1edd8b9a0845cc2071a57aafaccdd245811594d3f9b2b9bb8df20b3b44` |
| inbox_cable_clean.png | [145, 106, 229, 166] | `0a2f4e72a751a9b8371ea98a0aa330faffab47b36c76a41694e898af9b5d4de7` |
| inbox_manual_clean.png | [251, 106, 335, 166] | `8e9ae2dfc7de714cac9eb0ac26ab4ee00f43daecd8a13abe9ed438897bdba040` |

The existing Web illustration manifest binds the three replacement filenames
and records per-entry source PDF hashes, page, crop box and scale. Existing
manifest entries and the original Illustrator extraction recipe are unchanged;
the new per-entry PDF provenance applies only to these three crops.
No asset-registry, live table, frozen structured source, shared renderer,
LaTeX asset or manual wording changes are required.

## Verification

- Real `build.py md` using `configs/config.bp-eu-en-web.yaml`,
  JBP-3600A/EU/en and its frozen `manual_sources` data completed.
- Target `build.py check` passed with the same frozen input.
- Sphinx HTML rendered and Chromium screenshots inspected at 1280px and 390px:
  one border and one number per card, all three images loaded, no nested frames.
- The complete generated Markdown before/after is identical after replacing
  only the three `.hb-inbox-art` tags with a common marker. Captions and all
  other chapters are unchanged.
- 29 targeted Web IR / illustration manifest tests passed.

## Release boundary

Engineering correction only: merge, rebuild the JBP-3600A/EU/en frozen Web
publication through the existing Git-only release flow, then verify its RTD
page. Mirroring the renderer assets alone does not rewrite an already frozen
`docs/publish` manual. Online acceptance is pending.
