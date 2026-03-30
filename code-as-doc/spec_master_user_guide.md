# Spec Master User Guide

Updated: 2026-03-27

This file explains the current phase1 data layer, with [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) as the center.
It is meant to serve two audiences at the same time:

- editors who need to know where to put data in the CSVs
- developers who need the implementation details that keep the current flow maintainable

For the future canonical data model and CMS-direction schema boundary, see [`architecture/Content_Data_Model.md`](architecture/Content_Data_Model.md).
For current JP / US family differences and what must remain family-specific, see [`manual_family_guide.md`](manual_family_guide.md).

## 1. Which File To Edit For Which Data

Use this section first.
It answers the practical question: "I have a piece of manual data. Which file and which part of the sheet should I edit?"

| Data type | File | Where to fill it | Current rule |
| --- | --- | --- | --- |
| Product name | [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) | `Page=specifications`, `Section=GENERAL INFO`, `Row_key=product_name`, fill `Value_*` | Use the row that belongs to the target `Model` + `Region` |
| Model number | [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) | `Page=specifications`, `Section=GENERAL INFO`, `Row_key=model_no`, fill `Value_*` | Same placement rule as `product_name` |
| Visible spec rows | [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) | `Page=specifications`, choose visible `Section`, fill `Row_key`, `Row_label_*`, `Param_*`, `Value_*` | Use this for rows that should appear in the spec table |
| Product overview labels or per-model UI text | [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) | `Page=Product overview`, `Row_key=<concept_key>`, `Slot_key=<slot>` | Use this for placeholders consumed by templates |
| One value reused by Product overview and spec page | [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) | `Page=Product overview, specifications,` | Use only when the same visible value is truly shared |
| Spec footnotes | [`Spec_Footnotes.csv`](../data/phase1/Spec_Footnotes.csv) | footnote CSV rows | Do not stuff footnotes into visible spec rows just to keep all text in one file |
| Spec page title translation | [`spec_titles.csv`](../data/phase1/spec_titles.csv) | one row per visible spec title | Only for visible spec page titles |
| Safety prose or block text | [`content_blocks.csv`](../data/phase1/content_blocks.csv) + [`page_registry.csv`](../data/phase1/page_registry.csv) | content-block flow | Do not put long prose into `Spec_Master.csv` unless it is truly parameterized |

## 2. Current Phase1 CSV Files

The current manual data layer uses these files:

- [`data/phase1/Spec_Master.csv`](../data/phase1/Spec_Master.csv)
  - main product parameters
  - visible spec rows
  - `product_name`
  - `model_no`
- page-value placeholder rows
- [`data/phase1/Spec_Footnotes.csv`](../data/phase1/Spec_Footnotes.csv)
  - spec footnotes
- [`data/phase1/spec_titles.csv`](../data/phase1/spec_titles.csv)
  - localized visible title mapping for the spec page
- [`data/phase1/content_blocks.csv`](../data/phase1/content_blocks.csv)
  - block-based safety and content sections
- [`data/phase1/page_registry.csv`](../data/phase1/page_registry.csv)
  - page/block registry used by the phase1 content-block flow

[`Spec_Master.csv`](../data/phase1/Spec_Master.csv) remains the main structured source for product identity, spec rows, and template substitution.

## 3. How To Fill A Row In [`Spec_Master.csv`](../data/phase1/Spec_Master.csv)

This section is the editor-facing filling guide.

### 3.1 The Columns You Usually Need

| Column | What to put here | Current rule |
| --- | --- | --- |
| `Page` | visible page ownership | Use `specifications`, `Product overview`, or `Product overview, specifications,` |
| `Section` | logical group | Use the visible spec section for spec rows; use internal container sections for page-value rows |
| `Section_order` | section order | Keep section order consistent with current section conventions |
| `Row_key` | stable machine key | Same concept should use the same `Row_key` across regions; do not treat `Row_key` alone as a unique row ID |
| `Row_label_*` | visible row label | Fill the visible label that should appear in the final output |
| `Param_*` | left-side or prefix text inside the value cell | Use only when one row has a parameter + value pair |
| `Value_*` | main value text | Most rows need this |
| `Line_order` | order of multiple lines under the same row | Use `1`, `2`, `3`, ... when the same `Row_key` spans multiple lines |
| `Slot_key` | page-value slot marker | Leave blank for visible spec rows. Use values such as `label`, `text`, `value`, `front.label`, `front.low.spec`, `side.pv.spec` for template-fed rows |
| `Model` | target model | Must match the intended target build |
| `Region` | target region | Must match the intended target build |
| `Source_lang` | source-language code | Store the row's source manual language as a normalized code such as `en`, `ja`, or `zh` |
| `Is_Latest` | active row flag | Keep active rows as `TRUE` |

Current schema note:

- `Spec_Master.csv` no longer has a `project_code` / `项目代码` column
- target matching is based on `Region` + `Model`

### 3.2 How To Decide What Type Of Row You Are Adding

Use this rule of thumb:

- if the text should appear as a visible row in the spec table, add a normal spec row
- if the text should fill a template placeholder such as a button label, add a row with a non-empty `Slot_key`
- if the text is a footnote, use [`Spec_Footnotes.csv`](../data/phase1/Spec_Footnotes.csv)
- if the text is long safety prose, use [`content_blocks.csv`](../data/phase1/content_blocks.csv)

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
| `row_order` / `Row_order` | explicit row order inside a section; if missing, current parser falls back to CSV source order |
| `row_kind` / `Row_kind` | can mark rows as `data`, `title`, `section_title`, `title_map`, `note`, or `footnote` |
| `page_title_*` | can override the main spec page title |
| `section_title_*` | can override the visible section title before `spec_titles.csv` is applied |
| `line_text_*` | direct rendered row text; bypasses `Param_* + Value_*` assembly |
| `param_value_sep` | overrides the default `: ` separator between `Param_*` and `Value_*` |
| `note_text_*` / `footnote_text_*` | advanced inline note fields; current repo usually prefers `Spec_Footnotes.csv` instead |

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
- `Row_label_en`, `Param_en`, and `Value_en` are no longer accepted; rename them to `*_source`

Current practical rule:

- if dedicated localized columns already exist for the field, use them
- if they do not exist yet, the `*_source` columns are the active source
- source-language text must not stay in `*_en`; move it into `*_source`
- keep `Source_lang` aligned with the real source columns; for example, if `Value_source` holds Japanese source text then `Source_lang` should be `ja`
- `Source_lang` is now the explicit source-language declaration for the row; code no longer infers source language from `Region`
- `*_source` must be populated for the language declared by `Source_lang`
- keep the visible text correct first, and trust the row's explicit `Source_lang` workflow more than any legacy header alias
- current audit expectation depends on `Source_lang`; `ROW_LABEL_SOURCE_CONTAINS_EAST_ASIAN_TEXT` only applies to rows whose declared source language is English

## 5. Developer Implementation Details

This section is for people maintaining the code path, not just editing the CSV.

### 5.1 Where [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) Is Used

Current flow:

1. [`build.py`](../build.py) or [`tools/build_docs.py`](../tools/build_docs.py) resolves target `model` and `region`
2. product identity and template substitutions are resolved from [`Spec_Master.csv`](../data/phase1/Spec_Master.csv)
3. [`tools/phase1_build.py`](../tools/phase1_build.py) renders CSV-driven content
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

Current spec parsing lives mainly in [`tools/phase1/renderers_spec_parser.py`](../tools/phase1/renderers_spec_parser.py).

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
- [`spec_titles.csv`](../data/phase1/spec_titles.csv) is then applied as a visible title map
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
- it uses [`spec_titles.csv`](../data/phase1/spec_titles.csv) to render localized visible section titles

That means a title-map change can affect diff-report output even when the visible spec table still builds correctly.

## 6. [`spec_titles.csv`](../data/phase1/spec_titles.csv) Rule

[`spec_titles.csv`](../data/phase1/spec_titles.csv) is only the localized title dictionary for the visible spec page.

Current typical fields:

- `title_en`
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

Do not use [`spec_titles.csv`](../data/phase1/spec_titles.csv) for:

- internal placeholder sections such as `CONTROLS`, `SETTINGS`, `ACCESSORIES`, or `TEMPLATE VARS`
- general product parameter storage
- row-level labels

Current fallback rule:

- if a title is missing from [`spec_titles.csv`](../data/phase1/spec_titles.csv), current renderers fall back to the source section title

## 7. [`Spec_Footnotes.csv`](../data/phase1/Spec_Footnotes.csv) Rule

Keep footnotes separate from the main spec rows.
This makes spec tables and note content easier to maintain independently.

Use [`Spec_Footnotes.csv`](../data/phase1/Spec_Footnotes.csv) for:

- spec footnotes
- spec notes that are structurally separate from the main table rows

Do not fold footnotes back into the main spec rows just to keep all text in one file.

Current schema note:

- `Spec_Footnotes.csv` no longer has a `project_code` / `项目代码` column
- target matching is based on `Region` + `Model`

## 8. [`content_blocks.csv`](../data/phase1/content_blocks.csv) and [`page_registry.csv`](../data/phase1/page_registry.csv)

These files support the phase1 content-block system used mainly for safety or block-driven pages.

Current rule:

- use [`content_blocks.csv`](../data/phase1/content_blocks.csv) for content blocks
- use [`page_registry.csv`](../data/phase1/page_registry.csv) for block/page structure
- do not push safety prose into [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) unless it is really a parameterized row

## 9. Safe Edit Workflow

### 9.1 Family Config Rule

Use the shared family configs:

- `config.yaml` for US family flow
- `config.ja.yaml` for JP family flow

Do not create one config per model just because the model changed.

### 9.2 Data Change Checklist

When you change:

- [`Spec_Master.csv`](../data/phase1/Spec_Master.csv)
- [`Spec_Footnotes.csv`](../data/phase1/Spec_Footnotes.csv)
- [`spec_titles.csv`](../data/phase1/spec_titles.csv)
- [`content_blocks.csv`](../data/phase1/content_blocks.csv)

follow this order:

1. run `check`
2. if the target is already in review, run `sync-review`
3. publish from review only after the review bundle is current
4. generate release-manifest when the export artifacts matter

### 9.3 Common Validation Commands

Logic or data validation:

```powershell
python -m unittest
python build.py check --config config.yaml --model JE-1000F --region US
python build.py check --config config.ja.yaml --model JE-1000F --region JP
```

Review sync:

```powershell
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP --sync-scope generated
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP --page-file 02_whats_in_the_box.rst
```

Diff report:

```powershell
python build.py diff-report --config config.yaml --model JE-1000F --region US
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

- [`spec_titles.csv`](../data/phase1/spec_titles.csv) contains the visible section title, not an internal container section
- the target language column exists
- the section title in the CSV matches the rendered source section title

## 11. Minimal Example

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
