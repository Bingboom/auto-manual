# Build guide: production IDML and approved reference layouts

Part of the [build guide](../build_doc_guide.md); its index lists the other topics.
Add new notes for this topic here, not to the hub.

- `build.py idml` prepares only RST when the exact model/region/language target is present in the approved reference-layout registry; its production exporter consumes that hash-bound physical plan directly. A matching approved contract on disk without its registry entry is a hard error, not permission to use fuzzy page matching. The historical LaTeX-PDF fallback remains available only when the target has no approved contract.
- A candidate `target_assembly` plan is frozen against a specific book, so the target's page manifest has to declare every page the plan names — otherwise `build.py idml` prepares a bundle the plan rejects and the target is only buildable with an explicit `--source review`, through a derivative. [`tests/test_assembly_plan_manifest_coverage.py`](../../tests/test_assembly_plan_manifest_coverage.py) pins which targets are in that state; `JE-3000C_KR` is the one known case (its cover and back cover exist only under `docs/_review`, and `manual_kr.yaml` is shared with `JE-1000F_KR`/`JE-2000E_KR`, so declaring a per-model cover needs a cover asset for all three or a per-model manifest). A count mismatch names the offending pages in both directions; it is not a code regression.

### Approved-PDF native InDesign replica (option 2)

The production IDML path projects the prepared bundle through `manual.ir.json`
and shared layout tokens; `latex_page_plan.json` remains a same-source trace.
For ordinary targets without an approved reference-layout contract, the
measured LaTeX plan remains the fallback behavior. For the approved
`JE-1000F / US / en+fr+es` replica, the LaTeX PDF and its page plan are not the
visual approval master. The build must resolve the target through the
[`reference layout registry`](../../docs/renderers/contracts/reference_layout_registry.json)
to the reviewed, hash-bound
[`JE-1000F US V2.0 contract`](../../docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json).
The design and implementation rationale is recorded in
[`dev/idml_reference_replica_plan.md`](../dev/idml_reference_replica_plan.md), and
the module boundary remains documented in
[`dev/idml_module_map.md`](../dev/idml_module_map.md). When a new model, language,
page, or density should reuse an existing visual component, follow
[`dev/style_component_usage_guide.md`](../dev/style_component_usage_guide.md) before
adding page-level geometry or finalizer behavior.

The same registry entry declares `JE-1000F / US / en` as a pilot **component
target** (`component_targets`): its single-language build composes the approved
contract's registered pages (LCD profile, native Overview, Charging,
Storage+Troubleshooting, Warranty, main-power base art) without the contract's
physical page plan, and `build.py idml` skips the measured LaTeX plan for it.
This happens only while every source page of the build matches its pin in the
approved contract (today: business review content, `--source review`, as the
publish queue uses). Any drift keeps the ordinary layout and prints
`COMPONENT TARGET INERT` with each pinned/built digest; refresh the pins through
the rebind route below, never by hand. Other languages, the trilingual replica
and every other target are unchanged. Details:
[`dev/idml_component_targets.md`](../dev/idml_component_targets.md).

`JBP-2000B / EU / en+fr+es+de+it+uk` is the second target resolved from the
same `BP@INTL` skeleton. Build it with `configs/config.bp-eu.yaml`; `uk` is
Ukrainian and this target makes no UK-market claim. Its paired host is named
`Jackery Explorer 2000 Plus` in EU target data (the US target uses
`Jackery HomePower 2000 Plus`). The committed physical plan remains a
candidate, so a successful 54-page native PDF/X-4 pass proves candidate
assembly health but does not register an approved reference layout. Current
native evidence is recorded in
[`reviews/jbp2000b_eu_r2_native_validation_2026-08.md`](../reviews/jbp2000b_eu_r2_native_validation_2026-08.md).

