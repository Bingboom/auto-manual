# JE-2000F and JE-2000E EU four-language frozen IR adapter

Status: active

## Source and boundary

The two current EU six-language sources are immutable baselines under
`manual_sources/JE-2000F/EU/en/2.0` and `manual_sources/JE-2000E/EU/en/2.0`.
The new native-text PDF-compatible AI originals are `HTE154-EU-9国语言-0924.ai`
(JE-2000F, SHA-256 `eb899f4407517869e1a0405ce2b2ed6daa76196f23197ad03fb0e295d39d84e6`,
170 pages) and `HTE152-EU-9国语言-0924.ai` (JE-2000E, SHA-256
`d64624547e3b88fd1d8c3ea78f9e446f07e2364b148b707eb0d97ba4c24415de`,
179 pages). Their source receipts and current live coordinates are retained in
`/tmp/je2000-new-locales/source_receipt.json`; source-local investigations
are `/tmp/je2000f-new-locales-discovery.md` and
`/tmp/je2000e-new-locales-discovery.md`.

For F, new pt/nl/pl are physical pages 116–133, 134–151, 152–169; revised uk
is 98–115. For E, new pt/nl/pl are 122–140, 141–159, 160–178; revised uk
is 103–121. Use physical pages rather than defective printed Contents/page
numbers. F has two overview views, three AC sockets, and a UPS expansion;
E has three views, AC1/AC2, an extra-battery chapter, 27 LCD items, four App
controls and expansion-port specifications. Their source and artwork must be
bound independently. Neither is a JE-1000F parameter substitution.

The command remains `python -m tools.frozen_pdf_web --pdf <native-pdf-compatible-ai>
--recipe-root <model-frozen-recipe> --assets-manifest <artwork-binding>
--output <new-empty-package> --language <uk|pt|nl|pl>`. It produces
`manual-ir/v2` with embedded ComponentSpecs, then uses the shared Web replay.
`build.py md` is the older phase2/RST route and does not call this command.
There is no second renderer.

## Minimal adapter contract

The source package keeps manifest-pinned `source/<lang>_direct_source.json`,
`section_index.json`, `symbols.json`, `lcd_indicators.json`,
`operation_tables.json`, `warranty_columns.json`, `app_sections.json`,
`front_back_source.json`, `<lang>_figure_manifest.json`, and `errata.json`.
The optional manifest-pinned `source/target_layout.json` carries only target
geometry/shape: ordered section IDs; native specification and troubleshooting
row edges; symbol/LCD regions; inbox/overview/operation rectangles and
callout roles; App control regions/roles; expected LCD icon identities; and
additional chapter ownership such as E's `extra_battery`. The default when
absent is the current JE-1000F contract, keeping that package byte-stable.
No source prose, translated values, or image bytes belong in target_layout.

The adapter validates source identity, chapter order, every positioned
extraction, consumed media regions and governed asset hashes before package
assembly. It preserves native paragraphs, tables and warning semantics in
flow nodes and ComponentSpec carriers. The Web renderer, component registry,
style sheet and public replay stay shared. E's additional content receives
native flow and existing components; it does not justify screenshot tables.

The target-local layout may also pin native Overview view captions, reference
caption rectangles, figure-consumed rectangles, split warning label/body
rectangles, and a merged body-heading line within an exact source block.
These entries identify geometry and ownership; their displayed text is read
from the hash-pinned PDF. The artwork binding opts the exact model/region into
operation figures through `web_contract.figure_targets`. A reference-figure
Overview excludes that source path from `product_overview.source_patterns`,
so enabling operations does not require an incompatible Overview instance.
The App label record accepts the existing three-control sequence or E's
four-control sequence, with positions derived from source bboxes and the
bound control-art crop.

Two optional source-geometry controls also support the JE-1000H EU pt/nl/pl
addition. An LCD recipe row with `selection: "lines"` uses majority line
overlap, excluding a neighboring row's descender that barely touches its
rectangle; rows without this option retain textbox extraction. The target
layout's `app.caption_only_steps` may list a screenshot step such as `2.5`
whose prose has no printed number. This opt-in preserves the prose verbatim,
still requires the exact native screenshot-number block, and rejects a
conflicting numeric prefix. It never synthesizes a missing source number.

