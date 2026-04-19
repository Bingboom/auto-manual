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

## Review sync behavior

- A `generated_page` produces both generated draft fragments under `generated/{model}/...` and one materialized wrapper page under `page/*.rst`.
- `python build.py sync-review --sync-scope params` refreshes the review copy of that wrapper page through placeholder-line merging, so parameter-driven values stay current without overwriting the rest of the reviewed prose.
- `python build.py sync-review --sync-scope generated` only refreshes generated draft/spec files. It does not replace the `generated_page` wrapper under `page/*.rst`.
- If you intentionally need the whole wrapper page replaced from runtime, use `python build.py sync-review --page-file <file>` or reseed with `python build.py review --refresh-review`.

## Draft recipe rules

- Keep `page_id` aligned with the `generated_page.page` value in the manifest.
- Put extra non-`field_map` Spec_Master dependencies in `required_row_keys`.
- Use structured `field_map` selectors for page values, for example `row_key + pages + usage_type + placement_key + value_role + variant_key`.
- `field_map` bindings with no `default` are validated directly during render and `check`.
- Put reusable copy or button combinations into snippet files instead of duplicating them in multiple templates.

## Snippet rules

- Register every snippet in `docs/templates/snippets/registry.yaml`.
- Prefer one logical `snippet_id` with per-language entries instead of creating unrelated ids.
- Keep snippet files small and purpose-specific so they can be reused across pages or regions.
