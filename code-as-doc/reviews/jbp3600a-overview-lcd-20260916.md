# JBP-3600A EU/en overview and LCD presentation

Use the operator-supplied current published PDF (filename says JBP-3000A;
visible product and frozen target are JBP-3600A), SHA-256
`084dd4517feddcd9b77da10415a2787ec4427f882a7b819160725fdff679ccfe`.

The overview now has separate front and left illustrations under native Web
headings. Each crop retains its product markings, labels and leader lines;
it excludes the source heading. Explicit exact-text coverage bindings consume
only the redundant annotation tables and preserve their text as image alt.

LCD uses an annotated display map without the LCD DISPLAY heading or the
source table. The two explanation rows remain searchable native text, using
the existing text-only LCD legend (number/icon columns hidden). The source
rows retain their wording; only unused figure references are cleared.
The LCD style is shared with the existing JBP-2000B EU presentation, scoped
to the two exact artwork paths. Other product layouts remain unchanged.

## Reproduce crops

Render the following rectangles with PyMuPDF `get_pixmap(matrix=fitz.Matrix(4, 4),
clip=fitz.Rect(bbox), alpha=False)`. Page numbers are one-based; coordinates
are PDF points from the top-left. Each manifest entry records source name/hash,
page, bbox, scale and output hash.

| Asset | Page | Rectangle |
| --- | --- | --- |
| overview_front.png | 6 | 27, 304, 152, 432 |
| overview_left.png | 6 | 157, 304, 340, 432 |
| lcd_annotated.png | 7 | 27, 54, 342, 110 |
| power_annotated.png | 7 | 35, 232, 334, 309 |
| lcd_control_clean.png | 7 | 35, 387, 334, 466 |
| clearance_clean.png | 8 | 31, 352, 339, 484 |
| stacking_clean.png | 9 | 27, 10, 342, 191 |
| locking_clean.png | 9 | 27, 260, 342, 498 |

## Validation and release

Build with `build.py md --config configs/config.bp-eu-en-web.yaml --model
JBP-3600A --region EU --lang en --data-root manual_sources/JBP-3600A/EU/en/phase2`
and `AUTO_MANUAL_PRESENTATION_PROFILE=web`. Run the exact-target regression suite,
strict Sphinx build and desktop/mobile browser checks. The formal source
inventory is rehashed after clearing the two unused LCD icon references.

This engineering change requires rebuilding the frozen JBP-3600A/EU/en Web
publication through the existing Git-only flow before RTD can display it.
It does not change live tables, other languages, or the published PDF.

Battery-pack layout rules live in `web_battery_pack_components.css`, assembled
immediately after the base stylesheet by the existing ordered CSS loader. The
public stylesheet URL remains `web_manual.css`; existing JBP-2000B rules keep
the same cascade order and target scoping.

Operations follow the same boundary: crops contain only the device/hand art
and On/Off labels. Native headings, NOTE and LCD instructions remain outside
the images, with complete CSS card borders. Exact-text coverage consumes the
duplicate On/Off line block and preserves it as image alt text.

The connection clearance crop excludes the source CAUTION panel and broken
source frame; CSS supplies a complete frame. The native CAUTION is placed
before the diagram to match the published PDF, with unchanged wording.

The former full-page stacking/locking image is split at its NOTES panel. The
Web-only template renders stacking artwork, native NOTES, then locking artwork.
The NOTES copy is never embedded in a raster image; its existing wording stays
searchable and selectable. The additional Web artwork binding is confined to
the existing JBP-3600A EU/en configuration.

## Charging and warranty follow-up

AC charging is recropped from the supplied PDF page 10, bbox `[26, 115, 343, 272]`, at 4x, excluding the preceding warning frame. The exact-target warranty source pattern now includes `warranty_en`, enabling existing shared native warranty lead, section and year components. Copy remains unchanged.

The exact JBP-3600A Web warranty carrier separates duration and label into two strong nodes, omitting only the inline dash separator. Other targets and the shared renderer remain unchanged; the region profile and generated manifest/family diff bind this PDF-matched carrier.

The template structure baseline adds only `jbp3600a_11_warranty.rst: [[en-web]]`: this new exact Web carrier is intentionally separate from the unchanged shared print carrier. Existing language groups remain pinned.
