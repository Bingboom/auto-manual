# Auto-Manual Tool

Updated: 2026-03-24

Auto-Manual is the repository that turns structured content into target-specific manual bundles and release outputs.
It owns the current build, review, validation, revision tracking, and publish flow for this repo.
The current maintained smoke-check baseline is centered on `JE-1000F` across the active US, JP, and EU config families.

For the fixed US + JP release matrix, you can also use:

- [`scripts/build_us_jp_manuals.ps1`](scripts/build_us_jp_manuals.ps1): PowerShell wrapper for one-command `US/en + US/es + US/fr + JP/ja`
- [`scripts/build_us_jp_manuals.py`](scripts/build_us_jp_manuals.py): same workflow with `--languages`, `--formats`, `--check-first`, `--open-html`, and `--dry-run`

## 1. Current Role

This repository is responsible for:

- generating target-specific runtime bundles from templates and phase1 CSV data
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
- `Review Preview Package` is a separate non-gating workflow that packages review HTML, review Word, and diff-report HTML/CSV/XLSX for sharing
- the published review preview root is now a region-family managed review handoff workspace: families are hidden when `_review` content is missing, models are grouped, and language switching happens inside each model group
- family-level diff assets stay shared across the languages in that family, while the workspace keeps the top-level review actions and a compact document-identity card with product name, manual title, model, region, and language
- `manual/index.html` and `changes/index.html` remain compatibility entries that redirect to the workspace default manual and family diff pages

## 2. Primary Entrypoint

The primary entrypoint is [`build.py`](build.py).

Typical review-first flow:

```bash
python3 build.py doctor --config config.us-en.yaml --model JE-1000F --region US
python3 build.py rst --config config.us-en.yaml --model JE-1000F --region US --source runtime
python3 build.py review --config config.us-en.yaml --model JE-1000F --region US
python3 build.py check --config config.us-en.yaml --model JE-1000F --region US
python3 build.py publish --config config.us-en.yaml --model JE-1000F --region US
```

Batch export example:

```powershell
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats html,word,pdf
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats html --open-html
```

Word export note:

- `config.us-en.yaml` now reapplies the `reference_en.docx` heading, table, and default paragraph styling after DOCX generation, while keeping the generated `safety` and `spec` pages unchanged

HTML output note:

- generated cover pages remain part of the PDF/LaTeX flow; the HTML entry page starts at the first manual content section instead of rendering a standalone cover screen
- manual HTML now suppresses most Furo documentation chrome in preview mode, uses a continuous reading layout instead of browser-side fake pagination, regenerates a lightweight left outline from manual headings, and presents generic headings, copy width, figures, ordinary tables, and the multilingual preface notice with a restrained neutral manual-reader style while preserving dedicated layouts such as the `SPECIFICATIONS` table treatment
- review-preview/Vercel manual pages now reuse the same manual HTML/CSS/JS treatment as the local build, including the generated heading sidebar and the same no-top-switcher layout

Review-sharing example:

```powershell
python tools/process_docs/build_review_preview.py --config config.us-en.yaml --model JE-1000F --region US --source review --from-ref HEAD~1 --to-ref HEAD
```

Vercel note:

- the review-preview project should use the repo-level [`vercel.json`](vercel.json)
- GitHub Actions is the supported build-and-deploy path for review preview publishing
- the workflow installs `pandoc`, builds [`site/review-preview/dist/`](site/review-preview/dist), runs `vercel pull`, `vercel build`, and `vercel deploy --prebuilt`
- the Vercel bridge entrypoint is [`tools/process_docs/vercel_build_review_preview.py`](tools/process_docs/vercel_build_review_preview.py), which reuses the packaged preview when Actions already built it

Windows note:

- build actions except `fast` clean the current target output first
- if File Explorer, a browser, Word, or a PDF viewer is open under [`docs/_build/`](docs/_build), close it before rerunning
- if you only need an in-place rebuild, add `--no-clean`

Do not treat this file as the full command reference.
The command semantics and output layout are maintained in [`code-as-doc/build_doc_guide.md`](code-as-doc/build_doc_guide.md).

## 3. Editing Surfaces

Use different surfaces for different stages:

- shared template changes: [`docs/templates/`](docs/templates)
- structured data changes: [`data/phase1/`](data/phase1)
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
- current JP / US / EU family difference boundary: [`code-as-doc/manual_family_guide.md`](code-as-doc/manual_family_guide.md)
- current Git branching and GitHub protection rules: [`code-as-doc/dev/git_branching_guide.md`](code-as-doc/dev/git_branching_guide.md)
- current Vercel review-preview packaging flow: [`code-as-doc/dev/vercel_review_preview_guide.md`](code-as-doc/dev/vercel_review_preview_guide.md)
- current user workflow and editing rules: [`user-guide/hello_auto-doc.md`](user-guide/hello_auto-doc.md)
- happy-path example: [`user-guide/quick_start_guide.md`](user-guide/quick_start_guide.md)
- maintainer doc index: [`code-as-doc/README.md`](code-as-doc/README.md)
- current repository component map: [`code-as-doc/architecture/Hello_Docs_Architecture.md`](code-as-doc/architecture/Hello_Docs_Architecture.md)
- future canonical content model: [`code-as-doc/architecture/Content_Data_Model.md`](code-as-doc/architecture/Content_Data_Model.md)
- long-term strategy and stable architecture boundaries: [`code-as-doc/architecture/System Evolution Strategy.md`](code-as-doc/architecture/System%20Evolution%20Strategy.md)
- repo-level execution roadmap: [`optimization_project.md`](optimization_project.md)

## 5. Key Directories

- [`build.py`](build.py): top-level CLI entrypoint
- [`tools/`](tools): orchestration, rendering, validation, diff, and release helpers
- [`docs/manifests/`](docs/manifests): page-stack manifests for manifest-driven manual families
- [`data/phase1/`](data/phase1): current operational CSV snapshot inputs
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
