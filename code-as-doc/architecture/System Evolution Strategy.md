# System Evolution Strategy

Updated: 2026-03-17

## 1. Role

This file is the long-term strategy document for Hello-Docs.

Use it to define:

- the long-term system direction
- the target architecture shape
- the stable layer boundaries
- the evolution stages
- the architectural principles that should survive implementation changes

Do not use this file as the repo task list or optimization backlog.

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

Do not update this file for:

- ordinary repo cleanup
- current workstream reprioritization
- command-level changes
- implementation detail refactors

## 3. North Star

Hello-Docs should evolve from a repository-centered manual build system into a content infrastructure system with:

- structured content governance
- reproducible snapshots
- explicit page assembly
- deterministic build and rendering
- traceable review and release workflows

The target flow is:

```text
Content Governance -> Snapshot -> Page Assembly -> Build/Render -> Release/Traceability
```

In practical terms:

```text
CMS / Multidimensional Tables
        -> exported snapshot
        -> page assembly
        -> RST bundle
        -> HTML / Word / PDF
        -> review, diff, publish, release records
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

- exported CSV snapshots
- exported JSON snapshots

Responsibility:

- freeze build inputs
- preserve reproducibility
- make reviews and releases auditable

### 4.3 Page Assembly Layer

Examples:

- `page_registry`
- `content_blocks`
- template mapping
- contracts

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

### Stage 3: CMS-Driven Content Infrastructure

In the target end state:

- the CMS becomes the content source of truth
- the repository becomes a deterministic build, validation, and publishing engine
- every release is traceable to a frozen snapshot and a build record

## 6. Stable Architectural Principles

These principles should remain true even as repo implementation changes.

1. Content truth should move toward structured governance, not toward more template forks.
2. Build inputs should become more explicit and more reproducible over time.
3. Page assembly rules should be declared, not inferred from tribal knowledge.
4. Review and release must remain traceable.
5. Layer responsibilities should become clearer over time, not more blended.

## 7. Strategic Invariants

These are the boundaries that should not be casually broken.

- Content governance is not the same thing as build execution.
- Snapshot data is not the same thing as live editable content.
- Page assembly is not the same thing as rendering.
- Review and release are not side effects; they are first-class system concerns.
- Current repo workflows may evolve, but the system should not collapse back into a single undifferentiated script layer.

## 8. Relationship To Other Documents

- This file defines long-term direction and stable architecture boundaries.
- [`optimization_project.md`](../optimization_project.md) tracks repo-level execution and current optimization priorities.
- [`code-as-doc/build_doc_guide.md`](../build_doc_guide.md) describes current maintainer behavior.
- [`user-guide/hello_auto-doc.md`](../../user-guide/hello_auto-doc.md) describes the current user workflow.

## 9. Next Review Trigger

Review this file only when:

- the target layer model changes
- the intended end-state ownership between CMS and repository changes
- the evolution stage model changes
- a stable architectural principle must be revised

## 10. One-Sentence Summary

Hello-Docs should evolve into a snapshot-driven content infrastructure with clear governance, assembly, build, review, and release boundaries.
