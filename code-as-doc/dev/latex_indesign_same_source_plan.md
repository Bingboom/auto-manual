# LaTeX to InDesign Same-Source Handoff Plan

Status: implemented and verified on JE-1000F US

Branch: `feat/latex-indesign-same-source`

Updated: 2026-07-12

## 1. Objective

Make the production IDML an editable projection of the same reviewed content,
semantic components, layout tokens, assets, and page plan used by the LaTeX
reference PDF. InDesign owns final-mile layout adjustments after content
freeze; it does not become a second content source or a second independent
layout system.

## 2. Discovery Report

The repository already has useful foundations:

- both render paths start from a prepared RST bundle;
- `data/layout_params.csv` is intended to be the shared design-token source;
- LaTeX has a 31-style public registry and stable component entrypoints;
- production IDML has a component registry, deterministic golden fixtures,
  template resource merging, source trace, asset packaging, and a reference
  PDF in the publish handoff.

The current seam is not yet same-source:

- production IDML reparses RST and raw LaTeX with a hand-written parser instead
  of consuming the semantic state used by Sphinx;
- data pages can be loaded from phase2 a second time and appended independently
  of the prepared review bundle;
- the IDML path estimates page counts from text height, while LaTeX owns the
  actual pagination;
- the two renderers have separate style maps, fallbacks, locale behavior, and
  visible geometry constants;
- structural IDML validation cannot detect overset text, missing fonts, broken
  links, page-count drift, or content drift.

The initial JE-1000F US characterization demonstrated the gap: LaTeX and IDML
did not agree on physical pages, InDesign reported six overset stories, and the
IDML exporter skipped raw blocks. The completed proof now produces 60/60 pages,
0.003 pt maximum page-size delta, 0 skipped raw blocks, 0 overset stories,
0 missing fonts, and 0 bad links.

## 3. Architectural Decision

The target pipeline is:

```text
review bundle + frozen snapshot
  -> one semantic manual IR + resolved style/token contract
  -> LaTeX reference PDF + measured page plan
  -> production IDML generated from the same IR/tokens/page plan
  -> InDesign final-mile adjustment (reference PDF + stable page/frame labels)
  -> final IDML/INDD + InDesign PDF + preflight/design delta
```

LaTeX public component macros remain stable. Shared transforms own semantic
classification; the LaTeX visitor renders those semantics through the existing
macros, while the IDML renderer consumes their serialized IR representation.

## 4. Invariants

1. One target build has one config identity, git SHA, frozen snapshot, bundle
   hash, semantic IR hash, style-contract hash, and asset set.
2. Production IDML never re-reads governed content behind the prepared bundle.
3. Every visible `HB-*` style has a machine-checked LaTeX binding, InDesign
   binding, token dependency, and final-mile edit policy.
4. Unknown components, skipped raw content, missing assets, missing fonts,
   modified links, and overset text are publish failures.
5. The initial IDML follows the measured LaTeX logical-page plan. Deliberate
   final pagination changes are recorded, not silently accepted.
6. Text, translation, specifications, legal copy, table structure, and asset
   identity are corrected at their source. InDesign edits never become content
   truth.

## 5. Phases

### Phase 0 - Contract and safety net

Files:

- `docs/renderers/contracts/manual_style.yaml`
- `tools/render_contract.py`
- `tests/test_render_contract.py`
- existing LaTeX and IDML style registries

Deliverables:

- machine-readable style contract for all 31 public LaTeX style IDs;
- typed layout-token parsing and locale resolution contract;
- coverage tests that expose missing tokens or renderer bindings;
- no production artifact change.

Safety net:

- style-registry ID set equals contract ID set;
- every required token exists in `layout_params.csv`;
- every style forbids content edits in InDesign;
- contract serialization and SHA are deterministic.

### Phase 1 - Semantic manual IR

Files:

- new focused `tools/manual_ir/` package;
- shared semantic transforms extracted from the LaTeX-only transforms;
- `docs/conf_base.py` sidecar emitter;
- `tools/export_idml.py` compatibility facade;
- IR fixtures and parity tests.

Deliverables:

- deterministic `manual.ir.json` with stable document/page/block/source IDs;
- normalized content, component, table, asset, break-policy, and source hashes;
- production IDML can consume the IR behind a config feature switch;
- legacy IDML remains byte-identical until the new renderer is selected.

