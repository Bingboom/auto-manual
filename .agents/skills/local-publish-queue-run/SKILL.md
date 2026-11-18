---
name: local-publish-queue-run
description: "Maintenance only. Diagnose a retired template queue publish locally, or replay one existing target with explicit emergency authorization. An Actions outage alone does not authorize a local run."
metadata:
  owner: "发布维护人"
  status: "maintenance"
  entry: "单独授权后复现存量模板队列的本地发布故障"
  tools: "build.py process-build-queue、references/run-recipe.md"
  validation: "用隔离行和 dry-run 核对目标与动作，再按授权范围验收"
  reviewed: "2026-11-17"
  retire_when: "存量队列不再需要本地复现或应急重放"
---

# Local Publish Queue Run

Use only for explicitly authorized emergency replay or diagnosis of an existing template queue target. A disabled workflow is not permission to consume a row locally. The [queue retirement contract](../../../code-as-doc/build_doc_guide/queues.md) governs the scope of a replay.

Two-plane discipline still applies: this lane *runs* builds locally; any code
fix it uncovers is a normal auto-manual branch/PR (never a push to the
mirror), and any source-table change goes through its own approval gate.

## The spine

```
1. Env       — bot identity + the full FEISHU_PHASE2_* set (mirror of
               .github/workflows/feishu-build-queue.yml); view ids mandatory
2. Git plane — git branch -f main origin/main; phase2 mirror present
3. Queue row — row's Git_ref field decides the ref; consumed rows flip
               是否触发文档构建 back to Y (+ force data refresh)
4. Run       — PYTHONUNBUFFERED=1 python -u build.py process-build-queue \
                 --config configs/config.us.yaml --data-root data/phase2 \
                 --workflow-action publish [--record-id <rid>] [--dry-run]
5. Verify    — artifacts + wiki upload + row write-back (all three, always)
6. Deliver   — handoff zip contract; LOCAL naming for local iterations
7. Accept    — second host per code-as-doc/dev/indesign_second_host_runbook.md;
               equivalence = baseline-report match, NOT overset=0
```

Details, exact env names, and the failure-triage index live in
`references/run-recipe.md` — keep it open while running.

## Non-negotiables

- **Dry-run first** when touching a row you didn't create; the queue consumes
  rows, and a wrong consume needs manual row surgery to undo.
- **Verify all three outputs** (artifacts on disk, knowledge-base upload,
  row field write-back) before reporting success — a green orchestrator exit
  with a missing `idml_file` write-back is a failed publish.
- **Never run `tools/reference_layout_rebind.py --write`** to get past the
  reference-contract gate — rebinding an approved layout contract is an
  operator approval decision.
- Secrets arrive via clipboard (`pbpaste`), are exported into the shell only,
  and are masked in any echo/log.

## Boundaries

- Queue/watchdog *services* and their PowerShell wrappers → `scripts/`
  (`listen_build_queue.ps1`, `process_build_queue*.ps1`) — this skill is the
  interactive one-shot lane, not the resident service.
- Backporting reviewer edits found in the built doc → `cloud-doc-backport-ops`.
- Direct Bitable row surgery shapes → `lark-cli-bitable-ops`.