`JBP-2000B / JP / ja` is the first target resolved from the separate `BP@JP`
skeleton. Build it with `configs/config.bp-jp.yaml`; this config is exact-target
only and declares `family_default: false`, so ordinary MAIN JP continues to
resolve through `configs/config.ja.yaml`. Its paired host display name is
`Jackery ポータブル電源 2000 Plus`. The 12-page target plan adds only assembly
data: split signal/icon compositions, Inbox+Overview, LCD+Operation, a two-page
Connections stacking guide, Troubleshooting+Specifications, and the shared
warranty composition. New target behavior must stay in the manifest, Product
Manual Plan, target assembly JSON, region profile, localized carrier data, and
assets; do not add `JBP-2000B` or `JP` branches to page renderers. The plan
remains `candidate` until native InDesign/PDF/X and 12-page visual acceptance
are recorded and it is promoted separately.

`JS-100I / EU / en` is the first portable-solar target resolved from the
reusable `Solar@INTL` skeleton. Use `configs/config.solar-eu-en.yaml` with the
Web presentation profile. Its manifest starts at Safety Tips and deliberately
contains no cover, TOC, LCD, UPS, troubleshooting, or App slots. The five-item
Inbox uses the variable-card component; specifications come from the phase2
`Spec_Master`/notes contract; English-labelled figures are target-bound by a
`web-illustrations/v1` manifest and source/output hashes. Local bootstrap data
is in `tests/fixtures/js100i_eu_en_phase2`. For the authorized three-target
Git-only batch, reviewed Git sources and their `source_manifest.json` records
are the release authority; no live Base copy or write is required. Formal Web
release still goes through the generated Hello-Docs `docs/publish/**`-only PR
and RTD verification. Do not publish an unidentified fixture or write the
mirror engineering tree directly. See
[`dev/js100i_eu_en_web_acceptance.md`](../dev/js100i_eu_en_web_acceptance.md).

JS-100I EU adds a Git-only eight-language candidate through
`configs/config.solar-eu-multilingual.yaml`, the same Solar@INTL skeleton and
RST/CSV → `build.py md` → manual-ir/v2 → shared Web/Sphinx chain. Pair
`--lang <language>` with
`--data-root data/manual_sources/JS-100I/EU/added-locales/2026-09-28/phase2/<language>`;
`Source_lang` is source metadata, not a Spec_Master row filter. The eight
snapshots preserve the native source's 21 rows and localized notes independently.
The language registry recognizes `pt`, `nl`, and `pl` with `sync_enabled=False`,
so offline output does not add live synchronization columns or conflate `pt`
with `pt-BR`. A single-language Web projection consumes only that language's
illustration binding from the family map and fails if it is missing.

English retains its existing structured facts and approved Inbox/product-view
assets. Operation figures use 16 shared native derivatives with selectable
captions; narrow two-column specifications wrap within their container. The
old approved recipe is immutable. The new strict recipe and separate native
SVG/Chromium export receipt record backdrop removal and exact PNG hashes.
Source errata, reproduction commands and local nine-language browser evidence
are in the [review record](../reviews/js100i_eu_nine_language_2026-09.md).
MA-217 authorizes this candidate's Git-only publication after all checks pass;
Base writes and asset promotion remain excluded. Fresh publication requires
the eight locale enrollments in `prepared_component_admission.json`. Dutch
`OPMERKING` and Polish `Uwaga` retain their native labels in shared note strips.
Source-authored warranty/legal chapters remain exact, hash-pinned migration
debt, rather than claiming shared warranty-component coverage. The 24 new
drawings have pixel-identical lossless WebP delivery companions; their PNG
masters remain unchanged. See the snapshot reproduction instructions for the
encoding receipt and compact-JSON step before release sealing.

`JAAC-WHE-100-EUA1 / EU / en` reuses `configs/config.charger-eu-en.yaml`
through the `charger-intl` skeleton's `accessory-v1` Product Manual Plan. The
plan contains only Inbox, native specifications/notes, and two complete
source-owned how-to panels. Product Overview and Warranty are optional at the
skeleton level so this accessory does not invent them; the existing charger
plans explicitly keep both pages. The PDF-compatible AI and 38-row scope
snapshot are frozen in Git, including the `收纳小推车` same-manual association.
See [`reviews/jaac_whe100_eu_en_web_intake_2026-09.md`](../reviews/jaac_whe100_eu_en_web_intake_2026-09.md).

