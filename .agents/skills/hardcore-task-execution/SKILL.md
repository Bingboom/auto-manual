---
name: hardcore-task-execution
description: Execute large or high-risk repository work as small, observable, reversible phases with a discovery report, safety net, mechanical edits, and a cheap-to-expensive verification ladder. Use for full-repo reviews with fixes, refactors, migrations, format changes, release artifacts, or any task where silent regressions are expensive.
---

# Hardcore Task Execution

Treat a large task as a sequence of small changes, each one provable and reversible.

## 1. Decompose before editing

- Partition unknowns into disjoint read-only questions and map the load-bearing entrypoints, contracts, and traps.
- Re-read every fact that the implementation plan depends on; summaries are leads, not evidence.
- Write a discovery report and an implementation plan before production edits. Include non-goals, per-phase files, safety nets, and verification commands.
- If the scope becomes roughly three times larger than expected, stop and report the new scope.

## 2. Build a safety net first

- Characterize current behavior through the real user-facing entrypoint, not an internal shortcut.
- Compare output exactly and normalize only genuine nondeterminism. Do not regenerate a golden baseline during a pure refactor.
- Treat maintainability size limits as one-way ratchets; raise a threshold only with a documented reason in the same change.

## 3. Make risky edits mechanical

- Anchor verbatim moves with assertions that fail if the source shifted.
- Use word-boundary scripted renames instead of broad replacement.
- Move contracts and the comments explaining them together.
- Preserve callers with compatibility façades and test the public surface plus one-way imports.

See `references/recipes.md` for reusable patterns.

## 4. Verify on a ladder

Run the cheapest applicable check first, then climb only when it passes:

1. Ruff or syntax checks.
2. Targeted tests.
3. Full unit suite.
4. Structural guardrails and parity tests.
5. Documentation link/integrity checks.
6. Build or quality-gate commands.
7. Golden artifact comparison.

Report the actual failing command and output; never summarize an unrun or failing check as green.

## 5. Keep phases reversible

- Use one branch per task and one logically complete phase per commit/PR.
- Do not commit directly to `main`, force-push, delete generated or review artifacts, change public CLI signatures, schemas, or dependencies without explicit confirmation.
- Re-inventory assumptions before each remaining phase if another change lands.

## 6. Close the loop

- Update the owning docs when workflow or editing surfaces change.
- Record non-obvious traps with their reason and keep deferred work in a follow-up ledger.
