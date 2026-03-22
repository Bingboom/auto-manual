# code-as-doc Documentation Map

Updated: 2026-03-22

This directory is the maintainer-facing documentation area.
Use it to find the single owning document for the topic you are changing.

## 1. Current Normative Maintainer Docs

These files describe the current repo behavior today.

- [`build_doc_guide.md`](build_doc_guide.md)
  - sole maintainer command reference
  - build entrypoints, command semantics, and output layout
- [`code_style_guide.md`](code_style_guide.md)
  - codebase maintainability rules
  - module boundaries and change-placement rules
- [`spec_master_user_guide.md`](spec_master_user_guide.md)
  - current phase1 CSV semantics
  - current placeholder, review-sync, and data-change rules
- [`generated_page_authoring.md`](generated_page_authoring.md)
  - page manifest vs static include decision
  - generated_page, recipe, and snippet authoring rules
- [`dev/git_branching_guide.md`](dev/git_branching_guide.md)
  - current Git branching policy
  - GitHub branch protection and merge settings for this repo
- [`code-as-doc.md`](code-as-doc.md)
  - documentation maintenance policy
  - doc update expectations when code or data changes
- [`title_style_guide.md`](title_style_guide.md)
  - heading and title source rules across outputs
- [`dev/code_review_checklist.md`](dev/code_review_checklist.md)
  - review checklist for code, config, data, and docs
- [`tests/README.md`](tests/README.md)
  - current test and smoke-check entrypoints

## 2. Architecture Docs With Different Boundaries

- [`architecture/Hello_Docs_Architecture.md`](architecture/Hello_Docs_Architecture.md)
  - current repository component map
  - current ownership boundaries between build, review, validation, and release modules
- [`architecture/Content_Data_Model.md`](architecture/Content_Data_Model.md)
  - future canonical content model
  - conceptual schema direction beyond the current CSV snapshot files
- [`architecture/System Evolution Strategy.md`](architecture/System%20Evolution%20Strategy.md)
  - long-term strategy
  - stable architectural principles and platform direction

## 3. User Workflow Docs

These live under [`../user-guide/`](../user-guide).

- [`../user-guide/hello_auto-doc.md`](../user-guide/hello_auto-doc.md)
  - current workflow
  - current editing surfaces and source-of-truth rules
- [`../user-guide/quick_start_guide.md`](../user-guide/quick_start_guide.md)
  - one concrete happy-path example

## 4. Historical Logs

These files are history records, not the current source of truth.

- [`code_optimization_log.md`](code_optimization_log.md)
- [`dev/dev_log.md`](dev/dev_log.md)
- [`tests/test_report-260301.md`](tests/test_report-260301.md)

## 5. Draft / Archive Docs

- [`dev/system_contract(draft_not_in_used).md`](dev/system_contract(draft_not_in_used).md)

Keep draft files clearly marked so they do not compete with active guides.

## 6. Maintenance Rule

When the repo changes:

- update the single document that owns the changed behavior
- link to adjacent docs instead of restating the same rules
- append completed roadmap phases or workstreams to [`code_optimization_log.md`](code_optimization_log.md)
