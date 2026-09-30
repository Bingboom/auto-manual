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

The integrated candidates (final approved F in
`/tmp/je2000-new-locales/approved-corrections-v4`, E in
`/tmp/je2000-new-locales/approved-corrections-v3`)
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

After alignment with main `bf5d46ee`, the full unit suite passed 4,840 tests
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

## Operator source decisions — 2026-09-29

1. **F source errata approved:** change the miniature EU AC-input nameplates
   from 100–120 V / 15 A to 220–240 V / 10 A in pt/nl/pl, and correct four
   Dutch AC-button references from DC to AC. Same-page external callouts and
   native specification tables provide the electrical evidence. Original
   AI bytes and uncorrected text remain retained for comparison.
2. **E reused prefaces:** use the proposed source-provenanced pt/nl/pl copy
   with product name Explorer 2000 Plus and the operator-specified legal
   subject `Jackery`. Approval records accompany the locale bindings and
   individual paragraphs; no legal-subject substitution to `Jackery Inc.`
   remains in output.
3. **E Dutch App markup:** remove the literal `<g id="1">` suffix through an
   exact-text erratum. Native source evidence remains unchanged.

Pending and unknown source-approval states continue to block release evidence.
Both Git-only frozen evidence sealing and independent receipt verification
apply that guard. Approved source decisions remove only their corresponding
pending markers; they do not imply PR merge or RTD publication authorization.

The updated six-book native builds, strict Sphinx builds and cold replays
passed. The F source-local Web review records the three corrected nameplates,
four Dutch AC labels, one heading per Overview view and the repaired Dutch
DC symbol. The operator-installed Segoe UI Symbol U+2393 glyph replaces only
the missing character, retaining native geometry and source-frame evidence.
All six frontmatter legal subjects are `Jackery`; E Dutch App markup and
review-preface banners are absent. The revised suite passed 4,840 tests
(22 skipped), with Ruff, maintainability, document gates and the isolated US
baseline build green. No RTD publication or merge is claimed.

## Operation-panel geometry follow-up

The first Web preview reused operation rectangles from a different crop. Its
ordinary stage also included supporting paragraphs, so percentage positioning
shifted when those paragraphs wrapped. The follow-up selects the existing
`base-art-live-copy` component for the five operation panels in each new
locale. Per-model original artwork supplies each bracket, circle, prerequisite
pill and clock; crop-specific anchors are bound to the actual artwork SHA.
F's DC/USB circle and energy-saving product top are restored from the original
PDF paths. E retains its own product, AC1/AC2 and expansion hardware.

Main-power source ownership now includes the original frame's 12-hour note,
which previously appeared as a separate paragraph outside the card. Four
native blocks preserve the standby heading, body, App note and 12-hour note;
the shared base-art main-power style bolds the heading. E Dutch LED's first
instruction now includes the native third line, `te schakelen.`, by extending
only that field's extraction rectangle. No translated copy is invented.

This follow-up changes target recipes/assets and one scoped CSS rule, with
no new Python renderer, public interface or dependency. The earlier full
4,840-test result covers the unchanged Python implementation; the existing
12 base-art component tests pass for the selected presentation mode. Fresh
six-book build, cold-replay and browser receipts are recorded separately from
PR merge and RTD publication.

The final follow-up passed six strict Sphinx/native builds and six PDF-free
byte-identical cold replays. Browser checks at 859px and 390px verified all
30 operation figures with no panel overflow or broken operation art. Each
main-power card owns exactly four support blocks, a bold first line and one
12-hour note. Desktop screenshots confirmed native leader alignment; the
Dutch mobile preview confirmed steps stack below the art. The six previews
share a stable local entry; these checks do not claim RTD publication.

The four-block main-power layout keeps the first three standby blocks in an
independent rounded bubble on the right, with the fourth (12-hour) note on
white beneath it, separated by whitespace inside the outer card. At narrow
widths the bubble expands to the content width, while the note stays separate.
The CSS requires exactly four blocks, preserving older three-block cards.
Six rebuilt books and PDF-free replays passed; browser measurements confirmed
separate backgrounds and positive gaps at 859px and 390px, with no overflow.