#### Public v1 read contract

[`read_manual_ir(path)`](../../tools/manual_ir/serialize.py) is the shared file
boundary. A successful read returns a `ManualIR` satisfying the same base
contract as [`validate_manual_ir(ir)`](../../tools/manual_ir/validate.py):

- a typed `manual-ir/v1` envelope with at least one page; page/block collections
  are arrays, identities are non-empty strings, and `skipped_raw` is a
  non-negative integer (a boolean or numeric string does not qualify);
- unique page IDs and page source references, and globally unique block IDs
  and block source references; each block's source reference identifies its
  containing page followed by a non-empty `#` fragment. IDs and fragment names
  remain opaque; there is no new renderer-specific numbering convention;
- lowercase 64-character SHA-256 digests, recomputed block content hashes and
  aggregate content hash in page/block order, and the exact ordered union of
  block asset references at manual level;
- JSON payload/metadata values, with non-finite numbers, duplicate JSON keys,
  malformed containers and implicit type conversions rejected.

Invalid files raise the exported `ManualIRValidationError`, a `ValueError`
subclass carrying `source` and `issues`; its message includes the input path
and field/index or page/block identity. JSON syntax and decoding failures use
the same error boundary. Reading never rewrites, rehashes or repairs input.
Serialization format, hash algorithms and valid v1 content/order are unchanged.
Absent optional `asset_refs`, `metadata`, `skipped_raw` and `snapshot_sha256`
keep their previous defaults; explicit null is permitted only for the snapshot
digest. Arbitrary component kinds and JSON payloads remain the owning component
contract's concern, without a second IR or registry here.

The migrated file consumers are PDF parity (`tools/idml_pdf_parity.py`),
reference-layout rebind (single and all-registered), reference-layout scaffold,
and `tools/idml/target_assembly_scaffold.py`. They reject invalid input before
writing reports, drafts or rebound plans. The scaffold's in-memory entry also
uses shared validation instead of its former local schema/digest-format check.
The handoff report also reads its source sidecar through `read_manual_ir`
before copying production files or writing reports. It derives skipped-raw
counts from validated pages; an absent sidecar remains unavailable (`null`),
while a malformed sidecar fails instead of becoming zero. The source sidecar
path is preserved even when the handoff directory differs from the input.
No consumer currently needs an unchecked legacy file entrypoint.

The base contract does not open external bundle/snapshot/assets to verify
digest freshness, approve a layout, or prove renderer readiness. Language
registration and zero skipped raw blocks remain opt-in flags on
`validate_manual_ir`; ordinary reads preserve unknown languages and nonzero
counts. Reference-layout consumers retain their frozen-snapshot/layout-hash
algorithm requirements. `write_manual_ir` remains a serializer; callers
constructing IR in memory must validate before using it at a trusted boundary.

#### Public source-page assembly boundary

[`build_manual_ir_from_source`](../../tools/manual_ir/builder.py) assembles the
existing `ManualPage` / `ManualBlock` objects from
[`ManualSource` and `SourcePage`](../../tools/manual_ir/source.py). These two
unversioned Python inputs carry ordered, decoded `(kind, payload)` pairs and
source provenance; they have no separate serializer, schema or component
registry. `ComponentSpec` still owns component payloads, and `PagePlan` still
owns physical assembly. Source page IDs, references, paths, languages and
external digests are supplied by the adapter; the core derives block IDs,
block/manual content hashes, ordered asset references and aggregate counts.
It does not open source files, choose tags, decode RST or import IDML. Ordinary
and strict validation remain the existing `validate_manual_ir` contract.

[`prepared_rst.py`](../../tools/manual_ir/prepared_rst.py) is explicitly the
**legacy IDML/LaTeX projection adapter**. It retains `bundle_page_order`,
`extract_page`, `page_language`, manifest declarations and the existing
`latex` / `idml` / region / model / normalized-category / per-page-language
`only` tags. It decodes only the historical component/data/table JSON payloads;
other text is unchanged. The former source digest functions now live in
[`hashing.py`](../../tools/manual_ir/hashing.py), with identical attachment-token
normalization and snapshot/layout hash semantics. The parser itself remains
at its original paths and still depends on IDML implementations.

Real callers and retired responsibilities:

- `tools/manual_ir_cli.py` and `tools/idml/ir_sidecar.py` explicitly load a
  prepared source and call the shared assembler. The sidecar's redundant
  bundle traversal is removed; its optional empty-bundle behavior remains,
  while CLI/public builds still reject empty bundles.
- The exported `build_manual_ir` and `tools.manual_ir.builder.build_manual_ir`
  retain their keyword signatures as a lazy compatibility facade. Production
  `export_idml.main` reaches the same assembler through its existing
  `ir_projection.build_same_source_ir` caller. This preserves its completeness,
  asset and reference-layout gates without changing the IDML entrypoint.
  The facade contains no second extraction, assembly or hashing implementation.
- `tools/idml/flow_md.py` keeps its intentionally different tag selection:
  requested language, `latex`, region/model, without production `idml` or
  category tags. Flow export's IR sidecar uses the production projection as
  before; flow Markdown is not silently made equivalent to that IR.

The boundary test starts a fresh process that forbids **all** IDML imports and
the prepared-RST adapter, then builds, validates and round-trips a source with
non-RST identities. Real CLI, production exporter and sidecar tests observe
the source assembler and verify the emitted IR is its exact result. Refactor
checks also compare old/new CLI/public/sidecar IR JSON and IDML ZIP member
bytes, including source hashes, IDs, source references and asset order. Existing
goldens are not refreshed.

Integrity follow-up: every direct page include in the prepared index must
exist as a file; discovery reports the index and missing source reference
instead of silently shortening the book. The registered prose-macro decoder
requires complete arguments (respecting escaped braces and comments), and
counts non-plumbing residue around recognized calls as skipped raw content.
The existing preface-begin marker is recognized as layout-only; page-break
normalization is idempotent for bare and already-braced markers.
Strict IR rejects those pages through the existing skipped-raw policy;
permissive extraction retains supported blocks and reports the skipped count.
This is not a general TeX completeness proof: generated data macros and the
special LCD decoder retain their separate interpretation paths.

**Cross-renderer status:** declared Web specification tables now have a real
public IR consumer: `build_word_bundle_html` / `transform_web_fragment` →
`manual_ir.web_specs.load_web_spec_source` → `build_manual_ir_from_source` →
`web_spec_component.render_specification_ir`. The Web profile no longer calls
`_extract_spec_word_data` / `render_spec_word_html`; the document profile still
owns that existing path. Undeclared tables are never selected by filename alone.

The `manual-ir/v1` envelope is unchanged. This explicitly scoped
`metadata.projection=web-specifications` contains only declared sections from
one prepared HTML fragment. Each extension block (`web_specification`) owns a
validated ComponentSpec plus retained heading/table HTML for authored links,
emphasis and line breaks; markup/semantic disagreement fails closed. The
adapter hashes the actual input fragment and loaded registry/theme, records
snapshot as unavailable and layout parameters as unused, and indexes inline
image sources in the public asset union. It does not manufacture snapshot
provenance. All sections validate before the caller DOM changes, and a serialized
projection can replay without the source file. Core imports remain independent
of this HTML adapter and the legacy IDML extractor.

**LCD and troubleshooting consumers:** prepared Web bundles and standalone
MyST now use one `web_table_ir` consumer through the existing two transform
entrypoints. `manual_ir.web_tables` owns declaration selection, row geometry,
authored headers and role-labelled data (`number/icon/name/description` or
`code/measures`). The `web_table` extension payload retains rich markup for
presentation; semantic/markup drift and malformed later tables reject before
caller mutation. Images enter the public asset union, and provenance hashes
the actual prepared fragment plus the existing `web_manual.css` contract.
The bounded standalone runtime includes the same public assembler/reader and
language registry; it does not carry the legacy prepared-RST/IDML adapter.

`manual_ir.web_source` now owns the shared provenance envelope used by both
specifications and declared tables. Specification IR bytes remain unchanged.
LCD/troubleshooting are not registered ComponentSpecs; this migration does not
invent a registry registration or change `manual-ir/v1`.

