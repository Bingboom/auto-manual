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
| Specifications table | `spec_tables.py` + `data_stories.py` | Mostly closed | table geometry is internal, but the Storage composition still draws its own title/card | Keep the table; split out `StoragePanel` |
| Operation panels / notices in prose flow | `components/oppanel.py`, `components/notice.py`, `operation_stack.py` | Mostly closed | component geometry and spacing plan are outside page composers | Add common trilingual regression coverage |
| Key combinations | `components/key_combinations.py` | Closed | component owns table geometry and already has direct EN/FR/ES tests | Fold into the common regression runner |
| Fixed-page FCC panel | `page03._fcc_objects` | Leaking, P0 | page module creates K05 plate, mark and three text frames, including language-specific lead geometry | `FccPanel` owns all internal objects; caller passes rectangle, data, language, density |
| What's in the Box cards | `page03._inbox_objects` | Leaking, P0 | page module owns card width/height, x positions, badge circle, image widths, content offsets, stroke and language tokens | `InboxPanel` owns title, cards, badges, image fitting and optional footer strip |
| Inbox TIP strip | `page03._tip_objects` | Leaking, P0 | page module reconstructs plate/body rectangles from `notice_box_layout` | component owns the complete strip; page code never draws its subframes |
| Compact FCC + Inbox + Overview page | `shared_page.add_fcc_inbox_overview_page` | Leaking, P0 | imports private FCC/Inbox helpers and draws the Inbox title frame itself | page composer places public `FccPanel`, `InboxPanel`, and Overview component results |
| Standard Safety page | `pages.add_safety_page` | Leaking, P1 | page module owns title, warning, columns, subbar, section frames, fills and rounded shells | `SafetyPanel` owns the complete safety block within an assigned rectangle |
| Safety tail + maintenance block | `symbols_page.add_safety_symbols_page` | Leaking, P1 | Symbols is closed, but the same page function still draws two warning tails and maintenance title/body geometry | `SafetyMaintenancePanel` plus `SymbolsPanel`; composer only stacks outer rectangles |
| Compact Storage + Specifications page | `shared_page.add_storage_specifications_page` | Leaking, P1 | page module creates Storage H1 and rounded K05 body card and reads internal inset/top tokens | `StoragePanel` owns its title/card; page composer places it above the existing Specifications component |
| Product overview | `page_overview.py` / `page_overview_single_art.py` | Component-owned, P2 review | internal frames live in dedicated renderers, though one shared-page caller still supplies `image_height` rather than only available height | tighten the public rectangle API after P0/P1; preserve approved art geometry |
| TOC, folio, cover/back cover | dedicated page modules | Out of scope | these are page-level artifacts rather than reusable panels embedded by multiple composers | keep page ownership; add only regression coverage where missing |

## Implementation phases

### Phase A — FCC / Inbox family

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

Move the complete safety block and the maintenance/tail block behind public
component boundaries. Keep `SymbolsPanel` unchanged. Add standard/compact
EN/FR/ES fixtures before moving code.

### Phase C — Storage and regression unification

Introduce `StoragePanel`, then expose a single component-regression runner for
Symbols, FCC, Inbox, Safety, Storage, LCD, Troubleshooting, Specifications,
Operation, and Key Combinations. Each component declares applicable densities;
not every component must support both.

## Non-goals

- no visual token value changes;
- no re-generation of existing package goldens to hide a refactor diff;
- no source-table, template, CLI, config-selection, or finalizer behavior
  changes;
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
