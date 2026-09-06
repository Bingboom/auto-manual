# ManualIR Embedded Components — Discovery And Implementation Plan

Status: complete

Branch: `feat/manual-ir-embed-components`

Baseline: `f7a1be3d` (`#1059` merged)

Updated: 2026-09-05

## 1. Objective

Write the five already-registered ComponentSpec families directly into the
ordered whole-document ManualIR while preserving the current Web output,
packaged-asset integrity and historical replay contracts:

- `HB-CALLOUT-STRIP`;
- `HB-TABLE-SPEC`;
- `HB-SPECIAL-FCC`;
- `HB-SPECIAL-INBOX`;
- `HB-SPECIAL-OVERVIEW`.

The whole-document Web consumer must dispatch these embedded instances instead
of rediscovering their semantics from the reconstructed page DOM. Other
renderers must be able to enumerate the same ComponentSpecs in document order.

This is cut 2 of the seven-cut cross-renderer IR closure. It does not add the
remaining component families or split the presentation contract.

## 2. Discovery Report

### 2.1 Current path and duplicated work

The merged cut-1 path is:

```text
prepared RST
  -> neutral manual-flow/v1 nodes in manual-ir/v2
  -> flow_nodes_to_html
  -> transform_web_fragment
  -> scoped source projector reparses the DOM
  -> temporary manual-ir/v1
  -> scoped Web component consumer
```

The serialized document is renderer-neutral, but the five registered complex
components are absent. `project_manual_ir_components()` therefore cannot
consume the whole-document v2 file, and Web replay repeats semantic discovery.

### 2.2 Representative inventory

Existing frozen packages were decoded and each current source projector was
run against its governed source shape:

| Target | Callout | Spec | FCC | Inbox | Overview |
| --- | ---: | ---: | ---: | ---: | ---: |
| JE-1000F / US (EN/FR/ES) | 47 | 12 | 3 | 3 | 3 |
| JE-1000F / EU (EN/FR/ES/DE/IT) | 69 | 20 | 0 | 5 | 5 |
| JBP-2000B / JP (JA) | 4 | 4 | 0 | 1 | not this shape |

The JBP-JP overview is intentionally one localized finished illustration after
two source images and their duplicate labels are replaced. It is not the
two-section live Overview Web shape and must remain ordinary flow in this cut;
the later Reference Figure/carrier cut owns that finished-panel contract.

### 2.3 Ownership and ordering traps

- Callouts occur inside section flow, so page-level-only component blocks would
  flatten document hierarchy. The component carrier must be nestable.
- Inbox owns both its three-card table and adjacent TIP table. Some TIP tables
  also carry the generic callout class; Inbox claims them before Callout so one
  source node cannot create two semantic instances.
- A specification instance owns one declared H2 and its immediately following
  table. Notes and footnotes after the table remain ordinary flow.
- FCC owns all siblings after its H1. The heading remains ordinary document
  flow so navigation behavior stays unchanged.
- The JE Overview instance owns both ordered view sections while its H1 remains
  ordinary flow. Geometry continues to resolve by exact model and region.
- Component assets disappear from the ordinary DOM after extraction, so they
  must be packaged and rebound before the IR asset union is assembled.
- Semantic extraction must happen before any finished-illustration replacement
  removes source labels. Final asset binding happens after replacement policy
  is known.

## 3. Schema Decision

### 3.1 Versioned ordered carrier

- `manual-ir/v2` remains the envelope.
- Historical `whole-document-flow/v1` plus `manual-flow/v1` remain readable and
  replay through the cut-1 compatibility path.
- New whole-document producers write `whole-document-components/v1` using
  `manual-flow/v2` roots.
- `manual-flow/v2` adds one renderer-neutral `component` node. It can occur
  wherever an ordinary flow node can occur, including inside a section.
- A component node contains exactly one validated `component-spec/v1` mapping
  and optional neutral carrier flow for source-authored rich markup not modeled
  by the ComponentSpec slots. It does not serialize an HTML tag or selector as
  semantic authority.

### 3.2 Semantics and carrier

ComponentSpec is authoritative for component identity, variant, localized
slots, asset roles and token roles. Optional carrier flow preserves only
authored markup that the current ComponentSpec does not fully model, such as
links, emphasis or image attributes. Each component-specific adapter validates
carrier agreement with the semantic slots before rendering.

The component node is a dispatch point, not a DOM recognition hint. Web replay
selects the registered adapter from `component_id`. Unknown, duplicate,
malformed or unregistered instances fail before output mutation.

### 3.3 Assets

- Every ComponentSpec asset role is rebound to its package-relative frozen
  asset before serialization.
- Carrier images are rebound through the same package function.
- `ManualIR.asset_refs` contains component assets in first document-use order,
  and `metadata.asset_sha256` remains the file-integrity authority.
- Presentation attributes cannot introduce component assets.

