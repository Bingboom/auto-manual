# JE-2000F US V2 — deliberate Web layout differences

Wording is never changed; every difference below is layout only.

1. Cover (p1), paper TOC (p3), back cover (p22), printed page numbers, the EN language badge beside IMPORTANT and the ①–④ number badges of the in-box cards are not on the Web (`web_exclusions`).
2. The print's two-column safety, FCC and warranty pages flow in one column; column breaks are not kept.
3. Chapter title strips, ● subsection titles and bold lead-in labels use the shared h2/h3/h4 headings. The triangle band "INSTRUCTIONS PERTAINING TO RISK OF FIRE, ELECTRIC SHOCK, OR INJURY TO PERSONS" prints no signal word, so it is an h3 heading (JE-1500D US idiom), not a callout.
4. The WARNING precaution box, the grounding WARNING, the DANGER box and every CAUTION/NOTE/WARNING side box use the shared `HB-CALLOUT-STRIP`; the shared label column replaces the print's per-box triangle glyph.
5. Five operation/charging panels hold body copy inside the drawing (standby time box and the Energy Saving Mode note, prerequisite pills, the LED mode line and steps, the energy-saving instruction box, the AC charging caption). That copy is removed from the panel art by vector strip and set as native text: the shared grey `hb-text-panel`, a plain paragraph, or for the three LED steps an ordered list below the remaining ①②③ icons. The POWER panel keeps its full frame, so the area that held the removed copy stays empty inside the frame.
6. The two Symbol/Meaning pictogram tables (6 + 5 rows) and the battery-disposal symbol box printed at the top of p6 use one `HB-TABLE-SYMBOL-ICON` with two panels of six rows; the battery box closes the right panel. Its three printed lines are kept as three lines in the meaning cell.
7. The FCC panel has no printed heading; it follows the symbol tables inside MEANING OF SYMBOLS in a container (JE-1500D US idiom), so no navigation-only title is added.
8. The LCD SCREEN mode table uses the shared `HB-TABLE-LCD-MODE` beside its button art; KEY COMBINATIONS uses `HB-TABLE-KEY-COMBINATIONS`, whose shared 44rem minimum width scrolls inside the component (also at 1280 px in the 46rem reading column).
9. ㉒ spans the high- and low-temperature rows in print; the shared numbered LCD table repeats ㉒ on both rows.
10. Specification groups use the shared `HB-TABLE-SPEC` section strips; numbered troubleshooting steps show one step per line; the "Fully charge the product before its first use." pill is a bold paragraph.
11. Leader labels, button silk, step numbers and screenshot captions stay in the complete source panels; they are listed in `transcription.json` (`fig.*`, `ov.*`) and bound to each figure's alt text and IR `embedded_labels`.
12. On phones the overview views, the LCD map and the App control panel pan horizontally inside their figure (geometry.css) so leader labels stay legible.
