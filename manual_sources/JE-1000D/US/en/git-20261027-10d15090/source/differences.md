# Deliberate Web layout differences from the printed JE-1000D US English manual

Wording is never changed. These are layout and encoding decisions only.

1. Cover (physical 1) and back cover (physical 14: JACKERY INC. address, contact line, QR) are not on the Web page; the running US tabs and printed page numbers are dropped.
2. The p01 section band (US English / Model: JE-1000D) is a shared hb-text-panel before the intro paragraphs.
3. The TECHNICAL SPECIFICATIONS heading is the HB-TABLE-SPEC section title (the shared spec carrier draws it as the chapter h2). The DC Input value's three print lines are one wrapped value.
4. CERTIFICATIONS marks are three images in one paragraph (FCC and WEEE shared catalog files, BC native paths); the p09 FCC mark is the same FCC file.
5. PACKAGE LIST ①–③ become the numbered cards of HB-SPECIAL-INBOX; the shared component draws the numbers.
6. The ①–⑲ LCD legend printed in three columns across p02/p03 is one HB-TABLE-REFERENCE/lcd-descriptions list in number order.
7. Each LCD description block (icon, bold title, text) becomes a row of HB-TABLE-LCD-ICON (unnumbered), in printed order, in two tables (p03 and p04 groups) with the Energy Saving Mode table and its on/off instructions between them as printed.
8. The Energy Saving Mode table keeps its printed Defaults cell spanning the three port rows (declared plain table).
9. Bold run-in titles printed in the small bold style (UPS:, To turn off/on the Energy Saving Mode, LCD Screen On/Off, LCD is off automatically, Emergency Charging Mode, SAVE THESE INSTRUCTIONS) stay bold paragraphs; section headings printed in the larger style are h3. Charging via Car Charger is printed in the small style but is the third "Charging via …" section, so it is an h3 like its two siblings.
10. CAUTION: blocks (p04, p07), the WARNING: / DANGER: run-in notices (p09) and the Remarks: notes (p11, p12) become HB-CALLOUT-STRIP caution / warning / danger / note. The shared strip shows the signal word without its printed trailing colon (callout label normalisation, as in the JE-1000D JP edition); the words are unchanged.
11. Bullet glyphs (•, grey dots) are list markers of shared lists. The a)–m) safety items keep their printed letters as text in one paragraph each.
12. The Note: 1./2. charging notes, *-prefixed notes and Tip: stay plain paragraphs as printed (no frame in the print).
13. The 2.1 「+」 add-device glyph is native text in HB-SPECIAL-APP/inline-control.
14. Figure captions and leader labels printed inside panels stay in the panel art and are carried as alt text and IR metadata, not repeated as visible text.
15. Warranty sections are h3 headings with paragraphs (the print draws no cards). Download the Jackery Mobile App is an h3 followed by the complete badge pair.
16. On phones, the overview and LCD map pan sideways inside the figure; the LCD description and Energy Saving Mode tables scroll inside the shared table wrapper.
17. Text encoding: ligature code points of the text layer (U+FB00–U+FB03) are written as their letters (ff, fi, fl, ffi) — the printed glyphs are those letters. Other code points are kept as encoded, including U+2109 ℉ in the specification temperatures, U+2393 ⎓, and the full-width colon in 4.3. The registered marks in the trademark line follow the print (no space after ®); the text layer has a space under each superscript (see source_concerns). Multiple spaces inside a line are kept in the transcription; HTML displays them as one.
