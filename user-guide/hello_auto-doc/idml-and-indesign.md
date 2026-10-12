# Workflow guide: IDML, InDesign handoff and approved reference layouts

Part of the [workflow guide](../hello_auto-doc.md); its index lists the other topics.
Add new notes for this topic here, not to the hub.

InDesign export has two handoff modes. The default production path creates the
component-heavy native/editable IDML from one deterministic `manual.ir.json`
and the shared layout-token contract; `latex_page_plan.json` remains a
same-source trace. Flow mode (`python3 build.py idml --idml-mode flow ...`)
creates semantic Markdown plus an editable continuous-story IDML, style map,
source trace, and asset manifest for a designer-owned template workflow. Both
are generated outputs, never new content sources.

Document-profile Markdown preserves a plain, three-item inventory such as the
JP inbox as its authored text table and following notes. It does not require
the images and tip table used by illustrated inbox cards. Illustrated cards
retain their image/label/tip validation. The prepared-bundle IR adapter preserves
complete signal-word definition tables as tables, including the JP definitions
of warning, caution, note and tip; individual warning callouts retain their
existing validation.
The JP symbols page's boxed introductory title and both paragraphs are also
preserved as editable IDML text. The previous single skipped-block debt is
closed for this runtime source; this does not replace native InDesign checks
for page layout, overset, fonts and links.

The measured JP fallback now lets the final operation table flow into the
existing page chain and sizes specification shells from their actual cells.
The `℃` character stays unchanged and uses a bundled font containing its glyph.
After `build.py idml`, still run native save/reopen and inspect the exported
PDF: an IDML with no overset can still have missing glyphs at PDF export.
See the [JE-1000F JP repair record](../../code-as-doc/reviews/je1000f_jp_native_overflow_2026-09.md)
for the current acceptance state and remaining content debts.

For a single-language family such as `configs/config.ja.yaml`, you do not need
to repeat `--lang ja`: `build.py idml` forwards the config's sole language to
the exporter. On a multilingual family, add `--lang` when exporting only one
language; otherwise the existing whole-family/default behavior is preserved.

Production mode also checks assembly coverage. Current source pages are mapped
to target-neutral semantic roles before composition. If the command prints an
`assembly coverage` warning, the listed new or renamed page was preserved with
the ordinary editable-prose fallback, but it has no reviewed assembly role yet.
Update the shared role table and its regression test before release; do not add
a model/region-specific filename exception.

The BP family now has three exact-target configs. `JBP-2000B_US + us-merged`
selects `configs/config.bp-us.yaml`; `JBP-2000B_EU + eu-merged` selects
`configs/config.bp-eu.yaml`; `JBP-2000B_JP + jp-ja` selects
`configs/config.bp-jp.yaml`. The JP config has `family_default: false`, so MAIN
JP remains on `configs/config.ja.yaml`. The EU target contains
`en/fr/es/de/it/uk`, where
`uk` is Ukrainian, not a UK-market selector. It uses the paired host display
name `Jackery Explorer 2000 Plus`; only the US target uses
`Jackery HomePower 2000 Plus`; JP uses
`Jackery ポータブル電源 2000 Plus`. Keep those distinctions in target
substitutions and assets, not in page-renderer conditions. The EU and JP IDML
plans remain candidates until their separate promotion workflows approve them.

The production handoff's `production/source_trace.json` also records the
`skipped_raw_blocks` count from `manual.ir.json`. For ordinary/fallback targets
this remains report-only. For an approved-reference target, the approved plan
freezes `idml_contract.max_skipped_raw`, and production export stops if the
current count exceeds that baseline.

Strict Manual IR validation also stops on an unregistered build, manifest, or
page language. Approved-reference production runs this check automatically;
ordinary/fallback IDML keeps the existing permissive behavior. Add a language
to the shared registry instead of relying on the English fallback. Registered
aliases such as `jp` and `pt_br` are accepted.

