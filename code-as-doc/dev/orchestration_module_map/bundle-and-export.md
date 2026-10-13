# Orchestration module map: build bundle and export modules (§3)

Status: active · Part of the [orchestration module map](../orchestration_module_map.md); its index lists the other
module families. Update this page in the same PR that moves a boundary here; do not add
module notes to the hub.

## 3. Build Bundle And Export Modules

[`tools/utils/csv_fields.py`](../../../tools/utils/csv_fields.py) owns the pure
column spelling, header presence and cell text selection primitives. It has
no business-reader or language-registry imports.
[`tools/localized_copy.py`](../../../tools/localized_copy.py) retains compatible
exports, registry-aware snapshot helpers and the strict copy-key resolver. IDML
compatibility loaders and CSV page readers keep using those exports;
[`tools/lang_registry.py`](../../../tools/lang_registry.py) remains the language
metadata owner. Spec_Master row helpers and lookup consumers use `csv_fields`
directly, retaining their own narrow alias and source-language policy. The
dependency stays one-way: `localized_copy -> spec_master -> row_helpers ->
csv_fields`; no lazy import hides a return edge. Model canonicalization,
ranking, filtering, repair and cache owners are unchanged. Table fallback and
empty-cell policies are recorded in
[`external_table_contracts.md`](../external_table_contracts.md#localized-columns-in-frozen-snapshots).

[`tools/build/docs.py`](../../../tools/build/docs.py) should stay a wrapper-compatible facade. Its public names are listed in `__all__`; a wrapper or re-export that no code or test references is deleted rather than kept for symmetry. It delegates to:

- [`tools/build/docs_main.py`](../../../tools/build/docs_main.py)
  - CLI bootstrap for the low-level build entrypoint
- [`tools/build/docs_entry.py`](../../../tools/build/docs_entry.py)
  - top-level build session orchestration
- [`tools/build/docs_targets.py`](../../../tools/build/docs_targets.py)
  - build target resolution and configured target expansion
- [`tools/build/docs_bundle.py`](../../../tools/build/docs_bundle.py)
  - ordered bundle preparation: runtime materialization, review overlay, attachment aliases, then asset finalization
- [`tools/bundle_asset_finalize.py`](../../../tools/bundle_asset_finalize.py)
  - final `index.rst` include-closure scan with inherited language context and fail-closed conflict handling
  - post-overlay path rewrite, final page-path recomputation, support-tree/file hashes, and `bundle_sha256`
- [`tools/gen_index_bundle_assets.py`](../../../tools/gen_index_bundle_assets.py)
  - RST image/figure/substitution and raw-HTML `src` path mapping
  - bundle-relative staging bridge for semantic and legacy asset references
- [`tools/gen_index_bundle_materialize.py`](../../../tools/gen_index_bundle_materialize.py)
  - contract preflight and initial non-finalized bundle manifest assembly
- [`tools/build/docs_export.py`](../../../tools/build/docs_export.py)
  - export orchestration shell for one build target
- [`tools/build/docs_artifacts.py`](../../../tools/build/docs_artifacts.py)
  - export-plan derivation
  - word/pdf/html artifact steps
  - HTML postprocess handoff
- [`tools/build/docs_html.py`](../../../tools/build/docs_html.py)
  - manual HTML metadata and switcher helpers
- [`tools/web/presentation.py`](../../../tools/web/presentation.py)
  - compatibility facade for web-profile figure/table composition and Pandoc-safe semantic restoration
- [`tools/web/presentation_contract.py`](../../../tools/web/presentation_contract.py)
  - fail-closed resolver for `shared base → skeleton profile → target overlay`
  - recursively merges mappings, merges stable-`id` lists by item, replaces ordinary lists, and derives target-scoped capability selectors
- [`tools/operation_artwork_mode.py`](../../../tools/operation_artwork_mode.py)
  - reads an Operation figure's presentation mode from that resolved contract and marks a `base-art-live-copy` Web figure (Operation or reference)
  - the IDML main-power panel reads the same mode, but only for an active component target ([`idml_component_targets.md`](../idml_component_targets.md))
- [`tools/web/base_art_operation.py`](../../../tools/web/base_art_operation.py)
  - places one base-art Operation figure's live copy on its declared `base_art_layout` anchors, or lays out a footer-panel card (lead, art, numbered steps); never measures the artwork
- [`tools/web/base_art_reference.py`](../../../tools/web/base_art_reference.py)
  - places one base-art reference figure's captured source lines on the panel rectangles its `base_art_layout` declares, each line exactly once; never measures the artwork
- [`tools/component_specs/operation_html.py`](../../../tools/component_specs/operation_html.py) `base_art_panel_copy`
  - the one rule both Web paths use to give a base-art figure its source panel copy (`mode_label`, `sos_label`)
- [`tools/component_specs/fcc_declaration.py`](../../../tools/component_specs/fcc_declaration.py)
  - shares source-driven full-FCC admission between fragment rendering and whole-document ownership; exact declarations and headingless Part 15 fallback preserve compact mixed-page statements
- [`tools/manual_ir/whole_document_components.py`](../../../tools/manual_ir/whole_document_components.py)
  - whole-document ownership pass for the fourteen registered component types;
    claims shared special sections and native table components once and preserves flow order
- [`tools/manual_ir/components.py`](../../../tools/manual_ir/components.py)
  - strict embedded ComponentSpec carrier validation, asset enumeration and
    renderer-neutral document-order traversal
- [`tools/web/embedded_components.py`](../../../tools/web/embedded_components.py)
  - whole-document Web dispatch from embedded component identity to the existing adapters
- [`tools/web/component_carriers.py`](../../../tools/web/component_carriers.py)
  - rich carrier/semantic agreement checks shared by Inbox, FCC and Overview adapters;
    `web_fcc_markup` holds FCC-only HTML construction helpers below hotspot limits
- [`tools/manual_ir/web_specs.py`](../../../tools/manual_ir/web_specs.py)
  - declared HTML specification source adapter into the public ManualSource contract;
    isolated from the neutral core and IDML extraction
- [`tools/web/spec_component.py`](../../../tools/web/spec_component.py)
  - validated ManualIR specification consumer with rich markup replay and atomic DOM application;
    used by both the prepared Web bundle and standalone `SpecTableDirective`
  - Word extraction/re-rendering and directive-local grouping are absent from these Web paths
- [`tools/manual_ir/web_source.py`](../../../tools/manual_ir/web_source.py)
  - shared scoped HTML-source provenance envelope; reused by specifications, declared tables, callouts, Inbox, FCC and signal legends
- [`tools/manual_ir/web_tables.py`](../../../tools/manual_ir/web_tables.py)
  - one declared LCD/troubleshooting source decoder and owned payload validation;
    explicit CSV/class identities select tables independently of filenames or artwork grants
- [`tools/web/table_ir.py`](../../../tools/web/table_ir.py)
  - shared public IR replay and atomic DOM application for LCD/troubleshooting;
    `web_lcd_component` / `web_troubleshooting_component` are thin existing entrypoints
- [`tools/manual_ir/web_callouts.py`](../../../tools/manual_ir/web_callouts.py)
  - declared/generated HTML callout decoder; owns one-row geometry, ComponentSpec, image references
    and optional explicit carrier language/variant declarations
- [`tools/web/callout_ir.py`](../../../tools/web/callout_ir.py)
  - public IR replay for the Web/Pandoc placeholder handoff; verifies semantics against retained markup
- [`tools/web/callout_alignment.py`](../../../tools/web/callout_alignment.py)
  - page-level pass after the callouts are restored: every label cell carries the page's distinct labels
    as invisible width references, so all label columns share one width that fits the widest label
  - `web_presentation` passes IR and `markdown_bundle` supplies actual source/target context;
    standalone MyST uses the same consumer after Sphinx renders its resolved child nodes;
    already-protected composite figures remain a separate path
- [`tools/manual_ir/web_inbox.py`](../../../tools/manual_ir/web_inbox.py)
  - scoped Inbox source/payload adapter; reuses the existing three-card + internal TIP ComponentSpec
  - records retained markup/assets and validates complete geometry plus semantic agreement
- [`tools/web/inbox_component.py`](../../../tools/web/inbox_component.py)
  - real Web entrypoint assembles public IR, replays on detached tags, then atomically applies the figure
  - existing target gate and projection remain; direct ComponentSpec-only Web reading has exited
- [`tools/manual_ir/web_fcc.py`](../../../tools/manual_ir/web_fcc.py)
  - prepared FCC source and owned IR contract; carries existing semantic blocks and resolved mark binding
  - validates canonical semantics, source identity and asset binding without reparsing HTML at replay
- [`tools/web/fcc_component.py`](../../../tools/web/fcc_component.py)
  - actual Web consumer assembles public IR and renders its semantic slots before mutating caller DOM
  - retains existing FCC projection/layout; source marker config is not a renderer input
- [`tools/manual_ir/web_symbols.py`](../../../tools/manual_ir/web_symbols.py)
  - governed signal legend and icon/meaning pair sources; share provenance/envelope checks
  - validate complete rows, labels and pair assets against retained rich table markup before replay
- [`tools/web/symbol_components.py`](../../../tools/web/symbol_components.py)
  - actual signal-table Web consumer uses public IR and applies the figure only after validation
  - raw caller-row decoding exits; signal payloads/hashes stay stable as pair consumers migrate
- [`tools/web/symbol_pairs.py`](../../../tools/web/symbol_pairs.py)
  - public IR consumer for the existing left-six/right-five icon/meaning panels
  - moves the direct source/render loop out of `web_presentation`; applies only fully validated replay
- [`tools/manual_ir/web_app_download.py`](../../../tools/manual_ir/web_app_download.py)
  - prepared App download source and owned payload validation; binds two rich-copy columns and all artwork
  - snapshots config/CSS provenance; replay validates data without reopening source/config
- [`tools/web/app_download.py`](../../../tools/web/app_download.py)
  - real public IR consumer for store/QR columns; retains the original rendering body
  - replaces image/removes consumed paragraphs only after complete validation and detached rendering
- [`tools/manual_ir/web_app_controls.py`](../../../tools/manual_ir/web_app_controls.py)
  - prepared add-device paragraph source; validates localized label and markup/image agreement
  - owns prefix/button-vocabulary admission and config/CSS provenance
- [`tools/web/app_controls.py`](../../../tools/web/app_controls.py)
  - actual public IR consumer replaces only the validated paragraph after detached replay
  - renders the existing accessible glyph without source/config access; old direct caller exits
- [`tools/web/reference_components.py`](../../../tools/web/reference_components.py)
  - reusable reference-figure label validation, themeable captions, and shared App artwork with live localized control labels
- [`tools/web/stylesheets.py`](../../../tools/web/stylesheets.py)
  - ordered assembly of the responsive base theme and focused component CSS modules into one public Sphinx stylesheet
- [`tools/utils/spec_footnotes.py`](../../../tools/utils/spec_footnotes.py)
  - shared reference-ID parsing, numeric markers and marker attachment for CSV spec and IDML readers; row/language selection stays with callers
- [`tools/build/docs_io.py`](../../../tools/build/docs_io.py)
  - Sphinx, cleanup, Word/PDF I/O helpers
- [`tools/build/docs_validation.py`](../../../tools/build/docs_validation.py)
  - config/layout validation helpers for the build tool
- [`tools/word/bundle_docx.py`](../../../tools/word/bundle_docx.py)
  - DOCX export assembly and Word post-processing orchestration
- [`tools/word/bundle_docx_styles.py`](../../../tools/word/bundle_docx_styles.py)
  - DOCX heading/style remapping and outline-level normalization
- [`tools/word/bundle_docx_images.py`](../../../tools/word/bundle_docx_images.py)
  - DOCX external image embedding and content-type updates
- [`tools/word/bundle_docx_pandoc.py`](../../../tools/word/bundle_docx_pandoc.py)
  - pandoc version guardrails for reference-template DOCX exports
- [`tools/word/bundle_docx_xml.py`](../../../tools/word/bundle_docx_xml.py)
  - namespace-preserving XML serialization helpers for DOCX package rewrites
- [`tools/word/bundle_docx_reproducible.py`](../../../tools/word/bundle_docx_reproducible.py)
  - release-only DOCX canonicalization for timestamps, local file URIs, ZIP metadata, and member ordering
