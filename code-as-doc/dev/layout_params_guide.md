# Layout Params Guide

Updated: 2026-03-12

This file explains how [`data/layout_params.csv`](../../data/layout_params.csv) is used today.

## 1. What [`layout_params.csv`](../../data/layout_params.csv) Controls

Current primary scope:

- LaTeX / PDF layout tuning

Current chain:

```text
data/layout_params.csv
-> tools/validate_layout_params.py
-> tools/csv_to_tex_params.py
-> docs/renderers/latex/params.tex
-> docs/renderers/latex/*.tex
-> PDF build
```

Editable source:

- [`data/layout_params.csv`](../../data/layout_params.csv)

Generated file:

- [`docs/renderers/latex/params.tex`](../../docs/renderers/latex/params.tex)

Do not hand-edit [`params.tex`](../../docs/renderers/latex/params.tex).

## 2. What It Does Not Control

Current bundle-based Word export is not driven primarily by [`layout_params.csv`](../../data/layout_params.csv).
Word and HTML title styling also depend on:

- RST template structure
- [`docs/_static/hb_manual.css`](../../docs/_static/hb_manual.css)
- [`tools/word_bundle_html.py`](../../tools/word_bundle_html.py)

So if you change a PDF layout parameter and Word does not move with it, that is usually expected.

## 3. Current Parameter Families

Common prefixes:

- `page_`: page-level layout
- `type_`: typography
- `comp_`: component spacing and structure
- `brand_color_`: color values
- `lang_fr_` / `lang_es_`: language-specific overrides where supported

Current allowed unit categories are validated by [`tools/validate_layout_params.py`](../../tools/validate_layout_params.py).

## 4. Recommended Workflow

### 4.1 Edit the CSV

Update:

- [`data/layout_params.csv`](../../data/layout_params.csv)

### 4.2 Validate

```powershell
python tools\validate_layout_params.py --csv data\layout_params.csv
```

or:

```powershell
python build.py validate --config configs/config.us.yaml
```

### 4.3 Regenerate and Build PDF

```powershell
python build.py pdf --config configs/config.us.yaml --model JE-1000F --region US
```

If JP is the affected family:

```powershell
python build.py pdf --config configs/config.ja.yaml --model JE-1000F --region JP
```

### 4.4 Compare Results

At minimum, compare:

- one safety-heavy page
- one spec-heavy page
- one long-page case prone to overflow

## 5. Practical Tuning Order

When layout looks wrong, tune in this order:

1. page frame and margins
2. type density
3. component spacing
4. spec table density
5. language-specific overrides

This is usually more stable than immediately patching component `.tex` files.

## 6. Common Cases

Spec section gap too large or too small:

- start with `comp_spec_section_before`
- then `comp_spec_section_after`

Spec table too tall:

- start with `comp_spec_table_row_stretch`
- then review `type_spec_*`
- then `comp_spec_table_tabcolsep`

List bullets visually off:

- review bullet symbol and raise-related keys

FR / ES text more likely to overflow:

- prefer `lang_fr_*` or `lang_es_*` density tuning before changing the shared base values

## 7. When to Touch `.tex`

Only touch `.tex` component files when:

- the behavior is not parameterized yet
- the styling change is structural, not just numeric
- the team agrees the change should become a new stable component rule

If you patch `.tex` and the rule should be reusable, consider parameterizing it afterward.

## 8. Record Keeping

Every meaningful [`layout_params.csv`](../../data/layout_params.csv) tuning round should produce a small change record using:

- [`code-as-doc/dev/layout_params_change_log_template.md`](layout_params_change_log_template.md)

That record should capture:

- parameter names
- old value
- new value
- target pages
- verification command
- rollback note

