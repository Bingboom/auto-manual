# Claude Code Entrypoint

This file is the thin Claude Code map for this repo. Shared operating rules live in [`AGENTS.md`](AGENTS.md); read those first.

@AGENTS.md

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
