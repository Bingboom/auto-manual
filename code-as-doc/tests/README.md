# Tests Guide

Updated: 2026-03-22

This file describes the current test entrypoints and recommended smoke checks.

## 1. Run the Full Test Suite

```powershell
python -m unittest
```

Current test coverage includes:

- build script behavior
- target resolution
- config validation
- layout param validation
- phase1 rendering
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
python build.py check --config config.us.yaml --model JE-1000F --region US
python build.py word --config config.us.yaml --model JE-1000F --region US
```

### 2.2 JP family

```powershell
python build.py check --config config.ja.yaml --model JE-1000F --region JP
python build.py publish --config config.ja.yaml --model JE-1000F --region JP
python build.py release-manifest --config config.ja.yaml --model JE-1000F --region JP
```

## 3. Review-Specific Smoke Checks

Seed review once:

```powershell
python build.py review --config config.ja.yaml --model JE-1000F --region JP
```

Refresh data-driven review content:

```powershell
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP
```

Export review revision report:

```powershell
python build.py diff-report --config config.ja.yaml --model JE-1000F --region JP
```

Preview one page and prepare a fast runtime draft:

```powershell
python build.py preview --config config.us.yaml --model JE-1000F --region US --page 03_product_overview_placeholder
python build.py fast --config config.us.yaml --model JE-1000F --region US
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

