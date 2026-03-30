# Windows Build Guide

Updated: 2026-03-24

This file is the maintainer-facing Windows and PowerShell build guide.
The current cross-platform entrypoint is [`build.py`](../build.py).
For the fixed four-language release pack, use [`../scripts/build_us_jp_manuals.ps1`](../scripts/build_us_jp_manuals.ps1) or [`../scripts/build_us_jp_manuals.py`](../scripts/build_us_jp_manuals.py).

For user-facing review workflow details, read:

- [`user-guide/hello_auto-doc.md`](../user-guide/hello_auto-doc.md)
- [`user-guide/quick_start_guide.md`](../user-guide/quick_start_guide.md)

## 1. Recommended Entrypoint

```powershell
python build.py validate
python build.py rst
python build.py review
python build.py check
python build.py sync-review
python build.py publish --config config.ja.yaml --model JE-1000F --region JP
python build.py release-manifest --config config.ja.yaml --model JE-1000F --region JP
python build.py handoff --config config.us-en.yaml --model JE-1000F --region US --version V0.1 --baseline docs/_build/JE-1000F/US/en/rst
python build.py preview --config config.ja.yaml --model JE-1000F --region JP --page 03_product_overview_placeholder
python build.py fast --config config.ja.yaml --model JE-1000F --region JP
python build.py html
python build.py word
python build.py pdf
python build.py all
python build.py diff-report
python build.py clean
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats html,word,pdf
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats html --open-html
```

Meaning:

- `validate`: validate config and [`data/layout_params.csv`](../data/layout_params.csv)
- `rst`: materialize [`docs/_build/<model>/<region>/rst/`](../docs/_build)
- `review`: seed [`docs/_review/<model>/<region>/`](../docs/_review) from runtime draft
- `check`: run validation + prepare bundle + content checks, including stale identity scan and contract validation
- `sync-review`: refresh review files affected by CSV data changes
- `publish`: run `check -> diff-report -> word -> release-manifest` for one explicit target
- `release-manifest`: write JSON / CSV release traceability for one explicit target
- `handoff`: create a minimal explicit target design handoff package with rule-based diff outputs and traceability metadata
- `preview`: materialize one exact page selector under a preview-only output root
- `fast`: materialize a runtime draft only, with `prepare-only + no-clean`
- `html`, `word`, `pdf`: prepare RST first, then export
- `all`: export `html + word + pdf`
- `diff-report`: export Git-based revision tables, defaulting to the resolved target review root
- `clean`: remove [`docs/_build/`](../docs/_build), [`docs/_review/`](../docs/_review), old legacy output directories, and generated [`params.tex`](../docs/renderers/latex/params.tex)
- `build_us_jp_manuals.ps1`: build the fixed `US/en + US/es + US/fr + JP/ja` target set from one command, with selectable format combinations such as `html,word` or `word,pdf`
- `--open-html`: after the batch finishes, open the generated HTML entry pages for the selected language set

Windows cleanup note:

- build actions except `fast` run with clean enabled unless you pass `--no-clean`
- if cleanup fails with a file-in-use error under [`docs/_build/`](../docs/_build), close File Explorer, browser, Word, or PDF windows pointing at that target output and rerun
- `--no-clean` is the temporary workaround when you only need to rebuild in place

GitHub validation note:

- `Manual Validation` is the repository CI workflow
- pull requests run the required merge-gating checks
- pushes to `main` run the same workflow again after merge
- feature branches no longer run a duplicate `push` validation pass in GitHub
- `Review Preview Package` is a separate artifact workflow for design sharing and does not gate merge

## 2. Config Rule

Do not create one config file per model.

Current shared config families:

- [`config.yaml`](../config.yaml): shared EN / US template family
- [`config.us-en.yaml`](../config.us-en.yaml): canonical US English review / CI / Vercel entrypoint
- [`config.ja.yaml`](../config.ja.yaml): shared JP template family

Page-stack note:

- shared config families may resolve their page stack through `paths.page_manifest`
- keep manifest-driven page order changes under [`docs/manifests/`](../docs/manifests)

Pass target differences through:

- `--model`
- `--region`
- `build.targets`
- [`data/phase1/*.csv`](../data/phase1)

Only create a new config when one of these really changes:

- page stack
- template family
- output convention
- language family
- Word reference template

## 3. Standard Windows Flow

### 3.1 Validate Environment and Config

