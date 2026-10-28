# Deliberate Web layout differences from the printed JE-2000A US en manual

Wording is never changed. These are layout decisions only.

1. Cover (p1) and back cover (p19) are not on the Web page; the 「US」 region tabs, the 「US English」 band label and printed page numbers are dropped. The band's 「Model: JE-2000A」 opens the page as a bold paragraph.
2. Chapter titles are shared h2 strips; sub-headings are shared h3/h4 headings. The shared theme sets h3 in capitals; the characters in the page are as printed.
3. Each specification group (GENERAL INFO, OUTPUT PORTS, INPUT PORTS, ENVIRONMENTAL OPERATING TEMPERATURE) is one HB-TABLE-SPEC whose section title is the group heading; the second DC Input line is a spanned row of the same label.
4. The certification mark row and its CAN ICES-003(B)/NMB-003(B) line are one complete source panel; the line is also in the alt text and IR.
5. PACKAGE LIST cards are HB-SPECIAL-INBOX cards; the shared card number (1–5) stands in for the printed ①–⑤ marker.
6. The ①–⑮ LCD legend printed in two side-by-side columns is one declared three-column table (number, glyph, name) in number order.
7. Battery Power Indicator / Low Battery Indicator / Low Power Mode / Fault Code keep their printed 「Name (glyph) :」 run-in titles with the inline glyph; the body follows as a paragraph.
8. 「Tip:」, 「Caution:」, 「WARNING：」 and 「DANGER:」 run-in labels are HB-CALLOUT-STRIP labels; the shared label slot carries the word without its trailing colon (as JE-1000D JP 「備考：」).
9. Figure captions and leader labels printed inside panels stay in the panel art and are carried as alt text and IR metadata, not repeated as visible text.
10. ❶–❹, a.–i., a)–n), 1)–5) and 1.–3. markers stay in the paragraph text; 「·」 bullet lists are lists whose marker is drawn by `source/geometry.css`.
11. The troubleshooting table keeps its three printed columns and the spanned 「Error Code (F0-F9)」 cell; each F0–F9 glyph leads its Types cell.
12. Warranty section titles are headings drawn as the shared pill above HB-WARRANTY-SECTION cards.
13. On phones, the front overview, LCD map and prohibited-connection panel pan sideways inside the figure; tables scroll inside the shared table wrapper.
