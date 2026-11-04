# Deliberate Web layout differences from the printed JE-3000A JP manual

Wording is never changed. These are layout decisions only.

1. The cover (p1) is not on the Web page; printed page numbers are dropped. The print has no paper TOC.
2. The back cover (p14) carries the only App download notice in the manual, so it closes the Web page as an unheaded shared `hb-text-panel` plus the complete badge pair; no heading is invented for it.
3. Chapter titles are shared h2 strips. The print letter-spaces them (「6.安 全 上 の ご 注 意」); the Web keeps the characters without the spacing.
4. The specification table title 【Jackery ポータブル電源 3000 Pro】 is the HB-TABLE-SPEC section title; the printed colon after each label is kept. The two stacked labels 4×AC出力 / 1×AC出力 share one row as printed.
5. The Qualcomm quick charge 3.0 logo printed beside UN38.3 in the 認証 cell cannot sit inside the text-only spec cell; it follows the table as a small complete-logo figure, its printed text in the alt.
6. The ①–⑲ LCD legend printed in three columns is one HB-TABLE-REFERENCE/lcd-descriptions list in number order.
7. Each 液晶画面 description block (icon, bold title, text) becomes a row of HB-TABLE-LCD-ICON (unnumbered), in two tables (p3 and p4 groups) with the 省エネモード table and frequency notes between them as printed.
8. The 88H mark in the 省エネモード table and the thermometer in the 低温モード sentence are the same reused LCD files shown inline at text size.
9. The 絵表示について box prints only the two signal rows; the shared HB-TABLE-SYMBOL-SIGNAL draws its 表示/意味 header, and HB-TABLE-SYMBOL-ICON its 記号/意味 header (JE-1000D JP V2 component chrome, not source text).
10. Each banded 警告/注意 item becomes one HB-CALLOUT-STRIP with the band label; the item's pictogram is not repeated (the symbol meanings are in the symbol table).
11. The ご注意 framed box is HB-CALLOUT-STRIP/caution; its indented 保管時の残量… line stays a second paragraph of the third item.
12. ● section titles in 充電方法 are h3; the bold sub-titles (SolarSaga 60/100/200, SolarSaga 80, トランスジャック) are h4; 電源ON/OFF is h3 and the other ON/OFF leads are bold paragraphs, as their print weights differ.
13. Figure captions and leader labels printed inside panels stay in the panel art and are carried as alt text and IR metadata, not repeated as visible text.
14. On phones, the overview and LCD map pan sideways inside the figure; the LCD-icon tables, the 省エネモード table and recycling box scroll inside the shared table wrapper.
