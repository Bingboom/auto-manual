# Template Family Migration Plan

Updated: 2026-04-17

This file is the active execution plan for simplifying the current manual template matrix.
It is the implementation plan for the next migration wave.
It is not the long-term architecture document and it is not the general repo roadmap.

Use these files for the adjacent topics:

- [`architecture/System Evolution Strategy.md`](architecture/System%20Evolution%20Strategy.md)
- [`manual_family_guide.md`](manual_family_guide.md)
- [`../optimization_project.md`](../optimization_project.md)

## 1. Goal

Target direction:

- keep only the source-language template families that truly own prose structure
- move market differences out of duplicated page folders and into explicit market profiles, snippets, and unit/compliance rules
- let derived languages come from translation assets backed by Translation Memory and terminology, not from manually mirrored full-page template trees

Practical target for this repo:

- keep `en`, `ja`, and `zh` as source-language template owners
- treat `fr`, `es`, and future `de`, `it`, and similar locales as derived languages
- preserve deterministic builds by freezing translated assets into repo/snapshot inputs before build and publish

Non-goal for the first wave:

- do not attempt a one-shot cutover from all current `page_<market>-<lang>` folders to only `page_en`, `page_ja`, and `page_zh`
- do not replace the current build/review/publish entrypoints
- do not require live TM lookups during `build.py publish`

## 2. Current Baseline

The current repo already has part of the needed foundation:

- structured spec content already distinguishes `Source_lang` and source text columns in `Spec_Master`
- current US merged behavior already documents fallback from non-source CSV fields to source-language text
- Translation Memory and terminology assets already exist and can support derived-language generation

The current blockers are in the template assembly layer:

- prose templates are still stored as market-plus-language trees such as:
  - [`../docs/templates/page_us-en/`](../docs/templates/page_us-en)
  - [`../docs/templates/page_us-fr/`](../docs/templates/page_us-fr)
  - [`../docs/templates/page_us-es/`](../docs/templates/page_us-es)
  - [`../docs/templates/page_eu-en/`](../docs/templates/page_eu-en)
  - [`../docs/templates/page_jp/`](../docs/templates/page_jp)
  - [`../docs/templates/page_zh/`](../docs/templates/page_zh)
- manifests bind directly to those concrete folders, for example:
  - [`../docs/manifests/manual_us.yaml`](../docs/manifests/manual_us.yaml)
  - [`../docs/manifests/manual_eu-en.yaml`](../docs/manifests/manual_eu-en.yaml)
- manifest resolution currently selects one file path but does not support profile composition or layered template lookup:
  - [`../tools/page_manifest.py`](../tools/page_manifest.py)

Interpretation:

- the repo is ready for a staged migration
- the repo is not ready for a big-bang collapse

## 3. Migration Principles

Keep these rules fixed during the migration:

1. Source-language prose owns structure.
   - headings
   - section order
   - placeholders
   - include graph
   - model gates such as `.. only::`

2. Derived languages own wording, not structure.
   - translated prose should be generated or refreshed from source prose plus translation assets
   - derived languages should not keep independent full-page RST structure unless a proven exception exists

3. Market differences must be explicit.
   - compliance blocks such as `FCC`
   - unit style such as `dual` vs `metric`
   - market-only warnings, warranty text, symbol inventory, and app instructions

4. Builds must stay reproducible.
   - TM and terminology may help create or refresh translation assets
   - publish builds must consume frozen repo or snapshot inputs, not live translation calls

5. No family-wide delete before parity.
   - do not remove an old template folder until the replacement path passes check/build parity for the target family

## 4. Target Model

Target content model after the migration wave:

- source template directories:
  - `docs/templates/page_en/`
  - `docs/templates/page_ja/`
  - `docs/templates/page_zh/`
- market profile layer:
  - `docs/templates/profiles/us.yaml`
  - `docs/templates/profiles/eu.yaml`
  - `docs/templates/profiles/jp.yaml`
  - `docs/templates/profiles/cn.yaml`
