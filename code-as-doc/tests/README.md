# Tests Guide

Updated: 2026-11-18

This file describes the current test entrypoints and recommended smoke checks.

## 1. Run the Full Test Suite

```powershell
python -m tests.run_fast --all          # every module, in parallel: what CI `unit` runs
python -m tests.run_fast --shard 2/4    # exactly what CI shard `unit-shard (2)` runs
python -m tests.run_fast                # local fast tier (or: make test-fast)
python -m unittest                      # one process, sequential; 30+ minutes
```

[`tests/run_fast.py`](../../tests/run_fast.py) runs every test module in its own
Python process, one worker per CPU (`-j N` to change), heaviest modules first. It
prints one line per module, the slowest modules (`--durations N`, `0` for all),
and the full output of every failed module, and exits non-zero on any failure,
error, import error, crash, or a module that ran no tests (unless the manifest
declares it under `zero_test_modules`). A module that raises `unittest.SkipTest`
on import counts as one skipped test, as under discovery. Each module has a
15-minute limit (`MODULE_TIMEOUT_SECONDS`): past it, the module and every process
it started are killed and it fails as `timed out after 900 s` with the tail of
its output, so a hang is named instead of running into the CI job timeout.
`--write-timings` writes nothing unless every module passed. `--list` shows a
selection without running it. The fast tier skips modules recorded at 5 seconds
or more; a module not yet in the manifest always runs.

The CI `unit` check (`Manual Validation`) is the aggregate of the `unit-shard`
matrix: each shard runs `python -m tests.run_fast --shard K/N`, and `unit` fails
when any shard failed, was cancelled or was skipped. Shards come from the timing
manifest [`tests/unit_timings.json`](../../tests/unit_timings.json): modules are
dealt heaviest first to the lightest shard, so every module runs in exactly one
shard; a module the manifest does not know weighs `default_seconds`.
`tests/test_run_fast.py` checks the shards against real `unittest` discovery.
Refresh the manifest after adding or moving heavy tests, on Python 3.12 +
`requirements.lock`:

```powershell
python -m tests.run_fast --all --write-timings
```

Each module runs in isolation, so a module must import what it uses (for
example `import unittest.mock`) and must not rely on another module having run
first. A failure that appears only under `run_fast` but not `python -m unittest`
is such a hidden order dependency in the test module.

CI no longer runs the single-process `python -m unittest` mode. Order dependence
that only shows up when every module shares one process (one module's leftover
state breaking or masking another's tests) is therefore not gated; run
`python -m unittest` yourself when a change touches shared global state.

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
python build.py check --config configs/config.us-en.yaml --model JE-1000F --region US --data-root tests/fixtures/phase2 --staging-root .tmp/staging
python build.py word --config configs/config.us.yaml --model JE-1000F --region US
```

### 2.2 JP family

```powershell
python build.py check --config configs/config.ja.yaml --model JE-1000F --region JP --data-root tests/fixtures/phase2 --staging-root .tmp/staging
python build.py publish --config configs/config.ja.yaml --model JE-1000F --region JP
python build.py release-manifest --config configs/config.ja.yaml --model JE-1000F --region JP --data-root tests/fixtures/phase2 --staging-root .tmp/staging
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
