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
| Fixed-page FCC panel | `components/fcc_panel.py` | Closed | `FccPanel` owns K05 plate, mark, lead/body split, columns, and localized lead geometry | Keep page callers limited to the aggregate component rectangle |
| What's in the Box cards | `components/inbox_panel.py` | Closed | `InboxPanel` owns title, card shells, badges, image fitting, strokes, offsets, and density profiles | Keep card metrics private to the component |
| Inbox TIP strip | `components/inbox_panel.py` | Closed | the optional TIP strip is rendered with the same Inbox data and geometry contract | Page code never draws TIP subframes |
| Standard/compact FCC + Inbox stack | `components/fcc_inbox_panel.py` | Closed | the aggregate owns standard/compact stacking, Symbols continuation, story order, and all FCC/Inbox internals | Page callers pass only data, language, density, and an outer rectangle |
| Standard Safety page | `components/safety_panel.py` | Closed | `SafetyPanel` owns title, warning, semantic dense-language split, subbar, columns, and all frame options | Page code creates only the physical spread and outer component rectangle |
| Compact Safety block | `components/compact_safety_panel.py` | Closed | title/body story generation, gap, typography mode, and body frame stay in one component | Shared-page code places Safety above `SymbolsPanel` without drawing Safety internals |
| Safety tail + maintenance + Symbols | `components/safety_symbols_panel.py` | Closed | the aggregate owns both warning tails, maintenance block, cursor rhythm, and embedded `SymbolsPanel` | Page code creates only the spread and the aggregate rectangle |
| Compact Storage + Specifications page | `components/storage_panel.py` | Closed | `StoragePanel` owns title, rounded K05 body card, inset, and internal vertical bounds | Page composer places Storage above the existing Specifications story frame |
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

Introduce `StoragePanel`, then expose a single component-regression runner for
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
- Storage is frozen across EN/FR/ES. Existing Symbols EN/FR/ES goldens remain
  unchanged.
- The existing full-package IDML golden remains byte-identical. This ownership
  refactor did not regenerate any approved package golden.

The Product Overview P2 item remains deliberately separate. Its multi-art
variant is already target-instance-owned and uses approved absolute art and
leader geometry; changing it to a relocatable rectangle API requires its own
pre-refactor trilingual package baseline rather than being mixed into the
fixed-panel move.

### Symbols visual correction after the ownership refactor

The initial ownership move preserved an existing compact-path divergence:
compact Symbols rows excluded the native table-carrier allowance, leaving the
allowance as a blank band below the table, while both columns and later the
whole rounded shell were filled K05 to conceal it. That was component reuse in
name only because its visible fill behavior differed from the standard JE
contract and from the BP reference.

The follow-up correction keeps one internal rule for both densities: only the
Symbol/icon column is K05, the Meaning column and rounded shell are Paper, and
a component-owned K05 column plate uses the real table-column width and full
outer-frame height, with its divider continued through the carrier tail. The
existing carrier allowance therefore stays available
to native InDesign without becoming a visible white band. The EN/FR/ES
contract fixture checks both cell-fill boundaries and the plate's exact width
and height.

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
