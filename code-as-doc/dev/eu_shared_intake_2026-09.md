# EU authored-table and projected-page intake

Status: active; local implementation, not merged or published.

## Scope

JBP-2000B EU en/de/es/fr/it now passes the assembly plan's `symbols` role into
shared component discovery even when the slot renames the page. The existing
JBP EU warranty selector covers all projected language names. The lead adapter
preserves an ordered paragraph prefix plus the final local note; French has
three lead paragraphs. Interleaved or unsupported root blocks are rejected.

JE-100C, JE-300D and JE-500A English have 28 declared tables: 13 specifications,
three signal-word tables, two troubleshooting tables, and ten text references
(LCD legends/actions and icon-free symbol explanations). The first groups reuse
existing components. `HB-TABLE-REFERENCE` provides four explicit geometry
variants for the last group without relaxing the icon-catalog asset contract.
Blank/repeated LCD callout numbers and rich cell contents are source-owned.
JE-300D's five multi-port combination tables remain separate definition debt.

The new style entry is additive: all 33 existing style definitions and all
layout tokens remain unchanged. Non-Web adapters for text references are
semantic projections only. See [style definition](../../docs/renderers/contracts/STYLE_DEFINITION.md#authored-text-references-hb-table-reference).

## Validation and current acceptance boundary

- 29 focused tests pass, including real RST sources, blank numbers, malformed
  geometry, duplicate semantic roles, replay tampering and renamed CSV slots.
- All eight target `build.py md` and `build.py check` runs pass with isolated
  staging roots and frozen source data.
- All 16 baseline/final strict Sphinx builds pass.
- Browser checks pass 116 component/viewport cases across 16 navigations;
  no broken images or page-level horizontal overflow.
- All eight relocated IR packages replay exactly without source RST/CSV or
  current-contract reads; packaged image tampering is rejected.
- All eight image-byte inventories are unchanged. Rendered word inventories
  differ only by explicitly recorded Sphinx smartquotes versus source quotes
  and decorative warning badge markup. Do not describe this as exact rendered
  text parity. Table-cell preservation is tested against authored sources.

The final full suite passes: 4,869 tests, zero failures/errors and 22 skips.
Five host-local PDF/AI fixture constants were relocated in-process to the
hash-verified original files; no test logic was skipped or changed by that
wrapper. The ordinary US reference check also passes against the existing
frozen source snapshot.

The reference-layout update changes only the style hash for the additive
definition; existing content, geometry, layout and snapshot pins are untouched.
JE-300D retains eleven rows and its repeated callout number 8. All style
inventories include the new 34th definition. The warranty parser complexity
baseline is tightened from 21 to 16.

Phase 1 and this change both touch the shared dispatcher. Composed validation
must preserve phase 1's carrier-aware key-combination/LCD rendering while
adding the reference-table renderer; choosing one side of that merge conflict
would discard the other fix. A separately composed checkout passes the 19
combined operation/authored/warranty/table tests. No merge or publication is
included in this phase's current acceptance.

## Remaining rollout

This phase does not resolve every item in the 61-manual audit. The independent
13-table LCD source audit, remaining ordinary tables, short-form warranties and
27 historical App chapters retain their own acceptance boundaries. Existing
approved numbering and artwork must not be replaced by live row indexes or
unreviewed icons. Phase 3 will extend admission to prepared RST/projection
packages using explicit chapter/capability rules and visible legacy debt;
native-import-only PR #1339 does not provide that coverage.
