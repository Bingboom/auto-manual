# Deliberate Web layout differences from the printed JE-240A US English manual

Wording is never changed. These are layout decisions only.

1. The cover (p1), the back-cover QR code (p14), printed page numbers and the 「US」 corner tabs are not on the Web page. The back-cover JACKERY INC. text closes the last chapter in the shared text panel.
2. The printed 「US English … Model: JE-240A」 band is the first chapter strip, with the model as the shared hb-heading-model label. Chapter titles are the shared chapter strips; sub-headings are shared h3/h4 headings. Headings keep print case (`source/geometry.css` sets text-transform: none).
3. TECHNICAL SPECIFICATIONS is the HB-TABLE-SPEC section title; the 18 rows are one shared spec table. The shared table carries plain text, so 「LiFePO4」 has no subscript (as printed).
4. CERTIFICATIONS: the printed mark row (FC, BC, crossed-out bin) is one complete source panel; PACKAGE LIST cards are HB-SPECIAL-INBOX, whose cards draw their own 1–3 ordinals (the printed ①–③ are cropped out of the card art).
5. The ①–⑰ LCD legend printed in three columns is one HB-TABLE-REFERENCE/lcd-descriptions list in number order.
6. LCD icon blocks (icon, bold title, text) are rows of HB-TABLE-LCD-ICON (unnumbered), in two tables (printed 03 and 04) with the Energy Saving table and its two bold leads between them, as printed. The Energy Saving table is a declared plain table; its Defaults cell spans the three rows as printed.
7. Bold run-in leads (UPS:, Main power on/off:, Tip:, WARNING:, DANGER: …) stay bold inside native paragraphs; 「Note:」 and the two 「To turn off/on the Energy Saving Mode」 leads are bold paragraphs.
8. The FCC block is HB-SPECIAL-FCC: FC mark and the NOTE paragraph in the left column; the four 「--」 measures (kept verbatim) as a list and MODIFICATION in the right. The print stacks them in one column under the mark.
9. Warranty bold titles are h3 headings followed by HB-WARRANTY-SECTION cards; 「Download the Jackery Mobile App」 is a heading above the complete badge panel.
10. 2.1: the round 「+」 add-device glyph is native text in HB-SPECIAL-APP/inline-control.
11. Figure captions and leader labels printed inside panels stay in the panel art and are carried as alt text and IR metadata, not repeated as visible text. App screenshots keep complete phone frames.
12. On phones the product appearance and LCD map pan sideways inside the figure; tables scroll inside the shared table wrapper.
