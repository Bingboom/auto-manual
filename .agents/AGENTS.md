# Codex Local Skills

`.agents/` contains repo-local Codex skills and their supporting resources.

## Map

- `skills/*/SKILL.md`: skill instructions and trigger metadata.
- `skills/*/agents/openai.yaml`: optional UI bindings and default prompts.
- `skills/*/scripts/`: deterministic helpers owned by a skill.
- `skills/*/references/`: supporting material loaded only when needed.

## Local Rules

- Do not edit an existing `skills/**/SKILL.md` unless the task is about that skill.
- Keep skill entrypoints concise; move long references into `references/`.
- Prefer bundled scripts over retyping deterministic procedures.
- Validate changed skills with the skill creator quick validator and run documented script smoke tests.
