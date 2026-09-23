# JE-1000F US IDML/Web 基础图共用试点

Status: implementation trial

## 1. Scope

This trial covers exactly three JE-1000F/US operation components:

- `operation.main-power` / `asset:operation/main_power`
- `operation.ac-output` / `asset:operation/ac_output`
- `operation.energy-saving` / `asset:operation/energy_saving`

The source templates continue to own visible EN/FR/ES copy. The prepared bundle
and its asset manifest continue to own the resolved artwork path and hash. IDML
and Web consume the same frozen logical asset reference but keep renderer-native
layout.

## 2. Discovery

- The EN, FR, and ES operation templates already separate the three logical
  image references from visible copy.
- `HB-SPECIAL-OPERATION` already preserves artwork, ordered steps,
  prerequisites, supporting copy, language, and source reference as semantic
  component data.
- The Web renderer currently appends a locale composite for all five JE-1000F
  operation figures. CSS then hides the semantic operation stage. Replacing
  only the underlying asset therefore cannot remove the old whole-panel image.
- The IDML operation renderer already emits native text frames. Main-power and
  AC still include masks that cover labels baked into the legacy artwork;
  main-power also replaces a baked clock/duration. Those legacy masks are not
  part of a textless/base-art contract.
- All IDML artwork resolution already passes through `RenderContext` and
  `resolve_manifest_asset`; no renderer needs or may open a mutable source path.
- The target overlay already reaches Web as the resolved operation figure
  contract. A second Python `(model, region) -> operation ids` table would be a
  second policy source, so IDML must resolve the same checked-in presentation
  contract instead of repeating that table.
- Whole-document Web packaging already freezes every image as
  `metadata.asset_sha256`, and cold replay rejects a missing or hash-mismatched
  packaged file before coverage is accepted. `base-art-live-copy` coverage can
  therefore bind its sole rendered image to that existing path/hash manifest;
  no new approval or registry mechanism is needed.
- The read-only 2026-09-04 JE-1000F/US/en bundle records bundle SHA-256
  `8722f705511638f133e5e17a321e46939d5fa06b006c23a7c10928ce1de4a91b`.
  Its asset-usage manifest includes the approved main-power, AC-output, and
  energy-saving artwork and is a suitable frozen compatibility fixture.

Baseline safety net (Python 3.14, locked requirements): 144 focused operation,
IDML, Web-presentation, coverage, and ComponentSpec tests passed before edits.

Follow-up implementation plan:

1. replace the hard-coded Python target map with a fail-closed resolver over
   the existing layered presentation contract;
2. carry the resolved presentation mode through operation ComponentSpec
   metadata and the IDML compatibility payload, while keeping legacy RST
   extraction compatible;
3. make Web coverage record and validate the exact frozen asset path/hash for
   each base-art figure;
4. replay a read-only copy of the old bundle through current IDML and Web
   entrypoints, then refresh structural EN/FR/ES preview evidence;
5. run focused tests, Ruff, maintainability guardrails, document-link checks,
   package checks, and semantic assertions. Browser rendering is explicitly
   outside the evidence set after the local-file browser policy boundary was
   reached; no alternate browser URL is used.

## 3. Implementation contract

1. Add a target-overlay presentation mode named `base-art-live-copy` to the
   three JE-1000F/US operation figures only.
2. In that mode, Web renders the semantic operation stage and does not append
   the legacy locale composite. The figure retains its stable replace key,
   source-fragment hash, component ID, image reference, and visible/searchable
   copy.
3. Figure coverage reports `base-art-live-copy` only when the rendered figure
   carries that explicit mode. The JE-1000F/US coverage policy allows this
   status only for the three named slots; every other required slot keeps the
   existing finished-panel/approved-composite rule.