| Real consumer | Public IR status | Source boundary still present |
| --- | --- | --- |
| Prepared Web / standalone MyST specifications | Shared scoped specification IR | Prepared/generated HTML + retained rich markup |
| Prepared Web / standalone MyST LCD and troubleshooting | Shared scoped table IR | Prepared/generated HTML + retained rich markup |
| Prepared Web callouts / standalone MyST callouts | Shared callout IR consumer | Rendered HTML + ComponentSpec; protected composite figures remain separate |
| Prepared Web Inbox (three cards + internal TIP) | Scoped composite IR before figure protection | Existing Inbox HTML parser + retained markup; original figure-target gate |
| Prepared Web FCC | Scoped semantic component IR before figure protection | Existing FCC HTML/marker parser at source boundary; replay uses no HTML/config |
| Prepared Web signal-word legend | Scoped table IR before figure protection | Governed warning-lockup markup/row-count selection + retained HTML |
| Prepared Web icon/meaning pair panels | Scoped pair IR before figure protection | Existing 7 × 4 matrix and left 6 / right 5 contract + retained HTML |
| Other Web components; Word; Flow | Not closed by these batches | Existing component/read/tag policies |

The standalone `{spec-table}` directive now encodes its authored title and
inline rows for the existing specification IR adapter/consumer. Its duplicate
ComponentSpec grouping, rowspan and final-table rendering path has been removed.
The directive emits the figure only; the argument supplies IR section-title
semantics without introducing an extra visible heading. Inline escaping and
row tokenization remain the Markdown carrier's responsibility. Plain circled
references now receive the same Web superscript style; authored superscripts
are preserved without nesting. Staging reuses the existing specification modules,
with no new parser module, config, registry entry or serialized schema.

**Prepared Web callout handoff:** `export_markdown_from_bundle` now passes each
explicit `manual-callout-table` through `manual_ir.web_callouts` and public
assembly before Pandoc. The existing placeholder map carries ManualIR instead
of raw HTML. Restoration consumes `web_callout_ir.render_callout_ir`; there is
no raw-string fallback or second source-file read. The one-block `web-callout`
projection owns the registered ComponentSpec, original HTML and image references.
Both public envelope checks and semantic/markup/asset agreement are required;
recomputed envelope hashes cannot hide inconsistent owned payloads. Ambiguous
rows, cells, spans or nested tables fail. Original HTML bytes, lists, links,
images and label copy are retained. The actual bundle path/model/region are
provided by the caller; language comes from the table or remains `und`.

**Standalone MyST callouts:** the directive now keeps parsed document nodes
until Sphinx's HTML writer resolves their links, images and rich content. Its
callout node then supplies the label/body HTML to the same source adapter,
public assembler and replay consumer. Direct ComponentSpec-only HTML emission
has exited this Web path. The optional owned `declaration` payload preserves
configured language and an explicit `:variant:` (including custom labels);
malformed declarations and declaration/semantic/markup disagreement fail.
Prepared Web payloads without this declaration remain unchanged.

Staging reuses the existing callout modules; no new implementation module,
registry entry or serialized schema is introduced. The extension environment
version invalidates old cached doctrees. Non-HTML writers keep the parsed body
through their ordinary container visitors. The shared one-row label/body
contract rejects nested tables/callouts with source context; these are not
flattened or partially emitted. Other composite callouts remain on the figure
path; Inbox now has its own scoped public IR consumer described below.
Remaining HTML parsing and language-label lookup are explicit source-adapter
debt, not a renderer-neutral rich-text implementation.

**Prepared Inbox composite:** `transform_web_fragment` retains the existing
figure-target gate, then `transform_inbox` loads the public source and assembles
`metadata.projection=web-inbox`. Its single `web_inbox` block owns the existing
`HB-SPECIAL-INBOX` ComponentSpec, exact heading/card/tip markup and all markup
image references. The internal TIP remains part of Inbox, not a second callout.
`web_inbox_component.render_inbox_ir` validates the envelope and payload agreement,
then uses the existing component projection on detached tags. The caller replaces
its grid/tip only after replay succeeds. The former direct ComponentSpec-only
entry and hardcoded language facade exit; serialized replay needs no source file.
One source adapter is added; the existing renderer is reused without raising
its hotspot limit. Real EN/FR/ES outputs remain byte-identical. This does not
migrate the generic figure string-protection map, other composite figures or
Word/IDML Inbox adapters, and does not expand approved target admission.

