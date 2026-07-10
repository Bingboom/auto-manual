# Tools Directory

`tools/` is the Python implementation plane behind `build.py`. Prefer `build.py` for user-facing behavior.

## Map

- `build_*.py`: command dispatch, document build orchestration, publish, reports, runtime adapters.
- `check_*.py`: quality gates, docs checks, identity checks, maintainability guardrails.
- `queue_*.py` and `process_*queue*.py`: queue routing, execution, writeback, and adapters.
- `diff_report*.py` and `release_manifest*.py`: traceability and release reporting.
- `utils/`: shared path and utility helpers; keep repo paths centralized in `tools/utils/path_utils.py`.
- `csv_pages/`, `idml/`, `process_docs/`, `dingtalk/`: bounded implementation subpackages.

## Local Rules

- Do not hardcode repo segments such as `docs/_build`, `_review`, `reports/version_tracking`, or `renderers/latex`; use `tools/utils/path_utils.py` and `tools/build_paths.py`.
- Avoid model-specific defaults in CLI behavior, reports, or release paths.
- Keep user-facing command behavior in `build.py` and thin adapters; keep reusable logic in focused modules.

## Validation

- Lint: `python3 -m ruff check build.py integrations tools tests scripts`
- Full logic suite: `python3 -m unittest`
- Utility types: `python3 -m mypy tools/utils`
- Guardrails: `python3 tools/check_maintainability_guardrails.py`
- Build check: `python3 build.py check --config configs/config.us.yaml --model JE-1000F --region US`