4. IDML recognizes the same model/region and logical component identities from
   the render context, then resolves the mode from the same layered presentation
   contract as Web. A frozen ComponentSpec may carry the resolved mode for
   replay, but it must match the current target contract; an explicit stale or
   cross-target value fails closed. IDML keeps the existing measured geometry
   and native text frames. The main-power base already contains the clock, so
   the pilot keeps that single clock and adds only the editable duration. The
   AC prerequisite mask remains until the textless candidate is
   registry-approved, making the renderer safe with both the currently frozen
   art and the candidate. It never bypasses the bundle manifest.

## 4. Non-goals

- no button recognition, anchor system, automatic leader routing, or automatic
  multilingual positioning;
- no SVG requirement or global image-format preference change;
- no change to other operation figures, products, or approved composites;
- no asset registry, source, recipe, delivery, handoff, release-collector,
  workflow, CLI, or live Base change;
- no automatic conversion of product-internal, gesture, or insertion lines.

## 5. Artwork boundary

The base artwork must not contain localized words that the templates render as
live copy. Product-internal marks, the main-power clock, and non-text
gesture/insertion lines may stay in the base artwork. A bracket or leader that a designer must move independently
must either be delivered as a separate IDML-native object under a separately
approved geometry contract, or be added during the documented InDesign handoff.
This trial does not infer movable line geometry from pixels.

## 6. Verification ladder

1. Ruff on changed Python.
2. Focused Web contract, coverage, ComponentSpec, and IDML operation tests.
3. Full unit suite and maintainability guardrails.
4. Documentation link integrity.
5. JE-1000F/US quality gate.
6. EN/FR/ES Web builds and semantic copy inspection.
7. IDML package inspection for linked frozen art and independently selectable
   text stories; native InDesign visual acceptance remains serial if the shared
   desktop instance is in use.

## 7. Verification result

- Final focused regression: 401 tests passed, 5 skipped, across Web
  presentation/contract/coverage/cold replay and IDML operation/export/asset
  manifest paths. The full suite was not repeated after the bounded follow-up.
- Ruff passed on every changed Python/test file. Maintainability guardrails
  reported zero new violations; the six stale language-literal baselines are
  pre-existing. Documentation link integrity passed with 2,037 links and zero
  broken links.
- `build.py check` passed for JE-1000F/US/en with the repository's offline
  `tests/fixtures/phase2` snapshot and an isolated staging root. The default
  local snapshot invocation cannot run because this worktree has no
  `data/phase2/Spec_Master.csv`; no live sync was attempted.
- A read-only copy of the 2026-09-04 frozen bundle was re-fingerprinted at
  `8722f705511638f133e5e17a321e46939d5fa06b006c23a7c10928ce1de4a91b`.
  All 340 manifest file records and all 57 asset-usage rows matched their
  recorded hashes.
- Current code exported and structurally checked a new IDML from that copied
  bundle. Main-power links frozen SHA `740048…b5e2`, AC links the approved old
  SHA `43a46a…1d75` rather than the unregistered candidate, and energy-saving
  links `9dd943…3a07`. The three components contain the expected native text
  frames; native Adobe acceptance remains `pending-serial-open`.
- Native InDesign review found the first base-art duration frame overlapping
  the baked main-power clock. The bounded correction keeps the approved clock
  and its vertical alignment, and moves only the editable `3s` frame to the
  measured right edge of that clock plus the existing gap. Legacy targets keep
  the movable-clock formula unchanged. The corrected frozen replay changes one
  of 215 IDML members: only the four horizontal path coordinates of that text
  frame move, by 16.043 pt. The AC and energy-saving stories remain byte-for-byte
  identical.
- The duration-only comparison also reported one overset text frame on page 6
  and one on page 16, with no missing images or fonts. It established that
  neither was caused by the bounded duration-coordinate correction, but it did
  not establish their broader origin. The subsequent Product Overview routing
  diagnosis below identified page 6 as an exporter defect and removed that
  overset. Page 16 remains one pre-existing whole-manual layout issue outside
  this trial's bounded Product Overview correction.
