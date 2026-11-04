# Deliberate Web layout differences from the printed JE-1000G JP V3 manual

Wording is never changed. These are layout decisions only.

1. Cover (p1), paper TOC (p2) and back cover App/QR block (p28) are not on the Web page; printed page numbers are dropped.
2. Chapter titles are shared h2 strips and ● subsection titles shared h3 headings; 緊急充電モード： and the App 4.1–4.3 lead lines are h4.
3. The 絵表示について box prints no header row; the shared HB-TABLE-SYMBOL-SIGNAL draws its 表示/意味 header and HB-TABLE-SYMBOL-ICON its 記号/意味 header (JE-1000D / JE-1500D JP V2 component chrome, not source text). 説明 and ヒント rows carry no triangle, as printed.
4. The 本製品を火気の近くに置かないでください。 symbol row is withheld from the 絵表示の説明 table until the coordinator adds its shared variant (no admissible shared symbol; `source_manifest.json:pending_shared_symbols`). The left panel therefore shows four rows instead of five.
5. Each pictogram row of the 警告/注意 grids (p02–p03) becomes one HB-CALLOUT-STRIP with the band label; the row pictogram is not repeated (the symbol meanings are in the symbol table), and the two-column grids read left column then right column.
6. The recycling box (Li-ion 32 and crossed-bin marks) and the 省エネモード port table are declared plain tables (`shared_component_exceptions`); the default-setting cell keeps its two-row span.
7. The inline 88H mark printed in the 省エネモード copy is the LCD energy-saving icon inline in the text; the mark printed beside the 省エネモード heading is not repeated in the heading.
8. In-panel body copy (standby bubble, 前提 pills, 50Hz/60Hz text box, LED mode line and step texts, UPS bubble, energy-saving text and table) is native Web text in hb-text-panel paragraphs, plain paragraphs, a table or an ordered list next to the panel art; the art keeps its button labels, captions and step numbers.
9. The ①–③ in-box card numbers are not repeated (the shared inbox card carries no marker; card order kept).
10. The 1–25 number column of the LCD table is the shared numbered HB-TABLE-LCD-ICON (circled numbers; ㉒ repeated on the 低温インジケーター row as printed); ⑮'s grey sub-note sits under its name.
11. The key-combination table, auto-resume table and LCD-screen table are HB-TABLE-KEY-COMBINATIONS, HB-TABLE-AUTO-RESUME and HB-TABLE-LCD-MODE; the plus sign and clock glyph are component chrome.
12. Warranty titled cards are a heading (the printed pill) plus HB-WARRANTY-SECTION; the lead, 免責事項 and contact panels are the shared hb-text-panel. Leading 「・」 bullets of printed lists are carried by the list marker.
13. 備考 / ご注意 / 説明 side boxes become HB-CALLOUT-STRIP note / caution with the printed label.
14. The 2.1 「+」 add-device glyph is native text in HB-SPECIAL-APP/inline-control.
15. Figure captions and leader labels printed inside panels stay in the panel art and are carried as alt text and IR metadata, not repeated as visible text.
16. On phones, the overview views, LCD map and App panel pan sideways inside the figure; plain tables scroll inside the shared table wrapper. The shared theme upper-cases Latin letters in some headings (e.g. 50HZ/60HZ, JACKERY); the source text is unchanged.
