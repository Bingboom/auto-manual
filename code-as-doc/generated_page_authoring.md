# Generated Page Authoring

This repo now supports two authoring paths for manual pages:

1. `rst_include`
   Use this for stable static content that does not need Spec_Master field mapping or snippet injection.

2. `generated_page`
   Use this when the page depends on Spec_Master values, shared snippets, or explicit draft-engine checks.

## Required baseline

- Always install Python dependencies from `requirements.txt` before running local checks or tests.
- CI already assumes this baseline and runs `python -m pip install -r requirements.txt`.

## New page flow

1. Add or update the region manifest in `docs/manifests/`.
2. Decide whether the page is `rst_include` or `generated_page`.
3. For `generated_page`, create:
   - a recipe in `docs/templates/recipes/`
   - any shared snippets in `docs/templates/snippets/`
   - a template that may use `{{snippet:slot_name}}`
4. Run:
   - `python build.py rst --config <config> --model <model> --region <region>`
   - `python build.py check --config <config> --model <model> --region <region>`
   - `python build.py review --config <config> --model <model> --region <region>`

## Draft recipe rules

- Keep `page_id` aligned with the `generated_page.page` value in the manifest.
- Put required Spec_Master dependencies in `required_row_keys`.
- Use `field_map` when the placeholder name and the source row key are not the same concern.
- Put reusable copy or button combinations into snippet files instead of duplicating them in multiple templates.

## Snippet rules

- Register every snippet in `docs/templates/snippets/registry.yaml`.
- Prefer one logical `snippet_id` with per-language entries instead of creating unrelated ids.
- Keep snippet files small and purpose-specific so they can be reused across pages or regions.
