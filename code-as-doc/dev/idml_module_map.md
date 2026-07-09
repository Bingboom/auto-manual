# IDML Exporter Module Map

Result of the componentization plan (`reports/idml_componentization/20260705-01`,
P0–P4, 2026-07-05). The exporter went from a 2001-line single file to a layered
package with the emitted `.idml` **bit-identical** throughout (enforced by a
golden byte-comparison test at every phase).

## Layers (imports point downward only)

```
tools/export_idml.py          façade + CLI: main()'s page-composition state machine,
                              IdmlWriter (state: params/geometry + stories/spreads sinks;
                              every method is a thin delegate), full re-export surface
tools/idml/
  design_handoff.py          Phase 5 package writer: production copy, source
                              trace, missing-assets report, checklist, feedback
  export_paths.py             shared production / flow output path helpers
  flow_idml.py                flow-idml Phase 3 continuous-story IDML writer:
                              manual.flow.idml + flow_style_map.json
  flow_md.py                  flow-idml Phase 2 semantic Markdown artifacts:
                              manual.flow.md + trace + asset manifest + notes
  pages.py                    composed-page assemblers: safety page, safety+symbols
                              merge, fcc+inbox merge + frame helpers; declares
                              heading levels and frame geometry, not corner shapes
  page_objects.py             spread-level visual objects for composed pages:
                              H1/H2 heading object-style opts and independent
                              rounded table/callout outline rectangles
  prose_flow.py               ordinary-page flow buffering: adjacent prose pages share
                              one linked story until a hard layout boundary
  fcc_fallback.py             localized FCC prose -> fcc component fallback when the
                              source page has no explicit HBFccBlock
  notice_labels.py            localized NOTE/TIP/CAUTION/WARNING/DANGER label mapping
                              for notice-style list-table extraction
  stories.py                  story builders: prose (block-stream dispatch), lcd, symbols,
                              trouble, spec, text
  package.py                  zip contract (mimetype first + STORED), designmap wiring,
                              linked spread chain, height estimation
  components/                 the component registry — REGISTRY: kind -> renderer
    base.py                   RenderContext (geometry/params/asset roots; the seam for a
                              future Design_Asset_Registry) + shared figure paragraph
    callout.py                safetywarning / warninglead / tailwarnbox / warnbox / notice
    inbox.py fcc.py lcdmode.py
    prose_table.py            the extractor's ("table", json) block
    prose_image.py            the extractor's ("image", ref) block
  primitives.py               XML building blocks: psr/<Br/> semantics, bold runs, glyph
                              fallbacks, cells, tables, image frames, path geometry
  table_borders.py            table XML border helpers: table perimeter suppression
                              when a separate rounded outline object owns the border
  styles.py                   resource parts: paragraph styles/colors/fonts/preferences
  style_names.py              internal HB semantic style -> designer-template paragraph
                              style names, so exported stories can inherit the template
  loaders.py                  phase2 CSV -> rows (incl. SYMBOL_COPY l10n)
  params.py                   shared constants + layout_params.csv access
  check.py                    structural .idml validation (also the post-write self-check)
tools/idml_rst_extract.py     prepared-bundle RST -> block stream; owns component spec
                              shapes and EMITTED_COMPONENT_KINDS (registry parity is
                              test-enforced)
tools/idml_rst_tables.py      prepared-bundle RST table parsing helpers used by the
                              extractor
```

## Contracts to know before touching anything

- **Golden**: `tests/test_export_idml_golden.py` byte-compares every package part
  against `tests/fixtures/idml_golden/` (data-only + composed-bundle variants,
  URIs normalized). A diff means behavior changed — regenerate only for a
  deliberate, reviewed output change (`--regenerate`).
- **Registry parity**: every kind in `idml_rst_extract.EMITTED_COMPONENT_KINDS`
  must have a renderer in `tools/idml/components.REGISTRY`
  (`tests/test_idml_components.py`). `tailwarnbox` is synthesized by the
  safety+symbols composer, not extracted.
- **Adding a component**: one module under `components/` + one REGISTRY entry
  (+ extractor emission if it has a source form) + a golden regeneration if it
  changes shipped output. No writer surgery.
- **Template style names**: RST/LaTeX extraction may keep semantic `HB ...`
  names, but emitted IDML paragraph style refs and `Resources/Styles.xml`
  names must go through `tools/idml/style_names.py` so generated stories match
  the designer template's paragraph-style family.
- **Composed-page visual objects**: safety/symbols headings and rounded table
  outlines are spread-level objects with named object styles. H1 bars generated
  from section-level template semantics (`IMPORTANT SAFETY INFORMATION`,
  `MEANING OF SYMBOLS`, `WHAT'S IN THE BOX`) use square top corners and rounded
  bottom corners. H2/subbar components (`OPERATING INSTRUCTIONS`, the merged
  `USER MAINTENANCE INSTRUCTIONS` strip) stay full-pill. The symbol icon pair
  follows the template split (orders 1-6 left, 7-11 right; `weee2` is not forced
  into this page). The table story owns only the editable cell grid;
  `table_borders.py` suppresses the perimeter cell edges where a separate
  rounded outline object owns the border. Safety callouts follow the same rule:
  the spread-level rounded object owns the outer shape; the component table
  only carries editable icon/text content.
- **Template-baked object styles**: `tools/idml/template_merge.py` still adopts
  the designer template's resources, but it now injects object styles referenced
  by our spread/story content when the template does not define them, just like
  the existing missing-colour injection path.
- **Designer-reported InDesign traps** live as comments next to the exact
  strings that dodge them (`<Br/>` paragraph delimiting, `Paragraph*`-prefixed
  shading, `FillColor` not `CellFillColor`, PathGeometry not GeometricBounds,
  inline-anchor y∈[-h,0], DOMVersion 15.0, Auto leading for figures,
  SpanColumns). Move them with the code; never "normalize" the strings.
- **Size ratchet**: the façade and every package module are pinned in
  `tools/check_maintainability_guardrails.py`; the façade may only shrink.

## Entry points

- `python build.py idml --model M --region R [--lang L] [--data-root D]`
  (runs an rst prepare first, then the exporter; see `_dispatch_idml_action`;
  defaults to `--idml-mode production`)
- `python build.py idml --idml-mode flow --model M --region R [--lang L]`
  writes semantic flow artifacts and a simple continuous-story IDML under
  `docs/_build/<model>/<region>/<lang>/idml/flow/` for template handoff
- `python build.py idml --idml-mode both --model M --region R [--lang L]`
  writes the production IDML, the flow artifacts, and the design handoff package
  in one run
- `python tools/export_idml.py …` (direct CLI; `--check <file.idml>` validates)
- Tests: `python -m unittest tests.test_export_idml tests.test_export_idml_golden
  tests.test_export_idml_cli tests.test_idml_components tests.test_idml_package_layout`
