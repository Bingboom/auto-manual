# JE-2000 EU new locale intake acceptance

Status: active

The candidate intake adds Portuguese, Dutch and Polish for JE-2000F and
JE-2000E through native PDF-compatible AI extraction, `manual-ir/v2`, existing
ComponentSpecs and the shared Web renderer. These are review candidates, not
published releases. The existing six-language sources and published Ukrainian
routes remain the baseline; revised Ukrainian source text is audit-only.

## Sources and scope

- [JE-2000F source and reproduction](../../manual_sources/JE-2000F/EU/nine-language/git-20260929-eb899f44-intake/four-language/README.md)
- [JE-2000E source and validation](../../manual_sources/JE-2000E/EU/nine-language/git-20260929-d6462454-native-candidate/three-language/README.md)
- [Shared adapter contract](../dev/je2000_eu_new_locales_ir_adapters_2026-09.md)

The originals are `HTE154-EU-9国语言-0924.ai` (F, SHA-256
`eb899f4407517869e1a0405ce2b2ed6daa76196f23197ad03fb0e295d39d84e6`)
and `HTE152-EU-9国语言-0924.ai` (E, SHA-256
`d64624547e3b88fd1d8c3ea78f9e446f07e2364b148b707eb0d97ba4c24415de`).
Their original bytes were not modified. No OCR, live-table writes, automatic
translation of the books, or solar-asset sharing redesign was performed.

Product parameters, electrical artwork and feature coverage are independently
bound to each target. E retains its extra-battery chapter, three product views,
four App controls, 27 LCD rows and expansion-port specifications. F retains
its own control panel, source-specific charging diagrams and warnings.

## Candidate checks

The integrated candidates in `/tmp/je2000-new-locales/final-candidates-v3`
passed public frozen-PDF CLI intake and strict Sphinx. Each was copied to a
fresh location and replayed with PDF access forbidden; all six Markdown
outputs were byte-identical before and after replay.

| Model | Locale | IR chapters | Native long lines checked | Cold replay |
| --- | --- | ---: | ---: | --- |
| JE-2000F | pl | 15 | 404 | byte-identical |
| JE-2000F | pt | 15 | 399 | byte-identical |
| JE-2000F | nl | 15 | 391 | byte-identical |
| JE-2000E | pl | 16 | 412 | byte-identical |
| JE-2000E | pt | 16 | 402 | byte-identical |
| JE-2000E | nl | 16 | 388 | byte-identical |

Long-line matching is a triage check, not a claim of complete visual or
translation equivalence: it excludes short and outlined copy and includes
hidden semantic carriers. Remaining differences are classified as printed
duplicates with retained alternate wording, or tiny fixed product markings
owned by finished figures. Source-local ledgers retain the evidence.
Independent cell/line ownership checks cover adjacent troubleshooting rows
and operation labels to catch duplication that a presence check cannot find.

Browser review covers native headings outside images, full technical artwork,
LCD status emphasis, separate operation labels/instructions, native two-hour
standby copy, warranty cards, App numbers below screenshots and model-specific
App controls. Desktop and 390-pixel mobile views have no document-wide
horizontal overflow; wide tables remain locally scrollable.

After alignment with main `bf5d46ee`, the full unit suite passed 4,836 tests
(22 skipped). The 105 intake-focused tests and 50 publication/evidence tests
passed, as did Ruff, maintainability/complexity guardrails and documentation
links/lifecycle checks. Complexity allowances were only reduced or removed.
The JE-1000F/US `build.py check` passed again using an isolated copy of the
existing local phase2 snapshot and fresh staging root. The first check in the
clean worktree lacked that untracked snapshot; it was not a source-table
absence. All six integrated builds and cold replays were repeated after main
alignment; their Markdown was byte-identical to the browser-reviewed outputs.
Test and integrated-build receipts remain under `/tmp/je2000-new-locales` for
this workstation.

## Decisions required before publication

1. **F source errata:** EU miniature nameplates in three new locales say
   100–120 V / 15 A while the source's external labels/specifications say
   220–240 V / 10 A. Dutch AC-button text also says DC in four places.
   Before/after candidates are under the F package's `candidates/errata`;
   none is applied to released content.
2. **E prefaces:** the new source omits pt/nl/pl prefaces. The candidate
   reuses reviewed same-English-source translations, substitutes the product
   name and follows E English's legal subject `Jackery Inc.`. These are
   visibly marked as pending review.
3. **E Dutch imported markup:** the printed App instruction includes a
   literal `<g id="1">` suffix. The candidate preserves it pending an
   explicit source-cleanup decision. Quote escaping is normalized by the
   existing App display rules; the original evidence remains unchanged.

All six IR packages have `publication_eligible: false` and nonempty pending
review metadata. The release-evidence boundary rejects actual pending F and
E candidates. Both Git-only frozen evidence sealing and independent receipt
verification enforce the guard, with direct negative tests; approved-empty
and legacy metadata-free cases retain support.
No RTD publication or merge authorization is claimed by this report.
