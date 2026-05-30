# Title Style Guide

Updated: 2026-05-01

This file explains where headings and document titles come from in the current HTML, Word, and PDF flows.

## 1. Current Principle

Heading semantics must come from content structure, not from ad hoc hard-coded title text checks.

That means:

- page structure lives in RST templates
- spec section title localization lives in [`data/phase2/spec_titles.csv`](../data/phase2/spec_titles.csv)
- reusable short copy such as CSV-page titles, table headers, alt text, state words, and Product overview labels lives in [`data/phase2/Localized_Copy.csv`](../data/phase2/Localized_Copy.csv)
- visual style lives in CSS, LaTeX components, or the shared Word DOCX style remapper
- Word document title comes from config plus placeholder substitution

## 2. Current Source Matrix

### 2.1 Template Semantics

Shared page templates:

- [`docs/templates/page_us-en/*.rst`](../docs/templates/page_us-en)
- [`docs/templates/page_jp/*.rst`](../docs/templates/page_jp)

These files define normal page heading structure and placeholder-bearing page text.

### 2.2 Spec Title Localization

- [`data/phase2/spec_titles.csv`](../data/phase2/spec_titles.csv)

Use this file for spec section title mapping across languages.

### 2.3 Short Copy Localization

- [`data/phase2/Localized_Copy.csv`](../data/phase2/Localized_Copy.csv)

Use this file for reusable short text that should be translated and maintained with the phase2 content source, including LCD / Symbols page titles, table headers, state words, alt text, and Product overview labels. RST templates can reference this table with `{{ copy:<copy_key> }}`; missing copy is a build/check error. Symbols signal-word rows stay in `symbols_blocks.csv`.

### 2.4 HTML Style

- [`docs/_static/hb_manual.css`](../docs/_static/hb_manual.css)

This controls shared HTML presentation for headings and title-like components.

### 2.5 PDF / LaTeX Style

Main files:

- [`docs/renderers/latex/components_base.tex`](../docs/renderers/latex/components_base.tex)
- [`docs/renderers/latex/components_spec.tex`](../docs/renderers/latex/components_spec.tex)
- [`docs/renderers/latex/components_safety.tex`](../docs/renderers/latex/components_safety.tex)
- [`docs/renderers/latex/params.tex`](../docs/renderers/latex/params.tex) generated from [`data/layout_params.csv`](../data/layout_params.csv)

[`layout_params.csv`](../data/layout_params.csv) is the editable source.
Do not hand-edit [`params.tex`](../docs/renderers/latex/params.tex).

### 2.6 Word Title

Current Word title comes from config:

- `build.word_title`

Current examples:

- [`configs/config.us.yaml`](../configs/config.us.yaml): `|PRODUCT_NAME| User Manual`
- [`configs/config.ja.yaml`](../configs/config.ja.yaml): `|PRODUCT_NAME| 取扱説明書`

This title is resolved by placeholder substitution before Word export.

Word heading appearance is normalized after export by
[`tools/word_bundle_docx_styles.py`](../tools/word_bundle_docx_styles.py), called from
[`tools/word_bundle_docx.py`](../tools/word_bundle_docx.py). The remapper updates the shared reference heading styles
instead of hard-coding page text:

- `dingding-heading1`: Word level-1 title style with black text, no copied PDF title block
- `dingding-heading2`: bold level-2 title with a solid-dot visual marker, without Word numbering
- `dingding-heading3` / `Heading3`: smaller solid-dot local title when the style exists

## 3. Current Rules

### 3.1 Structural Title Scale

Manual output uses one three-level title scale across HTML and PDF:

- level 1: page/major section titles, rendered as a dark full-width title bar
- level 2: RST subsections, product overview panel titles, generated spec section titles, and subbar-style section breaks, rendered as a large solid-dot heading
- level 3: RST subsubsections and lower local headings, rendered as a smaller solid-dot heading

PDF/LaTeX entrypoints:

- `\section` -> `\HBTitleLevelOne`
- `\subsection`, `\HBOverviewPanel`, `\specsectiontitle`, `\safetysubbar` -> `\HBTitleLevelTwo`
- `\subsubsection` -> `\HBTitleLevelThree`

The runtime bundle index adds a LaTeX-only document root title with an overline/underline RST style before page includes.
That hidden root title seeds Sphinx's title hierarchy so templates can keep natural page-local RST:
`=` for page/major titles, `-` for level 2, and the next local adornment for level 3.
Do not add manual hierarchy seed headings to page templates.

