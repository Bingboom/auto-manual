# Review bundle language-scope closeout

Date: 2026-09-06

## Discovery

The committed `JE-1000F/EU` review derivative was seeded when the family book
contained EN/FR/ES/DE/IT/UK. The current target registry explicitly narrows
`JE-1000F/EU` to EN/FR/ES/DE/IT, but an exact merged `review-asis` overlay
still replaces the freshly planned five-language index with the old six-
language review index. The inline preface trimmer removes the UK block from
the shared preface, but the sixteen standalone UK pages remain included.

The strict whole-document Overview parser exposes the stale page set at
`p81_03_product_overview_placeholder.rst`: the page is outside the current
five-language plan and therefore has no planner language binding. Treating it
as Italian would be incorrect; it is an explicitly declared UK page and must
not be part of this target.

## Implementation

1. Add a shared bundle-language page trimmer beside the existing inline block
   trimmer. It reads each included page's explicit `\HBApplyLang{...}` marker
   as the only page-language authority, removes only index includes outside the
   resolved target language scope, and leaves review page bytes untouched. A
   filename suffix alone never causes a page to be removed.
2. Run it only after a review overlay, before asset finalization. Unknown or
   genuinely multi-language pages remain included and are handled by the
   existing inline block trimmer. When that page also carries a fully
   recognized `English / French / ...` catalogue, trim the catalogue through
   the same resolved scope so it cannot advertise a removed language.
3. Characterize the real review shape with prefix-renamed pages: an Italian
   `p66_...` page remains while the old Ukrainian `p81_...` page leaves the
   bundle index.

## Non-goals

- No model, page-number, or translated-heading special case.
- No mutation of `docs/_review`, source tables, or the supplied PDF.
- No change to Web figure artwork or its approval hashes.
- No screenshot conversion of LCD, specifications, Warranty,
  Troubleshooting, or Symbols.

## Safety net and verification ladder

1. Focused language-page and review-overlay tests.
2. Ruff, full unit suite, maintainability guardrails, and documentation links.
3. Fresh five-language `build.py md --source review-asis` from the isolated EU
   review worktree; assert 76 fragments and no UK page.
4. Cold replay with source reads forbidden plus ComponentSpec/adapter coverage.
5. Desktop and 390 px Italian inspection: all eleven required Overview,
   Operation, and Charging slots must be `approved-composite`, with no visible
   fallback or horizontal overflow.
