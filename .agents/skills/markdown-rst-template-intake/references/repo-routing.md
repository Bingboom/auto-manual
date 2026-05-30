# Repo Routing Reference

## Intake boundary

- Before review starts, edit `docs/templates/**` and `data/phase2/**`.
- After review starts, edit `docs/_review/<model>/<region>/**` for target-local copy changes unless the user explicitly wants to change the shared seed layer.
- Never treat `docs/_build/**` as the authoring source.
- Do not hand-edit `docs/index.rst` unless the task is about index generation.
- Single-language families may still carry multilingual prefaces when that is how the family already publishes.

## Standard section map

- Cover or introduction:
  route to `00_preface.rst` for most families and `cover_jp.rst` for JP.
- Safety:
  route to `safety_*.rst`.
- Symbols:
  route to `data/phase2/symbols_blocks.csv` for CSV-backed families.
  JP keeps detailed symbols content in `docs/templates/page_jp/01_meaning_of_symbols.rst`.
- In the box:
  route to `02_whats_in_the_box.rst`.
- Product overview:
  route to `03_product_overview_placeholder.rst`.
- LCD:
  route to `data/phase2/lcd_icons_blocks.csv` or the active phase2 snapshot. Current manifests generate it through `csv_page` page `lcd_icons`.
- Operation guide:
  route to `05_operation_guide_placeholder.rst`.
- UPS:
  route to `06_ups_mode.rst`.
- Charging:
  route to `charging.rst`.
- Charging methods:
  route to `08_charging_methods.rst`.
- Storage and maintenance:
  route to `09_storage_and_maintenance.rst` where that family has the page.
- Troubleshooting:
  route US/EU en/fr/es to `templates/page_shared/<lang>/10_troubleshooting.rst`; route other families to their local `10_troubleshooting.rst`.
- Specs:
  route to `data/phase2/Spec_Master.csv`, `Spec_Footnotes.csv`, and `Spec_Notes.csv`.
- Warranty:
  route to `11_warranty.rst`.
- App setup:
  route to `12_app_setup_placeholder.rst`.
- If `spec` or `symbols` are already `csv_page` in the manifest, keep them data-driven even when the source Markdown uses prose blocks or tables.

## Placeholder policy

- `03_product_overview`, `05_operation_guide`, and `12_app_setup` are the current recipe-backed placeholder pages.
- LCD display is data-driven through `lcd_icons`; do not reintroduce `04_lcd_display_placeholder.rst` as an authoring source.
- Check `docs/templates/contracts/03_product_overview.yaml`, `05_operation_guide.yaml`, and `12_app_setup.yaml` before removing or renaming required placeholders.
- Add a placeholder only when the content should resolve from structured page-value data instead of static prose.
- If a target family needs literal body copy but still inherits a contract for a placeholder page, keep the contract-required placeholders in a non-rendering RST comment instead of forcing the rendered copy to stay generic.

## Family notes

- `us-merged`:
  treat `docs/templates/page_us-en/` as the structure owner and keep `page_us-fr/` plus `page_us-es/` aligned.
- `us-fr` and `us-es`:
  the shared placeholder mapping for `03_product_overview` and `12_app_setup` currently lives under `docs/templates/recipes/us-en/`.
- `jp`:
  use `docs/manifests/manual_jp.yaml` and keep `01_meaning_of_symbols.rst` as the detailed symbols page.
- `zh`:
  use `docs/manifests/manual_zh.yaml` and `configs/config.zh.yaml` with region `CN`.
- `eu-en`:
  the family lives under `configs/config.eu-en.yaml` and `docs/manifests/manual_eu-en.yaml`.
  The current page-value path resolves through `JE-2000E` with region `US`; keep `spec` and `symbols` in `data/phase2/**`.

## Validation

- Start from `code-as-doc/dev/manual_template_intake_checklist.md`.
- Use `python build.py check --config <config> --model <MODEL> --region <REGION>` for shared template or data changes.
- Use `python build.py preview --config <config> --model <MODEL> --region <REGION> --page <page-stem>` for page spot checks.
- If the task changes logic, also run `python -m unittest`.
- If the default `python` lacks repo deps, use `.\.venv\Scripts\python.exe` for the same commands.