**Prepared FCC composite:** the existing Web target/source gate reaches
`load_web_fcc_source` → public assembler → `render_fcc_ir`. Its single `web_fcc`
block contains the existing `HB-SPECIAL-FCC` instance and an explicit mark binding
(`asset_ref`, `src`). Opening lines, ordered paragraphs/measures and column break
already express the rendered FCC content, so replay consumes semantic data
without retaining/reparsing a second HTML representation or loading source config.
It validates public hashes, canonical ComponentSpec fields, source/language identity
and the mark binding before caller DOM mutation. Source provenance includes
actual HTML, target context and active FCC config/registry/theme hashes.

The direct ComponentSpec-only Web route exits. Existing FCC parser rules,
label/filename language fallback, paragraph normalization, target admission,
Word/IDML behavior and generic figure protection remain. Three captured EN/FR/ES
outputs match byte for byte. Serialization tests delete source/config and forbid
parser calls; a valid semantic edit changes output, while inconsistent owned
payloads fail. One source/contract adapter reuses the existing renderer without
raising its 150-line limit. This does not promise arbitrary HTML rich-text fidelity.

**Prepared signal-word legend:** `transform_symbol_signal_table` now loads
`manual_ir.web_symbols` source, invokes the public assembler and consumes
`web-symbol-signals` IR before applying a figure. One `web_signal_table` block
retains headers, labels, meanings, table HTML and markup image references.
The source adapter owns the existing warning-lockup/row-count selection and
all visible-label extraction; the renderer no longer decodes raw caller rows.
Public hash validation and re-decoding of the retained table verify owned payload
agreement on replay. All rows must have complete unspanned geometry and exactly
one visible label; validation precedes any source DOM mutation.

The old direct DOM path exits, including its failure after partly rewriting a
malformed table. Three real EN/FR/ES outputs remain byte-identical, including
adjacent newlines left by removal of the print colgroup. One source/contract
adapter reuses the existing renderer with no raised hotspot limit or new
ComponentSpec registry/schema. This table did not already have a ComponentSpec;
its owned table payload is not a new parallel registry. Source markup/filename
admission remains debt; pair panels now have the consumer described below.
Generic figure protection and whole-manual migration remain separate.

**Prepared symbol pairs:** the actual Web call now loads `web-symbol-pairs`
source, invokes the public assembler and consumes a `web_symbol_pairs` block
before changing the selected table. It retains four headers, ordered semantic
icon/meaning pairs, original table HTML and all image references. Pair replay
verifies semantics/assets against retained markup. Full matrix geometry, one
nonempty icon per populated pair and truly empty unused right cells are checked
before mutation; nested tables, duplicate candidates and partial rows fail.

The existing `manual_ir.web_symbols` module now owns both source families and
shares their provenance/envelope helpers. Signal payloads and hashes remain
unchanged. The old direct pair implementation exits `web_presentation`;
`web_symbol_pairs` keeps its original rendering body behind the public IR
consumer. No hotspot threshold, registry, config or serialized schema changes.
Tests verify exact three-locale whole-page output and three unchanged signal
IR envelopes, including source-free pair replay, rich meaning markup, 6/5
ordering and asset completeness. The fixed matrix/source gate remains; this
does not generalize pair counts or complete whole-manual/neutral-rich-text work.

These are **three scoped table families across both Web entrances plus the
shared callout consumer, prepared signal-word legend and icon/meaning pairs,
Inbox and FCC composites**, not whole-manual Web IR or a
renderer-neutral rich-text parser. Tests observe actual bundle invocations,
standalone isolated-process builds, serialized replay, and unchanged existing
outputs. A shared ComponentSpec helper alone does not count as IR adoption.