For Japanese, Korean, or Chinese editable text, the IDML exporter writes
explicit script-aware font runs instead of letting those characters inherit
Gilroy. Korean uses the bundled SIL-OFL `NanumGothic` face. Japanese and
LaTeX use the bundled static TrueType `HBManualSansJP-Regular.ttf`
(`HB Manual Sans JP (OTF)` in InDesign, OpenTypeTT). Its project-unique family
and PostScript identity prevent a host `Noto Sans JP (OTF)` from shadowing the
packaged face after close/reopen. The `(OTF)` suffix is InDesign's normalized
CJK family spelling, not a dependency on a host CFF font; the same
hash-verified face travels with the designer package. Chinese continues to
use the separate `idml_font_family_cjk` renderer token. Font routing is not a
layout parameter, so changing a portable font does not require a
reference-layout rebind when geometry, content bindings, and composition stay
unchanged.

Editable symbol runs are cross-platform too. The `※` reference mark is a native
IDML vector, so reopening the saved INDD does not depend on a document font.
Warranty-year `3` / `2` values remain editable white ASCII digits inside native
black circular badges, preserving the approved appearance without relying on
host-specific `❸` / `❷` glyphs. The year unit and the warranty subtitle below
it share one component-owned x anchor, so `Standard Warranty` and
`Extended Warranty` stay left-aligned with their localized `YEARS` labels.
`Noto Sans` owns ordinals and subscript digits; `Noto Sans Symbols` owns DC and
circled labels 1-20; `Noto Sans Symbols2` owns the filled-circle fallback and
editable `☎ / ✉ / ◉` contact icons. Final assembly for
both approved-reference and target-assembly targets uses native vector heading
markers, and LCD labels 21-27 serialize as `(21)`-`(27)`. The exporter copies
the declared SIL-OFL files beside the IDML under `Document fonts/`, so raw
designer packages no longer depend on `Segoe UI Symbol`, `Yu Gothic`, or
`Noto Sans KR` being installed on the opening host.

The exporter also budgets Japanese, Korean, and Chinese wrapping by Unicode
East Asian Width instead of treating every character as a 0.52-em Latin
glyph. Fullwidth characters receive a full-em budget while ambiguous-width
characters stay narrow so CI and the design Mac agree. This reduces late
overset surprises, but it is still a deterministic estimate: the designer
must complete native InDesign preflight and page parity before release.

The production Meaning of Symbols page also remains editable. Its WARNING,
CAUTION, NOTE, and TIP badges use a linked white warning icon plus ordinary
InDesign label text, rather than a flattened language-specific badge image.
The safety-tail panels use the approved dark triangle, and the symbol-grid
icon size and columns come from shared layout tokens, so English, French, and
Spanish follow the same component definition.
The symbol-page copy and TOC language headers come from the shared language
registry's IDML language packs. Reference-bound spacing override rows are read
for the registry's `layout_override_languages()` set — the governed languages
plus lines in active layout tuning, currently adding Korean — while
`governed_languages()` (English, French, Spanish) still gates
approved-reference flow behavior such as fixed heights and reference offsets.
A tuning language's override rows take effect as they land, but its flow
behavior stays measured/fallback until its reference layout is approved, so
adding translation metadata still does not silently apply an unapproved
physical layout.
The LaTeX safety dispatcher uses the registered warning label for every
language passed to `HBApplyLang`, including the long-tail languages, instead of
silently retaining `WARNING`.

In production IDML operation panels, Prerequisite, standby, On, and Off are
separate unlocked text frames placed above the linked illustration. Designers
may select, edit, and move each frame for alignment without editing the image;
copy corrections still belong in the source and must be rebuilt, apart from
the explicitly approved target-scoped App display-variant binding described
below. Energy Saving
also exposes its two grey-box paragraphs, On/Off, 3s, and action instruction as
top-layer frames. LED exposes its grey-box lead, 1/2/3, SOS, and three step
instructions separately; their linked art and native shape underlays remain
below the text. LCD SCREEN likewise exposes two state, six action, and six
description frames above its left-side illustration and grid. KEY COMBINATION
uses linked button/clock graphics while every header, caption, plus sign,
duration, operation, and function remains a separate movable text frame across
English, French, and Spanish. One shared layout-token style owns its geometry
and typography; only the governed French/Spanish height, indent, and gap values
are locale overrides. The renderer emits all of those text frames last so they
stay above the artwork and remain individually editable.

