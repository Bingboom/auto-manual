# Auto-Manual Tool

Updated: 2026-04-03

Auto-Manual is the repository that turns structured content into target-specific manual bundles and release outputs.
It owns the current build, review, validation, revision tracking, and publish flow for this repo.
The current maintained smoke-check baseline is centered on `JE-1000F` across the active US and JP config families.

For the fixed US + JP release matrix, you can also use:

- [`scripts/build_us_jp_manuals.ps1`](scripts/build_us_jp_manuals.ps1): PowerShell wrapper for one-command `US/en + US/es + US/fr + JP/ja`
- [`scripts/build_us_jp_manuals.py`](scripts/build_us_jp_manuals.py): same workflow with `--languages`, `--formats`, `--check-first`, `--open-html`, and `--dry-run`

## 1. Current Role

This repository is responsible for:

- generating target-specific runtime bundles from templates and frozen CSV snapshots, with `data/phase2/` as the preferred synced snapshot root
- moving target-specific editing into [`docs/_review/`](docs/_review) once review starts
- validating review/runtime bundles before release
- exporting revision reports and release manifests
- generating a minimal design handoff package for explicit target delivery prep

This repository is not the place to define the long-term platform strategy.
That boundary lives in [`code-as-doc/architecture/System Evolution Strategy.md`](code-as-doc/architecture/System%20Evolution%20Strategy.md).

CI note:

- GitHub `Manual Validation` runs on pull requests for merge gating
- the same workflow runs again on `main` after merge for post-merge validation
- feature-branch pushes do not need a second duplicate `push` validation run
- `Review Preview Package` is a separate non-gating workflow that packages review HTML, review Word, and diff-report HTML/CSV/XLSX for sharing as a GitHub artifact
- the published review preview root is now a multi-model review handoff workspace: families are hidden when `_review` content is missing, models are grouped inside each family, and language switching happens inside each model group
- diff assets now stay shared across the languages of one `family + model` package, while the workspace keeps the top-level review actions and a compact document-identity card with product name, manual title, model, region, and language
- `manual/index.html` remains a compatibility redirect to the workspace default manual, while `changes/index.html` opens the family hub and each family hub fans out to model-specific diff packages

## 2. Primary Entrypoint

The primary entrypoint is [`build.py`](build.py).

Typical review-first flow:

```bash
python3 build.py sync-data --config config.us.yaml --data-root data/phase2
python3 build.py doctor --config config.us-en.yaml --model JE-1000F --region US
python3 build.py rst --config config.us-en.yaml --model JE-1000F --region US --source runtime --data-root data/phase2
python3 build.py review --config config.us-en.yaml --model JE-1000F --region US
python3 build.py check --config config.us-en.yaml --model JE-1000F --region US --data-root data/phase2
python3 build.py process-review-start-queue --config config.us.yaml --data-root .tmp/review-start/phase2
python3 build.py process-build-queue --config config.us.yaml --data-root data/phase2
python3 build.py publish --config config.us-en.yaml --model JE-1000F --region US --data-root data/phase2
```

Review sync note:

- once a review bundle exists, `check`, `html`, `word`, `pdf`, and `publish` automatically prepare the runtime bundle and run the same parameter sync before export
- that auto sync now refreshes parameter-driven lines in review-backed RST pages without overwriting the rest of the manual review prose
- use `sync-review --page-file ...` or `review --refresh-review` only when you intentionally want a whole review page or bundle replaced from runtime
- single-language US review bundles from `config.us-en.yaml` still live under `docs/_review/<model>/US/en/`; the merged US queue/review flow driven by `config.us.yaml` now uses `docs/_review/<model>/US/` and exports one combined `en + fr + es` Word under `docs/_build/<model>/US/word/`

Phase2 snapshot note:

