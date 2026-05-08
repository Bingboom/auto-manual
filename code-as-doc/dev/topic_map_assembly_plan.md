# Topic Map Assembly Plan

This plan is the next step after the `03_product_overview` assembly pilot.
The goal is to move from page-local block assembly toward a reusable topic map
model that can be configured from Feishu/Lark Base while keeping the current
build path stable.

## 1. Direction

Use a topic map hierarchy:

```text
Manual Map
  -> Page Map
      -> Topic Map
          -> Topic Template
          -> Topic Fields
          -> Topic Assets
          -> Topic Rules
```

Do not split content into sentence-level records. A topic should be the
smallest reusable content unit with independent meaning, validation, and
region/language applicability.

Good topic examples:

- `product_identity`
- `product_overview.front_asset`
- `product_overview.front_features`
- `product_overview.side_asset`
- `product_overview.side_features`
- `product_overview.total_output`
- `charging.ac_wall`
- `charging.solar_direct`
- `operation.energy_saving`
- `maintenance.storage`
- `troubleshooting.case`

Bad topic examples:

- one button label
- one table cell
- one image caption
- one sentence that cannot be reused independently

## 2. Implementation Phases

### PR 1: Topic Map Contract Documentation

- Add this plan and a Feishu Base table contract.
- Keep the existing `content_assembly` code unchanged.
- Define the migration mapping from current block tables to topic tables.

### PR 2: Fixture Topic Tables

- Add local fixture CSVs under `tests/fixtures/topic_map/`.
- Create tables that mirror the Feishu Base schema below.
- Add schema drift tests for required headers, required links, and enum values.

### PR 3: Topic Map Validator

- Add `tools/topic_map_contract.py`.
- Validate:
  - unknown topic type
  - missing topic template
  - missing required field
  - missing asset
  - missing fallback language
  - invalid manual/page/topic ordering
  - invalid rule action

### PR 4: Topic Map Adapter

- Add an adapter that converts topic map fixture rows into the current
  `content_assembly` shape.
- This keeps PR5's `03_product_overview` assembly path working while the
  external contract moves from block naming to topic naming.

### PR 5: Product Overview Topic Map Pilot

- Move only `03_product_overview` from `page_assembly/content_blocks` fixtures
  to topic map fixtures.
- Keep old fixture support as a compatibility fallback.
- Keep US/en and JP/ja as the only enabled pilot targets.

## 3. Feishu Base Table Design

Create one Base for content assembly, for example:

```text
Auto Manual Content Assembly
```

Use these tables first. The table names below are the recommended canonical
names. Keep English table and field names to make API/export code simpler.

### Table 1: `topic_registry`

Purpose: one row per reusable topic.

Primary field:

- `topic_id`
  - Type: Text
  - Example: `product_overview.front_features`
  - Rule: unique and stable

Fields:

| Field | Type | Required | Example |
| --- | --- | --- | --- |
| `topic_type` | Single select | Yes | `feature_overview` |
| `topic_title` | Text | No | `Front view features` |
| `template_path` | Text | Yes | `templates/assembly_blocks/03_product_overview/feature_overview.rst` |
| `repeatable` | Checkbox | Yes | false |
| `owner` | Person | No | maintainer |
| `status` | Single select | Yes | `active` |
| `description` | Text | No | `Front panel labels and specs` |

Recommended `topic_type` options:

- `product_identity`
- `feature_overview`
- `spec_summary`
- `asset_callout`
- `warning_notice`
- `operation_steps`
- `app_instruction`
- `maintenance_block`
- `troubleshooting_case`

Recommended `status` options:

- `draft`
- `active`
- `deprecated`

### Table 2: `topic_fields`

Purpose: declare data dependencies for each topic.

Primary field:

- `field_binding_id`
  - Type: Formula or Text
  - Suggested formula: `{topic_id} & "." & {field_key}`

Fields:

| Field | Type | Required | Example |
| --- | --- | --- | --- |
| `topic` | Link to `topic_registry` | Yes | `product_overview.front_features` |
| `field_key` | Text | Yes | `FRONT_USB_A_LABEL` |
| `source_table` | Single select | Yes | `Spec_Master` |
| `row_key` | Text | Yes | `usb_a` |
| `page_scope` | Text | No | `Product overview` |
| `usage_type` | Single select | No | `page_value` |
| `placement_key` | Text | No | `front` |
| `value_role` | Single select | No | `label` |
| `variant_key` | Text | No | `high` |
| `data_type` | Single select | Yes | `text` |
| `required` | Checkbox | Yes | true |
| `fallback_policy` | Single select | Yes | `error` |
| `default_value` | Text | No | empty |

Recommended `source_table` options:

- `Spec_Master`
- `Topic_Content`
- `Variable_Defaults`
- `Asset_Registry`

Recommended `value_role` options:

- `label`
- `spec`
- `body`
- `title`
- `alt`

Recommended `fallback_policy` options:

- `error`
- `skip`
- `fallback`

### Table 3: `topic_assets`

Purpose: declare image/file dependencies for topics.

Primary field:

- `asset_binding_id`
  - Type: Formula or Text
  - Suggested formula: `{topic_id} & "." & {asset_key}`

Fields:

| Field | Type | Required | Example |
| --- | --- | --- | --- |
| `topic` | Link to `topic_registry` | Yes | `product_overview.front_asset` |
| `asset_key` | Text | Yes | `front_product` |
| `asset_path` | Text | Yes | `docs/templates/word_template/common_assets/overview/front_product.jpg` |
| `alt_key` | Text | No | `front_product_alt` |
| `required` | Checkbox | Yes | true |
| `region` | Multi select | No | `US`, `JP` |
| `lang` | Multi select | No | `en`, `ja` |
| `status` | Single select | Yes | `active` |

### Table 4: `topic_rules`

Purpose: conditional include/skip/fallback behavior.

Primary field:

- `rule_id`
  - Type: Text
  - Example: `rule.product_overview.total_output.us_en`

Fields:

| Field | Type | Required | Example |
| --- | --- | --- | --- |
| `topic` | Link to `topic_registry` | No | `product_overview.total_output` |
| `page_id` | Text | No | `03_product_overview` |
| `condition_key` | Single select | Yes | `region` |
| `operator` | Single select | Yes | `equals` |
| `condition_value` | Text | Yes | `US` |
| `action` | Single select | Yes | `include` |
| `priority` | Number | Yes | `10` |
| `enabled` | Checkbox | Yes | true |

Recommended `condition_key` options:

- `region`
- `lang`
- `product_family`
- `model`
- `build_family`

Recommended `operator` options:

- `equals`
- `not_equals`
- `in`
- `not_in`

Recommended `action` options:

- `include`
- `skip`
- `fallback`
- `error`

### Table 5: `page_topic_map`

Purpose: order topics into one page for a target scope.

Primary field:

- `page_topic_id`
  - Type: Formula or Text
  - Suggested formula: `{page_id} & "." & {topic_order} & "." & {topic_id}`

Fields:

| Field | Type | Required | Example |
| --- | --- | --- | --- |
| `page_id` | Text | Yes | `03_product_overview` |
| `topic` | Link to `topic_registry` | Yes | `product_overview.front_features` |
| `topic_order` | Number | Yes | `20` |
| `slot_key` | Text | No | `front_panel` |
| `product_family` | Text | Yes | `JE-1000F` |
| `region` | Multi select | No | `US`, `JP` |
| `lang` | Multi select | No | `en`, `ja` |
| `fallback_lang` | Single select | No | `en` |
| `enabled` | Checkbox | Yes | true |
| `rule_set` | Link to `topic_rules` | No | empty |

Initial `03_product_overview` rows:

| page_id | topic_order | topic_id | region | lang |
| --- | ---: | --- | --- | --- |
| `03_product_overview` | 10 | `product_identity` | `US`, `JP` | `en`, `ja` |
| `03_product_overview` | 15 | `product_overview.front_asset` | `US`, `JP` | `en`, `ja` |
| `03_product_overview` | 20 | `product_overview.front_features` | `US`, `JP` | `en`, `ja` |
| `03_product_overview` | 25 | `product_overview.side_asset` | `US`, `JP` | `en`, `ja` |
| `03_product_overview` | 30 | `product_overview.side_features` | `US`, `JP` | `en`, `ja` |
| `03_product_overview` | 40 | `product_overview.total_output` | `US` | `en` |

