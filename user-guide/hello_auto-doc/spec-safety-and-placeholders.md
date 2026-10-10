# Workflow guide: spec, safety, symbols and placeholder rules

Part of the [workflow guide](../hello_auto-doc.md); its index lists the other topics.
Add new notes for this topic here, not to the hub.

   - [`data/phase2/page_registry.csv`](../../data/phase2/page_registry.csv) remains repo-maintained; `sync-data` copies it into isolated `--data-root` snapshots such as `.tmp/review-start/phase2`
   - page selection/applicability and [`data/layout_params.csv`](../../data/layout_params.csv) remain repo-maintained inputs
   - Safety intro pages are maintained in [`docs/templates/page_*/safety_*.rst`](../../docs/templates); the standalone user maintenance instructions page is maintained in shared templates such as [`docs/templates/page_shared/en/01_user_maintenance_instructions.rst`](../../docs/templates/page_shared/en/01_user_maintenance_instructions.rst) and is included immediately before `symbols`; JP keeps the detailed safety warnings in [`docs/templates/page_jp/01_meaning_of_symbols.rst`](../../docs/templates/page_jp/01_meaning_of_symbols.rst). The old `content_blocks.csv` safety source has been removed from the active repo flow
   - `Spec_Footnotes.csv` now holds only reusable spec footnote definitions; `Footnote_order` controls the rendered superscript marker order and `Footnote_id` is referenced from `Spec_Master.csv`
   - CSV/PDF and IDML use one shared footnote-marker rule: comma-separated IDs retain their order and repeated IDs print once. Existing language fallback and target selection remain unchanged.
   - `Spec_Footnotes.csv` and `Spec_Notes.csv` both carry a `Type` field from the Feishu source; keep it explicit as `Footnote` or `Note` so downstream renderers do not infer type from the visible text
   - `Spec_Notes.csv` holds bottom-of-spec notes that are not tied to superscript references, such as trademark statements
   - `Spec_Footnotes.csv` and `Spec_Notes.csv` now match rows by `Region` + `Model`; `project_code` / `项目代码` is no longer used there either
   - when one spec page renders both bottom notes and bottom footnotes, the final output order follows the template named by the `spec` row of the `page_registry.csv` the build reads (each frozen `manual_sources/.../phase2` source carries its own; `data/phase2/page_registry.csv` serves every live target): the default [`docs/templates/spec_template.rst`](../../docs/templates/spec_template.rst) puts the notes (such as the ※ trademark note) first, and [`docs/templates/spec_template_footnotes_first.rst`](../../docs/templates/spec_template_footnotes_first.rst) puts the footnotes first, for sources whose approved print does. Only the Web and the Word bundle (which takes its trailer order from the HTML) follow that choice; the PDF and IDML output is the same for both
   - `Spec_Master.csv` uses `Row_label_source`, `Param_source`, and `Value_source` as the shared source-language columns; `Source_lang` stores that source-language code explicitly, for example `en`, `ja`, and `zh`, and code no longer infers it from `Region`
   - `Spec_Master.csv` now starts with `spec_row_key`; `document_key` is still the target dimension, but not the unique row key
   - Specification rows sharing `Row_key` retain their distinct localized labels and label footnotes. Equal labels remain multiline groups; differing labels are separate rows ordered by `Line_order` within that group. Keep the released manual's port names in the source instead of relying on inferred wattage labels.
   - `document_key` is a derived helper column and may use either `[Model]_[Region]` or `[Model]_[Region]_[Source_lang]`
   - `Line_order` is required for spec rebuilds: use `1` for one-line rows and `1`, `2`, `3`, ... for multi-line values
   - the solar-panel input range in the eight shared-language charging-method pages comes from `页面占位参数`: use `Page=charging_methods`, `Row_key=pv_input_range`, `Slot_key=value`, and preserve the approved language-specific dash/spacing exactly; the template token is `|PV_INPUT_RANGE|`. The current JE-1000F US/EU/AU/KR and JE-1500D pt-BR rows were F6-approved, seeded, and read back on 2026-07-31; a future target still needs its own exact-value approval plus post-sync `diff-report`
   - the connector name in those charging pages uses `Page=charging_methods`, `Row_key=dc_input_connector`, `Slot_key=value` and token `|DC_INPUT_CONNECTOR|`; the shared UPS transfer time uses `Page=ups_mode`, `Row_key=ups_transfer_time`, `Slot_key=value` and token `|UPS_TRANSFER_TIME|`. Keep localized units in the value and keep the separate `0 ms` incompatibility caution as prose. The same five current document keys were seeded in the 2026-07-31 F6 batch; never blindly clone their values into a new target
   - `Row_label_en`, `Param_en`, and `Value_en` are no longer supported; rename them to `*_source`
   - `Row_label_footnote_refs`, `Param_footnote_refs`, and `Value_footnote_refs` store comma-separated `Footnote_id` values; do not handwrite `①②③` into visible spec text
   - `symbols_blocks.csv` uses `Market`, `Model`, and `Source_lang`; it does not use `Region`; use `Market=Global` when one symbols row is shared across markets
   - `symbols_blocks.csv` uses `image_path` for the icon asset referenced by each symbols-table row; phase2 sync fills it from the Base `Figure` attachment when present
   - `symbols_blocks.csv` can also use `Is_Latest` and `Market` as row conditions: rows marked false are skipped, and `Market` must include the current build region such as `US` or `EU`
   - use `block_type=table_row` for the normal symbol/meaning grid; use `block_type=signal_row` for signal metadata, with rendered `symbol_key` values `warning`, `caution`, `note`, and `tips`, plus labels such as `danger` that Word/HTML rewrite should recognize
   - `order` values must be unique within each symbols table section; normal symbols rows are sorted and split evenly into two columns, so the old `column_group` field has been removed

