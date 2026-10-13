# Optimization checklist: Milestone M execution slices

Part of the [optimization checklist](../next_optimization_checklist.md); its index lists every milestone page,
and its §1 update rules apply here. Update item status on this page and add new
items for this milestone here, not to the hub.

### Milestone M execution mode — vertical slice first (operator, 2026-08-21)

The wave structure below M-pre was **replaced by a vertical slice** on operator
direction: prove the full chain narrowly (one battery-pack target, one content
module, all four renderers, one real InDesign finishing round) before any
horizontal rollout. The audited wave items are preserved as deferred rollout
stubs at the end of this section; their full text is in git history
(commit 80321368). M-pre applies to slice and rollout alike.

Slice target (evidence: workflow `wf_72e57478-50e`): **`JBP-2000B_US`**
(HTP017 美加规, 3 languages, 28 pages, cell `BP@INTL`) — the only battery-pack
document_key that is **multi-language** (`data/model_capabilities.csv` carries
three JBP-2000B rows: `_CN`, `_JP`, `_US`, all all-FALSE, but CN and JP are
single-language) + a fully-specced paired host (`JE-2000E_US`, 50 Spec_Master
rows, verified) + a shipped book to reconcile against. Its capability row is
all-FALSE, so the existing gates drop UPS/extra-battery pages with zero work.
Data intake is **11 spec-detail rows + 9 page-placeholder rows**, all 13
needed `Row_key`s already present in `02_主数据_参数名` — but *not* zero new
vocabulary: it also needs 4 new `02_主数据_Slot` records and 1 new
`Manual_Copy_Source` copy key (see S4).
Content module: **`battery_long_storage_advisory`** (storage-page tail
paragraph; 7/7 battery-pack coverage, **9** hand-copied replicas, 0
placeholders, 0 brand words) — replaces `user_maintenance_instructions`, which
is 0/7 in battery packs and is demoted to a rollout host-line module. The 9
are the only `*storage*` templates in the repo:
`page_shared/{de,en,es,fr,it,ko,pt-BR,uk}/09_storage_and_maintenance.rst` plus
`page_zh/09_storage_and_maintenance.rst`; every one carries the advisory
exactly once (the other hits under `docs/` are build output and one review
derivative, not maintained copies).
Slice red lines: **no edits to `data/layout_params.csv` or any approved
reference-layout contract** (the JE-1000F/US plan hashes the entire CSV — one
added row unpins it, the #720 failure shape); no `figure_targets` whitelist
expansion; no JE-300E fork reclamation; no authoring flip (the resolver is
generate-then-verify; YAML stays the source of truth).

- [x] PR S1: Three layers + `BP@INTL` skeleton instance + slot_id guard
  - Status: `done` (merged 2026-08-21, #936, squash `1823cc4e`; full suite
    2979 tests OK, ruff clean, guardrails OK, fold 18/3/15, resolver verify
    green)
  - Gate: operator approves the slice plan (granted 2026-08-21).
  - Target files:
    - `docs/manifests/skeletons/bp-intl/blueprint.yaml` (new — Skeleton
      Blueprint: ordered `slot_id` list, `requirement` per slot
      (required/optional/capability:X), `presentation` four states, semantic
      co-page pairs; no languages, no regions, no file paths)
    - `tools/skeleton_resolve.py` (new — resolves Blueprint × capability row ×
      region profile × language set into a Product Manual Plan, and emits the
      Resolved Manifest; **generate-then-verify**: the emitted YAML must equal
      the committed manifest byte-for-byte, mirroring the family-diff
      discipline)
    - `docs/manifests/manual_bp-us.yaml` (new — the Resolved Manifest,
      committed; 3-language expansion included, 8-page blocks). Three
      spellings are load-bearing and none is interchangeable: the **file** is
      hyphenated `manual_bp-us.yaml`, its internal **`manifest_id`** is
      `manual_bp_us`, and `config.bp-us.yaml`'s **`build.family_id`** is
      `bp-us`
    - `docs/manifests/skeletons/bp-intl/slot_templates.yaml` (new — the
      slot→carrier mapping: `slot_id` → page_type / template / recipe /
      csv-page source)
    - `docs/manifests/region_profiles/us.yaml` (new — language-set reference,
      compliance mounting rows, cover/TOC/back-cover form, contact params)
    - `configs/config.bp-us.yaml` (new) — **decision recorded in the PR**:
      a new config is required because `config.us.yaml`'s `page_manifest` is
      static and a `{model}` token there would redirect JE-1000F too.
      Carries a unique `build.family_id: bp-us`.
    - [`../tools/config_pages.py`](../../tools/config_pages.py) — page entries
      accept an optional `slot_id`; for slot-bearing entries the materialized
      name derives from `slot_id` and **bypasses `ensure_unique_name`'s
      first-wins bare-name behavior**; entries without `slot_id` (all 17
      existing manifests) go through the legacy path byte-identically
    - [`../docs/manifests/family/index.yaml`](../../docs/manifests/family/index.yaml) + [`../tests/test_manifest_family.py`](../../tests/test_manifest_family.py) per M-pre.2
    - three surfaces the plan missed, all found while landing #936:
      [`../tools/gen_index_bundle_plan.py`](../../tools/gen_index_bundle_plan.py)
      (`slot_id` must survive planning, not only config parsing),
      [`../tools/process_review_start_queue.py`](../../tools/build_queue/process_review_start_queue.py)
      (a second region-only resolver — see the queue guard below), and
      [`../.github/ci_check_targets_skip_baseline.json`](../../.github/ci_check_targets_skip_baseline.json)
      (`skip_count` 4 → 5: the committed fixture snapshot has no
      `JBP-2000B_US` document_key, so CI reports the new target as **SKIP**,
      not coverage — S4 must ratchet it back down)
  - **Queue-routing guard (P0, operator review 2026-08-21; unified
    2026-08-24):**
    [`../tools/queue_config_resolution.py`](../../tools/build_queue/config_resolution.py)
    `config_match_score` adds +1 to **any** filename that is not
    `config.us.yaml`, so a US 3-language BP config outscores the host config
    105:104 — a plain US queue record with no `Build_family` would silently
    build a host manual from the battery-pack manifest. #936 originally
    guarded this with explicit `Build_family=bp-us`; that interim contract is
    superseded by the unified target + language resolver:
    - Base `Build_family` now remains the language range (`us-merged` for both
      MAIN and BP); `config.bp-us.yaml` keeps its internal `family_id=bp-us`
      and declares `language_family=us-merged`
    - `queue_requires_target_match` keeps BP out of every model-less fallback;
      an exact `Document_Key` model/region match is required before it can win
    - Start Review, Draft, Publish, and Preview share the same target scorer;
      JBP + `us-merged` resolves BP, ordinary host + `us-merged` resolves MAIN,
      and the legacy `bp-us` selector remains temporarily accepted
    - regression tests in `tests/test_queue_config_resolution.py`,
      `tests/test_process_review_start_queue.py`, and
      `tests/test_build_review_preview.py` cover those boundaries
  - **Resolver contract closure (operator review 2026-08-21):** every slot
    decision must trace to one of exactly three data carriers —
    `blueprint.yaml` (slots, requirement, presentation, co-page groups),
    `slot_templates.yaml` (slot→carrier), `region_profiles/us.yaml`
    (region parameters). Resolution precedence is fixed and documented:
    blueprint slots → capability gate (`model_capabilities.csv` row) →
    region profile → language expansion. `tools/skeleton_resolve.py` may
    contain **no slot-specific or region-specific literals** — any such
    literal is the template-clone failure mode reborn as resolver branches,
    and is a review-rejection criterion for this PR.
  - Done when:
    - blueprint slots carry stable `slot_id`s and the **new** manifest's
      materialized names derive from `slot_id`, not iteration position; the
      existing manifests' naming path is untouched (zero `pNN_` pin risk)
    - `python3 -c "import tools.target_defaults"` succeeds with the new config
      present, **and** `discover_target_defaults()` still resolves the US
      family default to `config.us.yaml` (guard against the silent-swap
      failure verified on the JP experiment; both `_family_default_map` and
      `_language_config_map` paths checked)
    - both queue-routing regression tests above pass
    - `manual_bp-us.yaml` is registered as the **third repository anchor**;
      `python3 tools/manifest_family.py fold` passes with exactly
      **18 manifests / 3 anchors / 15 folded** (re-measured green 2026-08-21)
    - the resolver proves emitted == committed bytes. `verify` is a
      **subcommand, not a flag**, and every argument is required:
      `python3 tools/skeleton_resolve.py verify --skeleton-dir
      docs/manifests/skeletons/bp-intl --region-profile
      docs/manifests/region_profiles/us.yaml --manifest-id manual_bp_us
      --manifest docs/manifests/manual_bp-us.yaml`. A wrong `--manifest-id`
      reports MISMATCH on a perfectly healthy tree
    - blueprint contains no `app_setup` and no `user_maintenance_instructions`
      slot (0/7 in corpus battery packs); `ups_mode`/`extra_battery` slots are
      `capability:`-gated and drop via the existing all-FALSE row
  - Verification: `python3 -m unittest`; fold; import probe; M-pre.4 staging
    diff on JE-1000F/US and JE-1000F/JP (host lines byte-identical).
  - Rollback: revert config + manifest + index + blueprint together; resolver
    is additive.

- [x] PR S2: Minimal contract tiering + BP recipes (mechanism + BP tier only)
  - Status: `done` (merged 2026-08-21, #937, squash `eeb8eaa8`)
  - Gate: S1 merged (#936).
  - **Mechanism correction (P0, operator review 2026-08-21 — verified in
    code):** the required spec rows come from **`recipe.required_row_keys` and
    `recipe.field_map`**
    ([`../tools/validate_spec_master_shared.py`](../../tools/validate_spec_master_shared.py)
    lines 275–288, still accurate), resolved through the manifest's
    `generated_page` entries — **not** from page contracts. Contracts gate
    assembly-time placeholders, a different surface. The first draft's claim
    that editing two contract YAMLs achieves 93 → 11 was wrong, and #937
    measured that the *attribution* was wrong too: 93 issues appear only under
    the **host** config (`config.us.yaml --model JBP-2000B`). Under S1's BP
    manifest the baseline was already **12**, because the blueprint has no app
    slot and the manifest points at BP recipes — so **S1 did 81 of the
    reduction** and S2's real job was **12 → 6**. The residual is not 11
    either: `validate_spec_master` reports per (language × binding), so one
    data gap surfaces many times. S2's actual exit condition was
    **`MISSING_RECIPE` == 0**.
  - Target files:
    - `docs/templates/recipes/bp-us/03_product_overview.yaml`,
      `docs/templates/recipes/bp-us/05_operation_guide.yaml` (new — recipes
      are **per-line by design**, this is not a fork). The 11-row list is the
      **intake** row set, not the recipes': the seven pure spec-page rows
      (`capacity`, `cell_chemistry`, `weight`, `dimensions`, `cycle_life`,
      `charging_temperature`, `discharging_temperature`) reach the book
      through the `csv_page` spec path and are never named by a recipe. As
      merged, 03 carries `required_row_keys: [product_name, model_no]` plus a
      `field_map` over `main_power_button` and `dc_expansion_port`; 05 carries
      `default_standby_duration` (restored in S4 — S2's empty `field_map` was
      one row too aggressive)
    - [`../tools/page_contracts.py`](../../tools/page_contracts.py) so the
      **shared** 03/05 contracts accept BP without a contract fork. As merged
      the shape is `ContractContext(lang, category, region, capabilities)`
      with `_TIER_PREFIXES = ("category:", "region:", "capability:")` and
      **`+`-joined conjunction keys** (`category:MAIN+en`). Real data forced
      the conjunction: `FRONT_TOTAL_OUTPUT_*` is host-only *and*
      language-scoped. No `requires_capability` group type shipped, and
      `region:` was added and was not in the plan. The
      14 host-specific placeholder groups (`ac_input`, `ac_output`,
      `ac_power_button`, `dc12_port`, `dc_input`, `dc_usb_power_button`,
      `default_standby_duration`, `energy_saving_ac_threshold`,
      `energy_saving_auto_off_duration`, `energy_saving_dc_threshold`,
      `main_power_button`, `total_output`, `usb_a`, `usb_c`) move behind host
      tiers
    - [`../docs/templates/contracts/03_product_overview.yaml`](../../docs/templates/contracts/03_product_overview.yaml), `05_operation_guide` contract
    - [`../tools/validate_spec_master_shared.py`](../../tools/validate_spec_master_shared.py)
      **only if** contract validation needs category/capability context passed
      through — determine in the PR, with tests either way
  - Scope guard: **the JE-300E fork is not touched** — reclaiming it is
    rollout work.
  - Done when:
    - `validate_spec_master` for `JBP-2000B_US` reports **`MISSING_RECIPE` ==
      0** and nothing but genuine missing-data rows, zero contract issues.
      Measured at merge: **21** issues. Re-measured 2026-08-21 on top of S4's
      recipe corrections: **30** — 10 requirement bindings over 5 distinct
      row_keys, × 3 languages. All are closed by the S4 intake
    - JE-1000F/US builds **byte-identically** (M-pre.4 worktree diff) — the
      tiering must be a pure no-op for hosts
  - Guard tests: [`../tests/test_page_contracts.py`](../../tests/test_page_contracts.py),
    [`../tests/test_validate_spec_master.py`](../../tests/test_validate_spec_master.py),
    + a new tier-resolution test.
  - Rollback: `git revert`.

- [x] PR S3: Extract `battery_long_storage_advisory` as the first real snippet
  - Status: `done` (merged 2026-08-22, #938, squash `71f7c5ec`; 18/18 checks
    green on a base refreshed to include S4, the illustration assets and the
    review-sync fix, after the pre-merge check found its earlier green predated
    all three)
  - Gate: S1 merged (#936).
  - Target files:
    - `docs/templates/snippets/battery_long_storage_advisory/{en,fr,es}.rst` (new)
    - [`../docs/templates/snippets/registry.yaml`](../../docs/templates/snippets/registry.yaml) — first real entry in the literal `snippets: []`
    - the BP storage page. As built it is a **plain `rst_include` page**
      (`docs/templates/page_bp/{en,fr,es}/09_storage.rst`) whose template
      names the snippet id directly — **not** a `generated_page` + recipe
      `snippet_slots` slot. That is the finding, not a shortcut: nearly all
      shared prose lives in `rst_include` templates, so a snippet layer that
      reached only generated pages could never collapse a hand-copied module,
      which is why the registry sat empty
    - `slot_templates.yaml` + `manual_bp-us.yaml` re-point the `storage` slot
      away from `page_shared`, so #938 is also a manifest PR and carries
      M-pre.1 and M-pre.2
  - Scope: the BP book **consumes** the module in all three languages; the 10
    host-side hand copies are measured but **not collapsed** (rollout work,
    with byte-diff proof per copy). Module body is the tail paragraph only —
    verified 0 placeholders (the page's temperature lines above it carry the
    placeholders; the boundary excludes them).
  - Done when:
    - registry non-empty and schema-valid; the snippet splices literally. The
      splice is `resolve_snippet_tokens` in
      [`../tools/draft_engine.py`](../../tools/draft_engine.py) — do **not** pin
      a line number (it moved 580 → 529 on the branch) — called from the
      draft engine for generated pages and from
      [`../tools/gen_index_bundle_page_render.py`](../../tools/gen_index_bundle_page_render.py)
      for include pages. A page carrying no token does zero registry work and
      keeps its exact bytes
    - the module renders in all three language blocks of the BP book
    - presentation is `untitled_block`, never enters any TOC
  - Guard tests: `tests/test_snippet_layer.py` (added by #938) (new, 202 lines) — `test_draft_engine.py` is not the carrier.
  - Rollback: `git revert`; snippet files become orphans.

- [x] S4: Data intake + ten authored templates (operator-gated)
  - Status: `done` (merged 2026-08-22, #940, squash `5e1d0c26`). Both halves
    landed: the live source-table intake was executed under operator
    confirmation (record_id ledger in
    [`../code-as-doc/reviews/jbp2000b_us_intake_record_ids_2026-08.md`](../reviews/jbp2000b_us_intake_record_ids_2026-08.md)),
    `build.py check --config configs/config.bp-us.yaml --model JBP-2000B
    --region US` exits 0, and the CI ratchet was reversed in #944
    (squash `baf8b712`): `tests/fixtures/phase2` now carries the
    `JBP-2000B_US` rows, `skip_count` is back to 4 and the lane reports the
    target as PASS (`PASS=12 SKIP=4 FAIL=2`, verified in the CI log, not just
    locally). The four illustration assets landed separately in #942
    (squash `c8b83f65`). Original open-PR note follows:
  - Was: PR #940 open on `feat/skeleton-s4-bp-intake`,
    17/17 checks green, carrying the **repo-side half only**: the ten BP page
    templates, `required_copy_keys` tiering in the 03 contract and
    `required_placeholders` tiering in the 05 contract, corrections to both
    bp-us recipes, and the intake-order review doc. The **live source-table
    intake has not happened** — it is blocked on the operator, specified row
    by row in
    `code-as-doc/reviews/jbp2000b_us_intake_order_2026-08.md` (added by #940),
    awaiting per-row / per-batch confirmation.
  - Gate: S2 merged (#937); operator approves each live-table write (existing
    spec-intake gate, per-write readback).
  - Work:
    - 11 `03_内容源_规格参数明细` rows + 9 `03_内容源_页面占位参数` rows for
      `JBP-2000B_US` (both land in the local `data/phase2/Spec_Master.csv`
      mirror). Spec `Row_key`s: `product_name`, `model_no`, `capacity`,
      `cell_chemistry`, `weight`, `dimensions`, `cycle_life`,
      `dc_expansion_port` ×2, `charging_temperature`,
      `discharging_temperature`; all 13 needed keys already exist in
      `02_主数据_参数名`
    - **not "via the existing clone-ingest path".** Nothing in that path
      physically blocks this intake; what is missing is first-class semantics
      for a **category** clone. (a) `build_staging_plan`'s key-set equality
      check (`source_intake_staging.py:286-294`) compares two caller-supplied
      JSON inputs, not the live tables — feeding it the 11-row projection of
      `JE-2000E_US` as `--spec-sibling` passes and yields a valid 11-row
      payload. The genuine gap is that a **subset** clone is then
      indistinguishable from a full one: no field declares the 10 excluded
      sibling rows, the summary still prints `complete: N rows cover region
      siblings (N)`, and hand-trimming the sibling export silently defeats the
      skill's hard gate 2. That argues for an explicit subset/tiering mode
      with a recorded exclusion list — not for calling the intake
      inexpressible. (b) The payload carries one localized pair per run and
      `--localized-lang fr,es` produces one bogus `手册值_fr,es` column — but
      BP US needs **no** staging localized columns: run `stage-plan` with
      `--localized-lang` omitted for the English structural layer, since the
      formal source tables already carry `Value_fr` / `Value_es`. The hard
      wall is downstream, not in `_STAGING_FIELDS`: the staging→source commit
      driver reads only `手册值_ko` / `行标签_ko`
      (`intake_commit_driver.py:399,401`) and explicitly refuses any other
      `Value_<lang>` (`:431-435`)
    - 4 new `02_主数据_Slot` records, written **first** because they gate the
      placeholder payload's `Slot_key_link`: `side.a.label`, `side.a.spec`,
      `side.b.label`, `side.b.spec`. The shipped overview page prints two
      physical expansion ports A/B, each a label plus a "connect to expansion
      cable terminal X" sub-note; none of the 17 existing slots carries an
      A/B position. `Slot_key` syntax is `placement.variant.role`, isomorphic
      to the host's `side.pv.spec` / `side.car.spec`
    - 1 new `Manual_Copy_Source` row (`product_overview.left_side_view`,
      `copy_type=panel_title`) **and its TM pair in the same batch** — BP
      prints LEFT SIDE VIEW where the host prints RIGHT SIDE VIEW.
      `build_spec_title_rows` and copy localization are both
      `translated or source_text`, so a missing TM entry **fails open**: the
      fr and es pages print the English panel title and the build stays green
    - battery-pack troubleshooting codes (8 codes, printed p05/p13/p21) as
      Model-scoped `troubleshooting_blocks` rows, plus the LCD icon rows
      (printed p03/p11/p19)
    - **ten** authored templates, not two. There is **no `installation` slot
      anywhere in the BP@INTL blueprint** — verified against
      `blueprint.yaml` and `slot_templates.yaml`: the `page_bp` carriers are
      `toc` at primary language only, plus `product_overview`, `operation`
      and `connections` at `{lang}`. So `page_bp/en/00_toc.rst` +
      `{en,fr,es}` × `03_product_overview_placeholder.rst`,
      `04_connections.rst`, `05_operation_guide_placeholder.rst`. Provenance
      per M-pre.5 (HTP017 US shipped book, printed p02-p04 and their fr/es
      counterparts p10-p12 / p18-p20); operator reviews wording; fr/es copy
      comes from the shipped book itself — the translations exist in print
    - **recorded degradation: three illustrations are unregistered** in
      [`../data/asset_registry.csv`](../../data/asset_registry.csv) — the BP
      front view, the BP left-side view, and the stacking/clearance diagram.
      The `connections/*` category holds **no assets at all** (the registry's
      categories are 二维码 / 图文混排 / 图标 / 插图 / 整页PDF / 标记).
      Text-free extraction needs the `.ai` master; the shipped PDF is not
      enough. The three templates therefore carry `TODO(资产)` comments naming
      the source page and deliberately do **not** reference a non-existent
      asset key, which would hard-fail the build. Asset intake is a separate
      PR
  - Done when:
    - `python3 build.py check --config configs/config.bp-us.yaml --model
      JBP-2000B --region US` exits 0. Baseline moved twice: pre-intake
      2026-08-21 on the #940 tree, **FAILED with 30 issue(s)**, every one a
      `MISSING_REQUIRED_SPEC_ROW`; post-first-batch 2026-08-22,
      `validate_spec_master` **OK** and the failure moves to the `csv_page`
      layer (`symbols page has no matching rows`). Both halves of the intake
      have to land for this to exit 0
    - the CI ratchet is reversed: `tests/fixtures/phase2` is refreshed to
      carry the `JBP-2000B_US` document_key and
      [`../.github/ci_check_targets_skip_baseline.json`](../../.github/ci_check_targets_skip_baseline.json)
      returns to `skip_count: 4` with `configs/config.bp-us.yaml` removed
      from `skipped_configs`. Without this the BP target stays a permanent
      `SKIP` and a green local check proves nothing about the CI lane
  - Rollback: live-table rows are individually deletable (record_ids logged
    per row at write time); templates, contracts and recipes revert by git.

- [x] S5: Four-renderer acceptance — mechanical criteria harness
  - Status: `done` (merged 2026-08-22, #939, squash `0432e5b7`; 17/17 checks
    green on a refreshed base, same pre-merge staleness check as S3). Running
    the harness against the slice target is S6's first step, not S5's — S5
    delivers the harness. It is **not** "no new code": it ships
    `tools/renderer_acceptance.py` (added by #939) (608
    lines), `tests/test_renderer_acceptance.py`, and
    `code-as-doc/dev/renderer_acceptance_runbook.md` (added by #939).
    The harness is mergeable now; the acceptance **run** was subsequently
    executed during S6 after both S4 intake batches landed.
  - Gate: the harness merged on S1–S3; the S4 data prerequisite for the run is
    now satisfied.
  - Mechanical criteria (each one command + one exit code / grep):
    - check/unittest/ruff/guardrails all green
    - **PDF page count == 28 exactly** (`F(L) + L·B + K`, `K = 1`;
      `F(L) = 1 + 2·⌈L/3⌉`, so `F(3) = 3`). "Zero exceptions on 25 books" was
      too strong: the formula is pinned against **7** shipped books in
      `tests/test_renderer_acceptance.py`, and single-language books are a
      real exception — `F = 2`, because the JP house style folds the preface
      into the cover. Where the formula does not apply, pin the measured
      count with `--expect-pages N`. Also: uniform page size, and zero
      `Undefined control sequence` **and** zero `Missing $` in the xelatex log
    - HTML: check → md → html all exit 0; each language block has the new
      pages' `<section>`s; `grep 'hb-[a-z-]*-composition'` on the new
      target's HTML = **zero hits**. This is a positive requirement, not a
      tolerance: BP is outside `web_manual.json`'s `figure_targets` whitelist
      (`[{JE-1000F, US}]`), so `transform_web_fragment` returns the fragment
      byte-unchanged at `tools/web_presentation.py:1686-1687` and the target
      is *designed* to emit plain HTML. A hit means someone hand-expanded the
      whitelist. The overview branch is a **silent soft skip**, not an error —
      nothing raises, so the criterion has to be the grep, never "did it
      crash"
    - HTML: a manual stylesheet exists, and the criterion **reports which
      channel** produced it — Sphinx emits `hb_manual.css`, `web_publish`
      emits `web_manual.css`. Asserting a single name reds the other channel
      for no reason
    - Word: bundle builds green (reference doc binds at config level — no
      per-model work expected)
    - IDML: fallback export produces the `.idml`;
      `git diff data/layout_params.csv docs/renderers/contracts/reference_layout/`
      **empty** — the approved JE-1000F/US plan hashes the *entire* CSV, so
      one added row unpins it (#720's failure shape). Review discipline is not
      the control; the empty diff is
    - IDML degradation, widened after refutation — the blocker is **not** the
      overview geometry registry.
      `docs/renderers/contracts/reference_layout_registry.json` holds exactly
      one plan (JE-1000F/US), so `page_plan["plan_source"]` is not
      `approved-reference` for BP and `tools/export_idml.py:377` never reaches
      `add_product_overview_page`; the resolver at
      `tools/idml/page_overview.py:368` is never called and nothing raises.
      So the **overview page itself** degrades into the generic prose flow
      alongside every `rst_include` page (`connections`, safety, box contents,
      charging, storage, warranty) as `UNCLASSIFIED_PROSE`, and prose
      typesetting runs non-`dense`. Data pages (spec / LCD / troubleshooting)
      still emit normally, and there is no `installation` page to classify.
      All of this is the accepted slice degradation (an optional 2-line
      `page_roles.py` rule if the warning noise matters)
    - regression: host lines byte-identical across two worktrees at base and
      head (M-pre.4) on JE-1000F/US and JE-1000F/JP. The LaTeX component
      library and the layout-params table are global singletons, so the slice
      cannot claim success without this
  - **Do not "fix" the overview geometry registry** (after refutation,
    2026-08-21). `docs/renderers/contracts/overview_component_instances.json`
    does hold exactly one instance (`je1000f-us-v1` → JE-1000F/US) and
    `resolve_overview_instance` does raise `ComponentSpecError` on an
    unmatched model/region — but **neither renderer calls it for BP**, so
    adding a BP instance changes nothing observable. HTML's call site
    (`tools/web_presentation.py:273-277`) passes
    `instance_id="je1000f-us-v1"` from `web_manual.json:81`, and
    `overview_instance.py:303-307` ignores model/region whenever
    `instance_id` is set — that path can never raise on a target mismatch; it
    would apply JE-1000F geometry to any model. Standing up BP overview
    composition needs, **in this order**: (1) the two missing BP
    illustrations, (2) a `figure_targets` row in `web_manual.json` for HTML,
    (3) an approved reference-layout plan + registry row for IDML, and only
    then (4) a BP instance. Steps 2 and 3 are slice red lines. Were step 3
    reached today the first hard error would be `page_overview.py:362-363`
    ("requires one h1, two h2s, and two images"), because the BP template's
    images are still `TODO(资产)`.
  - Deliverable: a short pass/fail table per criterion, attached to the PR
    thread — no prose claims of "works". `tools/renderer_acceptance.py --json`
    emits it; exit 0 means every selected criterion passed.

- [x] S6: InDesign finishing + page-by-page reconciliation (operator round)
  - Status: `done` — S5 is green and its S4 data prerequisite is satisfied.
    #955 (`ad14f261`) landed the JBP shared-component candidate assembly,
    #959 (`646050aa`) recorded the pipeline-side reconciliation, and #971
    (`c1d75d62`) closed the portable-font final-assembly defects. Operator
    closeout was recorded 2026-08-30.
  - Gate: S5 green — satisfied.
  - Work: pipeline delivers the handoff zip (existing mechanism: relative
    Links, fonts opt-in); operator performs one real InDesign finishing pass;
    the finished book is reconciled page-by-page against the shipped
    `Jackery Battery Pack 2000 User Manual V2.0-2026-04-27.pdf` (28 pages).
  - **The reconciliation baseline is not zero** (measured while building S5's
    harness): `JE-1000F/US`'s *existing* pipeline PDF is **66 pages against a
    58-page shipped book** at the same trim (368.79×524.69pt). That 8-page
    divergence predates the slice and is out of S5's scope, but S6 must not
    assume the pipeline should equal the shipped book page for page.
  - Deliverable: reconciliation report in `code-as-doc/reviews/`, every
    difference classified **pipeline-gap / finishing-layer / data-gap /
    accepted-degradation** with counts. This report re-scopes the rollout.
  - Evidence already recorded:
    - [`reviews/jbp2000b_us_s6_reconciliation_2026-08.md`](../reviews/jbp2000b_us_s6_reconciliation_2026-08.md):
      pipeline mechanical acceptance is 11/11, with 28/28 physical pages,
      43/43 source bindings, `skipped_raw=0`, and 41/41 delivery links
    - [`reviews/jbp2000b_us_local_validation_2026-08.md`](../reviews/jbp2000b_us_local_validation_2026-08.md):
      InDesign 2026 `21.0.1.6` native finalize produced 28 pages with
      0 overset, 0 missing fonts, 0 missing glyphs and 0 bad links
    - the same validation record documents a 28-page source/native side-by-side
      review and a clean-room ZIP unpack/reopen pass; the unpacked package
      retained 41/41 links and reproduced all 28 rendered pages
  - Final reconciliation counts use distinct root-cause families, not repeated
    language/page instances: `pipeline-gap=0`, `finishing-layer=3` observed / 0
    open, `data-gap=0`, `accepted-degradation=2` observed / 0 open. The two
    accepted differences are the current source authority's `EN` versus the
    historical reference's `US` label and the current source-authority TOC
    order; neither is a missing-data or layout-pipeline defect.
  - Operator ruling (2026-08-30): close S6 with zero pipeline gaps and accept
    those two source-authority differences for this slice. This ruling does
    **not** approve reference-layout promotion: the target assembly remains
    `candidate` / `production_eligible=false` until the separate promotion
    gate is approved.
  - Slice exit: satisfied — report delivered, counts recorded, and operator
    ruling recorded.
