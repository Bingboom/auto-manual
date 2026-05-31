# Spec Master User Guide

Updated: 2026-05-24

This file explains the current phase2 spec data layer, with [`Spec_Master.csv`](../data/phase2/Spec_Master.csv) as the build-time read model.
It is meant to serve two audiences at the same time:

- editors who need to know where to put data in the CSVs
- developers who need the implementation details that keep the current flow maintainable

For the future canonical data model and CMS-direction schema boundary, see [`architecture/Content_Data_Model.md`](architecture/Content_Data_Model.md).
For current JP / US family differences and what must remain family-specific, see [`manual_family_guide.md`](manual_family_guide.md).

## 0. Current Feishu Maintenance Model

In Feishu phase2, do not maintain `规格参数表/spec_master` as the human editing table.
It is now a legacy compatibility table; normal `sync-data --table spec_master` reads the split source tables and writes the local read-model CSV directly.

Human editors should use these source tables:

- `规格参数明细` (`tblTw54UzV4ry5VD`): only rows where `Page=specifications`
- `页面占位参数` (`tblhckTT7PfVBsuG`): `Product overview`, `operation_guide`, `storage`, and `ups_mode` placeholder rows
- `参数名`: row-key dictionary; create new `Row_key` values here before selecting or copying them into source rows
- `Document_key`: target dimension table; add the target document key here before copying rows for a new model/market

In both source tables, editors maintain `Row_key_link`.
The visible `Row_key` column is a lookup from `参数名.Row_key`, so it updates from the dictionary and should not be typed by hand.
The source tables do not carry separate `Model` or `Region` fields; the rebuild step derives them from `document_key` for the compatible read model.

The generated `Spec_Master.csv` exposes `spec_row_key` as the first visible read key, followed by `document_key`.
`document_key` remains the target dimension field but is no longer the unique row key.
The generated key is:

```text
document_key + "__v" + Version + "__" + Page + "__s" + Section_order + "__r" + Row_order + "__" + Row_key + "__" + Slot_key/default("main") + "__l" + Line_order
```

Example:

```text
JE-1000F_US__v1.0__specifications__s01__r03__capacity__main__l01
JE-1000F_US__v1.0__Product_overview__s03__r02__usb_c__front_high_spec__l01
```

`Line_order` is required. Single-line rows use `1`; multi-line rows use `1`, `2`, `3`, ... in display order.
Both source tables use `source_row_key` itself as a formula-generated primary key, so editors should not type or paste this key by hand.

When source tables change, rebuild the read model snapshot with:

```bash
python3 build.py spec-master-rebuild --config configs/config.ja.yaml --expect-spec-rows 157 --expect-placeholder-rows 222
```

The command reads `sync.phase2.spec_master_sources` from config, merges the two source tables, resolves Feishu linked-record footnote refs to stable `Footnote_id` values, validates row counts and unique `spec_row_key`, and writes a `Spec_Master.csv` compatible with the existing renderer and sync flow.
Normal `sync-data --table spec_master` now uses the same two source tables directly, so the old Feishu `spec_master` total table is no longer required for snapshot sync. To push source-table values back into that legacy table for compatibility, add `--write-back`.

## 1. Which File To Edit For Which Data

Use this section first.
It answers the practical question: "I have a piece of manual data. Which file and which part of the sheet should I edit?"

| Data type | File | Where to fill it | Current rule |
| --- | --- | --- | --- |
| Product name | Feishu `规格参数明细`, exported to [`Spec_Master.csv`](../data/phase2/Spec_Master.csv) | `Page=specifications`, `Section=GENERAL INFO`, `Row_key=product_name`, fill `Value_*` | Use the row that belongs to the target `Model` + `Region` |
| Model number | Feishu `规格参数明细`, exported to [`Spec_Master.csv`](../data/phase2/Spec_Master.csv) | `Page=specifications`, `Section=GENERAL INFO`, `Row_key=model_no`, fill `Value_*` | Same placement rule as `product_name` |
| Visible spec rows | Feishu `规格参数明细`, exported to [`Spec_Master.csv`](../data/phase2/Spec_Master.csv) | `Page=specifications`, choose visible `Section`, fill `Row_key`, `Row_label_*`, `Param_*`, `Value_*` | Use this for rows that should appear in the spec table |
| Product overview labels or per-model UI text | Feishu `页面占位参数`, exported to [`Spec_Master.csv`](../data/phase2/Spec_Master.csv) | `Page=Product overview`, `Row_key=<concept_key>`, `Slot_key=<slot>` | Use this for placeholders consumed by templates |
| One value reused by Product overview and spec page | [`Spec_Master.csv`](../data/phase2/Spec_Master.csv) | `Page=Product overview, specifications,` | Use only when the same visible value is truly shared |
| Spec footnotes referenced by superscripts | [`Spec_Footnotes.csv`](../data/phase2/Spec_Footnotes.csv) | one row per `Footnote_id` | Put the visible body text here and reference it from `Spec_Master.csv` |
| Bottom-of-spec notes without superscripts | [`Spec_Notes.csv`](../data/phase2/Spec_Notes.csv) | one row per `Note_id` | Use this for standalone notes such as trademark statements |
| Spec page title and section metadata | [`Manual_Copy_Source.csv`](../data/phase2/Manual_Copy_Source.csv), exported to [`spec_titles.csv`](../data/phase2/spec_titles.csv) | one source row per visible spec title/section plus `manual_copy` Translation Memory rows | Use this for visible spec title localization and default section ordering |
| Safety intro prose | [`docs/templates/page_*/safety_*.rst`](../docs/templates) | family safety templates | Do not put long prose into `Spec_Master.csv` unless it is truly parameterized |

