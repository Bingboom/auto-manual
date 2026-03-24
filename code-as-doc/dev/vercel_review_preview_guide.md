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
- diff-report HTML from [`reports/version_tracking/<model>/<region>/`](../../reports/version_tracking)
- a small summary page that links both surfaces together

## 2. Current Entry Point

Use:

```powershell
python tools/process_docs/build_review_preview.py --config config.yaml --model JE-1000F --region US --source review --from-ref HEAD~1 --to-ref HEAD
```

Default output:

- [`site/review-preview/dist/`](../../site/review-preview/dist)

Generated structure:

- `index.html`: summary page for design
- `manual/`: rendered review HTML
- `changes/`: diff-report HTML plus a simple landing page
- `generated/meta.json`: branch / commit / author metadata
- `generated/changes.json`: changed files, review pages, and grouped change areas

The current summary page is intentionally designer-facing:

- it tells design what to open first
- it separates rendered manual review from change tracing
- it explains whether the current round contains page-level review edits or mostly workflow / docs changes

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

The preview package copies the latest report set into stable paths under `changes/` so design can open:

- `changes/index.html`
- `changes/fields.html`
- `changes/pages.html`
- `changes/files.html`

## 5. GitHub Actions Role

Current workflow:

- [`../../.github/workflows/review-preview.yml`](../../.github/workflows/review-preview.yml)

It does not gate merge.
It packages the same review preview bundle in CI, uploads it as an artifact, and deploys the static output to Vercel.

This keeps the responsibilities separate:

- `Manual Validation`: machine validation and merge gating
- `Review Preview Package`: render-and-share packaging for collaboration

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

- GitHub Actions builds the review preview package and prepares `.vercel/output/static`
- GitHub Actions then deploys the prebuilt static output to Vercel with the CLI
- Vercel should not run the Python build itself for this flow

Do not ask Vercel to render raw `.rst`.
Let the repo generate review HTML first, then let Vercel host the resulting static package.

Vercel should be used for:

- preview URL distribution
- lightweight design review sharing
- showing branch / commit / author metadata on the summary page

Vercel should not be used as a required merge-gating check for this repo.

## 7. First-Phase Scope

Current first-phase target:

- `JE-1000F / US`

Later expansion can add:

- `JE-1000F / JP`
- `JE-1000F / EU`
- a target selector on the summary page

Do not expand the scope until the first single-target flow is stable.
