---
description: A working method for large, high-stakes, multi-step engineering tasks — decomposing them into provable steps, building a safety net before changing anything, making risky edits mechanical rather than manual, verifying on a cheap-to-expensive ladder, and deciding when to keep going versus stop and ask. Use this whenever a task is big enough that you cannot hold the whole thing in your head at once, whenever you are refactoring or moving code that must not change behavior, whenever a task will span several commits or PRs, or whenever the cost of a silent mistake is high (shipped output, released artifacts, data migrations, format contracts). Reach for it even when the user just says "refactor this", "clean this up", "split this file", "migrate X", or "do a full review and fix what you find" — those are exactly the tasks that go wrong without a method.
when_to_use: Trigger on large refactors, monolith decomposition, "split this file", multi-PR work, behavior-preserving code moves, format/serialization changes, full-repo reviews with fixes, data or schema migrations, or any task where a mistake is expensive to unwind. Also when you feel the urge to "just start editing" a task you cannot fully see yet — that urge is the signal to load this first.
argument-hint: "[optional: the task or the phase you're on]"
---

# Hardcore Task Execution

A big task is not a big edit. It is a sequence of small changes, each one *provable* and *reversible*. The whole method below exists to earn the right to make each change: before you touch anything you cannot fully see, you first make the change observable (a test that will scream if you break it) and small (one revertable unit). Speed comes from never having to backtrack, not from typing fast.

The failure mode this guards against is the confident cascade: you make ten changes, something is subtly wrong, and now you cannot tell which change did it or how to undo just that one. Every practice here is designed so that at any moment you can answer "is it still correct?" and "how do I undo the last step?" cheaply.

Work the phases in order. On a genuinely large task, produce the discovery and plan **before** any code change and let the user confirm the plan — the cheapest place to fix a wrong approach is before it exists.

## 1. Decompose before you touch

You cannot safely change what you do not understand, and you do not understand a large system by reading it front-to-back. Map it, then verify the map at the load-bearing points.

- **Fan out to explore, converge to decide.** Partition the unknown into disjoint questions ("where is X emitted?", "what calls Y?", "what format contract governs Z?") and dispatch parallel read-only searches, one per question. Their job is to *locate and summarize*, not to conclude. You keep the conclusion.
- **Personally re-read anything load-bearing.** A summary is a lead, not a fact. Before you build a plan on "the golden test normalizes URIs" or "this string dodges an InDesign bug", open the file and confirm it with your own eyes. Cheap to check now, expensive to discover mid-refactor.
- **Write the plan down, including the non-goals.** For a large task emit two artifacts before code: a discovery report (what exists, what the contracts are, where the traps are) and an implementation plan (ordered phases, each independently shippable). State explicitly what you are *not* doing — the non-goals are what stop scope creep from turning a 3-phase job into a 9-phase one.
- **Size honestly.** If the task turns out ~3× bigger than it looked, stop and report the new scope rather than silently grinding. The user may want to split it.

## 2. Build the safety net before you refactor

The single highest-leverage move in behavior-preserving work: **pin the current behavior in a test before you change the code.** Then any change that alters behavior fails loudly and immediately, and you know exactly which change did it.

- **Characterize, don't assume.** Capture what the system *actually does today* (a golden/snapshot: the real output bytes, the real CLI exit code and stdout, the real serialized file), not what the docs claim it does. You are pinning reality.
- **Make the comparison exact and stable.** For file-format output, byte-compare every part; normalize only the genuinely non-deterministic bits (absolute paths, timestamps) to a fixed token so a legitimate refactor stays green. See `references/recipes.md` for a golden-test scaffold.
- **Regenerating the golden during a refactor is a red flag, not a convenience.** If your "pure refactor" changes the golden, either it was not pure or the test found a real regression — investigate before you rebaseline. Rebaseline only as a *deliberate, reviewed* act, and only after you have read the diff and confirmed its scope is exactly the intended change and nothing else.
- **Ratchet size limits.** If the repo pins file sizes (a maintainability guardrail), treat the pin as a one-way ratchet: a façade you are shrinking may only get smaller. When a change legitimately needs to raise a pin, raise it in the same change with a one-line justification, following whatever procedure the guardrail file documents — do not silently loosen it.

## 3. Make risky changes mechanical, not manual

Retyping code by hand during a move is how load-bearing details die — a dropped attribute, a "normalized" string that was dodging a bug, a renamed variable missed in one branch. When you must move or rename verbatim code, drive it with a script that *refuses to run if its assumptions are wrong*.

