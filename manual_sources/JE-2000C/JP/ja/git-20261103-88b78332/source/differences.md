# Deliberate Web layout differences from the printed JE-2000C JP manual

Wording is never changed. These are layout decisions only.

1. The cover (p1) and printed page numbers are not on the Web page. The back-cover App download copy, badges and QR (p16) close the App chapter.
2. Chapter titles are shared h2 strips. The print letter-spaces them (「8.安 全 上 の ご 注 意」) and the 警 告 / 注 意 bands; the Web keeps the characters without the spacing (`line_map.json` op `despace`).
3. The specification table title 【Jackery ポータブル電源 2000 Plus】 is the HB-TABLE-SPEC section title; the printed colon after each label is kept. The printed 4×AC / 1×AC group keeps 「5ポート合計3000W (瞬間最大6000W)」 as its own continuation row.
4. The 認証： row of the specification table becomes a bold label paragraph followed by the complete logo panel (UN38.3, Qualcomm Quick Charge 3.0); the spec component carries text values only.
5. The ①–㉑ LCD legend printed in three columns is one HB-TABLE-REFERENCE/lcd-descriptions list in number order; the shared table draws the circled numbers.
6. Each 液晶画面 description block (icon, bold title, text) becomes a row of HB-TABLE-LCD-ICON (unnumbered), in printed order, in two tables (p3 and p4 groups) with the 省エネモード table and frequency notes between them as printed.
7. The 絵表示について box prints only the two signal rows; the shared HB-TABLE-SYMBOL-SIGNAL draws its 表示/意味 header, and HB-TABLE-SYMBOL-ICON its 記号/意味 header (JE-1000D / JE-1500D JP V2 component chrome, not source text).
8. Each banded 警告/注意 item becomes one HB-CALLOUT-STRIP with the band word as label; the item's pictogram is not repeated (the symbol meanings are in the symbol table).
9. 備考 lines in the App manual become HB-CALLOUT-STRIP/note with label 備考 (the printed 「備考：」 prefix is the label). The boxed ご注意 list (charging) is HB-CALLOUT-STRIP/caution.
10. The 2.1 「+」 add-device glyph (a vector mark in a gap of the text line) is native text in HB-SPECIAL-APP/inline-control.
11. Printed 「・」 list markers become shared list items with the 「・」 marker from geometry.css (`line_map.json` op `strip_bullet`); drawn ● markers of sub-headings are the shared h3 style.
12. Figure captions and leader labels printed inside panels stay in the panel art and are carried as alt text and IR metadata, not repeated as visible text.
13. On phones, the overview, LCD map and prohibited-connection panel pan sideways inside the figure; the 省エネモード table and recycling box scroll inside the shared table wrapper.
