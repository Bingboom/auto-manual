# Future Canonical Content Model

Updated: 2026-03-17

## 1. Role

This file describes the target canonical content model for the longer-term content platform.
It is a conceptual and strategic data-model note.

This file is not the current operational guide for the CSV files in this repo.
Current CSV semantics, placeholder rules, and review-sync behavior are maintained in [`../spec_master_user_guide.md`](../spec_master_user_guide.md).

## 2. Why This Document Exists

The current repository still builds from CSV snapshots.
That is operationally correct for today, but the long-term system should be modeled around stable content entities rather than around file formats.

This document exists to keep that future model explicit:

- so current CSV files do not become the accidental permanent architecture
- so future CMS or table exports can map into a stable build snapshot contract
- so multi-target content growth does not force uncontrolled template duplication

## 3. Canonical Entities

The future content platform should normalize around these entities.

### 3.1 Product Identity

Represents the identity of one build target.

Core fields:

- `model`
- `region`
- `language`
- `product_name`
- `product_short_name`
- `model_no`

### 3.2 Parameter Row

Represents a structured spec or parameter value.

Core properties:

- stable row key
- section membership
- localized values
- optional line ordering
- optional release applicability

### 3.3 Template Field

Represents a structured placeholder-backed value that templates can consume.

Core properties:

- stable field key
- rendered placeholder name
- localized value
- optional formatting variants

### 3.4 Content Block

Represents reusable prose or instructional content.

Core properties:

- stable block id
- localized text
- ordering
- page placement
- target applicability

### 3.5 Page Definition

Represents the composition contract for one page.

Core properties:

- stable page id
- page order
- template family
- included blocks or generators
- target applicability
- declared contract requirements

### 3.6 Asset Reference

Represents a managed asset dependency.

Core properties:

- stable asset id or path contract
- logical usage site
- target applicability
- bundle placement expectation

### 3.7 Release Snapshot

Represents the exported build snapshot consumed by the repo.

Core properties:

- snapshot timestamp
- source system revision
- exported data files
- target matrix coverage

## 4. Current CSV Snapshot Mapping

The current repo files should be treated as snapshots of the future model, not as the model itself.

| Current snapshot file | Closest canonical entity |
| --- | --- |
| `Spec_Master.csv` | Product Identity, Parameter Row, Template Field |
| `Spec_Footnotes.csv` | Parameter Row note metadata |
| `spec_titles.csv` | localized section metadata |
| `content_blocks.csv` | Content Block |
| `page_registry.csv` | Page Definition |

## 5. Canonical Invariants

The future model should keep these boundaries stable:

- identity is modeled separately from prose blocks
- target applicability is explicit, not implied by file naming
- page composition is modeled separately from text content
- exported build snapshots are versioned inputs to the build repo
- build outputs consume snapshots, not live editing systems

## 6. Planned Direction For Multi-Target Content

The long-term direction is to express applicability in structured data, not by cloning templates per region or model.

Expected direction:

- page-level applicability should live with page definitions
- block-level applicability should live with content records
- applicability should be normalized across `region`, `language`, `model`, and optional feature flags
- repo builds should continue consuming exported snapshots that already encode those scopes

## 7. Relationship To Current Repo Docs

- current CSV semantics: [`../spec_master_user_guide.md`](../spec_master_user_guide.md)
- current repository component map: [`Hello_Docs_Architecture.md`](Hello_Docs_Architecture.md)
- long-term platform direction: [`System Evolution Strategy.md`](System%20Evolution%20Strategy.md)
- current repo roadmap: [`../../optimization_project.md`](../optimization_project.md)

## 8. Next Review Trigger

Update this file when the intended canonical schema changes, when a new source system is introduced, or when exported snapshot boundaries change.
