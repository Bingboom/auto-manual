# Jackery SolarSaga 100 — US English Web candidate

Material **38-0001-000644**, model **JS-100F**, cover badge **V2** (no JAK-UM version string is printed). The original seven-page English 单语言 attachment and its SHA-256 are fixed in [source_manifest.json](source_manifest.json). The original PDF is [source/original.pdf](source/original.pdf). It is image-only, one 300-dpi raster per page with no text layer. All native text and the source-page mapping are in [source/transcription.json](source/transcription.json) and [source/page_map.json](source/page_map.json). The transcription was made with Tesseract 5 OCR ([evidence/ocr](evidence/ocr)), then every line was hand-corrected against the page pixels.

**Shared US/MX edition.** The print spec is HTO587H-**MX**-JAK, and the booklet prints the NOM mark, hello.mx@jackery.com and the JACKERY MEXICO S.A. DE C.V. address; the Feishu finished-goods spec is HTO587H-US-JAK. The operator confirmed on 2026-11-13 「JS-100F：这本是墨西哥版= 和美规共用」: this is the Mexico edition shared with the US. It is published as US/en with the copy exactly as printed. See `source_concerns`.

**Cover:** by operator rule (2026-11-13, 「封面信息 不用放进网页呀 直接从这个开始」) the Web page carries no cover or contents information and starts at its first body chapter. The cover facts (USER GUIDE, SolarSaga 100, Model: JS-100F, V2 badge, cover contact lines) are kept in `cover_facts` in the transcription, in the manifest and here.

## Conversion

The manual goes through the existing shared ManualIR Web pipeline. The block-to-component map is `component_map` in the manifest:

- **Parameters table:** the printed STC/BNPI table is one declared plain table, because it has three columns and spans. HB-TABLE-SPEC is two-column; the JS-100I JP spec-table exception is the precedent.
- **Multifunctional Adapter:** HB-TABLE-SPEC.
- **Tip:** HB-CALLOUT-STRIP.
- **Diagrams:** the four printed diagrams are HB-SPECIAL-REFERENCE-FIGURE, with their embedded English labels.
- **Warranty, contact and service:** HB-WARRANTY-SECTION.
- **FCC mark:** the shared FCC SVG.
- **NOM mark and QR:** small source crops.

The shared theme owns all styling. The package adds no colour, border or `ht-*` class.

## Artwork

Reuse decisions come before extraction and are recorded in [source/asset_decisions.preparation.json](source/asset_decisions.preparation.json).

- **Rejected:** the same product's EU edition art (`docs/renderers/web/assets/js100f_eu_en`, four diagrams). The EU V1 drawings show blank folding panels, while the US V2 pages show the cell grid.
- **Extracted:** the four diagrams, the NOM mark and the QR come from the current source through `tools.asset_intake` at native 300 dpi.
- **Reused:** the FCC mark is the shared SVG, byte-identical.

`derive_assets.py` reproduces every asset byte-for-byte.

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