- market snippets and inserts:
  - `docs/templates/snippets/market/us/...`
  - `docs/templates/snippets/market/eu/...`
  - `docs/templates/snippets/market/shared/...`
- derived-language translation assets:
  - repo-owned prose asset files or structured tables generated from source prose and TM
  - fallback to source prose when a derived translation is intentionally missing

Expected runtime meaning:

- template structure comes from source language
- market profile decides what blocks appear and how values are formatted
- derived language selection chooses translated prose assets and translated structured fields

## 5. Phase Table

| Phase | Objective | Primary scope | Main deliverables | Validation | Exit rule |
|------|-----------|---------------|-------------------|------------|-----------|
| 0 | Freeze the migration contract | inventory and rules only | page inventory, family-difference map, first profile schema, risk register | `python3 -m unittest` | we can classify every active page as source-owned, market-owned, or derived-only |
| 1 | Add composition support without moving content | manifest and resolver layer | manifest/profile composition design, loader hooks, compatibility tests | `python3 -m unittest` and `python3 build.py check --config configs/config.us.yaml --model JE-1000F --region US` | old manifests still build unchanged while new composition paths can be introduced behind flags |
| 2 | Remove derived-language page duplication inside US | US `en/fr/es` family | one US source-structure owner, derived prose asset format, US FR/ES built from shared structure | `python3 -m unittest` and `python3 build.py check --config configs/config.us.yaml --model JE-1000F --region US` and `python3 build.py diff-report --config configs/config.us.yaml --model JE-1000F --region US` | `page_us-fr` and `page_us-es` are no longer structure owners |
| 3 | Extract market-specific English deltas | US vs EU English | profile flags, unit formatter, compliance snippets, page-level include switches | `python3 -m unittest` and `python3 build.py check --config configs/config.eu-en.yaml --model JE-2000E --region US` and US check | FCC, unit style, and market-only prose no longer require separate full-page English folders |
| 4 | Merge US/EU English structure into shared English source templates | `page_us-en` and `page_eu-en` | `page_en` source templates plus `us` and `eu` profile wiring | same checks as Phase 3 plus review-preview smoke if affected | `page_us-en` and `page_eu-en` become compatibility wrappers or are fully retired |
| 5 | Generalize for future EU derived languages | EU family expansion | `fr/de/it/...` derived flow from English source plus EU profile | `python3 -m unittest` plus EU target checks for all enabled languages | future EU languages do not require new full-page template trees |
| 6 | Re-evaluate JP and ZH after EN family is stable | JP and CN source families | keep, simplify, or partially profile-ize JP/ZH based on evidence | `python3 -m unittest`, `python3 build.py check --config configs/config.ja.yaml --model JE-1000F --region JP`, `python3 build.py check --config configs/config.zh.yaml --model JE-2000E --region CN` when applicable | JP/ZH are either intentionally retained as source families or migrated by explicit follow-up decision |

## 6. Detailed Work By Phase

## Phase 0: Contract Freeze

Scope:

- document the current page inventory and classify every page
- decide what is:
  - structure-owned by source language
  - market-owned
  - model-owned
  - derived-language wording only

Target files:

- [`../docs/templates/page_us-en/`](../docs/templates/page_us-en)
- [`../docs/templates/page_us-fr/`](../docs/templates/page_us-fr)
- [`../docs/templates/page_us-es/`](../docs/templates/page_us-es)
- [`../docs/templates/page_eu-en/`](../docs/templates/page_eu-en)
- [`../docs/templates/page_jp/`](../docs/templates/page_jp)
- [`../docs/templates/page_zh/`](../docs/templates/page_zh)
- [`manual_family_guide.md`](manual_family_guide.md)

Tasks:

1. Build a page-level matrix:
   - `source structure owner`
   - `derived translation only`
   - `market-specific prose`
   - `spec/generated`
   - `needs model gate`
2. List required first-wave market flags:
   - `unit_style`
   - `include_fcc`
   - `symbols_variant`
   - `warranty_variant`
   - `safety_variant`
3. Mark pages that must not be merged yet.

Exit rule:

- every active page is classified
- first-wave profile keys are frozen for implementation

