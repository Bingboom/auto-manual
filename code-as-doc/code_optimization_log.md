# Code Optimization Log

Updated: 2026-04-04

This file records major maintainability milestones.
It is a history log, not the day-to-day usage guide.

For current rules, see:

- [`code-as-doc/README.md`](README.md)
- [`code-as-doc/build_doc_guide.md`](build_doc_guide.md)
- [`code-as-doc/code_style_guide.md`](code_style_guide.md)
- [`user-guide/hello_auto-doc.md`](../user-guide/hello_auto-doc.md)

## 1. 2026-03-08: Initial P0 / P1 Refactor Wave

Main outcomes:

- extracted shared target resolution helpers
- reduced duplicated target/token logic across build entry scripts
- split [`tools/phase1/renderers.py`](../tools/phase1/renderers.py) into smaller renderer modules
- split [`tools/word_bundle.py`](../tools/word_bundle.py) into `common / html / docx`
- introduced stronger config page parsing
- cleaned build noise and cache tracking from Git

Why it mattered:

- less duplicated logic
- clearer code ownership
- easier testing and future refactor work

## 2. 2026-03-11: Cross-Platform Builder and Output Layout

Main outcomes:

- introduced [`build.py`](../build.py) as the primary cross-platform entrypoint
- normalized actions such as `rst`, `word`, `html`, `pdf`, `all`
- grouped runtime outputs by target under:
  - [`docs/_build/<model>/<region>/rst`](../docs/_build)
  - [`docs/_build/<model>/<region>/html`](../docs/_build)
  - [`docs/_build/<model>/<region>/word`](../docs/_build)
  - [`docs/_build/<model>/<region>/pdf`](../docs/_build)
- moved away from relying on `make` as the main user entrypoint

Why it mattered:

- Windows, macOS, and CI can all use the same command surface
- target outputs stopped overwriting each other as easily

## 3. 2026-03-11 to 2026-03-12: Review-First Workflow

Main outcomes:

- introduced [`docs/_review/<model>/<region>/`](../docs/_review) as the review working layer
- added `build.py review`
- added `build.py check`
- added `build.py sync-review`
- changed default build behavior to overlay `_review` onto runtime bundles when present
- made reviewed content the real daily editing surface after review starts

Why it mattered:

- target-specific review edits no longer need to mutate shared templates
- Git history becomes meaningful at the target level
- publishing can happen from reviewed text instead of only from raw template output

## 4. Data and Contract Improvements

Main outcomes:

- page contracts added for placeholder-heavy pages
- current contract coverage includes:
  - `03_product_overview`
  - `05_operation_guide`
  - `12_app_setup`
- `check` now validates more than config syntax:
  - product identity
  - unresolved placeholders
  - missing includes
  - missing assets
  - contract-required placeholders

Why it mattered:

- missing parameter data is caught earlier
- template drift is easier to detect

## 5. Revision Tracking and Reports

Main outcomes:

- introduced `build.py diff-report`
- added file, page, and field level report exports
- added HTML report pages and report index pages
- added source tracing back to [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) rows where possible
- added first-baseline detection and `--ignore-initial-adds`

Why it mattered:

- document review history can be exported as tables
- reviewers can see not only which files changed, but which fields changed

## 6. Shared Config Family Rule

Main outcomes:

- stopped normalizing around one config per model
- consolidated to shared family configs:
  - [`config.us.yaml`](../config.us.yaml)
  - [`config.ja.yaml`](../config.ja.yaml)
- active family configs are now centered on US / JP shared configs instead of per-model files
- moved per-target differences to CLI target selection and phase1 data

Why it mattered:

- less config sprawl
- easier maintenance for multi-model families

## 7. Current Direction

The system is now optimized around:

- shared template families
- phase1 data as the structured source
- `_review` as the target editing surface
- [`build.py`](../build.py) as the primary command surface
- `diff-report` as the revision export layer

Future optimization logs should keep recording only meaningful maintainability milestones, not every small edit.

## 8. 2026-03-15: Stability, Contract V2, Release Traceability, and Preview Flow

Main outcomes:

- removed hardcoded `JE-1000F` defaults from `build.py diff-report`
- fixed runtime bundle asset classification when canonical paths pass through symlinked or temp-backed roots
- limited review overrides to `_assets`, `_static`, and `renderers` so review metadata files do not leak into publish bundles
- added stale identity scanning to `check`
- extended page contracts with `required_spec_keys`, `required_page_values`, `required_assets`, and `allowed_*` scope fields
- added `build.py release-manifest`
- added `build.py preview` and `build.py fast`
- added the GitHub Actions baseline workflow at [`.github/workflows/manual-validation.yml`](../.github/workflows/manual-validation.yml)

Why it mattered:

- target-aware diff reports no longer silently inspect the wrong subtree
- review metadata is now separated cleanly from runtime publish inputs
- missing CSV keys, missing assets, and stale model names are caught earlier in `check`
- release outputs now have a JSON / CSV traceability record with file hashes
- maintainers have a fast page-scoped preview path and a lightweight runtime draft path

## 9. 2026-03-31: Phase2 Snapshot Sync and Shared Data-Root Resolution

Main outcomes:

- added [`build.py sync-data`](../build.py) as the explicit local sync step for Feishu/Lark content snapshots
- introduced [`tools/data_snapshot.py`](../tools/data_snapshot.py) to centralize structured-data path resolution
- added `--data-root` support across build, check, diff-report, and release-manifest entrypoints
- added [`data/phase2/`](../data/phase2) as the preferred frozen snapshot root while keeping [`data/phase1/`](../data/phase1) as the legacy baseline
- kept [`data/phase1/page_registry.csv`](../data/phase1/page_registry.csv) and [`data/layout_params.csv`](../data/layout_params.csv) as repo-maintained inputs outside the Feishu sync flow

Why it mattered:

- online content governance is now separated cleanly from the offline build contract
- build-time consumers no longer need their own ad hoc CSV path rules
- maintainers can switch between phase1 and phase2 snapshots without changing manifests or renderer logic

## 10. 2026-04-04: Queue Action Normalization and Staged Verification Outputs

Main outcomes:

- made `Workflow_action` the primary queue-action field for `Document_link` while keeping `Doc_phase` as a compatibility fallback
- updated local/GitHub queue entrypoints to prefer `--workflow-action build-draft-package|publish`
- added `--staging-root` and `AUTO_MANUAL_STAGING_ROOT` so `docs/_build`, `reports/version_tracking`, and `reports/releases` can be redirected under an isolated root during verification
- extended `check`, `sync-review`, `review_bundle`, `release-manifest`, and publish-path helpers to read/write against staged output roots
- updated maintainer docs to keep `page_registry`, page selection/applicability, and `layout_params` explicitly repo-owned while queue data stays phase2-driven

Why it mattered:

- queue semantics are now less ambiguous for operators and Feishu automation authors
- local parity checks and smoke runs no longer need to pollute tracked output directories
- release-path consumers can rely on one normalized action vocabulary and one isolated-output mechanism