AC and DC/USB prerequisite pills now use one shared CSS token
(`--hb-prerequisite-surface: #e6e7e8`) in desktop and narrow layouts, matching
the common darker source pill selected by the operator. The native F source used different grayscale
fills on p139 and p140; the live rounded HTML pill normalizes that presentation
while preserving source artwork, native coordinates and searchable copy.

F LCD-mode artwork crops for pt/nl/pl now exclude the source outer-frame
and adjacent table strokes. The tighter source-PDF crop retains the full
product, hand and POWER callout (12x visual check); the live HTML table and
outer card border remain unchanged. E uses separate clean artwork.

In-box AC cable and manual pictogram bindings for F/E pt/nl/pl now directly
reference the existing `in_the_box/ac_charging_cable` and
`in_the_box/manual_icon1` common assets (the same hashes used by JE-1000F).
There is one canonical repository source for each image; frozen build outputs
copy those hash-verified bytes for self-contained replay. Native per-language
crops remain source evidence but are no longer used by these two slots.
Model-specific main-unit art, localized labels and HTML numbering stay intact.

Key combinations now use the shared `HB-TABLE-KEY-COMBINATIONS` ComponentSpec
and the existing English HTML transformer/CSS. Body cells remain regular-weight
text with 40/25/35 columns and the governed rounded frame. F/E pt/nl/pl native
operation text rectangles exclude the separate clock duration labels; the
complete instruction retains its duration. Auto-resume already uses its shared
component and remains unchanged.

Validation: six strict HTML builds and byte-identical PDF-free replays passed;
browser comparisons matched the English table frame, fill, proportions and
body weight. New component/roundtrip tests passed. The 4,842-test full run
found 20 errors and two failures from a modified local JE-1000F AI fixture;
all 34 tests in the affected modules passed with a separately downloaded,
hash-verified original (c38415f5...), preserving the existing local files.
The isolated US build check, lint, documentation links and guardrails passed.


## Shared battery symbol source replacement (2026-09-29)

The shared `symbols/weee2` export and live Symbols `weee2` record both carried
an 81 x 69 raster with an opaque white rectangle. The operator approved the
native-vector comparison and replacement on 2026-09-29. The canonical PNG is
now 492 x 519 RGBA, with transparent surroundings; the lower-bar `symbols/weee`
asset is unchanged. F/E pt/nl/pl all bind the same canonical source file,
rather than copying the symbol separately for each product or locale.

Both live attachments were downloaded after replacement and are byte-identical
to the canonical PNG (SHA-256 `cf04ff00bdeb8de5971a55e5d8be6ef91e1a4ddad479f817f0c535914a392d45`).
Readback confirms one nonempty file token in `recvuCHOujnTWI/export_file`,
`rec277z0GFV87J/Figure`, and gallery `recvuCHHTVB8zL/preview`; the export hash is
updated. Retained native vectors, extraction coordinates and readback receipts
are in `manual_sources/shared/symbols/weee2/20260929/`.

Validation: six strict Sphinx builds and byte-identical PDF-free cold replays;
all six resolved assets match the shared source; native-line findings are
unchanged; 25 asset-registry/charging regression tests pass. Browser F/NL
loads the 492 x 519 image without the white box. Existing frozen published
releases are unchanged until regenerated and republished.

## Publication authorization and frozen source

The operator authorized RTD publication on 2026-09-29; MA-202 covers #1328
and the ensuing six-route Hello-Docs publish PR. The release source packages
are `git-20260929-eb899f44-native-web/three-language` for F and
`git-20260929-d6462454-native-web/three-language` for E. Each retains
self-contained pt/nl/pl IR, MyST, governed images and an input hash inventory.
After incorporating main 7142b644, all six strict builds and PDF-free cold
replays passed and remained byte-identical to the approved v17 IR and MyST.
The US regression check, Ruff, maintainability and document gates passed.

Secret-scan flagged three Feishu attachment resource identifiers in the new
shared-symbol readback receipt. The public receipt now retains their SHA-256,
nonempty attachment verification, record/field identity, size and content hash;
full readbacks remain in the local audit bundle. The scanner rules are
unchanged and the complete local scan passes.
