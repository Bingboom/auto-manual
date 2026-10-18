# System Evolution Strategy

Updated: 2026-10-18

## 1. Role

This file is the long-term strategy document for Hello-Docs.

Use it to define:

- the long-term system direction
- the target architecture shape
- the stable layer boundaries
- the evolution stages
- the architectural principles that should survive implementation changes

Do not use this file as the repo task list or optimization backlog.
Do not append repo history here either — for how the system actually got to
its current shape, use
[`system_evolution_history.md`](system_evolution_history.md).

For repo-level execution planning, use:

- [`optimization_project.md`](../optimization_project.md)

For current workflows, use:

- [`code-as-doc/build_doc_guide.md`](../build_doc_guide.md)
- [`user-guide/hello_auto-doc.md`](../../user-guide/hello_auto-doc.md)

## 2. Stability Rules

Update this file only when one of these changes:

1. the long-term direction changes
2. the target layer model changes
3. the role split between CMS, snapshot, assembly, build, and release changes
4. the intended evolution stages change
5. a principle that should remain stable across repo refactors changes
6. the content-relation principles or the lifecycle framing change

Do not update this file for:

- ordinary repo cleanup
- current workstream reprioritization
- command-level changes
- implementation detail refactors

## 3. Vision and North Star

Vision. Product content should be a maintained knowledge asset: trusted,
reusable, consumable by people and by machines, and improved by what delivery
and use reveal, rather than a set of files delivered once.

North Star (end state). Hello-Docs is the content lifecycle system for that
asset: trusted content and its relations (one authority, an explicit identity
and an explicit applicability per governed item) are maintained once, reach
every delivery target and surface verifiably, and improve through governed
feedback that returns, through authorized review, to the content and to the
governance rules themselves. How commonality is shared and how change
propagates are principles (§6), not part of this statement.

Strategic objectives (the end state holds when all five are true for tier-1
content: warning, safety and compliance text and spec values; other content
carries light metadata only):

1. Trusted content: authority, identity, applicability and approved version
   are explicit for every target.
2. Maintain once: a shared change is made in one place and its affected
   targets are listed completely.
3. Verifiable propagation: declared, impact-identified, approved, built,
   published and verified are recorded separately per change and per target;
   historical releases keep their version meaning.
4. Same-source surfaces: Web, Word, PDF, IDML and machine-readable surfaces
   are derivatives of one approved production, never a second authority.
5. Governed evolution: observations become candidates, people decide, and
   confirmed decisions update content, relations and governance rules; the
   unknown boundary shrinks measurably.

The production spine is unchanged:

```text
Content Governance -> Snapshot -> Page Assembly -> Build/Render -> Release/Traceability
```

It is one part of a two-level lifecycle (§4.6):

```text
Content Governance -> Content Production -> Delivery & Consumption
    -> Content Intelligence -> Governed Feedback -> Content Governance
```

In practical terms:

```text
governed tables | Git-native originals | approved frozen sources
    -> frozen snapshot or source package
    -> page assembly / Shared IR
    -> RST / MyST bundle
    -> HTML / Word / PDF / IDML + machine corpus
    -> review, diff, publish, deployment receipt, release records
    -> observation, findings, authorized change
```

## 4. Fixed Layer Model

The long-term system has five layers.

### 4.1 Content Governance Layer

Examples:

- CMS
- multidimensional tables
- workflow tracking

Responsibility:

- manage multilingual content
- manage product applicability
- manage workflow state
- enforce structured content governance

### 4.2 Snapshot Layer

Examples:

- exported CSV / JSON snapshots
- frozen source packages (approved PDF / AI originals with input hashes)
- Manual IR packages

Responsibility:

- freeze build inputs
- preserve reproducibility
- make reviews and releases auditable

### 4.3 Page Assembly Layer

Examples:

- `page_registry`, template mapping, placeholder contracts
- skeleton blueprints, region profiles and product plans
- Shared IR and component contracts

Responsibility:

- convert structured data into page-ready content
- declare content requirements
- keep target selection explicit

### 4.4 Build And Render Layer

Examples:

- RST generation
- Sphinx
- HTML / Word / PDF export

Responsibility:

- build deterministic output bundles
- render release formats
- handle layout and styling

### 4.5 Release And Traceability Layer

Examples:

- review bundles
- diff reports
- publish flow
- release manifests

Responsibility:

- support review workflows
- expose change history
- create release records
- preserve build accountability

<a id="46-cross-layer-operations-feedback-and-shared-intake"></a>

### 4.6 Lifecycle: Intake, Consumption and Governed Feedback

