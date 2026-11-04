# JHP-1000B — full source layout review

The previous ten design declarations are not approval evidence. Their exact text and full disposition are preserved in `differences-audit.json`.

| Old item | Source physical pages | Actual Web location and disposition |
| --- | --- | --- |
| 1 | 1, 2, 3, 22 | `[data-source-preface-title]; [data-source-contact="back"]` — Front cover and paper TOC excluded by explicit operator scope. Restored EN next to IMPORTANT and the back contact address, source frame/icons/QR, and native telephone/email/website. |
| 2 | 4, 6, 19 | `[data-native-columns]; .hb-fcc-composition; .hb-warranty-period-card` — Restored two safety columns and the exact inside-item column break. FCC was already two columns and remains so. Warranty source has two columns only inside the 3/2 YEARS period panel; its other sections remain full width. The old blanket claim was inaccurate. |
| 3 | 2, 4, 5, 7, 10, 11, 12, 13, 15, 16, 20, 21 | `[data-source-preface-title]; [data-source-safety-title]; native h1/h2/h3` — Restored compact IMPORTANT badge/title, dark safety subsection bars, and four App subsection dots. Chapter bars and other source hierarchy remain native with the shared theme. Responsive line wrapping and vertical spacing are not fixed PDF pagination. |
| 4 | 4, 5, 11, 12, 14, 15, 16, 21 | `[data-native-strip]; [data-source-warning-card]; .manual-callout-table` — Top WARNING/DANGER use their exact source frame and warning mark with selectable copy. The basic WARNING card occupies the left column top only; bullets remain outside. Grounding WARNING is a plain bold lead followed by its source bullet. Other source side-label CAUTION/NOTE/WARNING callouts retain native label/body relationships. |
| 5 | 10, 11, 12, 15 | `[data-native-panel]; [data-native-copy]` — Restored all six source panel copy placements, including power standby, AC/DC prerequisites, AC outlet note, LED modes and three original step rows, energy-saving instruction, AC charging caption. Exact source asset rectangles are in asset_recipe.json and layout-positions.css. Native copy remains editable; source artwork is not drawn or rasterized as complete pages. |
| 6 | 12, 13 | `.hb-lcd-mode-composition; .hb-key-combination-table` — Native mode/key tables preserve source row order and button/description association. Restored all four plus signs and exact original clock glyphs. Desktop fits the reading rail; phone scrolls internally without changing row associations. |
| 7 | 5 | `[data-source-signal]; .hb-symbol-pair-composition` — Signal labels use the own-PDF triangle rather than a generic drawn mark; words and meanings remain native. Source 4+3 pictogram tables remain side by side on desktop. All seven admitted symbol assets pass the existing own-PDF admission threshold. |
| 8 | 9, 17, 18 | `.hb-lcd-table-composition; #troubleshooting; #source-spec-o` — Restored LCD number 23 spanning high/low temperature rows, original two-row USB-C label span, and F7 V_oc subscript. Source troubleshooting steps remain separate lines; all source values remain unchanged. |
| 9 | 6 | `.hb-fcc-composition` — FCC native two-column paragraph/list block retains its source mark. Navigation-only FCC title remains visually hidden. No RF or ISED text is added; this source has neither. |
| 10 | 7, 8, 10, 11, 12, 14, 15, 16, 20, 21 | `.hb-reference-figure` — Complete source leader/port/nameplate/screen panels remain the same model artwork. Every existing asset decision is rechecked against own-source recipe/hash or the symbol-admission evidence, rather than treated as approval. Native moved body text is overlaid in its original panel rectangles. |

Only the front cover and paper TOC are excluded by operator scope; printed page numbers are omitted from the continuous Web flow. Desktop retains the source column/panel/table relationships. At phone widths, safety text stacks and dense figures/tables scroll internally; their content/order/associations remain intact. No historical correction approval was inferred from old release or layout notes.

Final heading check: the four specification groups use native h2 with the existing hb-subbar class, preserving one dot and avoiding MyST chapter promotion. No duplicate App dots are emitted.

The source plain SAVE THESE INSTRUCTIONS, GROUNDING INSTRUCTION and Emergency Charging Mode leads remain native bold paragraphs without added circles. The first-charge reminder and full-width safety subsection bars use the existing hb-prose-pill treatment.

Final viewport review also corrected the right-view bottom and operation-panel frame crops against the own-PDF drawing bounds; LCD mode art/table widths follow the source, and the AC charging caption remains plain on its source white background. See restored-artwork.json for each final bbox and hash.

FCC p6 follow-up: the shared component remains authoritative. The source NOTE/These limits paragraph boundary is preserved as native newline in its text slot/carrier and shown by source-local pre-line CSS. The original FCC mark floats left to restore source wrapping. No extra wording or source data is introduced.
