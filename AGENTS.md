# Auto-Manual Agent Guide

Use this file for repo operating rules only.
It is not the architecture strategy and it is not the optimization roadmap.

This file is the single source of truth for **every** AI agent working in this repo (Claude Code, Codex, future agents). The root [`CLAUDE.md`](CLAUDE.md) is a thin entrypoint that pulls this file into Claude Code via `@AGENTS.md`; Codex reads this file directly. When rules change, edit this file — do not fork rules into per-agent files.

Document boundary:

- `AGENTS.md`: how an agent should operate in this repo today
- `System Evolution Strategy.md`: long-term system direction and stable architecture boundaries
- `optimization_project.md`: repo-level execution roadmap and next optimization priorities

For long-term direction, read:

- [`code-as-doc/architecture/System Evolution Strategy.md`](/Users/pika/Documents/GitHub/auto-manual/code-as-doc/architecture/System%20Evolution%20Strategy.md)

For repo optimization priorities, read:

- [`optimization_project.md`](/Users/pika/Documents/GitHub/auto-manual/optimization_project.md)

For current human workflows, read:

- [`code-as-doc/build_doc_guide.md`](/Users/pika/Documents/GitHub/auto-manual/code-as-doc/build_doc_guide.md)
- [`user-guide/hello_auto-doc.md`](/Users/pika/Documents/GitHub/auto-manual/user-guide/hello_auto-doc.md)

## 1. Entrypoint

- Default to [`build.py`](/Users/pika/Documents/GitHub/auto-manual/build.py).
- Treat [`tools/`](/Users/pika/Documents/GitHub/auto-manual/tools) as low-level implementation unless the task is explicitly about those scripts.

## 2. Editing Surface

- Shared changes: [`docs/templates/`](/Users/pika/Documents/GitHub/auto-manual/docs/templates), [`data/phase2/`](/Users/pika/Documents/GitHub/auto-manual/data/phase2)
- Target review changes after review starts: [`docs/_review/`](/Users/pika/Documents/GitHub/auto-manual/docs/_review)
- Generated output only: [`docs/_build/`](/Users/pika/Documents/GitHub/auto-manual/docs/_build)
- Do not hand-edit [`docs/index.rst`](/Users/pika/Documents/GitHub/auto-manual/docs/index.rst) unless the task is about index generation.

## 3. Workflow Rules

- Do not create one config per model just because the model changed.
- Keep the shared family config pattern with [`config.us.yaml`](/Users/pika/Documents/GitHub/auto-manual/config.us.yaml) and [`config.ja.yaml`](/Users/pika/Documents/GitHub/auto-manual/config.ja.yaml).
- If a target is already in review, prefer `sync-review` over `review --refresh-review` for data-driven updates.
- Review overrides must stay under `overrides/_assets/`, `overrides/_static/`, or `overrides/renderers/`.
- Avoid hardcoded model defaults such as `JE-1000F` in CLI behavior, report paths, or release paths.

## 4. Validation

- Logic changes: `python3 -m unittest`
- Build or quality-gate changes: `python3 build.py check --config config.us.yaml --model JE-1000F --region US`
- JP review or publish changes: `python3 build.py publish --config config.ja.yaml --model JE-1000F --region JP`
- Diff-report changes: `python3 build.py diff-report --config config.us.yaml --model JE-1000F --region US`
- Release traceability changes: `python3 build.py release-manifest --config config.ja.yaml --model JE-1000F --region JP`

## 5. Documentation

- Update docs in the same change when behavior changes.
- Minimum set: [`README.md`](/Users/pika/Documents/GitHub/auto-manual/README.md), [`code-as-doc/build_doc_guide.md`](/Users/pika/Documents/GitHub/auto-manual/code-as-doc/build_doc_guide.md), [`user-guide/hello_auto-doc.md`](/Users/pika/Documents/GitHub/auto-manual/user-guide/hello_auto-doc.md)
- If a code change affects the current workflow, editing surface, environment setup, or release flow, update [`user-guide/hello_auto-doc.md`](/Users/pika/Documents/GitHub/auto-manual/user-guide/hello_auto-doc.md) in the same change.
- If a code change affects the happy-path example, onboarding steps, or target-specific sample commands, update [`user-guide/quick_start_guide.md`](/Users/pika/Documents/GitHub/auto-manual/user-guide/quick_start_guide.md) in the same change.
- When a phase or workstream from [`optimization_project.md`](/Users/pika/Documents/GitHub/auto-manual/optimization_project.md) is completed, add a matching maintenance record to [`code-as-doc/code_optimization_log.md`](/Users/pika/Documents/GitHub/auto-manual/code-as-doc/code_optimization_log.md).