```powershell
python build.py validate --config config.yaml
```

Equivalent low-level checks:

```powershell
python tools\validate_config.py --config config.yaml
python tools\validate_layout_params.py --csv data\layout_params.csv
```

### 3.2 Create a Runtime Draft

```powershell
python build.py rst --config config.ja.yaml --model JE-1000F --region JP --source runtime
```

This creates:

- [`docs/_build/JE-1000F/JP/rst/`](../docs/_build/JE-1000F/JP/rst)

Use `--source runtime` when you want a fresh draft from template + data only.

### 3.3 Enter Review

```powershell
python build.py review --config config.ja.yaml --model JE-1000F --region JP
```

This seeds:

- [`docs/_review/JE-1000F/JP/`](../docs/_review/JE-1000F/JP)

After review starts, daily editing should happen in `_review`, not in `_build`.

### 3.4 Refresh Review After Data Changes

If you update any of these:

- [`data/phase1/Spec_Master.csv`](../data/phase1/Spec_Master.csv)
- [`data/phase1/Spec_Footnotes.csv`](../data/phase1/Spec_Footnotes.csv)
- [`data/phase1/spec_titles.csv`](../data/phase1/spec_titles.csv)
- [`data/phase1/content_blocks.csv`](../data/phase1/content_blocks.csv) (legacy safety source)
- [`data/phase1/symbols_blocks.csv`](../data/phase1/symbols_blocks.csv)

Safety page note:

- US safety intro pages are maintained directly in [`docs/templates/page_us-en/safety_en.rst`](../docs/templates/page_us-en/safety_en.rst), [`docs/templates/page_us-fr/safety_fr.rst`](../docs/templates/page_us-fr/safety_fr.rst), and [`docs/templates/page_us-es/safety_es.rst`](../docs/templates/page_us-es/safety_es.rst)
- the JP manual maintains its safety intro in [`docs/templates/page_jp/safety_ja.rst`](../docs/templates/page_jp/safety_ja.rst) through [`docs/manifests/manual_jp.yaml`](../docs/manifests/manual_jp.yaml)
- edit those `safety_*.rst` files when a family's safety intro page needs copy/layout changes
- the detailed JP safety warnings remain in [`docs/templates/page_jp/01_meaning_of_symbols.rst`](../docs/templates/page_jp/01_meaning_of_symbols.rst)
- [`data/phase1/content_blocks.csv`](../data/phase1/content_blocks.csv) is kept only for legacy reference and future cleanup; active family builds no longer use it as the main safety maintenance surface

`symbols_blocks.csv` note:

- `image_path` stores the RST image reference path for each symbols-table icon
- `Region` and `Model` now match the target-selection field names used by [`Spec_Master.csv`](../data/phase1/Spec_Master.csv)
- `Source_lang` stores the row's source-language code, using the same naming rule as [`Spec_Master.csv`](../data/phase1/Spec_Master.csv)
- leave `Region` / `Model` blank when one symbols row is shared across manuals
- `sku_scope` is no longer used in [`symbols_blocks.csv`](../data/phase1/symbols_blocks.csv)

`Spec_Master.csv` note:

- the `Page` column may now hold a comma-separated page list
- use `Product overview` for Product overview-only page-value rows
- use `Product overview, specifications,` when a row is intentionally shared by both pages
- `Row_label_source`, `Param_source`, and `Value_source` are the shared source-text columns; they should hold the row's source-manual text
- `Source_lang` stores that source-language code explicitly; use values such as `en`, `ja`, and `zh`, and do not rely on `Region` to infer it
- `project_code` / `项目代码` is no longer part of `Spec_Master.csv`; target rows by `Region` + `Model`
- `Row_label_en`, `Param_en`, and `Value_en` are no longer supported; rename them to `*_source` before importing or checking the sheet

`Spec_Footnotes.csv` supports two spec-bottom row types:

- `row_kind=footnote`: numbered entries such as `①`
- `row_kind=note`: plain note lines such as trademark statements
- If the numbering symbol differs by language, write it directly in each `footnote_text_*` cell and leave `footnote_mark` empty
- `project_code` / `项目代码` is no longer part of `Spec_Footnotes.csv`; target rows by `Region` + `Model`

run:

```powershell
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP
```

By default this updates data-driven files in the review bundle without resetting the entire review text.

Useful variants:

```powershell
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP --sync-scope generated
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP --page-file 02_whats_in_the_box.rst
```

