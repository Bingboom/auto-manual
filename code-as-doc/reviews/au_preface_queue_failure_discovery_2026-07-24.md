# AU draft-queue preface failure discovery (2026-07-24)

## Scope

Fix the JE-1000H AU draft-package queue failure reported by Hello-Docs runs
36-38, and determine whether the successful JE-1000H KR run 39 was stuck after
publishing its cloud document.

## Live evidence

- Hello-Docs run 38 failed in `build.py check --source review` for
  `JE-1000H/AU` with `LANG_PARITY_FOREIGN_LANG_BLOCK`.
- The failing review page was `page/00_preface.rst`; its family language is
  `en`, but it contains `FR` and `ES` language-tagged blocks.
- `manual_au-en.yaml` selects
  `templates/page_shared/en/00_preface.rst`. That shared component is
  intentionally trilingual for the merged US manual, and its EN/FR/ES
  contract is protected by `tests/test_preface_templates.py`.
- Hello-Docs PR 12 previously removed the same FR/ES blocks from one AU review
  derivative, but the reusable AU source composition was not corrected. A new
  JE-1000H AU review seed therefore reintroduced the defect.
- KR run 39 completed successfully in 3 minutes 30 seconds. Its queue step
  completed at 15:28:35 UTC, artifact upload completed at 15:28:41, and the
  job completed at 15:28:44. The Actions list screenshot was stale; no worker
  process remained stuck.

## Root cause

This is a component-selection error, not bad AU phase2 data and not a language
parity false positive. A single-language manifest consumes a deliberately
multilingual preface component. Review branches freeze that component, so the
mistake persists after review starts.

## Implementation plan

1. Characterize the shared US preface and the AU manifest binding.
2. Add an English-only reusable preface component without changing the
   trilingual component.
3. Point only `manual_au-en.yaml` at the English-only component.
4. Document the single-language composition rule.
5. Verify template tests, manifest/build tests, full unit tests, repository
   guardrails, and a JE-1000H AU check using a review fixture that contains the
   corrected preface.

## Non-goals

- do not weaken or allowlist `LANG_PARITY_FOREIGN_LANG_BLOCK` for AU
- do not edit phase2 source data or schemas
- do not silently rewrite an in-review derivative during a normal queue build
- do not change the US trilingual preface
- do not change KR queue execution or artifact behavior without evidence of a
  stuck process
