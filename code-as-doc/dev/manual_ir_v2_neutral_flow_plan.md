# ManualIR v2 Neutral Flow — Discovery And Implementation Plan

Status: implementation and local acceptance complete; PR pending

Branch: `feat/manual-ir-v2-neutral-flow`

Baseline: `bc31fec0` (`#1058` merged)
Updated: 2026-09-05

## 1. Objective

Replace the whole-document Web projection's HTML-shaped content authority with
renderer-neutral flow and rich-text nodes under `manual-ir/v2`. Keep the
currently rendered Web output and packaged-asset guarantees stable, and keep
existing `manual-ir/v1` files readable during the migration.

This is cut 1 of the seven-cut cross-renderer IR closure. It creates the
neutral document substrate; it does not claim that ComponentSpec instances or
all four renderer adapters have migrated.

## 2. Discovery Report

### 2.1 Current production path

The current whole-document path is:

```text
prepared RST
  -> web_document_source.load_web_document
  -> Pandoc/BeautifulSoup HTML
  -> one document_content block per page
  -> HTML tag/attribute/child dictionaries
  -> manual-ir/v1
  -> web_document_ir.tree_to_html
  -> web_presentation.transform_web_fragment
```

The public envelope, ordered pages, source hashes, asset union, packaged asset
hashes and cold Web replay are real. The page content is not renderer-neutral:
`document_content` stores `div`, `table`, `img`, CSS classes and other DOM
attributes, and the Web consumer reconstructs that DOM before it can identify
semantics.

### 2.2 Measured representative baseline

The merged `#1058` artifacts were inspected without modifying them:

| Target | Pages / blocks | Content SHA-256 | Observed HTML node vocabulary |
| --- | ---: | --- | --- |
| JE-1000F / US | 49 / 49 | `4a6c7290a94f73475e5dbcb0c3426c9c80be31602f7c2d7f59d54471a066fd4c` | `a`, `br`, `col`, `colgroup`, `div`, `h1`–`h3`, `img`, `li`, `p`, `section`, `span`, `strong`, `sub`, table nodes, `ul` |
| JE-1000F / EU / it | 15 / 15 | `ffaa91579b73445fa00bc6378f213d2aa034500efde57e18fe2bf11acc2736e7` | same production subset without links |
| JBP-2000B / JP / ja | 12 / 12 | `2f7f7d313df4f10b9aa4496a6b9fbf9bb3977fc72a12c84b8e007b64235885df` | the production subset plus ordered lists |

The active attributes are `alt`, `aria-hidden`, `class`, `data-*`, `href`,
`id`, `rowspan`, `scope`, `src` and `style`. `src`, `alt`, link targets,
anchors and table span/scope are content/accessibility semantics. CSS classes,
inline style and Web `data-*` attributes are renderer hints.

Calling `project_manual_ir_components()` on each of these whole-document IRs
currently fails at Product Overview because that projector expects typed
`h1`/`h2`/`image` blocks, not a nested HTML content tree. This is recorded as a
dependency for cut 2; cut 1 must not add another DOM scraper to that projector.

The pre-change focused safety net passes 79 tests:

```text
python3 -m unittest \
  tests.test_manual_ir tests.test_manual_ir_read_contract \
  tests.test_manual_ir_source tests.test_web_document_ir \
  tests.test_component_specs tests.test_component_spec_table \
  tests.test_component_spec_fcc tests.test_component_spec_inbox \
  tests.test_component_spec_overview
```

### 2.3 Load-bearing contracts

- `tools/manual_ir/model.py` owns the public schema version on the immutable
  envelope.
- `tools/manual_ir/validate.py` owns shape, identity, hash, ordering and asset
  union validation.
- `tools/manual_ir/serialize.py` is the only public file read boundary.
- `tools/manual_ir/builder.py` derives block IDs and hashes from decoded
  `ManualSource` blocks without reading source files.
- `tools/manual_ir/document.py` currently owns the HTML content-tree shape and
  whole-document-specific validation.
- `tools/web_document_source.py` reads each source page once, packages images
  by digest and builds the whole-document IR.
- `tools/web_document_ir.py` validates hashes and replays without reading RST
  or CSV.

The existing prepared-RST/IDML producer and its `manual-ir/v1` bytes are a
compatibility surface. Changing its default schema or hashes in this cut would
mix the neutral Web migration with the print handoff and is therefore rejected.

## 3. Schema Decision

### 3.1 Envelope versions

