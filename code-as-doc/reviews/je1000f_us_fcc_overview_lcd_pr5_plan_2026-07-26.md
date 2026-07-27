# JE-1000F US PR5: FCC, inbox, overview, and LCD parity

## Scope

PR5 aligns the repeated FCC/inbox, editable product-overview, and two-page LCD
compositions on physical pages 6-9, 24-27, and 42-45 with the supplied V2.0
reference. It starts from the merged PR4 tree and preserves pages 1-5 plus the
target-local frozen review copy.

All production imagery must resolve from the operator-provided Illustrator
master or its governed AI-derived phase2 attachments. The reference PDF is
comparison-only and must not be linked, cropped, rasterized, or embedded as
production artwork.

## Frozen PR4 baseline

| Page | Composition | RGB MAD | Changed-pixel ratio |
| ---: | --- | ---: | ---: |
| 6 | EN FCC + inbox | 0.040031 | 0.134488 |
| 7 | EN overview | 0.015829 | 0.058730 |
| 8 | EN LCD first | 0.075715 | 0.231441 |
| 9 | EN LCD continuation | 0.072887 | 0.227211 |
| 24 | FR symbol tail + FCC + inbox | 0.054310 | 0.182497 |
| 25 | FR overview | 0.036821 | 0.108842 |
| 26 | FR LCD first | 0.081360 | 0.251452 |
| 27 | FR LCD continuation | 0.080622 | 0.256571 |
| 42 | ES symbol tail + FCC + inbox | 0.054333 | 0.182038 |
| 43 | ES overview | 0.043361 | 0.132311 |
| 44 | ES LCD first | 0.077440 | 0.241468 |
| 45 | ES LCD continuation | 0.083017 | 0.262214 |

## Revalidated findings

- FCC/inbox geometry is broadly aligned, but the FCC live-text composition,
  card artwork scale/label baselines, and localized symbol-overflow region
  still differ from the reference.
- The product-overview line art is already AI-derived and editable label copy
  is native. Residuals are concentrated in artwork frames, leader endpoints,
  label frame geometry, and text metrics; no finished overview PDF is allowed.
- LCD table shells and three-column gray fill are present. The 14.2 pt icon
  profile remains visibly larger than the reference, matching the operator's
  request for a further small reduction. Hero art, column widths, row metrics,
  and localized typography also require measured adjustment.
- The two known full-book oversets remain outside PR5: Spanish operation pages
  46-49 (PR6) and Spanish warranty page 55 (PR9).

## Implementation phases

1. Add characterization tests for FCC/inbox frame geometry, overview artwork
   and label frames, LCD governed icon size, column widths, row metrics, and
   per-language page profiles.
2. Tune FCC/inbox and overview through shared or language-scoped layout tokens
   while keeping all text editable and all links on AI-derived assets.
3. Reduce LCD icon size slightly, then tune hero, table, and language metrics
   against the 12 target pages without changing phase2 rows or frozen copy.
4. Rebuild from the current frozen review bundle and pinned phase2 snapshot,
   finalize in native InDesign, and retain only measured improvements.
5. Run the full validation ladder and a 58-page regression, then package INDD,
   IDML, PDF, parity, preflight, provenance, and portable links as untracked
   review artifacts.

## Intended production surface

- `tools/idml/page03.py` and the FCC/inbox components.
- `tools/idml/page_overview.py`.
- `tools/idml/components/lcdmode.py` and the LCD reference profile.
- `data/layout_params.csv`, the approved reference-layout contract, and their
  characterization/golden tests.

## Non-goals

- No frozen RST copy, phase2 source rows, schema, dependency, public CLI,
  review-sync, workflow, operation, charging, troubleshooting, specification,
  warranty, app, or back-cover changes.
- No finished-page screenshots or reference-PDF crops in production IDML.
- No generated `_build`, `_review`, `output`, `reports`, or `tmp` artifacts in
  the commit.

## Acceptance and verification

- Physical page count remains 58; PR5 target pages have zero overset, missing
  fonts, and bad links.
- The 12-page aggregate improves without regressing pages 1-5 or unrelated
  formal pages. The strict per-page parity threshold remains the PR10 gate.
- LCD icons are smaller than the PR4 14.2 pt profile and visually match the
  supplied reference while columns 1-3 retain the gray fill.
- The IDML audit reports live text, native tables/leaders, AI-derived image
  links only, and no visible whole-page reference-PDF link.
- Portable delivery reports zero missing links.

```text
python -m ruff check build.py integrations tools tests scripts
python -m unittest <targeted PR5 tests>
python -m unittest
python tools/check_maintainability_guardrails.py
python tools/check_doc_link_integrity.py
python build.py check --config configs/config.us-en.yaml --model JE-1000F \
  --region US \
  --data-root /Users/pika/Documents/auto-manual2-pr2-visual-parity/data/phase2
```

## Accepted implementation result

- The approved LCD icon profile is 13 pt for English, French, and Spanish,
  reduced from the PR4 14.2 pt baseline. The first three table columns retain
  `HB Bg K05`; label and description text remain native and editable.
- LCD column, hero, hyphenation, and continuation offsets are language-scoped.
  The Spanish continuation table uses its own optical left offset instead of
  moving the shared table shell.
- Inbox imagery remains linked to the governed AI-derived assets. Per-card
  image-to-label spacing and content optical offsets move the three assets up
  without changing the frozen labels or replacing the card with flattened art.
- Product-overview line art, label frames, and all 16 leader paths remain
  native; their characterized reference geometry did not require a measured
  production change in this PR.

### Focused parity result

| Page | PR4 MAD | PR5 MAD | PR4 changed | PR5 changed |
| ---: | ---: | ---: | ---: | ---: |
| 6 | 0.040031 | 0.038546 | 0.134488 | 0.130738 |
| 7 | 0.015829 | 0.015829 | 0.058730 | 0.058730 |
| 8 | 0.075715 | 0.073699 | 0.231441 | 0.227070 |
| 9 | 0.072887 | 0.067810 | 0.227211 | 0.222261 |
| 24 | 0.054310 | 0.052745 | 0.182497 | 0.178592 |
| 25 | 0.036821 | 0.036821 | 0.108842 | 0.108842 |
| 26 | 0.081360 | 0.081262 | 0.251452 | 0.251332 |
| 27 | 0.080622 | 0.079627 | 0.256571 | 0.254471 |
| 42 | 0.054333 | 0.053594 | 0.182038 | 0.180496 |
| 43 | 0.043361 | 0.043361 | 0.132311 | 0.132311 |
| 44 | 0.077440 | 0.077007 | 0.241468 | 0.240409 |
| 45 | 0.083017 | 0.082140 | 0.262214 | 0.260341 |
| **Mean** | **0.059644** | **0.058537** | **0.189105** | **0.187133** |

The native preflight remains 58 pages with zero missing fonts and zero bad
links. The only overset stories are the previously deferred Spanish operation
story on pages 46-49 (PR6) and Spanish warranty story on page 55 (PR9).
