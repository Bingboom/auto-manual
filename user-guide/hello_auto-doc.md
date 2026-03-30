# Hello Auto Doc

Updated: 2026-03-24

This file replaces `Template_maintenance_and_using_guide.md`.
It documents the current build layout, maintenance rules, the review bundle layer under [`docs/_review/<model>/<region>/`](../docs/_review), and the current review-first publishing flow.
It is the current workflow and editing-surface guide.
It is not the full maintainer command reference; use [`../code-as-doc/build_doc_guide.md`](../code-as-doc/build_doc_guide.md) for command semantics.
For the current JP / US / EU family difference boundary, use [`../code-as-doc/manual_family_guide.md`](../code-as-doc/manual_family_guide.md).

---

## 1. Environment Setup

Before running any build, review, check, or publish command, prepare the local environment in the repository root.

### 1.1 Python Environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

The dependency install step is mandatory.
Do not skip `python -m pip install -r requirements.txt` or `python3 -m pip install -r requirements.txt` when preparing a fresh environment.

### 1.2 External Tools

- PDF export requires `xelatex`.
- Word export requires `pandoc` on macOS / Linux and on non-Word-COM paths.
- The Python dependencies in [`requirements.txt`](../requirements.txt) include the Sphinx theme and build libraries used by the current workflow.

If you only need the exact command semantics for one export path, use [`../code-as-doc/build_doc_guide.md`](../code-as-doc/build_doc_guide.md) as the authoritative reference.

GitHub note:

- pull requests are gated by the `Manual Validation` workflow
- after merge, `main` runs the same validation workflow again
- feature-branch pushes are not expected to run a second duplicate `push` validation pass
- `Review Preview Package` is the separate packaging path when you need to share rendered review HTML with design
- that workflow expects `pandoc` for the review Word export path and blocks preview deployment if the required Word / Excel downloads are missing

---

## 2. Source of Truth

The manual system now has four layers, but they are used at different stages.

1. Template seed layer
   - [`docs/templates/page_us-en/*.rst`](../docs/templates/page_us-en)
   - [`docs/templates/page_eu/*.rst`](../docs/templates/page_eu)
   - [`docs/templates/page_jp/*.rst`](../docs/templates/page_jp)
   - [`docs/manifests/*.yaml`](../docs/manifests)
   - Responsibility: reusable page structure, headings, shared prose, and initial draft layout

2. Data layer
   - [`data/phase1/Spec_Master.csv`](../data/phase1/Spec_Master.csv)
   - [`data/phase1/Spec_Footnotes.csv`](../data/phase1/Spec_Footnotes.csv)
   - [`data/phase1/spec_titles.csv`](../data/phase1/spec_titles.csv)
   - [`data/phase1/content_blocks.csv`](../data/phase1/content_blocks.csv)
   - [`data/phase1/symbols_blocks.csv`](../data/phase1/symbols_blocks.csv)
   - [`data/phase1/page_registry.csv`](../data/phase1/page_registry.csv)
   - Responsibility: model-specific parameters, safety/spec content, and placeholder values
   - JP safety page prose is maintained in [`docs/templates/page_jp/safety_ja.rst`](../docs/templates/page_jp/safety_ja.rst) through [`docs/manifests/manual_jp.yaml`](../docs/manifests/manual_jp.yaml); it is only the short safety intro, while detailed JP safety warnings remain in [`docs/templates/page_jp/01_meaning_of_symbols.rst`](../docs/templates/page_jp/01_meaning_of_symbols.rst). `content_blocks.csv` still drives CSV-backed safety pages for the other families
   - `Spec_Footnotes.csv` can hold both numbered spec footnotes and plain bottom notes such as trademark lines; if numbering differs by language, write the marker directly in each `footnote_text_*` cell and leave `footnote_mark` empty
   - `Spec_Master.csv` uses `Row_label_source`, `Param_source`, and `Value_source` as the shared source-language columns; `Source_lang` stores that source-language code explicitly, for example `en`, `ja`, and `zh`, and code no longer infers it from `Region`
   - `Row_label_en`, `Param_en`, and `Value_en` are no longer supported; rename them to `*_source`
   - `symbols_blocks.csv` uses `Region`, `Model`, and `Source_lang` with the same naming as `Spec_Master.csv`; leave `Region` / `Model` blank when one symbols row is shared
   - `symbols_blocks.csv` uses `image_path` for the icon asset referenced by each symbols-table row

