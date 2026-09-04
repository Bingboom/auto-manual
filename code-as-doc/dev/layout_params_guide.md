# Layout Params Guide

Updated: 2026-09-04

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

## 3. Inheritance and Override

This repo is built on inheritance and override, and the layout plane follows the
same rule as the config plane. Read this section before adding any parameter.

[`data/layout_params.csv`](../../data/layout_params.csv) is the **common** style
definition. Every target resolves all of its keys — both product categories, all
languages — and the paragraph style table renders identically for every
`(target, language)` pair. Keep it that way: the common is the thing being
reused.

A target-bound overlay is a **layer above** the common. Binding it in the config
(`paths.idml_layout_params_overlays_by_target`) is the inheritance declaration —
it is this plane's `from common import *` — and after that a key the overlay
defines simply **wins**. There is no per-row ceremony, for the same reason
`config.eu-de.yaml` does not annotate a key before redefining what
`eu-single-language-base.yaml` set.

The config plane to copy the shape from:

```
config.eu-de.yaml  ->  eu-single-language-base.yaml  ->  us-single-language-base.yaml
```

Each hop deep-merges and the later definition wins
([`tools/config_loader.py`](../../tools/config_loader.py)).

### 3.1 Express a difference as a layer, never as a key name

The layers, and what belongs in each:

| Layer | Scope | Example |
| --- | --- | --- |
| common | everything shared | `type_body_font_size` |
| category | one product line | a battery-pack panel height |
| target | one `(model, region)` | a Korean column width |
| language | font and text fitting only | `lang_de_type_spec_label_font_size` |

**Do not encode the layer into the key name.** A key such as
`idml_compact_safety_list_leading` or `lang_ko_idml_key_panel_height` is the
layer wearing a disguise: the first is the category layer as an infix, the second
is the target layer wearing a language prefix while changing geometry rather than
any font metric. Overriding used to be banned, so this was the only way to
differ; it no longer is. 46 keys across the two live overlays are still shaped
that way and are being migrated.

A per-language row is legitimate **only** as font or text fitting — size,
leading, horizontal scale, hyphenation — where a language's text genuinely does
not fit the shared value. It is not the place for a panel height.

### 3.2 Overriding is visible, not forbidden

`resolve_layout_token_layers` returns every common value a layer replaced, with
the value it replaced. [`tests/test_layout_token_override.py`](../../tests/test_layout_token_override.py)
pins that set, so adding an override means writing it down and it shows up in
review — the same ratchet shape this repo uses for SKIP counts, warnings, file
sizes and language literals. Update the pin deliberately, never to make a build
pass.

## 4. Current Parameter Families

Common prefixes:

- `page_`: page-level layout
- `type_`: typography
- `comp_`: component spacing and structure
- `brand_color_`: color values
- `lang_<code>_`: language fitting, per §3.1

Current allowed unit categories are validated by [`tools/validate_layout_params.py`](../../tools/validate_layout_params.py).

## 5. Recommended Workflow

### 5.1 Edit the CSV

Update:

- [`data/layout_params.csv`](../../data/layout_params.csv)

### 5.2 Validate

```powershell
python tools\validate_layout_params.py --csv data\layout_params.csv
```

or:

```powershell
python build.py validate --config configs/config.us.yaml
```

### 5.3 Regenerate and Build PDF

```powershell
python build.py pdf --config configs/config.us.yaml --model JE-1000F --region US
```

If JP is the affected family:

```powershell
python build.py pdf --config configs/config.ja.yaml --model JE-1000F --region JP
```

### 5.4 Compare Results

At minimum, compare:

- one safety-heavy page
- one spec-heavy page
- one long-page case prone to overflow

## 6. Practical Tuning Order

When layout looks wrong, tune in this order:

1. page frame and margins
2. type density
3. component spacing
4. spec table density
5. language-specific overrides

This is usually more stable than immediately patching component `.tex` files.

## 7. Common Cases

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

## 8. When to Touch `.tex`

Only touch `.tex` component files when:

- the behavior is not parameterized yet
- the styling change is structural, not just numeric
- the team agrees the change should become a new stable component rule

If you patch `.tex` and the rule should be reusable, consider parameterizing it afterward.

## 9. Record Keeping

Every meaningful [`layout_params.csv`](../../data/layout_params.csv) tuning round should produce a small change record using:

- [`code-as-doc/dev/layout_params_change_log_template.md`](layout_params_change_log_template.md)

That record should capture:

- parameter names
- old value
- new value
- target pages
- verification command
- rollback note