The five production layers are the deterministic spine of a two-level
lifecycle. Content Governance is layer 4.1 and, as a planned target state, a
registry of content identities, applicability statements, baseline-derivative
links and relation status (its delivery status is to be recorded only in the
[execution ledger](../dev/manual_revitalization_execution.md) before any of it
is built, not in this file). Content Production is layers 4.2 to 4.5.
Delivery & Consumption is the published human and machine surfaces (§4.7).
Content Intelligence is read-only observation over published editions: corpus,
relations, findings. Governed Feedback returns corrections through the editing
surface each authority declares; returning confirmed relations and rule
changes to governance is a planned target state, not a delivered capability.
None of these stages adds a build engine or a content authority. The first
feedback level uses correction paths that exist today; the second, which is to
correct the governance model itself, has no rule or carrier yet, is not
claimed here, and is to be recorded only in the [execution
ledger](../dev/manual_revitalization_execution.md) before any of it is built.
In both, an observation stays a candidate until a person with the accountable
role decides.

Intake, release and feedback boundaries:

- Governed table/template inputs and approved AI/PDF intake both freeze their
  content, structure, assets, configuration and source authority before assembly.
  Stock intake does not require copying every paragraph into live tables first;
  each target declares its current authoritative source and version.
- Shared IR owns document semantics, component instances and asset references.
  Web and fixed-page renderers own their layout; adapter conformance is distinct
  from native-format pagination, font and delivery acceptance.
- Queue and authorized Git-only inputs converge on the reviewed frozen release
  outlet. Input provenance remains distinct; Git-only delivery does not imply
  queue completion or permission to write online source/catalog records.
- Review approval, release-PR merge, deployment, online verification, archive and
  directory synchronization retain distinct evidence. An operations table is a
  derived view with protected human fields, not the build source or release ledger.
- A stable latest-version entry may change its target through a recorded mapping;
  version-bound historical links retain their version meaning. Feedback returns
  through the applicable review/template/source editing surface before release.

Current repository/Base ownership stays in the
[two-plane map](../../user-guide/two_plane_map.md); hosting choices and task dates
belong in the operating contract and roadmap, not in these stable invariants.

### 4.7 Human, Agent and Enterprise Access

Access layers connect people, AI clients and enterprise systems to the same
content infrastructure; they do not add production engines or content authorities.
The shared platform includes governed content, reuse, professional file processing
and content queries. Document production is one capability path within this platform,
not the boundary of the platform itself.

- Human access uses Portal, Workspace and existing Bot workflows to read,
  submit work and review. Agent skills and bounded manual-query interfaces
  already exist. Their coverage and approval rules remain capability-specific.
- Planned enterprise integration references PLM/ERP product, SKU, BOM, material
  and lifecycle records through synchronization and field mapping into the
  existing business tables. These tables support product information, content
  modules, specifications, multilingual content and business maintenance/review;
  validation, normalization and traceable snapshots connect them to production.
  Content Authority continues to resolve facts from tables, Git-native originals
  and approved assets before Assembly, Renderers and Publish.
  Enterprise systems remain authoritative for their records;
  document production must not maintain a competing copy of enterprise master data.
- Planned MCP access is a thin protocol adapter:
  `AI Client → MCP → Capability Interface → Core / Domain Services`.
  Translation, artwork processing and manual builds remain independent of MCP.
  Initial exposure candidates are TM lookup, terminology, pretranslation,
  translation QA and manual context. Later exposure of existing artwork/PDF/build skills requires its
  own scope and acceptance; a candidate capability is not a maturity claim.
- Formal artwork changes retain `Inspect → Compare → Propose Patch → Human
  Approval → Apply → Verify`. AI suggestions do not become business facts or
  bypass approval, and approval does not replace verification.
- Human and machine surfaces derive from governed production. Current machine
  corpus uses published HTML compatibility; further shared-IR consumption is a
  future extension, not a claim that all manuals are IR-first.
- Product Knowledge and Market Policy are reading/application surfaces with
  explicit source and verification boundaries, not universal SSOT. Knowledge
  feedback returns through human review and the declared editing surface.

