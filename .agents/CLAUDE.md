# Local Agent Skills Directory

`.agents/` contains repo-local skills for Codex and other local agents. These are not the same as Claude Code project skills, which live under `.claude/skills/`.

## Map

- `skills/*/SKILL.md`: local skill instructions.
- `skills/*/agents/openai.yaml`: agent bindings for skills that need them.
- `skills/*/scripts/`: helper scripts owned by the skill.
- `skills/*/references/`: supporting references loaded only when the skill calls for them.

## Local Rules

- Do not edit an existing `skills/**/SKILL.md` unless the task is about that skill.
- When adding or changing a skill, keep the entrypoint concise and move long references into `references/`.
- Prefer bundled scripts over retyping large procedures.
- For Claude Code project skills, use `.claude/skills/` instead.

## Validation

- Run any script-level smoke tests documented in the skill.
- For Word highlighting changes: exercise `.agents/skills/docx-highlight-changes/scripts/highlight_changes.py` on a fixture.
- For manual backport changes: run the extraction/residual scripts named by `.agents/skills/manual-revision-backport/SKILL.md`.
