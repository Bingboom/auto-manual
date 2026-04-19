# Business Logic Overview

Updated: 2026-04-19

This file is the current business-logic overview for `auto-manual`.
It explains the repo's maintained business flow in plain language, with the current codebase and maintainer workflow as the source of truth.

Use this file when you need to answer questions such as:

- what the repo is actually trying to do end to end
- which business objects matter most
- what changes after a document enters review
- what `Start Review`, `Build Draft Package`, and `Publish` mean today
- which rules must stay stable when refactoring code

This file is not:

- the full command reference
- the long-term architecture strategy
- the field-by-field CSV filling guide

Use these docs together with this one:

- [`build_doc_guide.md`](build_doc_guide.md): command semantics and output layout
- [`../user-guide/hello_auto-doc.md`](../user-guide/hello_auto-doc.md): workflow and editing surfaces
- [`spec_master_user_guide.md`](spec_master_user_guide.md): structured data semantics
- [`architecture/System Evolution Strategy.md`](architecture/System%20Evolution%20Strategy.md): long-term direction

## 1. Business Goal

The repository turns structured product content into target-specific manuals, then manages the full review-first release loop around those manuals.

The current business goal is not only "generate documents".
The maintained goal is:

1. read structured product content from the current snapshot layer
2. generate a target-specific manual draft from templates plus data
3. move that draft into a durable review layer
4. let humans edit the review layer as the formal review source
5. rebuild draft or publish outputs from that review source without losing traceability
6. write build status and artifact links back to the queue system

## 2. Core Business Objects

### 2.1 Target

A target manual is identified by `model + region + lang`.

Examples:

- `JE-1000F + US + en`
- `JE-1000F + JP + ja`

This is the base unit for draft generation, review bundles, runtime bundles, validation, diff reports, and release manifests.

### 2.2 Build Family

`Build_family` is the business routing key used by queue automation.
It decides which config family and page stack should be used.

Examples:

- `us-merged`
- `us-en`
- `us-es`
- `us-fr`
- `eu-en`
- `jp-ja`
- `cn-zh`

Current rule:

- queue routing is `Build_family`-first
- `Lang` is now a compatibility hint, not the primary routing key

### 2.3 Structured Snapshot

The current default structured-content source is `data/phase2/`.
It is the local materialized snapshot refreshed from Feishu/Lark Base.

Current meaning:

- Feishu/Lark Base remains the upstream business source
- `data/phase2/*.csv` is the local build-time snapshot
- build, review, check, diff-report, release-manifest, and publish default to `data/phase2` when it is valid
- explicit `--data-root` can still override the source

### 2.4 Template Seed Layer

The template seed layer is composed of:

- [`../docs/templates/`](../docs/templates)
- [`../docs/manifests/`](../docs/manifests)

It owns:

- shared page structure
- shared headings and section order
- stable prose skeletons
- generated-page wrappers and recipes

This layer creates the first draft before review starts.

### 2.5 Review Bundle

The review bundle lives under [`../docs/_review/`](../docs/_review).

It is the formal target-specific editing surface after review starts.
Once a target has entered review, this is the business source that should be treated as authoritative for reviewed content.

### 2.6 Runtime Bundle

The runtime bundle lives under [`../docs/_build/`](../docs/_build).

It is the generated working bundle consumed by `html`, `word`, and `pdf`.
It is not the long-lived authoring surface.

### 2.7 Queue Records

The current queue system has two business surfaces:

- `review_init`: move a document into review
- `Document_link`: rebuild draft packages or publish reviewed documents

These queues are not just technical triggers.
They define the operational business state transitions of the manual lifecycle.

## 3. Source Of Truth By Stage

The source of truth changes by stage.
This is one of the most important business rules in the repo.

### 3.1 Before Review Starts

Before review starts, the source of truth is:

- template seed layer
- structured snapshot layer

In plain language:

- structure comes from templates/manifests
- product-specific values come from the current snapshot
- runtime draft output is generated from those two inputs

### 3.2 After Review Starts

After review starts, the source of truth becomes:

- reviewed prose and reviewed page content in [`../docs/_review/`](../docs/_review)
- current structured snapshot values for the data-driven parts that still need refresh

In plain language:

- the human-reviewed manual text must live in `_review`
- `_build` stays generated
- snapshot changes may still refresh parameter-driven values, but should not wipe reviewed prose

### 3.3 What Is Never The Long-Lived Editing Surface

The following should not be treated as the durable authoring source:

