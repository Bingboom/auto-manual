# IDML Dual Mode Discovery Report

Run id: `20260707-095256`
Branch: `docs/idml-dual-mode-plan`
Base commit: `3c27e7c805a556504661105639729c6f04b3e92f`
Date: `2026-07-07`

## Scope

This report covers Phase 0 only. No exporter behavior has been changed. The goal is to understand the current production IDML path and define how to add `production` and `flow` modes without creating a second content source.

Files inspected:

- `tools/export_idml.py`
- `tools/idml_rst_extract.py`
- `tools/idml/**`
- `tools/build_cli.py`
- `tools/build_dispatch.py`
- `tools/markdown_bundle.py`
- `tests/test_export_idml.py`
- `tests/test_export_idml_cli.py`
- `tests/test_export_idml_golden.py`
- `tests/test_idml_components.py`
- `tests/test_build_dispatch.py`
- `data/layout_params.csv`
- `code-as-doc/dev/idml_module_map.md`

## 1. Current production IDML capability

The current `idml` action is production-oriented. `tools/build_dispatch.py` runs an RST prepare first, then invokes `tools/export_idml.py`. `tools/export_idml.py` builds an editable IDML package with:

- Prepared RST bundle extraction from `docs/_build/<model>/<region>/<lang>/rst` or `docs/_build/<model>/<region>/rst`.
- Structured phase2 data loading for specifications, LCD icons, troubleshooting, and symbols.
- Real IDML tables for specifications, symbols, troubleshooting, list tables, and component tables.
- Linked image references for prose images, LCD figures, and symbol assets.
- Production components for `inbox`, `warnbox`, `notice`, `fcc`, `lcdmode`, `safetywarning`, and `warninglead`.
- Special production page composers for safety, safety plus symbols, and FCC plus inbox pages.
- Adjacent ordinary prose pages buffered into one linked story until a hard layout boundary.
- Structural self-check through `tools/idml/check.py`.

The current default output path remains:

```text
docs/_build/<model>/<region>/idml/manual_<modelslug>_<regionslug>.idml
```

or, for language-specific bundles:

```text
docs/_build/<model>/<region>/<lang>/idml/manual_<modelslug>_<regionslug>_<lang>.idml
```

Important boundary: the existing `ProseFlowBuffer` is not the requested flow-idml mode. It only links adjacent ordinary prose pages inside the production exporter. It still preserves production components and hard composed pages.

## 2. Reusable logic in the current exporter

Reusable for both modes:

- `tools/idml_rst_extract.py`
  - `bundle_page_order()` gives prepared bundle reading order.
  - `extract_page()` already emits a block stream with `h1`, `h2`, `h3`, `body`, `list`, `image`, `table`, `component`, and `layout`.
  - Raw LaTeX component macros are converted into JSON component specs.
  - RST grid tables and list tables are parsed into structured rows.
  - Localized notice labels are already recognized through `tools/idml/notice_labels.py`.

- `tools/idml/loaders.py`
  - Loads phase2 structured data used by production pages.
  - Provides localization fallback for `en`, `fr`, and `es`.
  - Preserves asset paths for LCD and symbol rows.

- `tools/idml/components/`
  - The component registry maps semantic component kinds to production renderers.
  - Component specs are already stable enough to become the shared AST representation for flow degradation.

- `tools/idml/style_names.py`
  - Current production style-name mapping proves the exporter can separate semantic style intent from designer-template style names.
  - Flow mode should use a separate, config-backed style map instead of changing this production map.

- `tools/idml/package.py`, `tools/idml/styles.py`, `tools/idml/stories.py`, and `tools/idml/check.py`
  - Can be reused for a simple flow-idml package once flow rendering avoids production components.

Production-only logic that should not be reused directly for flow:

- Safety page split/composition in `tools/idml/pages.py`.
- FCC plus inbox composed page merge.
- Safety plus symbols composed page merge.
- Production component table renderers for warning boxes, notices, inbox, and FCC panels.
- Data-page story builders that optimize for production-style tables rather than continuous editing.

## 3. Existing Markdown output

The repo already has Markdown-related output, especially `tools/markdown_bundle.py`. That path builds a Word HTML bundle, then uses pandoc to convert it to MyST/CommonMark/GFM-style Markdown. It is useful for publish, cloud-doc import, and readable manual artifacts.

It is not sufficient as `manual.flow.md` because it:

- Is derived after Word/HTML rendering, not from the manual block model.
- Does not preserve component type, asset id, row/source reference, or flow conversion notes.
- Cannot reliably distinguish semantic components from already-rendered layout HTML.
- Is optimized for document publishing rather than InDesign template intake.

Conclusion: existing Markdown code can provide escaping and output scaffolding ideas, but `manual.flow.md` should be generated from the prepared RST block stream plus structured data loaders.

## 4. CLI changes needed for `idml-mode`

Current state:

