---
description: A working method for large, high-stakes, multi-step engineering tasks — decomposing them into provable steps, building a safety net before changing anything, making risky edits mechanical rather than manual, verifying on a cheap-to-expensive ladder, and deciding when to keep going versus stop and ask. Use this whenever a task is big enough that you cannot hold the whole thing in your head at once, whenever you are refactoring or moving code that must not change behavior, whenever a task will span several commits or PRs, or whenever the cost of a silent mistake is high (shipped output, released artifacts, data migrations, format contracts). Reach for it even when the user just says "refactor this", "clean this up", "split this file", "migrate X", or "do a full review and fix what you find" — those are exactly the tasks that go wrong without a method.
when_to_use: Trigger on large refactors, monolith decomposition, "split this file", multi-PR work, behavior-preserving code moves, format/serialization changes, full-repo reviews with fixes, data or schema migrations, or any task where a mistake is expensive to unwind. Also when you feel the urge to "just start editing" a task you cannot fully see yet — that urge is the signal to load this first.
argument-hint: "[optional: the task or the phase you're on]"
---

# Hardcore Task Execution

This is not theory. It was distilled from executing real workstreams in this repo — a 43-defect full review fixed across a dozen PRs, and the decomposition of a 2001-line exporter into a layered package with the shipped artifact provably bit-identical at every step. Every rule below was earned by a specific failure or near-miss during that work. Where a rule sounds pedantic, that is usually where it saved (or would have saved) the most time.

The core idea: a big task is a sequence of small changes, each one *provable* and *reversible*. Everything below exists to earn the right to make each change — first make it observable (something will scream if you break it), then make it small (one revertable unit), then make it. Speed comes from never having to backtrack, not from typing fast. The failure mode being guarded against is the confident cascade: ten changes deep, something is subtly wrong, and you can no longer tell which change did it or how to undo just that one.

Work the phases in order. On a genuinely large task, produce the discovery report and plan **before** any code change and let the user confirm the plan — the cheapest place to fix a wrong approach is before it exists.

## 1. Decompose before you touch

You do not understand a large system by reading it front-to-back. Map it wide, then verify the map at the points your plan will stand on.

- **Fan out to explore, converge to decide.** Partition the unknown into disjoint questions ("where is X emitted?", "what calls Y?", "what format contract governs Z?") and dispatch parallel read-only searches, one per question. Their job is to *locate and summarize* — you keep the conclusion. Never let a sub-search's summary become a plan input without the next rule.
- **A summary is a lead, not a fact.** Personally re-read anything load-bearing before building on it. This includes your *own* earlier observations: writing test expectations from a remembered data probe, instead of re-reading the actual fixture rows, produced tests asserting localized columns on the wrong region's rows — the failing test was right and the memory was wrong. Probe the data again at the moment you write against it.
- **Write the plan down, including the non-goals.** Two artifacts before code: a discovery report (what exists, the contracts that must not change with file:line citations, the traps) and an implementation plan (ordered phases, each independently shippable, each with its verification listed). The non-goals section is what stops a 5-phase job from quietly becoming a 9-phase one.
- **Order phases by risk, safety net first.** Phase 0 contains *only* the safety net — no production change shares a PR with the net that is supposed to catch it. Pure mechanical moves come next; anything that intentionally changes output comes **last**, when everything else is already pinned and green.
- **Size honestly.** If the task turns out ~3× bigger than it looked, stop and report the new scope rather than silently grinding. The user may want to split it.

## 2. Build the safety net before you refactor

The single highest-leverage move in behavior-preserving work: **pin the current behavior in a test before touching the code.** Then any change that alters behavior fails loudly, immediately, and points at exactly one change.

- **Characterize reality, not intent.** Capture what the system *actually does today* — the real output bytes, the real CLI exit code and stdout line, the real serialized file — built through the same entrypoint users hit (a subprocess CLI call beats an internal shortcut). You are pinning reality, not the docs' claims about it.
- **Compare exactly; normalize minimally.** Byte-compare every part of the artifact. Normalize only the genuinely non-deterministic bits (absolute paths, timestamps) to a fixed token, so a legitimate refactor stays green while a real output change cannot hide. Over-normalizing is how regressions slip through the net you built to catch them. Scaffold in `references/recipes.md`.
- **Regenerating the golden during a refactor is a red flag, not a convenience.** If a "pure refactor" diffs the golden, either it was not pure or the net caught a real bug — find out which before touching the baseline. Rebaseline only as a deliberate, reviewed act, in its own clearly-labeled change, after reading the diff and confirming its scope is *exactly* the intended change and nothing else. Across an entire multi-phase decomposition there should be at most a handful of these — the one in the source workstream happened in the final phase, for a deliberate output feature, with a two-file diff that was read line by line.
- **Ratchet size limits.** If the repo pins file sizes, treat each pin as a one-way ratchet: a façade being shrunk may only shrink. When a change legitimately needs to raise a pin, raise it in the same PR with a one-line justification, following the procedure the guardrail file itself documents — never silently loosen it, and never game it by moving code somewhere unpinned.

## 3. Make risky changes mechanical, not manual

Retyping code during a move is how load-bearing details die — a dropped attribute, a "normalized" string that was dodging a downstream bug, one missed occurrence in a branch you didn't scroll to. When moving or renaming verbatim code, drive it with a script that *refuses to run if its assumptions are wrong*.

