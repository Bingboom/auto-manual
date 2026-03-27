# Code Review Checklist

Updated: 2026-03-15

Use this checklist when reviewing changes to code, config, data, or review workflow.

## 1. Source of Truth

- [ ] Is it clear whether this change belongs in templates, phase1 CSV data, `_review`, or runtime `_build` output?
- [ ] If review has already started for a target, are target-specific text changes being made in [`docs/_review/<model>/<region>/`](../../docs/_review) instead of shared templates?
- [ ] If the change affects many manuals, is it being implemented in templates or shared data rather than copied into one review bundle?

## 2. Build and Release Flow

- [ ] Does the change preserve the current [`build.py`](../../build.py) entrypoint?
- [ ] If command behavior changed, were [`README.md`](../../README.md), [`code-as-doc/build_doc_guide.md`](../build_doc_guide.md), and the user guides under [`user-guide/`](../../user-guide) updated?
- [ ] If publish behavior changed, was `python build.py publish ...` kept or updated intentionally?
- [ ] If diff-report behavior changed, were the report docs updated too?
- [ ] If `preview`, `fast`, or `release-manifest` behavior changed, were their examples and output paths updated in docs?

## 3. Config Discipline

- [ ] Did we avoid creating a new config file only because the model changed?
- [ ] If a new config was added, is there a real template-family or page-stack reason for it?
- [ ] Does the config still use `manual_{model_slug}_{region_slug}` style output naming where expected?

## 4. Data Contract

- [ ] If [`Spec_Master.csv`](../../data/phase1/Spec_Master.csv) semantics changed, was [`code-as-doc/spec_master_user_guide.md`](../spec_master_user_guide.md) updated?
- [ ] If new page-value bindings were introduced, are the affected templates, recipes, and contracts aligned?
- [ ] If contracts changed, are `required_spec_keys`, `required_page_values`, `required_assets`, and `allowed_*` scopes still correct?
- [ ] If safety/spec data behavior changed, are [`Spec_Footnotes.csv`](../../data/phase1/Spec_Footnotes.csv), [`spec_titles.csv`](../../data/phase1/spec_titles.csv), and [`content_blocks.csv`](../../data/phase1/content_blocks.csv) interactions still correct?

## 5. Review Workflow

- [ ] If the target is already in review, is `sync-review` used for data-driven refresh instead of resetting the whole review bundle?
- [ ] If `review --refresh-review` is used, is that intentional and documented?
- [ ] Does `_review` still remain the durable editing surface after review starts?

## 6. Contracts and Validation

- [ ] If a placeholder-heavy page was added or changed, is there an appropriate page contract under [`docs/templates/contracts/`](../../docs/templates/contracts)?
- [ ] Does `check` still fail fast for missing identity, stale foreign identity, unresolved placeholders, missing assets, or missing contract data?
- [ ] If a foreign model literal is intentionally allowed, is `checks.allowed_foreign_identity_literals` being used instead of weakening the scan?
- [ ] Are error messages still specific enough to locate the problem?

## 7. Tests and Verification

- [ ] Was `python -m unittest` run if logic changed?
- [ ] Was at least one relevant smoke build run for the affected family?
- [ ] If JP review/publish flow changed, was `python build.py publish --config config.ja.yaml --model JE-1000F --region JP` verified or explicitly deferred?
- [ ] If release traceability changed, was `python build.py release-manifest --config config.ja.yaml --model JE-1000F --region JP` verified or explicitly deferred?

## 8. Documentation and History

- [ ] Were the current normative docs updated in the same change?
- [ ] If this is a major milestone, was [`code-as-doc/code_optimization_log.md`](../code_optimization_log.md) updated?
- [ ] If a document became historical or draft-only, is it clearly marked as such?