- **Anchor, then cut.** Before extracting lines N–M, assert that the text at N and M is exactly what you expect. If the file shifted, the assertion aborts instead of silently grabbing the wrong range. (Recipe in `references/recipes.md`.)
- **Rename with word-boundary precision.** A `self` → `writer` rename is `re.sub(r"\bself\b", ...)`, not find-replace-all that also mangles `self_id`. Scripted renames are auditable and repeatable; hand-edits are neither.
- **Move contracts with their comments.** When a string carries a hard-won reason ("the `Paragraph*` prefix or InDesign silently ignores this"), the comment moves *with* the string. Never "clean up" a string you do not fully understand — the ugliness may be the whole point.
- **Preserve the caller's world.** Behavior-preserving decomposition means tests and callers should not need to change. A façade that re-exports every public name, and methods that become one-line delegates, let you split a monolith while the outside sees nothing move. Enforce it: a test that the façade still exposes every name, and that no reverse-imports crept in.

## 4. Verify on a ladder — cheapest first

Run checks in increasing order of cost, and let each rung gate the next. A lint error makes a two-hour test run pointless; catch it in two seconds. The exact commands live in the repo's own guides (here: `AGENTS.md` §4 and §8.5) — match the ladder to what actually changed, do not run everything reflexively.

Typical order, fastest to slowest:

1. **Lint / format** — syntax and style, seconds.
2. **Targeted tests** — the module you touched, so failures point at your change.
3. **Full suite** — nothing elsewhere broke.
4. **Structural guardrails** — size ratchets, boundary checks, parity tests (e.g. "every emitted kind has a renderer").
5. **Doc-link / integrity checks** — if you touched docs or moved files.
6. **Build / quality-gate** — the real command the CI runs.
7. **Golden** — byte-identity of shipped output.
8. **CI poll** — after push, watch the actual CI run to green.

If a rung fails, stop and fix before climbing higher. Report *which* check failed and its output — "tests pass" when they do not is the one unrecoverable lie, because every later decision trusts it.

## 5. One phase, one branch, one PR

Structure the work so that any single step can be reverted without touching the others. This is what makes a large task safe: mistakes stay contained.

- **A phase is a logically complete, independently shippable unit** that builds and passes its own tests. Squash-merge collapses the internal commits, so per-commit granularity is for the review trail, not for `main`.
- **Branch through the repo's wrapper, off an up-to-date base.** Never commit to `main`. Never force-push shared history. One task → one branch; do not pile a second topic onto an open branch.
- **Conventional commit subjects, ≤72 chars, no agent attribution** (this repo's `AGENTS.md` overrides any default that adds `Co-Authored-By`). Detail goes in the body.
- **Stack only when you must**, and know how to unstack: if phase B builds on unmerged phase A, be ready to `rebase --onto` when A merges.
- **Fill the PR template honestly**, including the validation block with the commands you actually ran. An empty anti-debt section means you skipped the checklist, not that nothing applied.

## 6. Deciding the next action

After each step, choose deliberately between *proceed*, *verify*, and *stop-and-ask*. The default is to keep moving on reversible work that clearly follows from the request — but some actions are gated.

**Proceed autonomously** when the action is reversible and within the agreed scope: the next phase in a confirmed plan, a fix the review already identified, gathering more information yourself, retrying after a transient error.

**Stop and ask first** — even if the task seems to imply it — for anything hard to undo or outside scope:
- destructive or irreversible ops: `reset --hard`, force-push, deleting or reverting generated outputs and other windows' artifacts, large block deletions;
- contract changes: public CLI flags or exported signatures, data/schema, dependency bumps;
- genuine ambiguity in requirements (guessing wastes more than asking);
- scope that has grown well beyond what was agreed.

**Authorization is scoped and does not travel.** "Merge all of these" covers *this* workstream, not the next task you start. Re-confirm for a new body of work. Before running any state-changing command (restart, delete, config edit), check that the evidence supports *that specific action* — a symptom that pattern-matches a known failure may have a different cause.

**Before ending a turn, check your last paragraph.** If it is a plan, a promise ("I'll…", "next I'll…"), or a question you could answer yourself, that is unfinished work — do it now with tool calls. End the turn only when the task is genuinely complete or you are blocked on something only the user can provide.

## 7. Close the loop

- **Keep behavior and docs in the same change.** If you changed the workflow, editing surface, or an example, update the docs the repo names as the minimum set in the *same* PR — stale docs are a silent debt.
- **Archive the non-obvious.** When you hit a trap that cost you real time (a parallel window landing mid-plan, an import that breaks only in the direct-CLI path, a snapshot whose columns are non-uniform), write it to memory as one durable fact with the *why* — so the next session does not re-learn it. Do not memory-dump what the code or git history already records.
- **Track the leftovers.** Deferred items and follow-ups go in the PR body under "Follow-up", or in a running ledger — never dropped on the floor and never smuggled into an unrelated branch.

## The one-line version

Understand it, pin it, change it mechanically, prove it still works, ship it in a revertable slice, and stop at the gates. When in doubt about whether a step is safe, the answer is to make it *observable and reversible* first — then it is.
