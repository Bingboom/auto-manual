# Claude Code Hooks

Active hooks must be declared in `.claude/settings.json`; files in this directory are inert until settings reference them.

## Active Hooks

| Hook | Event / matcher | Script | Purpose |
| --- | --- | --- | --- |
| derived-surface-guard | `PostToolUse` / `Bash` | `derived_surface_guard.py` | After `build.py check\|sync-review\|publish`, warn (exit 2, stderr → agent) when tracked derived surfaces (`docs/_build`, `docs/index.rst`, `docs/_review`) got dirtied, so verification side-effects are restored instead of leaking into unrelated PRs (AGENTS.md §6). Silent (exit 0) otherwise; never blocks — the command already ran. |

This hook only fires inside Claude Code. Its **git-layer counterpart** —
`scripts/derived_surface_push_check.py`, wired into `.githooks/pre-push` (all
three variants) — fires at push time for every agent and human (Codex
included, wherever `core.hooksPath` is set per AGENTS.md §8.2), with
`review/*` / `backport/*` exempt. Claude hook = warn at the moment of
dirtying; git hook = advisory at the last gate before publication.

## Ownership

- Hook scripts belong here under `.claude/hooks/`.
- Hook configuration belongs in `.claude/settings.json`.
- Personal experiments belong in `.claude/settings.local.json`, not in committed project settings.

## When To Add A Hook

Add a hook only when deterministic automation is better than an instruction:

- block a dangerous action before it runs;
- run a narrow formatter or validator after edits;
- capture session learnings for a later `CLAUDE.md` or skill update;
- notify an external system from a known event.

Do not use hooks for broad judgment, long-running builds, or noisy reminders that fire every turn.

## Review Checklist

Before enabling a hook in `settings.json`:

- Confirm the hook event and matcher are as narrow as possible.
- Ensure the script exits `0` when it has no decision to make.
- Keep outputs short and actionable.
- Avoid writing generated files into tracked paths.
- Test the script manually with representative JSON input.
- Run `/config-review` and include the result in the PR notes.

## Useful Events

- `ConfigChange`: review project settings, skills, and hook edits during a session.
- `PostToolUse` with `Edit|Write`: run narrow validation after file edits.
- `Stop`: propose follow-up documentation or skill improvements after a session.
- `PreToolUse` with `Bash`: block destructive shell patterns that permissions cannot express cleanly.
