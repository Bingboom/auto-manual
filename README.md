# Auto-Manual Tool

Auto-Manual turns structured content — Feishu/Lark Base source tables plus
shared RST templates — into target-specific manual bundles and release
outputs (PDF, DOCX, IDML, Markdown, responsive web) across the config
families registered under [`configs/`](configs) — US, EU, JP, CN, AU, KR,
and pt-BR. The maintained smoke-check baseline is `JE-1000F` across US and
JP.

**This README is a quickstart and a navigation map, nothing more.** The full
command reference and every operational note live in
[`code-as-doc/build_doc_guide.md`](code-as-doc/build_doc_guide.md).

## 1. Recurring terms

Six internal terms the rest of the documentation uses without ceremony:

- **phase2** — the second-stage structured-data plane. The Feishu phase2
  source tables are the authoring source of truth; `sync-data` materializes
  them into the gitignored local snapshot `data/phase2/`, which is the
  default build/review/publish input (`--data-root` still overrides it). CI
  and tests use the frozen sample copy in
  [`tests/fixtures/phase2/`](tests/fixtures/phase2).
- **F6** — the operator-gated approval step for writes to the production
  Feishu source tables. Tools and agents only propose change requests and
  dry-runs; the operator personally executes the approved write, and every
  write is followed by a read-back of the same record.
- **build queue** — the Feishu build table that drives remote Draft /
  Publish: an operator arms a row, the queue worker consumes it, builds, and
  writes the result back to that row. Queue semantics live in
  [`build_doc_guide.md`](code-as-doc/build_doc_guide.md).
- **Manual IR** — `manual.ir.json`, the normalized content tree projected
  from the prepared bundle (templates + data). Production IDML renders from
  this frozen representation; the LaTeX PDF renders from the same prepared
  bundle (same source), with `latex_page_plan.json` retained as a trace.
- **fail-closed** — the default gate semantics here: when a validation,
  hash, or contract check fails, the build stops. Nothing silently falls
  back to an older or fuzzier value.
