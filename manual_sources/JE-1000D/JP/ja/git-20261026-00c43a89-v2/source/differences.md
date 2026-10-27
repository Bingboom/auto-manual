# Deliberate Web layout differences from the printed JE-1000D JP V2 manual

Wording is never changed. These are layout decisions only.

1. Cover (p1), paper TOC (p2) and back cover QR (p18) are not on the Web page; printed page numbers are dropped.
2. Chapter titles are shared h2 strips. The print letter-spaces them (「7.安 全 上 の ご 注 意」); the Web keeps the characters without the spacing.
3. The specification table title 【Jackery ポータブル電源 1000 】 is the HB-TABLE-SPEC section title; the printed colon after each label is kept.
4. Each 液晶画面 description block (icon, bold title, text) becomes a row of HB-TABLE-LCD-ICON (unnumbered), in printed order, in two tables (p03 and p04 groups) with the 省エネモード table and frequency notes between them as printed.
5. The ①–⑲ LCD legend printed in three columns is one HB-TABLE-REFERENCE/lcd-descriptions list in number order.
6. The 絵表示について box prints only the two signal rows; the shared HB-TABLE-SYMBOL-SIGNAL draws its 表示/意味 header, and HB-TABLE-SYMBOL-ICON its 記号/意味 header (JE-1500D JP V2 component chrome, not source text).
7. Each banded 警告/注意 item becomes one HB-CALLOUT-STRIP with the band label; the item's pictogram is not repeated (the symbol meanings are in the symbol table).
8. 備考 lines in the App manual become HB-CALLOUT-STRIP/note with label 備考 (the printed 「備考：」 prefix is the label).
9. The 2.1 「+」 add-device glyph is native text in HB-SPECIAL-APP/inline-control.
10. Warranty titled cards are a heading (the printed pill) plus HB-WARRANTY-SECTION; the lead, 免責事項 and contact panels are the shared hb-text-panel.
11. Figure captions and leader labels printed inside panels stay in the panel art and are carried as alt text and IR metadata, not repeated as visible text.
12. On phones, the overview and LCD map pan sideways inside the figure; the 省エネモード table and recycling box scroll inside the shared table wrapper.