## 6. How Safety and Spec Pages Work

Safety intro pages are now maintained as fixed RST templates and then materialized into the bundle.
The standalone user maintenance instructions page lives in shared templates and is included before the `symbols` page.

For FridgeGuard Web safety pages, EN/FR/ES reuse the same risk banner, warning lead, SVG icons and compact two-column styles. Keep each native source's wording. Desktop review must check aligned left edges and visible triangles; phone review must check that the stacked columns fill the content width. Maintain the shared [safety style contract](../../docs/renderers/contracts/STYLE_DEFINITION.md#1011-例外模板自带双分支的页安全页fcc), rather than adjusting each language separately.

Primary inputs:

- [`docs/templates/page_us-en/safety_en.rst`](../../docs/templates/page_us-en/safety_en.rst)
- [`docs/templates/page_us-fr/safety_fr.rst`](../../docs/templates/page_us-fr/safety_fr.rst)
- [`docs/templates/page_us-es/safety_es.rst`](../../docs/templates/page_us-es/safety_es.rst)
- [`docs/templates/page_shared/en/01_user_maintenance_instructions.rst`](../../docs/templates/page_shared/en/01_user_maintenance_instructions.rst)
- [`docs/templates/page_jp/safety_ja.rst`](../../docs/templates/page_jp/safety_ja.rst)

JP manual note:

- [`docs/manifests/manual_jp.yaml`](../../docs/manifests/manual_jp.yaml) includes [`docs/templates/page_jp/safety_ja.rst`](../../docs/templates/page_jp/safety_ja.rst) directly
- edit that template when the JP safety intro page must change
- the detailed JP warning content remains in [`docs/templates/page_jp/01_meaning_of_symbols.rst`](../../docs/templates/page_jp/01_meaning_of_symbols.rst)
- the old `content_blocks.csv` safety source has been removed from the active repo flow

Generated bundle output:

- materialized page include: [`docs/_build/<model>/<region>/rst/page/safety_<lang>.rst`](../../docs/_build)

Symbols content is generated from:

- [`data/phase2/page_registry.csv`](../../data/phase2/page_registry.csv)
- [`data/phase2/symbols_blocks.csv`](../../data/phase2/symbols_blocks.csv)

`symbols_blocks.csv` notes:

- use one `table_row` per symbols-table entry
- use `signal_row` entries for warning/caution/danger/note/tip signal structure; the signal token (`symbol_key`), target scope, order, and optional icon asset stay in `symbols_blocks.csv`. Visible signal labels and meanings are authored in `Manual_Copy_Source.csv`, translated through Translation Memory rows tagged `manual_copy`, and rendered from generated `Localized_Copy.csv`; legacy `label_*` and `aliases_*` columns are compatibility mirrors for old variants and rewrite detection only
- use `Market` and `Model` to target symbols rows; `symbols_blocks.csv` does not use `Region`
- use `Source_lang` for the row's source-language code, for example `en` or `ja`
- use `Market=Global` when one row should be shared across markets
- `image_path` stores the RST image reference path for that icon
- keep `symbol_key` stable so renderer alt text and layout metadata still resolve correctly; do not duplicate `copy_type=alt_text` rows in `Localized_Copy.csv`

Troubleshooting content is generated from:

- [`data/phase2/troubleshooting_blocks.csv`](../../data/phase2/troubleshooting_blocks.csv)
- [`docs/templates/**/10_troubleshooting.rst`](../../docs/templates/page_shared/en/10_troubleshooting.rst)