3. Review working layer
   - [`docs/_review/<model>/<region>/index.rst`](../docs/_review)
   - [`docs/_review/<model>/<region>/page/*.rst`](../docs/_review)
   - [`docs/_review/<model>/<region>/generated/<model>/*.rst`](../docs/_review)
   - [`docs/_review/<model>/<region>/manifest.json`](../docs/_review)
   - [`docs/_review/<model>/<region>/overrides/**`](../docs/_review)
   - Responsibility: target-specific review editing, Git review, revision history, final release source after review starts

4. Runtime build layer
   - [`docs/_build/<model>/<region>/rst/**`](../docs/_build)
   - [`docs/_build/<model>/<region>/html/**`](../docs/_build)
   - [`docs/_build/<model>/<region>/word/**`](../docs/_build)
   - [`docs/_build/<model>/<region>/pdf/**`](../docs/_build)
   - [`docs/index.rst`](../docs/index.rst)
   - Responsibility: generated bundle plus final outputs

Rules:

- Before review starts, use template/data to create the first draft.
- After review starts, use [`docs/_review/...`](../docs/_review/) as the daily editing surface for that target.
- Edit templates only when the change should be shared by multiple manuals.
- Edit CSV when product parameters change.
- Treat [`docs/_build/...`](../docs/_build/) as generated runtime output.
- Keep region-family differences explicit where they are real: spec data, certification text, unit conventions, and `meaning_of_symbols` stay family-specific.
- When design needs to review layout or page effect, share a review handoff workspace built from `_review`, not the raw `.rst`.
- when that workspace is published through Vercel, let GitHub Actions build the package first and let Vercel host the generated static output only
- designers should start from the workspace root, then pick a family, model, and language before opening the rendered manual or family diff page
- the workspace root now keeps the primary review actions plus a compact document-identity card with product name, manual title, model, region, and language
- the packaged preview now also includes `downloads/review-manual.docx`, `downloads/change-report.xlsx`, the raw diff CSV files, and `generated/workspace.json`
- families without `_review` content are hidden, so the preview only shows available families
- the packaged `changes/index.html` now opens a family hub first, so reviewers can switch between available families such as `US` and `JP` before jumping into a family-specific change report
- if the target branch already has an open pull request, each new push to that PR branch will rerun `Review Preview Package` automatically when the changed files match the workflow paths
- after that workflow finishes, Vercel will show the refreshed review preview for that round; you do not need to rebuild the site manually in Vercel
- if there is no open pull request yet, trigger `Review Preview Package` manually from the `Actions` tab

---

## 3. Current Build Pipeline

The cross-platform entrypoint is [`build.py`](../build.py).
It wraps [`tools/build_docs.py`](../tools/build_docs.py), which still drives the actual build logic.
If you need the fixed `US/en + US/es + US/fr + JP/ja` export set, use [`../scripts/build_us_jp_manuals.ps1`](../scripts/build_us_jp_manuals.ps1) as a thin wrapper over `build.py`.

Current flow:

1. `python build.py rst|html|word|pdf|all|review|check|sync-review|publish|diff-report|release-manifest|handoff|preview|fast|doctor`
2. [`tools/build_docs.py`](../tools/build_docs.py) validates config and layout params
3. target `model` and `region` are resolved from CLI or `build.targets`
4. `product_name` is resolved from [`Spec_Master.csv`](../data/phase1/Spec_Master.csv)
5. CSV-backed pages are generated by [`tools/phase1_build.py`](../tools/phase1_build.py)
6. [`tools/gen_index_bundle.py`](../tools/gen_index_bundle.py) materializes the runtime bundle
7. the runtime bundle is written to [`docs/_build/<model>/<region>/rst/`](../docs/_build)
8. if source mode is `auto` or `review` and a review bundle exists, review content is overlaid onto the runtime bundle
9. [`docs/index.rst`](../docs/index.rst) is refreshed to point at all existing bundle roots
10. `html`, `word`, and `pdf` outputs are built from the prepared bundle when requested
11. `python build.py review` seeds [`docs/_review/<model>/<region>/`](../docs/_review) from the runtime bundle when review starts
12. `python build.py sync-review` refreshes parameter-driven review files from the runtime bundle without replacing the whole review bundle
13. `python build.py check` runs config/layout validation, prepares the bundle, and scans for bundle issues
14. `python tools/process_docs/build_review_preview.py` packages review HTML, review Word, diff-report HTML, diff-report CSV, and a single Excel workbook for design sharing
15. `python build.py diff-report` exports review diffs, defaulting to the resolved target review root
16. `python build.py release-manifest` writes release traceability JSON / CSV for one explicit target
17. `python build.py preview` materializes one exact page selector under a preview-only output root
18. `python build.py fast` materializes a runtime-only draft without export

Important:

- `python build.py rst` only materializes the RST bundle.
- `python build.py word`, `python build.py html`, and `python build.py pdf` all prepare the RST bundle first.
- `python build.py all` runs `html`, `word`, and `pdf` after the same prepare step.
- build actions except `fast` clean the current target output first; on Windows, close File Explorer, browser, Word, or PDF windows opened under [`docs/_build/`](../docs/_build) before rerunning, or use `--no-clean` for an in-place rebuild.
- `python build.py review` prepares a runtime draft from template/data, then seeds review only if review does not already exist.
- `python build.py review --refresh-review` intentionally replaces an existing review bundle from template/data.
- `python build.py sync-review` is the safe path after [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) changes during review.
- `python build.py check`, `word`, `html`, and `pdf` use `source=auto` by default, so they build from `_review` once review exists.
- `python build.py publish` uses review content only, then runs `check -> diff-report -> word -> release-manifest` as one formal release command.
- `python build.py handoff` now generates a minimal handoff package under [`docs/_handoff/`](../docs): it resolves explicit baseline/current inputs, loads supported `rst/html` inputs, generates rule-based add/delete/replace records, copies referenced draft images into `draft/assets/`, and writes `draft/manual.md`, `draft/manual.docx`, optional `draft/manual.html`, `changes/change_log.csv`, `changes/change_log.xlsx`, `changes/change_summary.md`, `handoff/design_handoff.md`, and `manifest.json`. It does not yet provide final page mapping or advanced semantic change classification.
- `.\scripts\build_us_jp_manuals.ps1 --model <MODEL> --formats html,word,pdf` is the one-command wrapper for the fixed four-language export pack.
- `.\scripts\build_us_jp_manuals.ps1 --model <MODEL> --formats html --open-html` builds the selected HTML set and opens the generated HTML entry pages.
- `check` now catches stale foreign model names, unresolved placeholders, missing assets, and contract-required spec keys / page-value selectors / assets.
- review overrides only overlay `overrides/_assets/**`, `overrides/_static/**`, and `overrides/renderers/**` into the runtime bundle.

---

## 4. Materialized Bundle Layout

For a target such as `JE-1000F / US`, the working bundle now lives here:

- [`docs/_build/JE-1000F/US/rst/index.rst`](../docs/_build/JE-1000F/US/rst/index.rst)
- [`docs/_build/JE-1000F/US/rst/page/*.rst`](../docs/_build/JE-1000F/US/rst/page)
- [`docs/_build/JE-1000F/US/rst/generated/JE-1000F/*.rst`](../docs/_build/JE-1000F/US/rst/generated/JE-1000F)
- [`docs/_build/JE-1000F/US/rst/conf.py`](../docs/_build/JE-1000F/US/rst/conf.py)
- [`docs/_build/JE-1000F/US/rst/conf_base.py`](../docs/_build/JE-1000F/US/rst/conf_base.py)
- [`docs/_build/JE-1000F/US/rst/_static/**`](../docs/_build/JE-1000F/US/rst/_static)
- [`docs/_build/JE-1000F/US/rst/renderers/**`](../docs/_build/JE-1000F/US/rst/renderers)

This is the generated bundle consumed by Sphinx, HTML export, Word export, and PDF export.
It is not the editing surface. After review starts, `_review/...` is overlaid onto this bundle before publish.

---

## 5. Git Tracking Rule for Review Bundles

The current repo allows two Git-visible surfaces:

- [`docs/_build/**/**/rst/**`](../docs/_build) is no longer ignored
- [`docs/_review/**`](../docs/_review) is emitted as a review-first snapshot
- sibling outputs such as [`docs/_build/**/**/html/**`](../docs/_build), `word/**`, and `pdf/**` remain build artifacts

This gives you two benefits:

1. You can commit generated review bundles per target and keep reviewable history.
2. You can export Git diffs for a single model or region as CSV and HTML reports.

What this does not change:

- `_build/.../rst/**` is still regenerated on the next build.
- `_review/.../**` is now the durable review-editing surface for that target once review starts.
- `python build.py review --refresh-review` is the only path that intentionally replaces the existing review content from template/data.

Recommended use:

1. Seed the target review bundle once with `python build.py review --config ...`
2. Edit [`docs/_review/<model>/<region>/**`](../docs/_review)
3. Build preview/final outputs with `check/html/word/pdf`
4. Commit the resulting review bundle
5. Use `python build.py diff-report ...` when you need a table-style change export

For the current maintainer branch model, pull request rules, and GitHub protection settings, use [`../code-as-doc/dev/git_branching_guide.md`](../code-as-doc/dev/git_branching_guide.md).

---

## 5. Which Files You Should Edit

Edit these when the change should be shared across products or when creating the first draft:

- [`docs/templates/page_us-en/*.rst`](../docs/templates/page_us-en)
- [`docs/templates/page_eu/*.rst`](../docs/templates/page_eu)
- [`docs/templates/page_jp/*.rst`](../docs/templates/page_jp)

Edit these when safety/spec parameters change:

- [`data/phase1/content_blocks.csv`](../data/phase1/content_blocks.csv)
- [`data/phase1/symbols_blocks.csv`](../data/phase1/symbols_blocks.csv)
- [`data/phase1/Spec_Master.csv`](../data/phase1/Spec_Master.csv)
- [`data/phase1/Spec_Footnotes.csv`](../data/phase1/Spec_Footnotes.csv)
- [`data/phase1/spec_titles.csv`](../data/phase1/spec_titles.csv)

JP safety exception:

- edit [`docs/templates/page_jp/safety_ja.rst`](../docs/templates/page_jp/safety_ja.rst) when the Japanese safety page itself needs copy or layout changes
- edit [`docs/templates/page_jp/01_meaning_of_symbols.rst`](../docs/templates/page_jp/01_meaning_of_symbols.rst) when the detailed Japanese safety warnings need changes
- keep using [`data/phase1/content_blocks.csv`](../data/phase1/content_blocks.csv) for shared CSV-backed safety content in the other families

Edit these during target review and final polish:

- [`docs/_review/<model>/<region>/index.rst`](../docs/_review)
- [`docs/_review/<model>/<region>/page/*.rst`](../docs/_review)
- [`docs/_review/<model>/<region>/generated/<model>/*.rst`](../docs/_review)
- [`docs/_review/<model>/<region>/overrides/_assets/**`](../docs/_review)
- [`docs/_review/<model>/<region>/overrides/_static/**`](../docs/_review)
- [`docs/_review/<model>/<region>/overrides/renderers/**`](../docs/_review)

Do not use these as the primary authoring source:

- [`docs/_build/<model>/<region>/rst/page/*.rst`](../docs/_build)
- [`docs/_build/<model>/<region>/rst/generated/<model>/*.rst`](../docs/_build)
- [`docs/_build/<model>/<region>/rst/index.rst`](../docs/_build)
- [`docs/index.rst`](../docs/index.rst)

You may commit `_review/...` for review history because it is now the target editing surface after review starts.

---

## 6. How Safety and Spec Pages Work

Safety content is usually generated by [`tools/phase1_build.py`](../tools/phase1_build.py).

Primary inputs:

- [`data/phase1/page_registry.csv`](../data/phase1/page_registry.csv)
- [`data/phase1/content_blocks.csv`](../data/phase1/content_blocks.csv)
- optional page override CSV such as [`data/phase1/<page_id>_blocks.csv`](../data/phase1)

JP manual exception:

- [`docs/manifests/manual_jp.yaml`](../docs/manifests/manual_jp.yaml) now includes [`docs/templates/page_jp/safety_ja.rst`](../docs/templates/page_jp/safety_ja.rst) directly
- edit that template when the JP safety intro page must change
- the detailed JP warning content remains in [`docs/templates/page_jp/01_meaning_of_symbols.rst`](../docs/templates/page_jp/01_meaning_of_symbols.rst)
- keep the CSV-generated safety flow for families that still use `csv_page`

Generated bundle output:

- [`docs/_build/<model>/<region>/rst/generated/<model>/safety_<lang>.rst`](../docs/_build)
- materialized page include: [`docs/_build/<model>/<region>/rst/page/safety_<lang>.rst`](../docs/_build)

Symbols content is generated from:

- [`data/phase1/page_registry.csv`](../data/phase1/page_registry.csv)
- [`data/phase1/symbols_blocks.csv`](../data/phase1/symbols_blocks.csv)

`symbols_blocks.csv` notes:

- use one `table_row` per symbols-table entry
- use `Region` and `Model` to target the same way as `Spec_Master.csv`
- use `Source_lang` for the row's source-language code, for example `en` or `ja`
- leave `Region` / `Model` blank when one row should be shared
- `image_path` stores the RST image reference path for that icon
- keep `symbol_key` stable so renderer alt text and layout metadata still resolve correctly

Spec content is generated from:

- [`data/phase1/Spec_Master.csv`](../data/phase1/Spec_Master.csv)
- optional [`data/phase1/Spec_Footnotes.csv`](../data/phase1/Spec_Footnotes.csv)
- optional [`data/phase1/spec_titles.csv`](../data/phase1/spec_titles.csv)

Generated bundle output:

- [`docs/_build/<model>/<region>/rst/generated/<model>/spec_<lang>.rst`](../docs/_build)
- materialized page include: [`docs/_build/<model>/<region>/rst/page/spec_<lang>.rst`](../docs/_build)