- `sync-data` uses the local `lark-cli` login and `sync.phase2.*` config/env bindings to write normalized CSV snapshots into [`data/phase2/`](data/phase2), using the CLI's `base` record listing flow under the hood
- for queue-driven Draft / Publish builds, Feishu phase2 tables are the structured-data source of truth; committed `data/phase2/*.csv` files are treated as build-time snapshots and will be refreshed by `sync-data` before the queue builds
- `sync-data` normalizes `Spec_Master.csv Slot_key` back to plain tokens such as `front.label` when the source table stores markdown-link wrappers like `[front.label](front.label)`
- `sync-data` now resolves full field names through Base field metadata before writing CSVs, so long columns such as `Row_label_footnote_refs` are not lost when `lark-cli` abbreviates display headers in `base +record-list`
- when `spec_master` is part of the sync, `sync-data` also regenerates [`data/phase2/row_key_mapping.csv`](data/phase2/row_key_mapping.csv) from the synced snapshot while preserving any existing manual `Row_key` / `Remark` entries
- `python build.py sync-data --config config.us.yaml --data-root data/phase2 --dry-run` is the fastest preflight on a new machine; it now reports missing `lark-cli` and missing `FEISHU_PHASE2_*` bindings together before any API call
- on Windows, the default `sync.phase2.cli_bin: lark-cli` now resolves to the installed `lark-cli` shim automatically, so no config override is required just to run `sync-data`
- `python build.py process-review-start-queue --config config.us.yaml --data-root .tmp/review-start/phase2` consumes the `sync.phase2.review_init` table, finds rows where `是否进入Review` is checked and `Review_status` is empty / `NotStarted`, groups matching rows by `Document_Key`, syncs a fresh phase2 snapshot, creates or reuses one review branch, seeds `docs/_review`, pushes the branch, opens or reuses a PR, then writes back the same `Git_ref`, `PR_url`, `Review_status=InReview`, and cleared `是否进入Review` state to every pending row in that `Document_Key` group
- review-init duplicate guard: review start is now treated as one-time per `Document_Key` target. If `origin/main` already contains committed content under `docs/_review/<model>/<region>/`, the worker refuses duplicate seeding and writes back `Initial_result=不允许重复创建` plus `Remarks=如需强制刷新内容，请在vs通过相关git命令操作，具体详见文档quick_start_guide.md.`
- [`.github/workflows/feishu-start-review.yml`](.github/workflows/feishu-start-review.yml) is the GitHub-hosted review-init worker; it needs `FEISHU_PHASE2_REVIEW_INIT_TABLE_ID` and `FEISHU_PHASE2_REVIEW_INIT_VIEW_ID`, and it is the recommended way to let a Feishu table create the review branch + PR automatically
- `python build.py process-build-queue --config config.us.yaml --data-root data/phase2` consumes the `sync.phase2.document_link` task table, writes `开始构建时间` as soon as a pending row starts, resolves the build config from `Document_Key` first when that config enables `build.queue_by_document_key`, builds the generated Word file, uploads it to Feishu Drive, then moves that uploaded file into the current wiki knowledge-base container before writing the local Word path back to `Document directory`, the wiki URL back to `Document link`, a timestamped status string to `构建结果`, and the trigger back to `已构建`
- the merged US `config.us.yaml` bundle now exports one `JE-1000F / US` Word that contains `en`, `fr`, and `es` sections together; `Spec_Master.Source_lang` / `*_source` content is required, and CSV-driven non-source language fields may be blank because lookup falls back to source-language text automatically
- merged US review-init and build-queue rows are both keyed by `Document_Key`; when those rows leave `Lang` blank, the worker still resolves `config.us.yaml`, runs one shared review/build cycle for that group, and writes the same branch/build result back to every row in the group
- when the queue row includes `Version`, Draft queue DOCX names use `manual_<model>_<region>_<lang>_<Version>.docx`, while Publish queue DOCX names use `manual_<model>_<region>_<lang>_publish_<Version>.docx`
- when the queue row includes `Git_ref`, queue builds fetch that branch into a temporary worktree and build from that branch content instead of silently falling back to `main`
- Draft queue outputs stay staged under the current repo [`docs/_build/`](docs/_build) tree before upload/writeback
- Publish queue outputs are staged under [`reports/releases/<model>/<region>/<lang>/versions/<version>/`](reports/releases), and the latest publish HTML snapshot is mirrored under [`reports/releases/<model>/<region>/<lang>/latest/html/`](reports/releases) for Vercel hosting
- [`scripts/process_build_queue.ps1`](scripts/process_build_queue.ps1) is the Windows-friendly queue wrapper for automation: it restores the local Node/npm path plus `FEISHU_PHASE2_*` user env vars, runs `build.py process-build-queue`, and writes logs into [`.tmp/process-build-queue/`](.tmp/process-build-queue)
- `python build.py listen-build-queue --config config.us.yaml --data-root data/phase2` starts the push-based queue listener: it auto-subscribes the current `Document_link` base to docs events with the current user identity, waits on the Feishu long connection with the same user identity, and triggers `process-build-queue` immediately when the `是否立即构建` checkbox is checked on a `Document_link` row
- [`scripts/listen_build_queue.ps1`](scripts/listen_build_queue.ps1) is the Windows-friendly listener wrapper; on this machine it is launched from the Windows Startup folder so the listener starts after login and writes logs into [`.tmp/build-queue-listener/`](.tmp/build-queue-listener)
- [`.github/workflows/feishu-build-queue.yml`](.github/workflows/feishu-build-queue.yml) is the remote GitHub Actions worker: after merge to the default branch and after repo secrets are configured, it runs every 5 minutes plus `workflow_dispatch`, uses `FEISHU_PHASE2_IDENTITY=bot`, syncs `data/phase2`, then consumes the `Document_link` queue without relying on any local machine
- for remote immediate builds after merge to `main`, create a Feishu workflow with the combined condition `是否触发文档构建 = Y` and `是否立即构建 = true`, then call the GitHub `workflow_dispatch` API for `feishu-build-queue.yml`; the queue still only processes rows whose trigger field is `Y`, and the checkbox acts as an accelerator instead of a standalone build request
- the Document_link worker reuses `FEISHU_PHASE2_BASE_TOKEN`, expects `FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID` plus `FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID`, and can optionally honor `FEISHU_PHASE2_DOCUMENT_LINK_WIKI_PARENT_TOKEN` when you want to override the default knowledge-base destination
- the remote bot flow also needs the Feishu app behind `FEISHU_APP_ID/FEISHU_APP_SECRET` to have read access to the phase2 source tables and write access to the `Document_link` table; otherwise the poller can read pending rows but cannot write back `开始构建时间` / `构建结果`
- if the queue should move uploaded Word files into a wiki knowledge base, the same user/bot identity also needs edit/container permission on the destination wiki parent node; otherwise upload succeeds but the wiki move step fails
- the push listener requires the Feishu self-built app to have the `drive.file.bitable_record_changed_v1` event added and published in the Open Platform console; without that event, the long connection stays idle even though the local listener is running
- `page_registry.csv` and [`data/layout_params.csv`](data/layout_params.csv) stay repo-maintained and are not overridden by `--data-root`

