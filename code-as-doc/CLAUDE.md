# Code-As-Doc Directory

`code-as-doc/` contains maintainer-facing architecture, workflow, roadmap, and implementation records.

## Map

- `architecture/`: stable design notes and system direction.
- `dev/`: implementation plans, branch/worktree guides, and maintainer runbooks.
- `reviews/`: completed or in-progress review artifacts.
- `tests/`: test reports and validation records.
- `optimization_project.md`: repo-level optimization roadmap.
- `code_optimization_log.md`: recent maintenance records for completed roadmap workstreams, newest first; older records are in `code_optimization_log_archive.md`.
- `build_doc_guide.md`: index of the maintainer build guide; its topic pages live in `build_doc_guide/`.
- `dev/merge_authorizations.md`: gate-on-green protocol and live grants; expired rows are in `dev/merge_authorizations_archive.md`.

## Local Rules

- Use `System Evolution Strategy.md` for long-term architecture boundaries.
- Use `optimization_project.md` for current optimization priorities.
- When completing a phase or workstream from `optimization_project.md`, add a matching record at the top of `code_optimization_log.md`.
- Put new build-guide content on the owning `build_doc_guide/` page, not in the index; grep archives and logs instead of reading them whole.
- Keep user-facing workflow changes synchronized with `user-guide/` when the change affects operators.

## Validation

- Docs link check: `python3 -m tools.check_doc_link_integrity`
- If docs describe build behavior, also run the relevant build command from `AGENTS.md` validation.
