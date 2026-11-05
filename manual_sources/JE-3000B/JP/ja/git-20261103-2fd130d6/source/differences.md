# Deliberate Web layout differences from the printed JE-3000B JP V2 manual

Wording is never changed. These are layout decisions only.

1. The cover (physical page 1: brand, model, V2, 取扱説明書, 国内専用, support address, お買い上げ… preface and QR) is not on the Web page, as in JE-1000D JP V2; printed page numbers are dropped. The PDF has no paper TOC and no back cover.
2. Chapter titles are shared h2 strips. The print letter-spaces them (「8.安 全 上 の ご 注 意」); the Web keeps the characters without the spacing.
3. The specification table title 【Jackery ポータブル電源 3000】 is the HB-TABLE-SPEC section title; the printed colon after each label is kept. The full-width row 「5ポート合計3000W (瞬間最大6000W)」 is a label cell with an empty value cell.
4. The 同梱品 four cards are the shared HB-SPECIAL-INBOX variable-card variant without a tip; the ※ notes, the ■ change notice and the recycling box follow in printed order inside 2.同梱品.
5. Each 液晶画面 description block (icon, bold title, text) becomes a row of HB-TABLE-LCD-ICON (unnumbered), in printed order, in three tables (p3 first group; p3 second group; p4 group) with the 省エネモード table, its notes and the 自家発電モード drawing between them as printed. The 自家発電モード drawing printed beside its text follows the second table.
6. The ①–⑲ LCD legend printed in three columns is one HB-TABLE-REFERENCE/lcd-descriptions list in number order.
7. The 絵表示について box prints only the two signal rows; the shared HB-TABLE-SYMBOL-SIGNAL draws its 表示/意味 header, and HB-TABLE-SYMBOL-ICON its 記号/意味 header (JE-1000D / JE-1500D JP V2 component chrome, not source text).
8. Each banded 警告/注意 item becomes one HB-CALLOUT-STRIP with the band label; the item's pictogram is not repeated (the symbol meanings are in the symbol table).
9. 9.使用上のご注意: only the first paragraph carries a printed 「・」; it is a one-item list, and the four paragraphs printed at the margin after it stay paragraphs.
10. 備考 lines in the App manual become HB-CALLOUT-STRIP/note with label 備考 (the printed 「備考：」 prefix is the label).
11. The 2.1 「+」 add-device glyph is native text in HB-SPECIAL-APP/inline-control.
12. Figure captions and leader labels printed inside panels stay in the panel art and are carried as alt text and IR metadata, not repeated as visible text.
13. On phones, the overview and LCD map pan sideways inside the figure; the 省エネモード table and recycling box scroll inside the shared table wrapper.
