# Auto-Manual Tool

Updated: 2026-07-20

Auto-Manual turns structured content (Feishu/Lark Base CSV snapshots plus shared RST templates) into target-specific manual bundles and release outputs across the active US, EU, JP, and CN config families.
The current maintained smoke-check baseline is `JE-1000F` across US and JP.

**This README is a quickstart and a navigation map. The full command reference, every operational note (Phase 2 snapshot, review sync, Word/HTML/PDF/MD export, Vercel publish, Read the Docs catalog, Windows cleanup, Git workflow, queue routing) lives in [`code-as-doc/build_doc_guide.md`](code-as-doc/build_doc_guide.md).**

**New maintainer? Start with [`ONBOARDING.md`](ONBOARDING.md)** — the first-hour entrypoint: two-plane topology, what-runs-where (bus-factor register), and the golden-path drill that certifies a hand-over.

**For AI agent windows (Claude Code / Codex):** Claude Code auto-loads [`CLAUDE.md`](CLAUDE.md), which inlines the shared rules in [`AGENTS.md`](AGENTS.md); Codex reads [`AGENTS.md`](AGENTS.md) and the nearest directory-level `AGENTS.md` directly. To start a task in a new window, run `powershell -ExecutionPolicy Bypass -File scripts/start_branch.ps1 <type>/<area>-<topic>` for a fresh branch off up-to-date `main` (the wrapper refuses a dirty tree). Multi-window concurrency rules are in [`AGENTS.md`](AGENTS.md) §8.

## 1. Current Role

This repository is responsible for:

- generating target-specific runtime bundles from templates and local Feishu-synced CSV snapshots, with a valid generated `data/phase2/` snapshot as the default build/review/publish source and explicit `--data-root` still overriding it
- keeping CI deterministic with `tests/fixtures/phase2/` as a frozen sample snapshot while each mirror repo generates its own gitignored `data/phase2/` from its bound Feishu Base
- syncing `main` one-way into [`Bingboom/Hello-Docs`](https://github.com/Bingboom/Hello-Docs) through [`sync-hello-docs.yml`](.github/workflows/sync-hello-docs.yml); `Hello-Docs` keeps its own GitHub Secrets / Variables for the alternate Feishu and OpenClaw bindings, including the `FEISHU_PHASE2_MODEL_CAPABILITIES_TABLE_ID` table binding, with `FEISHU_BUILD_QUEUE_PAUSED=true` scoped to the mirror Feishu runtime workflows until those bindings are ready; trusted Feishu-triggered review PR checks are auto-approved while ordinary external PRs retain GitHub's approval gate
- configuring the mirror binding from local environment variables with [`scripts/configure_hello_docs_binding.sh`](scripts/configure_hello_docs_binding.sh), which writes GitHub Secrets / Variables without printing secret values; use [`scripts/hello_docs_binding.env.example`](scripts/hello_docs_binding.env.example) as the local `.tmp/hello-docs-binding/env.sh` template and add `--include-optional` when the mirror should also receive Feishu IM / OpenClaw adapter values
- auditing the mirror readiness with [`scripts/audit_hello_docs_binding.sh`](scripts/audit_hello_docs_binding.sh), which checks repo variables, required secret names, optional Feishu IM / OpenClaw entries, and source/mirror tree parity without reading secret values
- moving target-specific editing into [`docs/_review/`](docs/_review) once review starts
- validating review/runtime bundles before release
- exporting revision reports and release manifests
- generating same-source design handoff outputs: production IDML is projected
  from the prepared bundle's deterministic manual IR and shared layout tokens;
  the LaTeX page plan is retained as a trace, while ordinary prose uses linked
  natural flow between explicit fixed component pages
- generating fixed-format LaTeX manuals through shared page components: H1
  bars, capsule subbars, safety callouts, rounded table frames, FCC panels,
  inbox cards, warning/caution/note/tip strips, controlled symbol
  continuations, and app steps

This repository is not the place to define the long-term platform strategy.
That boundary lives in [`code-as-doc/architecture/System Evolution Strategy.md`](code-as-doc/architecture/System%20Evolution%20Strategy.md).

## 2. Quickstart

The primary entrypoint is [`build.py`](build.py). A minimal US/EN smoke check:

```bash
python build.py doctor --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py check  --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py review --config configs/config.us-en.yaml --model JE-1000F --region US

# Check the asset control plane and resolve an approved import.
python build.py asset-check --json
python build.py asset-check --asset-key operation/ac_output --asset-format png --json

# Package one PDF-compatible Illustrator master without editing the source,
# worktree, registry, or Feishu Base. The output directory must not exist.
python build.py asset-intake \
  --asset-source-key source/manual_je1000f_us_master \
  --asset-source-file '<local-master.ai>' \
  --asset-recipe data/asset_recipes/manual_je1000f_us_master.json \
  --asset-output-root .tmp/asset-intake/manual_je1000f_us_master/run-01
```

Image sources are registered separately from renderer exports: the editable
`.ai` master is archived in the dedicated Feishu asset-source table, while
[`data/asset_sources.csv`](data/asset_sources.csv) records its scope and hash,
and [`data/asset_generation_candidates.csv`](data/asset_generation_candidates.csv)
records which visual candidates may or may not be sent to an image generator.
`asset-check` resolves only approved exports by default. Its
`--allow-temporary` switch is a diagnostic/operator inspection escape hatch;
normal bundle assembly has no such switch and rejects temporary, missing, or
quarantined `asset:` references.
`asset-intake` first freezes a private, hash-verified source snapshot, then emits
cleaned page PDFs/previews, recipe exports, `manifest.json`, `artifacts.csv`, and
a deterministic ZIP. It fails closed on runtime drift, hash drift, unsafe paths,
render-budget overflow, or Illustrator private markers found in raw or decoded
PDF objects. The command is package-only: Base upload and build promotion remain
separate reviewed steps.
Sensitive App/QR candidates stay quarantined after intake. A production asset may
use `source=reviewed-promotion:<promotion_id>` only through a narrow contract in
[`data/asset_promotions/`](data/asset_promotions) that binds the reviewer, scope,
source AI, frozen reference PDF, recipe/evidence, candidate bytes, output bytes,
and composition with full SHA-256 values. Contract drift fails closed and never
falls back to a same-named shared image.
The maintainer-side `.ai` handoff, duplicate check, attachment upload, and
downloaded-hash verification are documented in the
[`closed_loop_ops_guide`](user-guide/closed_loop_ops_guide.md#492-ai-交付与登记一页流程).

RST can consume one approved registry export by semantic identity instead of
by a renderer path:

```rst
.. image:: asset:operation/ac_output
```

After runtime materialization, review overlay, and attachment-alias staging,
the bundle asset finalizer resolves each `asset:` reference against the exact
model, region, and language, stages only PNG/JPG/JPEG/SVG/PDF exports, and
freezes three bundle-side records: `asset_usage_manifest.json`,
`asset_registry_snapshot.csv`, and the finalized `bundle_manifest.json` with
`bundle_sha256`. HTML, Word, PDF, and Markdown then consume that finalized
bundle. An explicit file under a review `overrides/` tree keeps the semantic
`asset_key` but is recorded as `review-override`; existing path-based images
are recorded as `legacy-path` so remaining migration debt stays visible.

Shared templates are bulk-migrated to `asset:`. A target-specific registry row
may declare `override_for=<shared asset_key>`; the resolver selects that row
only when its model, region, and language scope matches, otherwise the shared
row remains in force. Ambiguous overrides fail closed. A `legacy-path` row
therefore means “accounted for in this bundle,” not “registry-gated.” Editable
`.ai` files are never selected as renderer inputs.
Release manifests do not yet embed this asset lineage; the finalized bundle
sidecars are the current provenance surface.
The cloud archive contract permits only three new tables in the target Base:
`04_资产源文件` (`tblsXlZx61Ff5pQC`), `04_资产定义`
(`tblWilXeN5FXPraC`), and `04_资产导出物` (`tblavT0dcjZGK9DR`). Their live
table/view/field IDs are frozen in
[`data/asset_base_bindings.json`](data/asset_base_bindings.json). The first
master is archived and round-trip hash verified; if these tables later become
inaccessible, archive work stops instead of falling back to the old
illustration table or the staging intake table.

For an editable InDesign handoff with fixed component anchors and natural prose
flow:

```bash
python build.py idml --config configs/config.us.yaml --model JE-1000F --region US --source review-asis
```

Production/both mode builds the LaTeX reference PDF first, then emits
`manual.ir.json`, `latex_page_plan.json`, and the production IDML from that
same frozen bundle. Cover/front matter, Safety + Symbols, FCC + What's in the
Box, LCD DISPLAY, specifications, warranty, and back cover are explicit new-
page anchors; ordinary editable prose is emitted as linked stories that flow
naturally across page frames. InDesign is the final-mile layout workspace;
copy, tables, specifications, legal text, and asset identity remain
source-owned.

Frozen review attachment names are resolved by their stable semantic identity
(ignoring the mutable leading row ordinal and opaque Feishu token) and staged
under the frozen basename; an unresolved or ambiguous asset now fails the IDML
export instead of producing a silent missing-link placeholder.
Fixed composite pages remain componentized, while ordinary operation,
charging, storage, and troubleshooting prose uses normal linked frame chains.
Operation-panel callouts are native top-layer objects: Prerequisite, standby,
On, and Off copy each has its own unlocked text frame above the linked artwork.
The Energy Saving and LED cards use the same contract for their grey-box copy,
On/Off, 3s, step numbers, SOS label, and individual instructions; the linked
artwork and native shape underlays stay below those frames. An InDesign
operator can therefore edit or reposition every label without altering the
source image. The LCD SCREEN card uses the same positioned-object contract for
its left illustration and 14 state/action/description frames. KEY COMBINATION
reconstructs each row from linked button and clock assets, native grid shapes,
and independently movable captions, plus signs, durations, operations, and
functions; the structural 3-column/4-combination shape works identically for
English, French, and Spanish headings.
For approved-reference pages, Product Overview uses two governed linked art
frames, native knockout-backed leader paths, and source-authored labels emitted
last as unlocked text frames. Its `overview/front_controls` semantic reference
selects the `overview/je1000f_us/front_controls` override only for JE-1000F/US;
the shared common-assets PNG remains unchanged for every other target.
Charging figures and the approved English, French, and Spanish App
Setup sources (`12_app_setup_placeholder` and their physical-page-prefixed
siblings) use `referencefigure` composites:
artwork, generated Store/QR/screen crops, and the governed
`controls/je1000f_us/network_pairing_panel` panel remain below separate movable
captions, step numbers, control labels, and notes. The approved JE-1000F/US/en
replica applies a target-scoped reference-label normalization (`POWER Button`
to `Main Power Button`, and `DC / USB` to `DC/USB`) without changing the
source/IR hash; the normalized copy is still emitted as unlocked top-layer
frames. French and Spanish use the same page split and editable geometry while
retaining their localized copy and labels.

Rounded data tables remain
editable: the IDML groups a rounded background with a square content frame so
InDesign does not inset the first/last cells at curved corners. Formal body
tables use the full text measure; the one-character inset belongs to cell text,
not to the heading/table group. During native finalization, each LCD segment's
rounded shell is tightened to InDesign's composed row heights so translated and
continuation tables cannot retain an unfilled bottom band.
The 26-row LCD icon table stays on two pages per language (7-row lead segment
plus 19-row continuation); its 5.6 mm maximum icon box and segment-specific
vertical padding follow the `Jackery Explorer 1000 User Manual V2.0` layout.
On the composed Meaning of Symbols page, the symbol/meaning tables use a
light-grey first column, and native finalization tightens each rounded shell to
its own InDesign row height so no empty band remains below the final row.
NOTE/TIP/CAUTION/WARNING labels are source-owned display text: the LaTeX and
IDML renderers preserve the RST/IR value verbatim and fail when it is missing;
they never singularize, pluralize, translate, or invent a fallback label.

Publish handoffs are portable ZIPs, not bare build-machine IDML files. The
versioned IDML sits at the ZIP root with links rewritten to `file:Links/...`.
Its `missing_assets_report.md` describes package-time link portability, while
`source_asset_resolution_report.md` keeps separate source/flow diagnostics.
Generated reference-figure crops and the pairing-panel PDF are linked
resources: they must be present under `Links/`, and release acceptance runs
native finalization on the exact packaged root IDML, not only the raw
build-machine IDML.

### Approved-PDF native InDesign replica (方案 2)

The approved-replica path for `JE-1000F / US / en+fr+es` is governed by the
[`reference layout registry`](docs/renderers/contracts/reference_layout_registry.json)
and the hash-bound
[`JE-1000F US V2.0 contract`](docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json).
It targets the approved
`Jackery Explorer 1000 User Manual V2.0-2026-06-05.pdf` (SHA-256
`e72b1ba01882062e261b17d5ba54a2f7c3099e5ba531a6428be13888641083f2`):
58 pages at `368.787 × 524.692 pt`, with 3 front-matter pages, 18 pages each
for English/French/Spanish, and one back cover. The plan binds all 52 IR source
references to compositions covering physical pages 1–58. A missing or
mismatched plan, source/hash drift, or page-count drift is a hard failure; this
approval path must not silently fall back to fuzzy PDF matching.

Text, headings, tables, callouts, Product Overview, and the back cover must
remain native InDesign objects/stories. Illustrations are linked, approved
registry exports referenced as `asset:<asset_key>`; the immutable `.ai` master
is archive/source material, not a renderer fallback. The approved reference
PDF may be placed only on a non-printing comparison layer. It and whole-page
body/back-cover exports must not become final visible content; a
contract-approved finished-art front cover is the narrow exception.

Acceptance is page-by-page, not an average score: all 58 pages are rendered at
300 dpi to fixed `1537 × 2187` RGB rasters, with the approved ICC profile,
1 px Gaussian blur, RGB MAD `≤ 0.008`, changed-pixel ratio `≤ 0.040`, and
changed-channel threshold `16`. The deliverable also requires 58-page geometry,
zero overset/missing-font/bad-link findings, PDF/X-4 with
`Japan Color 2001 Coated` / `JC200103`, approved and hash-correct used assets,
and no visible
whole-page shortcut. Do not hand off the IDML/INDD/PDF until the latest parity
report says `accepted=true`. This documentation states the workflow and gate;
it does not claim that the current artifact has passed them. See the
[`approved-replica plan`](code-as-doc/dev/idml_reference_replica_plan.md) and
the [maintainer commands](code-as-doc/build_doc_guide.md#approved-pdf-native-indesign-replica-option-2).

Optional local content QC for the current snapshot:

```bash
python tools/content_lint.py --data-root data/phase2 --json --write-report
```

This writes `findings.json` and `report.md` under `reports/content_qc/<run-id>/`.
It is a local report step only; it does not write Feishu rows or change Word
delivery semantics.

Optional cloud-doc template backport check:

```bash
python tools/cloud_doc_backport.py diff --doc-url <doc-or-fixture.md> --template docs/templates/page_zh/00_preface.rst --doc-type template --out reports/cloud_doc_backport/<run-id>
python tools/cloud_doc_backport.py apply-template --report reports/cloud_doc_backport/<run-id>/cloud_doc_backport_report.json
```

`apply-template` is dry-run by default; add `--write` only after reviewing the
apply report. It only patches guarded template prose deltas and skips
placeholder/spec/table-like changes.

For an in-review cloud doc, the blessed path is `run-review-branch`: it resolves
the cloud-doc's review branch, diffs the cloud-doc against a **render baseline**
(so the deltas are the reviewer's real edits, not RST-source noise), applies only
Class R prose with `--write`, and opens a draft PR into the review branch with
`--push`:

```bash
python tools/cloud_doc_backport.py run-review-branch --doc-name <doc name> --cloud-doc <url>
python tools/cloud_doc_backport.py run-review-branch --doc-name <doc name> --cloud-doc <url> --write --push
```

The legacy `run-review` / `apply-review` diff against the `_review` RST *source*
and are now **guarded**: a `--write` against an `.rst` baseline is refused and
steered to `run-review-branch` (the RST-vs-rendered diff over-reports and corrupts
RST markup) unless `--allow-rst-baseline` is passed. The dry-run still works for
inspection, and `open-pr` promotes a `PR_READY` run manifest:

```bash
python tools/cloud_doc_backport.py run-review --doc-url <doc-or-fixture.md> --source-path docs/_review/<model>/<region>/page/<page>.rst --out reports/cloud_doc_backport/<run-id>
python tools/cloud_doc_backport.py open-pr --manifest reports/cloud_doc_backport/<run-id>/cloud_doc_backport_run.json
```

The `run-review` dry-run writes diff/apply/run reports without editing `_review`;
its `PR_READY` manifest gates `open-pr`. Data-like edits remain report-only
source-table suggestions, and the runner writes
`cloud_doc_backport_source_table_suggestions.md` with candidate source tables and
operator steps. Feishu review highlight tags are stripped as metadata, image-only
token changes are reported as `image_asset_delta` instead of source-table edits,
and page-value rows resolve to `Page_Placeholders_Source` change requests when
the phase2 value index and `source_record_index.json` sidecar are available.
Terminology swaps between output wording and button wording are flagged as
semantic-review-required instead of being auto-written.
`open-pr` is the separate operator-gated PR step: it only accepts a `PR_READY`
run manifest, refuses unrelated working-tree changes, commits the changed
`docs/_review/...rst` source, and opens a draft PR with the manifest summary.
If GitHub rejects PR creation after the branch is pushed, the helper prints a
compare link plus the PR title/body so the operator can create the draft PR
manually.
Cloud-doc backport runs from Claude Code / Codex / a terminal only; it is not a
Feishu IM / BlockClaw command.

For first-pass intake of structured specs/manual tables into reviewable source
data, use `python tools/source_intake.py run --input <spec.md-or-doc-url>
--document-key <MODEL_REGION> --data-root data/phase2 --out
reports/source_intake/<run-id>`. The MVP emits candidate rows and existing-row
source-table change requests only. Close the loop with
`source_intake.py approve`, `source_intake.py apply`, then
`source_intake.py verify`; `apply` is dry-run by default and only writes live
Feishu rows with explicit `--write --table-binding TABLE=BASE:TABLE_ID`. Track
the staged rollout in
[`code-as-doc/dev/source_intake_mvp_checklist.md`](code-as-doc/dev/source_intake_mvp_checklist.md).

For the full review-first flow, queue-driven Draft/Publish workers, matrix runners, and every command flag, see [`code-as-doc/build_doc_guide.md`](code-as-doc/build_doc_guide.md). For the editing-surface and source-of-truth rules, see [`user-guide/hello_auto-doc.md`](user-guide/hello_auto-doc.md) and [`user-guide/quick_start_guide.md`](user-guide/quick_start_guide.md). For BlockClaw / Feishu IM behavior, including batch document-link replies and read-only `发布文档管理` manual-index lookups, see [`integrations/openclaw/feishu-im-webhook-adapter/README.md`](integrations/openclaw/feishu-im-webhook-adapter/README.md).

The fixed US + JP release matrix runners — [`scripts/build_us_jp_manuals.py`](scripts/build_us_jp_manuals.py) and [`scripts/build_us_jp_manuals.ps1`](scripts/build_us_jp_manuals.ps1) — are documented in [`code-as-doc/build_doc_guide.md`](code-as-doc/build_doc_guide.md). For a US-only subset, pass `--languages en,es,fr` (or the subset you need) to the same runner.

Do not treat this file as the full command reference.
The command semantics and output layout are maintained in [`code-as-doc/build_doc_guide.md`](code-as-doc/build_doc_guide.md).

## 3. Editing Surfaces

Use different surfaces for different stages:

- shared template changes: [`docs/templates/`](docs/templates)
- structured data changes: Feishu phase2 source tables are the authoring surface; [`data/phase2/`](data/phase2) is a gitignored local snapshot root used by build, review, and publish flows
  `Manual_Copy_Source.csv` is the human-maintained single-language source for reusable page chrome and labels such as LCD / Symbols page titles, table headers, Product overview part labels, Symbols signal labels / meanings, and spec page / section titles. `Localized_Copy.csv` and `spec_titles.csv` are generated from that source plus Translation Memory rows tagged `manual_copy`; do not maintain either file directly online. Keep long instructional prose in RST templates, model/spec values in `Spec_Master.csv`, normal Symbols row content in `symbols_blocks.csv`, and LCD description variables in `Variable_Defaults.csv` plus `Variable_Lang_Overrides.csv`. Image alt text is derived from existing page titles, panel titles, `symbol_key`, or generated signal labels instead of duplicated as copy rows. LCD status-word bolding is driven by `Status_Words.csv`, a local snapshot of Translation Memory rows marked `是否为 status word=Y`, so status words are not duplicated in `Localized_Copy.csv` or the LCD icon table.
  `Spec_Footnotes.csv` is now the footnote-definition table only. Keep one row per reusable `Footnote_id`, target rows by `Region` + `Model`, and let the system derive the visible superscript marker from `Footnote_order`.
`Spec_Master.csv` is now a read model rebuilt from Feishu `规格参数明细` (`Page=specifications`) and `页面占位参数` (non-spec placeholder pages). Its first column is `spec_row_key`; `document_key` remains the target dimension. In the two source tables, `Row_key` is derived from `参数名.Row_key` through `Row_key_link`, so editors choose the dictionary row instead of typing the key; `Model` and `Region` are also omitted from the source tables and derived from `document_key` during rebuild. `Page` may now be a comma-separated page list. Use `Product overview` for Product overview-only placeholder rows, and use `Product overview, specifications,` when the same row is shared by both pages. For page-value rows, keep `Row_key` as the concept and use `Slot_key` to describe the placeholder slot. The shared source-text columns are `Row_label_source`, `Param_source`, and `Value_source`; they hold the row's source-manual text. `Source_lang` stores that source-language code explicitly, for example `en`, `ja`, or `zh`, and code no longer infers it from `Region`. `document_key` is the target helper column in `[Model]_[Region]` form; `Source_lang` stays separate. `Row_order` is now a formal column and controls the row display order inside each `document_key + Page + Section`, while `Line_order` is required and controls the order of multiple lines inside one logical row. Visible section defaults can live in `spec_titles.csv section_order`, but if `Spec_Master.csv Section_order` is filled, that explicit value has the highest priority. `Row_label_en`, `Param_en`, and `Value_en` are no longer supported; source-language text must live in `*_source`. The old `project_code` / `项目代码` column has been removed; row targeting now uses `Region` + `Model`. Spec-cell footnotes are now referenced through `Row_label_footnote_refs`, `Param_footnote_refs`, and `Value_footnote_refs`; do not handwrite `①②③` into visible spec text.
  The configured source-table views are part of the binding: `sync-data --table spec_master` reads the pinned spec-row view and placeholder view instead of falling back to unfiltered table reads.
  `Spec_Footnotes.csv` and `Spec_Notes.csv` both include a `Type` column from the Feishu source. Keep it explicit as `Footnote` or `Note`; downstream spec rendering preserves that type instead of inferring it from text content.
  `Spec_Notes.csv` now stores bottom-of-spec notes that are not tied to a superscript reference, such as trademark statements. When both note and footnote blocks appear at the bottom of one spec page, their final display order is controlled by [`docs/templates/spec_template.rst`](docs/templates/spec_template.rst).
  `symbols_blocks.csv` stores symbols-page table rows, uses `symbol_key` as its primary key, uses `Market` and `Model` to match target manuals, keeps `Source_lang` explicit, and includes an `image_path` field for the referenced icon asset. Use `block_type=table_row` for normal symbol/meaning rows, and `block_type=signal_row` for warning/caution/danger/note/tip signal structure. Signal rows own the signal token (`symbol_key`), target scope, order, and optional icon asset; visible signal labels and meanings are maintained in `Manual_Copy_Source.csv` and generated into `Localized_Copy.csv` through Translation Memory. Legacy `label_*` and `aliases_*` columns are compatibility mirrors for detection only, not the maintained copy source; put old variants or editorial context in `notes`. When the authoring Base provides a `Figure` attachment, `sync-data` downloads it into `data/phase2/_attachments/symbols/` and uses that local file as `image_path`. Use `Market=Global` for rows shared across markets.
  `troubleshooting_blocks.csv` stores troubleshooting error-code rows from the shared TROUBLESHOOTING Base table. Use `Region` and `Model` to target the same page across US, EU, pt-BR, JP, and CN; use `Is_latest=TRUE` for active rows; keep the localized corrective text in `corrective_measures_en/fr/es/pt-BR/br/de/it/ukr/jp/zh`. The active `docs/templates/**/10_troubleshooting.rst` files own the localized page title, intro, table headers, and table settings, and expose `{{ troubleshooting_rows_rst }}` where Base rows are inserted.
  Safety intro pages are now maintained as fixed RST templates under [`docs/templates/page_*/safety_*.rst`](docs/templates), wired through each family's manifest or page list. The standalone user maintenance instructions page is maintained under [`docs/templates/page_shared/<lang>/01_user_maintenance_instructions.rst`](docs/templates/page_shared/en/01_user_maintenance_instructions.rst) and is included immediately before the `symbols` page in the US/EU manifests. JP still keeps its detailed warning content in [`docs/templates/page_jp/01_meaning_of_symbols.rst`](docs/templates/page_jp/01_meaning_of_symbols.rst). The old `content_blocks.csv` safety source has been removed from the active repo flow.
- target-specific review edits after review starts: [`docs/_review/`](docs/_review)
- generated runtime and export outputs: [`docs/_build/`](docs/_build)

Rule:

- before review starts, seed the draft from templates and data
- after review starts, edit `_review`
- do not use `_build` as the long-lived editing surface

The current user workflow and source-of-truth rules are maintained in [`user-guide/hello_auto-doc.md`](user-guide/hello_auto-doc.md).

## 4. Document Map

Use the document that owns the topic:

- maintainer doc index and ownership map: [`code-as-doc/README.md`](code-as-doc/README.md)
- current business logic overview and invariants: [`code-as-doc/business_logic_overview.md`](code-as-doc/business_logic_overview.md)
- current maintainer command reference: [`code-as-doc/build_doc_guide.md`](code-as-doc/build_doc_guide.md)
- current JP / US family difference boundary: [`code-as-doc/manual_family_guide.md`](code-as-doc/manual_family_guide.md)
- current Git branching and GitHub protection rules: [`code-as-doc/dev/git_branching_guide.md`](code-as-doc/dev/git_branching_guide.md)
- current Vercel latest-publish HTML flow: [`code-as-doc/dev/vercel_review_preview_guide.md`](code-as-doc/dev/vercel_review_preview_guide.md)
- current user workflow and editing rules: [`user-guide/hello_auto-doc.md`](user-guide/hello_auto-doc.md)
- happy-path example: [`user-guide/quick_start_guide.md`](user-guide/quick_start_guide.md)
- architecture doc index: [`code-as-doc/architecture/README.md`](code-as-doc/architecture/README.md)
- current repository component map: [`code-as-doc/architecture/Hello_Docs_Architecture.md`](code-as-doc/architecture/Hello_Docs_Architecture.md)
- AI agent operating rules (Claude / Codex / future agents): [`AGENTS.md`](AGENTS.md), with [`CLAUDE.md`](CLAUDE.md) as the Claude Code entrypoint and directory-level `AGENTS.md` files as the Codex local maps
- Codex scaffolding and architecture audit: [`code-as-doc/reviews/codex_scaffolding_discovery.md`](code-as-doc/reviews/codex_scaffolding_discovery.md)
- Codex skill migration plan: [`code-as-doc/reviews/codex_scaffolding_implementation_plan.md`](code-as-doc/reviews/codex_scaffolding_implementation_plan.md)
- current OpenClaw bootstrap: [`agent/BOOTSTRAP.md`](agent/BOOTSTRAP.md)
- current OpenClaw integration package: [`integrations/openclaw/README.md`](integrations/openclaw/README.md)
- repo-local translation memory skill for OpenClaw-assisted multilingual work: [`.agents/skills/bitable-translation-memory/SKILL.md`](.agents/skills/bitable-translation-memory/SKILL.md)
- repo-local Feishu DOCX preprocessing skill for TM-backed source/target language conversion: [`.agents/skills/lark-tm-translation-preprocess/SKILL.md`](.agents/skills/lark-tm-translation-preprocess/SKILL.md)
- repo-local TM-first manual rewrite skill for structured Markdown/manual translation work: [`.agents/skills/manual-rewrite-with-tm/SKILL.md`](.agents/skills/manual-rewrite-with-tm/SKILL.md)
- future canonical content model: [`code-as-doc/architecture/Content_Data_Model.md`](code-as-doc/architecture/Content_Data_Model.md)
- long-term strategy and stable architecture boundaries: [`code-as-doc/architecture/System Evolution Strategy.md`](code-as-doc/architecture/System%20Evolution%20Strategy.md)
- repo-level execution roadmap: [`code-as-doc/optimization_project.md`](code-as-doc/optimization_project.md)

## 5. Key Directories

- [`build.py`](build.py): top-level CLI entrypoint
- [`.readthedocs.yaml`](.readthedocs.yaml): Read the Docs build config for the generated MyST manual catalog
- [`tools/`](tools): orchestration, rendering, validation, diff, and release helpers
- [`docs/manifests/`](docs/manifests): page-stack manifests for manifest-driven manual families
- [`docs/templates/page_zh/`](docs/templates/page_zh): shared zh prose-template family for the CN manual stack
- `data/phase2/`: gitignored Feishu-synced CSV snapshot inputs for active build, review, and publish flows; only the repo-maintained [`data/phase2/page_registry.csv`](data/phase2/page_registry.csv) stays tracked because `sync-data` reads it as input
- [`data/source_table_contracts/phase2_source_tables.json`](data/source_table_contracts/phase2_source_tables.json): repo-maintained source-table contract for phase2 keys, snapshot files, intake targets, writable fields, and source-record-index mapping; update it when online source-table structure changes. `tools/schema_drift.py` validates the contract against fixture/local snapshot headers in CI.
- [`tests/fixtures/phase2/`](tests/fixtures/phase2): committed fixture snapshot used only by CI/tests, not by live authoring
- [`docs/templates/`](docs/templates): shared seed templates
- [`.agents/skills/bitable-translation-memory/`](.agents/skills/bitable-translation-memory): repo-local Codex skill for live sentence-pair lookup and terminology grounding
- [`.agents/skills/lark-tm-translation-preprocess/`](.agents/skills/lark-tm-translation-preprocess): repo-local Codex/OpenClaw skill for Feishu DOCX preprocessing with configurable Translation_Memory source/target language pairs and yellow-highlighted replacements
- [`.agents/skills/manual-rewrite-with-tm/`](.agents/skills/manual-rewrite-with-tm): repo-local Codex skill for TM-first Markdown/manual rewrite with structure preservation and `==...==` unmatched fallback
- [`.agents/skills/markdown-rst-template-intake/`](.agents/skills/markdown-rst-template-intake): repo-local Codex skill for mapping external Markdown manuals into the current RST template and recipe layout
- [`docs/_review/`](docs/_review): target-specific review layer
- [`docs/_build/`](docs/_build): runtime bundles and export outputs
- [`reports/`](reports): revision reports and release manifests
- [`tests/`](tests): automated regression coverage

## 6. Maintenance Rule

When command behavior, workflow ownership, or architecture boundaries change:

- update the owning document in the same change
- keep `python tools/check_maintainability_guardrails.py` green when touching the guarded hotspot files
- keep the PR checklist honest: if a helper boundary moves, update the module map in the same change
- avoid restating the same rules in multiple docs
- keep history in [`code-as-doc/code_optimization_log.md`](code-as-doc/code_optimization_log.md), not in the current guides
