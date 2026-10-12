# Tests Guide

Updated: 2026-09-30

This file describes the current test entrypoints and recommended smoke checks.

## 1. Run the Full Test Suite

```powershell
python -m unittest
```

This single-process run is what CI and pre-PR validation use (about 15 minutes).
For local iteration there is a parallel fast tier:

```powershell
python -m tests.run_fast          # or: make test-fast; about 3 minutes on 4 CPUs
python -m tests.run_fast --all    # every module, still in parallel
```

It runs each batch of test modules in its own process and skips the modules in
[`../../tests/slow_modules.txt`](../../tests/slow_modules.txt) (real Sphinx builds,
IDML golden exports, frozen-AI replays), which lists each one's measured slow-test
time. Refresh the list from `python -m unittest --durations 400` on Python 3.12 +
`requirements.lock`; a test fails if it names a module that no longer exists.

Current test coverage includes:

- build script behavior
- target resolution
- config validation
- layout param validation
- CSV page rendering from `data/phase2`
- review bundle flow
- sync-review
- diff-report
- page contracts
- stale identity scan
- release manifest
- preview / fast
- Word bundle logic

## 2. Baseline Smoke Checks

### 2.1 EN / US family

```powershell
python build.py check --config configs/config.us.yaml --model JE-1000F --region US
python build.py word --config configs/config.us.yaml --model JE-1000F --region US
```

### 2.2 JP family

```powershell
python build.py check --config configs/config.ja.yaml --model JE-1000F --region JP
python build.py publish --config configs/config.ja.yaml --model JE-1000F --region JP
python build.py release-manifest --config configs/config.ja.yaml --model JE-1000F --region JP
```

### 2.3 JP production-IDML smoke

The reproducible command, structural result, source identities, and acceptance
boundary are recorded in
[`jp_idml_smoke_acceptance_2026-07-31.md`](jp_idml_smoke_acceptance_2026-07-31.md).

## 3. Review-Specific Smoke Checks

Seed review once:

```powershell
python build.py review --config configs/config.ja.yaml --model JE-1000F --region JP
```

Refresh data-driven review content:

```powershell
python build.py sync-review --config configs/config.ja.yaml --model JE-1000F --region JP
```

Export review revision report:

```powershell
python build.py diff-report --config configs/config.ja.yaml --model JE-1000F --region JP
```

Preview one page and prepare a fast runtime draft:

```powershell
python build.py preview --config configs/config.us.yaml --model JE-1000F --region US --page 03_product_overview_placeholder
python build.py fast --config configs/config.us.yaml --model JE-1000F --region US
```

## 4. Expected Output Examples

- Word:
  - [`docs/_build/JE-1000F/JP/word/manual_je1000f_jp.docx`](../../docs/_build/JE-1000F/JP/word/manual_je1000f_jp.docx)
- PDF:
  - [`docs/_build/JE-1000F/JP/pdf/manual_je1000f_jp.pdf`](../../docs/_build/JE-1000F/JP)
- Review bundle:
  - [`docs/_review/JE-1000F/JP/`](../../docs/_review/JE-1000F/JP)
- Diff report:
  - [`reports/version_tracking/JE-1000F/JP/`](../../reports/version_tracking/JE-1000F/JP)
- Release manifest:
  - [`reports/releases/JE-1000F/JP/`](../../reports/releases/JE-1000F/JP)
- Preview bundle:
  - [`docs/_build/JE-1000F/US/preview/03_product_overview_placeholder/rst/`](../../docs/_build/JE-1000F/US/preview/03_product_overview_placeholder/rst)

## 5. Notes

- Historical test reports under [`code-as-doc/tests/`](../tests) are archive material, not the current source of truth.
- Prefer [`build.py`](../../build.py) for smoke checks instead of calling old low-level scripts directly.
- CI baseline lives in [`.github/workflows/manual-validation.yml`](../../.github/workflows/manual-validation.yml) and currently runs `unit`, `doctor-en`, `check-en`, and `check-jp`.
