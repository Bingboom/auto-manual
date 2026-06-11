# Templates Directory

`docs/templates/` is the reusable manual template layer. It is shared source, not generated output.

## Map

- `page_*`: region/language page fragments.
- `recipes/`: placeholder-backed page assembly recipes.
- `contracts/`: contracts for placeholder-driven sections.
- `snippets/`: shared reusable text or registry data.
- `word_template/`: Word export template assets.
- `*_template.rst`: shared page templates used by multiple manuals.

## Local Rules

- Preserve placeholder names and page contracts unless the task explicitly changes the data model.
- Route spec, symbols, and product facts through `data/phase2/` or the appropriate CSV source rather than baking values into templates.
- Keep shared family templates shared; do not fork a per-model template just because one model changed.
- If external Markdown is being mapped into templates, use `.agents/skills/markdown-rst-template-intake/SKILL.md`.

## Validation

- Template identity/literal checks: `python3 -m unittest tests.test_template_identity_literals tests.test_preface_templates`
- Placeholder and variable behavior: `python3 -m unittest tests.test_variable_resolver tests.test_page_contracts`
- CSV page rendering: `python3 -m unittest tests.test_csv_page_builder tests.test_csv_page_renderers`
- Build check after template behavior changes: `python3 build.py check --config configs/config.us.yaml --model JE-1000F --region US`