- `tools/build_cli.py` registers the `idml` action but has no `--idml-mode`.
- `tools/build_dispatch.py` invokes `tools/export_idml.py` without mode arguments.
- `tools/export_idml.py` has no `--mode` or `--idml-mode`.
- `tools/export_idml.py --check <file.idml>` validates an existing IDML and exits.

Recommended CLI extension:

```bash
python build.py idml --idml-mode production
python build.py idml --idml-mode flow
python build.py idml --idml-mode both
```

and direct exporter support:

```bash
python tools/export_idml.py --mode production
python tools/export_idml.py --mode flow
python tools/export_idml.py --mode both
```

Compatibility requirement:

```bash
python build.py idml
```

must remain equivalent to:

```bash
python build.py idml --idml-mode production
```

Implementation detail:

- Add `--idml-mode` to `tools/build_cli.py` with choices `production`, `flow`, `both`, default `production`.
- Pass it through in `_dispatch_idml_action()`.
- Add `--mode` and optional alias `--idml-mode` to `tools/export_idml.py`.
- Keep `--check` independent from mode.

## 5. Flow-md source model

Flow-md should be generated from the prepared RST bundle through a formalized Manual Block AST, not from generic Markdown output.

Reason:

- Prepared RST has already resolved target-specific template/data materialization.
- `idml_rst_extract.extract_page()` already preserves reading order and component boundaries.
- The block stream is close to the required Manual Block AST.
- The same block stream can feed production, flow-md, and flow-idml without splitting content sources.

Recommended first step:

- Keep the existing tuple block stream as input.
- Add a small enriched model around it for flow outputs:

```text
ManualBlock
  kind
  text_or_payload
  page_id
  source_ref
  asset_refs
  component_type
  language
```

Phase 2 can begin with page-level `source_ref` if row-level trace is not yet available, then tighten to source-table row keys where loaders already know the source.

## 6. Design-side template inputs still needed

The repo has `docs/templates/idml_template/manual.idml` and a template style-name mapping area has been mentioned, but the flow intake contract still needs confirmation from design.

Questions for design:

1. Markdown dialect: CommonMark, GFM, MyST, or Pandoc Markdown?
2. Heading style names: exact InDesign paragraph style names for H1, H2, H3.
3. Body/list style names: exact style names for paragraph, bullet list, numbered list, caption.
4. Admonition syntax: `::: warning`, blockquote, or plain heading plus paragraph?
5. Table format: Markdown pipe table, CSV sidecar, or simplified IDML table?
6. Image format: Markdown image link, `[FIGURE: asset_id]`, or both?
7. Whether the template accepts YAML front matter.
8. Whether localized style names differ for `fr` and `es`.

Default proposed `flow_style_map.json`:

```json
{
  "h1": "Manual H1",
  "h2": "Manual H2",
  "h3": "Manual H3",
  "paragraph": "Body",
  "list": "Bullet List",
  "table": "Simple Table",
  "warning": "Warning Paragraph",
  "note": "Note Paragraph",
  "caption": "Figure Caption"
}
```

## 7. Existing test coverage and gaps

Existing coverage is strong for production-idml:

- IDML package structure and self-check.
- Golden byte comparison for production output.
- Component registry parity.
- Component table rendering for inbox, notice, warning, safety, FCC, and LCD mode.
- Real image links and linked asset references.
- Localized notice-list-table detection.
- Localized safety plus symbols composition.
- FCC plus inbox composed page.
- List-table and grid-table parsing.
- DOMVersion, span columns, glyph fallback, and direct-current symbol behavior.
- No trailing blank pages in current production story estimates.
- `build.py idml` dispatch prepares RST before export.

New tests needed:

- `build.py idml` default still invokes production mode.
- `build.py idml --idml-mode production` keeps current output path and behavior.
- `build.py idml --idml-mode flow` invokes flow output generation after RST prepare.
- `build.py idml --idml-mode both` invokes both production and flow outputs.
- Direct `tools/export_idml.py --mode production|flow|both`.
- `manual.flow.md` front matter exists and contains model, region, language, version if available, and mode.
- Flow-md preserves page order.
- Flow-md degrades `warnbox`, `notice`, `fcc`, `inbox`, `lcdmode`, symbols, and spec tables into semantic Markdown.
- Flow-md writes `source_ref` comments for key blocks.
- Flow-md writes `asset_ref` or `[FIGURE: ...]` for images.
- Flow mode writes `source_trace.json`, `asset_manifest.csv`, `flow_style_map.json`, and `flow_conversion_notes.md`.
- Production golden output is unchanged when no flow mode is requested.

## Discovery conclusion

The current exporter is a viable production-idml renderer and should remain the default. The safest route is to add a second flow renderer beside it, using the existing prepared RST extraction and data loaders as the shared content source. The existing Markdown exporter should not be used as the flow source because it has already lost the component and trace semantics that flow-md must preserve.
