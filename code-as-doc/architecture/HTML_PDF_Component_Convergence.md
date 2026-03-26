# HTML/PDF Component Convergence Guide

Updated: 2026-03-26

## 1. Role

This file defines how Hello-Docs should gradually make HTML output converge toward the intended final PDF design language.

Use it to define:

- the convergence target between HTML and PDF
- the shared component vocabulary
- the migration order for high-value pages
- the implementation rules for HTML, LaTeX, and Word alignment

This file is not:

- the long-term system strategy document
- the day-to-day build workflow guide
- the current optimization backlog

Use these documents for those topics:

- long-term strategy: [`System Evolution Strategy.md`](System%20Evolution%20Strategy.md)
- current repo component map: [`Hello_Docs_Architecture.md`](Hello_Docs_Architecture.md)
- current build workflow: [`../build_doc_guide.md`](../build_doc_guide.md)
- current user workflow: [`../../user-guide/hello_auto-doc.md`](../../user-guide/hello_auto-doc.md)

## 2. Goal

The target is not pixel-perfect parity between HTML and PDF.

The target is:

- shared information hierarchy
- shared component structure
- shared visual language
- predictable Word adaptation from the same component semantics

In practical terms:

- PDF remains the final layout benchmark
- HTML should increasingly look like the same manual, not a default Sphinx page
- Word should reuse the same structure as much as possible, with format-specific adaptation only where needed

## 3. Current Baseline

Current useful reference pages:

- [`../../docs/templates/safety_template.rst`](../../docs/templates/safety_template.rst)
- [`../../docs/templates/spec_template.rst`](../../docs/templates/spec_template.rst)

Current PDF component implementations:

- [`../../docs/renderers/latex/components_safety.tex`](../../docs/renderers/latex/components_safety.tex)
- [`../../docs/renderers/latex/components_spec.tex`](../../docs/renderers/latex/components_spec.tex)

Current Word-side adaptation points:

- [`../../tools/word_bundle_html.py`](../../tools/word_bundle_html.py)
- [`../../tools/word_bundle_docx.py`](../../tools/word_bundle_docx.py)

Current baseline status:

- `safety` is the best current example of component-driven convergence
- `spec` is now the second benchmark component family for section title + data table alignment
- many other pages still depend too heavily on default docutils / Sphinx output shape

## 4. Stable Convergence Principles

1. Converge by shared component semantics, not by page-specific CSS patches.
2. PDF remains the visual benchmark for structure, rhythm, and emphasis.
3. HTML should express the same component intent even when pagination differs.
4. Word should inherit from the same component structure instead of being treated as a separate document design system.
5. High-value pages should be migrated first; low-value pages can temporarily remain generic.
6. New visual work should prefer reusable components over one-off page markup.

## 5. Shared Component Vocabulary

The system should gradually standardize on these semantic components.

### 5.1 Priority Components

- `warning_box`
- `subbar`
- `two_col_list`
- `lead_text`
- `spec_section`
- `data_table`
- `note_block`
- `footnote_block`

### 5.2 Component Intent

`warning_box`

- used for high-attention safety or caution lockups
- must preserve icon/label + body relationship across HTML, PDF, and Word

`subbar`

- used for strong section separators inside a page
- should carry the same visual hierarchy in HTML and PDF

`two_col_list`

- used when PDF layout depends on balanced multi-column reading flow
- HTML may stack on narrow screens, but desktop HTML should still express the two-column intent
- Word may use true tables when needed to preserve structure

`lead_text`

- used for short pre-list or pre-table emphasis text
- should not collapse into generic body styling

`spec_section`

- used for labeled section headings inside specification pages
- should preserve uppercase/rubric behavior and section rhythm

`data_table`

- used for structured label/value content
- must keep consistent borders, row rhythm, and left/right role distinction

`note_block` and `footnote_block`

- used for supporting legal, technical, or qualification text
- should stay visually secondary but intentionally styled

## 6. Format Mapping Rule

Every priority component should have three explicit implementations.

### 6.1 HTML

- component-driven markup in the template layer
- stable class names
- visual tokens expressed in CSS

### 6.2 PDF

- LaTeX macro or environment implementation
- PDF remains the benchmark for spacing, emphasis, and document tone

### 6.3 Word

- derived from the HTML-side structure when possible
- allowed to use Word-specific conversion helpers when HTML import alone is not reliable
- should not define an unrelated visual language

## 7. Recommended Migration Order

Use this order unless a release target forces a different priority.

### Phase 1: Baseline Component Pages

- `safety`
- `spec`

Purpose:

- lock the first stable component set
- validate HTML/PDF/Word alignment on high-visibility pages

### Phase 2: Front-of-Book Pages

- cover
- intro / important notice
- product overview
- package contents

Purpose:

- align first-impression pages with the final manual tone

### Phase 3: Operational Guidance Pages

- button/port overview
- getting started
- charging and output usage
- mode switching
- troubleshooting callouts

Purpose:

- migrate the highest-traffic instructional pages away from generic document markup

### Phase 4: Long-Tail Pages

- FAQ
- warranty
- appendix
- compliance and support pages

Purpose:

- complete visual consistency after high-value pages are stable

## 8. Page Acceptance Criteria

A page is considered converged enough when:

- HTML and PDF use the same component breakdown
- major headings, sub-bars, alerts, and tables express the same hierarchy
- HTML no longer looks like a default rendered RST page
- Word preserves the same content structure without collapsing into unstyled paragraphs
- page-specific fixes can be explained in terms of shared components, not ad hoc exceptions

## 9. Implementation Rules

1. Prefer changing shared template/component layers before patching generated HTML.
2. If a page needs custom Word preservation, keep the special handling in the Word bundle layer, not in random downstream scripts.
3. Avoid introducing format-only semantics that have no cross-format equivalent.
4. When a new component appears twice, formalize it.
5. When a page uses a stable component, give it a stable HTML class and a stable LaTeX macro/environment.

## 10. What To Avoid

- do not chase pixel-perfect HTML/PDF parity
- do not patch one page at a time without naming the reused component
- do not treat Word as a separate manual design system
- do not rely on default docutils output for pages that carry strong brand or layout intent
- do not fork whole templates when only one component needs improvement

## 11. Immediate Next Steps

Recommended immediate work sequence:

1. keep `safety` as the benchmark page for warning, subbar, and two-column behavior
2. keep tightening `spec` until section title rhythm, tables, and notes behave as a stable reusable component family
3. define the first reusable HTML visual token set for high-priority components
4. migrate one front-of-book page using the same component rules
5. review whether any new page-specific logic can be collapsed back into reusable component helpers

## 12. Review Trigger

Update this file when:

- the component vocabulary changes
- the migration order changes
- the HTML/PDF convergence target changes
- Word is intentionally moved to a different adaptation strategy