Draft / Publish queue split:

- `process-build-queue` now refreshes `data/phase2` with `sync-data` before it starts building queued rows
- `process-build-queue --doc-phase draft` uses Feishu-refreshed `data/phase2` plus the PR branch's current [`docs/_review/`](docs/_review) content; Draft is for documents that have already entered review
- `process-build-queue --doc-phase draft` consumes only `Doc_phase=Draft`
- `process-build-queue --doc-phase publish` uses Feishu-refreshed `data/phase2` plus `Document_link.Git_ref` when present, runs `build.py publish` and `build.py html --source review`, then stages the formal release bundle under `reports/releases`
- `process-build-queue --doc-phase publish` consumes only `Doc_phase=Publish`
- `process-build-queue --record-id <record_id>` lets one workflow rebuild exactly one `Document_link` row
- [`.github/workflows/feishu-build-queue.yml`](.github/workflows/feishu-build-queue.yml) is the `main`-owned Publish queue worker
- [`.github/workflows/feishu-draft-build-queue.yml`](.github/workflows/feishu-draft-build-queue.yml) is the PR-owned Draft queue worker
- when you dispatch the Draft worker, the GitHub `ref` must be the PR head branch, otherwise the generated Draft document will still come from `main`
- when a Publish row carries `Git_ref`, the `main`-owned Publish queue worker now builds that review branch instead of rebuilding from `main`

- recommended stage split:
  - use the review-init table to move one document into review and create its branch / PR once
  - use the `Document_link` queue with `Doc_phase=Draft` to rebuild Draft from that PR branch repeatedly
  - use the `Document_link` queue with `Doc_phase=Publish` plus `Git_ref` to publish from that same review branch

Dedicated zh bundle example:

```bash
python3 build.py check --config config.zh.yaml --model JE-2000E --region CN
python3 build.py all --config config.zh.yaml --model JE-2000E --region CN
```

Batch export example:

```powershell
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats html,word,pdf
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats html --open-html
```

Word export note:

- `config.us-en.yaml` now reapplies the `reference_en.docx` heading, table, and default paragraph styling after DOCX generation, while keeping the generated `safety` and `spec` pages unchanged
- generated DOCX images are now normalized to embedded relationships before post-processing so third-party viewers such as Feishu are less likely to drop image-backed table cells during preview

HTML output note:

