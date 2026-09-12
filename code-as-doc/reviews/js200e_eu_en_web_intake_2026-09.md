# JS-200E EU English Web Intake Review

## Scope and identity

- Target: `JS-200E / EU / en`
- Product: `Jackery SolarSaga 200`
- Source: DingTalk Base `YndMj49yWjP03jNjCDojvAQdJ3pmz5aA`, table `97v7518`, record `DFV5KKDywi`
- Source attachment SHA-256: `db150930c307590ad45daf236d1ed54ecbe05ca64e92b8b105abf5e058ff0f70`
- Source form: one PDF-compatible Illustrator page, `11219.300 × 7834.050 pt`
- English manual panel: six imposed pages within `x=4600.747–6941.733`, `y=1479.456–2003.866`
- Delivery scope: Web engineering only. No IDML, JP, live Bitable write, OSS upload, formal publication, or self-merge.

## Intake checklist

- [x] Exact model, market, language, product name and source record are pinned.
- [x] The supplied source hash matches the delegated hash.
- [x] The full artboard and all six English pages were visually inspected before extraction.
- [x] The shared `config.solar-eu-en.yaml` family config is reused; no per-model config was added.
- [x] JS-200E page-order differences are isolated in a target manifest and family diff.
- [x] Structured specifications are frozen under `data/manual_sources/JS-200E/EU/en/2.0/phase2` with target-local LF policy.
- [x] Safety, Inbox, Tip/Notes, specifications and warranty remain native semantic Web content.
- [x] The Inbox uses the shared renderer-neutral `HB-SPECIAL-INBOX` component.
- [x] Warranty years use the shared `HB-WARRANTY-YEARS` component and semantic warranty cards.
- [x] No LCD exists in the source; no LCD screenshot or power-station-only chapter was introduced.
- [x] Ten illustrations were extracted by the existing recipe pipeline and checked at 12×.
- [x] Complete image-owned grey panels retain their English labels and device markings.
- [x] Surrounding prose is excluded from crops to prevent image/live-copy duplication.
- [x] Recipe, illustration manifest, local registry and exported-byte hashes agree.
- [x] The build has no dependency on live Bitable or OSS.

## Component and image ownership

| Source area | Web owner | Decision |
| --- | --- | --- |
| Safety tips | HTML/RST | Live searchable list; no page screenshot. |
| What's in the box | Shared semantic component | Three source-matched object crops plus live labels. |
| Tip and usage notes | HTML/RST callouts | Live text; excluded from image crops. |
| Connection diagrams | Image | Preserve complete grey panels and image-owned connector labels. |
| Sun-angle guidance | Image + HTML/RST | Preserve complete grey panels; keep explanatory prose live outside the image. |
| Power-device diagram | Image | Preserve source-compatible host and interface markings; no host parameters are imported into structured data. |
| Technical parameters | Shared semantic spec tables | Native HTML/CSS; the source table is not rasterized. |
| Warranty | Shared semantic warranty components | Native year badges and cards; no warranty screenshot. |

## Source fidelity observations

- The source English pages contain `Jackery SolarSaga 200` and `JS-200E` consistently.
- The source power-device illustration depicts a compatible Jackery power station; it is retained only inside source artwork and is not treated as JS-200E product identity or specification data.
- The Web target contains only English. No `JS-100I`, `SolarSaga 100 Air`, `JE-2000F`, `2000 Plus`, LCD, UPS or App chapter is introduced.
- Specification values and the `3 YEARS + 2 YEARS` warranty periods come directly from the English source panel.

## Validation record

- [x] `build.py check` passes without capability warnings using the frozen target data root.
- [x] Real Pandoc conversion and `python -m sphinx -W --keep-going -b html` pass.
- [x] Publish-mode asset resolution validates all 10 target assets with zero errors and warnings.
- [x] Family fold covers 29 manifests (6 anchors, 23 folded) with byte-identical reconstruction.
- [x] Target and related regression suites pass; the full suite passes 3912 tests with 22 existing conditional skips.
- [x] Ruff, maintainability guardrails and 178-document link validation pass.
- [x] Chrome loads 10/10 images at 1440 px and 375 px; both viewports have zero broken images and zero whole-page horizontal overflow.
- [x] Desktop and mobile long screenshots were visually inspected.
- [x] Latest fetched `origin/main` equals the branch base at validation time; no exact-model or exact-branch PR exists.
- [ ] Engineering PR reviewed and merged.
- [ ] Formal publication and live URL verified.

Engineering preview and independent package readiness do not constitute formal publication.
