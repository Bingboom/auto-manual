# Hello Auto Doc

Updated: 2026-08-16

This file replaces `Template_maintenance_and_using_guide.md`.
It documents the current build layout, maintenance rules, the review bundle layer under [`docs/_review/<model>/<region>/`](../docs/_review), and the current review-first publishing flow.
It is the current workflow and editing-surface guide.
It is not the full maintainer command reference; use [`../code-as-doc/build_doc_guide.md`](../code-as-doc/build_doc_guide.md) for command semantics.
For the current JP / US family difference boundary, use [`../code-as-doc/manual_family_guide.md`](../code-as-doc/manual_family_guide.md).
For onboarding new external Markdown manuals into templates, use [`../code-as-doc/dev/manual_template_intake_checklist.md`](../code-as-doc/dev/manual_template_intake_checklist.md).
For Codex-assisted Markdown-to-template intake, use [`../.agents/skills/markdown-rst-template-intake/SKILL.md`](../.agents/skills/markdown-rst-template-intake/SKILL.md).
For Codex-assisted TM-first manual rewrite or translation that must preserve Markdown structure, use [`../.agents/skills/manual-rewrite-with-tm/SKILL.md`](../.agents/skills/manual-rewrite-with-tm/SKILL.md).

---

## 1. Environment Setup

Before running any build, review, check, or publish command, prepare the local environment in the repository root.

### 1.1 Python Environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

The dependency install step is mandatory.
Do not skip `python -m pip install -r requirements.txt` or `python3 -m pip install -r requirements.txt` when preparing a fresh environment.

To reproduce the exact environment a release was built with (or to avoid
rendering drift on a long-lived checkout), install from the pinned snapshot
instead: `pip install -r requirements.lock`. Regenerate the lock only on an
intentional dependency change (`pip freeze --exclude-editable`, keep the file
header). `python build.py doctor` prints the effective toolchain versions
(Python packages, xelatex, pandoc, InDesign when present), and every release
manifest embeds the same record under a `toolchain` key — a published PDF can
always name the environment that produced it.

For fixed-layout PDF work, edit the shared LaTeX component or its
data/layout_params.csv values instead of drawing borders directly in page
RST. Titles (H1 bars), capsule subbars, safety boxes, FCC panels, inbox
cards, tip strips, rounded table frames, symbol tables with controlled
symbol continuations, app steps, and app notices are reusable objects; page
RST supplies their text and image arguments. Body WARNING, CAUTION, NOTE, and TIP label/body tables are mapped
to the same rounded callout family automatically for LaTeX PDF output.
The visible label itself always comes from the page RST / source table. The
renderer does not change `TIP` to `TIPS` (or create any other fallback word),
and a missing label stops the LaTeX/IDML handoff instead of silently inventing
copy.

### 1.2 External Tools

- PDF export requires `xelatex`.
- Word export requires `pandoc` on macOS / Linux and on non-Word-COM paths.
- If the target uses a Word reference template such as the bundle flow, install `pandoc 3.9.0.2` or newer. The bundle exporter now auto-selects a compatible installed `pandoc` when multiple versions are present, and older versions can emit an invalid `/word/media/` content-type override that makes Microsoft Word repair the generated `.docx`.
- The Python dependencies in [`requirements.txt`](../requirements.txt) include the Sphinx theme and build libraries used by the current workflow.

If you want Gilroy only on your own machine for PDF preview, set `AUTO_MANUAL_LOCAL_GILROY_DIR` to the extracted font folder before running `pdf` or `publish`.
That folder must contain `gilroy-regular-3.otf`, `gilroy-bold-4.otf`, `Gilroy-LightItalic-12.otf`, and `Gilroy-ExtraBoldItalic-10.otf`.
If the env var is not set, or the folder is incomplete, the build keeps the normal shared fallback fonts and CI does not change.

If you only need the exact command semantics for one export path, use [`../code-as-doc/build_doc_guide.md`](../code-as-doc/build_doc_guide.md) as the authoritative reference.

### 1.3 DingTalk Wukong MCP Bridge

The version-controlled Wukong bridge lives at
[`agent/wukong-bridge/`](../agent/wukong-bridge). Do not maintain a second
untracked source copy under a home-directory `wukong-bridge` folder. Point the
MCP registration at the checked-in `server.py`, keep authentication in the
external `lark-cli` profile, and keep runtime jobs/exports under the external
state directory described in the bridge README.

For KR source intake, Wukong must pass an explicit sibling target to both
`intake_stage` and `intake_commit`. Staging validates canonical English source
text and the sibling identity
`Page + Row_key + Slot_key + Section + Line_order`; formal intake additionally
requires complete coverage of both `规格参数明细` and `页面占位参数`. A successful
partial staging response is not a complete target: inspect
`coverage_missing_rows`, finish the missing structures, review every value in
Base, and use the existing checkbox plus explicit-chat approval gates before
formal intake. Full configuration and the current contract version are in
[`agent/wukong-bridge/README.md`](../agent/wukong-bridge/README.md).

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
[`reference layout registry`](../docs/renderers/contracts/reference_layout_registry.json)
and the
[`JE-1000F US V2.0 contract`](../docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json).
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

When a source refresh changes mutable style/provenance identity without changing
the approved content or semantic/physical assembly, use the rebind command
instead of editing one hash or removing the registry entry. It is a dry-run
unless `--write` is present:

```bash
python3 tools/reference_layout_rebind.py \
  --plan docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json \
  --manual-ir <manual.ir.json>
python3 tools/reference_layout_rebind.py \
  --plan docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json \
  --manual-ir <manual.ir.json> \
  --write
```