- [`../docs/_build/`](../docs/_build)
- generated export outputs under `html`, `word`, and `pdf`

## 4. End-To-End Business Lifecycle

### 4.1 Sync Structured Data

`sync-data` refreshes the local `phase2` snapshot from Feishu/Lark Base.

Business meaning:

- update the local structured content used by later build/review/publish steps
- normalize external source data into repo-stable CSV form
- keep queue and local builds using the same snapshot semantics

Current important rules:

- this step is explicit in local workflows
- build commands do not silently fetch online data on their own
- invalid upstream data is preserved in the snapshot so validation can fail loudly

### 4.2 Generate Runtime Draft

`rst` builds the target runtime bundle from templates plus structured data.

Business meaning:

- materialize one target manual draft
- expand CSV pages, generated pages, placeholder-backed template pages, and assets into one bundle

Result:

- one generated bundle under `docs/_build/<model>/<region>/<lang>/rst/`

### 4.3 Start Review

`review` or the review-start queue moves a manual into review.

Current maintained meaning of `Start Review`:

- use the latest `main` template/data state
- create or refresh the review branch
- seed `docs/_review` for the target
- create or reuse the pull request

Important current rule:

- `Start Review` now means force restart and reseed from the latest template/data state
- existing review content on `main` is not used as a duplicate guard
- for merged families such as `JE-1000F_US`, `Start Review` seeds one shared family review bundle under `docs/_review/<model>/<region>/`
- the languages contained by that shared family review bundle come from the family config, for example `config.us.yaml build.languages`, not from separate per-language review-init tasks

### 4.4 Review Editing

After review starts, daily manual edits should happen in `_review`.

Business meaning:

- human wording changes
- target-specific fixes
- review corrections that must survive future rebuilds

The repo intentionally separates this from `_build` so regenerated runtime bundles do not erase reviewed text.

### 4.5 Refresh Data-Driven Parts During Review

`sync-review` exists for the case where structured data changes after review has already started.

Current maintained meaning:

- refresh only the data-driven parts of the review bundle
- preserve the rest of the human-reviewed prose

This rule is business-critical.
If this behavior regresses, data refreshes will overwrite review work.

Current detailed rules:

- `review --refresh-review` means whole-bundle replacement from runtime
- `sync-review` means safe review refresh
- `sync-review --page-file <file>` means explicit page replacement
- `sync-review --sync-scope params` refreshes parameter-driven lines without replacing the whole review page
- `generated_page` wrapper pages under `page/*.rst` are part of that parameter-refresh logic, not a special ignore case
- when a single-language target reuses a family-level shared review bundle, `sync-review` must map page files by language-aware manifest identity, not by naive same-name copy
- this matters for merged manuals where the shared review bundle may contain sibling files such as `01_fcc.rst`, `p20_01_fcc.rst`, and `p35_01_fcc.rst` while the single-language runtime bundle still uses `01_fcc.rst`
- in that case the system must refresh the matching language page inside the shared review bundle and must not overwrite the English sibling page

### 4.6 Build Draft Package

`Build Draft Package` is the review-stage rebuild path.

Current maintained meaning:

- rebuild review-stage artifacts from the selected review branch
- keep the current `main` toolchain and workflow code
- overlay only `docs/_review` from `Git_ref`
- if the authoritative review content for a target lives in a shared family review bundle, the rebuild must resolve the correct language pages from that shared bundle instead of falling back to same-name English pages

This rule matters:

- `Git_ref` is a review-content source, not an alternate whole-repo toolchain source

In plain language:

- build with today's tools
- render yesterday's or today's review content from the chosen review branch

### 4.7 Publish

`Publish` is the formal release build path.

Current maintained meaning:

- use reviewed content as the release source
- produce release-facing artifacts and traceability outputs
- write release results back to the queue surface

Direct `build.py publish` currently means:

1. run `check`
2. run `diff-report`
3. build `word`
4. build `pdf`
5. write `release-manifest`

This is not an arbitrary command chain.
It is the current business definition of a formal publish.

### 4.8 Report And Traceability

The repo treats reporting as part of the business flow, not as optional tooling.

Current business outputs:

- `diff-report`: what changed in reviewed content
- `release-manifest`: what was released, from which target, with which outputs
- versioned release directories under [`../reports/releases/`](../reports/releases)

## 5. Queue Business Logic

### 5.1 Queue Actions

The current queue action field is `Workflow_action`.

Supported business actions:

- `Start Review`
- `Build Draft Package`
- `Publish`

Current rule:

- `Doc_phase` is no longer the routing field
- queue automation should decide from `Workflow_action`

