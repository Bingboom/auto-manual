---
name: cloud-doc-backport-ops
description: Run a review cloud-doc backport ROUND end to end — the round-level SOP wrapping tools/cloud_doc_backport.py. Use whenever the operator hands a Feishu review cloud-doc (wiki/docx URL) and wants its reviewer edits reflected back into the repo/review branch/source tables — trigger phrases 「执行回写」+URL, "backport this doc", 「云文档回写」, or a build-table InReview sweep. Owns the preflight (snapshot/lang/baseline), run-review-branch dry-run→write→push, per-delta routing (review page vs source-table F6 via apply-source-table vs template PR vs debt), the MANDATORY post-apply checks (deletion sweep, symmetric-term pairs, per-write readback), final rediff-to-zero, and baseline re-snapshot. NOT for .docx tracked-changes revisions (use manual-revision-backport) and NOT spec-sheet onboarding (use spec-sheet-structured-intake).
---

# Cloud-Doc Backport Ops (round-level SOP)

A reviewer edits the **review cloud doc** (Feishu docx generated from a review
branch). Your job is one complete backport **round**: pull those edits back into
the right sources, prove nothing was missed (especially deletions), and advance
the baseline so the next round diffs cleanly.

`AGENTS.md` §3 documents the single command; this skill owns everything around
it that past rounds proved memory cannot hold: the preflight, the routing
decisions, the post-apply sweeps, and the baseline mechanics. Keep
`references/round-runbook.md` open while you work; run every item of
`references/post-apply-checklist.md` before calling a round done.

## Core principles

1. **The review tree lives on the review branch, not main.** Resolve first
   (`resolve-review-branch` / `run-review-branch` does it for you); never diff a
   cloud doc against the default branch's `docs/_review`.
2. **Deletions are the blind spot.** The apply/gate machinery is built around
   text replacement; whole-table / whole-section deletions get mis-aligned or
   abstained — and an abstained delete is **not noise**. Every "delete" delta is
   verified against the built artifact / cloud doc before it may be skipped, and
   every round ends with a dedicated deletion sweep. (Two real escapes: a
   deleted table resurrected on the next build; a "疑似 diff 错位" verdict that
   hid a real deletion and shipped a duplicated 「安全上のご注意」.)
3. **Exact-or-abstain abstaining is correct behavior, not failure.** Composite
   edits (rename + reorder across rows) will abstain by design — the round
   continues with manual record_id mapping. Don't force the tool to eat
   restructuring reviews.
4. **One writable surface per route.** The backport tool writes only the
   worktree's `docs/_review/...`. Source-table fixes go through the
   approval-gated F6 `apply-source-table` path; shared-template fixes go
   through a normal template PR **plus** propagation to in-flight review
   branches. Never hand-edit `docs/templates/`, `data/phase2/`, or a source
   table directly "because the backport found it".
5. **Every write is read back.** Source-table writes report record_id + field
   and are GET-verified (writes land with seconds of lag — sleep, then verify).
   "Applied" without a readback is unproven.
6. **A round ends at rediff = 0 AND baseline advanced.** deltas=0 on re-run,
   then re-snapshot the frozen baseline copy and repoint the build-table row —
   otherwise the same deltas re-report forever (the seed file is the *lower*
   priority baseline; see runbook).

## Default round

```
0. Preflight   — resolve branch, ensure worktree, check data snapshot + --lang
1. Dry-run     — run-review-branch (no --write), read the full report
2. Route       — classify every delta with the routing tree (runbook §3)
3. Apply       — --write (review pages) / apply-source-table --approve … --write
                 (F6, operator-approved per delta) / template PR + propagation
4. Post-apply  — references/post-apply-checklist.md (deletion sweep, pairs,
                 readback) — MANDATORY, not optional polish
5. Re-verify   — re-run dry-run until deltas=0 (NO_DIFF)
6. Baseline    — wiki +node-copy re-snapshot + build-table row repoint
7. PR          — --push opens backport/<...> sub-branch PR INTO the review
                 branch; operator merges. Never commit straight onto it.
```

The short-instruction contract: when the operator sends 「执行回写 <URL>」 (or
just a review cloud-doc URL with "回写"), execute this default round, surfacing
route decisions and F6 approvals as you reach them.

## Boundaries

- `.docx` tracked-changes revision file → **manual-revision-backport** (it
  shares the post-apply checklist in this skill's `references/`).
- New model/region spec onboarding → **spec-sheet-structured-intake**.
- Data-driven refresh of an in-review target without reviewer edits →
  `sync-review` (AGENTS.md §3), not a backport round.
- Multi-doc sweep trigger: build table (document_link) InReview rows are the
  authoritative to-recover list; `sync-review-worktrees` ensures a worktree per
  in-review branch.

## Use bundled resources

- `references/round-runbook.md` — preflight details, the delta routing tree
  (incl. the F6 `apply-source-table` forward recipe), rediff limits, baseline
  re-snapshot mechanics, worktree hygiene.
- `references/post-apply-checklist.md` — the mandatory post-apply gate; shared
  verbatim with manual-revision-backport.
