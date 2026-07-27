# JE-1000F US PR9: warranty parity and zero overset

## Scope

PR9 aligns the editable English, French, and Spanish warranty compositions on
physical pages 19, 37, and 55 with the supplied V2.0 reference. It starts from
merged PR8, preserves the frozen JE-1000F US review copy, and uses the pinned
phase2 snapshot.

Production artwork remains limited to governed derivatives of the
operator-provided Illustrator master. The supplied PDF is comparison-only and
must not become an IDML link, crop, or page image.

## Frozen PR8 baseline

The merged-main `review-asis` rebuild emits 58 physical pages and 600 stories.
Native InDesign 2026 preflight reports zero missing fonts, zero bad links, and
one overset story: the Spanish warranty composition in the text frame labelled
`hb:page=55;frame=246`.

| Page | Language | RGB MAD | Changed-pixel ratio |
| ---: | --- | ---: | ---: |
| 19 | EN | 0.064892 | 0.197410 |
| 37 | FR | 0.064611 | 0.206317 |
| 55 | ES | 0.077581 | 0.237678 |
| **Mean** |  | **0.069028** | **0.213802** |

## Discovery findings

- The bottom-frame allowance is selected by the visible English heading text
  `WARRANTY`. The same approved composition is not recognized when its frozen
  heading is `GARANTIE` or `GARANTÍA`, so the Spanish final interpretation
  panel cannot enter the page-55 story frame.
- Warranty identity and locale already exist in the approved reference plan.
  The fix must use that structural identity instead of translating or matching
  visible copy.
- The first two Spanish panels match the reference vertically. The Spanish
  repair/replacement panel is 6.01 pt too tall; every later panel is displaced
  by the same 6.00 pt. The final interpretation panel is therefore both
  displaced and indivisibly overset.
- French panel geometry is displaced by 0.40 pt after a lead panel that is
  0.40 pt taller than the approved reference.
- English section geometry is already aligned. Its interpretation panel is
  1.82 pt too short, while the H1 alone begins 1.92 pt too high; the lead starts
  at the correct reference coordinate.
- The approved warranty shell is locale-positioned. Relative to the current
  output, EN panel hosts move 0.32 pt left and FR/ES panel hosts move 2.02 pt
  left. Panel width reduces by 1.41 pt, while the H1 uses its own 0.18 pt width
  correction and a 0.87 pt inline inset.

## Implementation phases

1. Add characterization tests proving that all three approved warranty
   compositions receive the governed bottom allowance and locale geometry.
2. Resolve warranty identity from the approved composition/stem and apply
   renderer-owned, locale-scoped host and component measurements.
3. Rebuild and natively finalize all 58 pages. Retain only measurements that
   remove the Spanish overset and improve the three-page aggregate without
   changing frozen copy.
4. Compare the whole book against the PR8 PDF and require zero changed pixels
   outside physical pages 19, 37, and 55.
5. Package INDD, IDML, PDF, parity, preflight, provenance, and portable links
   as untracked PR9 review artifacts.

## Intended production surface

- `tools/idml/reference_story_flow.py`
- `tools/idml/stories.py`
- `tools/idml/components/warranty.py`
- `tools/idml/page_objects.py`
- PR9-scoped layout tokens in `data/layout_params.csv`
- focused tests beside the affected renderers

## Non-goals

- No frozen `_review` RST, phase2 row, schema, dependency, public CLI,
  review-sync, App, back-cover, or image-source change.
- No reference-PDF crop, finished-page screenshot, or rasterized warranty
  panel.
- No generated `_build`, `output`, `reports`, or `tmp` artifact in the commit.

## Safety nets and acceptance

- Physical page count remains 58 with zero overset stories, zero missing
  fonts, and zero bad links.
- All warranty copy remains present, editable, and byte-identical at the frozen
  RST source layer.
- The three-page RGB MAD and changed-pixel means both improve from the frozen
  PR8 baseline.
- Whole-book raster comparison shows no changed pixel outside pages 19, 37,
  and 55.
- IDML audit finds no visible whole-page reference-PDF link.

```text
python -m ruff check build.py integrations tools tests scripts
python -m unittest tests.test_reference_story_flow tests.test_idml_components
python -m unittest
python tools/check_reference_layout_pins.py
python tools/check_maintainability_guardrails.py
python tools/check_doc_link_integrity.py
python build.py check --config configs/config.us-en.yaml --model JE-1000F \
  --region US \
  --data-root /Users/pika/Documents/auto-manual2-pr2-visual-parity/data/phase2
```

## Implemented result

The retained candidate keeps all 58 pages editable and removes the last native
story overflow. InDesign preflight reports zero overset stories, zero missing
fonts, and zero bad links.

All three warranty shell geometries now derive from the approved composition
identity instead of the visible English heading. The EN, FR, and ES panel
outlines match the supplied PDF to approximately 0.01 pt; the Spanish final
interpretation panel is present on page 55 with the complete frozen copy.

| Measure | PR8 baseline | PR9 retained | Improvement |
| --- | ---: | ---: | ---: |
| Mean RGB MAD | 0.069028 | 0.061985 | 10.2% |
| Mean changed-pixel ratio | 0.213802 | 0.194998 | 8.8% |

A 58-page raster regression against the merged PR8 review PDF found changed
pixels only on physical pages 19, 37, and 55. No App, back-cover, frozen RST,
or production-art asset changed in PR9.