`JS-40C / EU / en` reuses the same `Solar@INTL` skeleton through its own
Product Manual Plan. It starts at Safety Tips, has a seven-item semantic Inbox,
omits the JS-100I unfolding/folding slots, and adds Solar Panel Storage before
Specifications. Its frozen Git source snapshot is
`data/manual_sources/JS-40C/EU/en/2026-08-30/`; 18 approved figure crops remain
hash-bound to the exact Illustrator master and target. Build it with the shared
`configs/config.solar-eu-en.yaml` entrypoint plus `--model JS-40C --region EU
--lang en`. See
[`dev/js40c_eu_en_web_acceptance.md`](../dev/js40c_eu_en_web_acceptance.md).

IDML-localized symbol copy and table-of-contents language headers are language
packs derived from [`tools/lang_registry.py`](../../tools/lang_registry.py),
not tables maintained by the individual IDML modules. For reference-bound
spacing and placement overrides the registry separates three sets:
`governed_languages()` gates approved-reference flow behavior (fixed approved
heights, reference offsets, planned composition — en/fr/es);
`layout_override_languages()` is the set whose `lang_<code>_` override rows the
shared token cascade reads (the governed languages plus lines in active layout
tuning, currently adding ko), with tuning languages keeping measured/fallback
flow behavior until their reference layout is approved; and each component's
`contract_languages` declares which override rows are contract-required under
approved-reference builds. Adding a language pack alone does not claim that
language has an approved physical layout.
The fixed-layout LaTeX `HBApplyLang` dispatcher also covers the warning label
for every registered language; its label values are parity-checked against the
registry's symbol language pack.

Contract selection is fail-closed before identity validation: if an approved
contract on disk exactly matches the Manual IR target but its registry row is
absent, production IDML stops and names the orphaned contract. Removing a row
must never turn an approved target into an ordinary measured-LaTeX target.
Fallback is valid only when neither the registry nor the contract directory
contains an approved contract for the exact model, region, and language list.

For a single-language config, `build.py idml` derives the exporter `--lang`
from `build.languages` when the CLI flag is omitted. This is required for
families such as JP and KR: passing only model/region must not let the low-level
exporter's historical English default select localized data. Multilingual
configs keep that historical default unless `--lang` is supplied explicitly.

The approved v2 contract separates enforced identity from provenance:

