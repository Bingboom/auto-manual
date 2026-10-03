# JE-1000H EU: Portuguese, Dutch and Polish source package

Status: active

This is a local review candidate adding **pt/nl/pl only** to the existing
JE-1000H / Jackery Explorer 1000 Plus EU Web manuals. The existing
**en/fr/es/de/it/uk** sources and published frozen editions are unchanged.
It reuses `tools.frozen_pdf_web`, `manual-ir/v2`, registered ComponentSpecs
and the common Web renderer/CSS. No source-table write or publication is
part of this package.

## Source and files

- Native AI: `HTE159-EU-9国说明书-0928(1).ai`, PDF-compatible, 161 pages.
- SHA-256: `8bcb378fd0505237d91d5aa201d8bc0e84ee392963bfa6a73d32b8ed90b68feb`.
- Printed version: `JAK-UM-V1.0`; it differs from the existing EUUK V2.0
  English source. That does not authorize changing the six old editions.
- PT body: 110–126; NL: 127–143; PL: 144–160. Each has its own preface
  region on page 4 and includes common declaration/manufacturer page 161.
  Printed contents page 7 is omitted.
- `source_manifest.json` hash-pins every geometry/raw inventory in `source/`.
  `source/target_layout.json` declares source ownership and extraction geometry.
- `source/glyph_recoveries.json` records the scoped Illustrator-native recovery
  of PT `12 V⎓10 A máx.`; `source/errata.json` contains no unapproved changes.
- Each locale's `*_assets_manifest.json` pins image bytes and its existing
  Web component contract. `extraction_recipes/je1000h_eu_native.json` pins
  39 normalized PDF exports. The corrective `je1000h_eu_finished_panels.json`
  recipe adds 21 locale-bound finished panels, superseding seven stripped shared
  reference crops (kept as history). Complete panels intentionally retain their
  original backgrounds; they are not transparent standalone illustrations.
- Existing same-model LCD icons are reused by semantic identity; the two
  temperature pictograms form one of the source's 26 LCD rows. At the operator's
  request, row 21 now uses a fresh vector extraction from native page 114,
  replacing the blurred 43×34 RGB attachment and its neighboring table edge.
  Its shared transparent PNG is 261×142, rendered at 12× from the retained PDF;
  the battery outline, inner opening and `x8` follow the current source.

## Reproduce from the repository root

Use the unchanged original at its current path, and **new empty output
folders**. Example for Portuguese; repeat with `nl` and `pl`:

```bash
python3 -m tools.frozen_pdf_web \
  --pdf '/Users/pika/Desktop/HTE159-EU-9国说明书-0928(1).ai' \
  --recipe-root manual_sources/JE-1000H/EU/three-language/git-20260930-8bcb378f-intake \
  --assets-manifest manual_sources/JE-1000H/EU/three-language/git-20260930-8bcb378f-intake/pt_assets_manifest.json \
  --output /tmp/je1000h-pt-review-new \
  --language pt
python3 -m sphinx -q -W --keep-going -b html \
  /tmp/je1000h-pt-review-new /tmp/je1000h-pt-html-new
```

For a PDF-free replay, copy the complete frozen candidate folder and call
`tools.frozen_ai_web.replay_package(Path(<copied-package>))`. The saved
acceptance evidence guards reads of the recipe root and original AI, and
compares the regenerated Markdown SHA-256 exactly.

Formal native extraction:

```bash
python3 -m tools.asset_intake \
  --asset-source-key source/je1000h-eu-three-locales-native \
  --asset-source-file '/Users/pika/Desktop/HTE159-EU-9国说明书-0928(1).ai' \
  --asset-recipe manual_sources/JE-1000H/EU/three-language/git-20260930-8bcb378f-intake/extraction_recipes/je1000h_eu_native.json \
  --asset-output-root /tmp/je1000h-native-assets-new
```

Convert each normalized one-page PDF export to its corresponding `.png` with
PyMuPDF `page.get_pixmap(matrix=fitz.Matrix(4,4), alpha=True).save(png_path)`.
The connected-battery LCD icon uses `fitz.Matrix(12,12)` as recorded by its
asset binding, since a 4× rendering is too small for this narrow vector crop.
Verify the PNG against its asset manifest; never regenerate all manifests from
an earlier scratch generator, which would overwrite reviewed source geometry.
The recipe removes only identified source layout/text objects. Product shading,
markings, wires and leader lines remain native artwork. Before/after 12× white
and checkerboard evidence is stored in the local acceptance report.

## Source binding decisions

The App control diagram keeps its complete native gray rounded panel. Only the
page backdrop and text are removed; product artwork, leader halos and the panel
remain intact. Its crop is `[25,400,344,484]`, leaving margin above the panel.
The four HTML labels use each locale's native text bounds.

App connection result steps 2.3–2.5 reuse the existing JE-1000H EU asset
`docs/renderers/web/assets/je1000h_eu_en/app_connect_result.png` byte for byte.
The `app.result` binding records its repository source and SHA-256 instead of
claiming a new AI extraction. This English App UI matches the target source and
retains complete phone tops/status bars. The old cropped `app-result` files and
recipe remain historical, unbound outputs. No new renderer or CSS is needed.


The left-side overview crop is `[25,266,344,368]` on PT page 112, NL 129 and
PL 146. Its top edge includes the complete handle/body outline below the
native heading; the prior 269pt edge clipped that outline. The heading stays
native HTML and is not duplicated inside the image.

The energy-saving panel is a locale-bound complete crop: its gray outer frame,
top gray note, native single clock/`3s`, bracket and nearby labels stay together.
The existing ReferenceFigure component retains searchable semantic copy without
duplicating the printed clock or labels. The old stripped shared crop remains
as history and is no longer bound. Main-power keeps its native clock and
binds a text-only duration anchor. AC/DC prerequisite sentences remain normal
native paragraphs immediately before their cards. This prevents long translated
pills from covering circles or wires at desktop and mobile widths. Step labels
and durations use the existing responsive operation component. The battery-stack
crop excludes the neighboring accessories panel's border.

At the user's visual correction, energy saving, UPS, battery stack, accessory
row, AC wall, solar and car charging reuse each locale's full native panel. The corrective
recipe uses **crop only**: native gray backgrounds, white caption bands,
rounded borders, badge and printed labels remain intact. The battery-stack
crop extends through its own bottom border without including the accessory row.
The accessory crop `[28,418,344,490]` comes from PT page 119, NL 136 and PL 153.
This explicitly selected `source-finished-panel` mode sets `captions_embedded:
true`; native captions remain searchable/accessibility copy without duplicate
visible captions. It retains printed text in the image, rather than individually
editable HTML labels. Locale/page identity is checked for embedded captions.
The existing ReferenceFigure renderer is reused; no renderer or CSS is added.
The energy-saving crop `[27,228,343,375]` retains all four frame edges on PT
page 117, NL 134 and PL 151. It is a figure only; the surrounding paragraphs
remain native HTML. Reproduce these 21 panels with the intake command above, substituting
`je1000h_eu_finished_panels.json` and a new empty output root. Do not use the old
stripped shared crops for these six references.

Preserved source issues: PT `ON` / `Apagado`; three AC outlets in PT specs versus
two independently controlled pairs in the operation paragraph; some trademark
superscripts appearing at the end of an extracted paragraph. The PT overview
bitmap still has the original PDF font-glyph limitation despite verified
semantic recovery. These are review items, not silent corrections.

See [the acceptance report](../../../../../reports/je1000h-eu-nine-language/README.md)
for final candidate paths, screenshots, content audit and validation blockers.
