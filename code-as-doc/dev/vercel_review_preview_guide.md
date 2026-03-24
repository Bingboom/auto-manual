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
It is the build system for review preview publishing.

Current CI responsibilities:

- build the review HTML package from `_review`
- generate the matching `diff-report`
- upload the packaged preview as a GitHub artifact
- convert the packaged site into `.vercel/output/static`
- deploy the static result to Vercel with `vercel deploy --prebuilt`
- comment preview links back onto the pull request

This keeps the responsibilities separate:

- `Manual Validation`: machine validation and merge gating
- `Review Preview`: render, package, and deploy preview-only collaboration output

Required repo secrets for Vercel deployment:

- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

One-time setup rule:

- create one dedicated Vercel project for review preview hosting
- connect it to this repository only for project identity
- do not rely on Vercel Git auto-builds for preview generation

## 6. Vercel Role

Vercel should host the generated static package only.

Recommended published surface:

- `/`: summary page
- `/manual/index.html`: rendered review HTML
- `/changes/index.html`: diff-report landing page

Current repo-level Vercel config:

- [`../../vercel.json`](../../vercel.json)

Current role of that config:

- disable Git-triggered Vercel deployments for this repo
- keep Vercel out of the review-preview build path

Do not ask Vercel to render raw `.rst`.
Do not ask Vercel to run the review-preview Python build.
Let GitHub Actions build the review HTML and `diff-report` first, then let Vercel host the prebuilt static output.

Vercel should be used for:

- preview URL distribution
- lightweight design review sharing
- showing branch / commit / author metadata on the summary page

Vercel should not be used as:

- the build environment for this repo's review preview
- a required merge-gating check for this repo

If a Vercel project is still connected to the repo's Git auto-deploy flow, disconnect that behavior in the project settings.
The intended model is:

- GitHub Actions builds and deploys
- Vercel serves the deployed static output

## 7. First-Phase Scope

Current first-phase target:

- `JE-1000F / US`

Later expansion can add:

- `JE-1000F / JP`
- `JE-1000F / EU`
- a target selector on the summary page

Do not expand the scope until the first single-target flow is stable.
