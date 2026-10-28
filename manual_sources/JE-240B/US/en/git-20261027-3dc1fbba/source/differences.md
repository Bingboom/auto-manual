# Deliberate Web layout differences from the printed JE-240B US English manual

Wording is never changed. These are layout decisions only.

1. Cover (p1), paper TOC (p3) and the back-cover QR code (p15) are not on the Web page; printed page numbers are dropped. The back-cover JACKERY INC. contact text closes the WARRANTY chapter in the shared text panel.
2. The IMPORTANT: front-matter page (p2) is the first chapter; its printed 「US」 corner badge is not repeated (transcription line `intro.badge`, `"web": false`).
3. Chapter strips are shared h2 headings; ● sub-headings, the boxed 「INSTRUCTIONS PERTAINING TO RISK…」 heading and the dark OPERATING INSTRUCTIONS / USER MAINTENANCE INSTRUCTIONS pills are shared h3 headings; 「SAVE THESE INSTRUCTIONS」 stays a bold line; the bold 「Energy Saving Mode」 lead is an h4. The risk box's printed warning triangle is not repeated (the symbol table carries it).
4. The print sets the safety bullets and the operating-instruction bullets in two columns; the Web runs each list in one column, in reading order (left column, then right).
5. USER MAINTENANCE INSTRUCTIONS (top of printed 02) stays at the end of the IMPORTANT SAFETY INFORMATION chapter, before MEANING OF SYMBOLS, as printed.
6. WARNING:, DANGER:, NOTE and CAUTION boxes are HB-CALLOUT-STRIP; the shared label drops the printed trailing colon (shared display_label policy).
7. The FCC block is HB-SPECIAL-FCC: the opening statement beside the FC mark, the NOTE paragraph in the left column and the interference paragraph, measures and MODIFICATION in the right (the print breaks the interference paragraph across the columns).
8. In-box cards are HB-SPECIAL-INBOX with its TIP row; the shared cards draw their own 1–3 ordinals.
9. LCD rows are HB-TABLE-LCD-ICON. The printed ⑧ spans the high- and low-temperature rows; the shared number column repeats 「8」 on both rows.
10. LCD SCREEN ON/OFF is HB-TABLE-LCD-MODE: the drawing from the table's left column and the state/action/description rows.
11. USB OUTPUT ON/OFF and USB-C CHARGING: the sentence printed in a pill at the top of each panel is a native paragraph above the panel; the panel art is the complete print panel with only that pill and its text removed. CAR CHARGING: the white caption pill 「* The car charging cable is sold separately.」 is removed from the panel the same way and follows it as a paragraph.
12. TROUBLESHOOTING is HB-TABLE-TROUBLESHOOTING; F7's three numbered measures keep their print line breaks.
13. Each ● specification table is one HB-TABLE-SPEC; multi-line values (DC8020 input, dual/triple-port modes) continue under the same label. The shared spec table carries plain text, so 「LiFePO4」 loses the printed subscript 4.
14. The warranty bold lead box and local note are HB-WARRANTY-LEAD; titled pills are h3 headings followed by HB-WARRANTY-SECTION cards; Warranty Period is HB-WARRANTY-YEARS with the 3/2 YEARS badges drawn by the shared component.
15. Figure captions and leader labels printed inside panels stay in the panel art and are carried as alt text and IR metadata, not repeated as visible text.
16. On phones the product overview pans sideways inside the figure; LCD, troubleshooting and spec tables scroll inside their shared components.