### 3.5 Build from Review

Once `_review` exists, these commands use review content by default because `--source auto` overlays review on top of the runtime bundle:

```powershell
python build.py check --config config.ja.yaml --model JE-1000F --region JP
python build.py html --config config.ja.yaml --model JE-1000F --region JP
python build.py word --config config.ja.yaml --model JE-1000F --region JP
python build.py pdf --config config.ja.yaml --model JE-1000F --region JP
```

`check` now also catches stale foreign model names and contract-required spec keys, required page-value selectors, and assets.

### 3.6 Package a Review Preview for Design

Use this when design needs the rendered review HTML plus the current family-level diff package:

```powershell
python tools/process_docs/build_review_preview.py --config config.us-en.yaml --model JE-1000F --region US --source review --from-ref HEAD~1 --to-ref HEAD
```

Default packaged output:

- [`../site/review-preview/dist/`](../site/review-preview/dist)

This package contains:

- `index.html`: the workspace root for region-family navigation
- `manual/`: review-based HTML, grouped by family and model, with language-specific entries inside each model group
- `changes/`: family-level diff pages plus a family hub at `changes/index.html`
- `downloads/`: family-scoped `review-manual.docx`, `change-report.xlsx`, and copied diff-report CSV files
- `generated/meta.json`: branch / commit metadata
- `generated/changes.json`: grouped changed files, review pages, and download metadata
- `generated/workspace.json`: the workspace data contract used by the root page
- `manual/index.html`: compatibility redirect to the default manual
- `changes/index.html`: family selector that links the packaged `US / JP` diff pages instead of dropping reviewers into one default family report

Packaging rule:

- the review preview output contract is `index.html`, `manual/`, `changes/`, `downloads/`, and `generated/`
- CI treats `review-manual.docx` and `change-report.xlsx` as required artifacts
- `--skip-word` is for local debugging only and is not used by the CI workflow
- the workspace hides families with no `_review` content, so the packaged site only shows available families
- diff, workbook, and CSV outputs stay family-level shared assets, not language-specific artifacts
- the default change entry in the packaged workspace now opens the family hub first, so reviewers can choose `US` or `JP` explicitly

Vercel note:

- GitHub Actions installs `pandoc`, builds the review preview package, uploads it as an artifact, then runs `vercel pull`, `vercel build`, and `vercel deploy --prebuilt`
- Vercel should host the prebuilt package only; do not rely on Git-triggered Vercel Python builds for this flow
- configure `VERCEL_TOKEN`, `VERCEL_ORG_ID`, and `VERCEL_PROJECT_ID` in repository secrets for the deploy step
- in normal use, open a pull request first; then each push to that PR branch will refresh the review preview automatically when the change hits the configured workflow paths
- if you are still iterating before opening a PR, use `Actions -> Review Preview Package -> Run workflow`

### 3.7 Publish a Final Word Release

```powershell
python build.py publish --config config.ja.yaml --model JE-1000F --region JP
```

This is the formal release command.
It requires an explicit `--model` and `--region`.

Outputs:

- review diff report: [`reports/version_tracking/JE-1000F/JP/`](../reports/version_tracking/JE-1000F/JP)
- final Word: [`docs/_build/JE-1000F/JP/word/manual_je1000f_jp.docx`](../docs/_build/JE-1000F/JP/word/manual_je1000f_jp.docx)
- release manifest: [`reports/releases/JE-1000F/JP/`](../reports/releases/JE-1000F/JP)

## 4. Output Layout

Runtime outputs:

- [`docs/_build/<model>/<region>/rst/`](../docs/_build)
- [`docs/_build/<model>/<region>/preview/<page>/rst/`](../docs/_build)
- [`docs/_build/<model>/<region>/html/`](../docs/_build)
- [`docs/_build/<model>/<region>/word/`](../docs/_build)
- [`docs/_build/<model>/<region>/pdf/`](../docs/_build)

HTML output starts at the first manual content section. Generated cover pages are preserved for PDF/LaTeX output, not rendered as a standalone HTML home screen.
In manual preview mode, the HTML view also suppresses most Furo navigation chrome, stays in a continuous reading flow instead of browser-side fake pagination, regenerates a lightweight left outline from manual headings, and applies a restrained neutral manual-reader treatment to generic headings, copy width, figures, ordinary docutils tables, and the multilingual preface notice while preserving dedicated component layouts such as `SPECIFICATIONS`.
For review-preview / Vercel packaging, the manual pages now reuse the same manual HTML/CSS/JS treatment as the local build, including the generated heading sidebar and the same no-top-switcher layout.

