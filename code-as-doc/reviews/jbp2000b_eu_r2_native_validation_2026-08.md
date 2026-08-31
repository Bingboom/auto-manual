# JBP-2000B EU R2 native IDML validation (2026-08)

## Decision and scope

R2 onboards `JBP-2000B_EU` as the second target of the existing `BP@INTL`
skeleton. The target is EU six-language `en/fr/es/de/it/uk`; `uk` means
Ukrainian and does not claim the UK market. The approved source authority is
the 54-page EU master, material `16-0102-000400`.

The paired host hardware is the same product sold under region-specific names:

- EU: `Jackery Explorer 2000 Plus`;
- US: `Jackery HomePower 2000 Plus`.

Those names are target substitutions in `config.bp-eu.yaml` and
`config.bp-us.yaml`. No renderer or page composer selects a name from model,
region, localized title, filename, or physical page number.

This change writes no live Feishu source-table or asset-table record. The
committed fixture rows are deterministic R2 build inputs; production-table
promotion remains a separately gated operation.

## Reuse proof

The EU target adds target assembly data, not a copied page renderer:

| Layer | R2 binding | Reused authority |
| --- | --- | --- |
| Skeleton | `region_profiles/eu.yaml` + resolved `manual_bp-eu.yaml` | `skeletons/bp-intl/blueprint.yaml` and `slot_templates.yaml` |
| Target | `configs/config.bp-eu.yaml` | existing target/config resolution and queue matching |
| Physical assembly | `jbp2000b_eu_v1_candidate.json` | registered composition types and shared page composers |
| Layout capacity | additive `layout_params.idml-compact.csv` rows | shared component geometry and character-metric adapters |
| Assets | EU-scoped asset overrides | shared asset resolver and registry |
| Content | six-language fixture rows and the EU terminal carrier | existing BP recipes, templates and `regulatory_compliance` slot |

The 54 physical pages consume 76 source pages through these registered
composition types: `front_cover`, `preface`, `toc`, `safety_symbols`,
`inbox_overview`, `lcd_operations`, `connections`, `troubleshooting`,
`charging`, `storage_specifications`, `warranty`, and
`regulatory_compliance`. The plan remains `status=candidate` and
`production_eligible=false`; R2 evidence does not perform approved
reference-layout promotion.

Two shared defects were exposed by the real six-language native pass and fixed
at their owners:

1. nested signal-badge table cells were invisible to the finalizer's old
   top-level table scan; the finalizer now reports nested-cell overset and
   fails before PDF export;
2. `☎ / ✉ / ◉` inherited Gilroy on the regulatory contact row; their source
   codepoints now use the already bundled `Noto Sans Symbols2` fallback.

German, Italian and Ukrainian signal labels use data-driven width reserves.
The final visual pass additionally found Italian `SUGGERIMENTO` hyphenating
inside the fixed badge; an Italian capacity row and atomic-label setting keep
it on one line without changing the shared badge geometry.

## Build evidence

Command:

```bash
python3 build.py idml \
  --config configs/config.bp-eu.yaml \
  --model JBP-2000B \
  --region EU \
  --data-root tests/fixtures/phase2
```

Result:

| Gate | Result |
| --- | --- |
| Physical pages | `54` |
| Source bindings | `76/76` (`100%`) |
| Manual IR blocks | `455` |
| Skipped raw blocks | `0` |
| IDML stories / spreads | `530 / 54` before native import |
| Candidate-plan SHA-256 | `0a5ca273a27a13fd8e1f6f3ebeaab693f05b65b54f34fbcbbab6ccc97910361e` |
| Built IDML SHA-256 | `83cadb751a792379bb45722e6a40f083d78b80165b3348924ed483e8169af94a` |

## Native InDesign evidence

Command:

```bash
python3 tools/indesign_finalize.py \
  --idml docs/_build/JBP-2000B/EU/idml/manual_jbp2000b_eu.idml \
  --indd docs/_build/JBP-2000B/EU/idml/manual_jbp2000b_eu_r10.indd \
  --pdf docs/_build/JBP-2000B/EU/idml/manual_jbp2000b_eu_r10.pdf \
  --report docs/_build/JBP-2000B/EU/idml/finalize_report_r10.json
```

The native toolchain was `Adobe InDesign 2026 21.0.1.6`, matching the
committed pin. The saved/reopened INDD and exported PDF reported:

| Native gate | Result |
| --- | --- |
| Pages | `54` |
| Overset stories / nested table cells | `0 / 0` |
| Missing fonts / glyphs / bad links | `0 / 0 / 0` |
| PDF glyph validation | `pass`, `finding_count=0` |
| PDF standard | `PDF/X-4` |
| Output intent / condition | `Japan Color 2001 Coated / JC200103` |
| INDD SHA-256 | `fbe66593d6912192ed97f09e585f7649bb16b55ce5d458cdb6777da9f803ef5b` |
| PDF SHA-256 | `8b7f02da46df79ff3385c8faa10a611a78551ab88e547956af4278ccbe541e2e` |
| Finalize-report SHA-256 | `162d984347566a910f71b8650efbdd307f30981493e678202ae5b20947de532b` |

`docs/_build/**` remains generated and is excluded from the commit.

## Visual review

The r10 PDF was rendered at 180 dpi. Focus pages were selected from the defects
found during native import and the EU source delta:

| Physical page | Review focus | Result |
| ---: | --- | --- |
| 30 | German Safety + Symbols | signal labels, rows and rounded shells fit |
| 38 | Italian Safety + Symbols | `SUGGERIMENTO` is one line; no inserted hyphen |
| 46 | Ukrainian Safety + Symbols | Cyrillic title and signal badges are intact |
| 51 | EU charging | artwork names `Explorer 2000 Plus` and uses the EU wall plug |
| 54 | EU regulatory terminal | `☎ / ✉ / ◉`, CE, QR and live contact copy are visible |

No visible clipping, `.notdef` boxes, broken tables, black squares, or missing
links were found in those pages. This is R2 candidate/native acceptance; it is
not the separate candidate-to-approved-reference promotion decision.

All six Troubleshooting pages were also reviewed at 180 dpi: EN 10, FR 18,
ES 26, DE 34, IT 42, and UK 50. Each page preserves the shared rounded-table
composition, row heights, readable copy, and complete lower boundary. No
language-specific page branch or troubleshooting renderer override was added.

The eleven reviewed r10 page rasters (the six Troubleshooting pages plus
30/38/46/51/54) are byte-identical to the already inspected r9 rasters. The
r10 identity change comes from removing an EU-only default token from the
globally pinned base layout table; it does not change visible composition.
