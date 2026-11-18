---
name: hello-docs-pipeline-dispatch-triage
description: "Maintenance only. Inspect a historical Hello-Docs template queue run or an explicitly authorized emergency replay. Use the current release contract for Git-only Web publication."
metadata:
  owner: "发布维护人"
  status: "maintenance"
  entry: "诊断既有模板队列运行，按单独授权应急重放"
  tools: "gh run view、历史 Feishu Actions、队列退役契约"
  validation: "读取一次历史运行，区分平台禁用、任务跳过与真实执行"
  reviewed: "2026-11-17"
  retire_when: "历史运行诊断和应急重放均移交或下线"
---

# Hello-Docs Pipeline Dispatch & Triage

Inspect historical Hello-Docs queue runs. Dispatch or retry only for an explicitly authorized emergency replay of an existing target after checking the retirement controls. The [queue retirement contract](../../../code-as-doc/build_doc_guide/queues.md) names the disabled workflows. Confirm the specific replay was authorized, the workflow is enabled for it and `LEGACY_TEMPLATE_QUEUE_ENABLED` is `true` before using the dispatch or retry recipes. Ordinary Git-only Web release and main mirror synchronization have their own workflows.

## The routing rule (hard, operator-corrected twice)

**Code (tools/templates/configs/workflows) is NEVER PR'd to Hello-Docs.** It
lands in auto-manual `main` and flows to the mirror automatically via
`sync-hello-docs.yml`. That sync preserves the business-owned
`Hello-Docs/main:docs/publish/**` subtree instead of overwriting it.

Legitimate mirror PRs are limited to two data-plane cases:

1. `backport/...` sub-branches into a `review/*` branch for reviewer-edit
   recovery;
2. the generated `publish -> main` Web release PR, whose diff must contain only
   `docs/publish/**`.

Never merge a whole `review/*` branch into `main`. Before opening any other PR,
state which plane it belongs to; when a code fix spans both, the answer remains
"auto-manual, then let sync carry it" (「代码一律在 auto-manual 改,
hello-docs 是镜像」).

## Semantics card (what each workflow actually produces)

| Workflow (same filenames both repos; run on the MIRROR) | Produces |
| --- | --- |
| `feishu-start-review.yml` | Seeds/re-seeds a `review/<MODEL>-<REGION>` branch with the `docs/_review` RST tree — **no document output**. 重新播种 = this. Re-seed moves the branch tip: open backport sub-branches go DIRTY (reset onto new tip + replay). |
| `feishu-draft-build-queue.yml` | Builds the draft package for queue rows (Workflow_action = Build Draft Package) — the review Word/cloud doc. |
| `feishu-build-queue.yml` | Publish lane (Workflow_action = Publish): release artifacts, IDML handoff zip, row write-backs. |
| `feishu-web-publish-queue.yml` | Web Publish lane: builds from the selected review ref, updates the generated `publish` candidate, enforces a `docs/publish/**`-only diff, and opens/updates `publish -> main`. It never merges the review branch. |
| `feishu-schema-parity.yml` / `phase2-content-backup.yml` / `backport-reminder.yml` | Source-table backup remains scheduled. The schema parity and backport reminder workflows are retained for emergency replay. |

An authorized emergency replay also respects `FEISHU_BUILD_QUEUE_PAUSED` (repo var).
Queue rows live in the build table (`document_link`, `tblbnRHjpJeCVTtj`,
business base) — row ops per `lark-cli-bitable-ops`.

## Dispatch

```bash
# one row (draft lane; publish lane = feishu-build-queue.yml)
gh workflow run feishu-draft-build-queue.yml --repo Bingboom/Hello-Docs -f queue_record_id=<rid>
# seed / re-seed a review line
gh workflow run feishu-start-review.yml --repo Bingboom/Hello-Docs
# then watch:
gh run list --repo Bingboom/Hello-Docs --workflow=<wf> --limit 3
gh run watch <run_id> --repo Bingboom/Hello-Docs   # or background-poll
```

Monitor to **settled**, then verify the produced artifact (row write-back /
branch tip / uploaded doc) — a green run is not the deliverable. Distinguish
`cancelled` from `failure` before diagnosing anything.

## Retry ladder (cheapest first, each rung has a side-effect)

1. **Plain re-dispatch** with the same `queue_record_id` — only works while
   the row still says 是否触发文档构建=`Y`.
2. **Row re-arm**: consumed rows (`已构建`) refuse `--record-id`; flip back to
   `Y` via `+record-batch-update`. If `data_sync=refreshed`, ALSO tick
   `是否强制刷新数据` or the fresh worktree misses `Spec_Master.csv`.
3. **Re-seed (Start Review)** — refreshes the review branch content from
   source; required after source-table corrections (localized value columns),
   destructive to un-backported reviewer edits: confirm the review doc has
   been recovered first (backport round) before re-seeding.

## Failure-signature triage (symptom → first look)

| Signature | First look |
| --- | --- |
| `queue_config_resolution: No config family matches` | Row `Lang` empty (single-language regions need `Lang=en`) or the region's config/manifest never merged to auto-manual main (mirror main lags = sync didn't run) |
| `MISSING_SPEC_MASTER` / validate failures | Retry rung 2's force-refresh; or the target was never ingested |
| Sentinel Issue opened (title carries record_id) | K5 failure sentinel — the issue body carries the writeback divergence; treat the issue as the per-record lifecycle thread |
| Run queued forever | Org Actions quota — switch to the local lane (`local-publish-queue-run`) |
| Build green but content stale | The row rebuilt an old `Git_ref`; check the row's ref field vs the review branch tip |
| Review-branch LaTeX-only crash in publish | De-templated review pages (raw tabular / SVG / prose outside macros) — fix on the review branch via backport sub-branch, not templates |
| Mirror behaves unlike auto-manual | Check the last `sync-hello-docs.yml` run — the mirror is only as new as its last sync |
| PR shows `no checks reported`; push / close-reopen / empty commits all trigger nothing | `gh pr view <n> --json mergeable` FIRST — `CONFLICTING` silently disables every PR-event workflow (see below) |

### `mergeable=CONFLICTING` = silent CI no-op (either repo)

When a PR conflicts with its base, GitHub cannot create the `refs/pull/N/merge`
merge commit, so every `pull_request`-event workflow silently never starts:
no failed run, no queued run, nothing for a push, close/reopen, or empty
commit to re-trigger. Do not waste rungs on re-dispatch — check
`gh pr view <n> --json mergeable` before anything else when a PR sits at
`no checks reported`. Fix on the PR branch, not in the workflows: rebase onto
`origin/main`, resolve the conflict, `git push --force-with-lease`; the moment
`mergeable` recovers, checks fire on their own. Proven 2026-07-31 on
auto-manual #816/#819 (`merge_authorizations.md` conflicted with a `main`
squash-merge).

Always end a triage with: root cause, which plane the fix belongs to, and the
re-run evidence (run URL + verified artifact).
