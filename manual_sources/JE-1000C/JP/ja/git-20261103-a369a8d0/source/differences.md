# Deliberate Web layout differences from the printed JE-1000C JP manual

Wording is never changed. These are layout decisions only.

1. Cover (p1, incl. support line, お買い上げ… lead and QR) and back cover (p14, App-store text and badges) are not on the Web page; printed page numbers are dropped. The print has no paper TOC.
2. Chapter titles are shared h2 strips. The print letter-spaces them (「8.安 全 上 の ご 注 意」); the Web keeps the characters without the spacing. 「5. バッテリーパック（別売）と併用」 keeps its printed space after 「5.」.
3. The specification table title 【Jackery ポータブル電源 1000 Plus】 is the HB-TABLE-SPEC section title; the printed colon after each label is kept; two-line values keep their line break.
4. Each 液晶画面 description block (icon, bold title, text) becomes a row of HB-TABLE-LCD-ICON (unnumbered), in printed order, in two tables with the 低電力モード port table, ON/OFF steps and frequency notes between them as printed.
5. The ①–⑱ LCD legend printed in three columns is one HB-TABLE-REFERENCE/lcd-descriptions list in number order.
6. The 絵表示について box prints only the two signal rows; the shared HB-TABLE-SYMBOL-SIGNAL draws its 表示/意味 header, and HB-TABLE-SYMBOL-ICON its 記号/意味 header (JE-1000D JP V2 component chrome, not source text).
7. Each banded 警告/注意 item becomes one HB-CALLOUT-STRIP with the band label; the item's pictogram is not repeated (the symbol meanings are in the symbol table).
8. 備考 lines in the App manual become HB-CALLOUT-STRIP/note with label 備考 (the printed 「備考：」 prefix is the label).
9. The 2.1 「+」 add-device glyph is native text in HB-SPECIAL-APP/inline-control.
10. The six numbered 同梱品 cards are HB-SPECIAL-INBOX/responsive-card-grid; the printed ①–⑥ numbers are not repeated.
11. Figure captions and leader labels printed inside panels stay in the panel art and are carried as alt text and IR metadata, not repeated as visible text. The SolarSaga 60/100/200 and SolarSaga 80 sub-headings become h4 headings.
12. On phones, the overview and LCD map pan sideways inside the figure; the 低電力モード table and recycling box scroll inside the shared table wrapper.
