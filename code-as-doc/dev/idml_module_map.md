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
tools/bundle_asset_manifest.py
                              fail-closed renderer boundary for semantic bundle assets:
                              schema/target/consumer/format/path/hash validation
tools/idml/
  asset_contracts.py          target/page-scoped native-IDML asset requirements shared
                              by bundle finalization and component promotion
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
  reference_story_flow.py     approved-reference page ordering plus per-language
                              operation host-frame placement
  control_labels.py           Product Overview language+role label index, approved
                              App display-variant binding, and exact duplicate guard
  reference_layout_plan.py    registry lookup + approved-plan validation; exact-target
                              approved files missing from the registry fail closed
  reference_layout_rebind.py  complete Manual-IR identity/page-binding refresh with
                              unchanged-composition validation and atomic replacement
  lcd_reference_profile.py    fail-closed approved LCD row order, display numbering,
                              typography roles, and locale-selected fixed row geometry
  story_rhythm.py             localized operation H2 spacing derived from the LCD/Key
                              object that immediately follows the heading
  fcc_fallback.py             localized FCC prose -> fcc component fallback when the
                              source page has no explicit HBFccBlock
  notice_labels.py            localized NOTE/TIP/CAUTION/WARNING/DANGER label mapping
                              for notice-style list-table extraction
  stories.py                  story builders: prose (block-stream dispatch), lcd, symbols,
                              trouble, spec, text; delegates localized operation rhythm
  package.py                  zip contract (mimetype first + STORED), designmap wiring,
                              linked spread chain, height estimation
  components/                 the component registry — REGISTRY: kind -> renderer
    base.py                   RenderContext (geometry/params/target/asset roots; resolves
                              semantic assets only through the finalized usage manifest)
                              + shared figure paragraph
    callout.py                safetywarning / warninglead / tailwarnbox / warnbox / notice
    inbox.py fcc.py lcdmode.py
    oppanel.py                editable operation artwork overlays and special Energy
                              Saving / LED panels with top-layer text frames
    key_combinations.py       token-driven KeyCombinationStyle, native four-row grid,
                              linked icons, FR/ES locale overrides, and top-layer
                              independently movable copy frames
    reference_figure.py       approved Charging/App linked-art composites with generated
                              crops and unlocked top-layer caption/control stories
    prose_table.py            the extractor's ("table", json) block; owns
                              TroubleshootingTableStyle, native locale row-height
                              baselines, and content-safe fixed-panel estimation
    prose_image.py            the extractor's ("image", ref) block
  primitives.py               XML building blocks: psr/<Br/> semantics, bold runs, glyph
                              fallbacks, cells, tables, image frames, path geometry
  character_metrics.py        native-import-safe PointSize/Leading overrides for
                              content-bearing character runs
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
tools/reference_layout_rebind.py
                              dry-run-by-default maintainer CLI for the atomic approved-
                              contract source rebind; never edits composition geometry
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
- **Approved-plan activation**: a registry match activates and validates its
  contract. An exact-target approved contract that exists on disk but is absent
  from the registry is an error, not an ordinary-target fallback. Fuzzy
  measured-LaTeX mapping is available only when no approved contract exists.
- **Approved-plan source rebind**: use
  `tools/reference_layout_rebind.py --plan ... --manual-ir ...` as a dry-run,
  then repeat with `--write`. It requires unchanged semantic content,
  `source_ref` order, page languages, and physical composition; refreshes the
  mutable non-content identities plus every page source digest; validates the
  full candidate; and atomically replaces the file. It is not a plan-layout
  editor.
- **Layout-token identity**: Manual IR hashes the ordered parsed
  `key`/`value`/`unit` rows from `layout_params.csv`; raw EOLs, blank rows, and
  the comment column are non-semantic, while token/order changes remain bound.
- **LCD approved geometry**: the exact-target profile maps stable LCD source
  numbers to display order, semantic typography roles, and optional positive
  `row_height_pt_by_language` values. A governed segment must supply every row;
  mixed governed/native heights fail before export. The generic component-table
  primitive emits those rows as editable fixed-height rows, while locale placement
  continues to resolve through base plus `lang_*` layout tokens.
- **Key Combinations style ownership**: `KeyCombinationStyle.from_context()`
  resolves the base grid, asset, and type measurements from shared layout
  tokens. Governed French/Spanish height, indent, and leading-gap differences
  are locale token overrides. Shapes/assets are emitted first and independent
  text frames last, preserving the editable top layer for all three languages.
- **Troubleshooting style ownership**: `TroubleshootingTableStyle.from_context()`
  resolves the shared table type, row, ratio, step-padding, and corner tokens.
  Approved EN/FR/ES native row-height baselines cover shaping that deterministic
  IDML generation cannot query from InDesign (including the two-line FR/ES code
  header); measured wrapping adds growth when localized copy exceeds that
  baseline. The rounded group stays fixed and editable with `AutoSizingType=Off`.
  The production-master 0.25pt inner rule, 0.57pt outer rule, row minima, optical
  offsets, 240pt English floor, and import allowance remain explicit renderer
  calibration and must be revalidated by native preflight when changed.
- **App control-label ownership**: Product Overview table slots are indexed by
  language and semantic role (`main_power`, `dc_usb`, `ac`). The approved plan
  binds those base labels to reviewed App display variants; only an exact
  three-line base-label duplicate is consumed. `AppFigureStyle` owns the shared
  overlay tokens, and approved contexts fail on missing source roles, variants,
  assets, or tokens instead of guessing from adjacent prose.
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
- `python tools/reference_layout_rebind.py --plan <approved.json> --manual-ir
  <manual.ir.json> [--write]` (complete source rebind; dry-run by default)
- Tests: `python -m unittest tests.test_export_idml tests.test_export_idml_golden
  tests.test_export_idml_cli tests.test_idml_components tests.test_idml_package_layout`
