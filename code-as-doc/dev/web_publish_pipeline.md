# Web Publish Pipeline

This document owns the release contract for responsive manuals published to
Read the Docs. Web delivery is intentionally separate from print delivery.

## 1. Two independent release actions

| `Workflow_action` | Worker | Output authority |
| --- | --- | --- |
| `Publish` | `feishu-build-queue.yml` | IDML, LaTeX, PDF, DOCX, formal Markdown and release manifests |
| `Web Publish` | `feishu-web-publish-queue.yml` | frozen MyST source under `Hello-Docs/publish:docs/publish/` and `HTML_link` |

`Publish` never deploys HTML. `Web Publish` never uploads or rewrites print
artifacts. Both actions render reviewed content selected by
`Document_link.Git_ref` with the current `main` toolchain.

## 2. Web Publish transaction

1. The business-plane worker claims only rows whose normalized action is
   `web_publish`; `Git_ref` is required.
2. It always runs live `sync-data` with the HT-Docs bot. Approved
   `04_资产导出物` rows are downloaded and hash-verified; unapproved or ambiguous
   Web composites fail closed.
3. The web presentation profile runs `check -> md -> html`. The HTML render is
   a verification output; the MyST directory is the durable publishing input.
4. `latest/web/publish_meta.json` records the target, version, review ref,
   queue rows, MyST source and verified HTML directory.
5. `publish_branch_assembly.py` copies that source into
   `docs/publish/sources/web/<model>/<region>/md/`, preserves other targets,
   rebuilds `docs/publish/web/`, and writes a SHA-256 inventory in
   `docs/publish/publish_manifest.json`.
6. The workflow advances `Hello-Docs/publish` with an ordinary non-force push.
   One global concurrency group serializes the complete build, branch update
   and writeback transaction.
7. The deterministic RTD manual URL is written to `Document_link.HTML_link`.
   A seven-day workflow artifact retains the Web release evidence; the Git
   branch remains the durable snapshot.

## 3. Repository and hosting boundaries

- Code changes land only in `Bingboom/auto-manual`, then
  `sync-hello-docs.yml` mirrors `main` into `Bingboom/Hello-Docs/main`.
- `Hello-Docs/publish` is a generated release branch. Operators do not edit it
  by hand, and it is not the GitHub repository's development default branch.
- The Read the Docs project uses `publish` as its default build branch and
  builds `docs/publish/web/` through `.readthedocs.yaml`.
- RTD never receives Feishu credentials and never reads mutable attachments.
  It renders only the frozen, hash-inventoried Git snapshot.

The first Web Publish creates `publish` from the current business-plane `main`.
Later runs retain the existing target sources, refresh the tracked code/config
tree to current `main`, replace only the newly published target, and append a
normal commit. A non-fast-forward push fails instead of overwriting another
publisher.

## 4. Operator contract

Before dispatch, the `Document_link` row must have:

- `Workflow_action = Web Publish`
- `Git_ref = <review branch>`
- `是否触发文档构建 = Y`
- `是否立即构建 = checked` when immediate dispatch is required

For a composite figure plus its governed copy, the matching
`04_资产导出物` row must have one `export_file`, a selected `web_locale`, valid
`content_sha256` and `source_fragment_sha256`,
`artifact_kind = web-composite`, `gate_status = approved`,
`build_eligible = true`, and `visual_review_required = false`.

Success requires all three pieces of evidence:

- the GitHub run is green;
- `Hello-Docs/publish` contains the expected target and manifest hashes;
- the RTD page opens and `HTML_link` points to that exact route.

## 5. Rollback

Do not force-push `publish`. Re-run Web Publish from the approved review ref and
asset rows to append a corrected snapshot. For an urgent hosting rollback,
revert the bad publish commit with a normal commit, verify the generated
manifest, and let the publish-branch webhook rebuild RTD.