Generated app setup pages opt into a recipe postprocess step,
`promote_standalone_bold_numbered_headings`, to promote standalone bold numbered step labels to structural headings during draft generation:
`**1. ...**` becomes level 2, and dotted substeps such as `**4.1 ...**` become level 3.
Keep those labels easy to maintain in the source template; the recipe owns whether this semantic promotion runs.

Product overview pages are authored directly as plain RST list-tables in each language's `page_<lang>/03_product_overview_placeholder.rst` template: layout, image placement, and table structure stay in RST, short labels resolve from `Localized_Copy.csv` through `{{ copy:<copy_key> }}`, and spec values remain `|TOKEN|` substitutions resolved from Spec_Master. There is no overview-layout renderer or `{{ product_overview }}` marker; edit the per-language template to change the overview's structure, and edit `Localized_Copy.csv` to change shared labels.

HTML entrypoints:

- `h1` and `.hb-h1-pill` -> level 1
- plain `h2`, `.hb-subbar`, and `.hb-spec-section` -> level 2
- `h3` -> level 3

The editable LaTeX parameters for this scale live in [`data/layout_params.csv`](../data/layout_params.csv) under `type_title_l2*`, `type_title_l3*`, `comp_title_l2*`, and `comp_title_l3*`.

Word entrypoints:

- structural Heading 1 / `dingding-heading1` -> level 1
- structural Heading 2 / `dingding-heading2` -> level 2
- structural Heading 3 / `dingding-heading3` or `Heading3` -> level 3

### 3.2 Shared Structure Change

If the heading hierarchy should change for many manuals:

- edit the template under [`docs/templates/page_*/*.rst`](../docs/templates)
- update CSS or LaTeX if the visual design also changes

### 3.3 Target-Specific Review Wording

If the change is only for one manual already in review:

- edit [`docs/_review/<model>/<region>/page/*.rst`](../docs/_review)

Do not edit shared templates for one-off target review wording.

### 3.4 Spec Section Text

If the change is specifically a localized spec title:

- edit [`data/phase2/spec_titles.csv`](../data/phase2/spec_titles.csv)

### 3.5 Do Not Encode Semantics in Exporter Text Matching

Avoid logic such as:

- if the title text equals some phrase, force a heading level

Semantics should come from the content structure and renderer pipeline, not from literal text matching.

## 4. Current JP Rule

The active JP template directory is:

- [`docs/templates/page_jp/`](../docs/templates/page_jp)

Do not use `page_ja` in new documentation or commands.

## 5. Validation Path

If you changed title behavior, verify at least one target from the affected family.

Examples:

```powershell
python build.py check --config configs/config.us.yaml --model JE-1000F --region US
python build.py word --config configs/config.us.yaml --model JE-1000F --region US
python build.py check --config configs/config.ja.yaml --model JE-1000F --region JP
python build.py word --config configs/config.ja.yaml --model JE-1000F --region JP
```

If the change is spec-title-specific, also validate that the relevant section titles render as expected after CSV page generation from `data/phase2`.

## 6. Typical Change Routing

Change the visual gap or typography of headings:

- [`data/layout_params.csv`](../data/layout_params.csv)
- [`docs/renderers/latex/components_*.tex`](../docs/renderers/latex)
- [`docs/_static/hb_manual.css`](../docs/_static/hb_manual.css)
- [`tools/word_bundle_html.py`](../tools/word_bundle_html.py) if needed for Word bundle CSS

Change the actual heading text:

- [`data/phase2/Localized_Copy.csv`](../data/phase2/Localized_Copy.csv) for shared short copy used by `{{ copy:<copy_key> }}`
- [`docs/templates/page_*/*.rst`](../docs/templates) for stable template prose and page structure
- [`data/phase2/spec_titles.csv`](../data/phase2/spec_titles.csv)
- [`data/phase2/Spec_Master.csv`](../data/phase2/Spec_Master.csv) for data-driven placeholder content

Change the document title shown in Word:

- [`configs/config.us.yaml`](../configs/config.us.yaml) or [`configs/config.ja.yaml`](../configs/config.ja.yaml)
- usually via `build.word_title`

## 7. Common Mistakes

- documenting `page_ja` instead of `page_jp`
- changing only Word appearance while leaving HTML and PDF inconsistent
- hard-coding title-level decisions in exporter code based on literal text
- editing [`params.tex`](../docs/renderers/latex/params.tex) instead of [`data/layout_params.csv`](../data/layout_params.csv)
