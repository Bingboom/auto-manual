# Claude Code Entrypoint

This file is the thin Claude Code map for this repo. Shared operating rules live in [`AGENTS.md`](AGENTS.md); read those first.

@AGENTS.md

## Delegation (Fable)

When the active model is Fable, do not do the work yourself. Never read the documentation, write the code, or run the tests in person — decompose the task and deploy every piece to others through Sub-agents and Dynamic Workflows, and keep your own turn to routing, briefing, and accepting their results. When staffing that work: (1) never assign Fable to it — Opus is the highest model an assignee may use; (2) the single exception is a high-stakes architecture review, which may be given to Fable.

## Start Small

Start Claude from the smallest directory that contains the work. Claude loads this root file plus the nearest child `CLAUDE.md` files as it moves through the tree.

- [`tools/`](tools/CLAUDE.md): Python build, queue, review, release, and validation implementation.
- [`docs/`](docs/CLAUDE.md): manual source, templates, manifests, renderers, review, and build outputs.
- [`docs/templates/`](docs/templates/CLAUDE.md): reusable RST templates, placeholder contracts, snippets, and recipes.
- [`data/`](data/CLAUDE.md): CSV source data and local phase2 mirror boundaries.
- [`configs/`](configs/CLAUDE.md): shared family configs and config-base inheritance.
- [`tests/`](tests/CLAUDE.md): unittest layout and targeted test selection.
- [`scripts/`](scripts/CLAUDE.md): branch, local-build, and service helper scripts.
- [`integrations/`](integrations/CLAUDE.md): OpenClaw and Feishu adapter packages.
- [`code-as-doc/`](code-as-doc/CLAUDE.md): architecture, roadmap, and maintainer documentation.
- [`user-guide/`](user-guide/CLAUDE.md): operator-facing workflow guides.
- [`.agents/`](.agents/CLAUDE.md): Codex/local skill inventory, distinct from Claude Code project skills.

## Claude Config

- Team-shared Claude Code settings live in [`.claude/settings.json`](.claude/settings.json).
- Personal permissions stay in `.claude/settings.local.json`; do not commit them.
- Hook management notes live in [`.claude/hooks/README.md`](.claude/hooks/README.md).
- Project skill management notes live in [`.claude/skills/README.md`](.claude/skills/README.md).
- When starting below repo root, confirm active project settings with `/config`; add subdirectory settings only after `/config-review`.
- Run `/config-review` before changing Claude settings, hooks, skills, or nested `CLAUDE.md` files.

Keep this root file as navigation only. Put directory-specific commands and conventions in the relevant child `CLAUDE.md`, and put reusable procedures in a skill.
