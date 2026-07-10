---
name: config-review
description: Review this repository's Codex and Claude agent scaffolding for drift, bloat, missing safety rules, and broken skill discovery. Use when changing AGENTS.md, CLAUDE.md, .agents/skills, .claude, .codexignore, hooks, permissions, plugin/MCP setup, or when asked to audit the agent configuration surface.
---

# Config Review

Review the repository's agent configuration surface without reading generated output.

## Inspect

1. Check the worktree and changed configuration files:
   - `git status --short -- AGENTS.md CLAUDE.md .agents .claude .codexignore`
   - `git diff --name-only origin/main...HEAD -- AGENTS.md CLAUDE.md .agents .claude .codexignore`
2. List active navigation and skill files:
   - `find . -path './.git' -prune -o \( -name AGENTS.md -o -name CLAUDE.md -o -path './.agents/skills/*/SKILL.md' -o -path './.claude/settings.json' -o -path './.claude/hooks/*' -o -path './.claude/skills/*/SKILL.md' \) -print | sort`
3. Read only relevant files. Exclude `docs/_build`, `docs/_review`, `reports`, caches, credentials, and runtime directories.

## Check

- Root `AGENTS.md` is the shared policy map, not a procedure dump.
- Nested `AGENTS.md` files provide local ownership, entrypoints, and targeted validation commands; nested `CLAUDE.md` files remain Claude-only navigation overlays.
- Reusable procedures live in skills, not in every navigation file.
- Every Codex skill has valid frontmatter with `name` and `description`.
- Skill names are lowercase hyphen-case and each skill with a UI binding has `agents/openai.yaml` whose prompt names `$skill-name`.
- `.codexignore` excludes generated output, caches, and temporary artifacts without hiding durable review/source surfaces.
- `.claude/settings.json` contains only project-safe deny rules and no absolute paths, secrets, or personal allow rules.
- Hooks remain inert unless a narrow event, matcher, tested script, and owner are documented.
- Claude compatibility files must not become the only place where Codex behavior is documented.

## Validate

Run the checks that match the changed surface:

- `python3 /Users/hello-tech-team/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/<skill-name>`
- `python3 tools/check_doc_link_integrity.py`
- `python3 tools/check_maintainability_guardrails.py`

For Python implementation changes, also run the repository lint and targeted tests from the applicable nested `AGENTS.md`.

## Report

Return the reviewed files, findings ordered by risk, edits made, validation commands and results, and follow-ups intentionally left out of the change.
