# Jackery Battery Pack 2000 Plus — US English Web candidate

Material **38-0001-000574**, model **JBP-2000A** (project HTP002, region US+CA), printed **JAK-UM-V1.0**. The original eleven-page English 单语言 attachment and its SHA-256 are fixed in [source_manifest.json](source_manifest.json). The original PDF is [source/original.pdf](source/original.pdf); it is image-only (one 300-dpi raster per page, no text layer). Raw Tesseract 5 OCR is kept under [evidence/ocr](evidence/ocr); every line was hand-corrected against the page pixels into [source/transcription.json](source/transcription.json), mapped by [source/page_map.json](source/page_map.json).

The complete manual is converted through the existing shared ManualIR Web pipeline with shared components and the shared theme only: HB-TABLE-SPEC for the three specification groups, HB-SPECIAL-INBOX, HB-SPECIAL-REFERENCE-FIGURE for overview/LCD/power/usage/charging diagrams and the printed certification and App-store rows, HB-TABLE-REFERENCE (lcd-descriptions) for the LCD definitions, HB-CALLOUT-STRIP for Notes, HB-SPECIAL-FCC, and HB-WARRANTY-SECTION / HB-WARRANTY-YEARS. The block-to-component map is in `component_map` of the source manifest; there are no plain-table exceptions, package colours or ht-* classes. Cover and contents pages are not body content; product name, model, printed version and cover contacts stay native. The Jackery Mexico S.A. de C.V. block is kept as printed.

Artwork reuse decisions were recorded before extraction in [source/asset_decisions.preparation.json](source/asset_decisions.preparation.json): same-family JBP-2000B / JBP-3600A / JBP-1000B-SIL and shared assets were inventoried; none matches this product's drawings, so 15 complete source panels are extracted at native 300 dpi, and the standard FC mark is reused byte-for-byte from JBP-3600A US.

This remains **review-candidate-no-release-authorization**, **publication_eligible=false**, with no approval.json. Agent checks are not operator source/pixel approval, a release receipt, Base completion or online publication. No Feishu/Base writes were made.

Rebuild from repository root with `python <package>/render.py <unused-output-directory>`, then `python -m sphinx -n -W --keep-going -b html <output> <unused-html-directory>`. Reproduce and verify the artwork with `python <package>/derive_assets.py --output <unused-scratch-directory>`. [web/en](web/en) is the frozen render.

Evidence: independent full-body QC against the source pixels ([evidence/independent-body-qc.json](evidence/independent-body-qc.json)), strict Sphinx, real 1280/390 Chromium screenshots with all images loaded and no page overflow, shared-style admission, exact cold-rebuild identity, and source-PDF / native-body / art / CSS tamper rejection. Source concerns are recorded in the transcription, not silently rewritten.

Raw OCR keeps Tesseract's trailing blank lines and the strict-Sphinx log keeps its original stdout bytes; that evidence is preserved verbatim.
