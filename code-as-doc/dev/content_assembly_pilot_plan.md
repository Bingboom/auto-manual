# Content Assembly Pilot Plan

This note is the pre-template-splitting safety plan for the long-term
content assembly pilot. It is intentionally narrower than the architecture
strategy: the goal is to prove one page can be described by explicit data and
validated before any existing HTML/PDF build path is replaced.

## Pilot Scope

- Pilot page: `03_product_overview`
- Product family: `JE-1000F`
- Initial targets: `US/en` and `JP/ja`
- Behavior change: none for the preparation phase
- Build integration: deferred until the template split phase

The first four preparation PRs add documentation, fixture-backed table
contracts, a validator, and a no-op assembler. They do not change `build.py`,
`tools/product_overview_renderer.py`, or the current RST template rendering
path.

## Current Product Overview Dependencies

Template sources:

- `docs/templates/page_us-en/03_product_overview_placeholder.rst`
- `docs/templates/page_us-es/03_product_overview_placeholder.rst`
- `docs/templates/page_us-fr/03_product_overview_placeholder.rst`
- `docs/templates/page_eu-en/03_product_overview_placeholder.rst`
- `docs/templates/page_eu-fr/03_product_overview_placeholder.rst`
- `docs/templates/page_eu-es/03_product_overview_placeholder.rst`
- `docs/templates/page_eu-de/03_product_overview_placeholder.rst`
- `docs/templates/page_eu-it/03_product_overview_placeholder.rst`
- `docs/templates/page_eu-uk/03_product_overview_placeholder.rst`
- `docs/templates/page_jp/03_product_overview_placeholder.rst`
- `docs/templates/page_zh/03_product_overview_placeholder.rst`

Recipes:

- `docs/templates/recipes/us-en/03_product_overview.yaml`
- `docs/templates/recipes/eu-en/03_product_overview.yaml`
- `docs/templates/recipes/jp/03_product_overview.yaml`
- `docs/templates/recipes/zh/03_product_overview.yaml`

Existing page contract:

- `docs/templates/contracts/03_product_overview.yaml`

Renderer and build touchpoints:

- `tools/product_overview_renderer.py`
- `tools/draft_engine.py`
- `tools/gen_index_bundle_page_render.py`

Assets:

- `docs/templates/word_template/common_assets/overview/front_product.jpg`
- `docs/templates/word_template/common_assets/overview/right_side_ports.png`
- `docs/templates/word_template/common_assets/overview/front_controls.png`

Data surfaces:

- `data/phase1/Spec_Master.csv`
- `data/phase2/Spec_Master.csv`
- recipe `field_map` selectors using `row_key`, `pages`, `usage_type`,
  `placement_key`, `value_role`, and `variant_key`

Current required identity rows:

- `product_name`
- `model_no`

Current product overview placeholder-backed rows include:

- `main_power_button`
- `dc12_port`
- `dc_usb_power_button`
- `usb_c`
- `ac_power_button`
- `usb_a`
- `ac_output`
- `total_output`
- `ac_input`
- `dc_input`

## Functional Block Taxonomy

The pilot defines the first block vocabulary before templates are split. A
block type is valid only when it is listed here and in the assembly contract
validator.

| Block type | Purpose | Repeatable | Region/lang filter | Missing field policy |
| --- | --- | --- | --- | --- |
| `product_identity` | Product name, model number, and page identity values. | No | Yes | `error` |
| `feature_overview` | Visual overview panels and major feature groups. | Yes | Yes | `fallback` |
| `spec_summary` | Compact spec rows or totals that summarize a feature group. | Yes | Yes | `skip` or `fallback` |
| `asset_callout` | Image-backed callouts with alt text and stable asset keys. | Yes | Yes | `error` |
| `warning_notice` | Safety or compliance warning blocks. | Yes | Yes | `error` |
| `operation_steps` | Ordered operation steps. | Yes | Yes | `error` |
| `app_instruction` | App pairing or software workflow instructions. | Yes | Yes | `fallback` |
| `maintenance_block` | Cleaning, storage, or maintenance guidance. | Yes | Yes | `fallback` |
| `troubleshooting_case` | Symptom/cause/action troubleshooting cases. | Yes | Yes | `skip` |

The first no-op assembler exercises only the product overview subset:

- `product_identity`
- `feature_overview`
- `spec_summary`
- `asset_callout`

The broader taxonomy is documented now so later page pilots do not invent
competing block names.

## Fixture Table Model

The preparation phase uses fixture tables under
`tests/fixtures/content_assembly/` instead of live Feishu/Lark Base reads.

Required fixture tables:

- `page_assembly.csv`: page, product family, target, block order, block type,
  enabled flag, and fallback language.
- `content_blocks.csv`: reusable block metadata, parent relation, title key,
  asset key, repeatability, and applicability.
- `block_fields.csv`: field selectors that connect a block field to existing
  Spec_Master or recipe concepts.
- `asset_registry.csv`: stable asset keys, repo-relative paths, alt keys, and
  applicability.
- `block_rules.csv`: simple include/skip/fallback rules that can later map to
  multidimensional table conditions.

This is not the final CMS schema. It is the smallest stable contract needed to
detect drift before splitting the first template.

## Assembly Contract

The pilot contract lives in:

- `docs/templates/assembly_contracts/03_product_overview.yaml`

It declares:

- page id
- product family
- supported regions and languages
- fallback language
- allowed block types for the page
- page-level required fields

Validation rules:

- `page_id` must have fixture rows.
- Every block type must be known.
- Every required field must be available from fixture `block_fields` or current
  recipe selectors.
- Asset keys used by blocks must exist in `asset_registry`.
- Asset paths must exist in the repo.
- Multi-language contracts must declare a fallback language.
- Unknown block types, missing fields, missing assets, and missing fallback
  declarations fail before any template is split.

## Rollout Boundary

The preparation phase is safe for current HTML/PDF generation because it is
read-only relative to the current build path:

- no changes to `build.py`
- no changes to existing recipes
- no changes to existing page contracts
- no changes to `tools/product_overview_renderer.py`
- generated assembly output goes only to a requested temporary path

The next phase can start splitting `03_product_overview` only after the
validator and no-op assembler pass for both `US/en` and `JP/ja`.
