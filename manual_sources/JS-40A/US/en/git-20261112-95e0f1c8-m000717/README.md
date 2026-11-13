# Jackery SolarSaga 40 Mini — US English Web candidate

Material **38-0001-000717**, model **JS-40A**, printed **JAK-UM-V2.0**. Original nine-page English attachment and SHA-256 are fixed in [source_manifest.json](source_manifest.json). The original PDF is [source/original.pdf](source/original.pdf); all native text and source-page mapping are [source/transcription.json](source/transcription.json) and [source/page_map.json](source/page_map.json).

The complete manual is converted through the existing shared ManualIR Web pipeline. Five native quick-start captions precede their full diagrams inside shared panels; specifications, seven inbox cards, Note and warranty/service sections use shared components. Common style is owned by the shared theme, with no package paint or ht-* classes. The matching source artwork reuse and rejection decisions are recorded before extraction; nine donor files remain byte-identical and five current-source crops reproduce exactly.

This remains **review-candidate-no-release-authorization**, **publication_eligible=false**. Agent checks do not constitute operator source/pixel approval, a production release receipt, Base completion or online publication. No source-table or global asset-registry writes were performed.

Rebuild from repository root with `python <package>/render.py <unused-output-directory>`, then `python -m sphinx -n -W --keep-going -b html <output> <unused-html-directory>`. Reproduce/verify source art using `python <package>/derive_assets.py --output <unused-scratch-directory>`. Both commands check the locked source/art inputs and retain the review-only gate. [web/en](web/en) is the frozen source render.

Evidence includes independent full-body/source and desktop/mobile reviews, actual 1280/390 page screenshots with all lazy images loaded, shared-style admission, exact cold-rebuild identity and deliberate source-PDF/native-body/art/CSS tamper rejection. The global existing US build check is a repository regression gate, not validation of this new external body. Source grammar/concerns are retained in the transcription, not silently technically rewritten.

Raw OCR retains Tesseract EOF blank lines, and the strict-Sphinx log retains its original trailing stdout spaces. Those bound evidence bytes are preserved verbatim; whitespace checking covers the remaining source/code files.