- The old frozen operation page also replayed through current Web IR. Each of
  the three `base-art-live-copy` slots records an exact `assets/ir/...` path and
  SHA from `metadata.asset_sha256`; cold replay independently checks those
  packaged bytes before rendering.
- Controlled EN/FR/ES fixture previews were regenerated and the complete live
  text inside all three pilot figures matched the expected localized strings.
  Browser visual acceptance was not run after the browser-policy boundary and
  no alternate URL was created.

## 8. Single-language Product Overview follow-up

### Discovery

The English-only frozen JE-1000F/US bundle has no approved reference page
plan: the registry approves the three-language `en,fr,es` document, not this
single-language carrier. The production exporter currently calls the native
Product Overview compositor only when that whole-document plan is approved,
so this otherwise governed target falls through to generic prose. The fallback
shrinks the front art, flattens callouts into ordinary tables, emits Total
Output as a second table, and can hide the complete DC Input copy in overflow.
The source RST and Manual IR retain that DC Input copy; this is an exporter
routing defect, not source loss or a designer-only refinement.

The frozen bundle already contains both required governed assets, so no asset
supplement is needed:

- `renderers/latex/assets/front_controls.png`, SHA-256
  `8cb417c0ade250d65f8ea1317c5d85cf86bc2b76f478306a6d2f5cddf13e9028`;
- `_assets/templates/word_template/common_assets/overview/right_side_ports.png`,
  SHA-256
  `b04dca41b7cc3211a30f3a3fc2b1e904c25330f28104e4338a8ed67a11378011`.

### Bounded implementation plan

1. Reuse the existing target-independent Overview instance and projection as
   the eligibility contract. A Product Overview page uses the native editable
   compositor when its model/region resolves exactly one registered instance,
   its source stem matches that instance, and its language is declared for
   both views. Whole-document approved-reference status remains unchanged.
2. Preserve generic prose for targets or source pages with no matching
   Overview instance. A registered target whose matching page requests an
   undeclared language fails with an explicit contract error instead of
   silently using the wrong geometry.
3. Add a regression through the real `export_idml.main()` entrypoint with no
   reference plan, then assert that the output contains governed linked art,
   native leaders and editable callout stories rather than overview tables.
4. Replay the read-only frozen bundle into a new output directory, retaining
   the main-power duration correction, and compare the new package to the
   duration-fixed baseline. Native GUI inspection remains with the serial
   operator.

Non-goals: do not approve a new whole-document reference plan, copy model
logic into the exporter, add or register assets, rasterize the page, alter
non-matching targets, modify live data, or repair unrelated pages.

### Result and native acceptance

The exporter now routes a Product Overview source page to the native component
when the registered model/region instance owns that source and declares the
requested language. This does not create or mutate a whole-document reference
plan. The real-entrypoint regressions cover the English-only no-plan replay,
unregistered fallback, undeclared-language failure, and the existing
single-art compatibility path.

The final-code frozen replay is:

- `je1000f-base-art-preview/old-frozen-replay/idml-overview-fixed-v2/manual_je1000f_us_en_old_frozen_replay_overview_fixed_v2.idml`;
- SHA-256
  `427302a0f8b1841d3c77f90c72e5db6f67da0d4c18b4763661f1d5f966123443`.

Its page-6 spread contains two governed linked graphics, 32 native leader
lines, 18 editable Overview stories, and zero tables. The full DC Input PV and
Car values are present, and Total Output is a native label frame. Its 231 ZIP
members are content-identical to the package opened for native review; the
outer ZIP hashes differ only because the archives were written at different
times. The main-power duration story and corrected bounds remain unchanged.

InDesign inspection at 126% whole-page view and 200% detail view accepted the
page-6 layout: both front and side views, native labels and leaders, complete DC
Input values, and the native Total Output annotation render correctly. Native
preflight reports no page-6 overset and no missing images or fonts. This is a
bounded Product Overview acceptance, not whole-manual acceptance: preflight
still reports one overset text frame on InDesign page 16, which remains
outside the scope of this change.