### Table 6: `manual_page_map`

Purpose: order pages into one manual target.

Primary field:

- `manual_page_id`
  - Type: Formula or Text
  - Suggested formula: `{manual_id} & "." & {page_order} & "." & {page_id}`

Fields:

| Field | Type | Required | Example |
| --- | --- | --- | --- |
| `manual_id` | Text | Yes | `je1000f_us_en` |
| `product_family` | Text | Yes | `JE-1000F` |
| `model` | Text | Yes | `JE-1000F` |
| `region` | Single select | Yes | `US` |
| `lang` | Single select | Yes | `en` |
| `page_id` | Text | Yes | `03_product_overview` |
| `page_order` | Number | Yes | `30` |
| `page_source_type` | Single select | Yes | `topic_map` |
| `enabled` | Checkbox | Yes | true |

Recommended `page_source_type` options:

- `topic_map`
- `generated_page`
- `csv_page`
- `rst_include`
- `cover_pdf`
- `pdf_insert`

### Table 7: `topic_content`

Purpose: optional fixed copy controlled by Base rather than `Spec_Master`.
Use this only for reusable body text. Keep technical specs in `Spec_Master`.

Primary field:

- `content_id`
  - Type: Formula or Text
  - Suggested formula: `{topic_id} & "." & {content_key} & "." & {lang}`

Fields:

| Field | Type | Required | Example |
| --- | --- | --- | --- |
| `topic` | Link to `topic_registry` | Yes | `charging.ac_wall` |
| `content_key` | Text | Yes | `intro_body` |
| `region` | Multi select | No | `US`, `JP` |
| `lang` | Single select | Yes | `en` |
| `content_rst` | Long text | Yes | `Connect the AC cable...` |
| `fallback_lang` | Single select | No | `en` |
| `status` | Single select | Yes | `active` |

## 4. Recommended Views

Create these views in Feishu Base:

- `Active Topics`
  - Table: `topic_registry`
  - Filter: `status = active`
- `Product Overview Topic Map`
  - Table: `page_topic_map`
  - Filter: `page_id = 03_product_overview` and `enabled = true`
  - Sort: `topic_order` ascending
- `US EN Manual`
  - Table: `manual_page_map`
  - Filter: `region = US`, `lang = en`, `enabled = true`
  - Sort: `page_order` ascending
- `JP JA Manual`
  - Table: `manual_page_map`
  - Filter: `region = JP`, `lang = ja`, `enabled = true`
  - Sort: `page_order` ascending
- `Drift Review`
  - Tables: all topic tables
  - Filter: missing required fields, empty template paths, disabled required
    topics, or inactive linked topics

## 5. Mapping From Current Block Pilot

Keep code compatibility first. Do not rename everything in one PR.

| Current fixture | Topic-map table |
| --- | --- |
| `content_blocks.csv` | `topic_registry` |
| `block_fields.csv` | `topic_fields` |
| `asset_registry.csv` | `topic_assets` |
| `block_rules.csv` | `topic_rules` |
| `page_assembly.csv` | `page_topic_map` |
| page manifest YAML | `manual_page_map` later |

The first implementation should add a topic-map adapter that reads the new
tables and produces the current `content_assembly` structures. After the pilot
is stable, the lower-level names can be migrated from block to topic.

## 6. Base Setup Checklist

When creating the Base manually:

1. Create the seven tables above.
2. Use the exact English field names from this document.
3. Make `topic_id`, `page_topic_id`, and `manual_page_id` stable identifiers.
4. Use linked records from `topic_fields`, `topic_assets`, `topic_rules`, and
   `page_topic_map` back to `topic_registry`.
5. Keep enum values lowercase with underscores where possible.
6. Add the recommended views before connecting automation.
7. Export fixture CSVs from the Base and compare headers against local tests
   before any live build reads the Base.

## 7. Guardrails

- Do not make a full manual depend on Base until fixture tests pass.
- Do not replace page manifests with `manual_page_map` in the first topic-map
  PR.
- Do not store generated RST/PDF/HTML outputs in Base.
- Do not split topics smaller than reusable semantic units.
- Keep `Spec_Master` as the source of product specs until a later content
  governance decision changes that boundary.
