# Data Directory

`data/` contains source CSVs and local source-table mirrors that feed manual generation.

## Map

- `layout_params.csv`: layout and rendering parameters.
- `product_info.csv`: product metadata source.
- `check.csv`: source check data.
- `config/`: language density and related config data.
- `phase2/`: local Feishu/Lark source-table mirror; gitignored in this checkout.

## Local Rules

- `data/phase2/**` schema changes require explicit operator confirmation.
- Treat `data/phase2/` as source-of-truth mirror data, not disposable build output.
- Keep data edits aligned with templates and recipes when placeholders depend on them.
- Do not invent model defaults in data migration or lookup behavior.

## Validation

- Data/schema tests: `python3 -m unittest tests.test_schema_drift tests.test_validate_spec_master tests.test_validate_layout_params`
- Sync behavior: `python3 -m unittest tests.test_sync_data tests.test_validate_config`
- Build check after data-driven changes: `python3 build.py check --config configs/config.us.yaml --model JE-1000F --region US`
