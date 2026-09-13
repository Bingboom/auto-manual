# JE-100C EU English Web intake — 2026-09

## Authority and target mapping

- Target: `JE-100C / EU / en`; public product name: `Jackery Explorer 100D`.
- Demand record: `0SLR873yRz` (`HTE162`).
- Published PDF node: `XPwkYGxZV3Rj0pEpF9mBdKrAWAgozOKL`.
- Published PDF SHA-256: `012465a75b3af63e66be5b16d553f3a0aa014256ac4cc0502a0f85dd3419bc1c`.
- Read-only structured source: `ZgpG2NdyVXrvPgqghPo1PyoA8MwvDqPk`.

The structured document was useful for chapter order only. Highlighted/struck
specification values differ from the published PDF, so the PDF is the sole
content authority for this target. No live source table or document was edited.

## Semantic mapping

The target selects `docs/manifests/manual_je100c_eu-en.yaml` from the shared
`eu-en` family config. Safety, maintenance, symbols, inbox, product overview,
three LCD interfaces (including fault and temperature states), operations,
charging, storage, specifications, and compact customer service warranty are
represented as live RST headings, admonitions, lists, and tables.

The PDF text-layer artifact `工作环境温度` is absent from the rendered source
page and is intentionally excluded. The product's 12 V and 24 V car-charging
support is retained; the unrelated 12 V-only shared warning is not used.

## Illustration contract

`data/asset_recipes/manual_je100c_eu_web.json` records the 64-page archive
catalog, source hash, page number, PDF-point crop box, scale, approval gate, and
expected output hash for every committed illustration. The intake command
replayed 141 artifacts (64 page PDFs, 64 previews, and 13 asset exports).

Inbox crops contain device art only. Overview and operation/charging instruction
panels retain the complete source grey frame and embedded source text. The LCD
interfaces and DISPLAY-button art retain only the device artwork; descriptions
remain native HTML tables, so the LCD composition is never a single screenshot.

## Dependency and publication boundary

This branch is stacked on PR #1082 for target-aware illustration manifests and
the shared Web semantic pipeline. It adds one minimal target-aware page-manifest
resolver instead of creating a per-model family config. Local builds and the PR
are review evidence only; neither is centralized publication.