## 2. Current phase2 CSV Files

The current manual data layer uses these files:

- [`data/phase2/Spec_Master.csv`](../data/phase2/Spec_Master.csv)
  - main product parameters
  - visible spec rows
  - `product_name`
  - `model_no`
- page-value placeholder rows
- [`data/phase2/Spec_Footnotes.csv`](../data/phase2/Spec_Footnotes.csv)
  - superscript footnote definitions
- [`data/phase2/Spec_Notes.csv`](../data/phase2/Spec_Notes.csv)
  - bottom-of-spec notes that are not referenced by superscripts
- [`data/phase2/spec_titles.csv`](../data/phase2/spec_titles.csv)
  - localized visible title mapping for the spec page
- [`data/phase2/page_registry.csv`](../data/phase2/page_registry.csv)
  - page registry used by the remaining phase2 CSV-page flow

[`Spec_Master.csv`](../data/phase2/Spec_Master.csv) remains the main structured source for product identity, spec rows, and template substitution.

## 3. How To Fill A Row In [`Spec_Master.csv`](../data/phase2/Spec_Master.csv)

This section is the editor-facing filling guide.

### 3.1 The Columns You Usually Need

| Column | What to put here | Current rule |
| --- | --- | --- |
| `Page` | visible page ownership | Use `specifications`, `Product overview`, or `Product overview, specifications,` |
| `Section` | logical group | Use the visible spec section for spec rows; use internal container sections for page-value rows |
| `Section_order` | section order | Optional. If filled in `Spec_Master.csv`, it is the highest-priority section order; if blank, the renderer can fall back to [`spec_titles.csv`](../data/phase2/spec_titles.csv) |
| `Row_order` | row order inside a section | Use `1`, `2`, `3`, ... inside the same `document_key + Page + Section`; keep the same value across all lines of one logical row |
| `Row_key` | stable machine key | Same concept should use the same `Row_key` across regions; do not treat `Row_key` alone as a unique row ID |
| `Row_label_*` | visible row label | Fill the visible label that should appear in the final output |
| `Param_*` | left-side or prefix text inside the value cell | Use only when one row has a parameter + value pair |
| `Value_*` | main value text | Most rows need this |
| `Row_label_footnote_refs` | footnote refs attached to the row label | Fill comma-separated `Footnote_id` values when the row label needs superscript markers |
| `Param_footnote_refs` | footnote refs attached to the `Param_*` text | Fill comma-separated `Footnote_id` values when the left-side parameter text needs superscript markers |
| `Value_footnote_refs` | footnote refs attached to the `Value_*` text | Fill comma-separated `Footnote_id` values when the main value text needs superscript markers |
| `Line_order` | order of multiple lines under the same row | Use `1`, `2`, `3`, ... when the same `Row_key` spans multiple lines |
| `Slot_key` | page-value slot marker | Leave blank for visible spec rows. Use values such as `label`, `text`, `value`, `front.label`, `front.low.spec`, `side.pv.spec` for template-fed rows |
| `Model` | target model | Read-model column derived from `document_key`; do not maintain it in the source tables |
| `Region` | target region | Read-model column derived from `document_key`; do not maintain it in the source tables |
| `Source_lang` | source-language code | Store the row's source manual language as a normalized code such as `en`, `ja`, or `zh` |
| `document_key` | target document key | Must identify the target as `[Model]_[Region]`; source language stays in `Source_lang` |
| `Is_Latest` | active row flag | Keep active rows as `TRUE` |

Current schema note:

- `Spec_Master.csv` no longer has a `project_code` / `项目代码` column
- target matching is based on `Region` + `Model`

### 3.2 How To Decide What Type Of Row You Are Adding

Use this rule of thumb:

