# Development Log

Updated: 2026-03-12

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

## 3. How to Use This Archive

Use this log when you want to answer questions like:

- why does the repo have a phase1-centered renderer architecture?
- why were some layout or spec decisions made?
- when did certain testing concerns first appear?

Do not copy old commands from this log into current practice without checking the current guides first.
