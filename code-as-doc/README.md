# code-as-doc Documentation Map

Updated: 2026-04-12

This directory is the maintainer-facing documentation area.
Use it to find the single current source of truth for the topic you are changing.

## 1. Start Here

Use these docs first before opening older plans or historical trackers:

- [`build_doc_guide.md`](build_doc_guide.md)
  - current maintainer command reference
  - build, review, check, diff, publish, and release semantics
- [`../user-guide/hello_auto-doc.md`](../user-guide/hello_auto-doc.md)
  - current workflow and editing-surface rules
- [`../user-guide/quick_start_guide.md`](../user-guide/quick_start_guide.md)
  - one concrete happy-path example
- [`architecture/README.md`](architecture/README.md)
  - active architecture and integration doc map

## 2. Current Normative Maintainer Docs

These files describe the repo behavior that should be maintained today.

- [`build_doc_guide.md`](build_doc_guide.md)
  - maintainer commands and output layout
- [`code_style_guide.md`](code_style_guide.md)
  - codebase maintainability rules and change-placement boundaries
- [`code-as-doc.md`](code-as-doc.md)
  - documentation maintenance policy
- [`spec_master_user_guide.md`](spec_master_user_guide.md)
  - current CSV, placeholder, and sync-review data semantics
- [`manual_family_guide.md`](manual_family_guide.md)
  - family-specific template boundaries that still matter today
- [`generated_page_authoring.md`](generated_page_authoring.md)
  - generated page, recipe, and snippet authoring rules
- [`title_style_guide.md`](title_style_guide.md)
  - title and heading source rules
- [`dev/layout_params_guide.md`](dev/layout_params_guide.md)
  - current layout parameter semantics
- [`dev/manual_template_intake_checklist.md`](dev/manual_template_intake_checklist.md)
  - intake checklist for new template families
- [`dev/git_branching_guide.md`](dev/git_branching_guide.md)
  - branch hygiene and GitHub protection rules
- [`dev/orchestration_module_map.md`](dev/orchestration_module_map.md)
  - ownership map for orchestration-first entrypoints
- [`dev/code_review_checklist.md`](dev/code_review_checklist.md)
  - code/config/data/doc review checklist
- [`dev/vercel_review_preview_guide.md`](dev/vercel_review_preview_guide.md)
  - latest-publish / review-preview hosting rules
- [`tests/README.md`](tests/README.md)
  - current test and validation baseline

## 3. Current OpenClaw Docs

Use these together; do not split operator guidance across older phase plans.

- [`../BOOTSTRAP.md`](../BOOTSTRAP.md)
  - short operator bootstrap for repo-local natural-language control
- [`../integrations/openclaw/README.md`](../integrations/openclaw/README.md)
  - current package map and ownership boundary
- [`architecture/OpenClaw_Control_Layer_Plan.md`](architecture/OpenClaw_Control_Layer_Plan.md)
  - active architecture and responsibility split for the control layer

## 4. Roadmap And Execution

- [`../optimization_project.md`](../optimization_project.md)
  - current repo roadmap and active workstreams
- [`next_optimization_checklist.md`](next_optimization_checklist.md)
  - active optimization checklist

## 5. Historical Or Archived Docs

These files are kept for traceability, not as the current source of truth.

- [`maintainability_refactor_tracker.md`](maintainability_refactor_tracker.md)
  - completed maintainability decomposition campaign
- [`openclaw_phase1_implementation_checklist.md`](openclaw_phase1_implementation_checklist.md)
  - archived rollout checklist for an earlier OpenClaw phase
- [`phase2_lark_setup_and_parity_plan.md`](phase2_lark_setup_and_parity_plan.md)
  - archived machine bring-up and parity record
- [`dev/system_contract(draft_not_in_used).md`](dev/system_contract(draft_not_in_used).md)
  - abandoned draft kept only as a marked archive
- [`code_optimization_log.md`](code_optimization_log.md)
  - historical maintenance milestones
- [`dev/dev_log.md`](dev/dev_log.md)
  - development log
- [`tests/test_report-260301.md`](tests/test_report-260301.md)
  - historical test report snapshot

For archived architecture plans, use [`architecture/README.md`](architecture/README.md).

## 6. Maintenance Rule

When the repo changes:

- update the single document that owns the changed behavior
- prefer the current docs in sections 1 to 4 over historical trackers and older plans
- keep archived docs clearly marked so they do not compete with active guidance
