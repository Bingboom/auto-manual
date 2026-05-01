# Title Style Guide

Updated: 2026-05-01

This file explains where headings and document titles come from in the current HTML, Word, and PDF flows.

## 1. Current Principle

Heading semantics must come from content structure, not from ad hoc hard-coded title text checks.

That means:

- page structure lives in RST templates
- spec section title localization lives in [`data/phase1/spec_titles.csv`](../data/phase1/spec_titles.csv)
- visual style lives in CSS, LaTeX components, or the shared Word DOCX style remapper
- Word document title comes from config plus placeholder substitution

## 2. Current Source Matrix

### 2.1 Template Semantics

Shared page templates:

- [`docs/templates/page_us-en/*.rst`](../docs/templates/page_us-en)
- [`docs/templates/page_jp/*.rst`](../docs/templates/page_jp)

These files define normal page heading structure and placeholder-bearing page text.

### 2.2 Spec Title Localization

- [`data/phase1/spec_titles.csv`](../data/phase1/spec_titles.csv)

Use this file for spec section title mapping across languages.

### 2.3 HTML Style

- [`docs/_static/hb_manual.css`](../docs/_static/hb_manual.css)

This controls shared HTML presentation for headings and title-like components.

### 2.4 PDF / LaTeX Style

Main files:

- [`docs/renderers/latex/components_base.tex`](../docs/renderers/latex/components_base.tex)
- [`docs/renderers/latex/components_spec.tex`](../docs/renderers/latex/components_spec.tex)
- [`docs/renderers/latex/components_safety.tex`](../docs/renderers/latex/components_safety.tex)
- [`docs/renderers/latex/params.tex`](../docs/renderers/latex/params.tex) generated from [`data/layout_params.csv`](../data/layout_params.csv)

[`layout_params.csv`](../data/layout_params.csv) is the editable source.
Do not hand-edit [`params.tex`](../docs/renderers/latex/params.tex).

### 2.5 Word Title

Current Word title comes from config:

- `build.word_title`

Current examples:

- [`config.us.yaml`](../config.us.yaml): `|PRODUCT_NAME| User Manual`
- [`config.ja.yaml`](../config.ja.yaml): `|PRODUCT_NAME| 取扱説明書`

This title is resolved by placeholder substitution before Word export.

Word heading appearance is normalized after export by
[`tools/word_bundle_docx.py`](../tools/word_bundle_docx.py). The remapper updates the shared reference heading styles
instead of hard-coding page text:

- `dingding-heading1`: Word level-1 title style with black text, no copied PDF title block
- `dingding-heading2`: bold level-2 title with a solid-dot visual marker, without Word numbering
- `dingding-heading3` / `Heading3`: smaller solid-dot local title when the style exists

## 3. Current Rules

### 3.1 Shared Structure Change

If the heading hierarchy should change for many manuals:

- edit the template under [`docs/templates/page_*/*.rst`](../docs/templates)
- update CSS or LaTeX if the visual design also changes

### 3.2 Target-Specific Review Wording

If the change is only for one manual already in review:

- edit [`docs/_review/<model>/<region>/page/*.rst`](../docs/_review)

Do not edit shared templates for one-off target review wording.

### 3.3 Spec Section Text

If the change is specifically a localized spec title:

- edit [`data/phase1/spec_titles.csv`](../data/phase1/spec_titles.csv)

### 3.4 Do Not Encode Semantics in Exporter Text Matching

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
python build.py check --config config.us.yaml --model JE-1000F --region US
python build.py word --config config.us.yaml --model JE-1000F --region US
python build.py check --config config.ja.yaml --model JE-1000F --region JP
python build.py word --config config.ja.yaml --model JE-1000F --region JP
```

If the change is spec-title-specific, also validate that the relevant section titles render as expected after `phase1` generation.

## 6. Typical Change Routing

Change the visual gap or typography of headings:

- [`data/layout_params.csv`](../data/layout_params.csv)
- [`docs/renderers/latex/components_*.tex`](../docs/renderers/latex)
- [`docs/_static/hb_manual.css`](../docs/_static/hb_manual.css)
- [`tools/word_bundle_html.py`](../tools/word_bundle_html.py) if needed for Word bundle CSS

Change the actual heading text:

- [`docs/templates/page_*/*.rst`](../docs/templates)
- [`data/phase1/spec_titles.csv`](../data/phase1/spec_titles.csv)
- [`data/phase1/Spec_Master.csv`](../data/phase1/Spec_Master.csv) for data-driven placeholder content

Change the document title shown in Word:

- [`config.us.yaml`](../config.us.yaml) or [`config.ja.yaml`](../config.ja.yaml)
- usually via `build.word_title`

## 7. Common Mistakes

- documenting `page_ja` instead of `page_jp`
- changing only Word appearance while leaving HTML and PDF inconsistent
- hard-coding title-level decisions in exporter code based on literal text
- editing [`params.tex`](../docs/renderers/latex/params.tex) instead of [`data/layout_params.csv`](../data/layout_params.csv)

