# JE-1000F US PR3: global page and type metrics

## Scope

PR3 aligns physical PDF pages 1-3 with the supplied V2.0 reference while
preserving the 58-page editable InDesign document inherited from PR2.

- Page 1: cover regression lock only; no production change.
- Page 2: preface line composition and language-block vertical metrics.
- Page 3: TOC typography, native editable leaders, and measured geometry.

The supplied Illustrator master is the only permitted source for placed image
assets. The reference PDF is comparison-only and must not be linked, cropped,
rasterized, or otherwise reused as production artwork. PR3 does not introduce
new placed images.

## Baseline evidence

The PR2 production PDF was compared with the supplied reference at 300 dpi
using the governed blur and changed-channel thresholds. The report is kept as
an untracked review artifact at `output/pr3/baseline/pages_1_3.json`.

| Physical page | RGB MAD | Changed-pixel ratio | Result |
| --- | ---: | ---: | --- |
| 1 | 0.000027 | 0.000014 | pass |
| 2 | 0.010744 | 0.038435 | fail: MAD |
| 3 | 0.010566 | 0.045059 | fail: MAD and changed ratio |

Inspection findings:

- Page 1 is already effectively identical and is a non-regression sentinel.
- Page 2 frame position, 7 pt Gilroy Regular body type, and 10.003 pt baseline
  rhythm are already aligned. The residual is concentrated in paragraph
  composition and several language-tag baselines.
- Page 3 title, language bars, columns, and folios are close to the reference.
  The largest systematic residual is the TOC leader treatment: the current
  exporter emits text periods through a tab leader, while the reference uses a
  non-text visual leader. PR3 will emit editable native InDesign vector leaders
  and keep titles/folios as live text.

## Implementation plan

1. Add characterization tests that pin page-specific preface composition,
   vector rather than text-period TOC leaders, and a no-cover-change contract.
2. Scope InDesign's single-line composer to the dedicated preface body
   paragraph style so other pages and shared typography do not move.
3. Replace TOC text-period tab leaders with editable native vector line
   objects, using measured row geometry and no placed or raster artwork.
4. Rebuild from the same frozen JE-1000F US review bundle used by PR2, finalize
   with Adobe InDesign 2026 21.0.1.6, and compare physical pages 1-3.
5. Run a full 58-page visual regression before packaging INDD, IDML, PDF,
   preflight report, parity report, and ZIP.

## Non-goals

- No content-copy changes, phase2 schema edits, dependency changes, or public
  CLI changes.
- No tuning of page groups assigned to PR4-PR9.
- No use of the reference PDF as production art.
- No cleanup of existing untracked `output/`, `tmp/`, or release artifacts.

## Safety nets and acceptance

- Physical page count remains 58.
- InDesign preflight reports zero overset stories, missing fonts, and bad links.
- Page 1 remains within RGB MAD 0.008 and changed-pixel ratio 0.040.
- Pages 2-3 each reach RGB MAD at most 0.008 and changed-pixel ratio at most
  0.040.
- The full-book regression does not worsen any page that passed before PR3.
- IDML editability audit contains no visible whole-page reference-PDF link.
- All placed image assets continue to resolve to the supplied AI-derived set.

Verification ladder:

```text
python -m ruff check build.py integrations tools tests scripts
python -m unittest tests.test_idml_preface_parity tests.test_idml_visual_parity
python -m unittest
python tools/check_maintainability_guardrails.py
python tools/check_doc_link_integrity.py
python build.py check --config configs/config.us-en.yaml --model JE-1000F --region US \
  --data-root /Users/pika/Documents/auto-manual2-pr2-visual-parity/data/phase2
```

Production proof then adds native InDesign finalization, the page 1-3 parity
report, the full 58-page regression report, and package hash inventory.

## Completion record

- The preface body now uses InDesign's `HL Single` composer only for the
  dedicated preface paragraph style. Physical page 2 improved from RGB MAD
  `0.010744` / changed ratio `0.038435` to `0.006528` / `0.023213`.
- The TOC uses 39 editable native dashed `GraphicLine` objects with measured
  reference geometry; entry text and folios remain live text. Physical page 3
  improved from `0.010566` / `0.045059` to `0.006511` / `0.028905`.
- Physical page 1 remains at `0.000027` / `0.000014`.
- Native finalization on Adobe InDesign 2026 21.0.1.6 produced 58 pages with
  zero overset stories, missing fonts, and bad links.
- Full 58-page comparison shows only pages 2 and 3 changed from the PR2
  baseline; both improved. Pages 4-58 have identical governed visual metrics,
  and the previously passing page 1 did not regress. Their remaining deltas
  stay assigned to PR4-PR10.
- The editability audit passes and reports no forbidden visible whole-page
  reference-PDF link. PR3 adds no placed image asset.
- The portable IDML package contains all 68 linked assets under `Links/`, uses
  relative link URIs, reports zero missing links, and passes ZIP integrity
  validation.
