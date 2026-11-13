# JS-40A / JP / ja — m000464 source edition

Status: review candidate, no release authorization. The operator requested conversion of eight Japanese material manuals on2026-11-12. This package covers only material38-0001-000464; it does not claim that the transcription, new artwork or production release is approved.

The operator clarified on2026-11-12: 「000348和000464都是JS-40A的不同版本，只要464这个版本」. This delivery therefore includes only material000464. Its JP正文/规格/适用性均以当前464竖版附件为准。Source348 is retained under source/ only as a byte-verified donor for five matching text-free unfolding drawings, with a separate recipe and comparison against464 quick-guide pages3–5; no348 prose or specification is imported.

## Source and coverage

`source/original.pdf` is the exact current Feishu竖版说明书 attachment. `source/intake-source.json` records live record/field/name/token/hash. `source/transcription.json` retains every included Japanese/common text block, with physical-page IDs and disposition; `source/page_coverage.json` declares every physical page. The PDF type is fully outlined, so prose/specification values are manually transcribed from native renders and independently checked using Japanese OCR, not extracted as a text layer or translated. `evidence/ocr` keeps the independent output; visual source comparison governs OCR errors.

Includes the common quick-guide Japanese on physical3–5, Japanese body25–27, and common manufacturer/QR28. Physical2 is blank, printed language contents6 and other-language body/cover identity are excluded. The Japanese/body source values come only from this edition.

## Shared Web presentation

The existing public ManualIR/components→Web/MyST consumer is used. Specifications are native HB-TABLE-SPEC, contents HB-SPECIAL-INBOX, and figures HB-SPECIAL-REFERENCE-FIGURE. Instructions appear before each step illustration in shared hb-text-panel; notes/safety/contact use shared panels and native paragraphs/lists. No paragraph or table is represented by a screenshot. No package color/border/font stylesheet exists; source/geometry.css controls geometry only, checked by the prepared-document shared-style admission.

Reference editions are JS-100I JP ja (shared layout) and JS-40C EU en (comparison only). Their product facts/whole panel drawings are not substituted. Artwork selection and exact hashes are recorded in source/asset_decisions.json before extraction. New source crops remain quarantined review candidates. The existing asset_intake pipeline and source/asset_recipe.json reproduce them; no global or online asset registry has been promoted. Product markings/surfaces, full hand/arrow geometry, pouches/straps and QR frames are retained; no empty source caption frame remains.

## Reproduce

Use the repository lock-pinned runtime (PyMuPDF1.28.0). Run from repository root with fresh scratch directories:

```sh
python manual_sources/JS-40A/JP/ja/git-20261112-1a96bf34-m000464/derive_assets.py --output /tmp/git-20261112-1a96bf34-m000464-art
python manual_sources/JS-40A/JP/ja/git-20261112-1a96bf34-m000464/build_content.py
python manual_sources/JS-40A/JP/ja/git-20261112-1a96bf34-m000464/refresh_manifest.py
python manual_sources/JS-40A/JP/ja/git-20261112-1a96bf34-m000464/rebuild.py --output /tmp/git-20261112-1a96bf34-m000464-web
python -m sphinx -n -W --keep-going -b html /tmp/git-20261112-1a96bf34-m000464-web /tmp/git-20261112-1a96bf34-m000464-html
```

`build_content.py` requires every nonexcluded transcript row to be bound exactly once. `rebuild.py` checks source/input hashes, component inventory, ManualIR schema and shared-style admission, then replays through the existing shared Web renderer. A byte change in a source/asset fails validation. `web/ja` is the checked frozen candidate, not a deployed site; HTML screenshots and comparison evidence are under evidence/. The coordinator runs repository-wide checks and registration once for the eight-manual batch.

## Release boundary

The conversion prepares reviewable source/Web artifacts only. After operator acceptance, a separately approved frozen version and input-bound acceptance can enter the existing Git-only Web publication transaction. No phase2 target, print output, live queue/source/link record, shared component, workflow, production branch or RTD deployment was changed by this package.