Review working bundle:

- [`docs/_review/<model>/<region>/`](../docs/_review)

Review handoff workspace:

- [`../site/review-preview/dist/`](../site/review-preview/dist)

Revision reports:

- [`reports/version_tracking/<model>/<region>/`](../reports/version_tracking)

Release manifests:

- [`reports/releases/<model>/<region>/`](../reports/releases)

## 5. Typical Commands

Build all targets defined in one config:

```powershell
python build.py rst --config config.yaml
python build.py word --config config.yaml
python build.py all --config config.ja.yaml
```

Build one explicit target:

```powershell
python build.py word --config config.us-en.yaml --model JE-1000F --region US
python build.py pdf --config config.ja.yaml --model JE-1000F --region JP
```

Word styling note:

- `config.us-en.yaml` now post-processes the generated DOCX so non-safety / non-spec pages inherit the `reference_en.docx` heading, table, and default paragraph styling

Single-page preview and fast draft:

```powershell
python build.py preview --config config.us-en.yaml --model JE-1000F --region US --page 03_product_overview_placeholder
python build.py fast --config config.us-en.yaml --model JE-1000F --region US
```

Standalone release traceability:

```powershell
python build.py release-manifest --config config.ja.yaml --model JE-1000F --region JP
```

Keep existing build artifacts:

```powershell
python build.py html --config config.yaml --no-clean
```

Open generated artifacts if the backend supports it:

```powershell
python build.py pdf --config config.yaml --open
```

Override PDF backend:

```powershell
python build.py pdf --config config.yaml --pdf-mode latex
python build.py pdf --config config.yaml --pdf-mode word
```

## 6. Diff Report

Typical usage:

```powershell
python build.py diff-report --config config.ja.yaml --model JE-1000F --region JP
python build.py diff-report --config config.ja.yaml --model JE-1000F --region JP --from-ref HEAD~1 --to-ref HEAD
python build.py diff-report --config config.ja.yaml --tracked-root docs/_review/JE-1000F/JP
python build.py diff-report --config config.ja.yaml --tracked-root docs/_review/JE-1000F/JP --from-ref HEAD~1 --to-ref HEAD
python build.py diff-report --config config.ja.yaml --tracked-root docs/_review/JE-1000F/JP --include-initial-adds
```

Generated report types:

- `*_files.csv` / `*_files.html`
- `*_pages.csv` / `*_pages.html`
- `*_fields.csv` / `*_fields.html`
- `*_index.html`

The current report defaults are review-oriented, not `_build`-oriented.
If `--tracked-root` is omitted, `build.py` resolves `docs/_review/<model>/<region>/` and `reports/version_tracking/<model>/<region>/` automatically from the target.
Initial baseline Added rows are now hidden by default so the first non-baseline review round is easier to read. Pass `--include-initial-adds` when you need the full initial import noise.
Field pairing now prefers stable source back-mapping before falling back to rendered labels, so placeholder/spec label rewrites are more likely to appear as one `M` row with clearer `old_value/new_value` instead of separate `A/D` rows.

## 7. Common Mistakes

- Editing [`docs/_build/**`](../docs/_build) as if it were the authoring surface
- Creating a new config only because the model changed
- Using `review --refresh-review` when only parameter pages need to be synced
- Forgetting to commit `_review/<model>/<region>/` after each review round
- Treating `_build/rst` and `_review` as the same thing
- Putting review metadata in `overrides/` and expecting it to overlay; only `_assets`, `_static`, and `renderers` are copied into the runtime bundle

## 8. Minimal Troubleshooting

`Failed to resolve Product Name from Spec_Master.csv`

- Check [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) for `Row_key=product_name`
- Check model / region / language coverage
- Run `python build.py check --config ... --model ... --region ...`

Review bundle not found

- Seed it first with `python build.py review --config ... --model ... --region ...`

Need to rebuild the first draft from template/data only

- Use `--source runtime`

Need to release from reviewed text only

- Use `python build.py publish --config ... --model ... --region ...`

`STALE_IDENTITY_LITERAL` or another model name is reported during `check`

- fix the template or review text if the model mention is stale
- if the foreign literal is intentional, add it to `checks.allowed_foreign_identity_literals`