[`Spec_Master.csv`](../data/phase1/Spec_Master.csv) remains the main source of truth for spec sections, rows, and page-value placeholder records.

---

## 7. Placeholder Rules

Core placeholders resolved from [`Spec_Master.csv`](../data/phase1/Spec_Master.csv):

- `|PRODUCT_NAME|`
- `|PRODUCT_NAME_BOLD|`
- `|PRODUCT_SHORT_NAME|`
- `|PRODUCT_SHORT_NAME_BOLD|`
- `|MODEL_NO|`

Resolution source:

- `product_name` comes from `Row_key=product_name`
- `model_no` comes from `Row_key=model_no`
- `PRODUCT_SHORT_NAME` is derived from `PRODUCT_NAME`

`Spec_Master.csv` `Page` note:

- `Page` can be a comma-separated list
- use `Product overview` for Product overview-only page-value rows such as front/side-view callouts
- use `Product overview, specifications,` when the same row is intentionally shared by both pages
- `Row_label_source`, `Param_source`, and `Value_source` should store the row's source-manual text
- `Source_lang` should store the normalized source-language code for the row, such as `en`, `ja`, or `zh`; do not expect code to infer it from `Region`
- source-language rows must keep their actual source text in `Row_label_source`, `Param_source`, and `Value_source`

For page-value rows, `Row_key` now keeps only the concept itself. Human editing should happen through `Slot_key`.

Examples:

- `Row_key=main_power_button`, `Slot_key=label` -> `|MAIN_POWER_BUTTON_LABEL|`
- `Row_key=ac_input`, `Slot_key=side.spec` -> `|SIDE_AC_INPUT_SPEC|`
- `Row_key=battery_pack_name`, `Slot_key=value` -> `|BATTERY_PACK_NAME|`

Derived behavior:

- non-empty placeholders also get `..._BOLD`
- placeholders ending in `_LABEL` also get `..._LOWER`
- multi-line page-value rows produce suffixed placeholders such as `|EXAMPLE_KEY_2|`

---

## 8. Build Commands

Cross-platform entrypoint:

```powershell
python build.py doctor --config config.us-en.yaml --model JE-1000F --region US
python build.py rst
python build.py review
python build.py check
python build.py sync-review
python build.py publish
python build.py release-manifest
python build.py preview --config config.us-en.yaml --model JE-1000F --region US --page 03_product_overview_placeholder
python build.py fast --config config.us-en.yaml --model JE-1000F --region US
python build.py html
python build.py word
python build.py pdf
python build.py all
```

Config scope rule:

- [`config.yaml`](../config.yaml): shared EN / US template-family config
- [`config.us-en.yaml`](../config.us-en.yaml): canonical US English review / CI / Vercel entrypoint
- [`config.ja.yaml`](../config.ja.yaml): shared JP template-family config
- [`config.eu.yaml`](../config.eu.yaml): shared EU template-family config
- the current maintained baseline target is `JE-1000F` across these active config families, including `JE-1000F / EU`
- do not create a new config only because the model changed; pass `--model` and `--region` instead
- create a new config only when the page stack, template family, or output conventions are genuinely different

Useful target-scoped examples:

```powershell
python build.py doctor --config config.ja.yaml --model JE-1000F --region JP
python build.py rst --config config.ja.yaml
python build.py review --config config.us-en.yaml --model JE-1000F --region US
python build.py review --config config.us-en.yaml --model JE-1000F --region US --refresh-review
python build.py sync-review --config config.us-en.yaml --model JE-1000F --region US
python build.py check --config config.us-en.yaml --model JE-1000F --region US
python build.py publish --config config.us-en.yaml --model JE-1000F --region US
python build.py rst --config config.yaml
python build.py word --config config.us-en.yaml --model JE-1000F --region US
python build.py pdf --config config.ja.yaml --model JE-2000F --region JP
```

Source mode examples:

```powershell
python build.py rst --config config.ja.yaml --model JE-1000F --region JP --source runtime
python build.py word --config config.ja.yaml --model JE-1000F --region JP --source review
```

Source mode meaning:

- `auto`: use `_review` if it exists, otherwise use template/data runtime draft
- `runtime`: ignore `_review` and build from template/data
- `review`: require `_review` and build from it

`publish` behavior:

- requires explicit `--model` and `--region`
- requires an existing `_review/<model>/<region>/`
- exports revision reports to [`reports/version_tracking/<model>/<region>/`](../reports/version_tracking) by default
- writes a release manifest to [`reports/releases/<model>/<region>/`](../reports/releases)

