# Code-As-Doc Directory

`code-as-doc/` contains maintainer-facing architecture, workflow, roadmap, and implementation records.

## Map

- `architecture/`: stable design notes and system direction.
- `dev/`: implementation plans, branch/worktree guides, and maintainer runbooks.
- `reviews/`: completed or in-progress review artifacts.
- `tests/`: test reports and validation records.
- `optimization_project.md`: repo-level optimization roadmap.
- `code_optimization_log.md`: maintenance records for completed roadmap workstreams.

## Local Rules

- Use `architecture/System Evolution Strategy.md` for long-term architecture boundaries.
- Use `optimization_project.md` for current optimization priorities.
- When completing a phase or workstream from `optimization_project.md`, add a matching record to `code_optimization_log.md`.
- Keep user-facing workflow changes synchronized with `user-guide/` when operators are affected.

## Validation

- Docs link check: `python3 tools/check_doc_link_integrity.py`
- If docs describe build behavior, also run the relevant build command from the root `AGENTS.md`.
