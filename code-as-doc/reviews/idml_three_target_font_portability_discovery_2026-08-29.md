# IDML three-target font-portability discovery — 2026-08-29

## Decision

The 2026-08-29 three-target structural build is not a visual acceptance. Fix
the shared IDML font and component contracts so the raw designer-facing
packages open on the supported macOS and Windows hosts without Windows-only
symbol fonts, Korean `.notdef` boxes, or circled Warranty-year glyphs.

The acceptance targets remain:

- JE-1000F / US: approved 52-source / 58-physical-page assembly;
- JE-3000C / KR: 18-page candidate target assembly;
- JBP-2000B / US: 43-page candidate target assembly.

Candidate governance does not change. A placed full-page PDF is not evidence
that native editable Korean IDML text has a usable font.

## Reproduced baseline

The three simultaneously built production IDML packages show three distinct
failures in InDesign 2026 on macOS:

| Target | Native-text failure | Baseline package evidence |
| --- | --- | --- |
| JE-3000C / KR | Korean body text displays as `.notdef` boxes | 2,746 explicit `Noto Sans KR` runs, but the host does not have that font and the handoff contains no font binary |
| JE-1000F / US | DC, subscript, reference and structural symbols use unavailable Windows faces | 163 `Segoe UI Symbol` and 90 `Yu Gothic` references; 95 literal `U+2393` DC symbols and three literal subscript-four glyphs |
| all three targets | Warranty-year numeral is a box | the shared component rewrites ordinary `2` / `3` source values to `❷` / `❸`, then routes them to `Yu Gothic` |

The `Status="Installed"` attributes emitted in `Resources/Fonts.xml` are
declarations, not a query of the opening host. Structural IDML validation
therefore cannot use them as proof that a font is available.

## Root causes

### 1. Production-mode asymmetry

`tools/export_idml.py::_new_production_writer()` enables the existing native
vector marker contract only for `target-assembly`. JE-1000F uses
`approved-reference`, so it falls back to literal `●`, `U+2393`, and Unicode
subscript glyphs even though the portable shared primitives already exist.

The mode distinction is governance, not typography. Both final-assembly modes
must consume the same portable symbol primitives.

### 2. Windows-only fallback families

`tools/idml/font_family.py` and `tools/idml/inline_text.py` route editable
symbols to `Segoe UI Symbol` and `Yu Gothic`. The former is Windows-only; the
latter has incompatible macOS/Windows family and face names. Finalizer-time
host substitution can make an exported PDF readable, but it cannot make the
raw IDML package portable when a designer opens it directly.

Use unchanged SIL-OFL font binaries with deterministic SHA-256 pins instead:

- `Noto Sans` for the reference mark, ordinal indicator and subscript set;
- `Noto Sans Symbols` for DC and editable circled markers through 20;
- `Noto Sans Symbols2` for the filled-circle fallback;
- `NanumGothic` for native Korean text.

The IDML output and production handoff must place the required files in a
`Document fonts/` directory beside the document. Commercial Gilroy remains an
operator-provisioned font and is not added to the repository.

### 3. Warranty component violated its source and visual contracts

`tools/idml/components/warranty.py::_year_heading()` originally mapped ordinary
source numbers through `_CIRCLED`, producing host-dependent `❷` / `❸` glyphs.
The first portability pass overcorrected by emitting bare large `2` / `3`
digits, which removed the approved black circular badge. The shared component
now preserves the source number as ordinary editable ASCII inside a native
IDML circle: the geometry supplies the black badge, while the white digit uses
the packaged production face and remains editable. The native circle changes
the inline advance relative to the former Unicode glyph, so the shared
component owns that migration delta and pins the year unit to a fixed tab stop.
The warranty subtitle reuses the same x anchor; focused PDF coordinate review
must show `YEARS` and `Standard Warranty` / `Extended Warranty` aligned within
0.01 pt without changing the frozen layout-params identity.

### 4. LCD rows beyond 20

Unicode has two incompatible circled-number blocks: `①`–`⑳` and `㉑`–`㉗`.
The portable Noto symbol face covers the first block but not the second. The
LCD projection must emit a readable ASCII parenthesized label for 21–27 rather
than silently reintroducing a host-only font. This affects only the editable
row marker, not row order, copy, assets, pagination or component geometry.

## Planned files and safety nets