## 6. Working Tree Safety

- `_build`, `reports/version_tracking`, and `reports/releases` may contain user work or verification artifacts.
- Do not delete or revert generated outputs unless the task explicitly requires cleanup.

## 7. Local Skills

- Use [`.agents/skills/markdown-rst-template-intake/SKILL.md`](/Users/pika/Documents/GitHub/auto-manual/.agents/skills/markdown-rst-template-intake/SKILL.md) when mapping external Markdown manuals into this repo's reusable RST template and recipe layout.
- Use [`.agents/skills/bitable-translation-memory/SKILL.md`](/Users/pika/Documents/GitHub/auto-manual/.agents/skills/bitable-translation-memory/SKILL.md) for one-shot sentence translation, terminology lookup, and live sentence-pair retrieval.
- Use [`.agents/skills/manual-rewrite-with-tm/SKILL.md`](/Users/pika/Documents/GitHub/auto-manual/.agents/skills/manual-rewrite-with-tm/SKILL.md) for full manual or Markdown rewrite tasks that must preserve structure, reuse translation-memory phrasing, or keep unmatched source text highlighted with `==...==`.
- Use [`.agents/skills/bilingual-tm-maintenance/SKILL.md`](/Users/pika/Documents/GitHub/auto-manual/.agents/skills/bilingual-tm-maintenance/SKILL.md) when bilingual source/target copy should be written to live `Translation_Memory`, followed by target-language maintenance logs, bilingual audit, and audit logs.
- For TM-guided rewrite jobs, use the skills in this order: `bitable-translation-memory` for lookup, then `manual-rewrite-with-tm` for the structure-preserving rewrite flow.

## 8. Multi-Window Parallel Development

These rules apply whenever more than one Claude or Codex window may be working on this repo at the same time. The goal is to keep windows from clobbering each other's work and to keep `main` releasable.

The authoritative branch / PR / protection rules already live in [`code-as-doc/dev/git_branching_guide.md`](code-as-doc/dev/git_branching_guide.md) and [`code-as-doc/dev/git_worktree_guide.md`](code-as-doc/dev/git_worktree_guide.md). This section adds the parallel-execution overlay only.

### 8.1 Starting a window task

Before editing any file:

1. Inspect the tree and decide whether it is yours to start from:

   ```powershell
   git fetch origin
   git status
   git branch --show-current
   ```

   If `git status` shows uncommitted files or `?? ` entries you did not create, **stop and ask the operator** before continuing — those may belong to another window.

