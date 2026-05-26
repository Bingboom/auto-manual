# Auto-Manual Agent Guide

Use this file for repo operating rules only.
It is not the architecture strategy and it is not the optimization roadmap.

Document boundary:

- `AGENTS.md`: how an agent should operate in this repo today
- `System Evolution Strategy.md`: long-term system direction and stable architecture boundaries
- `optimization_project.md`: repo-level execution roadmap and next optimization priorities

For long-term direction, read:

- [`code-as-doc/architecture/System Evolution Strategy.md`](/Users/pika/Documents/GitHub/auto-manual/code-as-doc/architecture/System%20Evolution%20Strategy.md)

For repo optimization priorities, read:

- [`optimization_project.md`](/Users/pika/Documents/GitHub/auto-manual/optimization_project.md)

For current human workflows, read:

- [`code-as-doc/build_doc_guide.md`](/Users/pika/Documents/GitHub/auto-manual/code-as-doc/build_doc_guide.md)
- [`user-guide/hello_auto-doc.md`](/Users/pika/Documents/GitHub/auto-manual/user-guide/hello_auto-doc.md)

## 1. Entrypoint

- Default to [`build.py`](/Users/pika/Documents/GitHub/auto-manual/build.py).
- Treat [`tools/`](/Users/pika/Documents/GitHub/auto-manual/tools) as low-level implementation unless the task is explicitly about those scripts.

## 2. Editing Surface

- Shared changes: [`docs/templates/`](/Users/pika/Documents/GitHub/auto-manual/docs/templates), [`data/phase2/`](/Users/pika/Documents/GitHub/auto-manual/data/phase2)
- Target review changes after review starts: [`docs/_review/`](/Users/pika/Documents/GitHub/auto-manual/docs/_review)
- Generated output only: [`docs/_build/`](/Users/pika/Documents/GitHub/auto-manual/docs/_build)
- Do not hand-edit [`docs/index.rst`](/Users/pika/Documents/GitHub/auto-manual/docs/index.rst) unless the task is about index generation.

## 3. Workflow Rules

- Do not create one config per model just because the model changed.
- Keep the shared family config pattern with [`config.us.yaml`](/Users/pika/Documents/GitHub/auto-manual/config.us.yaml) and [`config.ja.yaml`](/Users/pika/Documents/GitHub/auto-manual/config.ja.yaml).
- If a target is already in review, prefer `sync-review` over `review --refresh-review` for data-driven updates.
- Review overrides must stay under `overrides/_assets/`, `overrides/_static/`, or `overrides/renderers/`.
- Avoid hardcoded model defaults such as `JE-1000F` in CLI behavior, report paths, or release paths.

## 4. Validation

- Logic changes: `python3 -m unittest`
- Build or quality-gate changes: `python3 build.py check --config config.us.yaml --model JE-1000F --region US`
- JP review or publish changes: `python3 build.py publish --config config.ja.yaml --model JE-1000F --region JP`
- Diff-report changes: `python3 build.py diff-report --config config.us.yaml --model JE-1000F --region US`
- Release traceability changes: `python3 build.py release-manifest --config config.ja.yaml --model JE-1000F --region JP`

## 5. Documentation

- Update docs in the same change when behavior changes.
- Minimum set: [`README.md`](/Users/pika/Documents/GitHub/auto-manual/README.md), [`code-as-doc/build_doc_guide.md`](/Users/pika/Documents/GitHub/auto-manual/code-as-doc/build_doc_guide.md), [`user-guide/hello_auto-doc.md`](/Users/pika/Documents/GitHub/auto-manual/user-guide/hello_auto-doc.md)
- If a code change affects the current workflow, editing surface, environment setup, or release flow, update [`user-guide/hello_auto-doc.md`](/Users/pika/Documents/GitHub/auto-manual/user-guide/hello_auto-doc.md) in the same change.
- If a code change affects the happy-path example, onboarding steps, or target-specific sample commands, update [`user-guide/quick_start_guide.md`](/Users/pika/Documents/GitHub/auto-manual/user-guide/quick_start_guide.md) in the same change.
- When a phase or workstream from [`optimization_project.md`](/Users/pika/Documents/GitHub/auto-manual/optimization_project.md) is completed, add a matching maintenance record to [`code-as-doc/code_optimization_log.md`](/Users/pika/Documents/GitHub/auto-manual/code-as-doc/code_optimization_log.md).

## 6. Working Tree Safety

- `_build`, `reports/version_tracking`, and `reports/releases` may contain user work or verification artifacts.
- Do not delete or revert generated outputs unless the task explicitly requires cleanup.

## 7. Local Skills

- Use [`.agents/skills/markdown-rst-template-intake/SKILL.md`](/Users/pika/Documents/GitHub/auto-manual/.agents/skills/markdown-rst-template-intake/SKILL.md) when mapping external Markdown manuals into this repo's reusable RST template and recipe layout.
- Use [`.agents/skills/bitable-translation-memory/SKILL.md`](/Users/pika/Documents/GitHub/auto-manual/.agents/skills/bitable-translation-memory/SKILL.md) for one-shot sentence translation, terminology lookup, and live sentence-pair retrieval.
- Use [`.agents/skills/manual-rewrite-with-tm/SKILL.md`](/Users/pika/Documents/GitHub/auto-manual/.agents/skills/manual-rewrite-with-tm/SKILL.md) for full manual or Markdown rewrite tasks that must preserve structure, reuse translation-memory phrasing, or keep unmatched source text highlighted with `==...==`.
- Use [`.agents/skills/bilingual-tm-maintenance/SKILL.md`](/Users/pika/Documents/GitHub/auto-manual/.agents/skills/bilingual-tm-maintenance/SKILL.md) when bilingual source/target copy should be written to live `Translation_Memory`, followed by target-language maintenance logs, bilingual audit, and audit logs.
- For TM-guided rewrite jobs, use the skills in this order: `bitable-translation-memory` for lookup, then `manual-rewrite-with-tm` for the structure-preserving rewrite flow.
