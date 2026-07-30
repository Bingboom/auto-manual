---
name: local-publish-queue-run
description: Run the Feishu build-queue publish locally on this Mac as the CI bot, end to end — env assembly, local git-plane alignment, queue-row operations (Git_ref, re-triggering consumed rows), the CI-identical invocation, the three-part verification, IDML handoff-zip delivery, and second-host (K7) acceptance semantics. Use when CI cannot run (org Actions quota, runner outage), when a publish needs local diagnosis/repair iteration, when re-running an already-consumed queue row, or when preparing/validating the second-host handoff. NOT the normal path — the queue's home is the Hello-Docs mirror CI; code fixes always land in auto-manual (mirror rule).
---

# Local Publish Queue Run

The build queue's home is the Hello-Docs (business-plane) mirror CI. This
skill is the **local fallback and verification lane**: the same orchestrator,
run on this Mac with the bot identity, byte-for-byte the CI invocation. It
exists because the whole recipe (env set, queue-row semantics, verification
trio) previously lived only in operator recall — an 11-attempt publish night
proved that is too expensive.

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
- Direct Bitable row surgery shapes → `lark-cli-bitable-ops` (once merged; the
  queue-row recipes here are self-contained).
