# JHP-1000A US V2 — deliberate Web layout differences

Wording is never changed; every difference below is layout only.

1. Cover (p1), paper TOC (p3), back cover (p21), printed page numbers and the EN language badge beside IMPORTANT are not on the Web (`web_exclusions`).
2. The print's two-column safety, FCC and warranty pages flow in one column; column breaks are not kept.
3. Chapter title strips, ● subsection titles and bold lead-in labels use the shared h2/h3/h4 headings. The boxed 「INSTRUCTIONS PERTAINING TO RISK …」 band prints no signal word, so it is an h3 heading (as in JE-1500D US); its triangle is not repeated.
4. The WARNING precaution box on p4, the grounding WARNING, the DANGER box and every CAUTION/NOTE/WARNING side box use the shared `HB-CALLOUT-STRIP` callout; the shared signal triangle replaces the print's per-box glyph.
5. The GROUNDING INSTRUCTION is printed as the last bullet of SAVE THESE INSTRUCTIONS (continued on p5) and stays that bullet.
6. Six operation/charging panels hold body copy inside the drawing (standby time box, prerequisite pills, AC footer note, energy-saving instruction, LED mode line and steps, AC charging caption). That copy is removed from the panel art by vector strip and set as native text in the shared grey `hb-text-panel` or, for the three LED steps, an ordered list beside the remaining ①②③ icons.
7. The LCD SCREEN mode table and its button art use the shared `HB-TABLE-LCD-MODE`; the KEY COMBINATIONS table uses `HB-TABLE-KEY-COMBINATIONS`, whose shared minimum width scrolls inside the component.
8. The two Symbol/Meaning pictogram tables use one `HB-TABLE-SYMBOL-ICON` with two panels (3 + 4 rows); the signal-word table shows the shared triangle on every badge.
9. Specification groups use the shared `HB-TABLE-SPEC` section strips; numbered troubleshooting steps show one step per line.
10. The FCC panel keeps a navigation-only "FCC" title hidden by the shared FCC style, as every published FCC section does.
11. Leader labels, button silk, step numbers and screenshot captions stay in the complete source panels; they are listed in `transcription.json` (`fig.*`, `ov.*`) and bound to each figure's alt text and IR `embedded_labels`.