Approved Charging figures use the same top-layer rule for AC and vehicle
captions. The exact App reference composition applies to the English, French,
and Spanish App Setup sources: Store/QR and result-screen crops remain linked
art, while step numbers, pairing-panel labels, and notes are separate movable
text frames. Pairing-panel labels come from the Product Overview's stable
`main_power`, `dc_usb`, and `ac` slots, then use the reviewed per-language App
display variants stored in the approved plan; they are not guessed from the
next paragraph. Only an exact duplicate three-line label block is removed, so
Spanish step 2.3 remains ordinary editable prose. The shared `AppFigureStyle`
owns overlay sizing for all three languages, and approved builds fail when a
required source role, display variant, asset, or style token is missing. These
presentation variants do not change the source/IR content hash; every label
remains unlocked and editable in the top layer.
The same approved plan explicitly lists these source pages under
`idml_contract.editable_components.app_add_device.page_owners`. That list
drives both hidden App-asset packaging and production composition, so a page
that is absent, belongs to another language, or comes from a draft contract
cannot silently enter the reference layout.

For the approved-PDF replica of `JE-1000F / US / en+fr+es` (方案 2), production
mode must resolve the
[`reference layout registry`](../../docs/renderers/contracts/reference_layout_registry.json)
and the
[`JE-1000F US V2.0 contract`](../../docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json).
That contract is bound to the 58-page
`Jackery Explorer 1000 User Manual V2.0-2026-06-05.pdf` with SHA-256
`e72b1ba01882062e261b17d5ba54a2f7c3099e5ba531a6428be13888641083f2`
and `368.787 × 524.692 pt` page geometry. The physical structure is front
matter 1–3, English 4–21, French 22–39, Spanish 40–57, and back cover 58. Its
52 source references are bound by composition across all 58 pages. Missing or
mismatched enforced content/assembly/style identity, source/hash drift,
unclassified prose without an exact exception, or page-count drift is a hard
failure; the build must not silently use fuzzy PDF matching. The v2 contract
keeps the global phase2 snapshot hash as non-blocking provenance, so unrelated
table refreshes do not invalidate an unchanged target manual.
The same rule applies if the contract file is still approved but its registry
entry is missing: the build stops and names the orphaned contract. Only a target
with no approved contract may use measured-LaTeX fallback pagination.

The English single-language manual `JE-1000F / US / en` is a pilot component
target of that contract: when its source pages match the approved contract,
`build.py idml` prints `COMPONENT TARGET OK (pilot)` and composes the registered
LCD, Overview, Charging, Storage+Troubleshooting, Warranty and main-power pages
instead of the measured LaTeX layout. If the log shows
`COMPONENT TARGET INERT`, the content differs from the reviewed pages (each
drifted page is listed); the IDML falls back to the ordinary layout. Do not edit
hashes by hand: refresh the contract with the rebind commands below after
review. Details:
[`idml_component_targets.md`](../../code-as-doc/dev/idml_component_targets.md).

When a source refresh changes mutable style/provenance identity without changing
the approved content or semantic/physical assembly, use the rebind command
instead of editing one hash or removing the registry entry. It is a dry-run
unless `--write` is present:

```bash
python3 -m tools.reference_layout_rebind \
  --plan docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json \
  --manual-ir <manual.ir.json>
python3 -m tools.reference_layout_rebind \
  --plan docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json \
  --manual-ir <manual.ir.json> \
  --write
```

For a read-only summary of all registered contracts, run
`python3 -m tools.reference_layout_rebind --all-registered --manual-ir
<manual.ir.json>`. Batch mode never writes; keep `--write` limited to an
explicit single-plan command after review.

For a v2 plan, the ordinary command validates that semantic content, assembly,
source order, page languages, and physical composition remain unchanged. It
refreshes only the mutable non-content identities and every page's source
digest, then atomically replaces the plan. Review the dry-run summary and Git
diff before building. A v1 plan has no assembly pin, so v1-to-v2 migration is
an identity change and cannot use the ordinary route.

