# Tests Directory

`tests/` uses Python `unittest`. Test files are organized by repo behavior, not by a separate test framework.

## Map

- `test_build_*.py`: build command and build pipeline coverage.
- `test_check_*.py`: validation and guardrail coverage.
- `test_queue_*.py`, `test_process_*queue*.py`: queue routing and writeback coverage.
- `test_diff_report.py`, `test_release_manifest.py`: traceability outputs.
- `fixtures/`: committed fixtures only; do not overwrite broad fixture trees casually.

## Local Rules

- Prefer targeted unittest modules while developing, then run the broader suite when behavior touches shared tooling.
- Add regression tests near the behavior being changed.
- Keep generated verification artifacts out of tests unless they are explicit fixtures.

## Validation

- One module: `python3 -m unittest tests.test_<name>`
- Several modules: `python3 -m unittest tests.test_config_loader tests.test_validate_config`
- Full suite: `python3 -m unittest`
- Lint when tests or Python implementation changed: `python3 -m ruff check build.py integrations tools tests scripts`
