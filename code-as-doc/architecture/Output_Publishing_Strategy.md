# Output Publishing Strategy

Updated: 2026-06-06

## 1. Role

This file is the current architecture note for manual output and publishing
surfaces.

Use it to decide how HTML, Word, PDF, Markdown, Read the Docs, Feishu cloud
docs, and release traceability should relate to each other.

Historical detail lives in:

- [`archive/HTML_PDF_Component_Convergence.md`](archive/HTML_PDF_Component_Convergence.md)
- [`archive/MyST_Markdown_Feishu_Cloud_Doc_Publish_Plan.md`](archive/MyST_Markdown_Feishu_Cloud_Doc_Publish_Plan.md)

This file replaces those two top-level architecture entries as the maintained
output strategy.

## 2. Architecture Decision

The repository should keep one manual content/build source and several output
lanes.

The source boundary remains:

```text
templates + data/phase2 snapshot + review overlays
  -> target-scoped runtime bundle
  -> output-specific render/export lanes
```

Output lanes are siblings:

- `html`: preview and hosted reading output
- `word`: review and handoff DOCX output
- `pdf`: formal publish artifact
- `md`: MyST-compatible Markdown for electronic manuals and cloud-doc import

No output lane should create a second page assembly system or a new content
source of truth.

## 3. Current Output Ownership

| Surface | Role | Source of truth |
| --- | --- | --- |
| RST bundle | generated build source | `build.py` materialized target bundle |
| HTML | preview/hosted reading surface | same target bundle |
| Word | review handoff and draft artifact | same target bundle through Word bundle path |
| PDF | formal publish artifact | review-sourced publish build |
| Markdown | supplementary electronic manual source | same target bundle, aligned with Word path |
| Feishu cloud doc | optional imported cloud reading copy | generated Markdown import |
| Read the Docs | hosted electronic manual catalog | generated/migrated MyST source |
| release manifest | traceability record | publish build outputs and snapshot metadata |

## 4. Stable Principles

1. PDF remains the formal release benchmark.
2. Word remains the review/handoff format.
3. HTML should express the same manual structure instead of default generic
   document styling.
4. Markdown is a sibling output, not a replacement for RST.
5. Release traceability should record every generated release artifact.
6. Feishu cloud docs and Read the Docs are delivery/hosting surfaces, not the
   canonical build source.
7. Output work should reuse declared component semantics instead of page-specific
   CSS, LaTeX, or conversion patches.
8. Do not create one config per model or per output format.

## 5. Component Convergence

The long-term output goal is shared structure, not pixel-perfect parity.

Priority reusable components:

- `warning_box`
- `subbar`
- `two_col_list`
- `lead_text`
- `spec_section`
- `data_table`
- `note_block`
- `footnote_block`

Rules:

- HTML uses stable component class names.
- PDF uses matching LaTeX macros or environments.
- Word derives from the shared HTML/bundle structure where possible.
- New output behavior should first ask whether a component exists before adding
  page-local special handling.

Acceptance for a page:

- HTML and PDF use the same component breakdown.
- Word preserves the same content structure.
- page-specific exceptions can be explained in component terms.

## 6. Markdown And Electronic Manuals

Markdown should be generated from the same assembled manual content as Word and
PDF.

Preferred conversion shape:

```text
target bundle -> Word bundle HTML -> Pandoc -> MyST-compatible Markdown
```

Writer preference:

1. native `myst` when Pandoc supports it
2. MyST-compatible CommonMark with pipe tables
3. generic Markdown only as a last fallback

Generated Markdown remains target-scoped under the normal build output rules.
It should not introduce a separate template family or output-specific config.

## 7. Publish Flow

Formal publish remains review-sourced and gated by existing checks.

Target publish order:

```text
check -> diff-report -> word -> pdf -> md -> release-manifest
```

Queue writeback remains compatible with the current `Document_link` contract:

- Draft rows write DOCX to `Document link`.
- Publish rows write PDF to `Document link`.
- Markdown is supplementary.
- If `飞书云文档` exists, queue processing may import Markdown and write the cloud
  document URL there.
- Cloud-doc import failure must be visible and must not erase the latest primary
  artifact link.

## 8. Read The Docs Direction

Read the Docs is the preferred hosted electronic-manual surface.

It should support two lanes:

- generated manuals from target-scoped Markdown output
- migrated existing Markdown manuals normalized into a MyST source tree

The hosted catalog is a continuity layer while manuals gradually move from
legacy Markdown into structured templates and `data/phase2` content.

RTD must stay independent from Feishu. Feishu cloud-doc import is a delivery
integration, not the canonical web host.

## 9. Non-Goals

Do not:

- replace RST as the internal generated bundle format in the current stage
- replace Word or PDF release artifacts
- make `飞书云文档` the primary release link
- build a separate Markdown-only page assembly system
- chase pixel-perfect HTML/PDF parity
- treat Word as a separate manual design system
- fork whole templates when a reusable component would solve the output issue

## 10. Review Trigger

Update this file when:

- the supported output lanes change
- Markdown becomes more than a supplementary output
- Read the Docs becomes a release-blocking surface
- the primary `Document link` semantics change
- the component vocabulary changes
- Word stops deriving from the current bundle/HTML path