- **Anchor, then cut.** Before extracting lines N–M, assert the exact text at both boundaries. If the file shifted, the assertion aborts instead of silently slicing the wrong range.
- **When the mechanism fires, the mechanism is right.** An anchor assertion failing, a golden diffing, a guardrail rejecting — the correct response is always to fix your model of the world (re-read, re-locate, re-probe), never to widen the slice, loosen the comparison, or delete the assert to "make it work". In the source workstream an anchor fired four lines off the expected boundary; relocating the true boundary took a minute, and blindly widening would have shipped a corrupted move.
- **Rename with word-boundary precision.** `re.sub(r"\bself\b", "writer", ...)`, not find-replace-all that also mangles `self_id`. Scripted renames are auditable and repeatable after a rebase; hand-edits are neither.
- **Move contracts with their comments; never clean up what you don't fully understand.** When a string carries a hard-won reason ("the `Paragraph*` prefix, or InDesign silently ignores this"), the comment travels with the string. Ugliness in shipped-format code is often the entire point.
- **Preserve the caller's world, and enforce it.** A behavior-preserving split means tests and callers change *zero* lines: a façade re-exports every public name, former methods become one-line delegates. Lock it with tests — the façade still exposes every name, no reverse imports point back at it, delegate output equals module output.

## 4. Verify on a ladder — cheapest first

Run checks in increasing order of cost, each rung gating the next: a two-second lint failure makes a full-suite run pointless. Match the ladder to what changed (this repo's is in `AGENTS.md` §4 and §8.5) — but **match it completely**: the single CI failure across the entire source workstream came from running the full test suite locally while skipping one cheap structural gate that CI also runs. Run CI's exact set before pushing, not your remembered approximation of it.

Typical order: lint → targeted tests (failures point at your change) → full suite → structural guardrails and parity tests → doc-link/integrity checks → the real build/quality-gate command → golden byte-identity → push, then poll the actual CI run to green.

If a rung fails, stop and fix before climbing. Report *which* check failed with its actual output. "Tests pass" when they do not is the one unrecoverable lie — every later decision trusts it.

## 5. One phase, one branch, one PR

Structure the work so any single step reverts without touching the others; that containment is what makes a large task safe.

- **A phase is a logically complete, independently shippable unit** that builds and passes its own gates. Squash-merge collapses internal commits, so commit granularity serves the review trail, not `main`.
- **Branch through the repo's wrapper off an up-to-date base**; never commit to `main`, never force-push shared history. One task → one branch — a second topic on an open branch couples two reverts together.
- **Conventional commit subjects ≤72 chars, no agent attribution** (this repo's `AGENTS.md` overrides any harness default that appends one). Detail in the body.
- **Stack only when forced, and know the unstack move** (`rebase --onto` when the base merges). Prefer sequencing phases so each lands before the next starts.
- **Fill the PR template honestly** — the validation block lists the commands actually run, and an empty anti-debt section means the checklist was skipped, not that nothing applied.

## 6. Deciding the next action

This is the loop actually run after **every** tool result, not a vibe:

1. **Result confirms the current model of the world** → proceed to the next planned step. Do not re-verify what is already established; do not narrate options you won't take.
2. **Result contradicts the model** → stop mutating. The world is right and the model is wrong until proven otherwise. Re-anchor (re-read the file, re-probe the data, re-run the minimal case), *then* decide. A failing test gets understood before it gets "fixed" — sometimes the test is the thing that's correct.
3. **The next step is hard to reverse or outside agreed scope** → gate on the user, even mid-flow.

The gates that always stop for confirmation: destructive git ops (`reset --hard`, force-push, deleting or reverting generated outputs and other windows' artifacts), large deletions, public CLI/signature changes, schema or dependency changes, genuine requirement ambiguity, and scope that has grown well past what was agreed.

Three habits that keep the loop honest:

- **Re-check the world before each phase.** Other actors (parallel windows, teammates) land changes mid-plan. Fetch, re-inventory the assumptions the next phase stands on, and if reality moved, write a plan addendum instead of executing a stale plan. In the source workstream a parallel PR landed between planning and execution; ten minutes of re-inventory (5 component kinds had become 8) prevented building on a fiction.
- **Verify before asserting absence.** Never claim "X doesn't exist / isn't called / can't happen" from inference or a stale listing — probe directly first. Confident wrong absences are how whole phases get built on sand.
- **Route around blocks; don't force them.** A denied read, a missing credential, a locked file — find an equivalent source (the template that generates the output you can't read, the fixture instead of the artifact) rather than retrying the denied thing. If no route exists, that's a gate-3 stop, stated plainly.

Authorization is scoped and does not travel: "merge all of these" covers *that* workstream, not the next task. Re-confirm per body of work. And before ending a turn, read your own last paragraph — if it is a plan, a promise, or a question you could answer yourself, that is unfinished work; do it now.

## 7. Close the loop

- **Docs move with behavior, in the same PR.** If the change touches workflow, editing surface, or a documented example, update the repo's named minimum doc set in the same change — stale docs are silent debt with your name on it.
- **Archive the non-obvious, with the why.** A trap that cost real time (a parallel landing mid-plan, an import that only breaks in the direct-CLI path, a fixture whose columns are non-uniform across tables) becomes one durable memory fact. Skip what the code, git history, or existing docs already record.
- **Leftovers get a ledger line, not a burial.** Deferred items go in the PR body under "Follow-up" or the running ledger — never dropped, never smuggled into an unrelated branch.

## The one-line version

Understand it, pin it, change it mechanically, prove it still works, ship it in a revertable slice, and when the world disagrees with you — believe the world, then decide.