## 9. Single-language LCD Display follow-up

### Discovery

Native inspection of InDesign page 7 at 200% found a geometric defect that
preflight does not report: the Wi-Fi Off and Bluetooth Off baselines and
descenders press against their bottom rules, and the final lines in Quiet
Charging, Charging Plan, Self-powered, and TOU similarly touch or overlap the
row separators. The first table also leaves excess space after its final UPS
row, while the continuation table crosses its intended page boundary. The LCD
hero artwork and all source copy are present.

The exported first LCD table confirms the build-side cause. Because the
English-only frozen bundle has no whole-document approved page plan,
`lcd_page_data()` does not apply the registered JE-1000F/US LCD component
profile. Its rows therefore have no governed height attributes, use the
zero-inset standalone English cells, and still inherit the standalone terminal
fill. The approved reference contract already owns the row presentation,
per-language physical row heights, icon size, source-page identity, and
language set; this is a component-routing gap, not missing source data or an
image problem.

### Bounded implementation plan

1. Resolve the LCD component profile independently from whole-document plan
   approval only when an approved registry entry matches model/region, the
   actual LCD source page is declared by that contract, and the requested
   language belongs to the contract. Do not activate or synthesize the rest of
   the page plan.
2. Preserve the current ungoverned fallback for targets or source pages with no
   registered LCD ownership. When a matching registered LCD source requests a
   language the component does not declare, preserve the generic fallback and
   never borrow another language's registered geometry.
3. Add a real `export_idml.main()` no-plan regression that checks the packaged
   table rows use the registered physical heights and that the first and
   continuation panels close within their owned frames. Geometry assertions,
   rather than preflight or text-presence alone, are the acceptance gate.
4. Replay the same read-only frozen bundle to a new `lcd-fixed` directory and
   prove that the Product Overview package members, the corrected `3s` story,
   frozen artwork links, and source text stay unchanged. Native GUI inspection
   remains with the serial operator.

Non-goals: do not change LCD copy or source-table data, shrink type, rasterize
the table, change the Product Overview or operation components, repair page 16,
activate a whole-document reference plan, write live data, commit, or push.

### Result and native acceptance

The final-code replay is:

- `je1000f-base-art-preview/old-frozen-replay/idml-lcd-fixed-v3/manual_je1000f_us_en_old_frozen_replay_lcd_fixed_v3.idml`;
- SHA-256
  `9a7f1b8675e2ffc055b9d797ebeeefec80073433b2d174394fa1a02e1c43c5bf`.

Its 231 package members and Manual IR sidecar are content-identical to the
native-reviewed `lcd-fixed-v2` replay; only ZIP timestamps make the outer
package hashes differ. The compatibility follow-up preserves generic LCD
fallback for undeclared languages without changing this accepted EN package.
Against the accepted Product Overview package, exactly three members change:
the LCD host story and its first and continuation table stories. The Manual IR
sidecars are byte-identical, so the 26 source rows and all other source content
are unchanged. The first table now has seven fixed contract rows with physical
heights `19.95`, `21.49`, `40.13`, `39.65`, `45.51`, `68.08`, and `45.967` pt;
the continuation has 19 content-fitted governed rows. Product Overview,
operation `3s`, frozen artwork links, spreads, and every non-LCD story remain
byte-for-byte identical.

InDesign accepted printed page 04 / InDesign page 7 at 126% whole-page view and
200% upper/lower detail views: Wi-Fi, Bluetooth, Quiet Charging, Charging Plan,
Self-powered, and TOU copy no longer touches the separators; UPS is complete
and the excess bottom strip is gone. Printed page 05 / InDesign page 8 was
checked at 200% in upper, middle, and lower sections: the continuation closes
with complete Remaining Discharge Time copy and an intact rounded bottom edge.
All 26 source rows render as controlled display numbers through 25, with the
high/low-temperature rows sharing number 22 as specified. Native preflight
still reports only the existing overset text frame on InDesign page 16 and no
new LCD error. This is bounded LCD acceptance, not page-16 repair.