For a read-only summary of all registered contracts, run
`python3 tools/reference_layout_rebind.py --all-registered --manual-ir
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
python3 tools/reference_layout_rebind.py \
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
The [JP twelve-page acceptance record](../code-as-doc/reviews/bp_jp_r3c_native_validation_2026-09.md)
shows the package hashes, actual native results and explicitly retained debt.

For a multi-target design handoff, run
`python tools/indesign_finalize.py --jobs <manifest.json>` with one explicit
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
[`Approved-PDF native InDesign replica` section](../code-as-doc/build_doc_guide.md#approved-pdf-native-indesign-replica-option-2).

Write the finalize and parity artifacts **next to the production IDML**, in
`docs/_build/<model>/<region>[/<lang>]/idml/` — `<stem>.indd`,
`<stem>_indesign.pdf`, `finalize_report.json` and `parity_report.json`. That is
the only location `release-manifest` looks in, so artifacts left in a scratch
directory are simply not recorded. (The second-host verification run in
[`indesign_second_host_runbook.md`](../code-as-doc/dev/indesign_second_host_runbook.md)
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

GitHub note:

- pull requests are gated by the `Manual Validation` workflow
- after merge, `main` runs the same validation workflow again
- feature-branch pushes are not expected to run a second duplicate `push` validation pass
- `Manual Validation` now includes smoke checks for `diff-report` and `release-manifest` in addition to the existing validation jobs
- the shared GitHub-hosted Feishu worker setup now installs `pandoc` from the official release action instead of `apt-get`, and it reuses pip/npm download caches, so remote queue runs are less likely to spend 10+ minutes waiting on slow dependency downloads before the actual build starts
- `Manual Validation` now also runs `python tools/check_maintainability_guardrails.py` as a low-noise guard against the main orchestration and validation hotspots growing back into giant files
- that guard also applies a reviewed language-literal ratchet: language tables may shrink, but new literal tables must be explicitly reviewed in the baseline diff
- `build.py check` also compares duplicated RST and raw HTML list text so renderer-specific copies cannot silently drift from the source wording
- `build.py check` also renders every prepared FCC page with the target language in both document and web profiles. A missing FCC opening line block, an unregistered localized right-column marker, or a runtime filename remap that loses language context now fails during `check`, before Word generation.
- `build.py check` also enforces capability -> chapter consistency: [`../data/model_capabilities.csv`](../data/model_capabilities.csv) mirrors the 文档构建表 feature checkboxes (refreshed by `sync-data` when `FEISHU_PHASE2_MODEL_CAPABILITIES_TABLE_ID` is set — it is a tracked file like `page_registry.csv`, so the git diff is the review surface for capability changes; duplicate build-table rows collapse to one mirror row), and [`../data/capability_page_rules.csv`](../data/capability_page_rules.csv) maps each capability to a required/forbidden bundle page or in-page section regex. A target with `UPS功能=TRUE` must carry `06_ups_mode`; one with `加电包扩容=FALSE` must not carry an extra-battery page. Targets without a capability row emit a non-blocking `CAPABILITY_ROW_MISSING` warning unless listed in [`../data/capability_known_missing.csv`](../data/capability_known_missing.csv); capability page selection remains fail-open. Each rule's enforcement is toggled per direction in the rules CSV (`required_when_true` / `forbidden_when_false`), so noisy rules stay recorded but inert until their wording is unified. The Feishu 文档构建 base carries a mirror rules table for visibility; the repo CSVs are the consumed source.
- `sync-data` derives the capability mirror header from the ordered `capability` values in `capability_page_rules.csv`, so a new rule does not require a separate Python registration list.
- Manifest pages can carry a `capability:` key (the capability field name): at bundle-plan time the assembler keeps or drops the entry per target using the same capability mirror, so one family manifest declares the page superset and each model auto-selects its chapters. All 24 current `06_ups_mode` entries across the 17 family manifests—including JP, KR, EU, US, AU, pt-BR, and CN—declare `UPS功能`; `manual_us.yaml` additionally maps `07_extra_battery` to `加电包扩容`. Targets without a capability row keep every page. New family manifests must preserve these annotations and refresh the checked-in family diff carrier.
- When one model needs a different placeholder-backed page layout but the family page order stays the same, that `generated_page` may use `model_overrides.<MODEL>.recipe` and/or `.template`. This is a narrow layout exception: other models still resolve the shared paths, and product/spec values remain in phase2 source tables.
- **Languages are per model, not per family.** A family config's `build.languages` is the union across that region's models — `configs/config.eu.yaml` lists six because the EU line carries Ukrainian templates, while JE-1000F does not ship Ukrainian. [`../data/model_languages.csv`](../data/model_languages.csv) (`Document_key,Project,languages,notes`, languages `;`-separated) narrows the family list per `<MODEL>_<REGION>` at bundle-plan time, dropping that language's pages **and** its generated data pages (`spec_uk.rst`, `symbols_uk.rst`, …). Never delete a language from the family config to fix one model: the models that do ship it would lose it too. Resolution intersects while preserving the family's order, so the config still owns ordering. It is fail-open like the capability gate — no row keeps every family language — and it is a tracked CSV, so the git diff is the review surface.
- Prefaces carry every family language *inside one file*, which page selection cannot narrow. Those manifest entries declare `lang_blocks: true` and the assembler drops the out-of-scope blocks (`**FR IMPORTANT**` headers, `\HBLangTagLine{XX}` in `raw:: latex`), keeping page-structure macros. The annotation is required, not inferred, because `**IT ...**` is ordinary bold text elsewhere. This replaces forking a template per language line (`00_preface_single_language.rst` was the hand-made version of exactly this trim). A trimmed target also gets a `MANUAL_LANGUAGE_SCOPE` derived from its real languages, so the cover line stops advertising a language the book no longer contains.
- A committed `docs/_review` derivative is per `(model, region)` and shared by a region's merged and single-language configs, so it holds the merged book's languages. The trim runs again on the overlaid bundle copy — `docs/_review` itself is never rewritten, and the merged build is unaffected because all its languages are in scope.
- New `check` codes: `LANG_SCOPE_UNSHIPPED_LANGUAGE` (a scope row disjoint from the family the config declares — today `configs/config.eu-uk.yaml` with its inherited JE-1000F/EU default target, which ships no Ukrainian) and `LANG_SCOPE_FOREIGN_SCRIPT` (a bundle page carrying a dropped language's script, which catches leakage that has neither a `_<lang>` filename suffix nor a language tag). The per-language contract / generated-page / identity / parity collectors all see the narrowed set, so a model shipping five of six family languages no longer fails on the sixth's missing source data.
- `Review Preview Package` is the separate packaging path when you need to share rendered review HTML with design
- that workflow now runs a lighter smoke packaging pass with `--skip-word` and verifies the packaged preview files before upload

Git branch hygiene note:

- after one PR is merged or closed, start the next change with `powershell -ExecutionPolicy Bypass -File scripts/start_branch.ps1 <type>/<area>-<topic>` on Windows or `./scripts/start_branch.sh <type>/<area>-<topic>` on mac/Linux so the new branch comes from the latest `origin/main`; use a change-type prefix such as `feat/`, `fix/`, `refactor/`, or `docs/`, never an agent-name prefix
- enable the repo-managed pre-push guard with `git config core.hooksPath .githooks`
- that guard now runs through the shared [`../scripts/git_branch_guard.py`](../scripts/git_branch_guard.py) core instead of a bash-only hook, and the repo also ships [`.githooks/pre-push.cmd`](../.githooks/pre-push.cmd) plus [`.githooks/pre-push.ps1`](../.githooks/pre-push.ps1) as Windows-native companion launchers
- that guard blocks pushes from branches that do not contain the latest `origin/main`; bypass only when intentional with `git push --no-verify`
- if OpenClaw on your local machine needs to report branch state or switch to an existing branch from a Feishu chat flow, use [`../scripts/openclaw_git_guard.py`](../scripts/openclaw_git_guard.py) instead of exposing raw Git commands; it only supports `status` and safe `switch --pull`, and it refuses non-generated dirty worktrees
- OpenClaw / Feishu IM can now answer read-only product-manual inventory questions from the `发布文档管理` Base view before falling back to queue resolution. Use phrases like `查 JE-2000F 的说明书链接`, `查询各产品的说明书`, or `获取说明书总览信息`; build-copy phrases such as `输出JE-1000F的所有欧规说明书文案` still go through the existing Build Draft queue path.
- if you need to keep `main` open while editing one or more review branches in parallel, use the repo worktree flow in [`../code-as-doc/dev/git_worktree_guide.md`](../code-as-doc/dev/git_worktree_guide.md); on Windows, prefer worktree paths under your current user such as `C:\Users\<you>\Documents\cms2docs\worktrees\...` instead of another user's home directory

---

## 2. Source of Truth

The manual system now has four layers, but they are used at different stages.

1. Template seed layer
   - [`docs/templates/page_us-en/*.rst`](../docs/templates/page_us-en)
   - [`docs/templates/page_jp/*.rst`](../docs/templates/page_jp)
   - [`docs/manifests/*.yaml`](../docs/manifests)
   - Responsibility: reusable page structure, headings, shared prose, and initial draft layout
   - Some templates intentionally duplicate prose across normal RST and renderer-specific branches such as `.. raw:: html` or `.. raw:: latex`; when changing wording, treat the RST list as the source wording and keep renderer-specific copies aligned
   - Template-maintenance Feishu cloud docs can be compared with `python tools/cloud_doc_backport.py diff --template ...` and then planned with `python tools/cloud_doc_backport.py apply-template --report ...`; the apply step is dry-run by default and only writes guarded template prose replacements when `--write` is supplied. It does not write Feishu source tables or review bundles.

2. Data layer
   - preferred snapshot root [`data/phase2/`](../data/phase2)
   - [`data/phase2/Spec_Master.csv`](../data/phase2/Spec_Master.csv)
   - [`data/phase2/Spec_Footnotes.csv`](../data/phase2/Spec_Footnotes.csv)
   - [`data/phase2/Spec_Notes.csv`](../data/phase2/Spec_Notes.csv)
   - [`data/phase2/spec_titles.csv`](../data/phase2/spec_titles.csv)
   - [`data/spec_master_value_repairs.csv`](../data/spec_master_value_repairs.csv) — tracked dormant known-value repairs consumed by the spec repair pass
   - [`data/phase2/symbols_blocks.csv`](../data/phase2/symbols_blocks.csv)
   - [`data/phase2/lcd_icons_blocks.csv`](../data/phase2/lcd_icons_blocks.csv)
   - [`data/phase2/Manual_Copy_Source.csv`](../data/phase2/Manual_Copy_Source.csv)
   - [`data/phase2/Localized_Copy.csv`](../data/phase2/Localized_Copy.csv)
   - [`data/phase2/Status_Words.csv`](../data/phase2/Status_Words.csv)
   - [`data/phase2/troubleshooting_blocks.csv`](../data/phase2/troubleshooting_blocks.csv)
   - [`data/phase2/Variable_Defaults.csv`](../data/phase2/Variable_Defaults.csv)
   - [`data/phase2/Variable_Lang_Overrides.csv`](../data/phase2/Variable_Lang_Overrides.csv)
   - [`data/phase2/page_registry.csv`](../data/phase2/page_registry.csv)
   - Responsibility: model-specific parameters, spec content, symbols content, troubleshooting content, LCD status-word matching, and placeholder values
   - When a valid phase2 snapshot exists, build/review/publish flows default to `data/phase2`; explicit `--data-root` still overrides that default.
   - A phase2 snapshot is valid for automatic default use only when `snapshot_manifest.json` records the complete core table set from one sync run: `spec_master`, `spec_footnotes`, `spec_notes`, `symbols_blocks`, `troubleshooting`, `lcd_icons`, `variable_defaults`, `variable_lang_overrides`, and `manual_copy_source`, plus derived `row_key_mapping`, `spec_titles.csv`, `Localized_Copy.csv`, and `Status_Words.csv`. Partial `sync-data --table ...` refreshes are still useful for focused checks, but use explicit `--data-root` when building from them.
   - For queue-driven builds, Feishu phase2 tables remain the structured-data source of truth. `data/phase2` is the gitignored materialized snapshot refreshed before build, not the daily authoring surface or a mirror-repo code difference.
   - GitHub `Manual Validation` uses the committed fixture snapshot under [`../tests/fixtures/phase2`](../tests/fixtures/phase2) so CI stays deterministic after `data/phase2` became gitignored; local live builds should still sync into `data/phase2`. The stable US/JP checks remain, and `tools/ci_check_targets.py` now derives an additional check target from every `configs/config*.yaml`. A target whose fixture snapshot lacks its `document_key` is reported as `SKIP`, not coverage; the coverage formula is `PASS/(PASS+SKIP+FAIL)` and `.github/ci_check_targets_skip_baseline.json` carries two no-increase ratchets, `skip_count` and `fail_count`. The Stage 1 observation lane reports the already-recorded FAIL rows without blocking, but a **new** FAIL fails the lane, as does a new SKIP. Without the FAIL ratchet, `--observation` let a target slide from `PASS` to `FAIL` with the job still green, so only `check-en` and `check-jp` were really gating anything. The repo-maintained [`../data/phase2/page_registry.csv`](../data/phase2/page_registry.csv) is the one tracked exception because `sync-data` reads it as the page-structure input on every run, including fresh checkouts.
   - GitHub `Nightly Render` is the credential-free daily rendering sentinel. It doctors every target discovered from `configs/config*.yaml`, then builds and validates the JE-1000F US English production IDML from `tests/fixtures/phase2`; manual dispatch uses the same committed fixture inputs. A failure points to either the exact config doctor row or the pilot IDML check instead of waiting for the next designer handoff to expose renderer drift.
   - To refresh one CI fixture target from the local mirror, first run `python tools/data_snapshot.py fixture-refresh --document-key <MODEL_REGION> --source-root data/phase2 --fixture-root tests/fixtures/phase2` as a dry-run, then repeat with `--write` after review. The command merges only the selected `document_key` (and shared rows), preserves unrelated targets, copies referenced attachments, and updates manifest hashes; it does not replace the whole fixture snapshot.
   - `Bingboom/auto-manual` is the code source of truth. Its `sync-hello-docs.yml` workflow mirrors the `main` engineering tree one-way into `Bingboom/Hello-Docs` while preserving the business-owned `Hello-Docs/main:docs/publish/**` subtree; it composes Git objects without re-adding a checked-out tree that could rewrite file blobs through line-ending attributes and fails if auto-manual ever starts owning `docs/publish`. Configure `HELLO_DOCS_SYNC_TOKEN` only in the source repo, keep `Hello-Docs` Feishu/OpenClaw bindings in that repo's own GitHub Secrets / Variables, and leave `FEISHU_BUILD_QUEUE_PAUSED=true` in the mirror repo until those bindings are ready. That pause variable is scoped to mirror Feishu runtime workflows and does not pause source repo behavior.
   - Copy [`../scripts/hello_docs_binding.env.example`](../scripts/hello_docs_binding.env.example) to a gitignored local file such as `.tmp/hello-docs-binding/env.sh`, fill the alternate Feishu values there, run `scripts/configure_hello_docs_binding.sh --env-file .tmp/hello-docs-binding/env.sh --dry-run`, then rerun without `--dry-run` to write the values into `Hello-Docs`; add `--include-optional` when the env file also has mirror-only Feishu IM / OpenClaw adapter values, and add `--unpause` only after the audit should allow Feishu runtime workflows to run.
   - Before unpausing `Hello-Docs`, run `scripts/audit_hello_docs_binding.sh --report-only`; it reports source/mirror tree parity, missing GitHub Secret names (including the model-capabilities table binding), mirror variables, and optional Feishu IM / OpenClaw entries without printing secret values. The daily Feishu schema sensor treats `文档构建表`/`数据入库表` and `02_文档构建`/`01_数据入库` as documented old-base/business-base aliases, and treats the retired `Document link` as replaced by `基线文档`/`飞书云文档`, so it does not request duplicate schema.
   - For spec data authoring, edit `规格参数明细` for `Page=specifications` rows and `页面占位参数` for non-spec page placeholders. `sync-data --table spec_master` now reads those two source tables through the pinned source views and writes the local `Spec_Master.csv` read model.
   - When changing the online source-table structure, update the machine-readable source-table contract [`../data/source_table_contracts/phase2_source_tables.json`](../data/source_table_contracts/phase2_source_tables.json) in the same PR as the human reference docs. It records each table's source key, snapshot file, intake target, writable fields, and source-record-index mapping so intake/backport/writeback skills do not rely on memory. `python tools/schema_drift.py --payload tests/fixtures/schema_drift/passing_payload.json` validates this contract in CI.
   - For first-pass intake from a structured spec/manual Markdown or Feishu cloud doc, run `python tools/source_intake.py run --input <spec.md-or-doc-url> --document-key <MODEL_REGION> --source-lang en --data-root data/phase2 --out reports/source_intake/<run-id>`. This produces reviewable source-table candidates and existing-row change requests; it does not create new online rows or bypass the human-approved source-table writer. Continue with `source_intake.py approve`, `source_intake.py apply`, and `source_intake.py verify` to record the P4-P7 closure; `apply` is dry-run unless `--write --table-binding TABLE=BASE:TABLE_ID` is supplied. Use [`../code-as-doc/dev/source_intake_mvp_checklist.md`](../code-as-doc/dev/source_intake_mvp_checklist.md) as the staged checklist.
   - For repeated spec-sheet onboarding, do not assemble dozens of staging rows by hand. Run `source_intake.py spec-extract` with a real sibling reference, then `source_intake.py stage-plan --spec-candidates <...> --spec-sibling <...> --placeholder-sibling <...> --overrides <target-differences.json> --document-key <MODEL_REGION> --localized-lang <lang>`. The second command clones both sibling structures, rejects ambiguous/missing logical rows, carries localized fields with changed source values, marks inherited-but-unconfirmed rows, and writes one review file plus a lark-cli `create_records` payload without touching Feishu. With exports ready, the mechanical repeat-run target is 3–5 minutes before human review; staging write/readback and formal source-table promotion remain approval-gated. See [`.agents/skills/spec-sheet-structured-intake/SKILL.md`](../.agents/skills/spec-sheet-structured-intake/SKILL.md).
   - After changing either spec source table, run `python build.py sync-data --config configs/config.us.yaml --data-root data/phase2 --table spec_master` for the normal snapshot refresh, or `python build.py spec-master-rebuild --config configs/config.ja.yaml --expect-spec-rows 157 --expect-placeholder-rows 222` for a focused rebuild; add `--write-back` only when the merged source data should update the legacy Feishu total table.
   - `python build.py sync-data --config configs/config.us.yaml --data-root data/phase2` refreshes the frozen snapshot from Feishu/Lark using the local `lark-cli` login and the CLI's `base` record listing flow; it also reports source columns missing from the phase2 schema as non-blocking `MISSING_COLUMNS` warnings in `snapshot_manifest.json` and the command output
   - `python tools/content_lint.py --data-root data/phase2 --json --write-report` runs the local content-QC observation step against that snapshot and writes `reports/content_qc/<run-id>/findings.json` plus `report.md`; fix findings in the Feishu source tables or Translation Memory, not in the generated CSV/report files. This command does not write Feishu QC rows, resolve live `record_id`s, or block Word delivery beyond its own `FAIL` exit code.
   - `configs/config.eu.yaml` now represents the live `EU` region-family row as `Build_family = eu-merged`, reads `JE-1000F / EU` specs from the shared split spec source tables, and is the config that blank-`Lang` queue rows should resolve to
   - `configs/config.eu-en.yaml`, `configs/config.eu-fr.yaml`, and `configs/config.eu-es.yaml` are the explicit English, French, and Spanish EU single-language surfaces when you want one language family at a time; `configs/config.pt-br.yaml` follows the same single-language pattern for Brazil Portuguese
   - `configs/config.au-en.yaml` is the Australia (`AU`) single-language English surface (`Build_family = au-en`); it inherits the EU single-language base, builds the `JE-1000F / AU` target, and uses the Australia-specific warranty contact `hello.aus@jackery.com`. Its safety/安规 page is forked to `docs/templates/page_au-en/safety_en.rst` (copied from EU) via manifest `docs/manifests/manual_au-en.yaml`, while product-overview/operation-guide pages and shared pages still reuse the EU/shared templates. The AU manifest uses `docs/templates/page_shared/en/00_preface_single_language.rst`; keep that English-only component separate from the merged US `00_preface.rst`, whose EN/FR/ES language-tag blocks are invalid in a single-language AU bundle
   - phase2 table/view bindings now live in env names such as `FEISHU_PHASE2_LCD_ICONS_TABLE_ID` / `FEISHU_PHASE2_LCD_ICONS_VIEW_ID`; keep mirror-repo tenant differences in env or GitHub Secrets instead of committed config
   - `python build.py validate --config ...` now catches missing phase2 table base-token/table-id bindings and page-manifest languages that are not listed in `build.languages`
   - the LCD icons page is table-driven from `lcd_icons_blocks.csv`; `figure` attachments sync into `data/phase2/_attachments/lcd_icons/` and render as the LCD table image column, while symbols `Figure` attachments sync into `data/phase2/_attachments/symbols/` and render through `symbols_blocks.csv`; symbol signal structure lives in `symbols_blocks.csv` as `block_type=signal_row`; reusable short copy such as LCD / Symbols page titles, table headers, Symbols signal labels / meanings, Product overview labels, and spec titles is authored in `Manual_Copy_Source.csv`, translated from Translation Memory rows tagged `manual_copy`, and rendered from generated `Localized_Copy.csv` / `spec_titles.csv`; the US Spanish, French, and Brazilian Portuguese Product Overview templates now resolve their seven page/panel/part labels from the existing `product_overview.*` keys, while the EU raw-LaTeX Product Overview pages remain unchanged; image alt text is derived from existing titles, `symbol_key`, or generated signal labels; LCD status-word bolding reads `Status_Words.csv` exported from Translation Memory rows marked `是否为 status word=Y`; LCD `{{VARIABLE_KEY}}` placeholders resolve through `Variable_Defaults.csv`, then language-specific substitutions come from `Variable_Lang_Overrides.csv`
   - for variable defaults, keep `Model_key` as the text model selector when the Base `Model` field is a linked record; linked model fields can export as record ids and are not stable enough for build matching
   - `python build.py translation-memory --config configs/config.us.yaml --model JE-1000F --region US --query-text "USB-C 100W Port" --lang fr --table spec-master` reads the same snapshot as a compact multilingual memory lookup, which is useful when OpenClaw or a maintainer needs terminology grounded in the current Base content before translating copy
   - `python3 .agents/skills/bitable-translation-memory/scripts/query_live_translation_memory.py --query-text "Always follow these basic precautions when using this product." --source-lang en --target-lang fr --format prompt` is the higher-priority sentence-pair lookup when you already maintain a dedicated translation memory table in Feishu Base; on chat surfaces, treat it as background wording memory and answer with the translation itself instead of a narrated lookup step. The script keeps a short local cache for repeat lookups; use `--no-cache` only when you need a forced refresh.
   - For Taiwan Traditional Chinese, use `--source-lang zh --target-lang zh-TW`; the live Base stores Simplified Chinese in `zh` and Taiwan Traditional Chinese in `zh-TW`.
   - `python3 .agents/skills/manual-rewrite-with-tm/scripts/rewrite_markdown_with_tm.py input.md --target-lang de --use-feishu-term-source -o output.de.md` is the batch rewrite path when a full Markdown page or manual must follow TM wording, keep headings, tables, lists, and image links stable, and preserve unmatched source text as `==...==` instead of silently paraphrasing it
   - during that refresh, `Spec_Master.csv Slot_key` is normalized back to plain tokens like `front.label` when the source table stores markdown-link wrappers
   - the sync also resolves full field names through Base field metadata, so long columns like `Row_label_footnote_refs` do not disappear when the CLI view output abbreviates them
   - when `spec_master` is refreshed from the split source tables, linked-record style footnote refs like `{"id":"rec..."}` are converted to `Footnote_id` values before `Spec_Master.csv` is written
   - when one target references a `Footnote_id` that is missing only in its own region but exists as one unambiguous sibling-region row for the same model, validation and rendering now reuse that fallback definition instead of stopping the build immediately
   - the sync does not auto-fix bad `Is_Latest` data; if a latest row is wrong, keep it wrong in the snapshot and let validation stop the build
   - `python build.py sync-data --config configs/config.us.yaml --data-root data/phase2 --dry-run` is the recommended first check on a new machine; it reports missing `lark-cli`, missing `FEISHU_PHASE2_*` bindings, and the `FEISHU_TRANSLATION_MEMORY_BASE_TOKEN` binding used for generated manual copy before any API fetch
   - `build.py` auto-loads `~/.auto-manual-phase2.env` (when that file exists) into the environment at startup, so the `FEISHU_PHASE2_*` / `FEISHU_TRANSLATION_MEMORY_*` bindings no longer need a manual `source` before `sync-data` or review — keep the secrets in that `$HOME` file (never committed). It never overrides a variable you already exported in your shell, and `AUTO_MANUAL_PHASE2_ENV_FILE` can point it at a different path
   - on Windows, the default `sync.phase2.cli_bin: lark-cli` is resolved to the installed shim automatically, so the normal shared config still works
   - when `spec_master` is part of that refresh, the command also regenerates [`../data/phase2/row_key_mapping.csv`](../data/phase2/row_key_mapping.csv) while preserving existing manual `Row_key` and `Remark` entries when possible
   - for future app-only DingTalk provider research, [`../tools/dingtalk/spike_cli.py`](../tools/dingtalk/spike_cli.py) is the manual Phase 0 smoke helper; it gets an App-Only token by default, then lets you supply the exact DingTalk list/update/upload endpoints for the chosen product without changing the current queue runtime
   - [`../tools/dingtalk/auth.py`](../tools/dingtalk/auth.py) now wraps the verified App-Only token flow behind `DINGTALK_CLIENT_ID`, `DINGTALK_CLIENT_SECRET`, and `DINGTALK_CORP_ID`, and [`../tools/dingtalk/workspace.py`](../tools/dingtalk/workspace.py) can already extract a target docs node ID from a standard `alidocs.dingtalk.com/i/nodes/...` URL
   - `python build.py process-review-start-queue --config configs/config.us.yaml --data-root .tmp/review-start/phase2` is the Start Review bridge: it reads `sync.phase2.review_init` rows where `是否进入Review` is checked and `Workflow_action` maps to `Start Review`, resolves the exact model/region target from `Document_Key`, and combines it with the language-range `Build_family` plus optional `Lang`. For example, both `JBP-2000B_US` and an ordinary US host row use `Build_family=us-merged`; the exact target selects `configs/config.bp-us.yaml` for JBP and `configs/config.us.yaml` for the host. The worker groups only the rows whose resolved config enables `build.queue_by_document_key`, syncs a fresh phase2 snapshot, always reseeds `docs/_review` from the latest `origin/main` template/data state, force-updates the review branch when it already exists, creates or reuses the PR, then writes the same `Git_ref`, `PR_url`, `Review_status=InReview`, and cleared `是否进入Review` state back to every row in that routed group
   - Start Review only starts when `Document_Key` is a non-empty `<MODEL>_<REGION>` value, `是否进入Review` is checked, and `Workflow_action` maps to `Start Review`
 - `Start Review` now means "force restart and reseed from the latest template". Existing committed `docs/_review/<model>/<region>/` content on `main` is no longer a duplicate guard, and re-checking `是否进入Review` on an `InReview` row will restart the review seed flow
 - **Print-only pages must live in the manifest, not in a hand-edited review index.** The seeded index is generated from the page manifest, so review-index includes with no manifest entry silently lose their references on every reseed — the page files stay in `page/` but leave the built book, and the target then fails the same-source IDML gate at Publish (incidents: 2026-08-13/14 reseeds → runs 31767694706, 31779053321). The JE-1000F/US print book's `00_toc.rst` and `99_back_cover.rst` are therefore declared in `manual_us.yaml` with `ordinal_neutral: true`: reseeds regenerate them deterministically, and the annotation keeps every later duplicate page's positional `pNN_` file name (e.g. `p22_01_fcc.rst`) unchanged — those names are pinned by the committed review branch and by the approved reference-layout contract's `source_ref` list. Never hand-add an include to a seeded index as a durable fix; declare the page in the manifest instead
 - [`../.github/workflows/feishu-start-review.yml`](../.github/workflows/feishu-start-review.yml) is the `main`-owned remote review-init worker that performs the same review-start flow from GitHub Actions after a Feishu workflow dispatch
 - review PRs created by that trusted Feishu Start Review worker automatically approve their `Manual Validation` and `Review Preview Package` checks; ordinary external pull requests still use GitHub's approval gate
 - `python build.py queue-query --config configs/config.us.yaml --queue-scope all --task-id "JE-1000F_US_0.3_Build Draft Package" --json` is the recommended local Phase 2 lookup before a natural-language OpenClaw action; it resolves the exact Feishu row and returns the `record_id`, `Task_id`, `Workflow_action`, `Git_ref`, `构建结果`, and the phase-aware `delivery_kind / delivery_url / delivery_ready` contract
 - `python build.py queue-resolve-action --config configs/config.us.yaml --query-text "发布 JE-1000F_US_0.3" --json` is the structured dry-run resolver for the control layer; it returns the bounded `action_name`, `resolution_status`, confirmation requirement, and matched row fields before any dispatch happens
 - for a fixed "现在库里构建了多少文档" lookup, run `python build.py queue-query --config configs/config.us.yaml --queue-scope document-link --result-contains success --limit 200 --json` and the same command with `configs/config.ja.yaml`, then count rows whose `normalized_workflow_action` is `draft` or `publish`; natural-language asks such as `当前所有已构建文档链接` now resolve to the same successful `Document_link` surface with a larger default limit
 - inside this repo, the OpenClaw-backed assistant is named **BlockClaw** because it works with content blocks; treat it as the default document-build operator that helps you build, review, publish, inspect queue rows, and explain failures for `auto-manual`, with translation and copy work acting as supporting helpers
 - `python build.py translation-memory --config configs/config.us.yaml --model JE-1000F --region US --query-text "USB-C 100W Port" --lang fr --table spec-master` is the repo-local terminology lookup that pairs well with OpenClaw translation asks; it keeps the prompt small by returning matched multilingual rows instead of dumping raw CSV tables
 - for one-shot sentence translation, prefer `bitable-translation-memory`; for whole-page or whole-file rewrite jobs that must preserve Markdown structure or unmatched-source fallback, pair it with `manual-rewrite-with-tm`
 - [`../integrations/openclaw/feishu-im-webhook-adapter/`](../integrations/openclaw/feishu-im-webhook-adapter/) is the repo-external Feishu IM webhook adapter for this control layer; it receives Feishu text messages, calls `queue-resolve-action|queue-query|queue-execute`, and replies back into the same Feishu thread
 - cloud-doc review backport is **not** an IM/BlockClaw capability — its LLM target-resolution is too uncertain for chat. Run it from Claude Code / Codex / a terminal via `python tools/cloud_doc_backport.py run-review-branch ...` (see the backport step below and AGENTS.md §3)
 - the adapter reads optional local-only profile files from `.openclaw/` for private aliases, reply phrasing, and Feishu message reaction choices; keep personal memory, real chat samples, and custom wording there instead of committing them to remote
 - set `FEISHU_IM_ENABLE_MESSAGE_REACTIONS=true` only after the Feishu app has message reaction permission; reactions are best-effort, the initial received-stage reaction defaults to `Get`, and the same-thread text reply remains the reliable status surface
 - when the live desktop entrypoint is the installed OpenClaw gateway rather than the repo adapter, run [`../integrations/openclaw/scripts/patch_openclaw_feishu_received_reaction.mjs`](../integrations/openclaw/scripts/patch_openclaw_feishu_received_reaction.mjs) before `openclaw gateway` starts; it adds the native Feishu `Get` reaction directly inside the `im.message.receive_v1` handler, before agent reasoning, table lookup, or build dispatch; it supports both the legacy bundled-`dist/` install and the OpenClaw ≥ 2026.6 `@openclaw/feishu` plugin layout under `~/.openclaw/npm/projects/openclaw-feishu-*/`
 - `python build.py listen-message-control --config configs/config.us.yaml` is the no-server local Feishu IM entry for the same control layer; it listens to `im.message.receive_v1` through `lark-cli` and replies in-thread without exposing a public callback URL
 - if the same machine must keep the old Feishu app for local phase2 operations, set `FEISHU_IM_LARK_CLI_HOME` before starting `listen-message-control`; that makes the new app use its own isolated `lark-cli` home instead of rewriting the default `~/.lark-cli`
 - for a long-lived ECS host, use the adapter `systemd` deployment assets under [`../integrations/openclaw/feishu-im-webhook-adapter/deploy/systemd/`](../integrations/openclaw/feishu-im-webhook-adapter/deploy/systemd/); the wrapper script sources the same `env.sh` you already use for manual startup
 - the same `queue-query --query-text` parser also understands `Task_id` strings such as `JE-1000F_US_0.3_Build Draft Package`, spaced asks like `帮我生成 JE-1000F US 0.3 草稿`, document-key-only review asks like `review JE-1000F_EU`, `开始 review JE-1000F us-merged`, and `为什么 JE-1000F US 0.3 构建失败`; if it can derive an exact `Task_id`, that selector takes priority
 - OpenClaw can also resolve config-scoped batch Draft asks such as `输出JE-1000F的所有欧规说明书文案`, `构建JE-1000F的所有欧规说明书文案`, `基于配置构建JE-1000F的欧规`, or the implicit-all form `构建JE-1000F的欧规说明书文案`; it maps `欧规` into a `Task_id` prefix like `JE-1000F_EU_`, keeps only `Build Draft Package` rows with `是否触发文档构建` enabled, and dispatches those rows by Feishu `record_id`. Draft and print Publish share a Document_link record concurrency slot; Web Publish uses one global publish-branch transaction slot. `是否强制刷新数据` remains the print/draft row-level input, while Web Publish always refreshes approved assets.
 - GitHub Actions artifacts are short-lived inspection/handoff copies rather than another archive: Draft/Start Review/Web Publish verification/preview/OpenClaw outputs keep 7 days, and selective print Publish release outputs keep 14 days. Formal print files live in the release tree; the Web candidate lives on `Hello-Docs/publish` and the production snapshot lives under `Hello-Docs/main:docs/publish/`; the nightly phase2 backup keeps its separate 90-day restore window.
 - exact OpenClaw Build Draft Package / Publish dispatches require the selected row's `是否触发文档构建` to be enabled; unchecked rows fail fast instead of launching a GitHub run that exits without output.
 - status-like asks such as `草稿包好了没`, `这个跑完了吗`, or `这个到哪了` resolve as status checks even when they mention draft/publish wording; pronoun follow-ups can reuse the last resolved `record_id` from the local adapter state, but build/trigger/rerun requests always resolve fresh from the current Feishu table instead of appending a remembered `record_id`
 - retry-style asks such as `补跑英语和法语`, `补构建法语`, or `重试这个` are treated as Build Draft Package intent; the adapter reuses only safe context such as model, market, version, and Git_ref, then resolves fresh queue rows instead of reusing the previous `record_id`
 - `queue-query` and `queue-resolve-action` accept `--langs en,fr` for bounded multi-language selection; natural-language asks can also use the registered Chinese/English aliases such as `英语`, `法语`, `西语`, `德语`, `意语`, and `日语`. Display labels and query aliases come from `tools/lang_registry.py`, so new language coverage is added at the registry rather than in each consumer. The fake `xx` end-to-end probe verifies that the same registry row flows through sync, localized copy, content lint, queue query, and preview labels; reference-bound IDML registration remains separately approved.
 - `tools/manifest_lint.py --json` provides a report-only page-manifest inventory check. It reports orphan manifests, invalid/missing sources, and language-set drift between each config and its manifest; it does not alter build or approval gates.
 - `tools/manifest_family.py` provides the non-mutating family-manifest pilot. Its `diff` command writes a deterministic JSON-Pointer carrier and its `roundtrip` command applies that carrier in memory and checks canonical manifest bytes; it does not rewrite source manifests or change build assembly.
 - `tools/manifest_family.py fold --index docs/manifests/family/index.yaml` validates the full fold inventory: 2 anchor manifests plus 15 carriers cover all 17 current manifest files. `--write` refreshes only the JSON carriers and remains explicit.
 - The `Manifest Regenerate and Diff Guardrail` workflow runs the fold check for manifest/config changes, so a manually edited generated YAML fails CI when its carrier no longer rebuilds the same canonical bytes.
 - `queue-query`, `queue-resolve-action`, and `queue-execute` accept `--fresh-since <iso-or-epoch>` so status replies can distinguish this-run writeback from older row results; Document_link JSON rows include `freshness_status`, `result_built_at`, `result_is_fresh`, and `build_started_at`
 - `queue-query --json` includes `matched_count`, `returned_count`, `limit`, and `truncated`; if a broad query hits the default limit, treat `truncated=true` as an incomplete answer and re-run with narrower filters or a higher `--limit`
 - broad latest-link asks such as `构建好的文档链接发我` return successful latest-version rows per `Document_Key`, while inventory asks such as `当前所有已构建文档链接` keep all successful rows up to the larger inventory limit
 - batch delivery replies in Feishu IM are sent as one status summary plus one message per `delivery_url`; short follow-ups such as `发` or `发一下` reuse the previous batch context and resend those phase-aware links instead of flattening them into one plain-text block
 - adapter conversation memory is never the build truth source: `这个好了没` re-reads Feishu by `record_id`, and if a remembered row has been deleted or moved, BlockClaw reports it as not found and clears that context instead of replaying the old row
 - `python build.py queue-execute --config configs/config.us.yaml --query-text "请帮我构建 JE-1000F_US_en_0.3，并返回 Build Draft Package 记录。只返回 record_id、Git_ref、构建结果和 delivery_url。"` is the recommended deterministic execution entry for natural-language OpenClaw build asks; it resolves the Feishu row, dispatches the matching `main`-owned workflow, waits for completion, and then re-reads the Feishu row before returning the final fields plus `accepted_at`, `run_id`, `run_url`, and `freshness_status`. OpenClaw must not first run local `check` / `word` / `sync-data` or inspect `data/phase2/*.csv`; the remote worker owns the row's `是否强制刷新数据` behavior.
 - if the GitHub run finishes but the Feishu row still only has a pre-dispatch `FAILED` or `SUCCESS`, OpenClaw reports `freshness_status=stale_result` or `writeback_pending` instead of treating that old row value as the current run result
 - a local observation gap is never reported as an action failure: once GitHub accepts a dispatch, a transient `status`/poll error, a `control-layer ... fetch failed`, or a wait-deadline timeout makes `queue-execute` defer to the authoritative Feishu/Base writeback (`freshness_status`) instead of raising — it reports a failure only when the GitHub run reaches a genuine terminal failure **and** the row is still not fresh; `/manual-status` likewise returns the last known run state plus an `observation_error` line rather than erroring out, because the remote run keeps going regardless of whether the local poller could read it back
 - builds report results on an accept-first lifecycle, never by holding the chat turn open: the dispatch reply and `/manual-status` carry `state: accepted|processing|completed|failed` plus a `note:` pointing back to `status last`, so an in-flight run reads as `任务正在处理中` (not a failure). On the Feishu IM adapter a single-record build replies "已受理（处理中）" immediately, dispatches with `--no-wait`, and does **not** poll; progress is delivered **on demand** — when you re-ask "这个好了没", the adapter reads the authoritative state at that moment (a fresh Base writeback wins → `已完成`/`失败`; otherwise it reads the live GitHub run once via the remembered `run_id` → 仍在跑=`处理中`, run 已失败但未写回=`失败`, run 完成但结果未落表=`处理中`) and answers 处理中/已完成/失败. Single read per question, not polling
 - against the Feishu message control plan, the repo now has the full repo-local Phase 2 stack: query, deterministic execute, structured failure replies, explicit Publish confirmation, and a standalone Feishu IM webhook adapter are all live. Encrypted callback support and ECS deployment assets are now repo-owned; the remaining gaps are shared state and a stable named ingress rollout.
 - if you keep using `trycloudflare.com`, only the process restart becomes stable; the callback URL itself still changes after a tunnel restart. For a stable URL, switch the same adapter to a named Cloudflare Tunnel or another fixed HTTPS ingress
 - if `queue-execute` resolves `Workflow_action = Publish`, add `--confirm-publish`; otherwise it now stops before dispatch
 - repo-local OpenClaw dispatch no longer treats `adm-zip` as a required local install just to send a Build Draft Package or Publish dispatch from ECS; metadata artifact parsing is now best-effort, so missing package installs degrade status detail instead of blocking dispatch
 - when a `Start Review` worker fails before Feishu writeback, the worker now writes a structured failure summary into `openclaw-run-metadata`; OpenClaw status and `queue-execute` surface that summary directly, for example `缺少 JE-1000F_CN 的规格数据，无法进入 review。`
 - `queue-execute` treats a `Start Review` row that already has `Review_status=InReview` and `Git_ref` as completed and returns the current row without dispatching another Action; otherwise OpenClaw dispatches `start-review`, `build-draft`, and `publish` with the resolved Feishu `record_id` so the GitHub run and final writeback stay tied to that exact queue row
 - if the Start Review workflow is dispatched with one explicit `record_id` but the GitHub worker cannot re-read that row as pending from the current Feishu view, that run now emits a structured failure summary instead of ending as a silent success; if the row is already `InReview`/`ReadyForPublish` with `Git_ref`, the duplicate dispatch is treated as an idempotent success even when `Workflow_action` has already advanced to a later stage (e.g. `Build Draft Package`)
 - for a multi-target build (several targets at once, or one model across regions), use `queue-execute --allow-multiple`. It validates every matching row, runs the same warning-only target-bound asset preflight for each Draft/Publish row, then starts one batch worker run per queue action with the exact eligible record set, so the third pending target cannot be silently lost or accidentally replaced by another pending row. The command returns a per-record JSON report (`matched_count` / `dispatched_count` / `skipped_count` / `error_count` + `results` with `record_id`/`run_id`/`status`/`reason`/`asset_preflight`); all dispatched rows from one action share the same `run_id`. It is accept-first (no completion wait). Report only rows returned as `dispatched` (with a `run_id`) as actually started — never infer "已进队" from the trigger flag — and ask for a complete target name (e.g. `JE-1000F_CN_1.3`, not `JE-1000F_CN`) when a version is missing
- `python build.py process-build-queue --config configs/config.us.yaml` is the optional Feishu task-table bridge: it reads the historically named `sync.phase2.document_link` binding where `是否触发文档构建 = Y`, first writes and verifies a two-hour `claim_token` lease in `构建结果`, writes `开始构建时间` when that field exists, resolves the config from the exact `Document_Key` target plus language-range `Build_family` and optional `Lang`, groups only the rows whose resolved config enables `build.queue_by_document_key`, runs `sync-data` only when that row group has `是否强制刷新数据 = true`, builds Draft rows as `check -> word -> md`, upgrades Publish rows to `check -> diff-report -> word -> pdf -> md -> idml`, and uses phase-aware delivery fields: Draft imports the built Word `.docx` into editable `飞书云文档` plus frozen `基线文档`, Publish uploads the designer handoff ZIP and writes its knowledge-base link to `idml_file`, and Web Publish writes `HTML_link`. It also writes the local DOCX release path into `Document directory`, optionally writes `Document link_dd` for a mirror, writes a timestamped status into `构建结果`, writes the refresh result into `data_sync`, clears `是否强制刷新数据`, and flips the trigger back to `已构建` on success. The retired `Document link` field is not an upload-success signal.
   - for `build.queue_by_document_key` configs, Draft rows with a non-empty `Lang` are grouped by `Document_Key + normalized Lang`; `br` / `pt-br` normalizes to `pt-BR`, and the selected language is passed to build/check/validate/bundle/output resolution. `configs/config.pt-br.yaml` is now a single-language entrypoint, so Brazil Portuguese draft rows should use `Build_family = pt-br` with `Lang=br` or `Lang=pt-BR` instead of adding an English companion row.
   - when a row group starts, `构建结果` is first written as `RUNNING | ... started_at=... | claim_token=... | claim_expires_at=...`; the worker bypasses the pending view to read every row back and only the matching unexpired token continues. Active leases are skipped, expired leases can be retried, and final `SUCCESS` / `FAILED` writeback releases the lease. This is a verified lease because Feishu upsert has no compare-and-swap; workflow-level concurrency is maintained separately.
   - if that queue row has a `Version`, Build Draft Package DOCX/Markdown names use `manual_<model>_<region>_<lang>_<Version>.docx|md`, while Publish queue release artifact names use `manual_<model>_<region>_<lang>_publish_<Version>.docx|pdf|md`; Draft exposes the imported `飞书云文档`, while Publish exposes the packaged designer handoff through `idml_file`
   - the frozen baseline (`基线文档`, a second import of the same Word `.docx`, used only for backport render-vs-render diffing) is imported with a `_基线<YYYYMMDD>` name suffix (e.g. `manual_je1000f_us_en_0.1_基线20260706`), so it is distinguishable in the review-doc wiki node from the editable `飞书云文档`, which keeps the base name
- Within one `process-build-queue` invocation, a successful forced phase2 sync is memoized per config/data-root pair; later groups reuse that snapshot, while a failed sync is not memoized and remains retryable.
- `Workflow_action = Build Draft Package` rows must carry `Git_ref`; queue builds seed a temporary worktree from the latest `origin/main`, then overlay only the active `docs/_review/<model>/<region>` target from that review branch. Sibling targets remain exactly as they are on `main`, so one review branch cannot dirty or replace another target during queue Publish.
- 对已登记 approved reference-layout 的目标，Print Publish 的检查、DOCX、PDF、Markdown 和 IDML 全部读取同一份 `review-asis` 冻结内容。勾选「是否强制刷新数据」仍会刷新并归档 phase2 snapshot、供资产解析使用，但不会在 Publish 阶段把最新线上字段回写进已审核页面。若确实要发布新的线上文案，先同步或重新播种 review、完成版面复核并显式重批 content contract，再触发 Publish。未登记批准合同的目标继续使用原有 `review` 参数同步。
  - on a local worker, if a same-named local `Git_ref` branch already exists, the queue uses that local branch directly so you can verify and upload review updates before pushing them
  - if GitHub is briefly unstable but that same `origin/<Git_ref>` or local branch is already cached on the worker, the queue will reuse the cached ref and continue building from the intended review branch
   - queue rows use `Workflow_action` only: `Start Review` to force restart/reseed review branches, `Build Draft Package` for review-stage rebuilds, `Publish` for print release artifacts, and `Web Publish` for the responsive RTD manual; leave `Doc_phase` blank. For Start Review, `Document_Key` is enough; if the table exposes `Task_id`, use `Document_ID + "_" + Workflow_action` mainly for versioned build/publish rows.
   - if `Document_Key` is a linked Base field, OpenClaw uses `Task_id` as the stable Start Review selector and then checks `是否进入Review` plus `Workflow_action=Start Review`
   - when review-init reuses the shared `Document_link` view, each worker consumes only its own action; Web Publish cannot be consumed by the print Publish worker
   - Build Draft Package outputs stay under the current repo [`../docs/_build/`](../docs/_build) tree by default; pass `--staging-root <dir>` or set `AUTO_MANUAL_STAGING_ROOT=<dir>` to isolate generated `docs/_build`, `reports/version_tracking`, and `reports/releases` under that root instead
- `Build_family` only expresses the queue row's language range: `us-merged`, `eu-merged`, `us-en`, `eu-en`, `us-es`, `us-fr`, `pt-br`, `jp-ja`, or `cn-zh`. Product/skeleton identity comes from `Document_Key`; target-specific configs declare the accepted row language family through `build.language_family`. `Lang` remains optional compatibility/narrowing data.
- merged US/EU Start Review, Draft, and Publish rows should use `Build_family = us-merged` / `eu-merged` and may leave `Lang` blank; single-language rows should use the matching language family such as `us-en` / `eu-en` / `us-fr` / `us-es` / `pt-br`. JBP does not use a special Base value: `JBP-2000B_US + us-merged` resolves the BP skeleton by exact target.
- config policy for `build.queue_by_document_key`: enable it for merged whole-book families that intentionally produce one shared manual across multiple languages, such as today's `us-merged`, `eu-merged`, and future `cn-merged`; keep it disabled for single-language families such as `us-en`, `eu-en`, `us-fr`, `us-es`, `pt-br`, `jp-ja`, `cn-zh`, or future `eu-de` / `eu-fr`, which should continue to run one queue row per `record_id`
   - print Publish stages IDML/LaTeX/DOCX/PDF/ZIP/Markdown under the Git-ignored runtime tree [`../reports/releases/<model>/<region>/<lang>/versions/<version>/`](../reports/releases), delivers formal files through Feishu or short-lived GitHub Actions artifacts, and does not deploy HTML or commit those generated files. Web Publish always refreshes approved Web assets, writes MyST plus verification HTML under `versions/<version>/web/`, freezes only Web source/assets in the `Hello-Docs/publish:docs/publish/` candidate, opens or updates a `docs/publish/**`-only PR into `Hello-Docs/main`, and writes the deterministic RTD route to `HTML_link`.
   - [`../scripts/process_build_queue.ps1`](../scripts/process_build_queue.ps1) is the Windows automation wrapper for that queue bridge; it restores the local Node/npm path plus the saved `FEISHU_PHASE2_*` user env vars, then writes logs into [`../.tmp/process-build-queue/`](../.tmp/process-build-queue) and forwards extra queue args such as `--dry-run` or `--record-id`
   - [`../scripts/process_build_queue_feishu.ps1`](../scripts/process_build_queue_feishu.ps1) is the one-click Feishu-only queue entry on Windows; it fixes the primary upload target to Feishu/wiki
   - the DingTalk AliDocs mirror-upload chain was retired on 2026-07-02 (its one-click queue entry, session-upload CLI, and setup guide were removed); Feishu/wiki is the only artifact upload target
   - `python build.py listen-build-queue --config configs/config.us.yaml` is the push-based immediate-build listener: after the Feishu app has the `drive.file.bitable_record_changed_v1` event enabled, it subscribes the table and keeps the long connection on the same current user identity, then triggers `process-build-queue` immediately when `Document_link` rows are checked in `是否立即构建`
   - [`../scripts/listen_build_queue.ps1`](../scripts/listen_build_queue.ps1) is the Windows wrapper for that listener; it restores the local Node/npm path plus the saved `FEISHU_PHASE2_*` user env vars and writes logs into [`../.tmp/build-queue-listener/`](../.tmp/build-queue-listener)
  - [`../.github/workflows/feishu-build-queue.yml`](../.github/workflows/feishu-build-queue.yml) is the `main`-owned remote print Publish worker. [`../.github/workflows/feishu-web-publish-queue.yml`](../.github/workflows/feishu-web-publish-queue.yml) is the independent business-plane Web worker; it serializes writes to the generated `Hello-Docs/publish` candidate and maintains the scope-guarded PR into `main`.
   - its XeLaTeX/CJK apt downloads are cached by runner OS, architecture, and the checked-in `.github/texlive-apt-packages.txt` package-set hash; every run summary shows cache hit/miss plus install time. Use the boolean `texlive_smoke_only` dispatch input to run the deterministic PDF/cache acceptance path without selecting or changing any Feishu queue row.
   - if you want remote immediate builds, create a Feishu workflow whose combined condition is `是否触发文档构建 = Y` and `是否立即构建 = true`, then dispatch the workflow matching `Workflow_action`; the queue still only builds rows whose trigger field is `Y`
 - that remote bot flow requires the Feishu app/bot to have read access to the phase2 source tables and write access to the `Document_link` table; otherwise it can detect pending rows but cannot write back `开始构建时间` or `构建结果`
 - give the user/bot identity edit/container permission on the review-doc wiki parent node if the imported Draft cloud doc must land there; otherwise `飞书云文档` keeps the import URL and the status records the best-effort move warning
 - `python build.py md` and queue Markdown outputs reuse the Word bundle HTML path; the exporter prefers native MyST when Pandoc provides it and otherwise emits MyST-compatible CommonMark with pipe tables. Each generated `md` directory carries `conf.py`, `index.md`, and local `assets/`; RTD then uses `tools/readthedocs_source.py` to assemble the selected target directories into one catalog source under `docs/_build/rtd/`.
 - if you also want the remote GitHub Draft/Publish workers to mirror to DingTalk, configure GitHub Secrets `DINGTALK_DOCS_A_TOKEN`, `DINGTALK_DOCS_XSRF_TOKEN`, and `DINGTALK_DOCS_COOKIE`, then explicitly set the GitHub Actions repository variable `AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER=dingtalk_alidocs_session`; `DINGTALK_DOCS_TARGET_NODE_URL` is optional and only acts as the remote default target
 - when DingTalk mirror sync is enabled, Feishu still remains the queue control plane and canonical writeback surface; `Document link_dd` is supplemental mirror writeback and never replaces the phase-aware `delivery_url`
 - when Feishu is primary and DingTalk is only the mirror, mirror target/session errors no longer abort the whole row; the queue still writes the Feishu result and records the DingTalk problem as `dingtalk_sync=failed`
 - if the row also has `是否上传钉钉`, that checkbox becomes the row-level DingTalk gate: checked rows also sync DingTalk, unchecked rows stay on the normal Feishu/wiki path for that run
 - if the table does not have `是否上传钉钉`, the worker follows the current global worker mode for that whole row
 - if that checked row also has `DingTalk_target_node_url`, the worker uploads to that row-level target first; if it is blank, the worker falls back to the global `DINGTALK_DOCS_TARGET_NODE_URL` when present
 - if the row also has `operator_union_id`, the worker can resolve a per-operator DingTalk session file from `AUTO_MANUAL_DINGTALK_SESSION_ROOT` before falling back to the global browser-session envs
 - `DingTalk_session_key` and `钉钉会话键` are accepted as aliases for `operator_union_id`; if a row uses `alice`, the worker expects `<session_root>/alice.json`
 - if a DingTalk-enabled row points at a missing per-operator session or there is no usable global DingTalk session, the queue now fails that row before build starts and writes the missing-session reason back to `构建结果`
 - `钉钉上传节点` is accepted as a compatibility alias, but prefer `DingTalk_target_node_url` for new tables
 - for OpenClaw Phase 2, use `delivery_ready` as the completion predicate and return `delivery_url` with `delivery_kind`: Draft=`飞书云文档`, Publish=`idml_file`, Web Publish=`HTML_link`. `Document link` / `document_link` is retired and must never be used to infer Draft upload status; `Document link_dd` remains optional supplemental mirror writeback
 - **delivery outbox (DingTalk hand-off)**: set `AUTO_MANUAL_DELIVERY_OUTBOX_ROOT` on a worker to have every successful Publish also drop its artifacts into `<root>/<job_id>/` together with one `delivery_manifest.json`. With the variable unset the whole path is inert, so nothing changes for workers that do not deliver. Point it at an ignored directory outside the git tree — the repo ignores `/output/`, so `output/outbox` inside either checkout works
 - the drop covers Publish only (a Draft's deliverable is the Feishu cloud doc, and Web Publish has no artifact sink) and carries the print PDF, handoff zip, Word, and Markdown; `latex/` and `html/` render trees are deliberately excluded
 - the queue reports the outcome in `构建结果` next to `dingtalk_sync=*`: `delivery_outbox=ok` plus `delivery_outbox_job=<job id>`, `delivery_outbox=skipped` when that target is not mapped for DingTalk delivery (a normal state, not a fault), or `delivery_outbox=failed` plus `delivery_outbox_error=<reason>` when a mapped target could not be dropped. A delivery problem never fails the row: the artifact has already reached the knowledge base by then
 - which targets are delivered is a data contract, [`data/dingtalk_delivery_map.csv`](../data/dingtalk_delivery_map.csv): one row per `(model, region)` mapping to the DingTalk 项目代码 + 安规 + the 文案语言 set that region's book covers. Publish rows leave `Lang` blank and produce one whole-book bundle, so the map is deliberately keyed by region rather than by language. Add a row only after checking the 安规/语言 values against the live base
 - the manifest is immutable build output and carries `delivery_key`, a digest over target + version + artifact hashes. The delivery agent owns progress (its own `status.json` beside the manifest) and must dedupe on `delivery_key`: a rebuild legitimately produces a second job, and a runner that loses its queue claim mid-publish can leave a job whose row was never written
 - operator housekeeping: consumed job directories are not reclaimed automatically, and a second Publish of the same target/version inside the same second is refused rather than overwritten. Clear delivered jobs periodically — they hold full PDFs and zips
  - that queue worker reuses the same phase2 env-bound table/view configuration as `sync-data`; it additionally needs `FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID` plus `FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID`, auto-derives the current wiki destination from the same base when possible, and optionally accepts `FEISHU_PHASE2_DOCUMENT_LINK_WIKI_PARENT_TOKEN` to force a different parent wiki node
   - [`data/phase2/page_registry.csv`](../data/phase2/page_registry.csv) remains repo-maintained; `sync-data` copies it into isolated `--data-root` snapshots such as `.tmp/review-start/phase2`
   - page selection/applicability and [`data/layout_params.csv`](../data/layout_params.csv) remain repo-maintained inputs
   - Safety intro pages are maintained in [`docs/templates/page_*/safety_*.rst`](../docs/templates); the standalone user maintenance instructions page is maintained in shared templates such as [`docs/templates/page_shared/en/01_user_maintenance_instructions.rst`](../docs/templates/page_shared/en/01_user_maintenance_instructions.rst) and is included immediately before `symbols`; JP keeps the detailed safety warnings in [`docs/templates/page_jp/01_meaning_of_symbols.rst`](../docs/templates/page_jp/01_meaning_of_symbols.rst). The old `content_blocks.csv` safety source has been removed from the active repo flow
   - `Spec_Footnotes.csv` now holds only reusable spec footnote definitions; `Footnote_order` controls the rendered superscript marker order and `Footnote_id` is referenced from `Spec_Master.csv`
   - CSV/PDF and IDML use one shared footnote-marker rule: comma-separated IDs retain their order and repeated IDs print once. Existing language fallback and target selection remain unchanged.
   - `Spec_Footnotes.csv` and `Spec_Notes.csv` both carry a `Type` field from the Feishu source; keep it explicit as `Footnote` or `Note` so downstream renderers do not infer type from the visible text
   - `Spec_Notes.csv` holds bottom-of-spec notes that are not tied to superscript references, such as trademark statements
   - `Spec_Footnotes.csv` and `Spec_Notes.csv` now match rows by `Region` + `Model`; `project_code` / `项目代码` is no longer used there either
   - when one spec page renders both bottom notes and bottom footnotes, the final output order follows [`docs/templates/spec_template.rst`](../docs/templates/spec_template.rst)
   - `Spec_Master.csv` uses `Row_label_source`, `Param_source`, and `Value_source` as the shared source-language columns; `Source_lang` stores that source-language code explicitly, for example `en`, `ja`, and `zh`, and code no longer infers it from `Region`
   - `Spec_Master.csv` now starts with `spec_row_key`; `document_key` is still the target dimension, but not the unique row key
   - `document_key` is a derived helper column and may use either `[Model]_[Region]` or `[Model]_[Region]_[Source_lang]`
   - `Line_order` is required for spec rebuilds: use `1` for one-line rows and `1`, `2`, `3`, ... for multi-line values
   - the solar-panel input range in the eight shared-language charging-method pages comes from `页面占位参数`: use `Page=charging_methods`, `Row_key=pv_input_range`, `Slot_key=value`, and preserve the approved language-specific dash/spacing exactly; the template token is `|PV_INPUT_RANGE|`. The current JE-1000F US/EU/AU/KR and JE-1500D pt-BR rows were F6-approved, seeded, and read back on 2026-07-31; a future target still needs its own exact-value approval plus post-sync `diff-report`
   - the connector name in those charging pages uses `Page=charging_methods`, `Row_key=dc_input_connector`, `Slot_key=value` and token `|DC_INPUT_CONNECTOR|`; the shared UPS transfer time uses `Page=ups_mode`, `Row_key=ups_transfer_time`, `Slot_key=value` and token `|UPS_TRANSFER_TIME|`. Keep localized units in the value and keep the separate `0 ms` incompatibility caution as prose. The same five current document keys were seeded in the 2026-07-31 F6 batch; never blindly clone their values into a new target
   - `Row_label_en`, `Param_en`, and `Value_en` are no longer supported; rename them to `*_source`
   - `Row_label_footnote_refs`, `Param_footnote_refs`, and `Value_footnote_refs` store comma-separated `Footnote_id` values; do not handwrite `①②③` into visible spec text
   - `symbols_blocks.csv` uses `Market`, `Model`, and `Source_lang`; it does not use `Region`; use `Market=Global` when one symbols row is shared across markets
   - `symbols_blocks.csv` uses `image_path` for the icon asset referenced by each symbols-table row; phase2 sync fills it from the Base `Figure` attachment when present
   - `symbols_blocks.csv` can also use `Is_Latest` and `Market` as row conditions: rows marked false are skipped, and `Market` must include the current build region such as `US` or `EU`
   - use `block_type=table_row` for the normal symbol/meaning grid; use `block_type=signal_row` for signal metadata, with rendered `symbol_key` values `warning`, `caution`, `note`, and `tips`, plus labels such as `danger` that Word/HTML rewrite should recognize
   - `order` values must be unique within each symbols table section; normal symbols rows are sorted and split evenly into two columns, so the old `column_group` field has been removed

3. Review working layer
   - [`docs/_review/<model>/<region>/index.rst`](../docs/_review)
   - [`docs/_review/<model>/<region>/page/*.rst`](../docs/_review)
   - [`docs/_review/<model>/<region>/generated/<model>/*.rst`](../docs/_review)
   - [`docs/_review/<model>/<region>/manifest.json`](../docs/_review)
   - [`docs/_review/<model>/<region>/overrides/**`](../docs/_review)
   - Responsibility: target-specific review editing, Git review, revision history, final release source after review starts
   - Accepted Feishu cloud-doc revisions back-port through `python tools/cloud_doc_backport.py run-review-branch --doc-name <doc name> --cloud-doc <url>` — the blessed path: it resolves the review branch, diffs the cloud-doc against a **render baseline** (so deltas are the reviewer's real edits, not RST-source noise), and with `--write --push` applies only Class R prose and opens a draft PR into the review branch. The older `run-review --doc-url ... --source-path docs/_review/...` diffs against the RST source and is now **guarded**: a `--write` against an `.rst` baseline is refused and steered to `run-review-branch` unless `--allow-rst-baseline` is set. The runners write diff/apply/run reports and are dry-run by default. Add `--write` only after reviewing the apply report; write mode patches guarded review prose, runs residual verification, and marks the run `PR_READY` only when the review source changed and verification passed. Data-like deltas stay report-only and also get `cloud_doc_backport_source_table_suggestions.md` with candidate source tables and operator steps. Use `python tools/cloud_doc_backport.py open-pr --manifest reports/cloud_doc_backport/<run-id>/cloud_doc_backport_run.json` only after `PR_READY`; it commits the changed `_review` source to a draft PR and leaves local reports out of the commit.
   - you do not have to remember the backport: the daily [`../.github/workflows/backport-reminder.yml`](../.github/workflows/backport-reminder.yml) sentinel compares every InReview cloud doc against its committed render baseline and opens/updates a `[backport-reminder]` issue while un-backported edits exist (report-only; running the backport advances the baseline and the issue closes itself)
   - the operator-facing playbook for the whole closed loop (revision ledger commands, TM harvest approval, sentinel handling, annotated PDFs, first-run checklist) is [`./closed_loop_ops_guide.md`](./closed_loop_ops_guide.md)

   - Cloud-doc backport strips Feishu highlight tags before writing reports, keeps image-only/token-only changes out of source-table suggestions, resolves page-value rows to `Page_Placeholders_Source` when the phase2 value index and record sidecar identify the row, and requires human semantic review for output/button terminology swaps. If GitHub rejects automatic PR creation after the branch push, use the printed compare link and PR body to create the draft PR manually.

4. Runtime build layer
   - [`docs/_build/<model>/<region>/rst/**`](../docs/_build)
   - [`docs/_build/<model>/<region>/html/**`](../docs/_build)
   - [`docs/_build/<model>/<region>/word/**`](../docs/_build)
   - [`docs/_build/<model>/<region>/pdf/**`](../docs/_build)
   - [`docs/index.rst`](../docs/index.rst)
   - Responsibility: generated bundle plus final outputs

Rules:

- Before review starts, use template/data to create the first draft.
- To move one document into review automatically, trigger the review-init flow first; that flow creates the branch, seeds `docs/_review`, and opens the PR.
- After review starts, use [`docs/_review/...`](../docs/_review/) as the daily editing surface for that target.
- Edit templates only when the change should be shared by multiple manuals.
- For manually maintained parallel-language template pages, keep one source-language template as the structure owner and update the derived-language templates in the same change when shared headings, section order, placeholder sets, includes, or `.. only::` model gates change.
- Current example: if `charging.rst` changes in the source-language family template, keep the same battery-pack `.. only:: model_je_2000e` block boundary in the corresponding derived-language templates instead of updating only one language.
- Edit CSV when product parameters change.
- Treat [`docs/_build/...`](../docs/_build/) as generated runtime output.
- Keep region-family differences explicit where they are real: spec data, certification text, unit conventions, and `meaning_of_symbols` stay family-specific.
- When design needs to review layout or page effect, share a review handoff workspace built from `_review`, not the raw `.rst`.
- when that workspace is packaged for review sharing, let GitHub Actions build the package first and keep it as an artifact
- Read the Docs renders the frozen Web Publish catalog from `Hello-Docs/main:docs/publish/web/` after the generated publish PR is merged; it does not replace review-preview packaging or formal print release outputs
- designers should start from the workspace root, then pick a family, model, and language before opening the rendered manual or family diff page
- the workspace root now keeps the primary review actions plus a compact document-identity card with product name, manual title, model, region, and language
- the packaged preview now also includes model-scoped `downloads/<family>/<model>/<lang>/review-manual.docx`, `downloads/<family>/<model>/change-report.xlsx`, the raw diff CSV files, and `generated/workspace.json`
- families without `_review` content are hidden, so the preview only shows available families
- the packaged `changes/index.html` now opens a family hub first, and each family hub fans out to model-specific change pages
- if the target branch already has an open pull request, each new push to that PR branch will rerun `Review Preview Package` automatically when the changed files match the workflow paths
- after that workflow finishes, download the uploaded artifact when you need the packaged review workspace; it is no longer pushed to Vercel automatically
- if there is no open pull request yet, trigger `Review Preview Package` manually from the `Actions` tab

---

## 3. Current Build Pipeline

The cross-platform entrypoint is [`build.py`](../build.py).
It wraps [`tools/build_docs.py`](../tools/build_docs.py), which still drives the actual build logic.
If you need the fixed `US/en + US/es + US/fr + JP/ja` export set, use [`../scripts/build_us_jp_manuals.ps1`](../scripts/build_us_jp_manuals.ps1) as a thin wrapper over [`../scripts/build_us_jp_manuals.py`](../scripts/build_us_jp_manuals.py).

Current flow:

1. `python build.py sync-data|process-build-queue|message-control-dry-run|rst|html|word|pdf|all|idml|review|check|asset-check|asset-intake|sync-review|publish|diff-report|release-manifest|handoff|preview|fast|doctor`
1. `python build.py listen-message-control --config configs/config.us.yaml`
2. [`tools/build_docs.py`](../tools/build_docs.py) validates config and layout params
3. target `model` and `region` are resolved from CLI or `build.targets`
4. `product_name` is resolved from the active snapshot root, defaulting to [`data/phase2/Spec_Master.csv`](../data/phase2/Spec_Master.csv); explicit `--data-root` still overrides the default
5. CSV-backed pages are generated by [`tools/csv_page_build.py`](../tools/csv_page_build.py)
6. [`tools/gen_index_bundle.py`](../tools/gen_index_bundle.py) materializes the runtime bundle
7. the runtime bundle is written to [`docs/_build/<model>/<region>/rst/`](../docs/_build)
8. if source mode is `auto` or `review` and a review bundle exists, review content is overlaid onto the runtime bundle
9. after frozen attachment aliases are staged, the asset finalizer scans the final `index.rst` include closure, resolves semantic `asset:` references for the exact model/region/language, rewrites final bundle-relative paths, and freezes the bundle's asset evidence
10. [`docs/index.rst`](../docs/index.rst) is refreshed to point at all existing bundle roots
11. `html`, `word`, and `pdf` outputs are built from the prepared bundle when requested
12. `python build.py review` seeds [`docs/_review/<model>/<region>/`](../docs/_review) from the runtime bundle when review starts; semantic asset identities are restored from the runtime rewrite provenance before review files are written
13. `python build.py sync-review` refreshes parameter-driven review files from the runtime bundle without replacing the whole review bundle
14. `python build.py check` runs config/layout validation, prepares the bundle, and scans for bundle issues
15. `python build.py asset-check` validates the image-asset registry and resolves approved exports for renderer imports; `--allow-temporary` is diagnostic/operator inspection for `asset-check` only, while normal bundle assembly always rejects temporary, missing, and quarantined semantic assets; `--publish` is the stricter registry-wide status gate; `--refresh` dry-runs a machine recomputation of materialized SHA-256 values and requires explicit `--write` for an atomic registry update, with missing/malformed exports failing closed
    - editable `.ai` deliveries stay out of Git; the maintainer follows [`closed_loop_ops_guide.md` §4.9.2](closed_loop_ops_guide.md#492-ai-交付与登记一页流程) for hash-first duplicate detection, upload to the dedicated Base asset-source table, and download verification; the legacy illustration table is not a fallback
    - sensitive App/QR candidates remain quarantined after extraction; a registry row may declare `source=reviewed-promotion:<promotion_id>` only when its JSON contract under `data/asset_promotions/` still matches the reviewer decision, exact target scope, source AI/reference PDF/recipe/evidence identities, all candidate/output bytes, and deterministic composition by full SHA-256. During the carrier migration, the Python compatibility shadow is read in parallel and exact parity plus the whole-contract SHA-256 are required; any drift fails closed without a legacy-image fallback
16. `python build.py asset-intake --asset-source-key <key> --asset-source-file <master.ai> --asset-recipe <recipe.json> --asset-output-root <new-dir>` freezes and verifies a PDF-compatible Illustrator source, then writes cleaned page archives/previews, recipe exports, `manifest.json`, `artifacts.csv`, and a deterministic ZIP into a new isolated directory
    - this action is package-only: it does not edit the source/worktree/registry/Base, and it fails closed on source/runtime/hash/path/private-marker drift; upload and promotion remain explicit reviewed steps in the three new `04_资产*` tables
17. `python tools/process_docs/build_review_preview.py` packages review HTML, diff-report HTML/CSV/XLSX, and optional review Word output for design sharing
18. `python build.py diff-report` exports review diffs, defaulting to the resolved target review root
19. `python build.py release-manifest` writes release traceability JSON / CSV for one explicit target; add `--version <version>` to freeze and bind the exact phase2 input under that release version
20. `python build.py preview` materializes one exact page selector under a preview-only output root
21. `python build.py fast` materializes a runtime-only draft without export

Important:

- `python build.py rst` only materializes the RST bundle.
- `python build.py sync-data --config configs/config.us.yaml --data-root data/phase2` is the explicit local refresh step for Feishu/Lark content; build commands default to a valid phase2 snapshot when one exists and only fetch online data when you run `sync-data`.
- `python build.py sync-data --config configs/config.us.yaml --data-root data/phase2 --dry-run` is the safest readiness probe for a new machine because it checks the local CLI/env prerequisites before attempting the real sync.
- `python build.py process-build-queue --config configs/config.us.yaml` is the explicit local consume-and-build step for the Feishu `Document_link` task table; it never runs implicitly from `sync-data`, `check`, or `publish`.
- static legal/support placeholders such as `WARRANTY_EMAIL` and `LEGAL_COMPANY_NAME` are injected from `build.rst_substitutions` in the active config; keep US values in US configs and override EU / pt-BR values there instead of hardcoding region-specific names in shared templates.
- `python build.py message-control-dry-run --message "publish JE-1000F us-merged from branch feature/review-123"` is a maintainer-only Phase 0 helper for the planned Feishu message plus OpenClaw control layer; it returns structured JSON only and does not dispatch GitHub workflows or write back any Feishu fields yet.
- `python build.py listen-message-control --config configs/config.us.yaml` is the matching no-server runtime entry: it keeps one local Feishu IM long connection through `lark-cli`, supports the same bounded action set as the webhook adapter, and is the recommended path when you want one local machine to receive Feishu app messages and trigger remote GitHub Actions directly
- when you need the same machine to keep the old local Feishu app unchanged, initialize the new app under `FEISHU_IM_LARK_CLI_HOME` first and then start `listen-message-control`; that isolates the new app's `lark-cli` config from the default home used by the old app
- when the queue row carries `Git_ref`, that queue step keeps the latest `main` code/toolchain and overlays only `docs/_review` from the named review branch; queue Draft/Publish builds treat `Git_ref` as review content, not as an alternate worker/toolchain branch.
- `python build.py word`, `python build.py html`, and `python build.py pdf` all prepare the RST bundle first.
- `python build.py all` runs `html`, `word`, and `pdf` after the same prepare step.
- RST may reference an approved asset by identity, for example `.. image:: asset:operation/ac_output`. Bundle finalization accepts only PNG/JPG/JPEG/SVG/PDF exports; `.ai` is archive input and is never a renderer fallback.
- PDF-compatible Illustrator masters are extracted through `tools/asset_intake.py` and a committed `data/asset_recipes/*.json` contract. Use `retain_vector_drawings` only when the wanted illustration and burned labels are separate source drawing groups: declare ascending source indices, explicit fill overrides and stroke suppressions, review the quarantine render at 12x, then pin the approved output hash. The operator is exclusive after `crop` and fails closed on an out-of-range/non-intersecting group or an unsupported vector item; it is not a coordinate whiteout mechanism.
- Each finalized bundle contains `asset_usage_manifest.json`, `asset_registry_snapshot.csv`, and `bundle_manifest.json`. `registry-uri` means the bytes came from the frozen approved registry export; `review-override` keeps the `asset_key` while recording the explicit override bytes; `legacy-path` means a path-based image was staged and accounted for but has not yet been migrated under registry status/scope control.
- Shared templates (`docs/templates/`) are bulk-migrated to `asset:` — every `common_assets` image and raw-HTML `src` now resolves through the registry, so status/scope/hash gating applies to all of them; write new template image references as `asset:<asset_key>`, not as file paths. `legacy-path` accounting remains for any reference that has not (or cannot) be keyed.
- `release-manifest` carries an `assets` section: the bundle fingerprint, the registry-snapshot hash, and every registry-backed asset the build actually consumed (key, format, content SHA, status, resolution source); the release CSV gains `assets_registry_count`, `assets_legacy_path_count`, `assets_bundle_sha256` and `assets_registry_snapshot_sha256`. `publish` runs an asset gate after the last prepare and before the manifest, so a bundle that consumed a `🔧临时替代`, `❌缺失` or `⛔隔离` asset — or that carries no frozen lineage — fails before anything is released. The gate does not block `legacy-path` images — references with no registry attribution at all — but their count is recorded so the debt stays visible; JE-1000F US reached zero. Synced Feishu attachment images (`_attachments/lcd_icons`, `_attachments/symbols`) are attributed to their `feishu/*_attachments` collection rows as `feishu-attachment` entries: each manifest row records the exact bytes that shipped, the collection row's registry status gates publish for the whole column, and the RST keeps its path reference (file identity is the Feishu token, so these are never keyed per file).
- Queue Publish also freezes the complete manifest-backed phase2 root under `reports/releases/<model>/<region>/<lang>/versions/<version>/snapshot/`. The release JSON/CSV points to this archive instead of the mutable live root and records `snapshot_sha256`, source-manifest revision, freeze time, target matrix, commit-derived `SOURCE_DATE_EPOCH`, and the DOCX/Markdown/PDF byte-equivalence contract. When `Git_ref` supplies the approved review content, the same reproducibility record binds its exact review commit, active target path, and tree SHA. The publish-entry gate first verifies the complete overlaid file set and every Git blob. Approved-reference targets then keep those page bytes unchanged as `review-asis`; unregistered targets may still perform the historical review-parameter sync. Deterministic target-asset staging may mutate generated files inside the subtree, and the late manifest binds the already verified source tree instead of treating those build products as new source. The clean gate remains active outside the one target subtree, and an absent or changed verified tree SHA fails closed. Keep the archive for the full release lifetime; same-version retries may reuse byte-identical data, but changing the binding or editing archived bytes fails closed. Run `python build.py release-rebuild-verify --manifest <manifest.json>` on the recorded toolchain to rebuild in a disposable worktree at the recorded Git SHA, restore the bound review overlay, and compare all three SHA-256 values; its default evidence is `versions/<version>/rebuild_verification.json`.
- A versioned release manifest also records one stable `release_tag` covering
  model, region, every build language, and version. Preview it with
  `python tools/release_tag.py --manifest <manifest.json>`; only after artifact
  acceptance and `release-rebuild-verify` pass should an operator repeat the
  command with `--write --push`. Existing tags cannot be silently rebound to a
  different commit or manifest. Vercel rollback, prior Word/PDF re-delivery,
  historical rebuild, and the operator-owned timed-drill sheet are documented
  in [`closed_loop_ops_guide.md`](closed_loop_ops_guide.md#410-发布标记与回滚k14).
- A product/market export keeps its own key and declares `override_for=<shared asset_key>` in `data/asset_registry.csv`; do not narrow or overwrite the shared row. The same shared template URI then resolves to that export only for the matching model/region/language. No match falls back to the shared row; multiple matches stop the build.
- `sync-data` refreshes `data/asset_registry.csv` from the `04_资产定义` table as a **derived file**, alongside `model_capabilities.csv`. It is an overlay, not a replace: the Base owns 类别 / 语言维度 / 状态 / 待无字化 / 适用机型 / 适用区域 / 语言变体, while the repo keeps `导出物路径` and `内容哈希` (they describe committed bytes) and `备注` (maintenance history — the Base's notes are intake rationale, kept separately). Rows are never deleted, so an asset dropped from the Base leaves its registry row standing rather than silently breaking templates that resolve it; the git diff of the CSV is the review surface. Table coordinates come from the frozen [`data/asset_base_bindings.json`](../data/asset_base_bindings.json) unless `FEISHU_PHASE2_ASSET_DEFINITIONS_TABLE_ID` is set, so no extra secret is needed. A Base value the resolver would reject fails the sync instead of landing in the registry.
- The Feishu archive/write contract permits only the three separately created `04_资产源文件`, `04_资产定义`, and `04_资产导出物` tables; their live binding is frozen in [`data/asset_base_bindings.json`](../data/asset_base_bindings.json), and the JE-1000F US master is the first source whose AI/ZIP/manifest attachments passed download hash verification. If those tables are inaccessible, stop and leave the source pointer empty; do not read, write, or fall back to the old illustration or staging intake table.
- build actions except `fast` clean the current target output first; on Windows, close File Explorer, browser, Word, or PDF windows opened under [`docs/_build/`](../docs/_build) before rerunning, or use `--no-clean` for an in-place rebuild.
- `python scripts/local_build.py check|diff-report|release-manifest|publish ...` keeps generated verification/build outputs under `.tmp/staging/docs/_build`, `.tmp/staging/reports/version_tracking`, and `.tmp/staging/reports/releases` without making the operator remember `--staging-root`.
- `review` does not accept `--staging-root` because it seeds the real repo `docs/_review`, so it is intentionally excluded from `scripts/local_build.py`.
- `python build.py review` prepares a runtime draft from template/data, then seeds review only if review does not already exist.
- `python build.py review --refresh-review` intentionally replaces an existing review bundle from template/data.
- `python build.py sync-review` is the safe path after snapshot data changes during review.
- review builds auto-run the same parameter sync before `html`, `word`, `pdf`, and `publish`, so parameter lines stay current without overwriting the rest of the review prose. `check` does **not**: it validates the review surface as committed, because it is the command the pre-PR checklist prescribes and a validation run should not rewrite tracked files under `docs/_review`. Ask for the refresh explicitly with `check --refresh-review` (or `check --source review`).
- the parameter sync only refreshes a placeholder line that still matches its template's shape. If a reviewer edited anything else on that line — the surrounding wording, or the indentation — the line is left alone and its parameters go stale, rather than the edit being reverted to the template's text. `python tools/check_review_branch_sync.py` is the notice path for a shared-source change an open review branch still has to pick up.
- a target review manifest may declare exact `page/*.rst` or `generated/*.rst` files in `sync_preserve_paths`; those paths remain byte-stable during automatic or manual `sync-review`, and each skip is written to `last_sync_preserved_files`. Remove the declaration before intentionally refreshing that page.
- when a single-language build targets a merged review branch and only `docs/_review/<model>/US/` or `docs/_review/<model>/EU/` exists, that auto sync falls back to the merged review root instead of silently skipping the refresh, then remaps the shared-family review pages onto the requested single-language page order before export.
- if you intentionally want one review page replaced from runtime, keep using `sync-review --page-file <file>`; if you need the whole review bundle replaced, use `review --refresh-review`.
- single-language US English review targets still use `docs/_review/<model>/US/en/`, Brazil Portuguese review targets use `docs/_review/<model>/pt-BR/pt-BR/`, and single-language EU review targets still use `docs/_review/<model>/EU/<lang>/`, but the merged `configs/config.us.yaml` / `configs/config.eu.yaml` queue/review flows use the shared roots `docs/_review/<model>/US/` and `docs/_review/<model>/EU/`.
- for that merged US flow, `Spec_Master.Source_lang` / `*_source` values are required, while CSV-driven non-source language columns may be blank because runtime lookup falls back to the source-language text automatically.
- for the recommended new flow, sync Feishu/Lark into [`data/phase2/`](../data/phase2) first; once a valid snapshot exists, `rst`, `check`, `diff-report`, `release-manifest`, and `publish` default to it, while explicit `--data-root` still overrides the source root.
- `build.py validate` checks config/layout even on a fresh clone without `data/phase2`; pass `--data-root tests/fixtures/phase2` when you want the full Spec_Master content validation without syncing live Feishu data.
- `build.py new-line --config <config> --dry-run` is the Stage 3
  read-only onboarding plan. It resolves the config inheritance chain, target
  identity, manifest pages, and template/recipe references, then reports
  `new-line-scaffold/v1`, `whitelist_diff`, and the F6-blocked
  `data/phase2` source surface. `--write` requires explicit
  `--output-config` and `--output-manifest` paths, optionally creates a
  target-local review override scaffold with `--asset-override-root`,
  refreshes only the committed fixture through `fixture-refresh`, and automatically runs the
  normal `build.py check` gate. It never writes production `data/phase2`
  or Feishu source tables; those remain a separately approved F6 operation.
- `build.py new-line --seed-plan --config <config> --model <model> --region
  <region>` is the zero-write F6 seed plan. It reports the target
  `Document_key` row, page-placeholder clone candidates, and the local
  source-table field-create helper. If multiple same-model source documents
  exist, pass `--seed-source-document-key <key>`; otherwise the plan reports
  `needs_input` instead of guessing. The command does not call Feishu or write
  `data/phase2`; row/field creation still requires the separately approved F6
  write path.
- `python build.py check`, `word`, `html`, and `pdf` use `source=auto` by default, so they build from `_review` once review exists.
- `python build.py publish` uses review content only, then runs `check -> diff-report -> word -> pdf -> md -> release-manifest` as one formal release command.
- for both `Publish` and `Web Publish`, keep `Document_link.Git_ref` pointed at the active review branch. Print artifacts and responsive Web output are separate builds but must resolve the same approved content revision.
- `python build.py handoff` now generates a minimal handoff package under [`docs/_handoff/`](../docs): it resolves explicit baseline/current inputs, loads supported `rst/html` inputs, generates rule-based add/delete/replace records, copies referenced draft images into `draft/assets/`, and writes `draft/manual.md`, `draft/manual.docx`, optional `draft/manual.html`, `changes/change_log.csv`, `changes/change_log.xlsx`, `changes/change_summary.md`, `handoff/design_handoff.md`, and `manifest.json`. It does not yet provide final page mapping or advanced semantic change classification.
- `.\scripts\build_us_jp_manuals.ps1 --model <MODEL> --formats html,word,pdf` is the one-command wrapper for the fixed four-language export pack.
- `.\scripts\build_us_jp_manuals.ps1 --model <MODEL> --build-action validate --languages en,fr` runs one explicit `build.py` action across the selected matrix targets instead of deriving actions from `--formats`.
- `.\scripts\build_us_jp_manuals.ps1 --model <MODEL> --formats html --open-html` builds the selected HTML set and opens the generated HTML entry pages.
- `check` now catches stale foreign model names, unresolved placeholders, missing assets, and contract-required spec keys / page-value selectors / assets.
- review overrides only overlay `overrides/_assets/**`, `overrides/_static/**`, and `overrides/renderers/**` into the runtime bundle.

---

## 4. Materialized Bundle Layout

For a target such as `JE-1000F / US`, the working bundle now lives here:

- [`docs/_build/JE-1000F/US/rst/index.rst`](../docs/_build/JE-1000F/US/rst/index.rst)
- [`docs/_build/JE-1000F/US/rst/page/*.rst`](../docs/_build/JE-1000F/US/rst/page)
- [`docs/_build/JE-1000F/US/rst/generated/JE-1000F/*.rst`](../docs/_build/JE-1000F/US/rst/generated/JE-1000F)
- [`docs/_build/JE-1000F/US/rst/conf.py`](../docs/_build/JE-1000F/US/rst/conf.py)
- [`docs/_build/JE-1000F/US/rst/conf_base.py`](../docs/_build/JE-1000F/US/rst/conf_base.py)
- [`docs/_build/JE-1000F/US/rst/_static/**`](../docs/_build/JE-1000F/US/rst/_static)
- [`docs/_build/JE-1000F/US/rst/renderers/**`](../docs/_build/JE-1000F/US/rst/renderers)
- `docs/_build/JE-1000F/US/rst/asset_usage_manifest.json` — every semantic, review-override, and legacy image consumer plus rewrite provenance
- `docs/_build/JE-1000F/US/rst/asset_registry_snapshot.csv` — the exact registry bytes used for this bundle
- `docs/_build/JE-1000F/US/rst/bundle_manifest.json` — final file records plus `bundle_sha256` over the RST closure, config, support trees, and asset sidecars

This is the generated bundle consumed by Sphinx, HTML export, Word export, and PDF export.
It is not the editing surface. After review starts, `_review/...` is overlaid onto this bundle before publish.

---

## 5. Git Tracking Rule for Review Bundles

The current repo allows two Git-visible surfaces:

- [`docs/_build/**/**/rst/**`](../docs/_build) is no longer ignored
- [`docs/_review/**`](../docs/_review) is emitted as a review-first snapshot
- sibling outputs such as [`docs/_build/**/**/html/**`](../docs/_build), `word/**`, and `pdf/**` remain build artifacts

This gives you two benefits:

1. You can commit generated review bundles per target and keep reviewable history.
2. You can export Git diffs for a single model or region as CSV and HTML reports.

What this does not change:

- `_build/.../rst/**` is still regenerated on the next build.
- `_review/.../**` is now the durable review-editing surface for that target once review starts.
- `python build.py review --refresh-review` is the only path that intentionally replaces the existing review content from template/data.

Recommended use:

1. Seed the target review bundle once with `python build.py review --config ...`
2. Edit [`docs/_review/<model>/<region>/**`](../docs/_review)
3. Build preview/final outputs with `check/html/word/pdf`
4. Commit the resulting review bundle
5. Use `python build.py diff-report ...` when you need a table-style change export

For the current maintainer branch model, pull request rules, and GitHub protection settings, use [`../code-as-doc/dev/git_branching_guide.md`](../code-as-doc/dev/git_branching_guide.md).

---

## 5. Which Files You Should Edit

Edit these when the change should be shared across products or when creating the first draft:

- [`docs/templates/page_us-en/*.rst`](../docs/templates/page_us-en)
- [`docs/templates/page_jp/*.rst`](../docs/templates/page_jp)

Parallel-language template rule:

- `docs/templates/page_us-en/*.rst` is the current source-language structure owner for manually maintained US prose templates.
- `docs/templates/page_us-es/*.rst` and `docs/templates/page_us-fr/*.rst` are derived-language counterparts and must be updated in the same round when the source-language page changes shared section structure or `.. only::` gating.
- JP currently has only `ja`, so there is no second JP derived-language template to mirror today, but any future JP derived-language page should follow the same rule.
- before adding a new Markdown manual into the template library, fill out [`../code-as-doc/dev/manual_template_intake_checklist.md`](../code-as-doc/dev/manual_template_intake_checklist.md) so section mapping and placeholder rules are decided before page edits start.

Edit these when safety/spec parameters change:

- [`data/phase2/symbols_blocks.csv`](../data/phase2/symbols_blocks.csv)
- [`data/phase2/Spec_Master.csv`](../data/phase2/Spec_Master.csv)
- [`data/phase2/Spec_Footnotes.csv`](../data/phase2/Spec_Footnotes.csv)
- [`data/phase2/spec_titles.csv`](../data/phase2/spec_titles.csv)

Edit these when a safety intro page needs copy/layout changes:

- edit [`docs/templates/page_us-en/safety_en.rst`](../docs/templates/page_us-en/safety_en.rst), [`docs/templates/page_us-fr/safety_fr.rst`](../docs/templates/page_us-fr/safety_fr.rst), or [`docs/templates/page_us-es/safety_es.rst`](../docs/templates/page_us-es/safety_es.rst) for US safety intro changes
- edit [`docs/templates/page_jp/safety_ja.rst`](../docs/templates/page_jp/safety_ja.rst) when the Japanese safety intro page needs copy or layout changes
- edit [`docs/templates/page_jp/01_meaning_of_symbols.rst`](../docs/templates/page_jp/01_meaning_of_symbols.rst) when the detailed Japanese safety warnings need changes

Edit these during target review and final polish:

- [`docs/_review/<model>/<region>/index.rst`](../docs/_review)
- [`docs/_review/<model>/<region>/page/*.rst`](../docs/_review)
- [`docs/_review/<model>/<region>/generated/<model>/*.rst`](../docs/_review)
- [`docs/_review/<model>/<region>/overrides/_assets/**`](../docs/_review)
- [`docs/_review/<model>/<region>/overrides/_static/**`](../docs/_review)
- [`docs/_review/<model>/<region>/overrides/renderers/**`](../docs/_review)

Do not use these as the primary authoring source:

- [`docs/_build/<model>/<region>/rst/page/*.rst`](../docs/_build)
- [`docs/_build/<model>/<region>/rst/generated/<model>/*.rst`](../docs/_build)
- [`docs/_build/<model>/<region>/rst/index.rst`](../docs/_build)
- [`docs/index.rst`](../docs/index.rst)

You may commit `_review/...` for review history because it is now the target editing surface after review starts.

---

## 6. How Safety and Spec Pages Work

Safety intro pages are now maintained as fixed RST templates and then materialized into the bundle.
The standalone user maintenance instructions page lives in shared templates and is included before the `symbols` page.

Primary inputs:

- [`docs/templates/page_us-en/safety_en.rst`](../docs/templates/page_us-en/safety_en.rst)
- [`docs/templates/page_us-fr/safety_fr.rst`](../docs/templates/page_us-fr/safety_fr.rst)
- [`docs/templates/page_us-es/safety_es.rst`](../docs/templates/page_us-es/safety_es.rst)
- [`docs/templates/page_shared/en/01_user_maintenance_instructions.rst`](../docs/templates/page_shared/en/01_user_maintenance_instructions.rst)
- [`docs/templates/page_jp/safety_ja.rst`](../docs/templates/page_jp/safety_ja.rst)

JP manual note:

- [`docs/manifests/manual_jp.yaml`](../docs/manifests/manual_jp.yaml) includes [`docs/templates/page_jp/safety_ja.rst`](../docs/templates/page_jp/safety_ja.rst) directly
- edit that template when the JP safety intro page must change
- the detailed JP warning content remains in [`docs/templates/page_jp/01_meaning_of_symbols.rst`](../docs/templates/page_jp/01_meaning_of_symbols.rst)
- the old `content_blocks.csv` safety source has been removed from the active repo flow

Generated bundle output:

- materialized page include: [`docs/_build/<model>/<region>/rst/page/safety_<lang>.rst`](../docs/_build)

Symbols content is generated from:

- [`data/phase2/page_registry.csv`](../data/phase2/page_registry.csv)
- [`data/phase2/symbols_blocks.csv`](../data/phase2/symbols_blocks.csv)

`symbols_blocks.csv` notes:

- use one `table_row` per symbols-table entry
- use `signal_row` entries for warning/caution/danger/note/tip signal structure; the signal token (`symbol_key`), target scope, order, and optional icon asset stay in `symbols_blocks.csv`. Visible signal labels and meanings are authored in `Manual_Copy_Source.csv`, translated through Translation Memory rows tagged `manual_copy`, and rendered from generated `Localized_Copy.csv`; legacy `label_*` and `aliases_*` columns are compatibility mirrors for old variants and rewrite detection only
- use `Market` and `Model` to target symbols rows; `symbols_blocks.csv` does not use `Region`
- use `Source_lang` for the row's source-language code, for example `en` or `ja`
- use `Market=Global` when one row should be shared across markets
- `image_path` stores the RST image reference path for that icon
- keep `symbol_key` stable so renderer alt text and layout metadata still resolve correctly; do not duplicate `copy_type=alt_text` rows in `Localized_Copy.csv`

Troubleshooting content is generated from:

- [`data/phase2/troubleshooting_blocks.csv`](../data/phase2/troubleshooting_blocks.csv)
- [`docs/templates/**/10_troubleshooting.rst`](../docs/templates/page_shared/en/10_troubleshooting.rst)

`troubleshooting_blocks.csv` notes:

- maintain the online TROUBLESHOOTING Base table, then run `python build.py sync-data --config configs/config.us.yaml --table troubleshooting --data-root data/phase2`
- use `Region`, `Model`, and `Is_latest` to select active rows; blank placeholder records are ignored
- keep page title, intro, table headers, widths, and header-row settings in each language's `10_troubleshooting.rst`
- keep error-code rows and corrective-measure copy in the TROUBLESHOOTING Base table; the RST template exposes `{{ troubleshooting_rows_rst }}` where those rows are inserted
- localized corrective text lives in per-language `corrective_measures_<lang>` columns; the current snapshot set is `corrective_measures_en/fr/es/pt-BR/br/de/it/ukr/jp/zh/ko`. A new output language adds its column in the Base table first, then reaches the snapshot through `sync-data`

Spec content is generated from:

- [`data/phase2/Spec_Master.csv`](../data/phase2/Spec_Master.csv)
- optional [`data/phase2/Spec_Footnotes.csv`](../data/phase2/Spec_Footnotes.csv)
- optional [`data/phase2/Spec_Notes.csv`](../data/phase2/Spec_Notes.csv)
- optional [`data/phase2/spec_titles.csv`](../data/phase2/spec_titles.csv)

Generated bundle output:

- [`docs/_build/<model>/<region>/rst/generated/<model>/spec_<lang>.rst`](../docs/_build)
- materialized page include: [`docs/_build/<model>/<region>/rst/page/spec_<lang>.rst`](../docs/_build)

[`Spec_Master.csv`](../data/phase2/Spec_Master.csv) remains the build-time read model for spec sections, rows, and page-value placeholder records.
In Feishu, maintain those rows through `规格参数明细` and `页面占位参数`, then refresh the local snapshot with `sync-data --table spec_master` or a focused `spec-master-rebuild`.

---

## 7. Placeholder Rules

Core placeholders resolved from [`Spec_Master.csv`](../data/phase2/Spec_Master.csv):

- `|PRODUCT_NAME|`
- `|PRODUCT_NAME_BOLD|`
- `|PRODUCT_SHORT_NAME|`
- `|PRODUCT_SHORT_NAME_BOLD|`
- `|MODEL_NO|`

Resolution source:

- `product_name` comes from `Row_key=product_name`
- `model_no` comes from `Row_key=model_no`
- `PRODUCT_SHORT_NAME` is derived from `PRODUCT_NAME`

`Spec_Master.csv` `Page` note:

- `Page` can be a comma-separated list
- use `Product overview` for Product overview-only page-value rows such as front/side-view callouts
- use `Product overview, specifications,` when the same row is intentionally shared by both pages
- `Row_label_source`, `Param_source`, and `Value_source` should store the row's source-manual text
- `Source_lang` should store the normalized source-language code for the row, such as `en`, `ja`, or `zh`; do not expect code to infer it from `Region`
- `document_key` should be either `[Model]_[Region]` or `[Model]_[Region]_[Source_lang]`
- `Row_order` is now the explicit row order inside each `document_key + Page + Section`; `Line_order` only controls the order of multiple lines inside one logical row
- `Line_order` is required; single-line rows use `1`
- generated `spec_titles.csv section_order` can hold the default order for visible spec sections, but a filled `Spec_Master.csv Section_order` overrides it
- `project_code` / `项目代码` is no longer used in `Spec_Master.csv`; choose rows by `Region` + `Model`
- when a build target is passed in document-key style such as `JE-1000F_JP` or `JE-1000F-JP`, the spec lookup normalizes it back to the base model `JE-1000F` and still uses the explicit `Region`, so a `JP` target continues to read `JP` rows
- source-language rows must keep their actual source text in `Row_label_source`, `Param_source`, and `Value_source`

For page-value rows, `Row_key` now keeps only the concept itself. Human editing should happen through `Slot_key`.

Examples:

- `Row_key=main_power_button`, `Slot_key=label` -> `|MAIN_POWER_BUTTON_LABEL|`
- `Row_key=ac_input`, `Slot_key=side.spec` -> `|SIDE_AC_INPUT_SPEC|`
- `Row_key=battery_pack_name`, `Slot_key=value` -> `|BATTERY_PACK_NAME|`

Derived behavior:

- non-empty placeholders also get `..._BOLD`
- placeholders ending in `_LABEL` also get `..._LOWER`
- multi-line page-value rows produce suffixed placeholders such as `|EXAMPLE_KEY_2|`

---

## 8. Build Commands

Cross-platform entrypoint:

```powershell
python build.py doctor --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py doctor --data-plane --config configs/config.us-en.yaml --model JE-1000F --region US --data-root tests/fixtures/phase2
python build.py rst
python build.py review
python build.py check
python build.py sync-review
python build.py publish
python build.py release-manifest
python build.py preview --config configs/config.us-en.yaml --model JE-1000F --region US --page 03_product_overview_placeholder
python build.py fast --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py html
python build.py word
python build.py pdf
python build.py all
```

Config scope rule:

- [`configs/config.us.yaml`](../configs/config.us.yaml): shared EN / US template-family config
- [`configs/config.us-en.yaml`](../configs/config.us-en.yaml): canonical US English single-language review / CI / explicit review-preview landing target
- [`configs/config.ja.yaml`](../configs/config.ja.yaml): shared JP template-family config
- [`configs/config.zh.yaml`](../configs/config.zh.yaml): shared CN zh template-family config using [`docs/manifests/manual_zh.yaml`](../docs/manifests/manual_zh.yaml)
- [`configs/config.kr.yaml`](../configs/config.kr.yaml): shared KR ko template-family config for `JE-1000F_KR` and `JE-2000E_KR`, using [`docs/manifests/manual_kr.yaml`](../docs/manifests/manual_kr.yaml)
- [`configs/config.eu.yaml`](../configs/config.eu.yaml): shared EU merged template-family config using [`docs/manifests/manual_eu.yaml`](../docs/manifests/manual_eu.yaml)
- [`configs/config.eu-en.yaml`](../configs/config.eu-en.yaml), [`configs/config.eu-fr.yaml`](../configs/config.eu-fr.yaml), [`configs/config.eu-es.yaml`](../configs/config.eu-es.yaml), [`configs/config.eu-de.yaml`](../configs/config.eu-de.yaml), [`configs/config.eu-it.yaml`](../configs/config.eu-it.yaml), and [`configs/config.eu-uk.yaml`](../configs/config.eu-uk.yaml): explicit EU single-language configs using [`../docs/manifests/manual_eu-en.yaml`](../docs/manifests/manual_eu-en.yaml) plus the corresponding [`../docs/manifests/manual_eu-single-*.yaml`](../docs/manifests) stacks
- [`configs/config.us-en.yaml`](../configs/config.us-en.yaml), [`configs/config.us-es.yaml`](../configs/config.us-es.yaml), [`configs/config.us-fr.yaml`](../configs/config.us-fr.yaml), and [`configs/config.pt-br.yaml`](../configs/config.pt-br.yaml) now inherit their shared single-language US defaults from [`../configs/config-bases/us-single-language-base.yaml`](../configs/config-bases/us-single-language-base.yaml); keep common single-language build defaults there and keep language-specific page order in [`../docs/manifests/manual_us-single-en.yaml`](../docs/manifests/manual_us-single-en.yaml), [`../docs/manifests/manual_us-single-es.yaml`](../docs/manifests/manual_us-single-es.yaml), [`../docs/manifests/manual_us-single-fr.yaml`](../docs/manifests/manual_us-single-fr.yaml), and [`../docs/manifests/manual_pt-br.yaml`](../docs/manifests/manual_pt-br.yaml)
- the current maintained baseline target is `JE-1000F` across these active config families, including `JE-1000F / US`, `JE-1000F / EU`, and `JE-1000F / JP`
- do not create a new config only because the model changed; pass `--model` and `--region` instead
- create a new config only when the page stack, template family, or output conventions are genuinely different

Useful target-scoped examples:

```powershell
python build.py doctor --config configs/config.ja.yaml --model JE-1000F --region JP
python build.py rst --config configs/config.ja.yaml
python build.py review --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py review --config configs/config.us-en.yaml --model JE-1000F --region US --refresh-review
python build.py sync-review --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py check --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py publish --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py check --config configs/config.zh.yaml --model JE-2000E --region CN
python build.py check --config configs/config.kr.yaml --model JE-2000E --region KR
python build.py rst --config configs/config.us.yaml
python build.py word --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py pdf --config configs/config.ja.yaml --model JE-2000F --region JP
```

Source mode examples:

```powershell
python build.py rst --config configs/config.ja.yaml --model JE-1000F --region JP --source runtime
python build.py word --config configs/config.ja.yaml --model JE-1000F --region JP --source review
```

Source mode meaning:

- `auto`: use `_review` if it exists, otherwise use template/data runtime draft
- `runtime`: ignore `_review` and build from template/data
- `review`: require `_review` and build from it

PR preview note:

- when a PR changes `docs/_review/<model>/<region>/`, GitHub review-preview derives that exact target from the diff and uses the same target-aware config matching as Start Review/Draft/Publish; for example, `JBP-2000B / US` uses `configs/config.bp-us.yaml`, while ordinary US host targets keep the MAIN config
- when a PR changes the zh manual family under `docs/templates/page_zh/`, `docs/templates/recipes/zh/`, or `docs/manifests/manual_zh.yaml`, the preview tool still selects the config-derived CN runtime target automatically, while packaging every existing review model
- `python tools/process_docs/build_review_preview.py` can omit `--config` when `--model` and `--region` identify a declared target; it can omit all three in CI-style runs and infer the target from the changed review bundle or existing review tree. Keep `--config configs/config.us-en.yaml` when you explicitly want the US English single-language target
- the Vercel review-preview fallback derives those family configs and its first fallback target by scanning `configs/config*.yaml`; it is used only when `PREVIEW_MODEL` / `PREVIEW_REGION` and the review tree do not provide a target

`publish` behavior:

- requires explicit `--model` and `--region`
- requires an existing `_review/<model>/<region>/`
- exports revision reports to [`reports/version_tracking/<model>/<region>/`](../reports/version_tracking) by default
- writes a release manifest to [`reports/releases/<model>/<region>/<lang>/manifests/<timestamp>.json|csv`](../reports/releases)
- queue-driven `Workflow_action=Publish` stages the formal DOCX, PDF, Markdown, IDML outputs, and designer handoff ZIP under [`../reports/releases/<model>/<region>/<lang>/versions/<version>/`](../reports/releases), then writes the uploaded handoff ZIP URL to `idml_file`; it does not build a Draft cloud doc or HTML
- queue-driven `Workflow_action=Web Publish` forces live asset sync, renders web-profile MyST/HTML, advances the `Hello-Docs/publish:docs/publish/` candidate, opens or updates its `docs/publish/**`-only PR into `main`, and writes the short root-level RTD alias (for example `https://ht-doc.readthedocs.io/manual_je1000f_us.html`) to `HTML_link`; it does not upload or overwrite IDML/PDF/DOCX outputs

`preview` behavior:

- requires explicit `--model`, `--region`, and `--page`
- `--page` must match one exact page selector
- writes to [`docs/_build/<model>/<region>/preview/<page>/rst/`](../docs/_build)
- does not rewrite root [`docs/index.rst`](../docs/index.rst)

RTD catalog behavior:

- RTD builds the frozen `docs/publish/web/` catalog from `Hello-Docs/main`. The generated `publish` branch is only a release candidate; `review/*` is only a build input, and neither branch is merged wholesale. The review/fixture command in [`.readthedocs.yaml`](../.readthedocs.yaml) is only the bootstrap fallback before the first snapshot.
- PDF-like fixed figure panels use a separate, approval-gated Web composite chain. In `04_资产定义`, `web_replace_key` names the component. In `04_资产导出物`, upload exactly one image to `export_file`, select `web_locale` (`en`, `fr`, `es`, or `shared`), fill both the file and source-fragment SHA-256 values, then set both the definition and export to `gate_status=approved`, `build_eligible=true`, and `visual_review_required=false`. `artifact_kind` must be `web-composite`.
- `sync-data` downloads only those approved rows into `_attachments/web_composites/` and writes `web_composite_manifest.json`. The next Web materialization selects by `web_replace_key + model + region + locale`, verifies the bytes and the current semantic source fragment, and replaces the governed figure plus its associated copy while leaving the section title live. With no approved match it keeps the searchable HTML fallback. Ambiguous rows, missing attachments, or either hash mismatch stop the build.
- A local live freeze must use the business-plane HT-Docs bot, not another bot belonging to the same user. `sync-data` uses the active lark-cli profile; on the maintained Mac, first verify `lark-cli --profile prod whoami --as bot`, temporarily select profile `prod`, keep `FEISHU_PHASE2_IDENTITY=bot`, and restore the previous profile after the sync. The identity flag chooses bot versus user, while the profile chooses the Feishu application/tenant.
- RTD itself has no Feishu credentials. Web Publish uses the HT-Docs bot to freeze verified attachments and their manifest into Git first; RTD consumes that immutable snapshot. `tests/fixtures/phase2` remains a CI/bootstrap fixture.
- To show **ordinary hand-written Markdown** in the same web-manual style — a single note or a whole folder rendered as one site with a sidebar — run [`tools/plain_markdown_site.py`](../tools/plain_markdown_site.py): `python tools/plain_markdown_site.py --source <file-or-folder> --output-dir <site-out> --title "My Docs"`. For a backlog of existing documents, swap `--source` for `--manifest inventory.csv` (columns `source,title,section,order`; `section` becomes a sidebar group). No Feishu table is involved — this lane has no publish state to govern, so a CSV inventory (or just the folder tree) is the right level. Broken image paths inherited from wherever a document used to live are repointed automatically by filename. Legacy tables are upgraded on the way in: a headerless label/value pipe table becomes the manual's real spec-table markup (grey `<th>` label column, merged labels, `^(①)` superscripts, bordered wrapper) instead of rendering with the phantom empty header row a converter leaves behind — a plain pipe table cannot express any of that, which is why an untouched one looks nothing like the published table. Callout boxes that a cloud editor flattened into a header-only table are restored as callouts, tables whose first data row was captured as the header are un-headered, in-table `### SECTION` rows split a spec table into one block per section, and `^①^`/`V~oc~` become real superscripts — measured on a real HTE153 export: 17 malformed tables down to 1, 16 callouts and 4 spec blocks recovered. The conversion writes an **intermediate Markdown** form rather than HTML: `--to-intermediate DIR` gives you a reviewable file of `{callout}` / `{spec-table}` / `{lcd-mode}` / `{comparison}` / `{manual-table}` directives (tables it cannot classify stay pipe tables with a comment naming the candidates), and rendering that directory is a plain `--source` run that compiles the directives deterministically. Add `--download-images` to localize artwork hosted on a cloud editor. Use `--keep-tables` to opt out of the conversion, and `components/COOKBOOK.md` in the exported bundle when a document needs a component the shape alone cannot imply. The output directory is self-contained, so you can zip it or hand it over as-is. This is a preview/sharing lane only: it refuses to write into `docs/_build`, `reports/releases` or `docs/publish`, and it cannot put anything on the RTD site, which only renders the Web Publish snapshot. Plain Markdown gets the prose styling (typography, paper card, headings, table panels, images); the `hb-*` figure/spec/LCD components need pipeline-generated markup and will not appear. Do not try to "downgrade" a generated manual `.md` into plain Markdown with `pandoc -t gfm-raw_html`: measured on `JE-1000F / US`, that silently drops roughly a third of the visible text plus 26 images and 38 tables, because constructs that plain Markdown cannot express are discarded rather than degraded.
- 中间态里可写的 8 个指令、单元格能用的行内标记子集、类型化 option 和 strict 排错，见 [`md_site_guide.md`](md_site_guide.md)。存量转换的两条命令也在那份里。
- Web Publish enables `AUTO_MANUAL_PRESENTATION_PROFILE=web`. Normal `build.py md`, print Publish, IDML and DOCX exports keep the default `document` profile.
- the web profile skips `cover*`, `00_toc*`, and `99_back_cover*` and opens the manual directly at the `IMPORTANT` content in `00_preface`. If the source still carries the merged-language inventory line, Web hides it; a valid reseeded review page may already start with the governed bold `IMPORTANT` marker and is accepted as-is, while any unrelated leading block still stops the build. The catalog links to that manual entry rather than making readers pass through a nested target index
- For targets listed in [`web_manual.json`](../docs/renderers/contracts/web_manual.json) (currently `JE-1000F / US`), Product Overview becomes one `HB-SPECIAL-OVERVIEW` semantic instance with two views, two asset roles and 15 ordered live callouts; [`overview_component_instances.json`](../docs/renderers/contracts/overview_component_instances.json) supplies only that target's Web/IDML geometry and locale/source bindings. Both views use centered locale-matched approved PDF artwork in English, French, and Spanish, with the complete searchable HTML/SVG labels retained as the fallback when no approved manifest entry matches. The image crop excludes the FRONT/RIGHT view heading so theme changes still control it. WHAT'S IN THE BOX is one `HB-SPECIAL-INBOX` semantic instance: three ordered cards each carry their number, image asset role, accessible alt and editable localized label, followed by the same instance's editable TIP label/body. The Web adapter renders equal rounded cards with even outer alignment and a responsive full-width TIP strip; the LaTeX, IDML and Word adapters keep their own layout geometry without rasterizing the labels. App Setup renders the store badges and QR as two distinct shared images, centers each in its own column, and keeps both descriptions as live responsive HTML. Step 2.1 uses the themeable plus while preserving its localized screen-reader label. The add-device panel combines one shared PDF-derived two-phone artwork, with 2.1/2.2 already positioned inside the image, and shared text-free device-control art with the three localized RST button labels as visible HTML. The approved control art keeps the complete grey panel and leader lines; CSS places only the localized labels in its reserved zones and never draws replacement line fragments. Operation figures and the car-charging connection panel retain centered locale-matched 2x crops; the App connect-result panel uses one shared PDF-derived three-phone image with 2.3/2.4/2.5 already embedded. Responsive CSS therefore does not independently place any App screenshot caption. Reference artwork never contains the section heading, and surrounding instructions remain live HTML. In the web profile, every ordinary standalone RST image fills the same responsive content width, remains centered, and preserves its aspect ratio instead of retaining inconsistent print-width hints such as 360 px. Unlisted targets retain ordinary source HTML until their own presentation is validated and added to the contract.
- FCC is rendered from the localized RST as a searchable two-column card with the FCC mark, normalizes locale-specific trailing copy, uses one component-owned spacing token for paragraphs and measure items, and becomes one column on phones. Its H1 stays available to the page outline and RTD navigation but is visually hidden, so readers see only the FCC content card. H1 bars, generic tables, governed table frames, and FCC use one shared border-box component-band width, keeping their left/right edges aligned. Each localized MEANING OF SYMBOLS warning-definition table is rebuilt as semantic searchable HTML with the PDF's full dark grid and dark warning badges; the four labels and descriptions stay localized live text and source inline widths do not reach final HTML. The following safety-symbol matrix is rendered from the same localized RST as two independent rounded Symbol/Meaning tables, matching the PDF's left-six/right-five structure so a long right-side description does not stretch the paired left row. On desktop both panels share the same outer height and aligned top/bottom borders; phones stack the two tables. The LCD icon page remains a searchable four-column HTML table: `On` / `Blink` / `Off` line-blocks stay on separate lines; the rounded frame and every row/column rule mirror the PDF hierarchy; number/icon/name cells are lightly filled; compact number badges are centered in the first column; and phones use horizontal scrolling instead of crushing the copy.
- The LCD screen-mode panel remains searchable HTML while matching the template's rounded illustration-plus-table composition across EN/FR/ES. The AC/DC Auto Resume matrix also remains searchable HTML with equal-width columns, a light left column, white right column, dark full-grid rules, and a true two-row Battery SOC cell. On phones each compact table scrolls inside its own frame instead of widening the page.
- The EN/FR/ES Troubleshooting table remains searchable HTML with the PDF's rounded dark frame, full grid, 14% light error-code column, and 86% white corrective-measures column. F6/F7 actions keep their source line breaks through Pandoc. The four Specifications tables use a matching protected 31%/69% label/value grid and preserve row-spanning labels; the web transform removes the authored bullet glyph so the shared heading theme shows one section dot rather than two, and raises both governed `①` references as semantic superscripts. Both table types scroll inside their own frame on phones.
- Warranty also remains searchable HTML across EN/FR/ES. Both the current shared-template form (`warranty-lead` / `warranty-section` semantic containers) and an older flat review page are accepted; only those governed containers are unwrapped before HTML conversion so their nested headings are retained. The two opening paragraphs form the PDF-like rounded notice and local-law note; all six localized H2 headings stay theme-controlled and appear as floating dark labels on rounded cards. Five sections are ordinary copy cards, while Warranty Period is rebuilt from the source table as localized 3-year/2-year columns at approximately 61%/39% on desktop and one column on phones. The source 50/50 table geometry is removed, but email links, the four Exclusions items, and every localized paragraph remain live content.
- RTD also applies the shared IDML-derived responsive theme: brand-dark title bars, compact heading levels, rounded tables and warning/note groups, consistent spacing, and proportional images. A browser with licensed Gilroy installed uses it; other browsers use the declared system fallbacks. The site intentionally reflows on phones and does not claim the fixed page count or exact pagination of IDML/INDD.
- The web export protects each semantic callout before Pandoc and restores it afterward. WARNING, DANGER, CAUTION, and NOTE therefore keep one shared class structure, one light rounded visual treatment, and the theme's approximately 16% label / 84% body desktop split; fixed table layout keeps the first-column boundary aligned even when localized labels have different lengths. Pandoc does not add a 50/50 `colgroup` or an empty header row. On phones the same component stacks vertically.
- Scientific subscripts and specification superscripts are protected across the same Pandoc step, so source notation such as ``V\ :sub:`oc``` renders as semantic `V<sub>oc</sub>` and governed `①` references render as `<sup>①</sup>` in every language rather than showing literal inline Markdown notation.
- Web Publish first materializes target-scoped `md` directories, then assembles `docs/publish/web/` as the homepage catalog without rewriting the repo-root [`docs/index.rst`](../docs/index.rst). The assembler also writes one collision-checked root alias named from each manual stem; it forwards to the nested model/region page with a relative target and is the URL persisted in `HTML_link`. A pre-push three-dot diff guard permits only `docs/publish/**` in the production PR.
- RTD is the responsive Web presentation surface; it is not the release authority for IDML, LaTeX, PDF, DOCX or formal print Markdown

`fast` behavior:

- equivalent to a runtime-only `rst --prepare-only --no-clean`
- useful for template or placeholder debugging without export steps

`sync-review` behavior:

- first refreshes the runtime bundle from template/data
- then updates only data-driven review files by default
- does not replace ordinary review prose pages unless you explicitly name them with `--page-file`
- skips exact target-local paths declared by the review bundle's `manifest.json` `sync_preserve_paths`, including paths explicitly named with `--page-file`; only relative `.rst` files under `page/` or `generated/` are accepted
- data-driven means:
  - all generated CSV pages
  - all materialized `spec_*` / `safety_*` pages
  - all template pages whose source contains placeholders such as `|PRODUCT_NAME|` or `|MAIN_POWER_BUTTON_LABEL|`
  - cover pages generated from title/product identity
- generated cover pages still feed PDF/LaTeX output, but HTML now opens directly on the first manual content section instead of a blank cover-style landing screen
- manual HTML preview also suppresses most default Furo sidebar / TOC chrome, stays in a continuous reading flow instead of browser-side fake pagination, regenerates a lightweight left outline from the manual headings, and renders generic headings, copy width, figure presentation, ordinary table spacing, and the multilingual preface notice in a restrained neutral manual-reader style while keeping dedicated component layouts such as `SPECIFICATIONS`, so the result feels like a manual reader instead of a documentation site
- review-preview workspace manual pages now reuse the same manual HTML/CSS/JS treatment as the local build, including the generated heading sidebar and the same no-top-switcher layout

Shared-source propagation audit (read-only):

```powershell
python tools/check_review_branch_sync.py --base origin/main --remote origin --json
```

- the ledger reads every live `review/*` branch manifest, so legacy
  `review/id-*` names do not need to encode model or region
- each row binds one affected branch to one changed shared-source file and is
  either `merge_params_safe` or `needs_human`
- `merge_params_safe` is a narrow proof: the change is confined to stable
  placeholder-bearing lines and the reviewer has not edited text outside those
  placeholders on the same line
- unresolved branch refs/manifests, non-parameter files, structural changes,
  ambiguous derivative mapping, and same-line reviewer edits abstain as
  `needs_human`; the command never modifies or syncs a branch

Equivalent lower-level examples:

```powershell
.\.venv\Scripts\python.exe tools\build_docs.py --config configs/config.us-en.yaml --model JE-1000F --region US --prepare-only
.\.venv\Scripts\python.exe tools\build_docs.py --config configs/config.us-en.yaml --model JE-1000F --region US --formats word --no-open
```

Word styling note:

- the US English Word path now reapplies the `reference_en.docx` heading, table, and default paragraph styling after DOCX generation, while leaving the generated `safety` and `spec` pages as-is
- Word output now also normalizes image relationships to embedded media before the final DOCX post-processing step, which improves Feishu and other third-party preview compatibility for image-backed tables
- the exporter preserves `manual_bundle.html` unchanged for traceability, but
  removes only `<main ...>` wrapper tags in a temporary Pandoc input. This keeps
  all page children and component order while preventing an earlier empty
  `<main></main>` from making the generated DOCX body empty; the temporary file
  is deleted after conversion

---

## 9. Version Tracking and Diff Export

Because [`docs/_review/**`](../docs/_review) is now the preferred review surface, you can keep cleaner RST history per target.

Recommended everyday workflow:

1. Pick the target you want to track.
2. Seed the review bundle once for that target.
3. Commit the review bundle as a Git baseline.
4. Edit the review bundle for normal review rounds.
5. If parameters changed in CSV, run `sync-review`.
6. Rebuild preview outputs from that review bundle and commit again.
7. Run `publish` for the formal release output, or run `diff-report` separately when needed.

### 9.1 First-Time Baseline

Use this when a target has never been tracked in Git before.

Example baseline:

```powershell
python build.py review --config configs/config.us-en.yaml --model JE-1000F --region US
git add docs/_review/JE-1000F/US
git commit -m "Add JE-1000F US review baseline"
```

What this means:

- `review` prepares [`docs/_build/<model>/<region>/rst/**`](../docs/_build) from template/data
- then it seeds [`docs/_review/<model>/<region>/**`](../docs/_review)
- the commit becomes the starting point for future report comparisons

### 9.2 Daily Update Flow

After the baseline exists, the normal update loop is:

```powershell
python build.py check --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py word --config configs/config.us-en.yaml --model JE-1000F --region US
git add docs/_review/JE-1000F/US
git commit -m "Update JE-1000F US manual"
```

Recommended rule:

- `_review` is now the normal authoring source after review starts
- if a round also changed shared template/data, commit those with `_review`
- use `review --refresh-review` only when intentionally reseeding from the shared seed layer
- use `sync-review` after parameter changes in [`Spec_Master.csv`](../data/phase2/Spec_Master.csv) so review keeps up with regenerated values

### 9.3 Which `tracked-root` to Use

Use the tracked root that matches the scope you want to compare:

- one model across all tracked regions:
  [`docs/_review/JE-1000F`](../docs/_review/JE-1000F)
- one model and one region:
  [`docs/_review/JE-1000F/US`](../docs/_review/JE-1000F/US)
- temporary runtime-only comparison:
  [`docs/_build/JE-1000F`](../docs/_build/JE-1000F)

Recommended default:

- prefer `_review`
- use `_build` only for temporary debugging when you have not emitted a review bundle yet

Example report export for one model:

```powershell
python build.py diff-report --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py diff-report --config configs/config.us-en.yaml --tracked-root docs/_review/JE-1000F --from-ref HEAD~1 --to-ref HEAD
python build.py diff-report --config configs/config.us-en.yaml --tracked-root docs/_review/JE-1000F --from-ref HEAD~1 --to-ref HEAD --include-initial-adds
```

Example report export for one region:

```powershell
python build.py diff-report --config configs/config.us-en.yaml --tracked-root docs/_review/JE-1000F/US --from-ref HEAD~3 --to-ref HEAD
```

### 9.4 How to Compare Two Specific Commits

If you want to compare a baseline commit with the latest manual state:

```powershell
python build.py diff-report --config configs/config.us-en.yaml --tracked-root docs/_review/JE-1000F/US --from-ref <old_commit> --to-ref <new_commit>
```

Examples:

- compare the previous commit to the current one:
  `--from-ref HEAD~1 --to-ref HEAD`
- compare the baseline commit to current head:
  `--from-ref a1b2c3d --to-ref HEAD`
- compare two tags or branches:
  `--from-ref release/v1 --to-ref release/v2`

Default outputs:

- [`reports/version_tracking/JE-1000F/US/*_files.csv`](../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_files.html`](../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_pages.csv`](../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_pages.html`](../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_fields.csv`](../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_fields.html`](../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_index.html`](../reports/version_tracking/JE-1000F/US)
- legacy report path aliases remain available as [`reports/version_tracking/JE-1000F/US/*.csv`](../reports/version_tracking/JE-1000F/US) and `*.html`

Use `--report-dir` if you want a different output folder.

Useful option:

- `--include-initial-adds`
  The default report already hides one-time initial baseline Added rows. Use this only when you want to see the full first-import churn.

Automatic behavior:

- if the tracked subtree does not exist at `from-ref` but exists at `to-ref`, the report now shows an explicit note that this is an initial baseline and all Added rows are expected
- by default, the generated reports keep the note but suppress those initial Added rows
- if you pass `--include-initial-adds`, those initial Added rows are kept in the generated reports

### 9.5 Which Report to Open First

Open order:

1. `*_index.html`
2. `*_fields.html`
3. `*_pages.html`
4. `*_files.html`

Why:

- `index` gives the report homepage and target jump links
- `fields` is usually the most useful review view because it shows rendered value changes and source back-mapping
- `pages` is the next best rollup when you want page-level impact
- `files` is best when you need raw file churn, insertions, and deletions

What each report means:

- `files`: which tracked `.rst` files changed, plus insertions and deletions
- `pages`: page-level rollup with `fields_changed` counts
- `fields`: structured field/value changes extracted from list-tables and `Label: Value` lines
  For generated `spec_*.rst` pages, the report now also tries to fill `source_row_key`, `source_section_key`, `source_line_order`, and `source_csv_line` from [`Spec_Master.csv`](../data/phase2/Spec_Master.csv).
  For template-based pages such as `03_product_overview`, `05_operation_guide`, and `12_app_setup`, the report also tries to back-map changed field text to matching page-value rows by comparing rendered values against resolved placeholders.
  `fields.html` now includes built-in filters for `model`, `region`, `page_key`, `source_row_key`, `change_type`, plus a full-text search box.
- `index`: homepage that links `files/pages/fields` together and provides target-level jump links with filters pre-applied

### 9.6 How to Read `fields` Back-Mapping

Important columns in `*_fields.csv` and `*_fields.html`:

- `field_key`: the rendered field label found in the RST content
- `old_value` / `new_value`: the rendered before/after values
- `source_row_key`: the matched source row in [`Spec_Master.csv`](../data/phase2/Spec_Master.csv)
- `source_section_key`: the matched source section in [`Spec_Master.csv`](../data/phase2/Spec_Master.csv)
- `source_line_order`: the matched source line order for multiline rows
- `source_csv_line`: the original CSV line number
- when a field label itself changes, the diff now first tries to pair old/new rows through stable source back-mapping before falling back to rendered label text, so placeholder/spec renames are more likely to show up as one `M` row with both `old_value` and `new_value`

Interpretation rule:

- if `source_row_key` is filled, the report found a source row match
- if it is blank, the row is still useful as a rendered text diff, but the source mapping was not reliable enough to fill automatically

### 9.7 Typical Review Example

For a normal JE-1000F US review cycle:

```powershell
python build.py check --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py check --config configs/config.eu-en.yaml --model JE-1000F --region EU
git add docs/_review/JE-1000F/US
git commit -m "Refresh JE-1000F US manual"
python build.py publish --config configs/config.us-en.yaml --model JE-1000F --region US
```

Then:

1. open [`reports/version_tracking/JE-1000F/US/*_index.html`](../reports/version_tracking/JE-1000F/US)
2. click the `JE-1000F/US` target link
3. open `fields`
4. filter `source_row_key` when you want to inspect one spec or placeholder family

### 9.8 Common Mistakes

- Comparing `_build` after a fresh clean without rebuilding the same target first
- Running `review --refresh-review` without realizing it will replace the current review bundle
- Changing parameter CSV data during review and forgetting to run `sync-review`
- Forgetting that `check/html/word/pdf` now use review content by default once review exists
- Committing only `_review` when the round also changed shared template or CSV logic
- Reading `files.html` first and missing the more useful field-level diff in `fields.html`

---

## 10. Page Contracts

The repo now supports page contract checks under:

- [`docs/templates/contracts/03_product_overview.yaml`](../docs/templates/contracts/03_product_overview.yaml)
- [`docs/templates/contracts/05_operation_guide.yaml`](../docs/templates/contracts/05_operation_guide.yaml)
- [`docs/templates/contracts/12_app_setup.yaml`](../docs/templates/contracts/12_app_setup.yaml)

Current scope:

- contracts are matched by source template path from `config.pages`
- `check` validates required placeholders, spec row keys, page-value selectors, and required assets
- `required_assets` accepts both existing path values and `asset:<asset_key>`; `check` and materialization share the same model/region/language-bound resolver, so semantic scope/status decisions cannot drift between the two stages
- current coverage includes `03_product_overview`, `05_operation_guide`, and `12_app_setup`
- the active US and JP template families can each declare their own required placeholder sets
- contracts can be scoped by `allowed_languages`, `allowed_regions`, and `allowed_models`

Current contract keys:

- `required_placeholders`
- `required_spec_keys`
- `required_page_values`
- `required_assets`
- `allowed_languages`
- `allowed_regions`
- `allowed_models`

Why this matters:

- a page can fail early when required page-value bindings are missing
- fallback values in [`conf_base.py`](../docs/conf_base.py) no longer hide missing product-specific spec data
- new model onboarding becomes easier to validate before Word/PDF export

---

## 11. Common Pitfalls

### 11.1 Editing the wrong layer

Before review starts:

- edit template/data

After review starts:

- edit [`docs/_review/<model>/<region>/**`](../docs/_review)

Never edit:

- [`docs/_build/<model>/<region>/rst/**`](../docs/_build)

Use template/data only for shared reusable changes or intentional reseeding.

### 11.2 `?` appears in output

This is usually caused by dirty page-value rows in [`Spec_Master.csv`](../data/phase2/Spec_Master.csv), not by the template structure itself.

### 11.3 Old model names survive in the new manual

This usually means one of these happened:

- a template still contains hard-coded model text
- `product_name` in [`Spec_Master.csv`](../data/phase2/Spec_Master.csv) was not updated
- the wrong `config`, `model`, or `region` was used

`check` now reports this as `STALE_IDENTITY_LITERAL`.
If a foreign model mention is intentional, add it to `checks.allowed_foreign_identity_literals` in the config.

### 11.4 Hard-coded title in config

If `build.word_title` is fixed to an old model name, the generated Word title will stay wrong even if `PRODUCT_NAME` is correct.
Prefer a placeholder-based title such as:

```yaml
word_title: "|PRODUCT_NAME| User Manual"
```

---

## 12. Verification Checklist

After changing templates or CSV values, verify at least the following:

1. `python build.py check --config ...` succeeds
2. `python build.py doctor --config ... --model ... --region ...` reports no blocking errors for the current Word/PDF path
3. the target bundle appears under [`docs/_build/<model>/<region>/rst/`](../docs/_build)
4. the review bundle appears under [`docs/_review/<model>/<region>/`](../docs/_review)
5. generated pages contain no unresolved placeholders such as `|PRODUCT_NAME|`
6. generated pages contain no stale model names from older products
7. safety and spec still resolve from the intended source, including the JP template-backed safety page and the remaining CSV-backed generated pages
8. the expected `.docx`, `.html`, or `.pdf` file is generated when requested
9. `publish` or `release-manifest` produced a JSON / CSV record under [`reports/releases/<model>/<region>/<lang>/manifests/<timestamp>.json|csv`](../reports/releases); a versioned Publish also produced an immutable `versions/<version>/snapshot/release_snapshot_identity.json` and the manifest points to that archive
10. `python build.py release-rebuild-verify --manifest <manifest.json>` reports `status=passed` for the versioned release on its recorded toolchain

Useful checks:

```powershell
Select-String -Path docs\_build\JE-1000F\US\rst\page\*.rst -Pattern '\|[A-Z0-9_]+\|'
Select-String -Path docs\_build\JE-1000F\US\rst\page\*.rst -Pattern '\?'
git status --short -- docs/_review/JE-1000F/US
```

---

## 13. One-Sentence Rule

Templates and CSV create the first draft.
[`docs/_review/**`](../docs/_review) becomes the target editing source after review starts.
[`docs/_build/**/**/rst/**`](../docs/_build) remains the runtime publish bundle behind the final outputs.
## Start Review, Build Draft Package, Publish

- `process-build-queue` no longer runs `sync-data` unconditionally; it now refreshes phase2 only when `Document_link.是否强制刷新数据 = true`.
- `Document_link.data_sync` is the writeback field for that decision: `refreshed`, `skipped`, or `failed`.
- `sync-review` now also refreshes `generated_page` placeholder files under `page/*.rst`, so forced-refresh queue builds update the final rendered page text instead of keeping stale review placeholder content.
- `build.py check --source review` validates the rows needed to identify the target and render generated-page recipe inputs, plus footnotes referenced by those inputs, but retired `Spec_Master` rows and unreferenced `Spec_Footnotes` definitions that the review bundle does not consume no longer block Build Draft Package.
- `Workflow_action=Build Draft Package`, `Workflow_action=Publish`, and `Workflow_action=Web Publish` are the build actions.
- queue routing only looks at `Workflow_action`: use `Start Review`, `Build Draft Package`, `Publish`, or `Web Publish`, and keep `Doc_phase` blank.
- `feishu-draft-build-queue.yml` is the Build Draft Package worker on `main`; dispatch it on `main`, and let `Document_link.Git_ref` decide which review branch gets fetched and built.
- `feishu-start-review.yml` is the Start Review worker on `main`; dispatch it on `main` so review-init always uses the latest worker definition.
- `feishu-build-queue.yml` is the Publish-stage worker on `main`; dispatch it on `main`, and let `Document_link.Git_ref` decide the review-branch source when present.
- `feishu-web-publish-queue.yml` is the Web Publish worker on `Hello-Docs/main`; it writes the generated `publish` candidate, validates that its PR diff contains only `docs/publish/**`, opens or updates `publish -> main`, and writes the RTD link. It never merges the selected `review/*` branch.
- if your team uses OpenClaw as the operator entrypoint, install the repo package under [`../integrations/openclaw/auto-manual-control-layer/`](../integrations/openclaw/auto-manual-control-layer) and use `/start-review`, `/build-draft`, `/publish`, `/web-publish`, and `/manual-status` instead of hand-calling the GitHub API.
- the OpenClaw bridge does not move `build.py`, Feishu secrets, or queue writeback out of GitHub Actions. It only dispatches the existing workers on `main` and tracks them through `openclaw_dispatch_nonce` plus the `openclaw-run-metadata` artifact.
- OpenClaw dispatches `start-review`, `build-draft`, `publish`, and `web-publish` with the resolved Feishu `record_id`; both publish actions require explicit confirmation.
