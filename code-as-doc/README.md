# code-as-doc Documentation Map

Updated: 2026-03-12

This directory is the maintainer-facing documentation area.
It explains how the current manual system is built, reviewed, maintained, and evolved.

There are two documentation roots in this repo:

- [`code-as-doc/`](../code-as-doc): maintainer guides, architecture notes, review checklists, change history
- [`user-guide/`](../user-guide): user-facing workflow guides for daily drafting, review, publishing, and version tracking

## 1. Current Normative Maintainer Docs

Read these first when you need the current rules.

- [`code-as-doc/build_doc_guide.md`](build_doc_guide.md)
  - Windows and PowerShell build guide
  - current [`build.py`](../build.py) commands
  - output layout and release flow
- [`code-as-doc/code-as-doc.md`](code-as-doc.md)
  - documentation maintenance policy
  - which docs must be updated when code or data changes
- [`code-as-doc/code_style_guide.md`](code_style_guide.md)
  - current architecture boundaries
  - code and data maintainability rules
- [`code-as-doc/spec_master_user_guide.md`](spec_master_user_guide.md)
  - [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) and related phase1 CSV rules
  - placeholder resolution and review sync behavior
- [`code-as-doc/title_style_guide.md`](title_style_guide.md)
  - heading/title source rules across HTML, Word, and PDF
- [`code-as-doc/dev/code_review_checklist.md`](dev/code_review_checklist.md)
  - review checklist for code, config, data, and doc changes
- [`code-as-doc/dev/layout_params_guide.md`](dev/layout_params_guide.md)
  - [`data/layout_params.csv`](../data/layout_params.csv) usage and PDF layout tuning rules
- [`code-as-doc/dev/layout_params_change_log_template.md`](dev/layout_params_change_log_template.md)
  - template for recording layout tuning changes
- [`code-as-doc/tests/README.md`](tests/README.md)
  - current test and smoke-check entrypoints

## 2. Current User-Facing Workflow Docs

These live under [`user-guide/`](../user-guide).

- [`user-guide/hello_auto-doc.md`](../user-guide/hello_auto-doc.md)
  - current source-of-truth rules
  - review-first build flow
  - diff-report usage
- [`user-guide/quick_start_guide.md`](../user-guide/quick_start_guide.md)
  - concrete end-to-end example
  - currently centered on `JE-1000F / JP`

## 3. Historical Logs

These files are kept for traceability.
They are history records, not the current source of truth.

- [`code-as-doc/code_optimization_log.md`](code_optimization_log.md)
- [`code-as-doc/dev/dev_log.md`](dev/dev_log.md)
- [`code-as-doc/tests/test_report-260301.md`](tests/test_report-260301.md)

Use them to understand why the current structure exists.
Do not copy old commands from them without checking the current guides first.

## 4. Draft / Not Normative

- [`code-as-doc/dev/system_contract(draft_not_in_used).md`](dev/system_contract(draft_not_in_used).md)

This file is kept only as an archive draft.
It is not the contract used by the current build and review flow.

## 5. Maintenance Rule

When the repo changes, update documentation at the same time.

Minimum expectation:

- command behavior changes: update [`build_doc_guide.md`](build_doc_guide.md)
- architecture or maintainability rules change: update [`code_style_guide.md`](code_style_guide.md)
- phase1 CSV semantics change: update [`spec_master_user_guide.md`](spec_master_user_guide.md)
- title or heading behavior changes: update [`title_style_guide.md`](title_style_guide.md)
- review workflow changes: update [`user-guide/hello_auto-doc.md`](../user-guide/hello_auto-doc.md) and [`user-guide/quick_start_guide.md`](../user-guide/quick_start_guide.md)
- major refactor or process milestone: append to [`code_optimization_log.md`](code_optimization_log.md)

If a document is no longer normative, mark it clearly instead of letting it silently drift.
