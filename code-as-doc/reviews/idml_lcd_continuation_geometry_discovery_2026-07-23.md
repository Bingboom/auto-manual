# IDML LCD Continuation Geometry Discovery - 2026-07-23

## Scope

This phase targets the approved JE-1000F US V2.0 LCD continuation table on
physical pages 9, 27, and 45. It does not change source copy, source row
identifiers, the 7+19 page split, visual-parity thresholds, or unrelated page
families.

## Evidence

Geometry17 passes native InDesign preflight but the LCD continuation pages are
the highest reusable page-family delta:

| Page | Language | RGB MAD | Changed-pixel ratio |
| ---: | --- | ---: | ---: |
| 9 | English | 0.092261 | 0.272851 |
| 27 | French | 0.102713 | 0.306455 |
| 45 | Spanish | 0.106020 | 0.312708 |

The approved PDF uses one 467.631 pt table shell for all three languages, but
distributes that height differently across the 19 semantic rows. The current
IDML renderer lets InDesign derive every row height from localized copy and a
shared icon frame. That makes the first seven continuation rows nearly uniform
and moves every downstream grid line away from the approved master even when
the final shell height happens to be close.

Measured approved outer geometry:

| Language | Left | Top | Width | Height |
| --- | ---: | ---: | ---: | ---: |
| English | 28.901 pt | 29.100 pt | 312.442 pt | 467.631 pt |
| French | 28.416 pt | 28.037 pt | 312.442 pt | 467.631 pt |
| Spanish | 26.435 pt | 28.275 pt | 312.442 pt | 467.631 pt |

## Root cause

`HB-TABLE-LCD-ICON` owns typography, padding, columns, and outer panels, but its
contract explicitly leaves row heights as InDesign-native. A global padding or
leading adjustment cannot reproduce the approved grid because different
semantic rows need different localized heights while the total panel height
stays fixed.

## Implementation plan

1. Extend the approved LCD presentation profile with optional positive
   `row_height_pt_by_language` values keyed by stable source row identifier.
2. Project only the selected language's height into the render row; source data
   remains unchanged.
3. Add generic optional fixed-row support to component-table primitives.
4. Fail closed if a continuation segment mixes governed and ungoverned rows.
5. Resolve continuation left/top placement through base plus locale tokens.
6. Verify with targeted tests, a clean-bundle IDML export, native InDesign
   preflight, page PNG inspection, and strict PDF parity.

## Safety net

- The approved profile validator rejects unknown language keys, booleans,
  non-finite values, and non-positive heights.
- Existing bundles without row-height metadata preserve auto-growing rows.
- Exact row heights apply only when the approved profile supplies a complete
  segment.
- Golden IDML fixtures must remain unchanged unless they opt into the profile.
- The phase is retained only if all three LCD continuation pages improve and
  native preflight remains at zero overset, missing fonts, and bad links.
