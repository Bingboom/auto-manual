# Spec Topic Pilot Plan

This pilot narrows the content-assembly work to the most painful maintenance
surface first: `Spec_Master.csv`.

The current build path still reads `Spec_Master.csv`. The new spec-topic layer
is an offline fixture-backed authoring shape that can export compatible
`Spec_Master` rows. It does not change `build.py`, live Feishu/Lark sync, or
PDF/HTML generation.

## Direction

Split the flat spec table into three layers:

```text
spec_topics
  -> spec_topic_rows
      -> spec_topic_values
          -> compatible Spec_Master.csv
```

This keeps the existing runtime stable while making the source easier to
maintain:

- `spec_topics`: page/section-level ownership and ordering
- `spec_topic_rows`: reusable row keys, row order, slot/line semantics
- `spec_topic_values`: target-specific model/region values and translations

## Pilot Scope

- Product family: `JE-1000F`
- Target: `JE-1000F_US_en`
- Page: `specifications`
- Topics:
  - `spec.general_info`
  - `spec.input_ports`
  - `spec.output_ports`

The fixture is intentionally partial. It proves the split and export contract
without trying to migrate every `Spec_Master` row at once.

## Table Design

### `spec_topics`

One row per spec topic or section.

| Field | Required | Example |
| --- | --- | --- |
| `topic_id` | Yes | `spec.input_ports` |
| `topic_type` | Yes | `spec_section` |
| `page` | Yes | `specifications` |
| `section` | Yes | `INPUT PORTS` |
| `section_order` | Yes | `2` |
| `product_family` | No | `JE-1000F` |
| `status` | Yes | `active` |
| `description` | No | `Charging and DC input rows` |

Allowed `topic_type` values:

- `identity`
- `spec_section`
- `page_value_group`

Allowed `status` values:

- `draft`
- `active`
- `deprecated`

### `spec_topic_rows`

One row per row key / slot / line inside a topic.

| Field | Required | Example |
| --- | --- | --- |
| `topic_row_id` | Yes | `spec.input_ports.ac_input.1` |
| `topic_id` | Yes | `spec.input_ports` |
| `row_key` | Yes | `ac_input` |
| `row_order` | Yes | `1` |
| `slot_key` | No | `side.pv.spec` |
| `line_order` | Yes | `1` |
| `usage_type` | No | `spec_value` |
| `placement_key` | No | `front` |
| `value_role` | No | `value` |
| `variant_key` | No | `charge_mode` |
| `required` | Yes | true |

### `spec_topic_values`

One row per target-specific value.

| Field | Required | Example |
| --- | --- | --- |
| `topic_value_id` | Yes | `je1000f_us.ac_input.1` |
| `topic_row_id` | Yes | `spec.input_ports.ac_input.1` |
| `document_key` | Yes | `JE-1000F_US_en` |
| `model` | Yes | `JE-1000F` |
| `region` | Yes | `US` |
| `is_latest` | No | `TRUE` |
| `source_lang` | Yes | `en` |
| `row_label_source` | No | `1 x AC Input` |
| `param_source` | No | `Charge Mode` |
| `value_source` | No | `100V-120V~60Hz, 15A Max` |
| `row_label_fr` / `param_fr` / `value_fr` | No | localized values |
| `row_label_es` / `param_es` / `value_es` | No | localized values |

At least one of `row_label_source` or `value_source` should be filled.

## Local Commands

Validate the fixture contract:

```bash
python3 tools/spec_topic_contract.py validate \
  --fixtures tests/fixtures/spec_topics
```

Export a compatible temporary `Spec_Master.csv`:

```bash
python3 tools/spec_topic_adapter.py export-spec-master \
  --fixtures tests/fixtures/spec_topics \
  --model JE-1000F \
  --region US \
  --output .tmp/spec_topics/Spec_Master.csv
```

The adapter rejects writes under live data and generated-output roots:

- `data/phase1/`
- `data/phase2/`
- `docs/_review/`
- `docs/_build/`
- `reports/releases/`

## Validation Rules

The first validator catches:

- missing fixture tables or headers
- duplicate primary ids
- unknown topic types or statuses
- missing topic references from rows
- missing row references from values
- required topic rows without values
- duplicate `Spec_Master` selectors for the same target/page/row/slot/line
- invalid numeric section, row, or line order
- value rows with no display value

## Base Setup Recommendation

If this shape moves into Feishu/Lark Base, create one Base section with these
three tables first:

- `spec_topics`
- `spec_topic_rows`
- `spec_topic_values`

Keep `topic_id`, `topic_row_id`, and `topic_value_id` as stable text ids. Use
linked-record fields in the UI if helpful, but export stable ids for local
validation and adapter code.

Do not replace the existing `spec_master` sync table until a fixture export can
round-trip the target rows needed by `build.py check`.