`preview` behavior:

- requires explicit `--model`, `--region`, and `--page`
- `--page` must match one exact page selector
- writes to [`docs/_build/<model>/<region>/preview/<page>/rst/`](../docs/_build)
- does not rewrite root [`docs/index.rst`](../docs/index.rst)

`fast` behavior:

- equivalent to a runtime-only `rst --prepare-only --no-clean`
- useful for template or placeholder debugging without export steps

`sync-review` behavior:

- first refreshes the runtime bundle from template/data
- then updates only data-driven review files by default
- does not replace ordinary review prose pages unless you explicitly name them with `--page-file`
- data-driven means:
  - all generated CSV pages
  - all materialized `spec_*` / `safety_*` pages
  - all template pages whose source contains placeholders such as `|PRODUCT_NAME|` or `|MAIN_POWER_BUTTON_LABEL|`
  - cover pages generated from title/product identity
- generated cover pages still feed PDF/LaTeX output, but HTML now opens directly on the first manual content section instead of a blank cover-style landing screen
- manual HTML preview also suppresses most default Furo sidebar / TOC chrome, stays in a continuous reading flow instead of browser-side fake pagination, regenerates a lightweight left outline from the manual headings, and renders generic headings, copy width, figure presentation, ordinary table spacing, and the multilingual preface notice in a restrained neutral manual-reader style while keeping dedicated component layouts such as `SPECIFICATIONS`, so the result feels like a manual reader instead of a documentation site
- review-preview / Vercel manual pages now reuse the same manual HTML/CSS/JS treatment as the local build, including the generated heading sidebar and the same no-top-switcher layout

Equivalent lower-level examples:

```powershell
.\.venv\Scripts\python.exe tools\build_docs.py --config config.us-en.yaml --model JE-1000F --region US --prepare-only
.\.venv\Scripts\python.exe tools\build_docs.py --config config.us-en.yaml --model JE-1000F --region US --formats word --no-open
```

Word styling note:

- the US English Word path now reapplies the `reference_en.docx` heading, table, and default paragraph styling after DOCX generation, while leaving the generated `safety` and `spec` pages as-is

---

## 9. Version Tracking and Diff Export

Because [`docs/_review/**`](../docs/_review) is now the preferred review surface, you can keep cleaner RST history per target.

Recommended everyday workflow:

1. Pick the target you want to track.
2. Seed the review bundle once for that target.
3. Commit the review bundle as a Git baseline.
4. Edit the review bundle for normal review rounds.
5. If parameters changed in CSV, run `sync-review`.
6. Rebuild preview outputs from that review bundle and commit again.
7. Run `publish` for the formal release output, or run `diff-report` separately when needed.

### 9.1 First-Time Baseline

Use this when a target has never been tracked in Git before.

Example baseline:

```powershell
python build.py review --config config.us-en.yaml --model JE-1000F --region US
git add docs/_review/JE-1000F/US
git commit -m "Add JE-1000F US review baseline"
```

What this means:

- `review` prepares [`docs/_build/<model>/<region>/rst/**`](../docs/_build) from template/data
- then it seeds [`docs/_review/<model>/<region>/**`](../docs/_review)
- the commit becomes the starting point for future report comparisons

### 9.2 Daily Update Flow

After the baseline exists, the normal update loop is:

```powershell
python build.py check --config config.us-en.yaml --model JE-1000F --region US
python build.py word --config config.us-en.yaml --model JE-1000F --region US
git add docs/_review/JE-1000F/US
git commit -m "Update JE-1000F US manual"
```

Recommended rule:

- `_review` is now the normal authoring source after review starts
- if a round also changed shared template/data, commit those with `_review`
- use `review --refresh-review` only when intentionally reseeding from the shared seed layer
- use `sync-review` after parameter changes in [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) so review keeps up with regenerated values

### 9.3 Which `tracked-root` to Use

Use the tracked root that matches the scope you want to compare:

- one model across all tracked regions:
  [`docs/_review/JE-1000F`](../docs/_review/JE-1000F)
- one model and one region:
  [`docs/_review/JE-1000F/US`](../docs/_review/JE-1000F/US)
- temporary runtime-only comparison:
  [`docs/_build/JE-1000F`](../docs/_build/JE-1000F)

Recommended default:

- prefer `_review`
- use `_build` only for temporary debugging when you have not emitted a review bundle yet

Example report export for one model:

```powershell
python build.py diff-report --config config.us-en.yaml --model JE-1000F --region US
python build.py diff-report --config config.us-en.yaml --tracked-root docs/_review/JE-1000F --from-ref HEAD~1 --to-ref HEAD
python build.py diff-report --config config.us-en.yaml --tracked-root docs/_review/JE-1000F --from-ref HEAD~1 --to-ref HEAD --include-initial-adds
```