A content/assembly change, including v1-to-v2 migration, is rejected unless an
operator has first verified the final Manual IR's source-reference order,
language mapping, `skipped_raw` allowance, semantic page roles, physical page
count, and composition map. After recording that decision, use the explicit
approval route in dry-run mode first. The existing flag name is retained for
CLI compatibility:

```bash
python3 -m tools.reference_layout_rebind \
  --plan docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json \
  --manual-ir <manual.ir.json> \
  --approve-content-change \
  --approved-by "<operator>" \
  --approved-at "<RFC3339>" \
  --approval-method "<recorded review evidence>"
# Repeat the same command with --write only after reviewing the candidate.
```

The three approval fields are mandatory and are stored in the contract.
`--all-registered` cannot approve identity changes or write plans. Source order,
languages, and physical composition remain immutable even on the approved
identity-change route. v1 migration does not auto-populate
`allowed_unclassified_source_refs`; unclassified pages require a separately
reviewed layout decision.
The layout-parameter identity follows ordered `key`/`value`/`unit` semantics;
line-ending, blank-row, and comment-column edits do not create contract drift,
but a real token value, unit, or order change does.

The role boundary is strict:

- source owners correct copy, translation, specifications, legal text, table
  structure, and asset identity in Feishu/source tables, templates, review/TM,
  or the asset registry, then rebuild;
- the build creates native text, headings, tables, callouts, Product Overview,
  and back-cover objects/stories; illustrations remain governed linked assets;
- the designer may adjust frame geometry, explicit page breaks, asset fitting,
  and limited tracking, but may not turn INDD into a second content source;
- the approved reference PDF may be used only on a non-printing comparison
  layer. Visible whole-page body/back-cover PDF placement is forbidden; a
  contract-approved finished-art front cover is the narrow exception.

Use `asset:<asset_key>` (for example `asset:operation/ac_output`) for governed
illustrations. Only approved PNG/JPG/JPEG/SVG/PDF exports matching model,
region, and language may resolve. The `.ai` file is an immutable source archive,
not a renderer fallback. Missing, ambiguous, quarantined, stale, or
hash-mismatched assets block assembly. Keep `asset_usage_manifest.json`,
`asset_registry_snapshot.csv`, and `bundle_manifest.json`; a `legacy-path`
entry alone does not prove that an asset is governed.
The US front-panel extension is the
`overview/je1000f_us/front_controls` override behind the shared
`overview/front_controls` key. It resolves only for JE-1000F/US; the common
Word-template PNG remains the base asset for other targets.
The grey pairing panel is the approved
`controls/je1000f_us/network_pairing_panel` recipe export. Because the reviewed
App promotion binds the complete recipe SHA, changing that recipe requires a
new reviewer decision and a passing `asset-check --json`; operators must not
patch the hash alone.

The provisioned design Mac runs `tools/indesign_finalize.py` to create the INDD
and PDF, with zero overset/missing-font/missing-glyph/bad-link findings and
PDF/X-4 using `Japan Color 2001 Coated` / `JC200103`. The finalizer scans the
exported PDF for visible `U+FFFD` and `.notdef` glyphs, including text retained
inside placed PDF graphics; rasterized or outlined art remains part of visual
review. It then runs
`tools/idml_pdf_parity.py` against the approved PDF (the historical
`--latex-pdf` flag name does not mean the newly built LaTeX PDF here) and the
approved contract. All 58 pages are compared at 300 dpi as fixed
`1537 × 2187` RGB rasters with the approved ICC profile, 1 px blur, per-page
RGB MAD `≤ 0.008`, changed-pixel ratio `≤ 0.040`, and changed-channel threshold
`16`. Any failing page fails the run; averages cannot hide it.

Keep `Document fonts/` beside the generated INDD. Before exporting the final
PDF, the finalizer saves the INDD, closes it, reopens it, recomposes it, and
rechecks fonts, overset stories/cells, links, page count, and story count. The
`indesign-preflight/v2` report records this under `post_reopen`; a first-open
green result is no longer sufficient.

