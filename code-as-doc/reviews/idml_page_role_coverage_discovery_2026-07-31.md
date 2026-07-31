# IDML Page-Role Coverage Discovery — 2026-07-31

## Scope

Workstream W / Stage 4a item 14 replaces implicit source-file routing in the
production IDML assembler with one explicit, target-neutral page-role table.
It also adds a warning when a source page reaches the ordinary prose fallback
without an explicit role.

## Current state

`tools/export_idml.py` currently decides assembly behavior inside the main
page loop with independent filename tests:

- generated data pages use `startswith` checks for `spec_`, `lcd_icons_`, and
  `troubleshooting_`;
- product overview, FCC, inbox, maintenance, symbols, warranty, and safety use
  separate `stem_has`, substring, or prefix checks;
- every page that misses those tests silently enters the ordinary prose path.

The routing is therefore correct for today's filenames but has no single
inventory that a new source page can be checked against. A renamed or newly
introduced special page can still produce valid IDML while losing its intended
composition.

The current template/review inventory uses these semantic identities:

- preface, TOC, FCC, maintenance, symbols, inbox, overview;
- operation guide, UPS, extra battery, charging, charging methods, storage;
- troubleshooting, warranty, App setup, specification, LCD, safety, cover,
  and back cover;
- merged-language physical prefixes such as `p20_` do not change the semantic
  identity.

## Safety net

Before changing the assembler:

1. pin all known semantic stems and localized/generated filename families to
   explicit roles;
2. pin merged-language numeric prefixes to the same role;
3. pin unknown pages to an `unclassified_prose` fallback plus one stable
   assembly-coverage warning;
4. pin the existing end-to-end fixture to zero coverage warnings; and
5. pin an arbitrary new prose page to successful output with a warning rather
   than a build failure.

## Implementation plan

1. Add a focused `tools/idml/page_roles.py` module containing the ordered role
   table, canonical-stem normalization, classification, and warning rendering.
2. Classify each projected page once in `tools/export_idml.py` and replace its
   duplicated filename predicates with semantic role comparisons.
3. Preserve the existing placed-PDF check and all pending cross-page assembly
   behavior; the role table selects the same branches but does not render.
4. Emit one deterministic `[export-idml] WARNING: assembly coverage ...` line
   listing unclassified source refs after the page walk.
5. Document the onboarding signal and add the completion record to the scaling
   plan and optimization log.

## Non-goals

- No source-content, approved-layout, page-binding, composition, asset, or
  geometry change.
- No new model, region, or language predicate.
- No public CLI flag or fail-closed policy change; an unclassified page warns
  and keeps the historical ordinary-prose fallback.
- No long-form block-assembly relaunch and no change to the rolled-back
  `assembly_pilot` design.
- No release-manifest layout signals; that is Stage 4a item 15.
- No ExtendScript batch-loop work; Stage 4a item 12 remains design-Mac gated.
