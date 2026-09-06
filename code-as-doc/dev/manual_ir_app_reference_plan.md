# ManualIR v2 App and Reference Figure ComponentSpec Plan

Date: 2026-09-05
Branch: `feat/manual-ir-app-reference-figures`
Baseline: `ef45a0df` (cut 4)

## Discovery

The whole-document package already writes renderer-neutral `manual-flow/v2`
and embeds fourteen registered ComponentSpec types. App download, the inline
Add-device control, App artwork, and governed Charging/App reference figures
are still serialized as ordinary flow. During Web replay,
`tools/web_presentation.py` scans the reconstructed page DOM and invokes their
legacy source projectors again.

The existing Web behavior is mature and is the compatibility baseline:

- App download keeps two editable localized copy columns and uses shared
  store/QR artwork;
- the inline Add-device control keeps the surrounding rich paragraph and
  replaces only the localized button label with the shared `+` control;
- App add-device uses shared text-free phone/control artwork plus three live
  localized labels;
- general Charging/App reference figures retain a complete semantic fallback
  and may show one exact-locale or explicitly shared approved composite;
- approved composites are selected by target, stable replace key, and locale,
  and are rejected when their source-fragment or content SHA-256 changes.

`HB-SPECIAL-APP` already exists in the style contract but is not registered as
a ComponentSpec. Charging figures do not have a matching stable semantic style
ID; treating them as App or Operation would couple unrelated semantics.
Therefore this cut registers:

- `HB-SPECIAL-APP` with `download`, `inline-control`, and `add-device`
  variants;
- `HB-SPECIAL-REFERENCE-FIGURE` with `semantic-fallback` and
  `approved-composite` variants.

ComponentSpec owns localized slots, stable roles, exact/shared locale policy,
and packaged asset references. Neutral `carrier_flow` retains source-authored
rich markup and image attributes. The whole-document `asset_sha256` manifest
remains the byte-integrity authority. A selected approved composite is also
recorded on the reference instance with its asset key, locale, content hash,
and source-fragment hash; the Web adapter must reproduce and verify the latter
before displaying the frozen image.

## Implementation phases

1. Add characterization tests for the two component families, variant-specific
   validation, four renderer projections, carrier agreement, locale policy,
   and approved-composite identity/hash drift.
2. Register both ComponentSpec types, connect their theme roles, and add the
   generic reference-figure style contract without introducing model-specific
   Python or CSS.
3. Add focused source adapters. Reuse the existing App download/control source
   contracts; claim only exact contiguous carrier nodes. Parse reference
   figures structurally from the governed presentation contract and resolve at
   most one target/locale composite.
4. Package source art, shared App artwork, and selected approved composites by
   role. Preserve first-use ordering and bind every role to the existing
   whole-document SHA-256 asset union.
5. Dispatch embedded components directly during Web replay. Validate carrier
   agreement and approved source-fragment identity, then skip the old full-page
   App/reference DOM projectors for complete v2 packages. Historical and
   standalone compatibility callers remain available until cut 7.
6. Refresh owning documentation and the approved style pin mechanically if the
   new semantic style changes only the style-contract identity.
7. Run the cheap-to-expensive validation ladder and real US/EU/KR cold replay.

## Safety net

- A malformed or ambiguous source claim fails before page mutation.
- Component variants reject missing or cross-variant slots/assets even though
  the shared registry declares their union.
- Exact locale never falls back to another locale; `shared` is the only
  permitted fallback.
- Selected composites carry one packaged asset role and must agree with the
  recorded asset key, locale, content SHA-256, and source-fragment SHA-256.
- Missing approved composites retain the complete semantic figure; they do not
  copy US artwork into another target.
- Embedded replay tests remove the source pages and replace every legacy App/
  reference projector with a failing double.
- Existing EN/FR/ES HTML and all approved composite hashes are compatibility
  baselines. EU DE/IT uses the detached review worktree only for verification.

## Non-goals

- Do not create, modify, approve, or promote PDF/AI/composite artwork.
- Do not turn LCD, troubleshooting, specification, or other editable tables
  into screenshots.
- Do not change target presentation inheritance; shared base, skeleton profile,
  and target overlay are cut 6.
- Do not delete compatibility source projectors; their final retirement and
  anti-copy/four-renderer gate are cut 7.
- Do not change public CLI flags, dependencies, workflows, phase2/Base schemas,
  live Base data, or approved reference-layout geometry/composition.

## Mandatory follow-up: cut 5B asset closure

The semantic fallback in this cut is a safe rendering path, not final artwork
acceptance for JE-1000F/EU. After this architecture PR merges, extract the
locale-matched full Overview, Operation, and Charging panels for DE/IT from the
operator-supplied EU/UK source PDF, register their source page/crop, locale,
content SHA-256, and source-fragment SHA-256, then bind them through the approved
figure manifest. The final target gate must reject `editable-fallback` or
`missing` for those required slots; only `finished-panel` or
`approved-composite` closes the debt. Tables, Warranty, LCD, Troubleshooting,
and Symbols remain live semantic HTML and are outside this raster-art closure.

## Execution outcome

- Registered both component families with variant-specific slot/asset
  validation and explicit Web, LaTeX, IDML, and Word projections.
- Whole-document assembly packages App and Reference Figure carrier flow in
  source order. Frozen Web replay succeeds with the legacy App/reference
  projectors replaced by failing doubles, proving that replay no longer scans
  the reconstructed page DOM for those semantics.
- A real JE-1000F/US EN/FR/ES bundle produced 49 pages, 9 App instances, and
  15 Reference Figure instances; 6 exact/shared manifest matches used approved
  composites. JE-1000F/EU DE/IT each produced the same five Operation panels,
  localized App/Reference semantic instances, and `3/2 JAHRE` or `3/2 ANNI`.
  JE-3000C/KR produced no App/Reference instance, so the JE-1000F contract did
  not leak into a different skeleton.
- All representative packages replayed with RST/CSV reads forbidden and with
  their packaged image hashes verified. Browser acceptance covered the US
  approved On/Off and Charging panels, EU Italian live localized composition,
  App download/add-device, and Warranty badges at desktop and 390 px. After
  lazy-load traversal, the 210-image US bundle had zero broken images and no
  component-level horizontal overflow.
- Validation passed 107 focused tests and 3780 full-suite tests (19 skipped),
  full Ruff, 62 maintainability hotspots, 1713 documentation links, the
  reference-layout pin gate, and the fixture-backed JE-1000F/US target check.
  The 5B asset debt above remains deliberately open and is not counted as final
  convergence acceptance.

## Verification ladder

1. Ruff on touched Python and tests.
2. Targeted App/reference ComponentSpec, whole-document, Web, LaTeX, IDML, and
   Word tests.
3. Full `python3 -m unittest`.
4. Full Ruff, maintainability guardrails, documentation links, and reference
   style-pin checks.
5. Fixture-backed JE-1000F/US `build.py check`.
6. Whole-document cold replay for JE-1000F US EN/FR/ES, JE-1000F EU DE/IT from
   `origin/review/JE-1000F-EU@7d764e22`, and JE-3000C KR KO, with source reads
   forbidden and packaged asset hashes verified.
7. Desktop/mobile browser assertions for App download, inline control,
   Add-device live labels, Charging/App approved composites, semantic fallback,
   broken images, and horizontal overflow.