## 4. Implementation Phases

### Phase A — schema and traversal safety net

Files:

- `tools/manual_ir/flow.py`;
- new `tools/manual_ir/components.py`;
- `tools/manual_ir/validate.py` and `tools/manual_ir/document.py`;
- `tests/test_manual_ir_flow.py` and `tests/test_manual_ir_components.py`.

Prove v1/v2 dual read, nested document order, strict ComponentSpec validation,
asset union and direct `project_manual_ir_components()` traversal.

### Phase B — source extraction and ownership

Files:

- new focused whole-document component source module(s);
- existing five source projectors only where a reusable decode boundary is
  required;
- `tools/web_document_source.py`;
- focused source and whole-document tests.

Extract in ownership order Overview/FCC/Inbox/Spec/Callout, insert semantic
component nodes at the first claimed position, reject overlapping or
non-contiguous claims and package every claimed asset.

### Phase C — direct Web replay

Files:

- new whole-document component replay/dispatch module;
- focused refactors in the five existing Web component consumers;
- `tools/web_document_ir.py` and `tools/web_presentation.py`.

Render embedded instances directly and mark those families as already
resolved so the remaining presentation pass cannot invoke their DOM source
projectors. Retain the old path only for v1 and cut-1 v2 packages.

### Phase D — documentation and acceptance

Update the owning ManualIR and operator documents. Run exact fragment parity,
cold replay with RST/CSV reads forbidden, component inventory checks and the
full repository verification ladder.

## 5. Non-Goals

- Do not add Operation, Warranty, LCD, troubleshooting, Symbols, App or
  Reference Figure ComponentSpecs; cuts 3–5 own those families.
- Do not split `web_manual.json`; cut 6 owns presentation inheritance.
- Do not retire the compatibility DOM source projectors; cut 7 owns removal
  after every replacement adapter has representative acceptance evidence.
- Do not change public CLI flags, dependencies, phase2/Base schemas, workflows,
  approved reference-layout geometry or frozen illustration content.

## 6. Verification Ladder

1. Ruff and focused schema/source/replay tests.
2. All ManualIR and five-component tests.
3. Full `python3 -m unittest`.
4. Maintainability and documentation-link guardrails.
5. JE-1000F/US fixture `build.py check`.
6. Real JE-1000F/US, JE-1000F/EU and JBP-2000B/JP Web packages.
7. Exact old/new fragment comparison with only package-root file URIs
   normalized.
8. Cold replay with source RST/CSV reads forbidden and packaged asset hashes
   enforced.
9. Component inventory, text order, image order, desktop/mobile screenshots
   and all image loads checked on representative targets.

## 7. Exit Criteria

Cut 2 is complete only when:

1. all eligible instances of the five existing families are serialized once in
   document order;
2. nested components preserve section hierarchy and Inbox TIP is not duplicated;
3. `project_manual_ir_components()` returns embedded specs without DOM parsing;
4. new Web replay does not call any of the five source projectors;
5. old v1 and cut-1 v2 packages still replay;
6. component and ordinary-flow assets remain complete, ordered and hash-checked;
7. representative rendered HTML, text and image order match the frozen baseline;
8. the full verification ladder is green and the PR records actual evidence.

## 8. Completion Record (2026-09-05)

The new producer writes `whole-document-components/v1` with `manual-flow/v2`
roots. The five registered families are embedded at their original document
positions, and the whole-document Web replay dispatches those instances without
running their DOM source projectors. Historical `manual-ir/v1` and cut-1
`whole-document-flow/v1` packages remain readable through their compatibility
paths.

Acceptance covered real frozen Web packages for JE-1000F/US, JE-1000F/EU and
JBP-2000B/JP:

| Target | Pages | Embedded ComponentSpecs |
| --- | ---: | ---: |
| JE-1000F / US | 49 | 66 |
| JE-1000F / EU | 76 | 99 |
| JBP-2000B / JP | 12 | 9 |

The final family totals were Callout 45/FCC 3/Inbox 3/Overview 3/Spec 12 for
US, Callout 69/Inbox 5/Overview 5/Spec 20 for EU, and Callout 4/Inbox 1/Spec 4
for JBP-JP. Inbox TIP ownership therefore produces no duplicate Callout.

Each package replayed with all five source projectors replaced by failing test
doubles. Component and carrier assets remained in the ordered asset union and
passed package SHA-256 checks. A detached cut-1 build of the same sources was
compared page by page; all three targets had zero HTML fragment differences
after normalizing only package-root file URIs. The JBP-JP comparison also used
its rebuilt `web-illustrations/v1` manifest and retained the localized finished
Overview panel instead of falling back to textless source figures.

Focused validation passed 120 tests. The final repository ladder passed 3761
tests (19 skipped), full Ruff, 62 hotspot maintainability checks, documentation
link integrity and the JE-1000F/US fixture-backed `build.py check`.
