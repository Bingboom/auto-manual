# Deliberate Web layout differences from the printed JE-1500B US manual

Wording is never changed. These are layout decisions only.

1. Cover (p1) and back cover (p11, address and QR) are not on the Web page; printed page numbers, the
   "US" page tabs and the "US English" band label are dropped. The band's "Model: JE-1500B" stays as the
   first bold line. The page title "Jackery Explorer 1500 Pro User Manual" is composed from the cover lines
   USER MANUAL / Jackery Explorer 1500 Pro.
2. Chapter titles are shared h2 strips; sub-titles (Product Appearance, Power On/Off, connection guides,
   warranty sections, …) are shared h3 headings, which the shared theme displays in capitals.
   CHARGING FROM THE WALL, SOLAR ENERGY CHARGING and CHARGING IN THE CAR print at chapter size and are h2.
3. Each specification group (GENERAL INFO, OUTPUT PORTS, INPUT PORTS, ENVIRONMENTAL OPERATING TEMPERATURE)
   is one HB-TABLE-SPEC whose section title is the printed group title; the second DC Input value line is a
   continuation row of the same label.
4. The certification-mark row and the FCC logo are complete source crops, not a symbol table.
5. The MODIFICATION statement printed at the top of p02 follows the trademark footnotes, before PACKAGE LIST.
6. PACKAGE LIST uses HB-SPECIAL-INBOX (responsive card grid); the printed ①–⑤ are the component's card numbers.
7. The ①–⑮ LCD legend printed in three columns is one HB-TABLE-REFERENCE/lcd-descriptions list in number
   order, with the printed marker (including the plain "10").
8. The LCD icon + bold title + text blocks are HB-TABLE-LCD-ICON (unnumbered) in two tables, with the Low
   Power Mode table (declared plain table) and its on/off instructions between them as printed.
9. "Caution:", "Tip:" and "Warm Tip:" run-ins become HB-CALLOUT-STRIP caution/tip with the printed word as
   label; the shared callout drops the colon after the label.
10. Figure captions and leader labels printed inside panels stay in the panel art and are carried as alt text
    and IR metadata, not repeated as visible text.
11. On phones, the overview and LCD map pan sideways inside the figure; the LCD icon tables and the Low Power
    Mode table scroll inside their shared components.
