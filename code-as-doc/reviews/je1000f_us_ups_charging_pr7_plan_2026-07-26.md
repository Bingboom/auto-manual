# JE-1000F US PR7: UPS and charging parity

## Scope

PR7 aligns the editable UPS and charging compositions on physical pages 14-16,
32-34, and 50-52 with the supplied V2.0 reference. It starts from the accepted
PR6 tree and preserves the frozen JE-1000F US review copy and pinned phase2
snapshot.

All production imagery must resolve from the operator-provided Illustrator
master or its governed AI-derived attachments. The reference PDF is
comparison-only and must not be linked, cropped, rasterized, or embedded as
production artwork.

## Frozen PR6 baseline

| Language | Pages | RGB MAD | Changed-pixel ratio |
| --- | --- | ---: | ---: |
| EN | 14-16 | 0.063096 | 0.205232 |
| FR | 32-34 | 0.065426 | 0.227906 |
| ES | 50-52 | 0.067399 | 0.232747 |

Native preflight reports 58 pages, zero missing fonts, zero bad links, and the
single separately deferred Spanish warranty overset on page 55.

## Revalidated findings

- On pages 15, 33, and 51, the AC connection sentence should be an editable
  caption inside the AC-wall illustration. It currently remains ordinary prose
  above the illustration and displaces all following charging content.
- The approved flow first promotes reference figures and only then moves the
  charging tail into the `08_charging_methods` composition. At promotion time
  the AC body/image pair still has the `charging` stem, so the canonical
  charging-methods route does not recognize it.
- App and ordinary image promotion already depend on distinct structural and
  page-plan contracts. The fix must characterize those boundaries and avoid a
  broad second promotion pass over every composition.
- The car-charge section on pages 16, 34, and 52 is currently too early and too
  short, but part of that displacement may be downstream of the missing AC
  composite. Its governed container and art placement will be measured again
  only after the flow-order defect is fixed.

## Implementation phases

1. Characterize the production `ProseFlowBuffer` path: after the approved flow
   split, the moved AC body/image pair must become one `charging_ac` component;
   App and unrelated ordinary images must remain single-promoted or untouched.
2. Apply the smallest ordering change that promotes the charging-methods tail
   after it reaches its canonical composition, while retaining the established
   App alignment/promotion behavior.
3. Export and natively finalize the full 58-page document. Confirm that the AC
   caption is inside the figure on all three localized charging compositions
   and that only the deferred page-55 warranty story remains overset.
4. Remeasure the car-charge panels. Add component-scoped, parameter-governed
   container/placement geometry only if it improves all three languages while
   preserving the AI-derived linked art and editable Vehicle/note copy.
5. Retain only changes that improve the nine-page aggregate, then run the full
   validation ladder and package INDD, IDML, PDF, parity, preflight, provenance,
   and portable links as untracked review artifacts.

## Intended production surface

- `tools/idml/prose_flow.py`
- `tools/idml/components/reference_figure.py` only if measured car geometry
  requires component-level placement tokens
- Charging component layout tokens in `data/layout_params.csv` only if required
- Focused characterization tests beside the affected IDML flow/component code

## Non-goals

- No frozen RST copy, phase2 rows, schema, dependency, public CLI, review-sync,
  storage, troubleshooting, specification, warranty, App, or image-source
  changes.
- No page-55 warranty fix; it remains assigned to PR9.
- No reference-PDF crops, finished-page screenshots, or other non-AI source
  artwork in production IDML.
- No generated `_build`, `_review`, `output`, `reports`, or `tmp` artifacts in
  the commit.

## Safety nets and acceptance

- Physical page count remains 58; fonts and links remain clean.
- Native preflight contains only the explicitly deferred page-55 warranty
  overset.
- The AC sentence is editable and lives inside the governed AC figure on pages
  15, 33, and 51, with no duplicate prose copy above it.
- App reference figures are not promoted twice, and ordinary non-reference
  images remain ordinary images.
- The nine-page aggregate improves without changing accepted pages outside the
  scoped compositions.
- IDML audit finds only AI-master-derived production image links and no visible
  whole-page reference-PDF link.

```text
python -m ruff check build.py integrations tools tests scripts
python -m unittest tests.test_export_idml
python -m unittest tests.test_idml_reference_figure
python -m unittest
python tools/check_maintainability_guardrails.py
python tools/check_doc_link_integrity.py
python build.py check --config configs/config.us-en.yaml --model JE-1000F \
  --region US \
  --data-root /Users/pika/Documents/auto-manual2-pr2-visual-parity/data/phase2
```

## Accepted implementation result

- The approved split now re-runs canonical charging-methods promotion only
  after the AC tail reaches its target composition. EN, FR, and ES all render
  the localized AC sentence as one unlocked caption inside the governed
  illustration; App and ordinary solar images remain unaffected.
- The frozen French image-then-caption order and the Spanish RST underline
  residue are normalized structurally in the renderer. No frozen review RST or
  phase2 copy changed.
- The car heading, body-to-figure rhythm, and 134 pt editable panel are governed
  per language. The AI-derived art remains proportional and bottom-aligned;
  its Vehicle and cable-note overlays remain independent unlocked top layers.
- The English UPS-to-CHARGING rhythm and the three localized methods-frame top
  offsets now match the supplied reference measurements.

### Focused parity result

| Language | Pages | PR6 MAD | PR7 MAD | PR6 changed | PR7 changed |
| --- | --- | ---: | ---: | ---: | ---: |
| EN | 14-16 | 0.063096 | 0.057943 | 0.205232 | 0.199465 |
| FR | 32-34 | 0.065426 | 0.062536 | 0.227906 | 0.214480 |
| ES | 50-52 | 0.067399 | 0.064113 | 0.232747 | 0.217325 |
| **Nine-page mean** | **14-16, 32-34, 50-52** | **0.065307** | **0.061531** | **0.221961** | **0.210423** |

The full 58-page mean improves from `0.058899 / 0.187198` to
`0.058313 / 0.185408` (MAD / changed-pixel ratio). A PR6-to-PR7 72 dpi raster
regression finds changes only on physical pages 14-16, 33-34, and 51-52.
Native preflight remains 58 pages, zero missing fonts, zero bad links, and only
the explicitly deferred Spanish warranty overset on page 55. The local host
matches InDesign 21.0.1.6; High Quality Print exports successfully, while its
existing PDF/X-4 metadata limitation remains outside this PR's acceptance.
