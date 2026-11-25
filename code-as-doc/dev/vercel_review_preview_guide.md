# Vercel Latest Publish HTML Guide

Status: active

Updated: 2026-11-16

This guide defines the current Vercel publishing flow.
It now hosts the latest queue-driven Publish HTML only.

## 1. Goal

Use this flow when:

- a `Document_link` row reaches `Workflow_action = Publish` or legacy `Doc_phase = Publish`
- the final Publish designer handoff ZIP should be uploaded to Feishu / wiki and
  written to `idml_file`
- Vercel should expose only the newest published HTML

This keeps the responsibilities separate:

- Feishu / wiki: Publish handoff ZIP distribution and `idml_file` writeback
- `reports/releases/`: staged release artifacts and latest publish HTML snapshot
- Vercel: static hosting for the newest publish HTML

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

1. runs `python build.py process-build-queue --config configs/config.us.yaml --workflow-action publish`
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
- stages rendered HTML pages and their local dependencies into `site/publish-latest/dist`:
  HTML/SVG resource links, linked downloads, CSS imports/images/fonts, literal
  local JS/JSON asset references, and Sphinx's `searchindex.js`
- preserves each selected file's URL and bytes; unused source/print PDFs,
  unreferenced images and Sphinx build state are not copied
- rejects missing explicit local resources, HTML base URL overrides and links
  escaping the target's HTML root, rather than producing an incomplete preview
- copies `publish_meta.json` into `site/publish-latest/dist/generated/`

The Vercel adapter applies the same collection to an already staged site before
reusing it. It validates into a temporary directory first, so a missing resource
leaves the original staged site intact. Per-target/root publish metadata survives
this pass. JavaScript references assembled dynamically must resolve to files
already linked by a page, stylesheet or literal JS/JSON filename; generated
previews should be checked with their actual runtime assets before delivery.

The old `review-preview.yml` / `review-preview-workspace` artifact route is
retired. Do not restore whole-workspace uploads to obtain a preview. Temporary
Actions inspection copies keep 3 days; formal print Publish delivery copies keep
7 days. The independent phase2 restore backup retains 90 days. See the
[artifact policy tests](../../tests/test_workflow_artifact_policy.py).

## 5. Maintainer Rule

When you reason about hosted output, keep this split:

- Draft: working output under `docs/_build/` by default, or under `<staging-root>/docs/_build/` during isolated local verification
- Publish DOCX: staged under `reports/releases/.../versions/.../`
- Latest publish HTML: staged under `reports/releases/.../latest/html/` and hosted by Vercel

Do not treat Vercel as the source of truth for packaging.
Let GitHub Actions prepare the static publish site first, then let Vercel host it.
