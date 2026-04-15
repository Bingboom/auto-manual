---
name: markdown-rst-template-intake
description: Convert external Markdown manuals or Markdown-based instructions into this repo's reusable RST template layer. Use when Codex needs to map `.md` manual content into `docs/templates/page_*/*.rst`, preserve or introduce page-value placeholders, update `docs/templates/recipes/*/*.yaml` for placeholder-backed pages, or route spec and symbols content into `data/phase1` before review starts.
---

# Markdown RST Template Intake

Use this skill for first-time Markdown manual intake and shared template-family updates.
Do not use it for routine post-review wording edits inside `docs/_review/**` unless the user explicitly wants to change the shared seed layer.

## Default workflow

1. Read the incoming Markdown manual and fill `code-as-doc/dev/manual_template_intake_checklist.md`.
   Normalize the source first:
   - treat ATX headings, bold-only banners such as `**IMPORTANT**`, Markdown tables, and image-only rows as valid section signals
   - keep multilingual prefaces even when the target family is single-language if the repo family already publishes that way
2. Resolve the target family and current file surface:
   `python .agents/skills/markdown-rst-template-intake/scripts/template_surface.py --family <us-merged|us-en|us-es|us-fr|jp|zh> [--page <page-or-section>]`
3. Reuse the existing template boundaries unless the checklist explicitly allows a new page split.
4. Edit the shared authoring layer before review starts:
   - reusable prose/layout pages -> `docs/templates/page_*/...`
   - placeholder-backed pages -> template `.rst` plus any required recipe updates
   - generated spec/symbol content -> `data/phase1/*.csv`, not hand-authored RST
5. Validate with `python build.py check --config ... --model <MODEL> --region <REGION>`.
6. For changed placeholder pages, spot-check with `python build.py preview --config ... --model <MODEL> --region <REGION> --page <page-stem>`.

## Route content to the correct layer

- Edit `docs/templates/**` and `data/phase1/**` before review starts.
- Edit `docs/_review/<model>/<region>/**` after review starts when the request is target-local copy only.
- Never treat `docs/_build/**` as the authoring surface.
- Do not hand-edit `docs/index.rst` unless the task is explicitly about index generation.
- Keep the existing config family pattern. Do not create one config per model.
- When a family already uses `csv_page` for `spec` or `symbols`, keep those pages data-driven even if the Markdown source shows them as prose or tables.

## Route Markdown sections to repo surfaces

- Cover or introduction:
  route to the family preface or cover page from the manifest. Use `00_preface.rst` for most families and `cover_jp.rst` for JP.
- Safety:
  route to `safety_*.rst`. JP keeps the detailed warning-symbol page in `docs/templates/page_jp/01_meaning_of_symbols.rst`.
- Symbols:
  route to `data/phase1/symbols_blocks.csv` for CSV-backed families. For JP, keep detailed symbols content in `01_meaning_of_symbols.rst`.
- Specs:
  route to `data/phase1/Spec_Master.csv`, `Spec_Footnotes.csv`, and `Spec_Notes.csv`.
- Product overview, operation guide, app setup:
  treat `03_product_overview`, `05_operation_guide`, and `12_app_setup` as placeholder-backed pages. Preserve intentional `|PLACEHOLDER|` tokens and sync the matching recipe path when needed.
- LCD display:
  edit `04_lcd_display_placeholder.rst` directly. In the current repo it has placeholders but no dedicated recipe file.
- Static prose pages such as in-the-box, UPS, charging, charging methods, storage, troubleshooting, and warranty:
  edit the family page template directly.

## Handle placeholders deliberately

- Keep an existing placeholder when the value is model, region, or page driven.
- Add a new placeholder only when the content should resolve from structured page-value data instead of static prose.
- For `03_product_overview`, `05_operation_guide`, and `12_app_setup`, update the matching recipe file when a new placeholder requires a row-key mapping or required-row assertion.
- Check the matching contract under `docs/templates/contracts/` before removing or renaming a required placeholder.
- Do not replace generated spec or symbols tables with copied Markdown prose.
- If an inherited recipe-backed page needs family-specific body copy but the contract still requires legacy placeholders, preserve those required placeholders inside a non-rendering RST comment and keep the rendered body literal. Do not edit `data/phase2/**` unless the user explicitly asks for shared page-value data changes.

## Keep parallel-language families aligned

- Treat the source-language page as the structure owner for manually maintained parallel-language templates.
- For US merged work, use `docs/templates/page_us-en/` as the structure owner and keep `page_us-fr/` plus `page_us-es/` aligned in the same change when headings, order, includes, gates, or placeholder layout change.
- Preserve source-only sections outside derived templates when the checklist says they should stay source-only.

## Validate with repo commands

- Logic changes:
  `python -m unittest`
- Shared template or data changes:
  `python build.py check --config <config> --model <MODEL> --region <REGION>`
- Page-level placeholder spot check:
  `python build.py preview --config <config> --model <MODEL> --region <REGION> --page <page-stem>`
- If the default `python` environment is missing repo dependencies, use the repo virtualenv instead:
  `.\.venv\Scripts\python.exe build.py check --config <config> --model <MODEL> --region <REGION>`
- If the task changes release-traceability behavior, diff reporting, or JP publish flow, use the repo-specific minimum commands from `AGENTS.md`.

## Success criteria

- For intake benchmarking, match the repo family's section boundaries, routed surfaces, and semantic coverage.
- Do not require byte-for-byte identity with the incoming Markdown or existing generated Word output when the repo intentionally normalizes copy through renderers, CSV pages, or shared templates.

## Use bundled resources

- Read `references/repo-routing.md` when you need the family map, section routing, or validation command matrix.
- Run `scripts/template_surface.py` when you need the exact template, recipe, contract, and manifest paths for a family or page.