Current/planned access and the undated next directions are presented from the
existing [history summary](system_evolution_history.md#7-rtd-同源展示摘要).
Adding a diagram or planned adapter does not authorize implementation, enterprise
data writes or formal file modification.

### 4.8 Capability Boundary

Hello-Docs is: the authority-and-derivation system for product documentation
content; a deterministic, reproducible production line; the origin of
same-source human and machine surfaces; and the governed entry point for
feedback. As a planned target state, it is also the registry of content
identities, applicability statements, baseline-derivative links, change
records and relation status; that registry is not claimed here, and its status
is to be recorded only in the [execution
ledger](../dev/manual_revitalization_execution.md) before any of it is built.

Hello-Docs is not: enterprise master data (PLM, ERP and business tables remain
authoritative for their records); a judge of regulatory or certification
applicability; a general CMS, knowledge graph or semantic search platform; the
quality owner of a customer-facing answer product; a general AI importer; or an
analytics and event platform. Those are suppliers, consumers or separate
decisions with their own owners.

## 5. Evolution Stages

### Stage 1: Repository-Driven System

The repository temporarily acts as both:

- build engine
- content editing center

Purpose:

- discover stable rules through real manual production
- stabilize placeholders, contracts, page assembly rules, and review flow

### Stage 2: Hybrid CMS + Build Pipeline

Structured content editing moves gradually into a CMS or multidimensional table system.

In this stage:

- the CMS manages structured content and workflow state
- the repository still owns templates, assembly, validation, rendering, and release tooling
- builds consume exported snapshots rather than live content

### Stage 3: Governed Content Infrastructure (hybrid)

In the target end state:

- the CMS becomes the content source of truth for governed content classes
- the repository becomes a deterministic build, validation, and publishing engine
- every release is traceable to a frozen snapshot and a build record

Stage 3 is a deliberate hybrid, not total structuralization. "Source of truth"
applies to the content classes that benefit from governance — spec values,
high-reuse short copy, and tabular/reference content. Layout and page structure,
stable long-form and compliance prose, and environment differences (legal
identity, contacts, URLs, marketplaces) are deliberately owned by repository
templates and config, which are themselves versioned build inputs. The goal is to
eliminate template forks — the same page cloned per language or region — and to
govern reusable content; it is not to move every paragraph into a table. Which
class each piece of content belongs to is decided by an explicit content-truth
allocation rule, not case by case. See the allocation rule in
[`Long_Form_Content_Block_Design.md`](Long_Form_Content_Block_Design.md).

## 6. Stable Architectural Principles

Each principle names what it forbids; a principle that forbids nothing is not
one.

Production principles:

1. One authority per content item; structure is selective. Each governed item
   has exactly one editable authority at a time (a table, a repository
   template, a frozen source package or Shared IR), allocated by the
   content-truth rule. Forbidden: a second editable copy such as a machine
   JSON, an operations table or a parallel CMS; moving prose into tables for
   completeness; treating degree of structure as maturity. The enemy is
   forks, not templates.
2. Build inputs are explicit and reproducible. Forbidden: implicit environment
   and releases that cannot be rebuilt.
3. Assembly rules are declared, not inferred. Forbidden: page selection that
   lives in tribal knowledge.

Content-relation principles:

4. Share by confirmed relation; vary explicitly. Tier-1 content is reused
   across targets only along a relation whose identity, applicability and
   reason are recorded and confirmed by the accountable role. Textual
   similarity is not equivalence. A difference is recorded with its reason,
   not expressed by copying a file. Forbidden: merging because text matches;
   forking because one target changed; adding variation mechanisms that do not
   name the baseline they diverge from.
5. Change at the source; propagate by evidence. A shared change is made once
   at its authority; affected targets are listed from declared relations
   before approval; relation declared, impact identified, change approved,
   target built, published and verified online are separate records with
   separate evidence; review and release remain traceable, as today.
   Forbidden: automatic propagation along unconfirmed relations; marking a
   target updated because its baseline changed; treating a library fix as
   applied to frozen editions that were not rebuilt.
6. Feedback is governed and two-level. Observations are candidates, never
   facts; machines propose and verify, people decide, and approval does not
   replace verification. Content corrections return through the editing
   surface their authority declares. Changes to the governance model itself
   (identities, applicability vocabulary, allocation rule, relation status) are
   reviewed changes with cited evidence. Forbidden: any machine or knowledge
   layer writing an authority; AI judging regulatory applicability; a findings
   ledger holding content text.

## 7. Strategic Invariants

These are the boundaries that should not be casually broken.

- Content governance is not the same thing as build execution.
- Snapshot data is not the same thing as live editable content.
- Page assembly is not the same thing as rendering.
- Review and release are not side effects; they are first-class system concerns.
- Current repo workflows may evolve, but the system should not collapse back into a single undifferentiated script layer.
- Layer responsibilities should become clearer over time, not more blended.
- Machine and knowledge surfaces are consumers of approved content, never
  authorities.

## 8. Relationship To Other Documents

- This file defines long-term direction and stable architecture boundaries.
- [`platform_evolution_roadmap.md`](platform_evolution_roadmap.md) holds the platform maturity assessment, capacity-driven phases and exit criteria.
- [`system_evolution_history.md`](system_evolution_history.md) records how the system reached its current shape.
- [`optimization_project.md`](../optimization_project.md) tracks repo-level execution and current optimization priorities.
- [`manual_production_revitalization_plan.md`](../manual_production_revitalization_plan.md) applies these boundaries to stock-manual delivery.
- [`user-guide/two_plane_map.md`](../../user-guide/two_plane_map.md) records current repository/Base ownership.
- [`code-as-doc/build_doc_guide.md`](../build_doc_guide.md) describes current maintainer behavior.
- [`user-guide/hello_auto-doc.md`](../../user-guide/hello_auto-doc.md) describes the current user workflow.

## 9. Next Review Trigger

Review this file only when:

- the target layer model changes
- the intended end-state ownership between CMS and repository changes
- the evolution stage model changes
- a stable architectural principle must be revised
- a feedback level or the relation status model changes

## 10. One-Sentence Summary

Hello-Docs should evolve into a content lifecycle system in which trusted
content and its relations are maintained once, reach every delivery target and
surface verifiably, and improve through governed feedback, on the same
governance, snapshot, assembly, build, review and release boundaries it has
today.
