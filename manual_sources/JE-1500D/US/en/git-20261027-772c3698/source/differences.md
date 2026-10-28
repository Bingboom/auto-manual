# Deliberate Web layout differences from the printed JE-1500D US V2 manual

Wording is never changed. These are layout decisions only.

1. Cover (p1), paper TABLE OF CONTENTS (p3) and back cover (p21: JACKERY INC. address, contact, QR) are not on the Web page; printed page numbers are dropped. The IMPORTANT preface (p2) is the first Web chapter; its printed 「EN」 language tab is print-only chrome.
2. Chapter titles are shared h2 strips; the round-bullet sub-titles (FRONT VIEW, POWER ON/OFF, CHARGING VIA …, KEY COMBINATIONS, 1. To download the App and log in …) are h3, and 4.1–4.3 under 4. Notes are h4. The INSTRUCTIONS PERTAINING TO RISK … band, OPERATING INSTRUCTIONS and USER MAINTENANCE INSTRUCTIONS pills are h3, SAVE THESE INSTRUCTIONS is h4.
3. The WARNING box and the bullets printed under it are one HB-CALLOUT-STRIP/warning: the bold lead is the first body line, the bullets its list. DANGER, TIP, CAUTION and NOTE boxes are HB-CALLOUT-STRIP in their printed variant with the printed label.
4. The FCC statement printed below the symbol tables is HB-SPECIAL-FCC (two columns as printed) inside a generic docutils container, so MEANING OF SYMBOLS keeps its visible heading. The shared FCC renderer runs the two left paragraphs before NOTE together.
5. The WARNING/CAUTION/NOTE/TIP signal table is HB-TABLE-SYMBOL-SIGNAL with the printed Symbol/Meaning headers; the badges are drawn by the shared component. The 11-symbol table is HB-TABLE-SYMBOL-ICON with its two printed panels (6 + 5 rows).
6. The 23 LCD description rows (with the two temperature rows sharing ⑳) are one numbered HB-TABLE-LCD-ICON across printed pages 05–06. Printed bold On:/Blink:/Off: stay bold; the plain On:/Off: of row ㉑ stays plain.
7. Operation panels are complete source panels. Grey text boxes and pills printed inside them (the standby-time bubble, the two 「Prerequisite: The product is turned on.」 pills, the LED mode pill and footnote box, the Energy Saving 「On/Off:」 pill, the car-cable note) are removed from the art by deleting their vector objects (no overpainting) and set as native text in the shared grey `hb-text-panel` directly before or after the panel. Button labels (On / Press once …), LED step labels, Vehicle and the SolarSaga caption stay in the art and in alt text / IR metadata.
8. LCD SCREEN ON/OFF is HB-TABLE-LCD-MODE (two states × three actions) with its artwork; KEY COMBINATIONS is HB-TABLE-KEY-COMBINATIONS with the shared POWER, DC/USB and AC button SVGs, the shared clock duration mark and the shared emphasis on button names.
9. In the App NOTE about 「the device has been bound」 the printed bold quote is plain: the shared callout carrier binds its body as plain text.
10. Troubleshooting is HB-TABLE-TROUBLESHOOTING; the merged F0–F3 cell 「Restart the product.」 is repeated on each code row.
11. SPECIFICATIONS: the four printed groups are four HB-TABLE-SPEC/vertical tables whose section titles are the printed group titles; lines printed in one cell stay in one cell, and the second USB-C value cell is its own row.
12. Warranty: the bold lead and the *Warranty period note are HB-WARRANTY-LEAD; each titled card is the printed title pill (h3) plus HB-WARRANTY-SECTION; 3 YEARS / 2 YEARS is HB-WARRANTY-YEARS.
13. App: the download pair is HB-SPECIAL-APP/download, the 2.1 「+」 glyph is native text in HB-SPECIAL-APP/inline-control; phone screenshots and the button map are complete panels.
14. Straight apostrophes stay straight: the Web build disables Sphinx smart quotes.
15. On phones, overview panels and the LCD map pan sideways inside the figure; the LCD and key-combination tables scroll inside their shared components (also on desktop for the 44rem key-combination table).
