# Development Log

Updated: 2026-03-30

This file is an archive summary of earlier development phases.
It is historical context, not the current operating guide.

For current behavior, use:

- [`code-as-doc/build_doc_guide.md`](../build_doc_guide.md)
- [`code-as-doc/code_style_guide.md`](../code_style_guide.md)
- [`user-guide/hello_auto-doc.md`](../../user-guide/hello_auto-doc.md)

## 1. Historical Milestone: 2026-03-01

Key themes from that stage:

- repository cleanup around the original phase1 flow
- spec page integration into the renderer chain
- [`layout_params.csv`](../../data/layout_params.csv) expansion and tuning
- PDF-focused output verification
- early testing and report collection

Important note:

- that stage still used older mental models such as direct [`docs/generated/...`](../../docs) emphasis
- those references are historical only and should not override the current review-first flow

## 2. Historical Milestone: 2026-03-05

Key themes from that stage:

- continued stabilization of the phase1 build path
- deeper spec renderer integration
- earlier experiments around SKU-aware behavior
- font and platform compatibility work

Important note:

- old `--sku` and `default_sku` assumptions are not part of the current primary flow
- current target identity is based on `model + region` and shared config families

## 3. Historical Milestone: 2026-03-30

This branch-sized PR was a large consolidation pass from `origin/main` to the current
US/JP-focused workflow. The main changes were:

- output pipeline convergence:
  HTML preview styling was cleaned up, fake paging and extra language chrome were removed,
  Vercel review preview behavior was aligned with local output, and the Word path was
  tightened around the shared Word-template flow
- source data and spec model cleanup:
  `Spec_Master.csv` and related tables were normalized around source-owned language fields,
  deprecated language columns and project-code style fields were removed, FR/ES localized
  values were added, and slot-based page values were unified across recipes and contracts
- template and page generation refactor:
  JP and US safety pages moved away from the old `content_blocks` pipeline into fixed RST
  templates, legacy safety/template fragments were retired, symbols became region/model-aware,
  and more review content was backported into source templates
- region scope simplification:
  the EU family config, manifest, templates, and recipes were removed so the active manual
  workflow now centers on shared US and JP families
- charging-page model gating:
  `charging.rst` became the shared page entry for US/JP charging content, and build tooling
  now supports `.. only:: model_...`, `region_...`, and `lang_...` tags across both Sphinx
  and Word bundle rendering so model-specific blocks can be filtered during build
- workflow, docs, and test updates:
  CI/review preview scripts, build/check flows, guides, and regression tests were updated
  to match the new review-first and US/JP-only operating model
  The maintainer guides now also document a parallel-language template rule: when a
  source-language prose template changes shared section structure or `.. only::`
  model-gating boundaries, the derived-language templates must be updated in the same
  change so page structure stays aligned across languages.

Important note:

- this PR also refreshed many `_review`, `_build`, and `reports/version_tracking` artifacts
  to reflect the new source and workflow behavior; those artifacts are useful verification
  evidence, but the primary long-term changes live in `tools/`, `docs/templates/`,
  `docs/manifests/`, `data/phase1/`, and the user/developer guides

## 4. How to Use This Archive

Use this log when you want to answer questions like:

- why does the repo have a phase1-centered renderer architecture?
- why were some layout or spec decisions made?
- when did certain testing concerns first appear?

Do not copy old commands from this log into current practice without checking the current guides first.