## Phase 1: Composition Support

Scope:

- add the minimum infrastructure required to express:
  - source template
  - market profile
  - derived language asset selection

Target files:

- [`../tools/page_manifest.py`](../tools/page_manifest.py)
- [`../tools/config_pages.py`](../tools/config_pages.py)
- [`../tools/build_docs_pages.py`](../tools/build_docs_pages.py)
- [`../tools/word_bundle_common.py`](../tools/word_bundle_common.py)
- [`../tools/check_docs.py`](../tools/check_docs.py)
- [`../tests/`](../tests)

Tasks:

1. Introduce a manifest vocabulary for layered composition.
   - source template path
   - optional profile
   - optional translation asset reference
2. Keep old manifest entries valid.
3. Add compatibility tests proving current manifests still resolve unchanged.
4. Add one experimental manifest path for a new composed page without cutting over current builds.

Exit rule:

- the loader can express layered pages while old paths still work

## Phase 2: US Derived-Language Deduplication

Scope:

- first real content migration
- US only
- keep market fixed, remove derived-language structure copies

Target files:

- [`../docs/manifests/manual_us.yaml`](../docs/manifests/manual_us.yaml)
- [`../docs/manifests/manual_us-single-en.yaml`](../docs/manifests/manual_us-single-en.yaml)
- [`../docs/manifests/manual_us-single-fr.yaml`](../docs/manifests/manual_us-single-fr.yaml)
- [`../docs/manifests/manual_us-single-es.yaml`](../docs/manifests/manual_us-single-es.yaml)
- [`../docs/templates/page_us-en/`](../docs/templates/page_us-en)
- [`../docs/templates/page_us-fr/`](../docs/templates/page_us-fr)
- [`../docs/templates/page_us-es/`](../docs/templates/page_us-es)
- new translation asset location to be introduced in this phase

Tasks:

1. Declare US English as the structure owner for US derived languages.
2. Create a derived prose asset format for FR and ES.
3. Migrate the lowest-risk pages first:
   - `02_whats_in_the_box`
   - `06_ups_mode`
   - `08_charging_methods`
   - `09_storage_and_maintenance`
   - `10_troubleshooting`
   - `11_warranty`
4. Migrate higher-risk pages after the flow is stable:
   - `safety`
   - `charging`
   - `12_app_setup`
5. Leave generated/spec-driven pages using the current structured data path where possible.

Recommended sequencing inside Phase 2:

- PR 1: asset format plus one low-risk page
- PR 2: remaining low-risk pages
- PR 3: safety, charging, app setup
- PR 4: retire `page_us-fr` and `page_us-es` as structure owners

Exit rule:

- US FR and ES are built from one shared US source structure
- any remaining FR/ES-specific files are wording assets only

## Phase 3: Extract Market-Specific English Deltas

Scope:

- remove English market divergence caused by compliance and formatting rules
- do not merge folders yet until the extracted deltas are stable

Target files:

- [`../docs/templates/page_us-en/`](../docs/templates/page_us-en)
- [`../docs/templates/page_eu-en/`](../docs/templates/page_eu-en)
- new `docs/templates/profiles/`
- new `docs/templates/snippets/market/`
- unit formatting helpers under `tools/` if needed

Tasks:

1. Extract compliance inserts:
   - `FCC`
   - EU-only or non-US compliance prose
2. Extract unit formatting behavior:
   - `dual`
   - `metric`
3. Extract market-only legal and warning prose into snippets.
4. Replace page-level hardcoded market prose with profile-gated inserts.
5. Keep product- or model-specific content separate from market profile logic.

Important rule:

- do not use one giant page with dozens of inline conditionals
- prefer snippet insertion plus small profile switches

Exit rule:

- the meaningful US/EU English differences are represented as explicit profile data or snippets

## Phase 4: Shared English Source Templates

Scope:

- create the first real `page_en` source directory
- wire US and EU manifests to the same structure owner with different profiles

Target files:

