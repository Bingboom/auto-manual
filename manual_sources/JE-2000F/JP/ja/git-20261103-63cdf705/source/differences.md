# Deliberate Web layout differences from the printed JE-2000F JP manual

Wording is never changed. These are layout decisions only.

1. Cover (p1), paper TOC (p2) and back cover (p27, App promotion that repeats printed page 23) are not on the Web page; printed page numbers are dropped.
2. Chapter titles are shared h2 strips; ● subsection titles are h3; App 4.1–4.3 titles are h4. ■ section labels and the bold notices are strong paragraphs (the ■ is kept where it is a text-layer character).
3. The 絵表示について box becomes HB-TABLE-SYMBOL-SIGNAL with the shared 表示/意味 header and HB-TABLE-SYMBOL-ICON draws its 記号/意味 header (JE-1000D / JE-1500D JP V2 component chrome, not source text). The triangle icon shows on 警告/注意 only, as printed.
4. The p02 recycling boxes: the Li-ion 32 notice is a declared plain two-cell table (its mark has no admitted shared variant yet); the WEEE and battery crossed-bin boxes are a second HB-TABLE-SYMBOL-ICON (one row per panel).
5. Each banded 警告/注意 item becomes one HB-CALLOUT-STRIP with the band label; the item's pictogram is not repeated. The two-column p02 grid is read column by column (left column, then right), the order of the text layer.
6. 使用上のご注意 / 免責事項 grey boxes and the in-panel texts (standby bubble, 前提 pills, frequency text box, energy-saving text boxes, LED mode line, UPS bubble and texts, emergency charging, accessory box) are shared hb-text-panel paragraphs; the framed ■ sections of p04–p05 are flow paragraphs and lists.
7. Panel body copy (standby bubble, 前提 pills, LED step texts, UPS bubble) is stripped from the art on an in-memory copy and set as native text next to the figure; leader labels and short captions stay in the art and are carried as alt text and IR metadata.
8. The 液晶画面 rows are numbered HB-TABLE-LCD-ICON rows; ㉒ prints one number for two rows and is repeated on the low-temperature row. The ⑮ small second line 「Jackeryアプリで有効/無効にできます」 is a second line of the name cell.
9. The 省エネモード heading drops the 88H glyph printed after it; inside the copy the 88H glyph is the inline reused LCD energy-saving icon.
10. The 省エネモード port table is a declared plain table; its merged default-setting cell keeps rowspan 2.
11. Bullets printed with text-layer markers (•, ◦) become shared lists; 「・」 lines (UPS devices, warranty) keep the printed character as plain lines.
12. The トラブルシューティング code cell 「F0 / F1」「F2 / F3」 keeps its two printed lines; numbered measures are one step per line.
13. The 主な仕様 group titles (● 基本情報 …) are the HB-TABLE-SPEC section titles; multi-line values keep their printed lines.
14. Warranty title pills are headings followed by HB-WARRANTY-SECTION cards; the lead, 免責事項 and contact blocks are hb-text-panel paragraphs; the contact icons are dropped.
15. 備考 boxes in the App manual become HB-CALLOUT-STRIP/note; the 2.1 「+」 add-device glyph is native text in HB-SPECIAL-APP/inline-control.
16. On phones, the overview, LCD map and App panel figures pan sideways inside the figure; wide tables scroll inside the shared table wrapper.
