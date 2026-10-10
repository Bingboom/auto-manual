# User Guide Directory

`user-guide/` contains operator-facing workflow documentation.

## Map

- `hello_auto-doc.md`: index of the current human workflow guide; its topic pages live in `hello_auto-doc/`.
- `quick_start_guide.md`: happy-path onboarding and sample commands.
- `closed_loop_ops_guide.md`: closed-loop operator playbook.
- `two_plane_map.md`: authoritative map of the two repositories and Feishu base sets.

## Local Rules

- If a code change affects workflow, editing surface, environment setup, or release flow, update the owning page under `hello_auto-doc/` (the index only when a page is added, renamed or re-scoped).
- If a change affects onboarding or sample commands, update `quick_start_guide.md`.
- Keep commands copy-pasteable and aligned with `build.py`.

## Validation

- Docs link check: `python3 -m tools.check_doc_link_integrity`
