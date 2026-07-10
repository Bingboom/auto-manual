# Configs Directory

`configs/` owns manual family configuration and inheritance. Keep the shared family config pattern.

## Map

- `config.us.yaml`: US family config.
- `config.ja.yaml`: JP family config.
- `config-bases/`: shared inheritance bases.
- Other `config.*.yaml` files are target/family variants, not one-off per-model copies by default.

## Local Rules

- Do not create one config per model just because the model changed.
- Keep config-driven `docs_dir`, `layout_params_csv`, and staging resolution in `tools/build_paths.py`.
- Avoid hardcoded defaults such as `JE-1000F` in CLI behavior, reports, and release paths.
- When moving or renaming config files, update docs and tests in the same change.

## Validation

- Config tests: `python3 -m unittest tests.test_config_loader tests.test_config_pages tests.test_pilot_configs tests.test_validate_config`
- US check: `python3 build.py check --config configs/config.us.yaml --model JE-1000F --region US`
- JP check: `python3 build.py check --config configs/config.ja.yaml --model JE-1000F --region JP`
