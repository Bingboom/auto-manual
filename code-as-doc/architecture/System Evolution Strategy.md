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
and an explicit applicability per governed item) are maintained from confirmed
commonality baselines with explicit, necessary differences. Shared changes are
made once at their authority and reach applicable delivery targets and surfaces
verifiably. Governed feedback returns through authorized review to improve the
content and the governance rules themselves. The aim is to reduce repeated
editing and repeated judgment; the reuse and propagation constraints are in §6.

Reusable templates, skeletons, shared components, approved copy, terminology and
translation memory are governed knowledge assets, not merely inputs to a build
engine. They should help documentation specialists and agents understand how a
manual is organized, how approved content is expressed, and under which
conditions reuse is appropriate. Template-assisted drafting and structured
builds are complementary paths; neither is mandatory for every target.
Applicability, provenance, approval and target-specific verification take
precedence over similarity. Template guidance is a strategic direction, not a
claim that automated applicability assessment has been delivered.

The strategic priority is to govern approved originals and reusable assets, retain authoritative provenance and version applicability, and make selected knowledge useful to people and agents. Structured generation is an optional production route, not a prerequisite for admitting or publishing existing manuals. Selective extraction from approved editions serves concrete queries and maintenance decisions; extracted facts remain source-linked and unapproved as new authority until verified by an accountable role. Hypothetical cross-product bulk changes alone must not justify new schema, skeleton or assembly investment.

Writing is the main production route. In the private document workbench
(Hello-Docs-Review), agents draft with the engineering infrastructure, governed
data, templates and corpus, and people review the drafts; automated assembly from
data and templates is used on demand. Workbench drafting and its private review
site exist; promoting an approved draft into Hello-Docs publication and
traceability as an approved original is planned, not implemented. The repository
roles are mapped in [the two-plane map](../../user-guide/two_plane_map.md).

The five strategic objectives apply across content classes. Governance depth
is selective: tier-1 content (warning, safety and compliance text and spec
values) requires explicit item-level records and accountable review; other
content defaults to light metadata. Lightweight governance still requires
confirmed applicability for shared maintenance and evidence for propagation.
Record granularity follows risk, reuse value and total maintenance cost; this
does not require a registry entry for every sentence or immediate migration of
existing content.

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
   unknown boundary is visible and its resolution is measured within a
   declared scope, alongside the cost of maintaining those records.

The overall lifecycle includes workbench writing and review, approved-source intake, authority and version governance, publication, selective extraction and consumption, and governed feedback. The production spine below remains valid for builds but is not the only entry route or the entire platform architecture.

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

- the CMS owns the content classes assigned to it by the allocation rule
- the repository owns declared Git-native sources as well as deterministic
  build, validation, and publishing tooling
- every release is traceable to a frozen snapshot and a build record

Stage 3 investment is demand-led: retain approved-original intake and existing templates, and expand structured assembly only for a demonstrated high-value use case with clear applicability, authority, maintenance ownership and acceptance. Useful knowledge extraction does not require migrating entire manual bodies to tables. This is a prioritization principle, not an assertion that all extraction or feedback capabilities have passed acceptance.

Stage 3 is a deliberate hybrid, not total structuralization. CMS ownership applies
to the content classes that benefit from structured governance — spec values,
high-reuse short copy, and tabular/reference content. Layout and page structure,
stable long-form and compliance prose, and environment differences (legal
identity, contacts, URLs, marketplaces) are deliberately owned by repository
templates and config, which are themselves versioned build inputs. The goal is to
eliminate template forks — the same page cloned per language or region — and to
govern reusable content; it is not to move every paragraph into a table. Which
class each piece of content belongs to is decided by an explicit content-truth
allocation rule, not case by case. These table/template allocations coexist
with approved native-source production: a target can retain its declared
original or source-designated Manual IR, with an explicit revision and editing
surface, and freeze new input packages for release. A sealed package is an
immutable version, not an editing surface; where a Git-held source package is
the declared editing surface, a reviewed correction re-locks it as a new
version with recorded lineage. Generated IR remains a derivative unless
explicitly designated as the source. This route does not
require migration into tables or templates to count as governed. See the
allocation rule and its route boundary in
[`Long_Form_Content_Block_Design.md`](Long_Form_Content_Block_Design.md).

## 6. Stable Architectural Principles

Each principle names what it forbids; a principle that forbids nothing is not
one.

Production principles:

