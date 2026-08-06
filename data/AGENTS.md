# Data Directory

`data/` contains source CSVs and local source-table mirrors that feed manual generation.

## Map

- `layout_params.csv`: layout and rendering parameters.
- `product_info.csv`: product metadata source.
- `check.csv`: source check data.
- `model_capabilities.csv`: per-target feature booleans; derived, refreshed by `sync-data`.
- `model_languages.csv`: per-target language scope (which of the family's languages a model ships); hand-maintained.
- `config/`: language density and related config data.
- `phase2/`: local Feishu/Lark source-table mirror; gitignored in this checkout.

## Local Rules

- `data/phase2/**` schema changes require explicit operator confirmation.
- Treat `data/phase2/` as source-of-truth mirror data, not disposable build output.
- Keep data edits aligned with templates and recipes when placeholders depend on them.
- Do not invent model defaults in data migration or lookup behavior.
- Never narrow a family config's `build.languages` to fix one model — that strips the language from every model in the region. Add or edit the `model_languages.csv` row instead.
- `model_languages.csv` is hand-maintained; `model_capabilities.csv` is a `sync-data` mirror and hand edits there are overwritten.

## Validation

- Data/schema tests: `python3 -m unittest tests.test_schema_drift tests.test_validate_spec_master tests.test_validate_layout_params`
- Sync behavior: `python3 -m unittest tests.test_sync_data tests.test_validate_config`
- Build check after data-driven changes: `python3 build.py check --config configs/config.us.yaml --model JE-1000F --region US`