### 5.2 Queue Routing

Queue routing is based on `Build_family` first.

Current rule:

- use `Build_family` to select the config family
- only fall back to `Lang` when the family is not explicit enough

### 5.3 Queue Grouping

Some build families are treated as one grouped business document.

Current rule:

- only merged whole-book families should use `build.queue_by_document_key`
- single-language families should continue to run one queue row per record

Business meaning:

- a merged family represents one shared manual across languages
- a single-language family represents one language-specific manual job
- for review-stage US manuals, `JE-1000F_US` is the family document key and its included languages are defined by `config.us.yaml`, so downstream ES/FR builds are contained by that family review scope rather than starting separate family review bundles

### 5.4 Forced Snapshot Refresh

`是否强制刷新数据` is a queue-level business switch.

Current meaning:

- checked: refresh `phase2` immediately before the queued build
- unchecked: use the current local snapshot as-is

This is important because queue behavior is no longer "always sync first".

### 5.5 Writeback Semantics

The queue does not only build files.
It also maintains business state.

Current writeback responsibilities include:

- build started timestamp
- build result summary
- data refresh result
- local release directory path
- primary artifact link
- optional DingTalk mirror link
- trigger reset / completion state

## 6. External System Boundaries

### 6.1 Feishu/Lark

Feishu/Lark is still the primary upstream system for:

- structured source tables
- queue control tables
- status writeback
- primary artifact link writeback

### 6.2 DingTalk

DingTalk is currently an optional artifact mirror target.

Current maintained rule:

- Feishu remains the primary control plane
- DingTalk is supplemental
- `Document link` remains the canonical returned artifact link
- `Document link_dd` is optional mirror writeback only

### 6.3 OpenClaw And Message Control

OpenClaw is currently an operator layer on top of the queue system.

Its business role is:

- resolve natural-language operator requests
- map them to bounded queue actions
- dispatch the existing GitHub/queue workers
- report status and failure causes back in a controlled form

It does not redefine the core build business logic.
It operates the same build/review/publish system.

## 7. Must-Maintain Business Invariants

The following rules are the highest-priority maintenance targets.
Any refactor that changes them should be treated as a business-logic change, not a harmless implementation cleanup.

### 7.1 Source-Of-Truth Invariants

- before review: templates plus snapshot drive the draft
- after review: `_review` is the durable reviewed source
- `_build` is generated output, not the durable editing surface

### 7.2 Review Invariants

- `review --refresh-review` replaces review content intentionally
- `sync-review` preserves reviewed prose while refreshing data-driven parts
- parameter refresh must continue to cover placeholder-backed generated-page wrappers
- merged family review bundles must remain authoritative for the languages declared by the family config
- when single-language build or sync flows consume a shared family review bundle, page selection must stay language-aware and manifest-aware rather than name-only

### 7.3 Queue Invariants

- `Workflow_action` is the action router
- `Build_family` is the primary config router
- `Git_ref` means review-content branch, not toolchain branch
- queue Draft/Publish builds keep the latest `main` toolchain

### 7.4 Publish Invariants

- `publish` is a formal release path, not just "export pdf"
- `check`, `diff-report`, `word`, `pdf`, and `release-manifest` belong to the publish chain

### 7.5 Platform Invariants

- Feishu is the canonical queue and writeback surface
- DingTalk remains optional mirror output
- natural-language control layers must stay bounded to the same queue semantics

## 8. What Counts As A Business Logic Change

Treat a change as business logic when it changes any of the following:

- which layer is the source of truth at a given stage
- what `Start Review`, `Build Draft Package`, or `Publish` means
- how queue rows are routed or grouped
- when snapshot refresh is required or skipped
- how `Git_ref` is interpreted
- whether review sync preserves or replaces reviewed content
- which output is considered the primary release artifact
- which external system is authoritative for queue state or writeback

If a change falls into one of those categories, update this file in the same change.

## 9. Owning Docs By Topic

- business logic overview: this file
- command semantics: [`build_doc_guide.md`](build_doc_guide.md)
- workflow and editing surfaces: [`../user-guide/hello_auto-doc.md`](../user-guide/hello_auto-doc.md)
- structured data semantics: [`spec_master_user_guide.md`](spec_master_user_guide.md)
- generated-page authoring and review sync details: [`generated_page_authoring.md`](generated_page_authoring.md)
- component ownership and current module boundaries: [`architecture/Hello_Docs_Architecture.md`](architecture/Hello_Docs_Architecture.md)
