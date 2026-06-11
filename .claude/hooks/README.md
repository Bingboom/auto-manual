# Claude Code Hooks

No project hooks are active by default. Active hooks must be declared in `.claude/settings.json`; files in this directory are inert until settings reference them.

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