The committed engineering-plane review copy is synchronized to
`Bingboom/Hello-Docs:review/JE-1000F-US@731f1954c0e19020bd22b68876b0c536d564f647`,
which includes the 2026-09-23 refresh to the publish queue's review-sync output
([Hello-Docs #116](https://github.com/Bingboom/Hello-Docs/pull/116)).
The 2026-08-29 content reapproval covers the current editable IDML semantic
projection; its rebind changed zero page bindings and left the 58-page
composition map unchanged. The first 2026-09-23 content reapproval moved the
three operation pages (EN/FR/ES) to the JE-1000F/US LED override art
(`operation/je1000f_us/led_light`); that rebind changed exactly those three page
bindings and also left the composition map unchanged. The second refreshed the
review copy to the state the publish queue's review sync writes (the six
symbols and troubleshooting pages, EN/FR/ES: signal-row variants and the F9
"DC/USB" copy from live data); it changed exactly those six page bindings and
left the composition map unchanged.
A later 2026-09-23 style re-pin followed the common `idml_symbols_signal_alert_icon`
row in `data/layout_params.csv`. It changed only the layout-params identity; there
were no page bindings and no content change.

| Contract item | Approved value |
| --- | --- |
| Target | `JE-1000F / US / en+fr+es` |
| Reference PDF | `Jackery Explorer 1000 User Manual V2.0-2026-06-05.pdf` |
| Reference SHA-256 | `e72b1ba01882062e261b17d5ba54a2f7c3099e5ba531a6428be13888641083f2` |
| Page contract | 58 pages, `368.787 × 524.692 pt`, tolerance `0.02 pt` |
| Print contract | PDF/X-4, Output Intent `Japan Color 2001 Coated`, Output Condition `JC200103` |
| Content identity (enforced) | `46319119142e5824202d3f12297557ed46b67fb89bcbde363b852802980bc678` |
| Assembly identity (enforced) | `c5d6d94c5bc6eaf18e767af3113aa9c766fb01c519062751003d310e9684eb57` |
| Style-contract identity (enforced) | `cdf3b81f7b002bca4596565418c52c0a852666454b7fb77206ae71d1ab9ae420` |
| Layout-params identity (enforced) | `9781ef9eec94bd356fd862b231e57d04d2e56f0cd03016d78d85412e7312515b` |
| Snapshot provenance (not an activation gate) | `4c7b267672c8be081977c5644b444a6eb0059cacbd81de0a995ac6f58a859a2e` |

The 52 plan rows bind every IR source reference, by composition, to this
physical structure:

| Section | Physical pages | Count |
| --- | ---: | ---: |
| Front matter | 1–3 | 3 |
| English | 4–21 | 18 |
| French | 22–39 | 18 |
| Spanish | 40–57 | 18 |
| Back cover | 58 | 1 |

The build is fail-closed for this approval path. Target/language mismatch,
missing plan, enforced content/assembly/style drift, per-page source drift,
incomplete 52-source coverage, unclassified prose without an exact approved
exception, non-monotonic/out-of-bounds composition pages, or a final
page-count/geometry mismatch stops the build. Snapshot provenance drift alone
does not. The build must never partially use this plan and then silently fall
back to the fuzzy PDF mapper.

If source identity changes but the reviewed 58-page composition remains valid,
refresh it with the dedicated all-or-nothing rebind command. Run the dry-run
first:

```bash
python3 -m tools.reference_layout_rebind \
  --plan docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json \
  --manual-ir <manual.ir.json>
```

The dry-run builds a complete candidate from the validated Manual IR. For a v2
input, the ordinary route requires the semantic content hash, assembly hash,
`source_ref` order, page languages, and physical composition map to remain
unchanged; it refreshes style/provenance identities plus every page's
`source_sha256`, and writes nothing. A v1 input has no assembly pin, so it is
never treated as an ordinary unchanged rebind: migration requires the explicit
approval route below. After reviewing an ordinary v2 summary, apply the same
validated candidate and inspect the Git diff:

```bash
python3 -m tools.reference_layout_rebind \
  --plan docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json \
  --manual-ir <manual.ir.json> \
  --write
```

If semantic content or assembly identity changed—or the input is v1—the
ordinary route remains fail-closed. First prove against the final Manual IR that
`source_ref` order, page-language mapping, `skipped_raw` allowance, physical
page count, semantic page roles, and composition map are the reviewed assembly.
Record the operator's decision and evidence, then run the explicit identity
approval route without `--write`. The existing flag name remains for CLI
compatibility:

```bash
python3 -m tools.reference_layout_rebind \
  --plan docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json \
  --manual-ir <manual.ir.json> \
  --approve-content-change \
  --approved-by "<operator>" \
  --approved-at "<RFC3339>" \
  --approval-method "<recorded review evidence>"
```

Only after reviewing that candidate should the operator repeat the same command
with `--write`. All three approval values are mandatory and are persisted as
contract metadata. This route can update `manual_content_sha256` and the
assembly identity; it cannot change source order, page languages, or the
physical composition map. v1 migration defaults
`allowed_unclassified_source_refs` to an empty list and never manufactures
exceptions: if validation reports unclassified prose, stop and perform a new
reviewed layout approval.

To inspect every registered plan in one dry-run summary, use
`python3 -m tools.reference_layout_rebind --all-registered --manual-ir
<manual.ir.json>`. Batch mode is intentionally read-only and cannot approve a
content change; `--write` and content-approval metadata must be paired with one
explicit `--plan`.

When a refreshed Manual IR needs a new layout review, create a review-only
draft from the existing composition seed instead of hand-editing the 52 page
hashes:

```bash
python3 -m tools.reference_layout_scaffold \
  --seed-plan docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json \
  --manual-ir <manual.ir.json> \
  --output <review/reference-layout-draft.json>
```

The scaffold refreshes source identities, page digests, and the observed
`idml_contract.max_skipped_raw` baseline while preserving the seed's physical
composition map. The output is explicitly `approval.status=draft` and
`production_eligible=false`; it is not added to the registry and cannot
activate production IDML. Composition review, including that skipped-raw
baseline, and explicit approval must happen before a maintainer promotes a
contract and registers it.

The tool preserves file mode and uses an atomic replace only after full plan
validation. It is not a composition editor: a source-order or page-map change
requires a new layout review and approval. Never hand-edit a subset of hashes
or remove the registry entry to unblock a build.

`layout_params_sha256` is derived from the ordered parsed `key`, `value`, and
`unit` rows, not the raw CSV bytes. LF/CRLF changes, blank rows, and changes to
the comment column therefore do not invalidate an approved plan; changing a
token value/unit or reordering semantic rows does. This keeps the hash strict
about renderer behavior without treating formatting-only CSV edits as layout
drift.

Build from the frozen review and phase2 snapshot. For this registered target,
omitting `--source review-asis` is equivalent because `auto` selects the
approved review assembly:

```bash
python3 build.py idml \
  --config configs/config.us.yaml \
  --model JE-1000F \
  --region US \
  --source review-asis \
  --idml-mode production \
  --data-root <phase2-snapshot>
```

The editable-object boundary is part of acceptance, not a designer
preference:

- body text, headings, tables, callouts, Product Overview, and the back cover
  are native InDesign objects/stories;
- illustrations are governed linked assets; RST should identify them as, for
  example, `asset:operation/ac_output`;
- only approved PNG/JPG/JPEG/SVG/PDF exports that match model, region, and
  language may resolve; `.ai` is an immutable archive/source master and is
  never a renderer fallback;
- when live-text redaction cannot separate an illustration from outlined
  labels, a committed asset recipe may use `retain_vector_drawings` to replay
  only explicitly indexed source groups into a new crop-sized vector PDF.
  The retained indices must be ascending, the operator must be the sole
  transform after `crop`, zero-area line groups are overlap-checked safely,
  and unsupported path items or crop/index drift fail closed. Promote only
  after a 12x quarantine comparison and pin the resulting output SHA-256;
- when identical pinned PyMuPDF/MuPDF versions still produce isolated
  cross-platform antialiasing samples, a PNG output may declare
  `rgb_quantization_bits` from 1 through 8. The pipeline rounds every RGB
  channel into that fixed bit-depth before hashing; use the highest visually
  reviewed setting that yields byte-identical replay, and do not use it to
  conceal layout, font, source, or renderer-version drift;
- a PNG output may declare `palette_colors` from 2 through 256 to be written as
  an indexed-colour PNG instead of truecolour. These panels are line art — flat
  fills plus anti-aliased strokes — so a 256-entry palette stores them at about
  half the size, which buys back render scale rather than spending it. It is
  still lossy, so the pipeline measures the result: at most 0.1% of pixels may
  move further than 8/255 on any channel, and an encoding that exceeds it fails
  the intake with the measured share instead of shipping a degraded figure. The
  bound is deliberately about how *much* of the image moves, because the failure
  that would matter on this artwork is banding across a gradient, not a
  reassigned pixel on a stroke. Photographic or heavily graded artwork should
  stay truecolour;
- missing, ambiguous, quarantined, stale, or hash-mismatched used assets stop
  assembly;
- `asset_usage_manifest.json`, `asset_registry_snapshot.csv`, and
  `bundle_manifest.json` are the bundle trace. A `legacy-path` entry is only
  accounted for and does not prove registry governance;
- the approved reference PDF may appear only on a non-printing comparison
  layer. It and visible whole-page body/back-cover files such as
  `product_overview-*.pdf` or `back_cover-en.pdf` must not be used as final
  printed content. A contract-approved finished-art front cover may remain.

`controls/je1000f_us/network_pairing_panel` is an ordinary approved recipe
export, not a reviewed App-promotion output. It shares the official source
recipe with `je1000f-us-app-ui-v1`; adding or changing that recipe therefore
changes the recipe SHA bound by the promotion contract. The promoted App
outputs remain eligible only after a fresh reviewer decision updates that
binding and `python build.py asset-check --json` passes. Never refresh the hash
without the matching review decision.

The extended US front-panel crop is registered as
`overview/je1000f_us/front_controls`, an override of the shared
`overview/front_controls` semantic key. Its PDF/PNG stay under
`docs/renderers/latex/assets` and resolve only for JE-1000F/US. Do not replace
the common Word-template PNG with this US outlet drawing; non-US and future
model targets must continue to receive the shared base asset unless they own a
separate scoped override.

For approved-reference pages, Product Overview composes two governed linked
art frames with native knockout-backed leader paths; the source-authored part
labels are emitted last as unlocked top-layer text frames, so an InDesign
operator can move or edit every label without altering the linked artwork.

The production gate also rejects skipped raw content. Cover/front matter,
Safety + Symbols, FCC + What's in the Box, LCD DISPLAY, specifications,
warranty, and the back cover are the explicit new-page anchors: each starts
its own page as a fixed composite built from explicit component frames,
while ordinary operation, UPS/charging, storage, and troubleshooting
content flows through linked story chains. The
assembler classifies source pages once through
[`tools/idml/page_roles.py`](../../tools/idml/page_roles.py). Every current
template page has an explicit semantic role. If export prints
`[export-idml] WARNING: assembly coverage ...`, the named source page still
uses the historical ordinary-prose fallback and the build remains usable, but
its assembly intent has not been reviewed. Add a target-neutral semantic rule
and regression test before treating that page as governed; do not suppress the
warning with a model, region, language, or physical-page predicate.

The operation-panel renderer keeps the illustration at the bottom of its group,
then emits editable shape underlays, followed by separate unlocked text frames
for Prerequisite, standby, On, and Off. The text frames are therefore topmost
and may be moved or edited independently during final-mile InDesign alignment;
the Energy Saving paragraph after POWER remains full-width prose outside the
panel. Energy Saving then groups its two source guidance paragraphs into the
panel's grey header and exposes On/Off, 3s, and the localized action as separate
top-layer frames. LED groups its source lead into the grey header and exposes
1/2/3, SOS, and each of the three localized instructions separately. These
special layouts are detected from governed image identity plus neighbouring IR
structure, not localized English headings; the original Energy Saving PNG with
baked copy is not eligible for this overlay path. LCD SCREEN composes the
governed LCD illustration and a six-row native grid inside one rounded frame;
its two state, six action, and six description frames are emitted last and stay
independently movable. KEY COMBINATION is detected from its language-neutral
three-column, four-combination source shape. `KeyCombinationStyle.from_context()`
resolves a single base geometry/type token family from `data/layout_params.csv`;
the governed French and Spanish height/indent/gap differences are locale
overrides, not renderer forks or per-page literals. Button and clock assets
plus grid underlays are linked/drawn first; localized headers, button captions,
plus signs, durations, operations, and functions are separate top-layer frames
emitted last, so each remains independently editable and movable.
Approved-reference operation pages additionally apply locale-measured Auto
Resume, LCD SCREEN, and KEY COMBINATION geometry, localized flow gaps, and a
per-language translation of the final story frame. Components compensate that
host-frame translation with a non-negative first-line indent; keep the two
responsibilities separate because InDesign clamps or ignores equivalent
negative offsets on nested inline groups. Non-approved targets retain the
generic component fallbacks.

Approved-reference `referencefigure` promotion routes only by approved-plan
role, canonical source stem, asset basename, and adjacent IR shape; localized
headings are never routing keys. Charging-method compositions promote the AC
caption and the car `Vehicle`/cable note into independent top-layer stories.
The exact App composition applies to the approved English, French, and Spanish
`12_app_setup_placeholder` pages (including their physical-page-prefixed
stems): Download splits Store and QR into linked build-only crops with two copy
frames; Add Device places the approved pairing-panel export below independent
2.1/2.2 and POWER/AC/DC/USB frames; Connect Result crops the three screens and
emits 2.3/2.4/2.5 plus the reference note separately.
The source-page opt-in lives only in the approved contract at
`idml_contract.editable_components.app_add_device.page_owners`. Bundle asset
freezing and production composition consume that same list, including the
contracted page language. Do not add a model/region-named `is_*_page` helper
when onboarding another approved target; add its exact source refs to its own
approved contract.
The three Product Overview tables are the semantic source for Add Device
labels. Stable row/column slots resolve `main_power`, `dc_usb`, and `ac` by
language; the approved plan stores both that exact base snapshot and the
reviewed App display variant. The promotion step removes an adjacent label
block only when its three lines exactly match the base set, so unrelated copy
and Spanish step 2.3 cannot be consumed as overlay labels. Display variants do
not change the frozen source/IR content hash and are not a general content-edit
escape hatch. `AppFigureStyle` owns all nine shared overlay/fit tokens, and an
approved build fails when a required source role, variant, asset, or token is
missing or invalid. Every graphic, shape, and leader extension is emitted
before the unlocked text frames.

Source-authored TOC folios and back-cover copy come from the IR; InDesign must
not recompute or hardcode them. Content, translation, specification, legal,
table-structure, or asset-identity defects are corrected in the
Feishu/source-table/template/review/TM or asset-governance layer and then
rebuilt. The narrow approved App display-variant binding above changes
presentation only and does not authorize other renderer-side copy edits. INDD
is never a second content source.

Review bundles may retain an older opaque attachment hash after a live snapshot
refresh. The build resolves a unique current file by stable semantic identity,
stages it under the frozen basename, and rejects missing or ambiguous matches;
it does not silently emit a broken InDesign link. Rounded native tables remain
editable: a rounded background and a square table frame are grouped, and only
cell text receives the shared one-character inset. Formal body tables use the
full text measure; the one-character inset belongs to cell text, not to the
heading/table group. The finalizer fits LCD and
Meaning of Symbols shells to their composed row heights. The 26-row LCD table
normally stays at 7 rows plus 19 rows per language with a 5.6 mm maximum icon
box; its segment-specific vertical padding follows the approved
`Jackery Explorer 1000 User Manual V2.0` layout.
For governed LCD rows, the renderer first compacts short rows to a
deterministic content minimum and gives the recovered height to rows that need
more wrapped lines; each row is still emitted as an editable auto-growing row
so InDesign can honor the actual installed font metrics. If the complete
minimums still exceed the page budget, whole rows are moved to the next LCD
segment rather than allowing an overset row to remain on the current page. A
single indivisible row may grow beyond one segment's nominal budget. An
approved LCD presentation profile may select positive starting heights by
language and stable source number; the renderer rejects a partially governed
segment instead of mixing those values with InDesign-native growth. Targets
without that optional geometry retain native editable auto-growing rows.
On the combined maintenance/symbols page, the safety-tail panels use the
approved dark warning asset, and the symbol/meaning tables use a light-grey
first column. Signal badges are one-cell native tables with a
linked white warning symbol and editable localized text; French and Spanish
signal labels use the compact reference density, then fit horizontally to the
available badge width so long labels remain on one line. Symbol icon size,
icon-column width, and the gap between the two native tables resolve from the
IDML symbol tokens in `data/layout_params.csv`.
WARNING, CAUTION, NOTE, and TIP labels remain source-owned and are emitted
verbatim; a missing label stops export.
