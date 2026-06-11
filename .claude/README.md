# Claude Code Project Configuration

This directory is the committed Claude Code configuration surface for the repo. Keep personal permissions in `.claude/settings.local.json`; that file is gitignored and should stay local.

## Map

- `settings.json`: team-shared project settings. Keep hard exclusions here so every Claude session avoids the same generated and local-only noise.
- `hooks/README.md`: hook ownership, review rules, and rollout checklist.
- `skills/README.md`: project skill ownership and review rules.
- `skills/config-review/SKILL.md`: on-demand review procedure for Claude scaffolding and configuration drift.

## Review Cadence

Review this directory when any of these happen:

- A major Claude model or Claude Code release changes how configuration, hooks, skills, or permissions behave.
- A root or nested `CLAUDE.md` grows enough that it starts mixing navigation with procedure.
- New generated-output directories, caches, runtime folders, or local credentials appear in the repo.
- A new hook, skill, plugin, MCP server, or managed policy is proposed.
- Every three to six months even if nothing feels broken.

## Change Rules

- Keep `settings.json` project-safe: no user-specific absolute paths, tokens, or machine-local commands.
- Use deny rules for high-noise generated outputs and credentials; do not deny source surfaces that agents may need for real work.
- Claude Code project settings load from the directory where Claude starts. If a subdirectory becomes a normal launch point, add a reviewed subdirectory `.claude/settings.json` instead of assuming this root file applies there.
- Do not enable active hooks casually. Add the hook script, document its purpose, then add it to `settings.json` only after local testing.
- Prefer a skill when the content is a reusable procedure that does not need to load in every session.

Reference points: the Claude large-codebase article recommends lean layered `CLAUDE.md`, per-directory commands, and committed `permissions.deny`; the official settings, hooks, skills, and large-codebase docs define the current syntax.
