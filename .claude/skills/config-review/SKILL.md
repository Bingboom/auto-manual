---
description: Review Claude Code scaffolding for this repo. Use when changing CLAUDE.md files, .claude/settings.json, hooks, skills, permissions, plugin/MCP setup, or when asked to perform a configuration review.
when_to_use: Trigger phrases include config review, Claude setup, Claude scaffolding, hooks review, skills review, deny rules, ignore rules, nested CLAUDE.md, agent navigation, or model-release cleanup.
argument-hint: "[optional changed paths or focus area]"
---

# Config Review

Review the Claude Code configuration surface for drift, bloat, and missing safety rules.

## Inspect

1. List changed config files:
   - `git status --short -- CLAUDE.md AGENTS.md .claude .agents`
   - `git diff --name-only origin/main...HEAD -- CLAUDE.md AGENTS.md .claude .agents`
2. List active navigation/config files:
   - `find . -path './.git' -prune -o \( -name CLAUDE.md -o -path './.claude/settings.json' -o -path './.claude/hooks/*' -o -path './.claude/skills/*/SKILL.md' \) -print | sort`
3. Read only the relevant files. Avoid generated output and local-only settings.

## Check

- Root `CLAUDE.md` is a concise map, not a procedure dump.
- Subdirectory `CLAUDE.md` files contain local ownership, entrypoints, and targeted validation commands.
- Procedures that are not always needed live in skills, not root memory.
- `.claude/settings.json` has project-safe `permissions.deny` entries for generated output, caches, runtime folders, and credentials.
- `.claude/settings.json` does not include local absolute paths, secrets, or personal allow rules.
- Hooks are inactive unless they have a narrow event, matcher, tested script, and clear owner.
- Project skills have concise frontmatter descriptions and do not grant broad tools unnecessarily.
- `.agents/skills/` changes are treated as local Codex skill changes, not Claude Code project skills.
- Instructions that compensated for old model limitations are removed or softened after major model releases.

## Report

Return:

- config files reviewed;
- issues found, ordered by risk;
- suggested edits;
- validation commands run;
- any follow-up that should not be part of the current PR.
