# Docs Directory

`docs/` contains the manual source surface, render configuration, review surface, and generated build output.

## Map

- `templates/`: reusable RST source, recipes, snippets, Word templates, and contracts. See [`templates/CLAUDE.md`](templates/CLAUDE.md).
- `manifests/`: manual composition manifests by market/language.
- `renderers/`: render-time assets and LaTeX renderer configuration.
- `_review/`: target review surface after review starts; do not delete or rename committed review files without explicit confirmation.
- `_build/`: generated output only. Do not hand-edit.
- `index.rst`: generated index entrypoint; do not hand-edit unless the task is about index generation.

## Local Rules

- Shared source changes usually belong under `docs/templates/` or `data/phase2/`.
- If a target is already in review, prefer `sync-review` over `review --refresh-review` for data-driven updates.
- Review overrides must stay under `overrides/_assets/`, `overrides/_static/`, or `overrides/renderers/`.
- Keep generated artifacts out of manual reasoning unless the task is explicitly about build output.

## Validation

- Docs link check when editing docs or guides: `python3 tools/check_doc_link_integrity.py`
- US build/quality gate: `python3 build.py check --config configs/config.us.yaml --model JE-1000F --region US`
- JP review/publish path: `python3 build.py publish --config configs/config.ja.yaml --model JE-1000F --region JP`
- Diff report path: `python3 build.py diff-report --config configs/config.us.yaml --model JE-1000F --region US`
