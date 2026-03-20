# Code Style Guide

Updated: 2026-03-12

This file defines the current architecture and maintainability rules for the manual system.
It is not a generic Python style guide.
It focuses on keeping the build chain, review flow, and data model maintainable.

## 1. Current System Shape

The current manual system has four layers.

### 1.1 Template Seed Layer

- [`docs/templates/page_us-en/*.rst`](../docs/templates/page_us-en)
- [`docs/templates/page_eu/*.rst`](../docs/templates/page_eu)
- [`docs/templates/page_jp/*.rst`](../docs/templates/page_jp)

Purpose:

- shared page structure
- reusable wording
- initial draft creation

### 1.2 Data Layer

- [`data/phase1/Spec_Master.csv`](../data/phase1/Spec_Master.csv)
- [`data/phase1/Spec_Footnotes.csv`](../data/phase1/Spec_Footnotes.csv)
- [`data/phase1/spec_titles.csv`](../data/phase1/spec_titles.csv)
- [`data/phase1/content_blocks.csv`](../data/phase1/content_blocks.csv)
- [`data/phase1/page_registry.csv`](../data/phase1/page_registry.csv)
- [`data/layout_params.csv`](../data/layout_params.csv)

Purpose:

- structured product data
- placeholder values
- safety/spec content
- PDF layout parameters

### 1.3 Review Working Layer

- [`docs/_review/<model>/<region>/`](../docs/_review)

Purpose:

- target-specific authoring surface after review starts
- Git review history
- release source for reviewed manuals

### 1.4 Runtime Build Layer

- [`docs/_build/<model>/<region>/rst/`](../docs/_build)
- [`docs/_build/<model>/<region>/html/`](../docs/_build)
- [`docs/_build/<model>/<region>/word/`](../docs/_build)
- [`docs/_build/<model>/<region>/pdf/`](../docs/_build)

Purpose:

- generated runtime bundle
- export outputs

Rule:

- before review starts, create drafts from template + data
- after review starts, edit `_review`
- do not treat `_build` as the long-lived authoring source

## 2. Primary Entrypoint

The cross-platform primary entrypoint is:

- [`build.py`](../build.py)

[`build.py`](../build.py) orchestrates current high-level actions:

- `validate`
- `rst`
- `review`
- `check`
- `sync-review`
- `publish`
- `html`
- `word`
- `pdf`
- `all`
- `diff-report`
- `clean`

Low-level scripts still exist, but the default maintainer path should go through [`build.py`](../build.py).

## 3. Current Module Boundaries

### 3.1 Build Orchestration

- [`build.py`](../build.py)
- [`tools/build_docs.py`](../tools/build_docs.py)

Responsibilities:

- target resolution
- action routing
- runtime bundle preparation
- export ordering

### 3.2 Data Rendering

- [`tools/phase1_build.py`](../tools/phase1_build.py)
- [`tools/phase1/builder.py`](../tools/phase1/builder.py)
- [`tools/phase1/renderers*.py`](../tools/phase1)

Responsibilities:

- read phase1 CSV data
- render safety/spec content
- provide structured substitutions

### 3.3 Bundle Materialization

- [`tools/gen_index_bundle.py`](../tools/gen_index_bundle.py)

Responsibilities:

- resolve config pages
- materialize `index.rst`
- build runtime bundle layout

### 3.4 Review Support

- [`tools/review_bundle.py`](../tools/review_bundle.py)
- [`tools/review_support.py`](../tools/review_support.py)
- [`tools/sync_review.py`](../tools/sync_review.py)

Responsibilities:

- seed `_review`
- overlay review onto runtime bundles
- sync data-driven runtime files back into review

### 3.5 Validation and Contracts

- [`tools/validate_config.py`](../tools/validate_config.py)
- [`tools/validate_layout_params.py`](../tools/validate_layout_params.py)
- [`tools/check_docs.py`](../tools/check_docs.py)
- [`tools/page_contracts.py`](../tools/page_contracts.py)

Responsibilities:

- config schema checks
- layout param validation
- bundle quality checks
- page placeholder contracts

### 3.6 Export

- [`tools/word_bundle.py`](../tools/word_bundle.py)
- [`tools/word_bundle_common.py`](../tools/word_bundle_common.py)
- [`tools/word_bundle_html.py`](../tools/word_bundle_html.py)
- [`tools/word_bundle_docx.py`](../tools/word_bundle_docx.py)
- PDF build path via Sphinx / LaTeX in [`tools/build_docs.py`](../tools/build_docs.py)

### 3.7 Version Tracking

- [`tools/diff_report.py`](../tools/diff_report.py)

Responsibilities:

- Git-based file/page/field diff reports
- report index generation
- source-row tracing back to phase1 CSV

## 4. Maintainability Rules

### 4.1 Shared Config Rule

Prefer one config per template family, not one config per model.

Current rule:

- [`config.yaml`](../config.yaml): EN / US family
- [`config.ja.yaml`](../config.ja.yaml): JP family
- [`config.eu.yaml`](../config.eu.yaml): EU family

Do not clone a config only because the model changed.

### 4.2 No Model-Specific Logic in Templates by Default

Target-specific manual edits belong in:

- [`docs/_review/<model>/<region>/`](../docs/_review)

Shared changes belong in:

- [`docs/templates/**`](../docs/templates)
- [`data/phase1/**`](../data/phase1)

### 4.3 Use `sync-review` for Parameter Changes During Review

If CSV data changes while a manual is already in review, the safe default is:

```powershell
python build.py sync-review --config ... --model ... --region ...
```

Do not use `review --refresh-review` unless you intentionally want to reset the review bundle from template/data.

### 4.4 Keep Data Contracts Explicit

When a template page depends on placeholders, enforce it with a page contract under:

- [`docs/templates/contracts/*.yaml`](../docs/templates/contracts)

Current contract coverage already exists for:

- `03_product_overview`
- `05_operation_guide`
- `12_app_setup`

When adding new placeholder-heavy pages, add or update a contract.

### 4.5 Generated Output Is Not the Same as Review Source

[`docs/_build/**`](../docs/_build) can be committed for traceability, but it is still generated.
Current durable review authoring happens in `_review`.

### 4.6 Keep History and Rules Separate

- normative guidance goes in [`README.md`](../README.md), [`code-as-doc/`](../code-as-doc), and [`user-guide/`](../user-guide)
- historical milestones go in [`code-as-doc/code_optimization_log.md`](code_optimization_log.md) and [`code-as-doc/dev/dev_log.md`](dev/dev_log.md)

Do not hide current rules inside historical logs.

## 5. Code-Level Expectations

- Put reusable target logic in shared helpers instead of duplicating it across entry scripts.
- Keep rendering logic separate from file-system side effects where practical.
- Keep error messages specific enough to identify the file, target, and field involved.
- Prefer fail-fast validation over silent skipping.
- When a workflow changes, update the doc that owns that workflow in the same change.

## 6. Test Expectations

Baseline:

```powershell
python -m unittest
```

When build or review flow changes, also run at least one targeted smoke command:

```powershell
python build.py check --config config.yaml --model JE-1000F --region US
python build.py publish --config config.ja.yaml --model JE-1000F --region JP
```

When diff-report changes:

```powershell
python build.py diff-report --config config.ja.yaml --tracked-root docs/_review/JE-1000F/JP
```

## 7. Review Triggers

Update this file when any of these change:

- the source-of-truth layers
- the default build entrypoint
- the role of `_review` or `_build`
- config family strategy
- page contract policy
- major validation or reporting stages
