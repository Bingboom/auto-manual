# Vercel Review Preview Guide

Updated: 2026-03-24

This guide defines the current review-preview publishing flow for design collaboration.
It is for the review stage, not the final release stage.

## 1. Goal

Use this flow when:

- the manual is already being edited under [`docs/_review/<model>/<region>/`](../../docs/_review)
- design needs to see the rendered HTML result, not raw `.rst`
- design also needs to know what changed in the current review round

The preview package combines:

- review-based HTML from [`docs/_build/<model>/<region>/html/`](../../docs/_build)
- review-based Word from [`docs/_build/<model>/<region>/word/`](../../docs/_build)
- diff-report HTML / CSV from [`reports/version_tracking/<model>/<region>/`](../../reports/version_tracking)
- a workspace root that links families, models, and languages together

## 2. Current Entry Point

Use:

```powershell
python tools/process_docs/build_review_preview.py --config config.yaml --model JE-1000F --region US --source review --from-ref HEAD~1 --to-ref HEAD
```

Default output:

- [`site/review-preview/dist/`](../../site/review-preview/dist)

Generated structure:

- `index.html`: workspace root for design
- `manual/`: rendered review HTML, grouped by family and model
- `changes/`: family-level diff pages plus a compatibility redirect at `changes/index.html`
- `manual/index.html` and `changes/index.html`: compatibility redirects to the default workspace entries
- `downloads/`: family-scoped `review-manual.docx`, `change-report.xlsx`, `changes-summary.csv`, `changes-pages.csv`, `changes-fields.csv`, `changes-files.csv`
- `generated/meta.json`: branch / commit / author metadata plus download metadata
- `generated/changes.json`: changed files, review pages, grouped change areas, and download metadata
- `generated/workspace.json`: workspace data for family tabs, model groups, and language switching

The workspace is intentionally designer-facing:

- it tells design what to open first
- it separates rendered manual review from family-level change tracing
- it offers direct Word / Excel handoff downloads for offline review meetings
- it explains whether the current round contains page-level review edits or mostly workflow / docs changes
- it hides families that do not have `_review` content for the current round

## 3. Why This Uses Review Content

After review starts, the durable editing surface is:

- [`docs/_review/<model>/<region>/`](../../docs/_review)

For that reason, the preview package intentionally uses:

- `python build.py html --source review`

This keeps the preview aligned with the text that is actually being edited and versioned for review.

## 4. Why This Uses diff-report

The repo already has a useful change-report pipeline:

- `python build.py diff-report`

For review collaboration, the most useful outputs are:

- `*_index.html`
- `*_fields.html`
- `*_pages.html`
- `*_files.html`

The preview package copies the latest report set into stable paths under `changes/<family>/` so design can open:

- `changes/<family>/index.html`
- `changes/<family>/report-fields.html`
- `changes/<family>/report-pages.html`
- `changes/<family>/report-files.html`

It also copies the diff CSV set under `downloads/<family>/` and builds one Excel workbook from the same inputs:

- `downloads/changes-summary.csv`
- `downloads/changes-pages.csv`
- `downloads/changes-fields.csv`
- `downloads/changes-files.csv`
- `downloads/change-report.xlsx`

The Excel workbook is only a packaging layer over the existing diff CSV outputs.
It does not introduce a second change model.
These diff, workbook, and CSV files stay family-level shared assets across the languages in that family.

## 5. GitHub Actions Role

Current workflow:

- [`../../.github/workflows/review-preview.yml`](../../.github/workflows/review-preview.yml)

It does not gate merge.
It installs `pandoc`, packages the same review preview bundle in CI, uploads it as an artifact, and deploys the static output to Vercel through `vercel pull -> vercel build -> vercel deploy --prebuilt`.

This keeps the responsibilities separate:

- `Manual Validation`: machine validation and merge gating
- `Review Preview Package`: render-and-share packaging for collaboration

Practical maintainer rule:

- keep a pull request open for the working review branch
- after that, each matching push to the PR branch reruns `Review Preview Package`
- once the workflow succeeds, the Vercel preview reflects the latest review round automatically
- if there is no PR yet, use `workflow_dispatch` to run it manually
- make sure `VERCEL_TOKEN`, `VERCEL_ORG_ID`, and `VERCEL_PROJECT_ID` are configured in repository secrets before expecting the deploy step to run

## 6. Vercel Role

Vercel should publish the generated static package only.

Recommended published directory:

- `site/review-preview/dist`

Current repo-level Vercel config:

- [`../../vercel.json`](../../vercel.json)

Current first-phase Vercel build target:

- `config.yaml`
- `JE-1000F`
- `US`
- `source=review`

Vercel build note:

- GitHub Actions builds the review preview package first and treats the package contract as required
- `review-manual.docx` and `change-report.xlsx` are required artifacts in CI; a missing download blocks preview deployment
- GitHub Actions then runs `vercel pull`, `vercel build`, and `vercel deploy --prebuilt`
- Vercel should not be the source of truth for packaging; disable or stop relying on Git-triggered Vercel builds for this flow

Do not ask Vercel to render raw `.rst`.
Let the repo generate review HTML first, then let Vercel host the resulting static package.

Vercel should be used for:

- preview URL distribution
- lightweight design review sharing
- showing branch / commit / author metadata on the workspace root

Vercel should not be used as a required merge-gating check for this repo.

## 7. First-Phase Scope

Current first-phase target:

- `JE-1000F` workspace with `US`, `JP`, and `EU` families when those `_review` roots exist

Later expansion can add:

- more models inside each family
- richer workspace filters and deep links

Do not expand the scope until the workspace flow is stable.