Example report export for one region:

```powershell
python build.py diff-report --config config.us-en.yaml --tracked-root docs/_review/JE-1000F/US --from-ref HEAD~3 --to-ref HEAD
```

### 9.4 How to Compare Two Specific Commits

If you want to compare a baseline commit with the latest manual state:

```powershell
python build.py diff-report --config config.us-en.yaml --tracked-root docs/_review/JE-1000F/US --from-ref <old_commit> --to-ref <new_commit>
```

Examples:

- compare the previous commit to the current one:
  `--from-ref HEAD~1 --to-ref HEAD`
- compare the baseline commit to current head:
  `--from-ref a1b2c3d --to-ref HEAD`
- compare two tags or branches:
  `--from-ref release/v1 --to-ref release/v2`

Default outputs:

- [`reports/version_tracking/JE-1000F/US/*_files.csv`](../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_files.html`](../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_pages.csv`](../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_pages.html`](../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_fields.csv`](../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_fields.html`](../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_index.html`](../reports/version_tracking/JE-1000F/US)
- legacy report path aliases remain available as [`reports/version_tracking/JE-1000F/US/*.csv`](../reports/version_tracking/JE-1000F/US) and `*.html`

Use `--report-dir` if you want a different output folder.

Useful option:

- `--include-initial-adds`
  The default report already hides one-time initial baseline Added rows. Use this only when you want to see the full first-import churn.

Automatic behavior:

- if the tracked subtree does not exist at `from-ref` but exists at `to-ref`, the report now shows an explicit note that this is an initial baseline and all Added rows are expected
- by default, the generated reports keep the note but suppress those initial Added rows
- if you pass `--include-initial-adds`, those initial Added rows are kept in the generated reports

### 9.5 Which Report to Open First

Open order:

1. `*_index.html`
2. `*_fields.html`
3. `*_pages.html`
4. `*_files.html`

Why:

- `index` gives the report homepage and target jump links
- `fields` is usually the most useful review view because it shows rendered value changes and source back-mapping
- `pages` is the next best rollup when you want page-level impact
- `files` is best when you need raw file churn, insertions, and deletions

What each report means:

- `files`: which tracked `.rst` files changed, plus insertions and deletions
- `pages`: page-level rollup with `fields_changed` counts
- `fields`: structured field/value changes extracted from list-tables and `Label: Value` lines
  For generated `spec_*.rst` pages, the report now also tries to fill `source_row_key`, `source_section_key`, `source_line_order`, and `source_csv_line` from [`Spec_Master.csv`](../data/phase1/Spec_Master.csv).
  For template-based pages such as `03_product_overview`, `05_operation_guide`, and `12_app_setup`, the report also tries to back-map changed field text to matching page-value rows by comparing rendered values against resolved placeholders.
  `fields.html` now includes built-in filters for `model`, `region`, `page_key`, `source_row_key`, `change_type`, plus a full-text search box.
- `index`: homepage that links `files/pages/fields` together and provides target-level jump links with filters pre-applied

### 9.6 How to Read `fields` Back-Mapping

Important columns in `*_fields.csv` and `*_fields.html`:

- `field_key`: the rendered field label found in the RST content
- `old_value` / `new_value`: the rendered before/after values
- `source_row_key`: the matched source row in [`Spec_Master.csv`](../data/phase1/Spec_Master.csv)
- `source_section_key`: the matched source section in [`Spec_Master.csv`](../data/phase1/Spec_Master.csv)
- `source_line_order`: the matched source line order for multiline rows
- `source_csv_line`: the original CSV line number
- when a field label itself changes, the diff now first tries to pair old/new rows through stable source back-mapping before falling back to rendered label text, so placeholder/spec renames are more likely to show up as one `M` row with both `old_value` and `new_value`

Interpretation rule:

- if `source_row_key` is filled, the report found a source row match
- if it is blank, the row is still useful as a rendered text diff, but the source mapping was not reliable enough to fill automatically

### 9.7 Typical Review Example

For a normal JE-1000F US review cycle:

```powershell
python build.py check --config config.us-en.yaml --model JE-1000F --region US
git add docs/_review/JE-1000F/US
git commit -m "Refresh JE-1000F US manual"
python build.py publish --config config.us-en.yaml --model JE-1000F --region US
```

Then:

1. open [`reports/version_tracking/JE-1000F/US/*_index.html`](../reports/version_tracking/JE-1000F/US)
2. click the `JE-1000F/US` target link
3. open `fields`
4. filter `source_row_key` when you want to inspect one spec or placeholder family