2. Create the branch through the wrapper (it fast-forwards `main`, refuses a dirty tree, and branches from up-to-date `origin/main`):

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/start_branch.ps1 <branch>
   ```

   On macOS / Linux use `./scripts/start_branch.sh <branch>` instead.

3. Branch names follow [`git_branching_guide.md`](code-as-doc/dev/git_branching_guide.md) §2: `feat/<area>-<topic>`, `fix/<area>-<topic>`, `refactor/<area>-<topic>`, `docs/<topic>`, `chore/<topic>`, `review/<MODEL>-<REGION>-<topic>`, `spike/<topic>`, or `release/<MODEL>-<REGION>-<yyyymmdd>`. **Do not** prefix branches with the agent identity (`claude/`, `codex/`); the change type is what the branch name encodes. Identify the agent in the PR body if it matters.

4. If you need two branches checked out at once, use `git worktree` per [`git_worktree_guide.md`](code-as-doc/dev/git_worktree_guide.md). Never share one checkout across two windows.

### 8.2 Branch discipline

- Never commit directly to `main`. Branch protection blocks it server-side; the managed [`.githooks/pre-push`](.githooks/pre-push) also blocks pushes from branches whose base is behind `origin/main` (enable once with `git config core.hooksPath .githooks`).
- Never `git push --force`. Use `git push --force-with-lease` only when rewriting history you are certain no other window has fetched.
- One task → one branch. Do not add a second unrelated topic onto an open branch.

### 8.3 Commit discipline

- Each commit should be a logically complete unit that builds and passes its relevant tests on its own. Squash-merge on the PR collapses them at merge time, so granularity here is for the review trail, not for `main`.
- Use Conventional Commits with a repo scope, matching [`git_branching_guide.md`](code-as-doc/dev/git_branching_guide.md) §6:
  - `feat(build): add manifest-based draft generation`
  - `fix(check): catch stale foreign model names`
  - `refactor(targets): split target resolution helpers`
  - `docs(branching): refresh worktree examples`
- Subject line ≤72 chars. Detail goes in the body after a blank line.
- Do not add agent attribution such as `Generated by Claude`, `Co-Authored-By: Claude …`, or `[claude]` / `[codex]` prefixes. Identity comes from `git config user.*`.

### 8.4 Concurrency safety

These rules exist so two windows working in parallel do not quietly clobber each other.

- Before any edit, run `git status` and confirm you are on the branch you intended, with no foreign in-progress changes.
- Do not touch files outside your task scope. The only exception is a small autofix (formatter, import sort, ruff fix) — call it out explicitly in the PR body.
- Do not modify the following unless the task is *about* them: `.git/**`, `.githooks/**`, `.github/workflows/**`, `.github/pull_request_template.md`, `AGENTS.md`, `CLAUDE.md`, `code-as-doc/dev/git_branching_guide.md`, `code-as-doc/dev/git_worktree_guide.md`, other `.agents/skills/**/SKILL.md`, `BOOTSTRAP.md`, `IDENTITY.md`, `SOUL.md`, `USER.md`.
- Do not delete or rename files another window might be editing. If you are unsure who owns a file, stop and ask the operator.
- Honour §6 working-tree safety: `_build/`, `reports/version_tracking/`, and `reports/releases/` may hold another window's verification artifacts — do not clean them unless the task is cleanup.
- If your task is a refactor that renames or moves a hotspot module (anything listed in `code_style_guide.md` §2), confirm with the operator before pushing — other windows may have open branches against the old path.

### 8.5 Local validation before PR

The PR cannot be opened until the validation set that matches the change passes locally. Use [`git_branching_guide.md`](code-as-doc/dev/git_branching_guide.md) §4.4 as the authoritative checklist; the minimum baseline is what CI runs (the `Manual Validation` workflow):

| Change touches | Run locally |
| --- | --- |
| any Python under `build.py`, `tools/`, `tests/`, `scripts/`, `integrations/` | `python -m ruff check build.py integrations tools tests scripts` |
| logic in `tools/`, `build.py`, `tests/` | `python -m unittest` |
| `tools/utils/**` types | `python -m mypy tools/utils` |
| `tools/` boundary, `build.py`, `tools/build_docs.py`, `tools/process_build_queue.py` | `python tools/check_maintainability_guardrails.py` |
| any `code-as-doc/**` or `user-guide/**` docs | `python tools/check_doc_link_integrity.py` |
| build / quality-gate behaviour | `python build.py check --config config.us-en.yaml --model JE-1000F --region US` |
| JP review or publish behaviour | `python build.py check --config config.ja.yaml --model JE-1000F --region JP` |
| diff-report behaviour | `python build.py diff-report --config config.us.yaml --model JE-1000F --region US` |
| release traceability | `python build.py release-manifest --config config.ja.yaml --model JE-1000F --region JP` |

If any check fails, do not open the PR. Report which check failed and the last command output to the operator.

### 8.6 PR flow

1. Open the PR with `gh pr create --base main`. Title format: Conventional Commits (`feat(area): topic` etc.), ≤72 chars.
2. Fill in every field of [`.github/pull_request_template.md`](.github/pull_request_template.md), including the validation block with the actual commands you ran.
3. Tick the impact-surface and anti-debt boxes honestly. An empty Anti-Debt section is a signal you skipped the checklist, not that nothing was relevant.
4. Do **not** self-merge. Wait for the operator (夏冰) to review. Do not run `gh pr merge` from the window.
5. After merge, delete the head branch (`gh pr` already does this when the repo has *Automatically delete head branches* on, which it does — see §8.8 of `git_branching_guide.md`). Do not keep it open as a second working lane.

### 8.7 Communication boundaries with the operator

- Requirements ambiguous → stop and ask. Do not guess.
- Out-of-scope bugs noticed mid-task → call them out in the PR body under a "Follow-up" or "Future work" section; do not fix them in the same branch.
- The task turns out 3× larger than expected → stop, report the new scope, let the operator decide between splitting and continuing.
- The following always require explicit confirmation **before** acting, even if the task seems to imply them: deleting large blocks of code, changing public CLI flags or function signatures exported by `build.py`, editing `data/phase2/**` schema, bumping dependency versions in `requirements.txt` or `pyproject.toml`, deleting / renaming committed files under `docs/_review/**`, touching `.github/workflows/**`.