- generated cover pages remain part of the PDF/LaTeX flow; the HTML entry page starts at the first manual content section instead of rendering a standalone cover screen
- manual HTML now suppresses most Furo documentation chrome in preview mode, uses a continuous reading layout instead of browser-side fake pagination, regenerates a lightweight left outline from manual headings, and presents generic headings, copy width, figures, ordinary tables, and the multilingual preface notice with a restrained neutral manual-reader style while preserving dedicated layouts such as the `SPECIFICATIONS` table treatment
- review-preview workspace manual pages now reuse the same manual HTML/CSS/JS treatment as the local build, including the generated heading sidebar and the same no-top-switcher layout
- when a PR changes the zh manual family under `docs/templates/page_zh/`, `docs/templates/recipes/zh/`, or `docs/manifests/manual_zh.yaml`, review-preview keeps `JE-2000E / CN` as the primary runtime target but still packages every existing review model into the same workspace
- `build.py diff-report` now ignores initial baseline Added rows by default; pass `--include-initial-adds` when you need the full first-import churn
- diff-report field matching now prefers stable source back-mapping before falling back to rendered labels, so placeholder/spec label rewrites are more likely to surface as one `M` row with clearer `old_value/new_value` instead of separate `A/D` noise

Review-sharing example:

```powershell
python tools/process_docs/build_review_preview.py --config config.us-en.yaml --model JE-1000F --region US --source review --from-ref HEAD~1 --to-ref HEAD --all-review-models
```

Vercel note:

- the repo-level [`vercel.json`](vercel.json) now points at the latest publish HTML flow, not the review-preview package
- [`.github/workflows/feishu-build-queue.yml`](.github/workflows/feishu-build-queue.yml) builds queue-driven Publish rows, stages the latest publish HTML under [`site/publish-latest/dist/`](site/publish-latest/dist), then runs `vercel pull`, `vercel build`, and `vercel deploy --prebuilt`
- the Vercel bridge entrypoint is [`tools/process_docs/vercel_build_publish_latest.py`](tools/process_docs/vercel_build_publish_latest.py), which reuses an already staged latest publish site when it exists
- `Review Preview Package` no longer deploys to Vercel; it uploads the review-sharing package as an artifact only

Read the Docs note:

- [`.readthedocs.yaml`](.readthedocs.yaml) now provides a minimal RTD entrypoint for the default runtime HTML manual only: `config.us-en.yaml + JE-1000F + US + en`
- the RTD job runs `python build.py rst --config config.us-en.yaml --model JE-1000F --region US --source runtime --no-clean --skip-root-index`, then points Sphinx at [`docs/_build/JE-1000F/US/en/rst/`](docs/_build) instead of the repo-root [`docs/`](docs)
- RTD is for a stable public reading target only; it does not replace review-preview packaging, queue-driven Publish releases, Vercel latest-publish hosting, or Word / PDF export

Windows note:

- build actions except `fast` clean the current target output first
- if File Explorer, a browser, Word, or a PDF viewer is open under [`docs/_build/`](docs/_build), close it before rerunning
- if you only need an in-place rebuild, add `--no-clean`

Do not treat this file as the full command reference.
The command semantics and output layout are maintained in [`code-as-doc/build_doc_guide.md`](code-as-doc/build_doc_guide.md).

## 3. Editing Surfaces

Use different surfaces for different stages:

- shared template changes: [`docs/templates/`](docs/templates)
- structured data changes: preferred snapshot root [`data/phase2/`](data/phase2), with [`data/phase1/`](data/phase1) kept as the legacy baseline
  `Spec_Footnotes.csv` is now the footnote-definition table only. Keep one row per reusable `Footnote_id`, target rows by `Region` + `Model`, and let the system derive the visible superscript marker from `Footnote_order`.