`troubleshooting_blocks.csv` notes:

- maintain the online TROUBLESHOOTING Base table, then run `python build.py sync-data --config configs/config.us.yaml --table troubleshooting --data-root data/phase2`
- use `Region`, `Model`, and `Is_latest` to select active rows; blank placeholder records are ignored
- keep page title, intro, table headers, widths, and header-row settings in each language's `10_troubleshooting.rst`
- keep error-code rows and corrective-measure copy in the TROUBLESHOOTING Base table; the RST template exposes `{{ troubleshooting_rows_rst }}` where those rows are inserted
- localized corrective text lives in per-language `corrective_measures_<lang>` columns; the current snapshot set is `corrective_measures_en/fr/es/pt-BR/br/de/it/ukr/jp/zh/ko`. A new output language adds its column in the Base table first, then reaches the snapshot through `sync-data`

Spec content is generated from:

- [`data/phase2/Spec_Master.csv`](../../data/phase2/Spec_Master.csv)
- optional [`data/phase2/Spec_Footnotes.csv`](../../data/phase2/Spec_Footnotes.csv)
- optional [`data/phase2/Spec_Notes.csv`](../../data/phase2/Spec_Notes.csv)
- optional [`data/phase2/spec_titles.csv`](../../data/phase2/spec_titles.csv)

Generated bundle output:

- [`docs/_build/<model>/<region>/rst/generated/<model>/spec_<lang>.rst`](../../docs/_build)
- materialized page include: [`docs/_build/<model>/<region>/rst/page/spec_<lang>.rst`](../../docs/_build)

[`Spec_Master.csv`](../../data/phase2/Spec_Master.csv) remains the build-time read model for spec sections, rows, and page-value placeholder records.
In Feishu, maintain those rows through `规格参数明细` and `页面占位参数`, then refresh the local snapshot with `sync-data --table spec_master` or a focused `spec-master-rebuild`.

---

## 7. Placeholder Rules

Core placeholders resolved from [`Spec_Master.csv`](../../data/phase2/Spec_Master.csv):

- `|PRODUCT_NAME|`
- `|PRODUCT_NAME_BOLD|`
- `|PRODUCT_SHORT_NAME|`
- `|PRODUCT_SHORT_NAME_BOLD|`
- `|MODEL_NO|`

Resolution source:

- `product_name` comes from `Row_key=product_name`
- `model_no` comes from `Row_key=model_no`
- `PRODUCT_SHORT_NAME` is derived from `PRODUCT_NAME`

`Spec_Master.csv` `Page` note:

- `Page` can be a comma-separated list
- use `Product overview` for Product overview-only page-value rows such as front/side-view callouts
- use `Product overview, specifications,` when the same row is intentionally shared by both pages
- `Row_label_source`, `Param_source`, and `Value_source` should store the row's source-manual text
- `Source_lang` should store the normalized source-language code for the row, such as `en`, `ja`, or `zh`; do not expect code to infer it from `Region`
- `document_key` should be either `[Model]_[Region]` or `[Model]_[Region]_[Source_lang]`
- `Row_order` is now the explicit row order inside each `document_key + Page + Section`; `Line_order` only controls the order of multiple lines inside one logical row
- `Line_order` is required; single-line rows use `1`
- generated `spec_titles.csv section_order` can hold the default order for visible spec sections, but a filled `Spec_Master.csv Section_order` overrides it
- `project_code` / `项目代码` is no longer used in `Spec_Master.csv`; choose rows by `Region` + `Model`
- when a build target is passed in document-key style such as `JE-1000F_JP` or `JE-1000F-JP`, the spec lookup normalizes it back to the base model `JE-1000F` and still uses the explicit `Region`, so a `JP` target continues to read `JP` rows
- source-language rows must keep their actual source text in `Row_label_source`, `Param_source`, and `Value_source`

For page-value rows, `Row_key` now keeps only the concept itself. Human editing should happen through `Slot_key`.

Examples:

- `Row_key=main_power_button`, `Slot_key=label` -> `|MAIN_POWER_BUTTON_LABEL|`
- `Row_key=ac_input`, `Slot_key=side.spec` -> `|SIDE_AC_INPUT_SPEC|`
- `Row_key=battery_pack_name`, `Slot_key=value` -> `|BATTERY_PACK_NAME|`

Derived behavior:

- non-empty placeholders also get `..._BOLD`
- placeholders ending in `_LABEL` also get `..._LOWER`
- multi-line page-value rows produce suffixed placeholders such as `|EXAMPLE_KEY_2|`