- **two planes / two Bases** — auto-manual is the engineering plane bound to
  the engineering Feishu Base; the
  [`Bingboom/Hello-Docs`](https://github.com/Bingboom/Hello-Docs) mirror is
  the business plane with its own Base bindings (`main` syncs one-way via
  [`sync-hello-docs.yml`](.github/workflows/sync-hello-docs.yml)). Read
  [`user-guide/two_plane_map.md`](user-guide/two_plane_map.md) before
  reasoning about which repo or Base an operation touches.

## 2. Where to start

- **New maintainer** → [`ONBOARDING.md`](ONBOARDING.md): two-plane topology,
  what-runs-where, and the golden-path drill that certifies a hand-over.
- **Daily operation** →
  [`user-guide/hello_auto-doc.md`](user-guide/hello_auto-doc.md) (workflow
  and source-of-truth rules) and
  [`user-guide/quick_start_guide.md`](user-guide/quick_start_guide.md)
  (happy-path example).
- **AI agent windows (Claude Code / Codex)** → [`CLAUDE.md`](CLAUDE.md)
  auto-loads the shared rules in [`AGENTS.md`](AGENTS.md); Codex reads
  `AGENTS.md` directly. Start every task with
  `scripts/start_branch.ps1 <type>/<area>-<topic>` (macOS/Linux:
  `./scripts/start_branch.sh`); multi-window rules are in `AGENTS.md` §8.
- **Command semantics** →
  [`code-as-doc/build_doc_guide.md`](code-as-doc/build_doc_guide.md).
- **Long-term direction** →
  [`code-as-doc/architecture/System Evolution Strategy.md`](code-as-doc/architecture/System%20Evolution%20Strategy.md)
  — platform strategy is defined there, not in this repo's working docs.

## 3. Quickstart

The primary entrypoint is [`build.py`](build.py). Minimal US/EN smoke check
(`config.us-en.yaml` is the single-language US config that CI also uses;
`config.us.yaml` is the merged en/fr/es US family):

```bash
python build.py doctor --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py check  --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py review --config configs/config.us-en.yaml --model JE-1000F --region US
```

Add `--data-plane` to `doctor` to fail early on an incomplete phase2
snapshot or missing target rows.

The one authoring rule to carry into day one: in page RST, reference an
approved image export from the asset registry by semantic identity instead
of a renderer path:

```rst
.. image:: asset:operation/ac_output
```

That is the whole first hour. Everything else is topic-shaped — jump
straight to the owning section of
[`build_doc_guide.md`](code-as-doc/build_doc_guide.md):

| Topic | Entry points |
| --- | --- |
| CI sweep over every config target; fixture snapshot refresh | `tools/ci_check_targets.py`, `tools/data_snapshot.py fixture-refresh` |
| Asset control plane: approved exports, intake, promotion, quarantine | `build.py asset-check`, `build.py asset-intake` |
| New model / region / line scaffolding | `build.py new-line` (dry-run by default); skill [`new-region-line`](.agents/skills/new-region-line/SKILL.md) |
| Editable InDesign handoff and production IDML export | `build.py idml`; publish handoffs are portable ZIPs with relinked `Links/` |
| Approved-PDF native replica (“方案 2”); a target without an approved reference layout contract falls back to the measured-LaTeX page plan | reference layout contracts, `tools/reference_layout_rebind.py`, `tools/indesign_finalize.py`, [`STYLE_DEFINITION.md`](docs/renderers/contracts/STYLE_DEFINITION.md) |
| Content QC over the current snapshot | `tools/content_lint.py` |
| Cloud-doc backport (reviewer edits → repo) | `tools/cloud_doc_backport.py run-review-branch` — the blessed path for in-review docs |
| Structured spec / manual-table intake | `tools/source_intake.py run / approve / apply / verify` |
| Queue-driven Draft / Publish; release verification and tags | `build.py process-build-queue`, `build.py release-rebuild-verify`, `tools/release_tag.py` |
| Manifest inventory and family-manifest fold | `tools/manifest_lint.py`, `tools/manifest_family.py` |
| Fixed US + JP release matrix | `scripts/build_us_jp_manuals.py` (pass `--languages` for a subset) |

Two navigation notes worth keeping in view:

- Replica acceptance is page-by-page visual parity against the approved
  reference PDF — do not hand off the IDML/INDD/PDF until the latest parity
  report says `accepted=true`. Workflow, thresholds, and maintainer commands:
  [the replica section of `build_doc_guide.md`](code-as-doc/build_doc_guide.md#approved-pdf-native-indesign-replica-option-2)
  and the
  [approved-replica plan](code-as-doc/dev/idml_reference_replica_plan.md).
- Build requests arriving through OpenClaw (the Feishu-side dispatch agent)
  or Feishu IM go through the adapter's `queue-resolve-action` →
  `queue-execute` and are consumed by the remote queue worker, which syncs
  its own fresh snapshot. A local `check` against `data/phase2/*.csv` is
  therefore not a valid preflight. Details:
  [`integrations/openclaw/feishu-im-webhook-adapter/README.md`](integrations/openclaw/feishu-im-webhook-adapter/README.md).

## 4. Editing surfaces

Use different surfaces for different stages:

- **Shared templates**: [`docs/templates/`](docs/templates) — reusable RST
  pages, placeholder contracts, snippets, and recipes.
- **Structured data**: the Feishu phase2 source tables are the authoring
  surface; `data/phase2/` is only their gitignored local snapshot. Per-file
  column semantics (`Spec_Master`, `Manual_Copy_Source`, `symbols_blocks`,
  `troubleshooting_blocks`, …) are maintained in the Source of Truth
  section (§2) of
  [`user-guide/hello_auto-doc.md`](user-guide/hello_auto-doc.md).
  Production source-table writes go through F6.
- **Target-specific review edits** (once review starts):
  [`docs/_review/`](docs/_review); review overrides stay under
  `overrides/_assets/`, `overrides/_static/`, or `overrides/renderers/`.
- **Generated output only**: [`docs/_build/`](docs/_build) — never a
  long-lived editing surface.

Three rules, one per stage: before review starts, seed the draft from
templates and data; after review starts, edit `_review`; never treat
`_build` as source.

The responsive web output (published to Read the Docs) is a
presentation-only projection of reviewed content through the independent
`Web Publish` action; ordinary CLI/queue builds keep the default `document`
(print) profile, so IDML, DOCX, PDF, and formal Markdown do not change. See
[`code-as-doc/dev/web_publish_pipeline.md`](code-as-doc/dev/web_publish_pipeline.md).

## 5. Document map

Use the document that owns the topic:

- maintainer doc index and ownership map: [`code-as-doc/README.md`](code-as-doc/README.md)
- current business logic overview and invariants: [`code-as-doc/business_logic_overview.md`](code-as-doc/business_logic_overview.md)
- current maintainer command reference: [`code-as-doc/build_doc_guide.md`](code-as-doc/build_doc_guide.md)
- current JP / US family difference boundary: [`code-as-doc/manual_family_guide.md`](code-as-doc/manual_family_guide.md)
- current Git branching and GitHub protection rules: [`code-as-doc/dev/git_branching_guide.md`](code-as-doc/dev/git_branching_guide.md)
- current responsive Web Publish and Read the Docs flow: [`code-as-doc/dev/web_publish_pipeline.md`](code-as-doc/dev/web_publish_pipeline.md)
- legacy Vercel latest-publish implementation reference: [`code-as-doc/dev/vercel_review_preview_guide.md`](code-as-doc/dev/vercel_review_preview_guide.md)
- current user workflow and editing rules: [`user-guide/hello_auto-doc.md`](user-guide/hello_auto-doc.md)
- happy-path example: [`user-guide/quick_start_guide.md`](user-guide/quick_start_guide.md)
- closed-loop operations playbook (release tags and rollback, `.ai` handoff, sentinels): [`user-guide/closed_loop_ops_guide.md`](user-guide/closed_loop_ops_guide.md)
- two-plane repo / Base topology: [`user-guide/two_plane_map.md`](user-guide/two_plane_map.md)
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

## 6. Key directories

- [`build.py`](build.py): top-level CLI entrypoint
- [`configs/`](configs): shared family configs (`config.us.yaml`, `config.ja.yaml`, …) with config-base inheritance
- [`tools/`](tools): orchestration, rendering, validation, diff, and release helpers
- [`scripts/`](scripts): branch wrappers, local-build helpers, and queue service scripts
- [`docs/manifests/`](docs/manifests): page-stack manifests for manifest-driven manual families
- [`docs/templates/`](docs/templates): shared seed templates
- [`docs/_review/`](docs/_review): target-specific review layer
- [`docs/_build/`](docs/_build): runtime bundles and export outputs
- `data/phase2/`: gitignored Feishu-synced CSV snapshots; only the repo-maintained [`data/phase2/page_registry.csv`](data/phase2/page_registry.csv) stays tracked because `sync-data` reads it as input
- [`data/source_table_contracts/phase2_source_tables.json`](data/source_table_contracts/phase2_source_tables.json): the machine-readable source-table contract; update it when the online source-table structure changes
- [`tests/fixtures/phase2/`](tests/fixtures/phase2): committed fixture snapshot used only by CI/tests, not by live authoring
- [`tests/`](tests): automated regression coverage
- [`reports/`](reports): revision reports and release evidence; `reports/releases/` is gitignored, and queue Publish ships deliverables to Feishu or short-lived Actions artifacts instead of committing them
- [`integrations/`](integrations): OpenClaw and Feishu adapter packages
- [`.readthedocs.yaml`](.readthedocs.yaml): Read the Docs build config for the generated MyST manual catalog

## 7. Maintenance rules

When command behavior, workflow ownership, or architecture boundaries change:

- update the owning document in the same change, and avoid restating the
  same rules in multiple docs
- **keep this README a map**: it changes only when an entry point, a
  navigation pointer, or an editing-surface rule changes. Behavior and
  contract details go to the owning document (`build_doc_guide.md`,
  `hello_auto-doc.md`, `web_publish_pipeline.md`, …) with at most a one-line
  pointer here. Treat a README beyond ~200 lines as documentation debt.
- keep `python tools/check_maintainability_guardrails.py` green when
  touching the guarded hotspot files, and keep the PR checklist honest: if a
  helper boundary moves, update the module map in the same change
- keep history in
  [`code-as-doc/code_optimization_log.md`](code-as-doc/code_optimization_log.md),
  not in the current guides
