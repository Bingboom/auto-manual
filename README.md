# Auto-Manual Tool

Updated: 2026-05-28

Auto-Manual turns structured content (Feishu/Lark Base CSV snapshots plus shared RST templates) into target-specific manual bundles and release outputs across the active US, EU, JP, and CN config families.
The current maintained smoke-check baseline is `JE-1000F` across US and JP.

**This README is a quickstart and a navigation map. The full command reference, every operational note (Phase 2 snapshot, review sync, Word/HTML/PDF/MD export, Vercel publish, Read the Docs catalog, Windows cleanup, Git workflow, queue routing) lives in [`code-as-doc/build_doc_guide.md`](code-as-doc/build_doc_guide.md).**

**For AI agent windows (Claude Code / Codex):** Claude Code auto-loads [`CLAUDE.md`](CLAUDE.md), which inlines the shared rules in [`AGENTS.md`](AGENTS.md); Codex reads [`AGENTS.md`](AGENTS.md) directly. To start a task in a new window, run `powershell -ExecutionPolicy Bypass -File scripts/start_branch.ps1 <type>/<area>-<topic>` for a fresh branch off up-to-date `main` (the wrapper refuses a dirty tree). Multi-window concurrency rules are in [`AGENTS.md`](AGENTS.md) §8.

## 1. Current Role

This repository is responsible for:

- generating target-specific runtime bundles from templates and local Feishu-synced CSV snapshots, with a valid generated `data/phase2/` snapshot as the default build/review/publish source and explicit `--data-root` still overriding it
- keeping CI deterministic with `tests/fixtures/phase2/` as a frozen sample snapshot while each mirror repo generates its own gitignored `data/phase2/` from its bound Feishu Base
- syncing `main` one-way into [`Bingboom/Hello-Docs`](https://github.com/Bingboom/Hello-Docs) through [`sync-hello-docs.yml`](.github/workflows/sync-hello-docs.yml); `Hello-Docs` keeps its own GitHub Secrets / Variables for the alternate Feishu and OpenClaw bindings, with `FEISHU_BUILD_QUEUE_PAUSED=true` scoped to the mirror Feishu runtime workflows until those bindings are ready
- configuring the mirror binding from local environment variables with [`scripts/configure_hello_docs_binding.sh`](scripts/configure_hello_docs_binding.sh), which writes GitHub Secrets / Variables without printing secret values
- auditing the mirror readiness with [`scripts/audit_hello_docs_binding.sh`](scripts/audit_hello_docs_binding.sh), which checks repo variables, required secret names, and source/mirror tree parity without reading secret values
- moving target-specific editing into [`docs/_review/`](docs/_review) once review starts
- validating review/runtime bundles before release
- exporting revision reports and release manifests
- generating a minimal design handoff package for explicit target delivery prep

This repository is not the place to define the long-term platform strategy.
That boundary lives in [`code-as-doc/architecture/System Evolution Strategy.md`](code-as-doc/architecture/System%20Evolution%20Strategy.md).

## 2. Quickstart

The primary entrypoint is [`build.py`](build.py). A minimal US/EN smoke check:

```bash
python build.py doctor --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py check  --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py review --config configs/config.us-en.yaml --model JE-1000F --region US
```

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

For an in-review cloud doc, bind the diff to the current review source and use
`run-review`:

```bash
python tools/cloud_doc_backport.py run-review --doc-url <doc-or-fixture.md> --source-path docs/_review/<model>/<region>/page/<page>.rst --out reports/cloud_doc_backport/<run-id>
python tools/cloud_doc_backport.py run-review --doc-url <doc-or-fixture.md> --source-path docs/_review/<model>/<region>/page/<page>.rst --out reports/cloud_doc_backport/<run-id> --write
python tools/cloud_doc_backport.py open-pr --manifest reports/cloud_doc_backport/<run-id>/cloud_doc_backport_run.json
```

`run-review` is dry-run by default and writes diff/apply/run reports without
editing `_review`. Add `--write` only after reviewing the apply report; the
write run patches guarded review prose, verifies residuals, and marks the run
`PR_READY` only when the review source changed and verification passed.
Data-like edits remain report-only source-table suggestions, and the runner
writes `cloud_doc_backport_source_table_suggestions.md` with candidate source
tables and operator steps.
`open-pr` is the separate operator-gated PR step: it only accepts a `PR_READY`
run manifest, refuses unrelated working-tree changes, commits the changed
`docs/_review/...rst` source, and opens a draft PR with the manifest summary.

The Feishu IM adapter can also trigger the same review backport runner from a
typed message, gated by `FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOWED_SENDERS`:

```text
cloud-doc backport <Feishu cloud-doc URL> docs/_review/<model>/<region>/page/<page>.rst
cloud-doc backport <Feishu cloud-doc URL>
cloud-doc backport-pr reports/cloud_doc_backport/<run-id>/cloud_doc_backport_run.json
```

The Feishu IM adapter may omit `docs/_review/...rst` only when it can infer a
single review source from a message/cloud-doc title target such as
`manual_je2000f_eu_en_0.7` and the current checkout has exactly one safe
candidate or one unique message-hint match. Ambiguous review bundles reply with
candidate paths instead of guessing.

For the full review-first flow, queue-driven Draft/Publish workers, matrix runners, and every command flag, see [`code-as-doc/build_doc_guide.md`](code-as-doc/build_doc_guide.md). For the editing-surface and source-of-truth rules, see [`user-guide/hello_auto-doc.md`](user-guide/hello_auto-doc.md) and [`user-guide/quick_start_guide.md`](user-guide/quick_start_guide.md). For BlockClaw / Feishu IM behavior, including batch document-link replies that send each artifact link as its own message, see [`integrations/openclaw/feishu-im-webhook-adapter/README.md`](integrations/openclaw/feishu-im-webhook-adapter/README.md).

The fixed US + JP release matrix runners — [`scripts/build_us_jp_manuals.py`](scripts/build_us_jp_manuals.py), [`scripts/build_us_jp_manuals.ps1`](scripts/build_us_jp_manuals.ps1), and the US-only [`scripts/build_us_manuals.ps1`](scripts/build_us_manuals.ps1) — are documented in [`code-as-doc/build_doc_guide.md`](code-as-doc/build_doc_guide.md).

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
- AI agent operating rules (Claude / Codex / future agents): [`AGENTS.md`](AGENTS.md), with [`CLAUDE.md`](CLAUDE.md) as the Claude Code entrypoint
- current OpenClaw bootstrap: [`agent/BOOTSTRAP.md`](agent/BOOTSTRAP.md)
- current OpenClaw integration package: [`integrations/openclaw/README.md`](integrations/openclaw/README.md)
- repo-local translation memory skill for OpenClaw-assisted multilingual work: [`.agents/skills/bitable-translation-memory/SKILL.md`](.agents/skills/bitable-translation-memory/SKILL.md)
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
- `data/phase2/`: gitignored Feishu-synced CSV snapshot inputs for active build, review, and publish flows
- [`tests/fixtures/phase2/`](tests/fixtures/phase2): committed fixture snapshot used only by CI/tests, not by live authoring
- [`docs/templates/`](docs/templates): shared seed templates
- [`.agents/skills/bitable-translation-memory/`](.agents/skills/bitable-translation-memory): repo-local Codex skill for live sentence-pair lookup and terminology grounding
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
