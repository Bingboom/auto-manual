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
- Patch the name where the code under test looks it up, not a re-export on a facade module (`tools.build_docs`, `tools.process_build_queue`, `tools.process_review_start_queue`, `tools.cloud_doc_backport`). Pass external boundaries (lark-cli, git, subprocess, clock, network) in as parameters where the code offers them. For `process_build_queue.process_build_queue`, pass `deps=replace(default_queue_deps(process_build_queue), <field>=...)` (see `tools/process_build_queue_deps.py`) instead of patching the facade. `python3 tools/check_facade_patch_ratchet.py check` (part of the maintainability guardrails) fails on new or grown facade patches.
- Keep generated verification artifacts out of tests unless they are explicit fixtures.

## Validation

- One module: `python3 -m unittest tests.test_<name>`
- Full suite: `python3 -m unittest`
- Local fast tier: `python3 -m tests.run_fast` (or `make test-fast`) runs every module except `tests/slow_modules.txt` in parallel processes (`-j N`, `--all` adds the slow modules). It is for iteration only; CI and pre-PR validation stay `python3 -m unittest`.
- Node UI tests, when a portal script or a `*.test.mjs` file changes: `node --test tests/*.test.mjs`
- Lint: `python3 -m ruff check build.py integrations tools tests scripts`