## 10. Body pages 11, 13, and 15 follow-up

Native review exposed three independent renderer defects while the frozen RST,
data, and artwork remained correct. The long no-plan prose story let the
Operation-only `48.2 pt` inter-section calibration leak onto the Emergency
Charging body before the solar heading. Storage and Troubleshooting then shared
the final generic frame even though the complete editable F0-FE table is an
indivisible anchored component, leaving it overset with no continuation frame.
Finally, the no-plan Warranty boundary bypassed semantic transformation and
printed the warranty container JSON instead of invoking the existing lead,
section, and years renderers.

The bounded repair keeps the established main-power `3s`, Overview, and LCD
work unchanged. It limits the Operation calibration to the extractor's explicit
`body_operation_inter_section` role; resolves the already approved, hash-pinned
Storage + Troubleshooting composition as a component-only route (never as a
whole-book page plan); and transforms the isolated Warranty blocks before
emission. Acceptance requires all eleven fault codes, six warranty sections,
editable 3/2-year badges, no visible semantic JSON, and no source/data/art
change. A changed page count is reported rather than hidden by shrinking text.

### Result and native acceptance

The final frozen replay is:

- `je1000f-base-art-preview/old-frozen-replay/idml-pages-11-13-15-fixed-v3/manual_je1000f_us_en_pages_11_13_15_fixed_v3.idml`;
- SHA-256
  `a65d217ca36c6c64b67d15c7ef66e7aae48e9f80e9fc655f5ccd7b179f33debf`.

Printed page 11 keeps the accepted Emergency Charging rhythm without the
Operation-only `48.2 pt` gap. Printed page 13 / InDesign page 16 now gives the
car-charging CAUTION its own leading region above Storage. The complete
long-term charge/discharge paragraph remains in the Storage story, while the
editable Troubleshooting table closes with all codes from F0 through FE.
Printed page 15 / InDesign page 18 renders all six Warranty groups, including
editable 3-year and 2-year badges and Interpretation Rights. The final panel
reclaims `5.4932 pt` of unused bottom height, increasing the measured gap to
the page-number baseline from about `2.5 pt` to about `8 pt`, without changing
type size or removing copy.

InDesign review at 200% accepted the content, order, panel closures, and footer
clearance. The whole-document Basic preflight reports **no errors**: the prior
Storage overset is gone, with no missing images or fonts. The component-only
resolver also rejects unsupported schemas, registry/payload target mismatch,
escaping paths, non-list page declarations, and selected pages whose declared
language differs from the requested language. It does not activate a
whole-document reference plan or write any live source data.

## 11. Car-charging Vehicle label follow-up

The frozen `08_charging_methods.rst` correctly keeps `Vehicle` and the
sold-separately note as a two-line block immediately after `car_charge.png`.
The approved reference path already promotes that image and adjacent block to
the editable `charging_car` figure, but the single-language replay previously
skipped promotion because it has no whole-document approved page plan. Generic
prose therefore printed both lines below the image.

The component-only resolver now exposes the exact, approved, hash-pinned
Charging Methods ownership alongside the Storage and Warranty ownership. Only
that registered source page reuses the existing figure promotion: `Vehicle`
lands in its editable frame above the in-vehicle socket detail, and the note
lands in the editable white rounded strip at the upper right of the gray
panel. The source block, artwork, copy, physical pagination, and whole-document
plan status are unchanged.

InDesign accepted the 21-page replay at native scale. Printed page 12 / InDesign
page 15 matches the original placement, the panel is complete, and the footer
remains clear. Whole-document Basic preflight continues to report **no
errors**. This acceptance preserves the page 11, 13, and 15 corrections from
the preceding round.
