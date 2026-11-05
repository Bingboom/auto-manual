# Deliberate Web layout differences from the printed JE-100C US English manual

Wording is never changed. These are layout decisions only.

1. Cover (p1), paper TOC (p2) and the back-cover QR code (p15) are not on the Web page; printed page numbers are dropped. The back-cover JACKERY INC. contact text closes the WARRANTY chapter in the shared text panel.
2. Chapter strips are shared h2 headings; ● sub-headings, the boxed 「INSTRUCTIONS PERTAINING TO RISK OF FIRE…」 heading and the dark 「USER MAINTENANCE INSTRUCTIONS」 pill are shared h3 headings. The risk box's printed warning triangle is not repeated (the symbol table carries it).
3. USER MAINTENANCE INSTRUCTIONS (top of printed 02) stays at the end of the IMPORTANT SAFETY INFORMATION chapter, where the print places it before MEANING OF SYMBOLS.
4. WARNING:, CAUTION and NOTE boxes are HB-CALLOUT-STRIP; the shared label drops the printed trailing colon of 「WARNING:」 (shared display_label policy).
5. The shared HB-TABLE-SYMBOL-SIGNAL draws the WARNING and CAUTION badges with the triangle and NOTE/TIP without, as printed.
6. The FCC block is HB-SPECIAL-FCC: the opening statement beside the FC mark, the NOTE paragraph in the left column and the interference paragraph, measures and MODIFICATION in the right. The print breaks the interference paragraph across the two columns and sets the whole first NOTE line in bold; the shared component bolds the 「NOTE:」 and 「MODIFICATION:」 labels.
7. In-box cards are HB-SPECIAL-INBOX; the shared cards draw their own 1–3 ordinals.
8. LCD interface rows are HB-TABLE-LCD-ICON. Printed circled numbers ①–⑩ are the shared number column. The interface-1 Fault code / temperature rows (printed 05, without numbers) are an unnumbered table. The battery-health colour bullets are a list inside the description cell.
9. LCD SCREEN: the drawing printed in the table's left column is a figure above the shared HB-TABLE-REFERENCE/lcd-actions-compact Function/Description table.
10. OUTPUT ON/OFF: the bullet printed in a grey pill inside the drawing panel is a native list item above the drawing. ENERGY SAVING MODE: the three paragraphs printed inside the panel are native paragraphs above the drawing.
11. Cart pills are the shared hb-source-purchase strip with the cart mark of the JE-100C EU Web edition.
12. Each ● specification table is one HB-TABLE-SPEC; multi-line values (Dimensions, USB-C1 input) continue under the same label. The shared spec table carries plain text, so 「LiFePO4」 loses the printed subscript 4.
13. Warranty pills are h3 headings followed by HB-WARRANTY-SECTION cards (JE-1000D JP precedent).
14. Figure captions and leader labels printed inside panels stay in the panel art and are carried as alt text and IR metadata, not repeated as visible text.
15. On phones the product overview pans sideways inside the figure; LCD tables scroll inside the shared component.
