# Tools Directory

`tools/` is the Python implementation plane behind `build.py`. Prefer `build.py` for user-facing behavior and edit files here only when the task is about low-level implementation.

## Map

- `build_*.py`: command dispatch, document build orchestration, publish, reports, runtime adapters.
- `check_*.py`: quality gates, docs checks, identity checks, maintainability guardrails.
- `queue_*.py` and `process_*queue*.py`: build/review queue routing, execution, writeback, and adapters.
- `diff_report*.py` and `release_manifest*.py`: traceability and release reporting.
- `utils/`: shared path and utility helpers. Keep repo paths centralized in `tools/utils/path_utils.py`.
- `csv_pages/`, `phase1/`, `phase2/`, `process_docs/`, `dingtalk/`: bounded implementation subpackages.

## Local Rules

- Do not hardcode repo segments such as `docs/_build`, `_review`, `reports/version_tracking`, or `renderers/latex`; use `tools/utils/path_utils.py` and `tools/build_paths.py`.
- Avoid adding model-specific defaults in CLI behavior, reports, or release paths.
- Keep user-facing command behavior in `build.py` and thin adapters; keep reusable logic in focused modules.

## Validation

- Python lint for this layer: `python3 -m ruff check build.py integrations tools tests scripts`
- Full logic suite: `python3 -m unittest`
- Targeted tests: `python3 -m unittest tests.test_<name>`
- Utility type checks: `python3 -m mypy tools/utils`
- Boundary guardrails: `python3 tools/check_maintainability_guardrails.py`
- Build behavior: `python3 build.py check --config configs/config.us.yaml --model JE-1000F --region US`
- Diff behavior: `python3 build.py diff-report --config configs/config.us.yaml --model JE-1000F --region US`
- Release traceability: `python3 build.py release-manifest --config configs/config.ja.yaml --model JE-1000F --region JP`