Operation label anchors must be derived from each model/language's bound
art crop. The existing `base-art-live-copy` presentation separates the art
canvas from supporting paragraphs, so paragraph height cannot shift labels
relative to leader lines. Preserve complete circles, leaders and prerequisite
pills in the crop; titles stay outside artwork. Reusing another target's
percentage rectangles is not a substitute for checking native coordinates.
The text-extraction rectangle is not the display pill's width: size each
locale's prerequisite pill from its rendered text and the drawing's safe
area, including narrow-screen wrapping. Footer-overlay components already
render a clock beside the live duration; their bound artwork must not retain
a second baked clock. Status-right duration anchors retain the native clock
and add only the duration text. These are source-binding decisions, not
reasons to change shared CSS.

`pending_source_review` in the frozen IR metadata marks a review candidate,
including E's visibly marked preview preface. The Web release-evidence seal
reads the built IR sidecar and rejects any nonempty pending list or explicit
`publication_eligible=false`; the queue staging path checks before copying
the candidate. Approved source packages with an empty list and existing
projection releases continue through the same seal. This gate does not
substitute for source approval, PR review, or browser acceptance.

A reused preface can transition to `operator-approved` only with a dated
operator instruction on its hash-pinned binding and approval on every
paragraph. Approved paragraphs retain their original source provenance and
render without the review banner. Missing approval or unknown status is
rejected. Corrected finished-figure semantic copy applies the same exact-text
errata as visible text, so accessibility content does not retain old labels.

## Implementation and acceptance order

1. Define and validate the target-layout recipe with exact source/target
   matching. Parameterize fixed JE-1000F row/region assumptions behind it;
   retain old defaults and existing public CLI.
2. Add target-local F/E recipes and governed artwork manifests in separate
   source worktrees. Intake one locale at a time (pl first), then pt/nl/uk.
   Keep revised uk as a comparison package until differences against the
   published six-language route are reviewed.
3. Run focused frozen-PDF/ManualIR/ComponentSpec/Web tests, then cold replay
   with originals unavailable. Require zero unmapped or duplicated body
   blocks, no unresolved glyphs, complete safety/warranty/UPS/extra-battery
   content, correct model specifications and all asset SHA-256 checks.
4. Inspect desktop and mobile Web pages in each locale, including overview,
   LCD, operations, App and long tables. Compare the existing six-language
   published source hashes to verify no regression. Publication is a separate
   step.

Known source-recovery debt is documented in the two `/tmp` discovery reports:
F has three wrong EU right-view nameplates, Dutch AC-button labels, two null
glyphs, and UK warranty text missing from native extraction. E has outlined
or missing text and multiple product-specific structures. These require
explicit source evidence and approved corrections, not silent fallbacks.


## Charging-label regression and English artwork reuse (2026-09-29)

The JE-1000F fix (`4e413875`) already supplied the shared live-label binder.
JE-2000F's initial intake (`0e3bb672`) omitted `live_labels` and
`base_art_layout` from all three charging-figure bindings. Solar captions
were consequently emitted by both the reference-caption adapter and the
body stream; car artwork still contained its localized vehicle label.
This persisted through the preview revisions: it was an onboarding omission,
not a later renderer rollback. The earlier regression test exercised only
the JE-1000F frozen books.

F pt/nl/pl now share three bases derived from the approved same-model English
PDF (SHA-256 `6b4af85236ccfee0f4d24ad55ee8b24684d023982b5da216023d4f716f183f3d`).
The full-frame English crops preserve both magnifier circles and the correct
2-panel/4-panel arrangements. The corrective source-package recipe removes
native labels with graphics preserved; the car note's white pill is removed
using an equally sized, empty native background region. The existing English
assets and approved recipe are unchanged. Locale text is extracted from each
locale's original source and consumed exactly once by the shared
`HB-SPECIAL-REFERENCE-FIGURE` base-art/live-copy component.

The car note is an HTML span; its white fill, padding, rounded corners and
wrapping come from `.hb-reference-live-pill`. This component is model-neutral
and can serve other portable power stations. Each model still binds its own
verified device/interface artwork; sharing the component never authorizes
substituting another model's product diagram. On narrow screens the note
moves below the art without leaving a baked empty white pill behind.

Validation: all six F/E pt/nl/pl strict Sphinx builds and PDF-free byte-identical
replays passed; native-line audit findings are unchanged from the preceding
build. F's three locales have one DOM occurrence per solar label and no
separate caption paragraph. E's sources/artwork are unchanged in this fix.
`tests/test_je2000f_charging_bindings.py` exercises the committed source
bindings through the shared renderer, asserts same-model shared asset paths,
and rejects a baked car-note pill or residual text in the empty artwork region.