- if the text should appear as a visible row in the spec table, add a normal spec row
- if the text should fill a template placeholder such as a button label, add a row with a non-empty `Slot_key`
- if the text is a footnote, use [`Spec_Footnotes.csv`](../data/phase2/Spec_Footnotes.csv)
- if the text is long safety prose, edit the family's `docs/templates/page_*/safety_*.rst`

### 3.3 Example: Product Identity Row

Use this shape for `product_name` and `model_no`:

```csv
...,specifications,GENERAL INFO,1,product_name,Product Name,1,,Jackery Explorer 1000,...,JE-1000F
...,specifications,GENERAL INFO,1,model_no,Model No.,1,,JE-1000F / JE-1000F-SG,...,JE-1000F
```

Current placement rule:

- keep them in `GENERAL INFO`
- keep `Page=specifications` unless the value is truly shared by multiple visible pages

### 3.4 Example: Normal Visible Spec Row

A row with only one visible value:

```csv
...,specifications,GENERAL INFO,1,cell_chemistry,Cell Chemistry,1,,LiFePO4,...,JE-1000F
```

A row with `Param + Value` in the same displayed cell:

```csv
...,specifications,INPUT PORTS,2,ac_input,1 x AC Input,1,Charge Mode,"100V-120V~60Hz, 15A Max",...,JE-1000F
```

Current display rule:

- if both `Param_*` and `Value_*` exist, current renderers join them with `: `
- if only `Value_*` exists, it is displayed by itself
- if a full cell contains commas, quote the full CSV value

Current footnote rule:

- do not type `①②③` into `Row_label_*`, `Param_*`, or `Value_*`
- fill `Row_label_footnote_refs`, `Param_footnote_refs`, or `Value_footnote_refs` with comma-separated `Footnote_id` values instead
- the renderer derives the visible superscript marker from [`Spec_Footnotes.csv`](../data/phase2/Spec_Footnotes.csv) `Footnote_order`

### 3.5 Example: Multi-Line Spec Row

If the same visible row label has multiple lines, repeat the same `Row_key` and increment `Line_order`.
For page-level placeholders that are not part of the visible spec table, use the real page token instead of `specifications`:

```csv
...,storage,ENVIRONMENTAL OPERATING TEMPERATURE,4,storage_temperature,Storage Temperature,1,1 month,-20C to 45C,...,JE-1000F
...,storage,ENVIRONMENTAL OPERATING TEMPERATURE,4,storage_temperature,Storage Temperature,2,3 months,0C to 45C,...,JE-1000F
...,storage,ENVIRONMENTAL OPERATING TEMPERATURE,4,storage_temperature,Storage Temperature,3,1 year,0C to 25C,...,JE-1000F
```

Current rule:

- same visible row = same `Row_key`
- different lines under that row = different `Line_order`
- if the row is meant for a template page instead of the spec table, use that page's token in `Page`

### 3.6 Example: Template Placeholder Row

Use this shape for template-driven labels or values:

```csv
...,Product overview,CONTROLS,7,main_power_button,label,Main Power Button,1,,Main POWER Button,...,JE-1000F
...,Product overview,OUTPUT PORTS,3,ac_output,front.spec,AC Output,1,,"120V~60Hz, 12.5A, 1500W Rated",...,JE-1000F
```

Current rule:

- `Row_key` must keep only the concept itself
- leave `Slot_key` blank for visible spec rows
- fill `Slot_key` for template-fed rows
- example: `Row_key=main_power_button` + `Slot_key=label` -> `|MAIN_POWER_BUTTON_LABEL|`
- example: `Row_key=ac_input` + `Slot_key=side.spec` -> `|SIDE_AC_INPUT_SPEC|`

### 3.7 Advanced Columns Developers May Touch

Most editors can ignore this subsection.
These fields are useful when you need to maintain parser behavior rather than just fill ordinary rows.

| Column | Current implementation use |
| --- | --- |
| `row_order` / `Row_order` | explicit row order inside a section; keep it populated in the sheet, even though the parser still falls back to CSV source order for old data |
| `row_kind` / `Row_kind` | can mark rows as `data`, `title`, `section_title`, `title_map`, `note`, or `footnote` |
| `page_title_*` | can override the main spec page title |
| `section_title_*` | can override the visible section title before `spec_titles.csv` is applied |
| `line_text_*` | direct rendered row text; bypasses `Param_* + Value_*` assembly |
| `param_value_sep` | overrides the default `: ` separator between `Param_*` and `Value_*` |
| `note_text_*` / `footnote_text_*` | legacy inline note fields; prefer [`Spec_Footnotes.csv`](../data/phase2/Spec_Footnotes.csv) and [`Spec_Notes.csv`](../data/phase2/Spec_Notes.csv) instead |

## 4. Current Editing Conventions