`Spec_Master.csv` `Page` may now be a comma-separated page list. Use `Product overview` for Product overview-only placeholder rows, and use `Product overview, specifications,` when the same row is shared by both pages. For page-value rows, keep `Row_key` as the concept and use `Slot_key` to describe the placeholder slot. The shared source-text columns are `Row_label_source`, `Param_source`, and `Value_source`; they hold the row's source-manual text. `Source_lang` stores that source-language code explicitly, for example `en`, `ja`, or `zh`, and code no longer infers it from `Region`. `document_key` is a derived helper column and may use either `[Model]_[Region]` or `[Model]_[Region]_[Source_lang]`. `Row_order` is now a formal column and controls the row display order inside each `document_key + Page + Section`, while `Line_order` controls the order of multiple lines inside one logical row. Visible section defaults can live in `spec_titles.csv section_order`, but if `Spec_Master.csv Section_order` is filled, that explicit value has the highest priority. `Row_label_en`, `Param_en`, and `Value_en` are no longer supported; source-language text must live in `*_source`. The old `project_code` / `项目代码` column has been removed; row targeting now uses `Region` + `Model`. Spec-cell footnotes are now referenced through `Row_label_footnote_refs`, `Param_footnote_refs`, and `Value_footnote_refs`; do not handwrite `①②③` into visible spec text.
  `Spec_Notes.csv` now stores bottom-of-spec notes that are not tied to a superscript reference, such as trademark statements.
  `symbols_blocks.csv` stores symbols-page table copy, uses `Region` and `Model` to match target manuals like `Spec_Master.csv`, keeps `Source_lang` aligned with the same source-language code pattern, and includes an `image_path` field for the referenced icon asset. Leave `Region` / `Model` blank when one symbols row should be shared.
  Safety intro pages are now maintained as fixed RST templates under [`docs/templates/page_*/safety_*.rst`](docs/templates), wired through each family's manifest or page list. JP still keeps its detailed warning content in [`docs/templates/page_jp/01_meaning_of_symbols.rst`](docs/templates/page_jp/01_meaning_of_symbols.rst). The old `content_blocks.csv` safety source has been removed from the active repo flow.
- target-specific review edits after review starts: [`docs/_review/`](docs/_review)
- generated runtime and export outputs: [`docs/_build/`](docs/_build)

Rule:

- before review starts, seed the draft from templates and data
- after review starts, edit `_review`
- do not use `_build` as the long-lived editing surface

The current user workflow and source-of-truth rules are maintained in [`user-guide/hello_auto-doc.md`](user-guide/hello_auto-doc.md).

## 4. Document Map

Use the document that owns the topic:

- current maintainer command reference: [`code-as-doc/build_doc_guide.md`](code-as-doc/build_doc_guide.md)
- focused design handoff usage guide: [`code-as-doc/README_design_handoff.md`](code-as-doc/README_design_handoff.md)
- current JP / US family difference boundary: [`code-as-doc/manual_family_guide.md`](code-as-doc/manual_family_guide.md)
- current Git branching and GitHub protection rules: [`code-as-doc/dev/git_branching_guide.md`](code-as-doc/dev/git_branching_guide.md)
- current Vercel latest-publish HTML flow: [`code-as-doc/dev/vercel_review_preview_guide.md`](code-as-doc/dev/vercel_review_preview_guide.md)
- current user workflow and editing rules: [`user-guide/hello_auto-doc.md`](user-guide/hello_auto-doc.md)
- happy-path example: [`user-guide/quick_start_guide.md`](user-guide/quick_start_guide.md)
- maintainer doc index: [`code-as-doc/README.md`](code-as-doc/README.md)
- current repository component map: [`code-as-doc/architecture/Hello_Docs_Architecture.md`](code-as-doc/architecture/Hello_Docs_Architecture.md)
- future canonical content model: [`code-as-doc/architecture/Content_Data_Model.md`](code-as-doc/architecture/Content_Data_Model.md)
- long-term strategy and stable architecture boundaries: [`code-as-doc/architecture/System Evolution Strategy.md`](code-as-doc/architecture/System%20Evolution%20Strategy.md)
- repo-level execution roadmap: [`optimization_project.md`](optimization_project.md)

## 5. Key Directories

- [`build.py`](build.py): top-level CLI entrypoint
- [`.readthedocs.yaml`](.readthedocs.yaml): minimal Read the Docs build config for the default US English runtime HTML target
- [`tools/`](tools): orchestration, rendering, validation, diff, and release helpers
- [`docs/manifests/`](docs/manifests): page-stack manifests for manifest-driven manual families
- [`docs/templates/page_zh/`](docs/templates/page_zh): shared zh prose-template family for the CN manual stack
- [`data/phase2/`](data/phase2): preferred Feishu-synced CSV snapshot inputs
- [`data/phase1/`](data/phase1): legacy baseline snapshot inputs
- [`docs/templates/`](docs/templates): shared seed templates
- [`docs/_review/`](docs/_review): target-specific review layer
- [`docs/_build/`](docs/_build): runtime bundles and export outputs
- [`reports/`](reports): revision reports and release manifests
- [`tests/`](tests): automated regression coverage

## 6. Maintenance Rule

When command behavior, workflow ownership, or architecture boundaries change:

- update the owning document in the same change
- avoid restating the same rules in multiple docs
- keep history in [`code-as-doc/code_optimization_log.md`](code-as-doc/code_optimization_log.md), not in the current guides

