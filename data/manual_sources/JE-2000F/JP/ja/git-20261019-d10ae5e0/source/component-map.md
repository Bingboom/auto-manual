# JE-2000F JP source-to-shared-component map

Reference structure: JE-1000F JP, git-20260930-d88b32fe-jp-reviewed. Its source-local styles are historical; this candidate uses the current shared theme only. All Japanese copy, numbers and procedures come from the supplied 28-page JE-2000F PDF.

| PDF block | Shared component / flow |
| --- | --- |
| Safety signal table | HB-TABLE-SYMBOL-SIGNAL |
| Safety pictograms and recycling | HB-TABLE-SYMBOL-ICON, existing shared JP variants |
| Safety warnings, cautions, notes, App 備考 | HB-CALLOUT-STRIP; nested lists retain ownership |
| Inbox | HB-SPECIAL-INBOX |
| Product overview / wiring / UI drawings | HB-SPECIAL-REFERENCE-FIGURE; dense overview labels and complete phone frames retained |
| 25 LCD symbols | HB-TABLE-LCD-ICON; reuse JE-1000F shared-lcd bytes by semantic meaning, not printed number |
| LCD states/actions | HB-TABLE-LCD-MODE |
| Auto-resume conditions | HB-TABLE-AUTO-RESUME |
| Four button combinations | HB-TABLE-KEY-COMBINATIONS |
| Error codes | HB-TABLE-TROUBLESHOOTING |
| Four specification groups | HB-TABLE-SPEC |
| Warranty | HB-WARRANTY-LEAD / HB-WARRANTY-SECTION |
| App download | HB-SPECIAL-APP |
| Energy thresholds | Plain native table; source has a merged default-setting cell and 3 columns, no dedicated energy-threshold component. Declared exception by its text hash. |
| Body, headings and lists | Shared semantic flow |

The print cover, printed contents, blank page and repeated back-cover App promotion stay in the archive, outside the Web body.