1. One authority per content item; structure is selective. Each governed item
   has one declared content authority and version, allocated by the
   content-truth rule, with an explicit editing surface for revisions. Tables,
   repository templates and config, and approved native originals can own
   content; source-designated Manual IR can do so, but generated IR cannot
   become an authority merely because it carries the same content. Sealed
   snapshots and release packages remain immutable; corrections use the declared
   editing surface (which may be a Git-held source package, re-locked by a
   reviewed change) and produce a new version with recorded lineage. Forbidden:
   a second editable authority such as a machine JSON, an operations table or a
   parallel CMS; changing a sealed version in place; moving prose into tables
   for completeness; treating degree of structure as maturity. The enemy is
   uncontrolled template forks, not templates or versioned derivatives.
2. Build inputs are explicit and reproducible. Forbidden: implicit environment
   and releases that cannot be rebuilt.
3. Assembly rules are declared, not inferred. Forbidden: page selection that
   lives in tribal knowledge.

Content-relation principles:

4. Share by confirmed relation; vary explicitly. Shared maintenance across
   targets requires a relation whose identity, applicability and reason are
   recorded and confirmed by the accountable role, at the governance depth
   appropriate to its risk and reuse value (§3). Textual similarity is not
   equivalence. A governed difference records its reason and the baseline
   identity and version it diverges from; a copied file alone is not that
   record. When the baseline or applicability conditions change, the affected
   relation must be revalidated before it authorizes propagation. Forbidden:
   merging because text matches; treating a target change as sufficient reason
   for an untracked fork; adding variation mechanisms without a versioned
   baseline.
5. Change at the source; propagate by evidence. A shared change is made once
   at its authority. Before approval, impact analysis declares its target
   inventory and scope, lists affected targets from confirmed relations, and
   exposes missing, unknown, stale or conflicting relations as unresolved,
   never as unaffected. Confirmed targets may proceed within an explicitly
   approved scope while exclusions and unresolved targets remain visible;
   propagation is not complete for a scope with unresolved targets. Relation
   declared, impact identified, change approved, target built, published and
   verified online are separate records with separate evidence; review and
   release remain traceable, as today. Forbidden: automatic propagation along
   unconfirmed or invalidated relations; treating an incomplete inventory as
   complete coverage; marking a target updated because its baseline changed;
   treating a library fix as applied to frozen editions that were not rebuilt.
6. Feedback is governed and two-level. Observations are candidates, never
   facts; machines propose and verify, people decide, and approval does not
   replace verification. Content corrections return through the editing
   surface their authority declares. Changes to the governance model itself
   (identities, applicability vocabulary, allocation rule, relation status) are
   reviewed changes with cited evidence. Observation and knowledge tools do not
   write content authorities. Authorized change-execution tools may apply a
   change that a person with the accountable role approved (recorded with the
   approver and date), through its declared editing surface, within the approved
   scope and with an audit trail and read-back or rebuild verification.
   Forbidden: observation or knowledge layers writing an authority directly;
   automated writes of a change that no accountable person approved, or outside
   the approved scope; AI judging regulatory applicability; a findings ledger
   copying approved wording or becoming a wording authority.

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
- [`dev/manual_revitalization_execution.md`](../dev/manual_revitalization_execution.md) is the execution ledger: per-item state, dependencies and acceptance evidence.
- [`manual_production_revitalization_plan.md`](../manual_production_revitalization_plan.md) applies these boundaries to stock-manual delivery.
- [`user-guide/two_plane_map.md`](../../user-guide/two_plane_map.md) records current repository/Base ownership.
- [`code-as-doc/build_doc_guide.md`](../build_doc_guide.md) describes current maintainer behavior.
- [`user-guide/hello_auto-doc.md`](../../user-guide/hello_auto-doc.md) describes the current user workflow.

Adopting this strategy does not start implementation, reopen deferred work or
relax existing execution gates and governance decisions. Those remain binding
until explicitly revised in their owning documents; new capabilities require
scoped work and acceptance evidence in the execution ledger.

## 9. Next Review Trigger

Review this file only when:

- the target layer model changes
- the intended end-state ownership between CMS and repository changes
- the evolution stage model changes
- a stable architectural principle must be revised
- a feedback level or the relation status model changes

## 10. One-Sentence Summary

Hello-Docs should evolve into a content lifecycle system in which trusted
content and its relations are maintained from confirmed commonality baselines
with explicit, necessary differences, reach applicable delivery targets and
surfaces verifiably, and improve through governed feedback, on the same
governance, snapshot, assembly, build, review and release boundaries it has
today.
