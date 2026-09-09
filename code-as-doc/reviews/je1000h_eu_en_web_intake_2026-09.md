# JE-1000H EU/en Web intake — 2026-09

## Scope

- Target: `JE-1000H / EU / en`
- Published source: `Jackery Explorer 1000 Plus User Manual (JE-1000H) EUUK V2.0-2026-08-03.pdf`
- Source SHA-256: `07e9ac4b9faabd0852f61702df06f2837caa952c2fa28151b599ad930b1c0bcc`
- Source size: 108 pages, 368.787 × 524.692 pt (approximately 130 × 185 mm)
- English manual body: physical PDF pages 6–22; EU radio declaration: physical page 108

## Controlled-source decisions

- The build reads only the target-scoped frozen snapshot under
  `manual_sources/JE-1000H/EU/en/2.0/phase2`; no live Bitable query is required.
- Product, port, LCD-map, battery-pack, charging, and App images are extracted
  from this JE-1000H source. No product illustration from another model is used.
- Product-overview crops exclude the source artwork's embedded FRONT VIEW and
  LEFT/RIGHT SIDE VIEW headings so the Web section headings are not duplicated.
- Text-bearing illustration frames consume their duplicated Web annotations.
  The LCD detail remains a searchable semantic HTML/CSS table beside the source
  numbered overview image; the manual is not published as PDF-page screenshots.
- Numeric values retain the published source notation, including 1024 Wh,
  1800 W rated / 3600 W surge, USB-C 140 W, 10 ms UPS transfer, and the DC
  expansion input/output limits.

## Verification and publication boundary

The extraction recipe, target illustration manifest, and every frozen source
file are SHA-256 locked. Local build, test, and preview evidence establish Web
readiness only. They do not establish merge, centralized publication, OSS
deployment, or a live asset-register write.

## Acceptance results

| Gate | Result |
| --- | --- |
| Approved-state asset replay | Pass: 108 archived pages, 108 previews, and 21 approved 12× illustration exports reproduced from the source PDF with locked hashes |
| Target source/manifest suite | Pass: frozen inputs, source manifest, illustration recipe/manifest, semantic output, cold IR replay, and asset-tamper rejection |
| Target build check | Pass: `build.py check` against the committed target-scoped frozen snapshot |
| Real Web build | Pass: 18 public-IR pages, 21 finished JE-1000H illustrations, 12/12 governed figure slots, 27 semantic LCD rows, and no unresolved placeholder token |
| Strict Sphinx | Pass: the generated MyST Web package builds with `python -m sphinx -W --keep-going -b html` |
| Generated-site media | Pass: 28 image references, zero missing files; localhost returned HTTP 200 for the manual and representative hash-addressed artwork |
| Browser layout | Pass: localhost preview was opened in the in-app browser; safety, LCD, charging, warranty, and App sections were visually inspected at the available narrow viewport without whole-page screenshot substitution |
| Asset registry | Pass: 219 records, 211 approved, zero registry errors; known missing/unmaterialized debt remains warning-only |
| Shared CI fixture | Pass: JE-1000H/EU/en runs instead of skipping; config-derived observation stays at 18 pass / 6 baseline skips / 2 baseline failures with both ratchets clean |
| Repository regression | Pass: 3,873 tests, 22 skipped |
| Static and policy checks | Pass: Ruff, maintainability guardrails, documentation links (170 files / 1,745 links / zero broken), Git diff check, and gitleaks |

## Remaining boundaries

- The Git-side target is ready for engineering review only; the branch and PR
  do not constitute merge or formal publication.
- No live Bitable source, capability, asset-source, or asset-registry row was
  written. The committed snapshot and CSV rows are the reproducible engineering
  input for this PR; any live synchronization requires separate authorization
  and exact record read-back.
- No Hello-Docs snapshot, OSS deployment, Read the Docs route, or production
  link has been created or verified.

## 2026-09-09 integration

The shared EU battery-pack slot uses generated-page model overrides so JE-1000H receives its reviewed chapter while JE-2000E retains its existing charging-page chapter without duplicates or foreign assets. Both target Web regression suites are included in integration validation.
