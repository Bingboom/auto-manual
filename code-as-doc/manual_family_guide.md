# Manual Family Guide

Updated: 2026-03-30

This file documents the current family-level differences between the active JP and US manual families.
It is the current boundary document for family-specific rules.
It is not the future canonical data model.

For the future canonical content schema direction, see [`architecture/Content_Data_Model.md`](architecture/Content_Data_Model.md).

## 1. Current Scope

The current repo maintains two active manual families:

- `JP`
- `US`

Current language sets:

- `JP`: `ja`
- `US`: `en`, `fr`, `es`

Current phase rule:

- keep the family boundary explicit
- do not collapse JP / US into one generic family

## 2. Family Difference Matrix

The current confirmed differences are:

| Area | JP | US |
|------|----|----|
| Supported languages | `ja` | `en`, `fr`, `es` |
| Spec data source | JP family spec sheet | US family spec sheet |
| Certification content | JP family source | includes US-only items such as `FCC` where applicable |
| Unit convention | no US imperial mix by default | often contains imperial + metric together |
| `meaning_of_symbols` / stickers | family-specific | family-specific |

Interpretation rule:

- most of the reusable page structure may still be shared
- but `spec`, `certification`, `units`, and `meaning_of_symbols` must remain family-specific unless proven identical by the real source documents

## 3. What Must Stay Family-Specific

Until the future table-driven model is ready, treat these as explicit family-owned surfaces:

1. Spec data
   - [`data/phase2/Spec_Master.csv`](../data/phase2/Spec_Master.csv)
   - [`data/phase2/Spec_Footnotes.csv`](../data/phase2/Spec_Footnotes.csv)
   - [`data/phase2/spec_titles.csv`](../data/phase2/spec_titles.csv)

2. Certification and compliance wording
   - spec rows
   - footnotes
   - any certification note embedded in template text

3. Unit conventions
   - US may include imperial + metric together
   - JP should not inherit US-style imperial units by default

4. `meaning_of_symbols` and sticker-driven pages
   - each family may have a different symbol inventory
   - do not assume the US symbol page can be copied into JP unchanged

## 4. What Can Be Reused More Safely

These page types are better candidates for shared structure, snippet reuse, or generated-page recipes:

- operation guide
- app setup
- generic maintenance flow pages

`product overview` needs a stricter rule:

- its page structure can still be standardized through generated-page recipes
- but the rendered content is still family-specific because it includes port names, input/output ratings, button labels, and other spec-driven fields
- do not treat `product overview` as a plain shared prose page across JP / US

Even for reusable-structure pages:

- family-specific placeholders must still come from the correct family data
- do not hardcode family-specific spec or certification text into shared prose

## 5. Current Maintenance Rule

Current phase rule:

- use docs + config + manifest structure to document the family boundary now
- do not wait for the future multidimensional table to begin enforcing these differences

Operational rule:

- the active source families are JP and US
- when a family-specific source document changes, update that family's data and templates before treating the output as final
- within one family, keep the source-language template as the semantic structure owner for manually maintained parallel-language prose pages
- when that source-language page changes shared headings, section order, placeholders, includes, or `.. only::` model gates, update the derived-language family pages in the same change so the structure stays aligned across languages
- current example: if the US source `charging.rst` changes its JE-2000E battery-pack `.. only::` block, mirror the same gated block boundary in the ES and FR `charging.rst` pages
- JP currently has only `ja`, so there is no JP derived-language mirror step today

## 6. Future Table-Driven Direction

Planned direction:

- this family difference information should later move into a multidimensional table / structured data source
- the table should become the live maintenance surface for family/language coverage and family-specific content differences

Current constraint:

- only record the currently active and confirmed family rules

## 7. Maintainer Checklist

When changing a family template or family data set, ask:

- Is this difference truly family-specific?
- Is the source document for this family already available?
- Are we accidentally copying a US-only certification item such as `FCC` into JP?
- Are we accidentally carrying US imperial units into JP?
- Does `meaning_of_symbols` still match the current family sticker set?

## 8. One-Sentence Rule

JP and US share a build system, but they do not share one identical content contract.
