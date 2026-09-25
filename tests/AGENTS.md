# Tests Directory

`tests/` uses Python `unittest`, organized by repository behavior. Browser-side portal scripts also have Node UI tests (`*.test.mjs`) on Node's built-in test runner.

## Map

- `test_build_*.py`: build command and pipeline coverage.
- `test_check_*.py`: validation and guardrail coverage.
- `test_queue_*.py`, `test_process_*queue*.py`: queue routing and writeback coverage.
- `test_diff_report.py`, `test_release_manifest.py`: traceability outputs.
- `*.test.mjs`: Node UI tests for `tools/rtd_portal_assets/_static/*.js` against a minimal fake DOM; the `Manual Validation` `node-ui` job runs every file.
- `fixtures/`: committed fixtures; do not overwrite broad fixture trees casually.

## Local Rules

- Prefer targeted unittest modules while developing, then run the broader suite when shared tooling changes.
- Add regression tests beside the behavior under test.
- Keep generated verification artifacts out of tests unless they are explicit fixtures.

## Validation

- One module: `python3 -m unittest tests.test_<name>`
- Full suite: `python3 -m unittest`
- Node UI tests, when a portal script or a `*.test.mjs` file changes: `node --test tests/*.test.mjs`
- Lint: `python3 -m ruff check build.py integrations tools tests scripts`
