# IDML Component Boundary Audit — 2026-08-25

## Goal

Extend the `SymbolsPanel` ownership rule to other reusable IDML visual
components:

- a page composer may choose a component's outer rectangle and z-order;
- the component owns its internal fills, corner treatment, columns, rows,
  carrier allowance, typography fitting, and minimum internal gaps;
- English, French, and Spanish use one component regression fixture, with
  language as an input rather than three drawing implementations.

This audit is based on `39234162` (`refactor(idml): consolidate shared
SymbolsPanel`) and covers the standard JE page path and compact JBP shared-page
path.

## Evidence and classification rule

A component is **closed** only when page code passes semantic data, language,
density, and an available rectangle. It is **leaking** when page code does any
of the following:

- reads a component-internal row, column, image, inset, fill, radius, or
  typography token;
- constructs the component's stories, cells, background plates, masks, or
  internal frames;
- selects per-language internal coordinates;
- calls a private renderer helper instead of a public component boundary.

Exact package goldens in `tests/fixtures/idml_golden/` are the pre-refactor
safety net for the standard path. The compact BP path must additionally freeze
the EN/FR/ES page spreads and component stories before any mechanical move.
Existing goldens are not regenerated during a pure ownership refactor.

## Inventory

| Area | Current owner | Verdict | Evidence | Required boundary |
|---|---|---:|---|---|
| Symbols title + signal/icon tables | `components/symbols_panel.py` | Closed | JE/JBP callers pass data, language, density, and an outer rectangle; EN/FR/ES standard/compact fixture exists | Keep as the reference implementation |
| LCD data table | `data_stories.py` + `lcd_style.py` | Mostly closed | shared page assigns only the outer story frame; row/column metrics stay in the LCD renderer | Add a shared EN/FR/ES contract fixture; no geometry move required |
| Troubleshooting table | `data_stories.py` | Mostly closed | shared page assigns only the outer story frame; table rows and columns stay in the renderer | Add to the common trilingual contract suite |
| Specifications table | `spec_tables.py` + `data_stories.py` | Mostly closed | table geometry is internal; the adjacent Storage section now uses the same prose/H1 renderer as JE-1000F | Keep the table and the shared Storage story as separate outer rectangles |
| Operation panels / notices in prose flow | `components/oppanel.py`, `components/notice.py`, `operation_stack.py` | Mostly closed | component geometry and spacing plan are outside page composers | Add common trilingual regression coverage |
| Key combinations | `components/key_combinations.py` | Closed | component owns table geometry and already has direct EN/FR/ES tests | Fold into the common regression runner |
| Fixed-page FCC panel | `components/fcc_panel.py` | Closed | `FccPanel` owns K05 plate, mark, lead/body split, columns, and localized lead geometry | Keep page callers limited to the aggregate component rectangle |
| What's in the Box cards | `components/inbox_panel.py` | Closed | `InboxPanel` owns title, card shells, badges, image fitting, strokes, offsets, and density profiles | Keep card metrics private to the component |
| Inbox TIP strip | `components/inbox_panel.py` | Closed | the optional TIP strip is rendered with the same Inbox data and geometry contract | Page code never draws TIP subframes |
| Standard/compact FCC + Inbox stack | `components/fcc_inbox_panel.py` | Closed | the aggregate owns standard/compact stacking, Symbols continuation, story order, and all FCC/Inbox internals | Page callers pass only data, language, density, and an outer rectangle |
| Standard Safety page | `components/safety_panel.py` | Closed | `SafetyPanel` owns title, warning, semantic dense-language split, subbar, columns, and all frame options | Page code creates only the physical spread and outer component rectangle |
| Compact Safety block | `components/compact_safety_panel.py` | Closed | title/body story generation, gap, typography mode, and body frame stay in one component | Shared-page code places Safety above `SymbolsPanel` without drawing Safety internals |
| Safety tail + maintenance + Symbols | `components/safety_symbols_panel.py` | Closed | the aggregate owns both warning tails, maintenance block, cursor rhythm, and embedded `SymbolsPanel` | Page code creates only the spread and the aggregate rectangle |
| Compact Storage + Specifications page | shared prose/H1 renderer via `components/storage_panel.py` | Closed | the adapter calls the exact JE-1000F story path; no JBP K05 card, radius, inset, or title-frame geometry remains | Page composer places the shared Storage story above the existing Specifications story frame |
| Product overview | `page_overview.py` / `page_overview_single_art.py` | Component-owned, P2 review | internal frames live in dedicated renderers, though one shared-page caller still supplies `image_height` rather than only available height | tighten the public rectangle API after P0/P1; preserve approved art geometry |
| TOC, folio, cover/back cover | dedicated page modules | Out of scope | these are page-level artifacts rather than reusable panels embedded by multiple composers | keep page ownership; add only regression coverage where missing |

## Implementation phases

### Phase A — FCC / Inbox family

Status: complete on `refactor/idml-component-boundaries`.

Files:

- add `tools/idml/components/fcc_panel.py`;
- add `tools/idml/components/inbox_panel.py` (including the optional TIP strip);
- reduce `tools/idml/page03.py` and
  `tools/idml/shared_page.py` to placement and z-order;
- add one EN/FR/ES fixture covering `standard` and `compact` densities;
- add a boundary test that rejects private FCC/Inbox helpers and internal
  metric keys in page composers.