Deferred: renderer-neutral extraction, remaining RST/LaTeX parser dependencies,
and any deliberate reconciliation of flow policies. The prepared-RST adapter
preserves a multi-row signal-word definition table when every row has exactly
two nonempty cells and a distinct label recognized by the shared callout
vocabulary. This resolves the JE-1000F/JP Web-bundle failure on its four-row
definition table while keeping all rows and source wording. Single notices
still become callouts; incomplete notices and malformed definition tables
starting with a known label still fail instead of becoming generic tables.
The prepared-RST decoder also recognizes a plain white/bold `tcolorbox`
heading followed by explicit `par/noindent` paragraphs, emitting existing
`h2` and `body` blocks in source order. It consumes the whole block only when
the options are content-free layout keys and the text is plain copy or escaped
punctuation. Unknown commands, content-bearing options, malformed boxes and
empty paragraphs remain skipped; embedded recognized macros cannot hide an
unsupported box. No target or language dispatch is added.
This restores the JE-1000F/JP symbols heading and both introductory paragraphs:
the same frozen runtime bundle goes from 267 to 270 blocks and passes strict
IR validation with `skipped_raw=0`. The source template and LaTeX geometry are
unchanged. This closes that extraction debt, not native page-layout acceptance
or production-delivery signoff.
Native comparison on 2026-09-05 (InDesign 21.0.1.6, the previous frozen local
snapshot) finds the same existing layout failures before and after this fix:
28 pages, two overset stories and 17 overset table cells, repeated identically
after save/reopen. Affected pages are 14–17 (operation guide) and 24
(temperature specification table); missing fonts, glyphs and links are zero.
The tool's aggregate 38 counts both inspection passes, not 38 distinct defects.
Native PDF export is blocked by overset. The same-source LaTeX PDF has 22 pages;
reconciling the fallback page plan and native content budgets is a separate
layout task, without changing constants solely to force equal page counts.
This boundary does not change native acceptance
D1–D4 (including the power on/off factual debt) or `production_eligible`.

### Phase 2 - Shared tokens and production IDML renderer

Files:

- `tools/idml/ir_renderer.py`
- `tools/idml/layout_tokens.py`
- existing IDML component/page/style modules;
- config-aware IDML dispatch and export paths.

Deliverables:

- production IDML reads only the IR and resolved tokens;
- visible hardcoded geometry moves into the shared contract/token surface;
- all 31 public styles and specialized tables/components have explicit IDML
  bindings;
- flow IDML remains a diagnostic semantic attachment, not the visual baseline.

### Phase 3 - LaTeX page plan and InDesign proof

Files:

- LaTeX page-anchor emitter and page-plan parser;
- IDML stable labels/layers/reference-page support;
- an InDesign runtime preflight/export script;
- parity-report and proof tests.

Deliverables:

- `latex_page_map.json` with logical page/component anchors;
- IDML frame chains follow the measured plan instead of character estimates;
- versioned LaTeX reference PDF and stable labels for designer overlay/comparison;
- machine-readable InDesign preflight covering overset, fonts, links, pages,
  and exported PDF status.

### Phase 4 - Final-mile trace and publish integration

Files:

- IDML delivery and source-trace modules;
- release-manifest integration;
- designer checklist and operator documentation;
- optional stable-ID layout-delta extraction/replay.

Deliverables:

- engineering baseline package and designer-return package;
- hashes for source, bundle, IR, contract, reference PDF, baseline IDML,
  preflight, final IDML/INDD, InDesign PDF, and design delta;
- final-mile edits are auditable and reusable layout fixes are routed back to
  shared components/tokens.

## 6. Non-goals

- Do not replace the existing LaTeX visual implementation.
- Do not make flow IDML the production baseline.
- Do not promise arbitrary InDesign edits survive regeneration in the first
  implementation. Version 1 freezes content before design handoff.
- Do not require Adobe InDesign on normal CI workers. Structural and semantic
  parity runs in CI; real InDesign preflight runs on a provisioned design host.
- Do not back-port edited IDML text into source tables or templates.

## 7. Verification Ladder

Run in order for each phase:

1. `python -m ruff check build.py integrations tools tests scripts`
2. targeted contract/IR/IDML tests
3. `python -m unittest`
4. `python -m mypy tools/utils`
5. `python tools/check_maintainability_guardrails.py`
6. `python tools/check_doc_link_integrity.py`
7. JE-1000F US build and cross-renderer parity checks
8. real InDesign preflight and exported-PDF comparison on the design host

The verified JE-1000F US result is: identical bundle/IR/style identity across
the handoff, 52 IR source pages and 602 blocks with zero skipped raw content,
51/52 source-page anchors matched (the graphical cover is intentionally
unmatched), 60 LaTeX and 60 InDesign pages, 0.003 pt page-size delta, zero
overset/missing-font/bad-link findings, and a full 60-page descriptive raster
delta report. Visual differences remain final-mile design work, not content
divergence.
