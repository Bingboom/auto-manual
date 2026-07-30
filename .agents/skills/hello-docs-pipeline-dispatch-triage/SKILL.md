---
name: hello-docs-pipeline-dispatch-triage
description: Operate the Hello-Docs (business-plane mirror) build pipeline — dispatch Start Review / Draft / Publish / 重播种 runs, monitor them, and triage failures by signature — plus the hard mirror-PR routing rule (code changes NEVER target the mirror's main; they land in auto-manual and auto-sync). Use for requests like 「触发US的重新播种」「你现在 publish JE-1000F_US_1.7」「这个 run 失败了 排查修复」, a pasted Actions run URL, or any dispatch/monitor/retry work on the mirror. NOT the local publish lane (local-publish-queue-run) and NOT plane topology background (user-guide/two_plane_map.md).
---

# Hello-Docs Pipeline Dispatch & Triage

The business plane runs on the Bingboom/Hello-Docs mirror; every dispatch /
retry / failure-triage round used to start with the operator re-explaining
workflow names, queue-table coordinates, and retry semantics. This skill holds
the operating layer. Topology background is `user-guide/two_plane_map.md`;
running the queue locally instead is `local-publish-queue-run`.

## The routing rule (hard, operator-corrected twice)

**Code (tools/templates/configs/workflows) is NEVER PR'd to Hello-Docs.** It
lands in auto-manual `main` and flows to the mirror automatically via
`sync-hello-docs.yml` (push-triggered, exact-tree mirror). The ONLY legitimate
PRs on the mirror are **data-plane derivatives**: `backport/...` sub-branches
into a `review/*` branch (reviewer-edit recovery). Before opening ANY PR,
state which plane it belongs to; when a fix spans both, the answer is always
"auto-manual, then let sync carry it" (「代码一律在 auto-manual 改,
hello-docs 是镜像」).

## Semantics card (what each workflow actually produces)

| Workflow (same filenames both repos; run on the MIRROR) | Produces |
| --- | --- |
| `feishu-start-review.yml` | Seeds/re-seeds a `review/<MODEL>-<REGION>` branch with the `docs/_review` RST tree — **no document output**. 重新播种 = this. Re-seed moves the branch tip: open backport sub-branches go DIRTY (reset onto new tip + replay). |
| `feishu-draft-build-queue.yml` | Builds the draft package for queue rows (Workflow_action = Build Draft Package) — the review Word/cloud doc. |
| `feishu-build-queue.yml` | Publish lane (Workflow_action = Publish): release artifacts, IDML handoff zip, row write-backs. |
| `feishu-schema-parity.yml` / `phase2-content-backup.yml` / `backport-reminder.yml` | Daily guards: schema parity alarm, nightly source-table backup, un-recovered-review sentinel. |

Gating var: mirror runs respect `FEISHU_BUILD_QUEUE_PAUSED` (repo var).
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

Always end a triage with: root cause, which plane the fix belongs to, and the
re-run evidence (run URL + verified artifact).
