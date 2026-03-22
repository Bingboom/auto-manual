# Documentation Maintenance Policy

Updated: 2026-03-15

This file defines how documentation must be maintained together with code and data changes.
The goal is simple:

- code history should remain traceable
- code and data should stay maintainable
- maintainers should not have to guess which document is still valid

## 1. Scope

This policy applies to changes in:

- [`build.py`](../build.py)
- [`tools/**/*.py`](../tools)
- [`docs/templates/**/*.rst`](../docs/templates)
- [`docs/_review/**`](../docs/_review)
- [`data/**/*.csv`](../data)
- `config*.yaml`
- [`tests/**`](../tests)
- [`README.md`](../README.md)
- [`code-as-doc/**`](../code-as-doc)
- [`user-guide/**`](../user-guide)

## 2. Documentation Roles

Current documentation roles are split like this:

- [`README.md`](../README.md)
  - repo overview
  - top-level build usage
- [`code-as-doc/*.md`](../code-as-doc)
  - maintainer rules
  - architecture and change-control notes
- [`user-guide/*.md`](../user-guide)
  - user workflow guides
  - review and publishing procedures
- [`code-as-doc/*log*.md`](../code-as-doc)
  - historical record

Do not mix normative guidance and historical notes in the same place without saying so explicitly.

## 3. Change Type -> Required Doc Updates

### 3.1 Build Entrypoint or Command Behavior

Examples:

- [`build.py`](../build.py) action changes
- output path changes
- review / publish / diff-report / preview / fast / release-manifest behavior changes

Must update:

- [`README.md`](../README.md)
- [`code-as-doc/build_doc_guide.md`](build_doc_guide.md)
- [`user-guide/hello_auto-doc.md`](../user-guide/hello_auto-doc.md)
- [`user-guide/quick_start_guide.md`](../user-guide/quick_start_guide.md) if an example workflow changed

### 3.2 Architecture or Maintainability Rules

Examples:

- source-of-truth changes
- `_review` / `_build` responsibility changes
- module boundary changes
- shared config strategy changes

Must update:

- [`code-as-doc/code_style_guide.md`](code_style_guide.md)
- [`code-as-doc/code-as-doc.md`](code-as-doc.md)
- [`code-as-doc/code_optimization_log.md`](code_optimization_log.md)

### 3.3 Data Contract Changes

Examples:

- [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) field semantics
- new `tpl_*` placeholders
- [`content_blocks.csv`](../data/phase1/content_blocks.csv) or [`spec_titles.csv`](../data/phase1/spec_titles.csv) usage changes
- sync-review behavior after CSV edits

Must update:

- [`code-as-doc/spec_master_user_guide.md`](spec_master_user_guide.md)
- [`user-guide/hello_auto-doc.md`](../user-guide/hello_auto-doc.md)
- [`user-guide/quick_start_guide.md`](../user-guide/quick_start_guide.md) if the workflow changed

### 3.4 Title or Layout Behavior Changes

Examples:

- title source changes
- CSS / LaTeX / Word heading behavior changes
- [`layout_params.csv`](../data/layout_params.csv) usage changes

Must update:

- [`code-as-doc/title_style_guide.md`](title_style_guide.md)
- [`code-as-doc/dev/layout_params_guide.md`](dev/layout_params_guide.md)
- [`code-as-doc/dev/layout_params_change_log_template.md`](dev/layout_params_change_log_template.md) if the tuning process changed

### 3.5 Test Strategy Changes

Examples:

- new smoke command
- new mandatory test gate
- changed review or publish verification path
- new CI workflow baseline

Must update:

- [`code-as-doc/tests/README.md`](tests/README.md)
- [`code-as-doc/dev/code_review_checklist.md`](dev/code_review_checklist.md)

### 3.6 Major Refactor or Milestone

Examples:

- new review layer
- cross-platform builder
- new diff-report stage
- new page contract system
- new release manifest stage

Must update:

- [`code-as-doc/code_optimization_log.md`](code_optimization_log.md)
- any normative guide affected by the new behavior

## 4. Mandatory Maintenance Rules

Rule 1:
Do not land a behavior change without updating the matching docs in the same change.

Rule 2:
If a document is historical, mark it as historical.
Do not let old commands look current.

Rule 3:
If a document is draft-only, say it is draft-only in the first screenful.

Rule 4:
If a workflow changes for reviewers or document editors, update [`user-guide/`](../user-guide) as well, not only [`code-as-doc/`](../code-as-doc).

Rule 5:
Do not treat generated runtime output as the authoring source unless the current workflow explicitly says so.
In the current system, `_review` is the authoring surface after review starts.

## 5. Minimal Verification Before Commit

Run the smallest check set that matches the change.

Recommended baseline:

```powershell
python build.py validate --config config.yaml
python -m unittest
```

If build flow changed:

```powershell
python build.py check --config config.yaml --model JE-1000F --region US
```

If JP review flow changed:

```powershell
python build.py publish --config config.ja.yaml --model JE-1000F --region JP
```

If diff-report changed:

```powershell
python build.py diff-report --config config.ja.yaml --model JE-1000F --region JP
```

If release traceability changed:

```powershell
python build.py release-manifest --config config.ja.yaml --model JE-1000F --region JP
```

## 6. Review Questions

Before merging, check:

- Is the current source of truth still clear?
- Did we accidentally reintroduce model-specific config duplication?
- Did we document new data assumptions?
- Did we preserve history while keeping normative docs current?
- Can another maintainer follow the updated commands without reading the code first?
