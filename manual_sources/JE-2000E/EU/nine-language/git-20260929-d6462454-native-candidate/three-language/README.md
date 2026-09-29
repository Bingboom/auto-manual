# JE-2000E / EU native candidate source

This package is a local **review candidate**, not an approved release. It adds selectable Polish, Portuguese and Dutch source records from HTE152's September 24 nine-language AI. Existing en/fr/es/de/it/uk release 2.10 remains protected; Ukrainian is comparison-only.

## Authority and provenance

The PDF-compatible AI is the visual and native-text authority, SHA-256 `d64624547e3b88fd1d8c3ea78f9e446f07e2364b148b707eb0d97ba4c24415de`, 179 pages. `source/source_receipt.json` records the exact DingTalk record/attachment. Illustrator textFrames were inspected read-only; source fonts were not substituted or saved. No OCR or new translation was applied to body copy.

`source_manifest.json` pins every source recipe. `artwork_bindings.json`, `artwork_bindings.pt.json`, and `artwork_bindings.nl.json` independently pin artwork bytes. Source-local extraction recipes use the existing asset pipeline with crop and native-text redaction preserving graphics; extracted assets remain quarantined pending visual acceptance. The 27 icon assets come from this target's previously frozen source, mapped by semantic identity rather than filename number.

## Target differences

Fourteen chapters include battery expansion. LCD contains 27 semantic rows (the source shares number 23 across two temperature rows), troubleshooting contains F0–F9, FC and FE. There are three Overview views and four App control labels. Charging has three connection diagrams: AC wall, four SolarSaga panels, and vehicle. There is no independent single-panel drawing in this source. Body/table text remains native and selectable; complex Overview panels exclude the chapter heading.

## Candidate boundary

The new-language prefaces are missing from AI p4. `source/preface_candidates.json` proposes separately provenanced shared paragraphs, with the EU legal subject **Jackery**, explicitly confirmed by the operator on 2026-09-29. Approval of the complete reused prefaces remains pending A local preview may visibly mark these as pending; no approved source or publication claim is permitted. `source/candidate_review_ledger.json` preserves other source defects and geometry decisions. `source/uk_comparison_scope.json` records inherited approved fixes and the unresolved outlined-text comparison.

Run the existing shared `tools.frozen_pdf_web` entrypoint with this directory as `--recipe-root`, the exact AI as `--pdf`, the locale's artwork binding, and a fresh external output directory. This package must not add a per-model renderer or rewrite the old six routes. Public renderer, source coverage and visual checks must pass before any release decision.

## Local validation and handoff

The public `python3 -m tools.frozen_pdf_web` CLI and Sphinx HTML build are exercised for all three languages through the shared integration checkout. The result has 16 IR pages (introduction, fourteen source chapters, and source provenance). Every locale includes eight safety precautions, 27 LCD rows, twelve fault-code rows (including FC), three Overview views, five operation figures, four App control labels, and the expansion-battery chapter. `validation/candidate_validation.json` records final candidate paths, hashes, native-line triage and the exact acceptance boundary.

The native long-line triage checks PL 412 / PT 402 / NL 388 lines. The intentionally excluded 8 / 8 / 6 lines are only tiny repeated product-engraving AC/DC text inside diagrams. This check excludes short and outlined text, and is not a substitute for browser visual review. The Polish operation layout was browser reviewed by the coordinating task; PT/NL and mobile review remain part of that task's final acceptance. No old six-language route was modified by this source-local package.

The missing-preface banner and `publication_eligible: false` are intentional. Dutch literal App import markup remains explicitly pending review. This is not a release approval or a publication artifact.
