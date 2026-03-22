# Manual Family Guide

Updated: 2026-03-22

This file documents the current family-level differences between the active JP, US, and EU manual families.
It is the current boundary document for family-specific rules.
It is not the future canonical data model.

For the future canonical content schema direction, see [`architecture/Content_Data_Model.md`](architecture/Content_Data_Model.md).

## 1. Current Scope

The current repo maintains three active manual families:

- `JP`
- `US`
- `EU`

Current language sets:

- `JP`: `ja`
- `US`: `en`, `fr`, `es`
- `EU`: `en`, `fr`, `es`, `de`, `it`

Current phase rule:

- keep the family boundary explicit
- do not collapse JP / US / EU into one generic family
- do not pre-design future merged families such as `EU+UK` in the current phase

## 2. Family Difference Matrix

The current confirmed differences are:

| Area | JP | US | EU |
|------|----|----|----|
| Supported languages | `ja` | `en`, `fr`, `es` | `en`, `fr`, `es`, `de`, `it` |
| Spec data source | JP family spec sheet | US family spec sheet | EU family spec sheet |
| Certification content | JP family source | includes US-only items such as `FCC` where applicable | does not inherit `FCC` from US |
| Unit convention | no US imperial mix by default | often contains imperial + metric together | no US imperial mix by default |
| `meaning_of_symbols` / stickers | family-specific | family-specific | family-specific |

Interpretation rule:

- most of the reusable page structure may still be shared
- but `spec`, `certification`, `units`, and `meaning_of_symbols` must remain family-specific unless proven identical by the real source documents

## 3. What Must Stay Family-Specific

Until the future table-driven model is ready, treat these as explicit family-owned surfaces:

1. Spec data
   - [`data/phase1/Spec_Master.csv`](../data/phase1/Spec_Master.csv)
   - [`data/phase1/Spec_Footnotes.csv`](../data/phase1/Spec_Footnotes.csv)
   - [`data/phase1/spec_titles.csv`](../data/phase1/spec_titles.csv)

2. Certification and compliance wording
   - spec rows
   - footnotes
   - any certification note embedded in template text

3. Unit conventions
   - US may include imperial + metric together
   - JP and EU should not inherit US-style imperial units by default

4. `meaning_of_symbols` and sticker-driven pages
   - each family may have a different symbol inventory
   - do not assume the US symbol page can be copied into EU or JP unchanged

## 4. What Can Be Reused More Safely

These page types are better candidates for shared structure, snippet reuse, or generated-page recipes:

- operation guide
- app setup
- generic maintenance flow pages

`product overview` needs a stricter rule:

- its page structure can still be standardized through generated-page recipes
- but the rendered content is still family-specific because it includes port names, input/output ratings, button labels, and other spec-driven fields
- do not treat `product overview` as a plain shared prose page across JP / US / EU

Even for reusable-structure pages:

- family-specific placeholders must still come from the correct family data
- do not hardcode family-specific spec or certification text into shared prose

## 5. Current Maintenance Rule

Current phase rule:

- use docs + config + manifest structure to document the family boundary now
- do not wait for the future multidimensional table to begin enforcing these differences

Operational rule:

- if the family source documents are not yet available, prepare the template structure first
- once the real family spec sheet arrives, update family-specific data before treating the output as final

Example:

- EU template structure may be prepared in advance
- but EU `spec`, `certification`, `units`, and `meaning_of_symbols` are not considered final until the real EU source material is available

## 6. Future Table-Driven Direction

Planned direction:

- this family difference information should later move into a multidimensional table / structured data source
- the table should become the live maintenance surface for family/language coverage and family-specific content differences

Current constraint:

- do not model future merged families such as `EU+UK` yet
- only record the currently active and confirmed family rules

## 7. Maintainer Checklist

When changing a family template or family data set, ask:

- Is this difference truly family-specific?
- Is the source document for this family already available?
- Are we accidentally copying a US-only certification item such as `FCC` into EU?
- Are we accidentally carrying US imperial units into JP or EU?
- Does `meaning_of_symbols` still match the current family sticker set?

## 8. One-Sentence Rule

JP, US, and EU share a build system, but they do not share one identical content contract.
