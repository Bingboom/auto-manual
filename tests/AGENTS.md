# Tests Directory

`tests/` uses Python `unittest`, organized by repository behavior.

## Map

- `test_build_*.py`: build command and pipeline coverage.
- `test_check_*.py`: validation and guardrail coverage.
- `test_queue_*.py`, `test_process_*queue*.py`: queue routing and writeback coverage.
- `test_diff_report.py`, `test_release_manifest.py`: traceability outputs.
- `fixtures/`: committed fixtures; do not overwrite broad fixture trees casually.

## Local Rules

- Prefer targeted unittest modules while developing, then run the broader suite when shared tooling changes.
- Add regression tests beside the behavior under test.
- Keep generated verification artifacts out of tests unless they are explicit fixtures.

## Validation

- One module: `python3 -m unittest tests.test_<name>`
- Full suite: `python3 -m unittest`
- Lint: `python3 -m ruff check build.py integrations tools tests scripts`