- `manual-ir/v1` remains supported and remains the default for existing
  prepared-RST, IDML and scoped Web component producers.
- `manual-ir/v2` uses the same envelope identities and hash rules, but permits
  whole-document `flow` blocks whose payloads are validated neutral nodes.
- The whole-document Web producer emits `manual-ir/v2` with
  `metadata.projection = whole-document-flow/v1`.
- `read_manual_ir()` validates and returns either version without silently
  upgrading, rehashing or rewriting the file.
- The whole-document consumer accepts both the existing v1
  `whole-document-content/v1` projection and the new v2 projection. The v1
  adapter converts its legacy tree in memory before rendering; newly written
  whole-document files never use `document_content`.

This dual-read/single-write transition makes rollback explicit and prevents a
flag day across IDML, layout plans and historical build artifacts.

### 3.2 Neutral flow node

Each top-level document node becomes one `flow` block. Its payload has
`schema_version = manual-flow/v1`, a renderer-neutral `kind`, semantic fields,
ordered `children`, and an optional `presentation` object.

The initial vocabulary covers the complete finite source vocabulary already
accepted by the whole-document adapter:

- structure: `section`, `group`, `paragraph`, `heading`, `list`, `list_item`,
  `definition_list`, `definition_term`, `definition_description`, `quote`;
- tables: `table`, `table_head`, `table_body`, `table_foot`, `table_row`,
  `table_cell`, `column_group`, `column`;
- media: `figure`, `caption`, `image`;
- rich text: `text`, `inline_group`, `strong`, `emphasis`, `link`,
  `superscript`, `subscript`, `code`, `preformatted`, `small_text`,
  `abbreviation`, `line_break`, `thematic_break`;
- compatibility annotation: `comment`.

Semantics are stored outside renderer hints:

- headings carry `level`;
- lists carry `ordered`;
- groups carry a neutral structural `role` such as `container`, `aside`,
  `header` or `footer`;
- images carry `source` and `alt`;
- links carry `target`;
- anchored nodes carry `anchor`;
- table cells carry `header`, `row_span`, `column_span` and `scope` when
  present;
- accessibility-hidden nodes carry `hidden`.

### 3.3 Presentation hints

CSS classes, inline styles and residual HTML attributes live only under:

```json
{
  "presentation": {
    "html": {
      "attributes": {
        "class": ["..."],
        "style": "..."
      }
    }
  }
}
```

No HTML tag is serialized. The Web adapter selects the tag from neutral
`kind`, `level`, `header`, `ordered` and `role`, then applies the optional
attributes. Semantic fields always win if a legacy hint attempts to supply
`src`, `href`, `id`, span/scope or accessibility keys.

Presentation hints remain necessary for byte-compatible Web transformation
during the migration. Other renderers can ignore the whole object and still
recover document order, text hierarchy, links, tables and images. Later
component cuts remove class-dependent interpretation for the registered
complex shapes.

### 3.4 Assets and hashes

- Asset references continue to come from semantic `image.source` fields and
  ComponentSpec assets; presentation hints cannot introduce an asset.
- The ordered manual-level asset union and `metadata.asset_sha256` remain
  mandatory for whole-document replay.
- Block hashes use the existing canonical `{kind, payload}` algorithm. A v2
  file therefore hashes neutral semantics and hints, not an unversioned DOM.
- A v1 file keeps its original hashes and is never rewritten during read or
  replay.

## 4. Implementation Plan

### Phase A — Characterization and v2 read contract

Files:

- `tests/test_manual_ir_read_contract.py`
- `tests/test_manual_ir_source.py`
- `tests/test_web_document_ir.py`

Safety net:

- existing v1 fixture hash and public consumers remain unchanged;
- valid v1 and v2 envelopes read successfully;
- unsupported versions, malformed neutral nodes and semantic/presentation
  conflicts fail with file/page/block context before output mutation.

### Phase B — Neutral flow codec

Files:

- new focused `tools/manual_ir/flow.py`
- `tools/manual_ir/document.py`
- `tools/manual_ir/__init__.py`

Safety net:

- every currently accepted HTML tag maps to exactly one neutral kind;
- semantic content survives even when all presentation hints are removed;
- HTML → neutral flow → HTML is stable for representative production markup;
- unknown nodes/fields do not disappear silently.

### Phase C — v2 production and dual replay

Files:

- `tools/manual_ir/model.py`
- `tools/manual_ir/source.py`
- `tools/manual_ir/builder.py`
- `tools/manual_ir/validate.py`
- `tools/manual_ir/serialize.py`
- `tools/web_document_source.py`
- `tools/web_document_ir.py`

Safety net:

- new whole-document builds contain only `flow` blocks and no serialized HTML
  tag/type tree;
- current v1 whole-document artifacts still replay;
- a moved package replays after the source pages are deleted;
- RST/CSV reads remain forbidden in a fresh replay process;
- asset deletion or digest changes fail before rendering.

### Phase D — Documentation and acceptance

Files to review/update:

- `README.md`
- `code-as-doc/optimization_project.md`
- `code-as-doc/dev/ir_document_closeout.md`
- `code-as-doc/build_doc_guide.md`
- `user-guide/hello_auto-doc.md`
- `code-as-doc/code_optimization_log.md`

The stable operator commands do not change. Documentation must distinguish
the completed neutral flow substrate from the still-pending ComponentSpec and
four-renderer adapter cuts.

## 5. Non-Goals For Cut 1

- Do not migrate the five existing ComponentSpecs into whole-document IR; that
  is cut 2.
- Do not add Operation, Warranty, LCD, troubleshooting, Symbols, App or
  reference-figure ComponentSpecs; those are cuts 3–5.
- Do not split `web_manual.json` into skeleton/target overlays; that is cut 6.
- Do not delete the v1 document adapter or other old DOM paths; retirement and
  anti-copy hard gates are cut 7 and require a separate explicit deletion
  decision.
- Do not change public `build.py` flags, phase2 schemas, dependencies, approved
  reference layouts or frozen composite assets.

## 6. Verification Ladder

Run in order and record the exact result:

1. `python3 -m ruff check build.py integrations tools tests scripts`
2. focused ManualIR/whole-document/component projection tests
3. `python3 -m unittest`
4. `python3 tools/check_maintainability_guardrails.py`
5. `python3 tools/check_doc_link_integrity.py`
6. `python3 build.py check --config configs/config.us-en.yaml --model JE-1000F --region US`
7. build a real JE-1000F/US Web package, verify v2-only flow blocks, then cold
   replay it with RST/CSV reads forbidden
8. compare v1 and v2 rendered fragments after normalizing only package-root
   file URIs; text, image count/order and transformed HTML must match

## 7. Exit Criteria

Cut 1 is complete only when:

1. new whole-document Web IR uses `manual-ir/v2` and `flow` blocks;
2. no HTML tag is serialized as semantic authority;
3. removing presentation hints preserves a renderable neutral document with
   headings, prose, lists, tables, links and images intact;
4. existing v1 ManualIR remains byte/hash-compatible and readable;
5. Web replay remains source-free and asset-hash-checked;
6. the full verification ladder is green and the PR records the evidence.

## 8. Local Acceptance Record

The implementation passed the complete ladder on 2026-09-05:

- full Ruff: pass;
- focused ManualIR/whole-document/component regressions: 90 tests pass;
- full unit suite: 3756 tests pass, 19 skipped;
- maintainability: 62 hotspot files pass, with the same six pre-existing stale
  language-literal baselines and no new finding;
- documentation integrity: 154 Markdown files and 1698 links checked, zero
  broken;
- `build.py check` passes for JE-1000F/US/en with the committed
  `tests/fixtures/phase2` snapshot. The first command without `--data-root`
  stopped before build because this isolated worktree has no local
  `data/phase2/Spec_Master.csv`; no validation was bypassed.

The real three-language JE-1000F/US acceptance reused the frozen prepared
bundle produced by merged PR #1058 and its matching `configs/config.us.yaml`:

```text
schema_version=manual-ir/v2
projection=whole-document-flow/v1
pages=49
blocks=353 (flow only)
assets=57
content_sha256=266e0ccb3541e57d23f6ba218f18c43c144103382d128a057b22cacbdeefc020
final_images=210
```

All serialized mappings were inspected recursively and contained no `type` or
`tag` key. Every page rendered after all presentation hints were stripped.
V2 replay matched the synthesized v1 compatibility projection exactly; it also
matched the pre-change v2 Web fragments after normalizing only the package-root
file URI. A cold process forbidding `.rst` and `.csv` reads reproduced the same
49 fragments, and the packaged-asset hash gate remained active. The machine
readable evidence is local-only at
`.tmp/manual-ir-v2-real-us-final-multilang/manual_ir_v2_acceptance.json`.
