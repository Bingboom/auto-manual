# Frozen four-language Web alignment

Status: active

Shared intake rules for subsequent models, regions and reviewed RST sources
live in [STYLE_DEFINITION §5](../../docs/renderers/contracts/STYLE_DEFINITION.md#新录入网页的图文分工).
This report's EU package tests are evidence for those packages, not acceptance
of a new CN/JP target. Each new target must bind its required components and
art hashes and receive its own source/asset and desktop/mobile validation.

## Current correction: native PDF re-intake

The screenshot-based candidate described below was rejected during user review.
Its earlier test/build results do **not** accept the corrected re-intake.
The historical files and adapter remain immutable evidence, not the preferred
content authoring path.

The corrected path reads selectable text again from the supplied editable PDF.
`frozen_pdf_intake` uses old JSON only as a coordinate/schema recipe. Missing
DC glyphs are recovered by `frozen_pdf_glyphs` only when the verified original
AI has exactly matching text except for the missing glyph; the original PDF
text, location, AI digest and correction are retained. Approved source errata
remain separate from extraction repair.

`frozen_pdf_document` omits printed Contents. `frozen_pdf_media` and
`frozen_pdf_app` map native labels and instructions to the existing Inbox,
Overview, Operation and App ComponentSpecs. Symbol, specification, warranty,
LCD and fault copy stays editable. Source regions are consumed once so a
component does not repeat its text below a panel image. The existing public
reference consumer now supports its registered explicit `caption_mode=none`;
`live` still requires captions and `embedded` retains its previous behavior.

Charging labels such as `SolarSaga 200 × 2` and `SolarSaga 100 Air × 4`, plus the localized vehicle label,
are figure content, not following prose. A figure binding may declare exact
`live_labels` (a common list or an exact locale-to-list mapping) and the existing `base_art_layout` (art SHA-256, panel tone and
percentage label rectangles). `frozen_pdf_reference` requires each label to
match exactly one native PDF block inside that figure, consumes that block once,
and builds the registered ReferenceFigure `base-art-live-copy` variant through
the shared adapter. Missing/duplicate labels or a different artwork hash fail
before output assets are copied. Desktop labels sit in the artwork's reserved
space; narrow-screen labels remain inside the same gray panel, with the shared
readable mobile layout. The immutable `git-20260928-c38415f5-layout-fixes` package
corrects these three figures in each of the four languages. Native chapter and
subsection headings use the template H1/H2 scale; component-owned headings keep
their contracts. Preface paragraphs and IMPORTANT label are separated, and the
safety warning and eight precautions use the existing callout/list structure.
Warranty scope copy retains its original bold emphasis and existing 3+2 cards.
The LCD table uses HB-TABLE-LCD-ICON with 26 independent source-matched icons,
including both printed rows numbered 22. App screenshots carry live step labels
2.1–2.5. Dense front/right overview panels reuse the corresponding source-language
finished artwork through the existing composite adapter, preserving semantic
callout text in IR and the approved Dutch AC-label erratum. Other body text and
tables remain native HTML. Old five-language presentation stays unchanged.
Browser visual acceptance must be recorded separately from text/asset parity.

The asset manifest contains target identity, a new immutable `technical_version`,
the exact PDF `text_source` filename/SHA-256, and one path, full SHA-256 and
`content_mode` per role. Allowed artwork modes are `textless`,
`fixed-product-markings` and `app-ui`; printed body/table composites are
rejected. Each role must still be visually checked against the original
product: a registry's `ALL` label does not override visibly different sockets
or engraved voltage. Any `pending` entry prevents output creation. Each geometry
or erratum JSON actually read must match the historical manifest hash and size;
old screenshot files are never opened for this verification.

```bash
python3 -m tools.frozen_pdf_web \
  --pdf /path/to/editable-export.pdf \
  --recipe-root manual_sources/JE-1000F/EU/nine-language/git-20260927-c38415f5/four-language \
  --assets-manifest /path/to/verified-asset-bindings.json \
  --language pl --output /tmp/fresh-pdf-pl/md
```

The verified AI original must be beside the PDF under the original filename.
Use a new output directory. The command shares the existing assembler,
stylesheet, Sphinx scaffold and cold replay; it adds no renderer. The source
identity is `frozen-pdf-json`, bound to the same strict target/language/manifest
checks as the historical external adapter. It does not register phase2 fields.

Local acceptance now covers all four complete manuals: 836 positioned field
hashes and 68 native body pages rechecked against the PDF, 26 LCD legend rows and
11 fault rows per language, strict Sphinx builds, source/asset digests and cold
public replay. The operation layout preserves localized mode, light and SOS
labels. Its duration parser recognizes the supplied Dutch, Polish and Ukrainian
second expressions alongside existing English/French/Portuguese copy.

The independent graphics match the supplied two-BS1363-socket product. Reused
symbols come from the live Symbols attachments; missing Operation, right-view,
charging and App controls follow the native extraction recipes. The frozen Overview instance binds a matching front/right canvas and preserves
all long native labels. Browser checks at 390, 768, 1024 and 1280 pixels found
no callout collisions or clipping in any of the four languages. The App
control canvas matches the existing shared label geometry; no locale CSS fork
is added. These source-bound assets are frozen for this authorized release,
not promoted into the live asset registry. Synthetic artwork remains test-only.

The operator approved completing and publishing these four languages on
2026-09-28; MA-196 records the scoped gate-on-green authorization. PR/RTD
publication receipts remain separate from local acceptance. Detailed source
checks are in `reports/four-language-pdf-reimport/content-audit.md`.

## Historical candidate (superseded)

## Discovery and scope

The approved JE-1000F/EU `uk`, `pt`, `nl`, and `pl` inputs are frozen in
`manual_sources/JE-1000F/EU/nine-language/git-20260927-c38415f5/four-language`.
The first Web release uses the shared stylesheet but its package-local
`build_web.py` directly emits HTML. That is not whole-document shared IR.
The baseline is engineering commit `b84239b3`, with the original five v2.7
books and all extracted source, figures and approved errata retained.

The existing production consumer is `web_document_ir.render_document_fragments`.
It accepts assembled `manual-ir/v2`, frozen registry/theme/presentation data,
neutral flow, and embedded ComponentSpecs. Component source carriers are
required by several existing renderers; they must be constructed from the
same source fields and validated against their specs, never from a finished
page of HTML. Ordinary prose remains neutral flow.

## Implementation plan

1. Capture approved text, ordered tables and image hashes from the current
   four-language output. Preserve the old frozen package as historical input.
2. Add a bounded frozen-AI source adapter that maps existing extracted JSON
   into `ManualSource`/`SourcePage`, registered ComponentSpecs and neutral flow.
   Assemble and serialize with the existing public assembler. Resolve and
   freeze the current shared Web contract, component registry and theme.
3. Replay using the public Web consumer into a new candidate package. Keep
   all source imagery and approved text corrections. No source-table writes,
   new model configs, print registration, workflow changes, or new renderer.
4. Verify source/hash preservation, four-language semantic parity, genuine
   component use, source-independent cold replay, and asset-tamper rejection.
   Inspect desktop/mobile component layout against the shared reference.
5. Run applicable lint, tests, guardrails, docs and build checks. Create a
   reviewable engineering PR with the measured evidence and remaining limits.
   The previous publication authorization covers #1315/#148, not a new PR.

## Safety and validation

- Work in isolated `fix/web-frozen-shared-ir`; root checkout's `tmp/` is foreign.
  The main-switching branch wrapper cannot be used in a linked worktree while
  main is checked out by another window; the new worktree starts at freshly
  fetched and API-verified `origin/main` instead.
- Never modify the historical extraction, image or errata bytes.
- Characterization uses the approved frozen output, not a regenerated golden.
- Targeted tests first, then `python3 -m ruff check build.py integrations tools
  tests scripts`, `python3 -m unittest`, maintainability guardrails, doc-link
  integrity, and the JE-1000F US build check in an isolated staging directory.
- Four strict Sphinx builds and desktop/mobile local browser acceptance are
  required. A successful build alone does not prove visual parity.

## Candidate generation and replay

This is a bounded maintenance adapter for the already approved extraction
format, not a general AI importer or a new rendering framework. From the repo:

```bash
python3 -m tools.frozen_ai_web \
  --source-root manual_sources/JE-1000F/EU/nine-language/git-20260927-c38415f5/four-language \
  --output-root /tmp/four-language-shared-ir-candidate
```

Use a new output directory. The command checks the original input inventory,
copies exact approved image bytes, applies the existing errata, assembles and
validates `manual-ir/v2`, serializes it, and invokes
`web_document_ir.render_document_fragments`. It produces one `md` package per
manifest language, including `manual.ir.json`, MyST, assets, and the shared
Sphinx stylesheet. The original five languages and historical package are
never regenerated by this command. For each candidate language, run:

```bash
python3 -m sphinx -W --keep-going -b html \
  /tmp/four-language-shared-ir-candidate/JE-1000F/EU/nl/md \
  /tmp/four-language-shared-ir-candidate/JE-1000F/EU/nl/html
```

`replay_package(package)` consumes the packaged IR/assets/stylesheet without
reopening source extraction, the old renderer, or mutable presentation
contracts. It rejects changed image or stylesheet bytes. The model, region,
locale and manifest digest are bound together; this source-scoped locale
support does not register phase2 columns or print templates.

## Historical frozen-AI representation boundaries

The bullets below describe the retained earlier `frozen_ai_web` intake, not the
current `frozen_pdf_web` layout-fixes delivery described above. The current PDF
route uses the four-column LCD icon component, split App components with live
step captions, and finished composites only for the two approved Overview views.

- Each book has 13 source chapters plus its introduction and EU declaration.
  Prose and the 26 numbered LCD explanations use neutral flow. The LCD source
  has one complete illustration, not 26 extracted icons. It must not be
  labelled with the legacy four-column `lcd-text-only` class, which hides the
  first two columns; its two-column table uses the shared scrolling wrapper.
- Tables, warranty, LCD modes, App inline control and geometrically bound
  notices use registered ComponentSpecs. Source label/body rectangles are
  interpreted only during intake. Public replay validates carrier semantics.
- The 21 original figure crops remain intact, including the two approved
  Dutch AC corrections. Twenty use approved-composite ReferenceFigure;
  LCD mode artwork is carried by the registered LCD mode component. Seven
  pictograms use the symbol component. This does not claim editable Overview
  or Operation artwork; their original labels remain in the source images.
- The App download source is one combined QR/store-badge image. It remains
  an approved ReferenceFigure, not an invented split download component.
- The frozen target Overview instance is retained as required by the public
  document contract. The inventory describes the ReferenceFigure components
  actually rendered, without claiming an editable Overview instance was used.
- The common renderer can merge repeated LCD state cells and format warranty
  years as cards. Acceptance compares all source words/numbers with only the
  explicitly accounted repeated state cells removed, all image hashes, and
  the exact approved corrections. Pixel equality with the legacy custom
  layout is neither expected nor a substitute for shared component checks.

## Verification record

The focused suite covers all four books, shipped-copy and image parity,
source preservation, relocation/cold replay, manifest/locale tampering,
asset/stylesheet tampering, and individual component semantics. Browser
acceptance must additionally check visible LCD text, exact chapter anchors,
image loading and narrow-screen table scrolling. Strict Sphinx alone does
not catch hidden columns or normalized anchor names.

This engineering change prepares a candidate only. The previous gate-on-green
authorization is not reused for this change; production still requires a
separately authorized engineering/publication merge and live RTD verification.

Local verification on 2026-09-28: the full suite ran 4,746 tests with 22
documented skips and no failures; the final affected-suite rerun passed 19
tests. Ruff, maintainability guardrails, documentation links, isolated
JE-1000F/US fixture `check`, and all four strict Sphinx builds passed. The
in-app browser checked all four locales at widths 390 and 1280: no missing
chapter anchors, no document overflow or uncontained wide tables, all 26 LCD
legend rows visible, and 13 shared notices per locale (including Polish
`Uwaga`/`UWAGA`). Local HTTP verification checked all 112 source image files
against their packaged SHA-256 values. These are local acceptance results,
not RTD deployment evidence.
