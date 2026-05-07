# Test Helpers

- Use [`test_helpers.py`](./test_helpers.py) for the lightweight shared scaffolding that appears across orchestration-heavy suites.
- Prefer `temp_test_root()` when a test needs an isolated repo-like root.
- Prefer `write_text()` when seeding fixture files so parent directories are created inline with the test setup.
- Prefer `write_lines()` when fixture setup reads more clearly as one list of expected lines.
- Prefer `patch_module_attrs()` when a test needs short-lived module-level overrides without open-coded `try/finally` restore blocks.
- Keep `test_process_build_queue.py` focused on end-to-end queue orchestration behavior; place independently testable routing/config/grouping coverage in `test_process_build_queue_routing.py`.
