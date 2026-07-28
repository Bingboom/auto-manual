# LaTeX Style Registry

This registry is the canonical map from a visible manual style to its public
LaTeX entrypoint, owning module, and parameter namespace. It counts semantic
styles rather than every helper macro or generated design token.

The renderer has **31 base styles** and **34 visible variants**. The difference
comes from `HB-CALLOUT-STRIP`: one component owns the four visible `WARNING`,
`CAUTION`, `NOTE`, and `TIP` variants.

## Load Order

Component modules are loaded in dependency order by `theme.tex` and copied into
the Sphinx LaTeX bundle by `docs/conf_base.py`.

| Order | Module | Ownership |
| ---: | --- | --- |
| 1 | `components_base.tex` | Shared image, list, table-frame, and callout foundations |
| 2 | `components_headings.tex` | Level-1, level-2, and level-3 title objects |
| 3 | `components_special_pages.tex` | Back cover, app, inbox, overview, FCC, preface, and TOC |
| 4 | `components_symbols.tex` | Signal-word and symbol-icon tables |
| 5 | `components_lcd.tex` | LCD icon and LCD mode tables |
| 6 | `components_safety.tex` | Safety-page warning and danger objects |
| 7 | `components_spec.tex` | Dedicated specification page and tables |
| 8 | `components_data_tables.tex` | Auto Resume, Key Combinations, and Troubleshooting tables |
| 9 | `components_warranty.tex` | Dedicated warranty page objects |

## Typography And Headings

| Style ID | Visible role | Public entrypoint | Owner | Parameter namespace |
| --- | --- | --- | --- | --- |
| `HB-TYPE-BODY` | Body paragraphs | `HBTypeBaseStart`, `HBTypeBody` | `type_system.tex` | `type_body_*`, `page_par*` |
| `HB-TYPE-LIST` | Bulleted and numbered copy | `HBTypeListStart` | `type_system.tex`, `components_base.tex` | `comp_list_*`, `type_body_*` |
| `HB-TITLE-L1` | Dark level-1 band, square top and rounded bottom | `HBTitleLevelOne` | `components_headings.tex` | `comp_h1_*`, `type_title_l1_*` |
| `HB-TITLE-L2` | Dot-led level-2 heading | `HBTitleLevelTwo` | `components_headings.tex` | `comp_title_l2_*`, `type_title_l2_*` |
| `HB-TITLE-L3` | Compact dot-led level-3 heading | `HBTitleLevelThree` | `components_headings.tex` | `comp_title_l3_*`, `type_title_l3_*` |
| `HB-TYPE-LEAD` | Safety lead, warning text, and rubric copy | `HBTypeWarningTextStart`, `HBTypeRubricStart` | `type_system.tex` | `type_warning_*`, `type_rubric_*` |
| `HB-TYPE-FOOTER` | Footer text | `HBTypeFooter` | `type_system.tex` | `page_footer_*` |
| `HB-TYPE-PAGE-NUMBER` | Page number | `HBTypePageNumber` | `type_system.tex` | `page_number_*` |

## Callouts And Safety

| Style ID | Visible role | Public entrypoint | Owner | Parameter namespace |
| --- | --- | --- | --- | --- |
| `HB-CALLOUT-STRIP` | `WARNING`, `CAUTION`, `NOTE`, and `TIP` split-label strips | `HBWarningBlock`, `HBCautionBlock`, `HBNoteBlock`, `HBTipBlock` | `components_base.tex` | `comp_callout_*`, `comp_caution_*`, `comp_tip_*` |
| `HB-SAFETY-INSTRUCTION` | Outlined safety instruction lockup | `HBSafetyInstruction` | `components_safety.tex` | `comp_safety_instruction_*` |
| `HB-SAFETY-WARNING` | Standard safety warning panel | `safetywarningbox`, `safetywarning` | `components_safety.tex` | `comp_warning_*` |
| `HB-SAFETY-LEAD` | Large warning icon and lead copy | `HBWarningLeadBlock` | `components_safety.tex` | `comp_safety_lead_*` |
| `HB-SAFETY-DANGER` | Danger lockup and explanatory copy | `HBDangerBlock` | `components_safety.tex` | `comp_danger_*` |

## Tables

All data-bearing table cells use vertically centered `m{}` columns or `[c]`
content boxes. Rounded outer frames are separate from the internal grid.

