# Content Block Migration Assessment

Updated: 2026-05-31

This report records the Phase 3 assessment for long-form template pages after the LCD / Symbols / Product overview short-copy consolidation. It is intentionally an assessment only: Operation guide and App setup body copy stays in RST until a follow-up migration is approved.

## Scope

Reviewed template families:

| Page | Current footprint | Current owner |
| --- | ---: | --- |
| `05_operation_guide` | 13 templates, about 2.7k lines total | RST templates plus Spec_Master placeholders |
| `12_app_setup` | 10 templates, about 0.9k lines total | RST templates plus Spec_Master placeholders |

## Classification Standard

Move to a data table when text is repeated across more than three targets, business-maintained, multilingual operational content, or product/UI copy that changes outside engineering.

Keep in RST when content is layout, directives, stable instructional shell text, or engineering-maintained structure.

Move to config when content is regional legal identity, support contact, URL, marketplace destination, or another environment difference.

## Page Findings

| Page area | Recommendation | Why | Estimated change | Risk |
| --- | --- | --- | --- | --- |
| Operation guide section titles and image alt text | Candidate for `localized_copy` | Short, repeated page chrome that translators may maintain consistently | Medium | Low |
| Operation guide button-action microcopy such as On / Off / Press once | Candidate for `localized_copy` after key naming review | Repeated across targets and already overlaps LCD state terminology | Medium | Medium, because page-specific grammar differs by language |
| Operation guide long safety cautions, notes, and explanatory paragraphs | Keep in RST for now | They are long-form translated prose with page-local structure and warning formatting | High | High, because accidental sentence splitting can damage compliance wording |
| Operation guide thresholds and product-specific values | Keep in `Spec_Master.csv` | These are model/spec values, not reusable copy | None | Low |
| Operation guide images and RST directives | Keep in RST | Layout and asset placement are template structure | None | Low |
| App setup section headings, button labels, and image alt text | Candidate for `localized_copy` | Short UI copy repeats across language families and may need coordinated translation | Medium | Medium, because CN app naming differs from global Jackery App wording |
| App setup QR/app-store instructions | Audit before moving | Business-maintained and regional, but may require per-market app name/store routing | Medium | Medium |
| App setup binding, Wi-Fi, Bluetooth, and reset paragraphs | Keep in RST until content-block schema exists | Long procedural prose with target-specific phrasing | High | High |
| App setup manufacturer/address and support tail text | Move to config if reused | This is regional environment/legal identity, not page content | Low | Medium, because CN-only legal text may not map to other families |

## Migration List

Recommended next implementation round:

1. Add `localized_copy` keys for Operation guide and App setup page titles, section headings, table labels, and image alt text.
2. Keep body paragraphs in RST and add only copy-token support where labels are already isolated.
3. Add a check contract for required copy keys per page/language before touching long prose.
4. Review app market, support, manufacturer, and URL text for config ownership instead of a content table.

Not recommended in the next round:

- Moving whole Operation guide paragraphs into a generic block table.
- Splitting warning/caution bodies into sentence-level copy keys before compliance review.
- Mixing model/spec values into `localized_copy`.

## Decision

Proceed with a narrow short-copy pass only after LCD / Symbols / Product overview validation is stable. Defer full content-block migration for Operation guide and App setup until a dedicated long-form schema and review workflow are designed.