This section is still editor-facing, but it encodes the conventions developers should preserve.

### 4.1 `Page`

Current practical values:

- `specifications`
- `Product overview`
- `Product overview, specifications,`

Current rule:

- use `specifications` for spec-only rows
- use `Product overview` for Product overview-only placeholder rows
- use the combined page list only when one row is truly shared by both visible pages

### 4.2 Visible `Section` Values

Current visible spec sections should normally be:

- `GENERAL INFO`
- `INPUT PORTS`
- `OUTPUT PORTS`
- `ENVIRONMENTAL OPERATING TEMPERATURE`

Current internal or placeholder-heavy sections may still exist in the sheet:

- `CONTROLS`
- `SETTINGS`
- `ACCESSORIES`
- `TEMPLATE VARS`

Current rule:

- `CONTROLS`, `SETTINGS`, and `ACCESSORIES` are usually containers for rows with non-empty `Slot_key`
- `TEMPLATE VARS` is internal and should not be treated as a visible spec section
- for new visible temperature rows, prefer `ENVIRONMENTAL OPERATING TEMPERATURE`

### 4.3 Recommended Canonical `Row_key` Set

Current preferred identity keys:

- `product_name`
- `model_no`

Current preferred general-info keys:

- `capacity`
- `cell_chemistry`
- `weight`
- `dimensions`
- `cycle_life`

Current preferred temperature keys:

- `charging_temperature`
- `discharging_temperature`
- `storage_temperature`

### 4.4 `Row_key` Is Not A Single-Column Primary Key

Current rule:

- `Row_key` is a semantic key, not a row-unique key
- one `Row_key` may appear in multiple `Region` values
- one `Row_key` may appear in multiple `Page` values
- one `Row_key` may appear multiple times with different `Line_order` values
- this is expected for rows such as `ac_input`, `usb_c`, `ac_output`, and `storage_temperature`

What this means in practice:

- use `Row_key` to answer "what concept is this row about?"
- do not use `Row_key` alone to answer "is this the same physical row in the sheet?"

Current code behavior:

- duplicate-latest validation groups rows by `Model + Region + Page + Row_key + Line_order`
- runtime lookup also matches by `Model`, `Region`, `Row_key`, `Page`, and optionally `Line_order`

Recommended maintenance identity:

```text
Maint_key = Model | Region | normalized(Page) | Row_key | normalized(Slot_key) | normalized(Line_order)
```

Normalization rule:

- `Model`: trim spaces and keep the build target value, for example `JE-1000F`
- `Region`: trim spaces and use the canonical region token, for example `US`, `JP`
- `Page`: split by comma, trim each token, lowercase for comparison, sort the tokens, then join with `+`
- `Row_key`: lowercase snake_case semantic key such as `cell_chemistry` or `ac_output`
- `Slot_key`: trim spaces, lowercase, keep blank for visible spec rows
- `Line_order`: if empty, treat it as `1`

Examples:

- `JE-1000F|US|specifications|ac_input||1`
- `JE-1000F|US|specifications|ac_input||2`
- `JE-1000F|US|storage|storage_temperature||3`
- `JE-1000F|US|product overview|ac_output|front.spec|1`

Recommended editing rule:

- keep `Row_key` stable even when the visible label changes
- if only translation or wording changes, keep the same `Row_key`
- if only page ownership changes, keep the same `Row_key`
- if one visible row grows from one line to multiple lines, keep the same `Row_key` and split by `Line_order`
- create a new `Row_key` only when the underlying concept changes

Anti-patterns to avoid:

- do not encode language into `Row_key`
- do not encode the current visible label into `Row_key`
- do not encode units into `Row_key`
- do not encode section order or line order into `Row_key`
- do not rename `Row_key` just because one region uses a shorter or more marketing-style label

### 4.5 Keep `Row_key` Deterministic And Keep `Slot_key` Human-Readable

Current recommendation:

- do not derive `Row_key` directly from `Row_label_*`, `Param_*`, or `Value_*`
- do not pack placement, template usage, or display-role information into `Row_key`
- `Row_key` should represent the concept only
- the template-facing shape should be captured by `Slot_key`

Why the current `tpl_*` style is not ideal:

- `tpl_front_ac_output_label` mixes at least four meanings into one field: template usage, placement, concept, and display role
- once those meanings are packed into `Row_key`, the key is no longer stable when layout or placeholder strategy changes
- the same concept should keep one canonical key even if it appears on different pages or in different UI slots

Recommended generation rule:

```text
Row_key = concept only
Slot_key = blank | role | placement.role | placement.variant.role
```

Recommended `Slot_key` examples:

- blank -> visible spec row
- `label` -> concept-level label placeholder
- `value` -> bare page value whose placeholder is just the concept name
- `text` -> free-text placeholder such as `UPS_BYPASS_OUTPUT_TEXT`
- `front.label` -> front-view label
- `front.spec` -> front-view spec text
- `front.low.label` -> front-view low-variant label
- `side.pv.spec` -> side-view PV spec text

Examples:

- `cell_chemistry + blank` -> spec row
- `storage_temperature + blank` -> spec row
- `main_power_button + label` -> `|MAIN_POWER_BUTTON_LABEL|`
- `ac_output + front.spec` -> `|FRONT_AC_OUTPUT_SPEC|`
- `dc_input + side.pv.spec` -> `|SIDE_DC_INPUT_PV_SPEC|`

Recommended constraints:

- `Row_key` should be lowercase snake_case English
- `Slot_key` should be lowercase dot-separated text
- `Slot_key` should be blank for visible spec rows
- `Line_order` should never be folded into `Row_key`; keep it in `Line_order`

Practical conclusion:

- with this model, `Row_key` becomes truly canonical and reusable
- the real row identity becomes a composite of `Model`, `Region`, `Page`, `Row_key`, `Slot_key`, and `Line_order`
- current `tpl_*` rows should be treated as a legacy compatibility format, not the long-term writing rule
- code may still derive selector fields internally, but the sheet should not require editors to hand-maintain them

Current normalization guidance:

- prefer `cell_chemistry` over region-only variants such as `battery_type`
- prefer split `dimensions` and `weight` over combined keys such as `size_weight`
- prefer `discharging_temperature` over `operating_temperature` when the source is really the discharge range
- keep a region-specific key only if it represents a genuinely different concept, not just a different label

### 4.6 Language Columns

Current reality:

- the sheet now uses `Row_label_source`, `Param_source`, and `Value_source` as the shared source-text columns
- these source columns hold the row's actual source-manual text
- `Source_lang` stores that source language explicitly as a normalized code such as `en`, `ja`, or `zh`
- `document_key` identifies the target as `[Model]_[Region]`; source language stays in `Source_lang`
- `Row_label_en`, `Param_en`, and `Value_en` are no longer accepted; rename them to `*_source`

Current practical rule:

- if dedicated localized columns already exist for the field, use them
- if they do not exist yet, the `*_source` columns are the active source
- source-language text must not stay in `*_en`; move it into `*_source`
- keep `Source_lang` aligned with the real source columns; for example, if `Value_source` holds Japanese source text then `Source_lang` should be `ja`
- `Source_lang` is now the explicit source-language declaration for the row; code no longer infers source language from `Region`
- keep `document_key` aligned with the row identity as `[Model]_[Region]`
- `*_source` must be populated for the language declared by `Source_lang`
- keep the visible text correct first, and trust the row's explicit `Source_lang` workflow more than any legacy header alias
- current audit expectation depends on `Source_lang`; `ROW_LABEL_SOURCE_CONTAINS_EAST_ASIAN_TEXT` only applies to rows whose declared source language is English

## 5. Developer Implementation Details

This section is for people maintaining the code path, not just editing the CSV.

### 5.1 Where [`Spec_Master.csv`](../data/phase2/Spec_Master.csv) Is Used

Current flow:

1. [`build.py`](../build.py) or [`tools/build_docs.py`](../tools/build_docs.py) resolves target `model` and `region`
2. product identity and template substitutions are resolved from [`Spec_Master.csv`](../data/phase2/Spec_Master.csv)
3. [`tools/csv_page_build.py`](../tools/csv_page_build.py) renders CSV-driven content
4. [`tools/gen_index_bundle.py`](../tools/gen_index_bundle.py) materializes runtime pages
5. `_review` can then be seeded or synced from that runtime output
6. `word`, `html`, `pdf`, `publish`, and `release-manifest` consume the prepared bundle or its outputs

That means one data change can affect:

- generated spec content
- placeholder pages
- Word title or metadata
- review sync results
- diff-report field tracing
- release manifest metadata

### 5.2 Current Row Matching Logic

Current utility code lives mainly in [`tools/utils/spec_master.py`](../tools/utils/spec_master.py).

Current filter order:

- `enabled` / `Enabled` must be truthy if present
- `Is_Latest` / `is_latest` must be truthy if present
- `Row_key` must match when requested
- `Page` must match when a page filter is passed
- `Model` must match when provided and when the row has a model value
- `Region` must match when provided and when the row has a region value
- `Line_order` must match when requested

Current ranking rule:

- rows are scored by model match, region match, language-specific value presence, and active-state presence
- candidates are then sorted by score first, then by CSV line number
- the first ranked row wins

Implication:

- duplicate active rows can silently override each other
- earlier CSV lines win on ties

### 5.3 Current `Page` Matching Logic

