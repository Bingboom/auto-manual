# Jackery SolarSaga 100 Light — US English Web candidate

Material **38-0001-000864**, model **JS-100G**, project HTS017, finished goods US/CA. No manual version is printed, and none is inferred. The original seventeen-page English 单语言 attachment and its SHA-256 are fixed in [source_manifest.json](source_manifest.json). The original PDF is [source/original.pdf](source/original.pdf). It is image-only, one 300-dpi raster per page with no text layer. All native text and the source-page mapping are in [source/transcription.json](source/transcription.json) and [source/page_map.json](source/page_map.json). The transcription was made with Tesseract 5 OCR ([evidence/ocr](evidence/ocr)), then every line was hand-corrected against the page pixels.

**Cover:** by operator rule (2026-11-13, 「封面信息 不用放进网页呀 直接从这个开始」) the Web page carries no cover or contents information and starts at its first body chapter. The cover facts (USER MANUAL, Jackery SolarSaga 100 Light, Model: JS-100G, cover CONTACT US box; no version printed) are kept in `cover_facts` in the transcription, in the manifest and here.

## Conversion

The manual goes through the existing shared ManualIR Web pipeline. The block-to-component map is `component_map` in the manifest:

- **Box contents and Suspension Wire Kit:** HB-SPECIAL-INBOX.
- **Notes and warnings:** HB-CALLOUT-STRIP. The printed `Note:` lines are notes. The icon-only triangle boxes are warnings, labelled with the printed ⚠ glyph.
- **Mounting steps:** the six adhesive and nine suspension steps are native numbered captions above HB-SPECIAL-REFERENCE-FIGURE, inside the shared panel.
- **Other figures:** front/rear view, rope clamp, rope tensioner, and series and parallel connection are complete source figures.
- **Parameters table:** the STC*/BNPI* table is one declared plain table, because it has three columns and spans.
- **Warranty:** HB-WARRANTY-YEARS (5 YEARS Standard Warranty) and HB-WARRANTY-SECTION.
- **FCC mark:** the shared FCC SVG.

The printed INSTALLATION section (pages 03–12) becomes three Web sections: INSTALLATION / Adhesive Mounting, Suspension Mounting, and How to Connect Multiple Solar Panels. Copy and order are unchanged. The shared theme owns all styling. The package adds no colour, border or `ht-*` class.

## Artwork

No earlier JS-100G or SolarSaga 100 Light art exists. The 29 illustrations and the QR are extracted from the current source through `tools.asset_intake` at native 300 dpi. Each keeps complete edges and no neighbouring prose. One crop (adhesive step 1) whites out only the neighbouring step text, so that the wall-corner line stays complete. The FCC mark is the shared SVG, byte-identical. `derive_assets.py` reproduces every asset byte-for-byte.

## Status

**review-candidate-no-release-authorization**, `publication_eligible=false`, no `approval.json`. These agent checks are not operator source or pixel approval, a release receipt, Base completion or online publication. No Feishu, source-table or global asset-registry writes were made.

## Rebuild

From the repository root:

1. `python <package>/render.py <unused-output-directory>`
2. `python -m sphinx -n -W --keep-going -b html <output> <unused-html-directory>`

`python <package>/derive_assets.py --output <unused-scratch-directory>` reproduces and verifies the artwork. [web/en](web/en) is the frozen render.

## Evidence

- An independent full-body QC compared every Web block, table cell and image against the source pixels: [evidence/independent-body-qc.json](evidence/independent-body-qc.json).
- Strict Sphinx.
- Real 1280 and 390 Chromium screenshots, with no broken images and no page overflow.
- Shared-style admission.
- Exact cold-rebuild identity.
- Rejection of deliberate tampering with the source PDF, the native body, the source art, the frozen art and the CSS.
