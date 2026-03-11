# Historical Test Report - 2026-03-01

Updated: 2026-03-12

This file is preserved as an archive summary of an earlier regression round.
It is not the current test contract.

## 1. What This Historical Report Covered

At that time the main focus was:

- phase1 renderer fail-fast behavior
- schema and CSV diagnostics
- older SKU-related selection behavior
- layout parameter validation
- PDF build smoke validation

## 2. What Is Obsolete Today

These assumptions are now historical:

- old `--sku` centric build discussions
- `build.default_sku`
- older [`docs/generated/...`](../../docs)-first mental model

Current flow is instead centered on:

- [`build.py`](../../build.py)
- shared config families
- `model + region`
- `_review` as the review editing surface
- `publish` and `diff-report`

## 3. Current Replacement

For the current test surface, use:

- [`code-as-doc/tests/README.md`](README.md)

For the current review and publishing workflow, use:

- [`user-guide/hello_auto-doc.md`](../../user-guide/hello_auto-doc.md)
- [`user-guide/quick_start_guide.md`](../../user-guide/quick_start_guide.md)