Current page matching is implemented by tokenizing the cell:

- split by comma
- trim spaces
- lowercase

Current implementation behavior:

- `Page=Product overview, specifications,` matches either page token
- blank `Page` currently matches all page filters

Current code-level consequence:

- blank `Page` is permissive
- do not rely on blank page cells as intentional data modeling

### 5.4 Current Spec Page Extraction

Current spec parsing lives mainly in [`tools/csv_pages/renderers_spec_parser.py`](../tools/csv_pages/renderers_spec_parser.py).

The parser treats the input as `Spec_Master`-style data when:

- the rows have `Section`, `Row_key`, and `Line_order`
- and do not look like content-block rows

Current visible-spec filtering rule:

- only rows whose `Page` matches `spec` / `specifications` are used for the spec page
- rows with non-empty `Slot_key` are skipped
- rows under `Section=TEMPLATE VARS` are skipped

Current row assembly rule:

- rows are grouped by `Section`
- inside each section, rows are grouped by `Row_key`
- multiple lines under the same `Row_key` are sorted by `Line_order`
- if both `Param_*` and `Value_*` exist, the renderer joins them with `: `

Current title rule:

- page title and section title can come from row fields when present
- [`spec_titles.csv`](../data/phase2/spec_titles.csv) is then applied as a visible title map
- missing mapped titles fall back to the source section title

### 5.5 Current Placeholder Resolution

Current placeholder resolution also lives in [`tools/utils/spec_master.py`](../tools/utils/spec_master.py).

Current behavior:

- `product_name` is resolved with `pages=None`
- `model_no` is resolved with `pages=None`
- rows with non-empty `Slot_key` are also collected with `pages=None`
- `storage_temperature` rows under `Page=storage` are exposed as multiline placeholders

This is important:

- `Page` does not currently gate identity resolution
- `Page` does not currently gate page-value placeholder collection
- `Page` is therefore stronger as page-ownership metadata than as a guaranteed lookup fence

Current derived placeholder rules:

- `PRODUCT_SHORT_NAME` is derived by stripping the `Jackery ` prefix
- `_BOLD` variants are generated automatically
- `_LOWER` variants are generated automatically for keys ending in `_LABEL`
- for page-value rows with `Line_order > 1`, the placeholder gains a suffix such as `_2`
- `storage_temperature` currently generates `STORAGE_TEMPERATURE_LINE_1/2/3` plus matching `..._PARAM_1/2/3` and `..._VALUE_1/2/3`
- language-specific translated columns can be added when a page placeholder needs localized text instead of source-language fallback

### 5.6 Current Diff-Report Behavior

Current diff-report field extraction lives mainly in [`tools/diff_report.py`](../tools/diff_report.py).

Current rule:

- diff-report filters spec rows by `Page=spec` / `specifications`
- it skips rows with non-empty `Slot_key`
- it skips `Section=TEMPLATE VARS`
- it uses [`spec_titles.csv`](../data/phase2/spec_titles.csv) to render localized visible section titles

That means a title-map change can affect diff-report output even when the visible spec table still builds correctly.

## 6. [`spec_titles.csv`](../data/phase2/spec_titles.csv) Rule

[`spec_titles.csv`](../data/phase2/spec_titles.csv) is the generated visible spec title and section-metadata table. Do not hand-edit it; maintain the source-language rows in [`Manual_Copy_Source.csv`](../data/phase2/Manual_Copy_Source.csv) with `page_id=specifications`, then maintain the corresponding Translation Memory row with `用途标签=manual_copy`.

Current typical fields:

- `title_en`
- `section_order`
- `title_zh`
- `title_jp`
- `title_fr`
- `title_es`

Current recommended scope:

- `SPECIFICATIONS`
- `GENERAL INFO`
- `INPUT PORTS`
- `OUTPUT PORTS`
- `ENVIRONMENTAL OPERATING TEMPERATURE`

Current order rule:

- use `section_order` here as the default order for visible spec sections
- if a row in [`Spec_Master.csv`](../data/phase2/Spec_Master.csv) already has `Section_order`, that explicit value wins
- if `Section_order` is blank in [`Spec_Master.csv`](../data/phase2/Spec_Master.csv), the renderer may fall back to `spec_titles.csv section_order`

Do not use [`spec_titles.csv`](../data/phase2/spec_titles.csv) for:

- internal placeholder sections such as `CONTROLS`, `SETTINGS`, `ACCESSORIES`, or `TEMPLATE VARS`
- general product parameter storage
- row-level labels

Current fallback rule:

- if a title is missing from [`spec_titles.csv`](../data/phase2/spec_titles.csv), current renderers fall back to the source section title

## 7. Spec Footnotes And Notes

Keep spec-table content, superscript footnotes, and standalone notes separate.
This makes the spec page easier to validate and keeps superscript numbering deterministic.

