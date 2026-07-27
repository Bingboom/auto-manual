# JE-1000F US PR6: Spanish operation parity

## Scope

PR6 aligns the Spanish editable operation composition on physical pages 46-49
with the supplied V2.0 reference. It starts from the accepted PR5 tree and
preserves the frozen JE-1000F US review copy and pinned phase2 snapshot.

All production imagery must resolve from the operator-provided Illustrator
master or its governed AI-derived attachments. The reference PDF is
comparison-only and must not be linked, cropped, rasterized, or embedded as
production artwork.

## Frozen PR5 baseline

| Page | Composition | RGB MAD | Changed-pixel ratio |
| ---: | --- | ---: | ---: |
| 46 | ES operation 1 | 0.050030 | 0.163770 |
| 47 | ES operation 2 | 0.062219 | 0.186901 |
| 48 | ES operation 3 | 0.076357 | 0.286923 |
| 49 | ES operation 4 | 0.068247 | 0.203510 |

Native preflight reports one overset Spanish operation story spanning pages
46-49 and one separately deferred Spanish warranty story on page 55. Fonts and
links are otherwise clean and the document remains 58 pages.

## Revalidated findings

- The complete Spanish operation is one linked editable story across pages
  46-49. The final `COMBINACIONES DE TECLAS` heading is visible on page 49,
  but its governed editable panel remains overset.
- Page 49 has approximately 154 pt of visible space below the heading while
  the governed Spanish panel is 166.70 pt high. The approved operation story
  currently receives only the shared 18 pt invisible final-frame allowance.
- The shared allowance already fits English and French. A Spanish-only
  `lang_es_comp_operation_page_extra_height` token can deepen the final frame
  without changing EN/FR geometry, frozen copy, panel size, or page count.
- Page 48 still differs materially because the reference uses a gray prose
  panel. That component will be measured only after the overset is removed so
  flow and visual changes remain independently attributable.

## Implementation phases

1. Characterize language-scoped operation final-frame depth: Spanish must use
   its own token while English and French retain the shared value.
2. Add the Spanish token, regenerate derived TeX params, and refresh only the
   normalized layout-parameter hash in the approved reference-layout contract.
3. Export and finalize the complete 58-page IDML through native InDesign.
   Accept the structural change only if the Spanish operation overset is gone,
   the Key Combinations panel appears completely on page 49, and the deferred
   page-55 warranty overset is the only remaining story overflow.
4. Tune pages 46-49 against the supplied reference, including the page-48 gray
   prose panel and localized text rhythm. Keep every panel and text run native
   and editable, and retain only measured aggregate improvements.
5. Run the full validation ladder and package INDD, IDML, PDF, parity,
   preflight, provenance, and portable links as untracked review artifacts.

## Intended production surface

- `tools/idml/reference_story_flow.py`
- Spanish operation layout tokens in `data/layout_params.csv`
- Derived renderer params and the approved reference-layout source identity
- Focused characterization tests beside the affected IDML flow/component code

## Non-goals

- No frozen RST copy, phase2 rows, schema, dependency, public CLI, review-sync,
  English/French operation geometry, or image-source changes.
- No Spanish warranty fix; page 55 remains assigned to PR9.
- No reference-PDF crops, finished-page screenshots, or other non-AI source
  artwork in production IDML.
- No generated `_build`, `_review`, `output`, `reports`, or `tmp` artifacts in
  the commit.

## Safety nets and acceptance

- Physical page count remains 58; fonts and links remain clean.
- Native preflight contains no overset story on pages 46-49. Page 55 may remain
  as the single explicitly deferred warranty overset.
- The page-49 editable Key Combinations panel is fully on-page and does not
  overlap the footer or adjacent content.
- EN/FR operation final-frame allowances remain byte-for-byte characterized by
  the shared token; only ES reads the language-specific override.
- The four-page aggregate improves without regressing accepted pages 1-45.
- IDML audit finds only AI-master-derived production image links and no visible
  whole-page reference-PDF link.

```text
python -m ruff check build.py integrations tools tests scripts
python -m unittest tests.test_reference_story_flow
python -m unittest <other targeted PR6 tests>
python -m unittest
python tools/check_maintainability_guardrails.py
python tools/check_doc_link_integrity.py
python build.py check --config configs/config.us-en.yaml --model JE-1000F \
  --region US \
  --data-root /Users/pika/Documents/auto-manual2-pr2-visual-parity/data/phase2
```

## Accepted implementation result

- Spanish operation receives a 46 pt language-scoped final-frame allowance;
  English and French remain on the shared 18 pt contract. Native preflight no
  longer reports any overset container on pages 46-49.
- The Spanish combined Energy Saving guidance paragraph now enters the same
  editable gray operation-panel component used by the two-paragraph EN/FR
  structure. The copy is unchanged and its linked illustration remains the
  governed `operation/je1000f_us/energy_saving` asset derived from
  `source/manual_je1000f_us_master`.
- The Spanish Key Combinations heading and editable panel are raised 12 pt in
  total. Their governed panel height remains 166.70 pt; the panel clears the
  page number and matches the reference top/bottom geometry.
- A 58-page raster regression against the PR5 PDF found changes only on pages
  48 and 49. Pages 1-47 and 50-58 are pixel-identical at 72 dpi.

### Focused parity result

| Page | PR5 MAD | PR6 MAD | PR5 changed | PR6 changed |
| ---: | ---: | ---: | ---: | ---: |
| 46 | 0.050030 | 0.050030 | 0.163770 | 0.163770 |
| 47 | 0.062219 | 0.062219 | 0.186901 | 0.186901 |
| 48 | 0.076357 | 0.071744 | 0.286923 | 0.243770 |
| 49 | 0.068247 | 0.066389 | 0.203510 | 0.214382 |
| **Mean** | **0.064213** | **0.062596** | **0.210276** | **0.202206** |

The full 58-page mean improves from `0.059011 / 0.187755` to
`0.058899 / 0.187198` (MAD / changed-pixel ratio). Native preflight reports
58 pages, zero missing fonts, zero bad links, and only the explicitly deferred
Spanish warranty overset on page 55. The local InDesign host matches the
committed 21.0.1.6 pin; its PDF/X-4 preset still cancels at export, while the
High Quality Print review PDF exports successfully. This is the same local
PDF/X metadata limitation already recorded in PR4 and is not represented as a
clean PDF/X acceptance.
