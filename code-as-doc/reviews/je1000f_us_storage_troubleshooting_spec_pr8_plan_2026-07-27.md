# JE-1000F US PR8: storage, troubleshooting, and specification parity

## Scope

PR8 aligns the editable storage/troubleshooting and specification compositions
on physical pages 17-18, 35-36, and 53-54 with the supplied V2.0 reference. It
starts from merged PR7 and preserves the frozen JE-1000F US review copy and the
pinned phase2 snapshot.

Production artwork remains limited to governed derivatives of the
operator-provided Illustrator master. The reference PDF is comparison-only and
must not become an IDML link, crop, or page image.

## Frozen PR7 baseline

| Page | Language / role | RGB MAD | Changed-pixel ratio |
| ---: | --- | ---: | ---: |
| 17 | EN storage + troubleshooting | 0.076268 | 0.209940 |
| 18 | EN specifications | 0.039568 | 0.124508 |
| 35 | FR storage + troubleshooting | 0.080437 | 0.219257 |
| 36 | FR specifications | 0.050765 | 0.150638 |
| 53 | ES storage + troubleshooting | 0.070886 | 0.207051 |
| 54 | ES specifications | 0.053673 | 0.157400 |
| **Six-page mean** |  | **0.061933** | **0.178132** |

Native preflight reports 58 pages, zero missing fonts, zero bad links, and only
the separately assigned Spanish warranty overset on page 55. Rebuilding the
same frozen bundle from merged `main` reproduces every six-page metric exactly.

## Discovery findings

### Storage / troubleshooting composition

- The car-charging CAUTION continuation begins too high. Its label baseline is
  12-17 pt above the reference, depending on language.
- The reference keeps the localized storage heading text in the PDF text layer,
  but EN and FR omit the dark heading plate. ES retains the normal dark plate.
  This is a render-only locale contract; frozen RST must not be rewritten.
- The troubleshooting heading itself is already vertically aligned to within
  0.01 pt in all three languages. Upstream continuation/storage corrections
  must therefore preserve that fixed anchor instead of pushing the table down.
- The troubleshooting table shell is close, but header wrapping and localized
  row budgets differ. EN must keep `Error Code` on one line. FR and ES finish
  about 4-5 pt too low and need locale-scoped native row calibration rather
  than a scaled or raster table.

### Specification composition

- Section heading baselines are exact in EN and within 2.3 pt in FR/ES, but the
  `●` text glyph renders much smaller than the reference's circular marker.
  The marker should be an editable/native vector primitive with independent
  geometry, not a bitmap or reference-PDF crop.
- The four rounded table shells are already structurally correct. Remaining
  differences are localized vertical rhythm, cell optical offsets, and note
  leading; no source-table values or specification schema changes are needed.
- The two specification notes are too tight, especially in FR/ES. The second
  note begins about 17-28 pt too early relative to the reference.
- Every generated folio is currently placed at the right edge. The approved
  reference alternates by logical folio: odd folios on the left, even folios on
  the right. The baseline is also about 3 pt too high. This is a global master
  defect, so the change must be verified across every numbered page, not only
  the six PR8 pages.

## Implementation phases

1. Add characterization tests for locale-scoped storage heading treatment,
   continuation top rhythm, troubleshooting header/row geometry, native spec
   markers, note rhythm, and alternating folios.
2. Add renderer-owned layout tokens and the smallest semantic markers required
   to express the approved EN/FR/ES differences without changing frozen copy.
3. Rebuild and natively finalize the full 58-page manual. Retain only changes
   that improve the six-page aggregate and do not regress accepted pages.
4. Run a whole-book raster regression because the folio correction is global.
   Page changes outside the six primary pages must be limited to folio pixels.
5. Package INDD, IDML, PDF, parity, preflight, provenance, and portable links
   as untracked PR8 review artifacts.

## Intended production surface

- `tools/idml/reference_story_flow.py`
- `tools/idml/prose_flow.py`
- `tools/idml/components/prose_table.py`
- `tools/idml/data_stories.py`
- `tools/idml/page_folio.py`
- PR8-scoped layout tokens in `data/layout_params.csv`
- Focused tests beside the affected renderers

## Non-goals

- No frozen `_review` RST, phase2 row, schema, dependency, public CLI,
  review-sync, warranty, App, back-cover, or image-source change.
- No page-55 warranty fix; it remains PR9.
- No reference-PDF crop, finished-page screenshot, or rasterized table.
- No generated `_build`, `output`, `reports`, or `tmp` artifact in the commit.

## Safety nets and acceptance

- Physical page count remains 58; fonts and links remain clean.
- Native preflight contains only the explicitly deferred page-55 warranty
  overset.
- Storage, troubleshooting, and specification copy remains editable and is not
  duplicated or lost.
- The six-page MAD and changed-pixel means both improve from the frozen PR7
  baseline.
- A full-book comparison shows no non-folio pixel changes outside pages 17-18,
  35-36, and 53-54.
- IDML audit finds no visible whole-page reference-PDF link.

```text
python -m ruff check build.py integrations tools tests scripts
python -m unittest tests.test_export_idml tests.test_idml_components
python -m unittest
python tools/check_reference_layout_pins.py
python tools/check_maintainability_guardrails.py
python tools/check_doc_link_integrity.py
python build.py check --config configs/config.us-en.yaml --model JE-1000F \
  --region US \
  --data-root /Users/pika/Documents/auto-manual2-pr2-visual-parity/data/phase2
```

## Implemented result

The retained native candidate keeps all 58 pages editable and improves both
six-page aggregate measures from the frozen PR7 baseline:

| Measure | PR7 baseline | PR8 retained | Improvement |
| --- | ---: | ---: | ---: |
| Mean RGB MAD | 0.061933 | 0.052142 | 15.8% |
| Mean changed-pixel ratio | 0.178132 | 0.164376 | 7.7% |

The troubleshooting table was not uniformly stretched. Native inspection
proved that the row rules already matched the reference after the locale host
shift; only the code and step-copy optical baselines needed row-scoped
calibration. The retained PDF places the EN/FR/ES F6, F7, F8, F9, and FE code
baselines at the same coordinates as the supplied reference, to two decimal
places. EN `Error Code` is kept on one line.

The specification marker is a separately styled text glyph, not artwork. The
FR and ES note baselines now match the reference exactly. Folios alternate at
the outer edge and sit 3 pt lower; a full-book raster comparison against the
PR7 PDF found no changed pixel outside folio regions on any non-scope page.

Native preflight remains at the planned PR8 boundary: 58 pages, zero missing
fonts, zero bad links, and the one deferred Spanish warranty overset on page
55. That overset is assigned to PR9.
