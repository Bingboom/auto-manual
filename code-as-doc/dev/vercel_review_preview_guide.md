# Vercel Latest Publish HTML Guide

Updated: 2026-04-04

This guide defines the current Vercel publishing flow.
Vercel no longer hosts the PR review-preview workspace.
It now hosts the latest queue-driven Publish HTML only.

## 1. Goal

Use this flow when:

- a `Document_link` row reaches `Doc_phase = Publish`
- the final Publish DOCX should be uploaded to Feishu / wiki
- Vercel should expose only the newest published HTML

This keeps the responsibilities separate:

- Feishu / wiki: final DOCX distribution and document link writeback
- `reports/releases/`: staged release artifacts and latest publish HTML snapshot
- Vercel: static hosting for the newest publish HTML
- `Review Preview Package`: design-sharing artifact only

## 2. Source Layout

Queue-driven Publish now stages release artifacts under:

- `reports/releases/<model>/<region>/<lang>/versions/<version>/`
- `reports/releases/<model>/<region>/<lang>/latest/html/`

Example:

- `reports/releases/JE-1000F/US/en/versions/0.2/manual_je1000f_us_en_publish_0.2.docx`
- `reports/releases/JE-1000F/US/en/latest/html/index.html`
- `reports/releases/JE-1000F/US/en/latest/publish_meta.json`

`publish_meta.json` is the handoff contract between the Publish queue and the Vercel site builder.

## 3. GitHub Actions Role

Current Publish worker:

- [`.github/workflows/feishu-build-queue.yml`](../../.github/workflows/feishu-build-queue.yml)

After a successful queue-driven Publish row, it now:

1. runs `python build.py process-build-queue --config config.us.yaml --doc-phase publish`
2. stages the DOCX and latest HTML snapshot under `reports/releases/...`
3. builds `site/publish-latest/dist/`
4. runs `vercel pull`
5. runs `vercel build`
6. runs `vercel deploy --prebuilt`

Required repository secrets:

- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

## 4. Vercel Build Entrypoints

Current repo-level Vercel config:

- [`../../vercel.json`](../../vercel.json)

It points to:

- build command: [`../../tools/process_docs/vercel_build_publish_latest.py`](../../tools/process_docs/vercel_build_publish_latest.py)
- output directory: `site/publish-latest/dist`

Static site assembly is handled by:

- [`../../tools/process_docs/build_publish_latest_site.py`](../../tools/process_docs/build_publish_latest_site.py)

That builder:

- scans `reports/releases/*/*/*/latest/publish_meta.json`
- picks the newest publish snapshot by `built_at`
- copies that HTML tree into `site/publish-latest/dist`
- copies `publish_meta.json` into `site/publish-latest/dist/generated/`

## 5. Review Preview Role

Current review-sharing worker:

- [`.github/workflows/review-preview.yml`](../../.github/workflows/review-preview.yml)

It still packages:

- review HTML
- review Word
- diff-report HTML / CSV / XLSX

But it now uploads that package as a GitHub artifact only.
It no longer deploys review-preview content to Vercel.

## 6. Maintainer Rule

When you reason about hosted output, keep this split:

- Draft: working output under `docs/_build/`
- Review preview: artifact under `site/review-preview/dist/`
- Publish DOCX: staged under `reports/releases/.../versions/.../`
- Latest publish HTML: staged under `reports/releases/.../latest/html/` and hosted by Vercel

Do not point Vercel back at `site/review-preview/dist`.
Do not treat Vercel as the source of truth for packaging.
Let GitHub Actions prepare the static publish site first, then let Vercel host it.