For Japanese documents the portable-font rebind preserves each character's
declared Regular/DemiLight/Medium/Bold face; an unavailable requested face stops
finalization. The report records counts under `portable_font_rebinds[].style_counts`.
Keep frozen inputs and native evidence outside the target build directory before
running another `build.py idml` or `check`, because preparation cleans that target.
The [JP twelve-page acceptance record](../../code-as-doc/reviews/bp_jp_r3c_native_validation_2026-09.md)
shows the package hashes, actual native results and explicitly retained debt.

For a multi-target design handoff, run
`python -m tools.indesign_finalize --jobs <manifest.json>` with one explicit
PDF preset, output intent, output condition, and PDF/X level on every job.
The batch writes an aggregate report, isolates one failed InDesign job from
the others, and lists IDML directories whose InDesign package is incomplete.
Jobs with the same `application` value are finalized sequentially inside one
InDesign/ExtendScript invocation; each document still gets its own INDD, PDF,
preflight report, close step, and failure result.

Delivery requires all 52/52 source identities, all used asset hashes/scopes,
58-page geometry, native-object/no-whole-page-shortcut checks, preflight, print
contract, and every page-level visual check to pass. The latest parity report
must say `accepted=true`. This guide describes that acceptance contract; it
does not claim the current IDML/INDD/PDF has already passed. Copyable commands
are in the
[`Approved-PDF native InDesign replica` section](../../code-as-doc/build_doc_guide/idml-reference-layouts.md#approved-pdf-native-indesign-replica-option-2).

Write the finalize and parity artifacts **next to the production IDML**, in
`docs/_build/<model>/<region>[/<lang>]/idml/` — `<stem>.indd`,
`<stem>_indesign.pdf`, `finalize_report.json` and `parity_report.json`. That is
the only location `release-manifest` looks in, so artifacts left in a scratch
directory are simply not recorded. (The second-host verification run in
[`indesign_second_host_runbook.md`](../../code-as-doc/dev/indesign_second_host_runbook.md)
is the deliberate exception: it writes to a temp dir precisely because it must
not touch the repo.) The manifest's `indesign_package` section then records the
IDML, INDD, InDesign PDF, handoff zip and both reports with sha256, plus the
preflight numbers and the parity verdict; `complete` is true only when the
IDML, INDD, InDesign PDF, handoff zip and finalize report are all present. An
automated publish with no finalize run records what exists and marks the rest
absent rather than failing. The JSON keeps native page/overset counts under
`indesign_package.preflight`; the CSV mirrors them in
`indesign_preflight_page_count` and
`indesign_preflight_overset_stories` for dashboards. Blank means “not reported”
and `0` means a verified zero, so a partial legacy report cannot look clean by
accident.

Use `python3 build.py idml --idml-mode both ...` when design also needs the
paired flow handoff folder: it keeps the production IDML and adds
`production/manual.production.idml`, the flow folder,
`missing_assets_report.md`, `designer_checklist.md`, and `layout_feedback.md`.

For reference-layout-registered targets, the IDML command's default
`--source auto` resolves to the frozen `review-asis` bundle so production and
flow use the approved page assembly. Explicit `runtime`, `review`, or
`review-asis` remains unchanged; unregistered targets still default to
runtime.

`review-asis` preserves the committed review page bytes, but the prepared
bundle always applies the target's current language registry. If a historical
merged review index still includes a language that this model no longer ships,
the build removes those out-of-scope page includes and their generated page
copies by their explicit `\HBApplyLang{...}` declarations, rejecting paths
that escape the generated bundle, and trims the matching block from shared
multi-language pages. A fully recognized `English / French / ...` language
catalogue on that shared page is trimmed to the same scope. It does not edit
`docs/_review`, infer language from filenames or translated headings, or relabel
the stale page as another locale.

The merged Web manual turns that resolved language order into a top jump bar.
Each pill uses the language's native name and jumps to the first page of that
language; the old plain-text language catalogue is therefore not shown twice.
This is automatic for any whole-document Web build with at least two declared
languages, so a new target does not add model-specific HTML or CSS. On phones
the pills scroll inside the bar without widening the page; print output hides
the bar. A single-language manual keeps its previous output unchanged.

Publish queue runs use `--idml-mode both` automatically and upload a single
designer delivery zip (`manual_..._publish_<version>_handoff.zip`) instead of
the bare `.idml`: it bundles the production IDML with its image links
rewritten to a packaged `Links/` folder, the flow outputs, the handoff
reports, a fonts manifest, the bundled SIL-OFL fonts under `Document fonts/`,
and the reference PDF; the zip's knowledge-base link is what lands in the
queue row's `idml_file` field.
If `AUTO_MANUAL_LOCAL_GILROY_DIR` is set on the build machine, licensed Gilroy
files from that folder are added to the same directory. Gilroy remains a
commercial operator-provisioned font; the repository does not redistribute it.
The checklist opens the versioned IDML at the zip root. Package link failures
are reported in `missing_assets_report.md`; unresolved semantic source/flow
references remain available separately in `source_asset_resolution_report.md`.
Before handoff, extract the final delivery ZIP, confirm its package link report
has zero missing assets and that the generated reference crops plus pairing
panel are under `Links/`, then run native InDesign finalization on that exact
root IDML. A valid ZIP or structural IDML check is not native preflight.

When a queue row carries `Git_ref`, the worker uses the current `origin/main`
for build code and overlays `docs/_review/` from that review ref. This keeps
merged renderer fixes in Publish output even when the worker's local `main`
branch is stale.

JP IDML screenshot checks: safety icons must appear as images, energy-saving
thresholds must show their resolved values, and recovery conditions must stay
in the correct table column. Literal `.. image::`, `:alt:`, `:width:` or unresolved
substitution names are failed output, even when the package has no overset.
Keep the package version with each screenshot; see the
[JP review record](../../code-as-doc/reviews/je1000f_jp_native_overflow_2026-09.md).

JP IDML uses its manifest-declared Japanese TOC payload with dynamically
collected headings; the TOC is excluded from non-IDML builders. Its
`front_matter_roles: ["cover", "toc"]` declaration controls both the TOC slot
and fallback folios, so the first body page is 01. An explicit renderer page
plan still owns its physical folios. Front-matter metadata alone does not
create a reference-layout sidecar. Final story reflow and TOC page accuracy
must be checked in InDesign screenshots of the identified candidate package.

The six approved JE-1000F/JP illustrations resolve through scoped registry
overrides. Product engravings and logos remain; added manual annotations are
removed. Other targets retain their existing asset resolution. Local approved
files are usable for review while dedicated asset-Base archival remains
pending write permission; local hash checks do not prove online archival.

`build.py idml` now prints `[export-idml] STORY SPANS`: each prose story's
allocated page chain, with the height estimate shown in brackets whenever the
two differ. A story allocated more pages than its content composes into is
what produces blank body pages, so read this line before asking for another
screenshot round. Under the measured-LaTeX fallback plan an unmatched source
between two anchors no longer donates its pages to the preceding story, and
Warranty and App Setup are kept in separate linked chains so the App section
starts its own page instead of continuing under the warranty tail.

Under a measured fallback plan a story's chain is never longer than its own
content needs. LaTeX and the IDML writer compose at different densities, so an
anchor distance that is longer than the composed section used to leave trailing
empty frames — blank body pages. Targets with an approved reference or target
assembly plan are unaffected. When a section now runs out of room, InDesign
marks it as overset rather than printing a blank page; that is the intended
trade, so check the red overset markers after a rebuild.
Prepared-source integrity: a declared page include that is missing or is not a
file now stops source discovery with the index and source path. Registered
prose macros need complete arguments; unsupported content around recognized
macros increments `skipped_raw` and fails strict Manual IR validation. A valid
macro no longer hides adjacent unsupported copy. Existing language/tag
selection and successful payload formats remain unchanged.

IDML handoff validates the source `manual.ir.json` before copying artifacts or
writing reports. Missing IR is explicitly unavailable; corrupt IR is an error,
not a zero-skipped report. This IDML integrity path remains on its existing v1
producer and does not by itself consume the Web whole-document v2 flow or
certify native JP layout. See the
[shared-source plan](../../code-as-doc/dev/latex_indesign_same_source_plan.md) for remaining consumer and parser boundaries.
