# Spec Master User Guide

Updated: 2026-03-17

This file explains the current phase1 data layer, with [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) as the center.
It is the operational guide for the CSV files used by the current repo.
For the future canonical data model and CMS-direction schema boundary, see [`architecture/Content_Data_Model.md`](architecture/Content_Data_Model.md).

## 1. Active Phase1 CSV Files

The current manual data layer uses these files:

- [`data/phase1/Spec_Master.csv`](../data/phase1/Spec_Master.csv)
  - main product parameters
  - spec rows
  - `product_name`
  - `model_no`
  - `tpl_*` placeholders
- [`data/phase1/Spec_Footnotes.csv`](../data/phase1/Spec_Footnotes.csv)
  - spec footnotes
- [`data/phase1/spec_titles.csv`](../data/phase1/spec_titles.csv)
  - localized spec section title mapping
- [`data/phase1/content_blocks.csv`](../data/phase1/content_blocks.csv)
  - block-based safety and content sections
- [`data/phase1/page_registry.csv`](../data/phase1/page_registry.csv)
  - page/block registry used by phase1 safety flow

[`Spec_Master.csv`](../data/phase1/Spec_Master.csv) remains the main structured source for product identity and placeholder substitution.

## 2. Where [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) Is Used

Current flow:

1. [`build.py`](../build.py) or [`tools/build_docs.py`](../tools/build_docs.py) resolves target `model` and `region`
2. product identity is resolved from [`Spec_Master.csv`](../data/phase1/Spec_Master.csv)
3. [`tools/phase1_build.py`](../tools/phase1_build.py) renders CSV-driven content
4. [`tools/gen_index_bundle.py`](../tools/gen_index_bundle.py) materializes runtime pages
5. `_review` can then be seeded or synced from that runtime output
6. `word`, `html`, `pdf`, `publish`, and `release-manifest` consume the prepared bundle or its outputs

That means one data change can affect:

- generated spec content
- placeholder pages
- Word title
- review sync results
- diff-report field tracing
- release manifest metadata

## 3. Required Data for Current Builds

At minimum, [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) needs enough data to resolve the target identity and render spec content.

Important columns commonly used by the current system:

- `Section`
- `Row_key`
- `Line_order`
- `Model`
- `Region`
- language-specific value columns such as `Value_en` / `Value_ja`

Important row keys:

- `product_name`
- `model_no`
- `tpl_*`

If `product_name` cannot be resolved for `model + region + lang`, `build.py check` and [`tools/build_docs.py`](../tools/build_docs.py) will fail fast for target identity.

## 4. Current Placeholder Rules

### 4.1 Core Identity Placeholders

Resolved from [`Spec_Master.csv`](../data/phase1/Spec_Master.csv):

- `|PRODUCT_NAME|`
- `|PRODUCT_NAME_BOLD|`
- `|PRODUCT_SHORT_NAME|`
- `|PRODUCT_SHORT_NAME_BOLD|`
- `|MODEL_NO|`

### 4.2 Template Placeholders

Any row with `Row_key` starting with `tpl_` becomes a placeholder.

Examples:

- `tpl_main_power_button_label` -> `|MAIN_POWER_BUTTON_LABEL|`
- `tpl_battery_pack_name` -> `|BATTERY_PACK_NAME|`
- `tpl_side_ac_input_spec` -> `|SIDE_AC_INPUT_SPEC|`

Derived variants may also exist, for example:

- `_BOLD`
- `_LOWER`
- suffixed placeholders for multi-line values

### 4.3 Current Usage Rule

If the same text should be shared across many models, keep it in template or config.
If the text is target-specific and data-driven, keep it in [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) as `tpl_*`.

### 4.4 Contract V2 Rule

For placeholder-heavy or data-heavy pages, contracts can now validate:

- `required_placeholders`
- `required_spec_keys`
- `required_tpl_keys`
- `required_assets`

`required_tpl_keys` must keep the `tpl_` prefix.
Use `allowed_languages`, `allowed_regions`, and `allowed_models` when the contract is intentionally scoped.

## 5. [`spec_titles.csv`](../data/phase1/spec_titles.csv) Rule

[`spec_titles.csv`](../data/phase1/spec_titles.csv) is a localized title dictionary for spec sections.

Typical fields:

- `title_en`
- `title_zh`
- `title_jp`

Use it for section title localization.
Do not use it as the place for general product parameter storage.

## 6. [`Spec_Footnotes.csv`](../data/phase1/Spec_Footnotes.csv) Rule

Keep footnotes separate from the main spec rows.
This makes spec tables and note content easier to maintain independently.

## 7. [`content_blocks.csv`](../data/phase1/content_blocks.csv) and [`page_registry.csv`](../data/phase1/page_registry.csv)

These files support the phase1 content block system used mainly for safety or block-driven pages.

Current rule:

- use [`content_blocks.csv`](../data/phase1/content_blocks.csv) for content blocks
- use [`page_registry.csv`](../data/phase1/page_registry.csv) for block/page structure
- do not push safety prose into [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) unless it is really a parameterized row

## 8. Review-Phase Data Changes

When a target is already in review and you change:

- [`Spec_Master.csv`](../data/phase1/Spec_Master.csv)
- [`Spec_Footnotes.csv`](../data/phase1/Spec_Footnotes.csv)
- [`spec_titles.csv`](../data/phase1/spec_titles.csv)
- [`content_blocks.csv`](../data/phase1/content_blocks.csv)

do not reset the whole review bundle by default.

Use:

```powershell
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP
```

This syncs the runtime result of data-driven pages back into `_review`.

Useful variants:

```powershell
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP --sync-scope generated
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP --page-file 02_whats_in_the_box.rst
```

Use `review --refresh-review` only if you intentionally want to reseed the whole review bundle.

## 9. Common Failures

### 9.1 Product Name Resolution Failure

Symptom:

- `Failed to resolve Product Name from Spec_Master.csv`

Check:

- target `model`
- target `region`
- language coverage
- `Row_key=product_name`

### 9.2 Template Placeholder Leaks

Symptom:

- `|PLACEHOLDER|` still appears in `_build` or `_review`

Check:

- matching `tpl_*` row exists
- value is not empty
- page contract covers the page if it is placeholder-heavy

### 9.4 Stale Foreign Identity in Review or Runtime Output

Symptom:

- `STALE_IDENTITY_LITERAL` appears during `python build.py check`

Check:

- the template or review text is not carrying an old product name
- the current target `product_name` and `model_no` are correct
- if the foreign literal is intentional, add it to `checks.allowed_foreign_identity_literals`

### 9.3 Review Not Updated After Data Change

Symptom:

- runtime draft changed but `_review` still shows old parameter text

Check:

- run `python build.py sync-review ...`
- confirm the page is in the default sync scope or include it with `--page-file`

## 10. Minimal Example

For `JE-1000F / JP`, a common data-change flow is:

```powershell
python build.py check --config config.ja.yaml --model JE-1000F --region JP
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP
python build.py publish --config config.ja.yaml --model JE-1000F --region JP
python build.py release-manifest --config config.ja.yaml --model JE-1000F --region JP
```

This is the current maintainable path:

- change data
- validate
- sync review
- publish from review
- keep the release manifest with the exported outputs