| Phase | Files | Safety net |
| --- | --- | --- |
| portable font assets | `docs/templates/word_template/common_assets/fonts/idml_portable/**`, `tools/idml/font_assets.py` | exact file hashes; every referenced portable family has one distributable binary and OFL notice |
| font contract | `tools/idml/font_family.py`, `tools/idml/inline_text.py`, `tools/idml/style_resources.py` consumers | no `Segoe UI Symbol` / `Yu Gothic` in generated resources, stories or delivery manifest |
| shared production mode | `tools/export_idml.py` | approved-reference and target-assembly writers both enable native structure markers; fallback/golden mode remains explicit |
| Warranty | `tools/idml/components/warranty.py` | source `2` / `3` stays ASCII in an editable child story; a native black circle preserves the approved badge without a circled glyph or symbol-family run |
| LCD | `tools/idml/ir_projection.py` | 1–20 keep approved circled labels; 21–27 become `(21)`–`(27)` without row loss |
| handoff | `tools/idml/design_handoff.py`, `tools/idml/delivery.py` | direct IDML and delivery ZIP contain `Document fonts/`; the manifest distinguishes bundled OFL fonts from optional commercial fonts |
| final verification | no committed `_build` artifacts | Ruff, targeted tests, full unittest, guardrails, reference pins, three clean `--idml-mode both` builds, native InDesign preflight and focused PDF review |

## Non-goals

- No model-specific page renderer, font override or Warranty copy patch.
- No reference-PDF, 52-source / 58-page composition-map, page-binding or
  geometry change for JE-1000F.
- No promotion of JE-3000C / KR or JBP-2000B / US to approved status.
- No redistribution of Gilroy or any Windows/macOS system font.
- No source-table, schema, public CLI, workflow or dependency-version change.
- No deletion or cleanup of existing `_build`, release or review artifacts.

## Implemented verification

The final shared contract keeps U+2393 as editable text and routes it through
the bundled `Noto Sans Symbols` face.  The earlier three-object vector replica
was removed from fixed specification rows because native InDesign measured
each affected row 1.5 pt taller.  The shared car-charging note frame now has a
15 pt two-line safety height, without a language or target branch.

Native InDesign 2026 `21.0.1.6` verification after rebuilding all three
targets produced:

| Target | Assembly | Native preflight |
| --- | --- | --- |
| JE-1000F / US | 52/52 source pages, 58 physical pages | 0 overset, 0 missing fonts, 0 missing glyphs, 0 bad links |
| JE-3000C / KR | 18/18 source and physical pages | 0 overset, 0 missing fonts, 0 missing glyphs, 0 bad links |
| JBP-2000B / US | 43/43 source bindings, 28 physical pages | 0 overset, 0 missing fonts, 0 missing glyphs, 0 bad links |

The JBP baseline initially retained three pre-existing connection-tail carrier
oversets.  They were not font regressions: the locked image plus its governed
paragraph spacing exceeded the target split by 1.4-4.4 pt.  The candidate
assembly now declares one shared `306.5` pt troubleshooting split for EN, FR,
and ES.  No renderer condition or page-local geometry was added.

Static scans of the final IDML packages find no `Segoe UI Symbol`, `Yu Gothic`,
`Noto Sans KR`, `❷` / `❸`, or high circled LCD labels. Warranty headings keep
ordinary editable `2` / `3` in native circular badges; the KR package declares and carries
`NanumGothic-Regular.ttf`.  The three delivery ZIPs package 112/112, 103/103,
and 41/41 links respectively, with zero missing links and the required OFL
font binaries and license notices under `Document fonts/`.

## Save/reopen hardening follow-up

The first portable-font implementation still allowed U+203B (`※`) to depend
on the bundled `Noto Sans` face. It passed the import-time preflight, but a
saved JE-1000F INDD could reopen with the reference mark as a pink missing-glyph
box. The shared inline serializer now emits the approved 5.6 pt reference mark
as native IDML path geometry. Package assembly binds its left bearing, glyph,
and right bearing objects to deterministic IDs derived from the story identity
and occurrence index; no U+203B text run or reference-mark font resource is
written.

`indesign_finalize.py` now enforces `indesign-preflight/v2`: save INDD, close,
reopen, recompose, rerun page/story/overset/font/link checks, and only then
export the PDF and scan it for `.notdef` glyphs. With `Document fonts/` beside
the output INDD, the rebuilt JE-1000F package passed the post-reopen gate at
58 pages with zero overset, missing fonts, missing glyphs, and bad links. The
page-15 specification footnote was also rendered at 400 dpi and visually
confirmed without a pink frame or baseline/advance regression.
