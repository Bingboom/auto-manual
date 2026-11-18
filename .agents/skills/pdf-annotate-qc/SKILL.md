---
name: pdf-annotate-qc
description: Render QC findings as highlight + note annotations on a built manual PDF, producing a read-only *_annotated.pdf sidecar for PDF-facing reviewers. Use when someone asks to "标注 PDF"、"在 PDF 上高亮问题"、review/audit a shipped PDF, or deliver content_lint results in PDF form. The shipped PDF is never modified, and fixes route through the existing docx/cloud-doc backport path — never edit the PDF itself. NOT for docx highlighting (use docx-highlight-changes) or for making content corrections.
metadata:
  owner: "资料审核维护人"
  status: "on-request"
  entry: "按审核意见交付有高亮及批注的 PDF 副本"
  tools: "tools/pdf_annotate.py"
  validation: "用 tests/test_pdf_annotate.py 核对定位及找不到原文时的处理"
  reviewed: "2026-11-17"
  retire_when: "审阅方停用 PDF 侧批件"
---

# PDF Annotate QC

## Overview

Architecture rule: **annotate on the PDF, correct at the source.** The PDF is a
rendered artifact — editing it is futile (the next build overwrites it) and
mapping PDF coordinates back to RST/source tables is the hardest reverse path
in the pipeline. This skill renders QC findings as a read-only presentation
layer on the built PDF so a PDF-only reviewer sees exactly what was flagged
and where the source lives.

## Flow

1. Produce findings (or accept an existing findings.json):

   ```bash
   python -m tools.content_lint --data-root data/phase2 --json --write-report
   # -> reports/content_qc/<run-id>/findings.json
   ```

2. Render them onto the built PDF:

   ```bash
   python -m tools.pdf_annotate \
     --pdf docs/_build/<model>/<region>/pdf/<manual>.pdf \
     --findings reports/content_qc/<run-id>/findings.json
   # -> <manual>_annotated.pdf next to the input (or --out <path>)
   ```

3. Deliver the `*_annotated.pdf` to the reviewer. Each highlight carries a note
   with severity, rule, message, the **source location** (table/copy_key/lang
   from `source_ref`), and the suggested action.

## Guarantees and boundaries

- The input PDF is opened read-only and never modified; output is a sidecar.
- Locating degrades, never lies: a finding whose text is not found on any page
  gets **no misplaced highlight** — it lands in a summary note on page 1 and
  in the JSON result as `unlocated`.
- Fixes flow through the source: cloud-doc / 修订 docx review →
  `cloud_doc_backport` (Class R) or the approval-gated source-table / TM
  paths. Never transcribe corrections into the PDF.
- Requires `PyMuPDF` (in `requirements.txt`). Known limitation: two-column
  layouts can defeat text search (the known pdftotext 错位 problem) — those
  findings degrade to the page-1 summary note instead of wrong highlights.

## Validation

- `python3 -m unittest tests.test_pdf_annotate`