### 7.1 [`Spec_Footnotes.csv`](../data/phase2/Spec_Footnotes.csv)

Use [`Spec_Footnotes.csv`](../data/phase2/Spec_Footnotes.csv) for:

- footnotes that are referenced by superscripts in the spec table
- one reusable definition row per `Footnote_id`

Current schema:

- `Region`
- `Model`
- `Source_lang`
- `Is_Latest`
- `Page`
- `Footnote_id`
- `Footnote_order`
- `Type`
- `Text_en`
- `Text_fr`
- `Text_es`
- `Text_ja`
- `Enabled`

Current rule:

- keep only plain body text in `Text_*`
- do not store `①②③` or `*` in the footnote text cells
- use `Footnote_order` to control the rendered marker order
- keep `Type=Footnote` for explicit trailer classification coming from the Feishu source
- `Footnote_id` must be stable enough to be referenced from [`Spec_Master.csv`](../data/phase2/Spec_Master.csv)
- `Spec_Footnotes.csv` no longer has a `project_code` / `项目代码` column
- target matching is based on `Region` + `Model`

### 7.2 [`Spec_Notes.csv`](../data/phase2/Spec_Notes.csv)

Use [`Spec_Notes.csv`](../data/phase2/Spec_Notes.csv) for:

- bottom-of-spec notes that are not referenced by a superscript
- standalone statements such as trademark or standards notes

Current schema:

- `Region`
- `Model`
- `Source_lang`
- `Is_Latest`
- `Page`
- `Note_id`
- `Note_order`
- `Type`
- `Text_en`
- `Text_fr`
- `Text_es`
- `Text_ja`
- `Enabled`

Current rule:

- keep only plain note text in `Text_*`
- use `Note_order` to control the rendered note order
- keep `Type=Note` for explicit trailer classification coming from the Feishu source
- `Spec_Notes.csv` is not referenced from spec cells and does not generate superscript markers
- when one rendered spec page contains both notes and footnotes at the bottom, their final display order follows [`../docs/templates/spec_template.rst`](../docs/templates/spec_template.rst)

### 7.3 How [`Spec_Master.csv`](../data/phase2/Spec_Master.csv) References Footnotes

Use these columns in [`Spec_Master.csv`](../data/phase2/Spec_Master.csv):

- `Row_label_footnote_refs`
- `Param_footnote_refs`
- `Value_footnote_refs`

Current rule:

- each cell holds zero, one, or more comma-separated `Footnote_id` values
- do not handwrite `①②③` into `Row_label_*`, `Param_*`, or `Value_*`
- every referenced `Footnote_id` must exist in [`Spec_Footnotes.csv`](../data/phase2/Spec_Footnotes.csv) for the same target

Example:

```csv
...,ac_input,1 x AC Input,2,Bypass Mode,"100V-120V~60Hz, 15A Max",ac_bypass,,...
...,ac_output_bypass,AC Output in Bypass Mode,1,,100V-120V~60Hz,ac_bypass,,...
```

### 7.4 Current Validation Expectations

Current validation checks now enforce:

- `Region + Model + Page + Footnote_id` must be unique
- `Region + Model + Page + Footnote_order` must be unique
- `Region + Model + Page + Note_id` must be unique
- `Region + Model + Page + Note_order` must be unique
- `Row_label_footnote_refs`, `Param_footnote_refs`, and `Value_footnote_refs` must only reference existing `Footnote_id` values
- hardcoded superscript markers such as `①②③` in visible spec text are treated as legacy input and should be removed

## 8. Safety Templates and [`page_registry.csv`](../data/phase2/page_registry.csv)

Safety intro pages are now maintained as fixed RST templates. [`page_registry.csv`](../data/phase2/page_registry.csv) remains only for the csv-page flow that is still active.

Current rule:

- use `docs/templates/page_*/safety_*.rst` for safety intro content
- use [`page_registry.csv`](../data/phase2/page_registry.csv) for block/page structure
- do not push safety prose into [`Spec_Master.csv`](../data/phase2/Spec_Master.csv) unless it is really a parameterized row

## 9. Safe Edit Workflow

### 9.1 Family Config Rule

Use the shared family configs:

- `configs/config.us.yaml` for US family flow
- `configs/config.ja.yaml` for JP family flow

Do not create one config per model just because the model changed.

### 9.2 Data Change Checklist

When you change:

- [`Spec_Master.csv`](../data/phase2/Spec_Master.csv)
- [`Spec_Footnotes.csv`](../data/phase2/Spec_Footnotes.csv)
- [`Spec_Notes.csv`](../data/phase2/Spec_Notes.csv)
- [`spec_titles.csv`](../data/phase2/spec_titles.csv)
follow this order:

1. run `check`
2. if the target is already in review, run `sync-review`
3. publish from review only after the review bundle is current
4. generate release-manifest when the export artifacts matter

### 9.3 Common Validation Commands

Logic or data validation:

```powershell
python -m unittest
python build.py check --config configs/config.us.yaml --model JE-1000F --region US
python build.py check --config configs/config.ja.yaml --model JE-1000F --region JP
```

Mapping export:

```powershell
python tools/export_spec_master_row_key_mapping.py
```

Current output:

- [`data/phase2/row_key_mapping.csv`](../data/phase2/row_key_mapping.csv)
- [`data/phase2/row_key_mapping.csv`](../data/phase2/row_key_mapping.csv) after `python build.py sync-data --config configs/config.us.yaml --data-root data/phase2`
- [`reports/spec_master/row_key_mapping.md`](../reports/spec_master/row_key_mapping.md)
- `row_key_mapping.csv` is the human-maintained source of truth for `Row_label_source + Line_order -> Row_key`
- the CSV keeps `Row_label_source`, `Line_order`, `Row_key`, and `Remark`
- the first column stays `Row_label_source`, so the sheet can still be imported into external tools for label-first lookup or bi-directional reference
- `Line_order` is the second lookup key and must stay aligned with [`Spec_Master.csv`](../data/phase2/Spec_Master.csv)
- rerunning the export script syncs the latest `Row_label_source + Line_order` set from [`Spec_Master.csv`](../data/phase2/Spec_Master.csv) while preserving any existing manual `Row_key` and `Remark`
- keep `Row_key` in snake_case canonical form, for example `Product Name -> product_name`
- when you reconcile [`Spec_Master.csv`](../data/phase2/Spec_Master.csv), align each `Row_key` to the matching `Row_label_source + Line_order` entry from this mapping table

Review sync:

```powershell
python build.py sync-review --config configs/config.ja.yaml --model JE-1000F --region JP
python build.py sync-review --config configs/config.ja.yaml --model JE-1000F --region JP --sync-scope generated
python build.py sync-review --config configs/config.ja.yaml --model JE-1000F --region JP --page-file 02_whats_in_the_box.rst
```

Diff report:

```powershell
python build.py diff-report --config configs/config.us.yaml --model JE-1000F --region US
```

Use `review --refresh-review` only if you intentionally want to reseed the whole review bundle.

## 10. Common Failures

### 10.1 Product Name Resolution Failure

Symptom:

- `Failed to resolve Product Name from Spec_Master.csv`

Check:

- target `model`
- target `region`
- language coverage
- `Row_key=product_name`
- whether the matching row is active and not shadowed by an unintended duplicate

### 10.2 Template Placeholder Leaks

Symptom:

- `|PLACEHOLDER|` still appears in `_build` or `_review`

Check:

- matching page-value row exists
- value is not empty
- there is not a duplicate page-value row winning earlier in ranking
- page contract covers the page if it is placeholder-heavy

### 10.3 Page-Scope Confusion

Symptom:

- a row does not show on the spec page
- or a placeholder still resolves even though its `Page` looks unrelated

Check:

- `Page` tokens are comma-split and case-insensitive
- blank `Page` currently matches all filters
- spec-page rendering filters by `Page`
- current identity and template substitution lookup does not

### 10.4 Stale Foreign Identity in Review or Runtime Output

Symptom:

- `STALE_IDENTITY_LITERAL` appears during `python build.py check`

Check:

- the template or review text is not carrying an old product name
- the current target `product_name` and `model_no` are correct
- if the foreign literal is intentional, add it to `checks.allowed_foreign_identity_literals`

### 10.5 Review Not Updated After Data Change

Symptom:

- runtime draft changed but `_review` still shows old parameter text

Check:

- run `python build.py sync-review ...`
- confirm the page is in the default sync scope or include it with `--page-file`

### 10.6 Section Title Not Localized

Symptom:

- the spec page shows the raw English section name instead of the localized title you expected

Check:

- [`spec_titles.csv`](../data/phase2/spec_titles.csv) contains the visible section title, not an internal container section
- the target language column exists
- the section title in the CSV matches the rendered source section title

## 11. Minimal Example

For `JE-1000F / JP`, a common data-change flow is:

```powershell
python build.py check --config configs/config.ja.yaml --model JE-1000F --region JP
python build.py sync-review --config configs/config.ja.yaml --model JE-1000F --region JP
python build.py publish --config configs/config.ja.yaml --model JE-1000F --region JP
python build.py release-manifest --config configs/config.ja.yaml --model JE-1000F --region JP
```

This is the current maintainable path:

- change data
- validate
- sync review
- publish from review
- keep the release manifest with the exported outputs