| Style ID | Visible role | Public entrypoint | Owner | Parameter namespace |
| --- | --- | --- | --- | --- |
| `HB-TABLE-SPEC` | Specification section tables | `spectable` | `components_spec.tex` | `comp_spec_*`, `type_spec_*` |
| `HB-TABLE-SYMBOL-SIGNAL` | Full-width signal-word table | `HBSymbolTable` | `components_symbols.tex` | `comp_symbol_*`, `type_symbol_*` |
| `HB-TABLE-SYMBOL-ICON` | Two-column symbol icon tables | `HBSymbolTwoColumnTables` | `components_symbols.tex` | `comp_symbol_*`, `type_symbol_*` |
| `HB-TABLE-LCD-ICON` | Multi-page LCD icon table | `HBLcdIconTable` | `components_lcd.tex` | `comp_lcd_*`, `type_lcd_*` |
| `HB-TABLE-LCD-MODE` | LCD state/action table | `HBLcdModeTable` | `components_lcd.tex` | `comp_lcd_mode_*` |
| `HB-TABLE-AUTO-RESUME` | Auto Resume conditions table | `HBAutoResumeTable` | `components_data_tables.tex` | `comp_auto_resume_*`, `comp_data_table_*` |
| `HB-TABLE-KEY-COMBINATIONS` | Key Combinations table | `HBKeyCombinationTable` | `components_data_tables.tex` | `comp_key_table_*`, `comp_data_table_*` |
| `HB-TABLE-TROUBLESHOOTING` | Fault-code and corrective-measures table | `HBTroubleshootingTable` | `components_data_tables.tex` | `comp_trouble_*`, `comp_data_table_*` |

## Special Manual Blocks

| Style ID | Visible role | Public entrypoint | Owner | Parameter namespace |
| --- | --- | --- | --- | --- |
| `HB-SPECIAL-FCC` | Two-column FCC panel | `HBFccBlock` | `components_special_pages.tex` | `comp_fcc_*`, `type_fcc_*` |
| `HB-SPECIAL-INBOX` | Three independent What's In The Box cards | `HBInBoxThree` | `components_special_pages.tex` | `comp_inbox_*`, `type_inbox_*` |
| `HB-SPECIAL-OVERVIEW` | Product overview image and data panel | `HBOverviewPanel` | `components_special_pages.tex` | `comp_overview_*`, `type_overview_*` |
| `HB-SPECIAL-APP` | App setup step, asset, and notice primitives | `HBAppStep`, `HBAppAsset`, `HBAppNotice` | `components_special_pages.tex` | Component-local dimensions |
| `HB-WARRANTY-LEAD` | Warranty eligibility lead panel | `HBWarrantyLead` | `components_warranty.tex` | `comp_warranty_lead_*` |
| `HB-WARRANTY-SECTION` | Labeled rounded warranty section | `HBWarrantySection` | `components_warranty.tex` | `comp_warranty_section_*` |
| `HB-WARRANTY-YEARS` | Standard and extended warranty columns | `HBWarrantyYears` | `components_warranty.tex` | `comp_warranty_year_*` |

## Page Templates

Special-page variants such as preface, TOC, and back cover are implemented in
`components_special_pages.tex` and select one of these page-level families.

| Style ID | Visible role | Public entrypoint | Owner | Parameter namespace |
| --- | --- | --- | --- | --- |
| `HB-PAGE-STANDARD` | Standard body page with footer | `HBPageTemplateStandard` | `layout_templates.tex` | `page_*` |
| `HB-PAGE-NO-FOOTER` | Preface, TOC, and other footerless pages | `HBPageTemplateNoFooter` | `layout_templates.tex` | `page_*`, special component params |
| `HB-PAGE-COVER` | Front and back cover page family | `HBPageTemplateCover`, `HBBackCoverPage` | `layout_templates.tex`, `components_special_pages.tex` | `page_*` |

## Editing Rules

1. Keep public entrypoint names stable; templates and doctree transforms depend on them.
2. Add geometry or typography values to `data/layout_params.csv`, not inline in templates.
3. Let object components own fill, stroke, corner geometry, padding, and fixed height.
4. Let source RST and generated tables own content only.
5. Add a registry row and an ownership test whenever a new visible style family is introduced.