### 9.8 Common Mistakes

- Comparing `_build` after a fresh clean without rebuilding the same target first
- Running `review --refresh-review` without realizing it will replace the current review bundle
- Changing parameter CSV data during review and forgetting to run `sync-review`
- Forgetting that `check/html/word/pdf` now use review content by default once review exists
- Committing only `_review` when the round also changed shared template or CSV logic
- Reading `files.html` first and missing the more useful field-level diff in `fields.html`

---

## 10. Page Contracts

The repo now supports page contract checks under:

- [`docs/templates/contracts/03_product_overview.yaml`](../docs/templates/contracts/03_product_overview.yaml)
- [`docs/templates/contracts/05_operation_guide.yaml`](../docs/templates/contracts/05_operation_guide.yaml)
- [`docs/templates/contracts/05_operation_guide_eu.yaml`](../docs/templates/contracts/05_operation_guide_eu.yaml)
- [`docs/templates/contracts/12_app_setup.yaml`](../docs/templates/contracts/12_app_setup.yaml)
- [`docs/templates/contracts/12_app_setup_eu.yaml`](../docs/templates/contracts/12_app_setup_eu.yaml)

Current scope:

- contracts are matched by source template path from `config.pages`
- `check` validates required placeholders, spec row keys, page-value selectors, and required assets
- current coverage includes `03_product_overview`, `05_operation_guide`, and `12_app_setup`
- `EN`, `JP`, and `EU` template families can each declare their own required placeholder sets
- contracts can be scoped by `allowed_languages`, `allowed_regions`, and `allowed_models`

Current contract keys:

- `required_placeholders`
- `required_spec_keys`
- `required_page_values`
- `required_assets`
- `allowed_languages`
- `allowed_regions`
- `allowed_models`

Why this matters:

- a page can fail early when required page-value bindings are missing
- fallback values in [`conf_base.py`](../docs/conf_base.py) no longer hide missing product-specific spec data
- new model onboarding becomes easier to validate before Word/PDF export

---

## 11. Common Pitfalls

### 11.1 Editing the wrong layer

Before review starts:

- edit template/data

After review starts:

- edit [`docs/_review/<model>/<region>/**`](../docs/_review)

Never edit:

- [`docs/_build/<model>/<region>/rst/**`](../docs/_build)

Use template/data only for shared reusable changes or intentional reseeding.

### 11.2 `?` appears in output

This is usually caused by dirty page-value rows in [`Spec_Master.csv`](../data/phase1/Spec_Master.csv), not by the template structure itself.

### 11.3 Old model names survive in the new manual

This usually means one of these happened:

- a template still contains hard-coded model text
- `product_name` in [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) was not updated
- the wrong `config`, `model`, or `region` was used

`check` now reports this as `STALE_IDENTITY_LITERAL`.
If a foreign model mention is intentional, add it to `checks.allowed_foreign_identity_literals` in the config.

### 11.4 Hard-coded title in config

If `build.word_title` is fixed to an old model name, the generated Word title will stay wrong even if `PRODUCT_NAME` is correct.
Prefer a placeholder-based title such as:

```yaml
word_title: "|PRODUCT_NAME| User Manual"
```

---

## 12. Verification Checklist

After changing templates or CSV values, verify at least the following:

1. `python build.py check --config ...` succeeds
2. `python build.py doctor --config ... --model ... --region ...` reports no blocking errors for the current Word/PDF path
3. the target bundle appears under [`docs/_build/<model>/<region>/rst/`](../docs/_build)
4. the review bundle appears under [`docs/_review/<model>/<region>/`](../docs/_review)
5. generated pages contain no unresolved placeholders such as `|PRODUCT_NAME|`
6. generated pages contain no stale model names from older products
7. safety and spec still resolve from the intended source, including the JP template-backed safety page and the remaining CSV-backed generated pages
8. the expected `.docx`, `.html`, or `.pdf` file is generated when requested
9. `publish` or `release-manifest` produced a JSON / CSV record under [`reports/releases/<model>/<region>/`](../reports/releases)

Useful checks:

```powershell
Select-String -Path docs\_build\JE-1000F\US\rst\page\*.rst -Pattern '\|[A-Z0-9_]+\|'
Select-String -Path docs\_build\JE-1000F\US\rst\page\*.rst -Pattern '\?'
git status --short -- docs/_review/JE-1000F/US
```

---

## 13. One-Sentence Rule

Templates and CSV create the first draft.
[`docs/_review/**`](../docs/_review) becomes the target editing source after review starts.
[`docs/_build/**/**/rst/**`](../docs/_build) remains the runtime publish bundle behind the final outputs.