- new `docs/templates/page_en/`
- [`../docs/manifests/manual_us.yaml`](../docs/manifests/manual_us.yaml)
- [`../docs/manifests/manual_eu-en.yaml`](../docs/manifests/manual_eu-en.yaml)
- compatibility wrappers in old folders if needed during cutover

Tasks:

1. Move one page at a time from `page_us-en` and `page_eu-en` into `page_en`.
2. Start with pages already stabilized in Phase 3.
3. Keep old paths as wrappers or aliases until parity is proven.
4. Only after successful parity, retire direct ownership of:
   - `page_us-en`
   - `page_eu-en`

Exit rule:

- US and EU English both build from `page_en` plus market profile inputs

## Phase 5: EU Derived Languages

Scope:

- unlock future EU multi-language output without adding new full-page folders per language

Tasks:

1. Reuse `page_en` as the EU source structure owner.
2. Add derived prose assets for:
   - `fr`
   - `de`
   - `it`
   - other planned EU locales
3. Keep EU market profile stable across all derived EU languages.
4. Validate text expansion and density impacts separately from structure ownership.

Exit rule:

- future EU language onboarding means adding translation assets, not adding page trees

## Phase 6: JP And ZH Re-evaluation

Scope:

- decide whether JP and ZH should stay as independent source families or partially adopt the same profiling approach

Working assumption:

- JP and ZH remain valid source families unless real evidence shows they should be collapsed further

Tasks:

1. Re-check whether JP and ZH differ mainly by source language or also by family-specific content contracts.
2. Keep them independent if they still own distinct prose structure.
3. Only profile-ize shared pieces when the win is clear and low-risk.

Exit rule:

- JP and ZH have an explicit decision record instead of being implicitly dragged into the EN migration

## 7. Recommended PR Breakdown

Use this PR sequence unless the repo context changes materially:

1. PR A: page inventory, profile schema, migration tests scaffolding
2. PR B: manifest composition support with backward compatibility
3. PR C: US low-risk derived-page migration
4. PR D: US high-risk derived-page migration and FR/ES structure retirement
5. PR E: market snippet and unit-profile extraction for EN pages
6. PR F: first shared `page_en` cutover for one or two pages
7. PR G: full US/EU English cutover
8. PR H: EU derived-language onboarding flow

Preferred PR size rule:

- one PR should move one migration concern, not one entire family rewrite

## 8. Validation Matrix

Run these commands at the relevant phases:

- logic and loader changes:
  - `python3 -m unittest`
- US migration checks:
  - `python3 build.py check --config configs/config.us.yaml --model JE-1000F --region US`
  - `python3 build.py diff-report --config configs/config.us.yaml --model JE-1000F --region US`
- EU migration checks:
  - `python3 build.py check --config configs/config.eu-en.yaml --model JE-2000E --region US`
- JP stability checks when shared loader logic changes:
  - `python3 build.py check --config configs/config.ja.yaml --model JE-1000F --region JP`
- release traceability checks when publish paths are affected:
  - `python3 build.py release-manifest --config configs/config.ja.yaml --model JE-1000F --region JP`

Extra parity rule for every cutover PR:

- compare generated RST and Word outputs before deleting the previous owner path

## 9. Cutover And Rollback Rules

Cutover rule:

- keep the old page path as a compatibility wrapper until the replacement path passes the target family checks

Rollback rule:

- if one phase breaks family parity, restore the previous manifest ownership and keep the new path behind a non-default config or local experiment manifest

Do not do this:

- do not delete old family folders in the same PR that introduces the first new composed path
- do not mix TM pipeline redesign, market-profile extraction, and EN/JP/ZH convergence into one branch-sized change

## 10. Immediate First Coding Slice

Recommended first slice after this planning branch:

1. Add a page inventory table for all active page folders and classify each page.
2. Add the first profile schema draft for:
   - `unit_style`
   - `include_fcc`
   - `symbols_variant`
   - `warranty_variant`
   - `safety_variant`
3. Add manifest-composition tests without changing current output behavior.
4. Choose one low-risk US page and prove FR/ES can consume shared source structure.

If this first slice succeeds, continue with US-only deduplication before touching US vs EU English convergence.