Safety nets:

- existing full-package golden must remain byte-identical;
- frozen JBP EN/FR/ES component stories and spreads must remain byte-identical;
- InDesign finalization must report zero overset, missing fonts, and bad links.

### Phase B — Safety family

Status: complete on `refactor/idml-component-boundaries`.

Move the complete safety block and the maintenance/tail block behind public
component boundaries. Keep `SymbolsPanel` unchanged. Add standard/compact
EN/FR/ES fixtures before moving code.

### Phase C — Storage and regression unification

Status: component-boundary portion complete; broader P2 regression aggregation
remains a follow-up.

Route compact Storage through the JE-1000F prose/H1 story, then expose a single component-regression runner for
Symbols, FCC, Inbox, Safety, Storage, LCD, Troubleshooting, Specifications,
Operation, and Key Combinations. Each component declares applicable densities;
not every component must support both.

## Implemented result

- `page03.add_fcc_inbox_page`,
  `shared_page.add_fcc_inbox_overview_page`, `pages.add_safety_page`,
  `shared_page.add_safety_symbols_page`,
  `symbols_page.add_safety_symbols_page`, and
  `shared_page.add_storage_specifications_page` now create only the physical
  spread, choose an outer rectangle, and call a public component.
- Boundary tests reject component-internal frame builders and metric keys in
  those page composers.
- FCC/Inbox/TIP is frozen for `standard` and `compact` across EN/FR/ES.
- Safety is frozen for standard, compact, and maintenance/Symbols compositions
  across EN/FR/ES.
- Storage is frozen across EN/FR/ES on the JE-1000F H1/prose contract: the
  title uses the same inline anchored H1 story and the body stays in the same
  white content flow. There is no JBP-only K05 body card. Existing Symbols
  EN/FR/ES goldens remain unchanged.
- The ownership-only move kept the existing full-package IDML golden
  byte-identical. The later Symbols visual correction intentionally updates
  only the affected Symbols spreads and stories, with EN/FR/ES component
  fixtures recording that geometry change.

The Product Overview P2 item remains deliberately separate. Its multi-art
variant is already target-instance-owned and uses approved absolute art and
leader geometry; changing it to a relocatable rectangle API requires its own
pre-refactor trilingual package baseline rather than being mixed into the
fixed-panel move.

### Symbols visual correction after the ownership refactor

The initial JBP compact composition reused the low-level Symbols table
builders, but introduced separate compact row tokens and left its 11.5pt
table-carrier allowance below the rows. The earlier JE-1000F correction in
`ec0a4294` fixed badge/content baselines on the standard path; it did not
define the compact panel's whole-row and native-carrier geometry. Consequently
the same visible content could still render differently after the compact path
was added. The first ownership move preserved that divergence, and later fill
patches merely covered the blank band instead of removing its cause.

The final correction keeps one fill and ownership rule for both densities:
only the Symbol/icon column is K05, while the Meaning column and rounded shell
are Paper. Standard density retains JE's approved fixed row heights and its
0.25pt shell tolerance. Compact signal carrier allowance is used
shortest-row-first, which levels the four signal rows for the approved EN/FR/ES
layouts; compact icon allowance is distributed through the visible body rows,
so neither compact table has a bottom carrier band. A separate 4mm transparent
text-frame carrier remains available to native InDesign outside the visible
shell. Finalization may fit that transparent frame only and may not resize any
visible shell, K05 plate, mask, outline, or table row. The EN/FR/ES contract
fixture checks row centering, cell-fill boundaries, plate geometry, and the
separation between visible geometry and the native carrier.

### Follow-through on Troubleshooting and Charging

The same boundary now covers the two whitespace findings raised during JBP
acceptance. Compact Troubleshooting rows are deterministic visible geometry:
their measured height is written as both `SingleRowHeight` and
`MinimumHeight`, AutoGrow is disabled, and the 1pt terminal-marker allowance
extends only the transparent story frame. The InDesign finalizer may fit that
carrier but cannot resize the visible rounded shell or its shaded code column.

Charging owns the transition from a diagram to the following suffix-pill H2.
The AboveLine diagram already contributes a native paragraph line box, so the
shared `charging` variant does not stack the generic 4.25pt figure-after and
5.67pt H2-before margins on top of it. The target assembly selects only the
variant and image measure; it does not receive page coordinates or spacing
values. EN/FR/ES exercise the same code path and package regression.

## Non-goals

- no model-specific visual token overrides or page-coordinate patches;
- no unrelated package-golden regeneration;
- no source-table, template, CLI, or config-selection changes;
- no requirement to turn page-only artifacts such as TOC or back cover into
  embedded panels;
- no cross-renderer geometry sharing: this audit is about IDML ownership, not
  copying InDesign coordinates into Web, LaTeX, or Word.

## Verification ladder

1. Ruff on touched modules and tests.
2. Direct component contract and boundary tests.
3. `tests.test_export_idml_golden`, `tests.test_export_idml`, and shared-page
   tests.
4. Full `python -m unittest`.
5. maintainability and documentation-link guardrails.
6. `build.py check` for JE-1000F/US and JBP-2000B/US fixtures.
7. exact IDML part comparison, InDesign finalization, and rendered PDF page
   comparison against the frozen baseline.
