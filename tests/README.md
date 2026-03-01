# Tests

Run all tests:

```bash
python3 -m unittest discover -s tests -v
```

Notes:

- Current tests are all hard assertions and should pass.
- If new known issues are intentionally tracked before fix, use `@unittest.expectedFailure` temporarily and remove it after remediation.
