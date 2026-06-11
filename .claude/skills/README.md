# Claude Code Project Skills

Project skills in `.claude/skills/` load on demand for this repo. They are separate from Codex/local skills under `.agents/skills/`.

## Current Skills

- `config-review`: reviews Claude Code scaffolding, deny rules, hooks, skills, and nested `CLAUDE.md` files for drift and bloat.

## When To Add A Skill

Add a project skill when a procedure is useful across sessions but too specific or too long for `CLAUDE.md`:

- repeatable review checklists;
- manual rewrite/backport workflows that need supporting files;
- release or build procedures with several decision points;
- domain-specific audit routines.

Keep the root `CLAUDE.md` as a map. Put reusable procedures here.

## Review Checklist

- Keep `SKILL.md` concise; move long references to `references/`.
- Use frontmatter `description` so Claude loads the skill only when relevant.
- Use `paths` when a skill applies only to a subtree.
- Do not grant broad `allowed-tools` unless the skill genuinely needs them.
- Test direct invocation with `/skill-name` after changing the skill.
- Run `/config-review` before opening a PR that changes project skills.
