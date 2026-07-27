# JE-1000F US PR4: safety and symbols parity

## Scope

PR4 aligns the repeated safety and meaning-of-symbols compositions on physical
pages 4-5, 22-23, and 40-41 with the supplied V2.0 reference. It starts from
PR3 commit `2e93f006` and preserves the already accepted pages 1-3.

The supplied Illustrator master remains the only permitted source for placed
image assets. The reference PDF is used only to measure geometry and pixel
residuals; it must not be linked, cropped, rasterized, or embedded as visible
production artwork.

## Current baseline

The PR3 renderer was rebuilt from the current frozen review content with Adobe
InDesign 2026 21.0.1.6. It reports 58 pages, zero missing fonts, zero bad links,
and two known content-flow oversets outside PR4: Spanish operation on physical
pages 46-49 and Spanish warranty on page 55. Its governed 300 dpi comparison
against the supplied reference gives:

| Physical page | Language / composition | RGB MAD | Changed-pixel ratio |
| --- | --- | ---: | ---: |
| 4 | English safety | 0.066938 | 0.240757 |
| 5 | English symbols | 0.072101 | 0.221541 |
| 22 | French safety | 0.085679 | 0.294457 |
| 23 | French symbols | 0.071443 | 0.212896 |
| 40 | Spanish safety | 0.087845 | 0.302323 |
| 41 | Spanish symbols | 0.070031 | 0.212208 |

The strict page thresholds remain RGB MAD at most `0.008` and changed-pixel
ratio at most `0.040`.

## Revalidated findings

The earlier discovery report predates `2e0165ec`. Its first-round fixes are
already present: safety-tail and signal badges use governed warning artwork,
symbol icon frames are token-driven, and the symbol columns and gap have
explicit component tokens. PR4 therefore will not repeat or revert those
changes.

A fresh side-by-side render of PR3 and the supplied reference shows:

- Safety-page outer bars and warning lockups are close, but the two-column text
  uses different line composition, column starts, and vertical distribution.
  French and Spanish have the largest residuals.
- On symbols pages, the reference uses larger signal badges and symbol artwork,
  different table column ratios, and tighter content-to-shell alignment.
- English, French, and Spanish require separate vertical page profiles while
  sharing the same semantic components and source content.
- All labels and body copy must remain live text. All warning and symbol images
  must remain the AI-derived semantic assets already linked by the exporter.

## Implementation phases

1. Add characterization tests for safety frame coordinates, language-scoped
   text metrics, symbol table columns/insets, icon frames, and shared asset
   bindings before changing production code.
2. Measure the reference safety-page regions and tune only governed shared or
   language-profile parameters. Do not edit frozen RST or phase2 copy.
3. Measure signal and icon tables, then adjust token-driven badge, icon,
   column, inset, row, and shell geometry while preserving editable stories.
4. Export from the current frozen `docs/_review/JE-1000F/US` source with the
   pinned phase2 data snapshot, finalize in native InDesign, and compare the
   six target pages after each coherent tune. Do not reuse the stale PR2 bundle.
5. Run a full 58-page regression. Keep the phase only if pages 1-3 do not
   regress and pages outside PR4 retain their PR3 governed metrics.
6. Package INDD, portable linked IDML, PDF, preflight, focused parity, full-book
   regression, and an asset provenance manifest as untracked review artifacts.

## Intended production surface

- `tools/idml/pages.py` for safety-page composition.
- `tools/idml/symbols_page.py` for combined maintenance and symbols geometry.
- `tools/idml/styles.py` only if measured live-text metrics cannot be expressed
  by existing page/component tokens.
- `data/layout_params.csv` and
  `docs/renderers/contracts/manual_style.yaml` for governed geometry tokens.
- IDML characterization tests and their golden fixtures.

## Non-goals

- No source-copy, phase2 schema, dependency, public CLI, review-sync, or
  workflow changes.
- No LCD, operation, charging, troubleshooting, FCC, inbox, specification,
  warranty, app, or back-cover tuning.
- No finished-page screenshots or reference-PDF crops in production IDML.
- No generated `_build`, `_review`, `output`, `reports`, or `tmp` artifacts in
  the commit.

## Frozen-content constraint

The approved reference plan is rebound to the current target-scoped frozen
review content (`manual_content_sha256` =
`cc2ac59f3878788028f7acf61aa1fce535a3e2b80aaa87e8978e50b1db51fae7`).
Its 52 source-page bindings still cover the same 58 physical pages. This PR
must not alter the review copy or broaden the JE-1000F US-only sync exception.

## Safety nets and acceptance

- Physical page count remains 58.
- Native preflight has zero overset on the six PR4 target pages, zero missing
  fonts, and zero bad links. The two frozen-content oversets on pages 46-49 and
  55 are explicitly deferred to PR6 and PR9; PR10 owns the full-book zero-
  overset and PDF/X-4 gates.
- The six-page aggregate improves from the frozen-content baseline without a
  material target-page regression. The strict per-page visual thresholds remain
  the PR10 final-book gate rather than a false PR4 completion claim.
- Pages 1-3 retain their PR3 passing metrics.
- Pages outside PR4 have identical governed metrics to PR3.
- IDML audit confirms live safety/symbol text, editable native table geometry,
  no visible whole-page reference-PDF link, and no newly placed image asset.
- Portable delivery reports zero missing links.

Verification ladder:

```text
python -m ruff check build.py integrations tools tests scripts
python -m unittest <targeted safety and symbols tests>
python -m unittest
python tools/check_maintainability_guardrails.py
python tools/check_doc_link_integrity.py
python build.py check --config configs/config.us-en.yaml --model JE-1000F \
  --region US \
  --data-root /Users/pika/Documents/auto-manual2-pr2-visual-parity/data/phase2
```

Production proof additionally requires native InDesign finalization, focused
six-page parity, a full 58-page regression, archive integrity, link inventory,
and SHA-256 inventory.

## Final PR4 evidence

The accepted v16/final candidate retains the frozen 52-source-page to
58-physical-page map. The focused 300 dpi result is:

| Physical page | Baseline MAD / changed | PR4 MAD / changed | Result |
| --- | ---: | ---: | --- |
| 4 | 0.066938 / 0.240757 | 0.067122 / 0.241340 | effectively stable |
| 5 | 0.072101 / 0.221541 | 0.068740 / 0.213908 | improved |
| 22 | 0.085679 / 0.294457 | 0.080486 / 0.272773 | improved |
| 23 | 0.071443 / 0.212896 | 0.071083 / 0.212176 | improved |
| 40 | 0.087845 / 0.302323 | 0.086677 / 0.292256 | improved |
| 41 | 0.070031 / 0.212208 | 0.069480 / 0.211433 | improved |

The six-page mean is `0.073931 / 0.240648`, down from approximately
`0.075673 / 0.247364`. A 72 dpi pixel regression against the last equivalent
native candidate changes only page 5 plus the known diagnostic/formal overset
pages 46-49 and 55; no unrelated production page changed. All placed symbol
art remains linked to the AI-derived phase2 assets. The reference PDF is absent
from the production link inventory.
