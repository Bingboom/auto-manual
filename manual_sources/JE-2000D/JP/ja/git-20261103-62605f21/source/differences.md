# Deliberate Web layout differences from the printed JE-2000D-SG JP manual

Wording is never changed. These are layout and encoding decisions only.

1. The cover (physical 1: model, V2, product drawing, 国内専用/For use only in Japan, support address, お買い上げありがとうございます。 and the reading notes, QR) is not on the Web page; printed page numbers are dropped. The PDF prints no paper TOC and no back cover.
2. Chapter titles are shared h2 strips. The print letter-spaces them (「8.安 全 上 の ご 注 意」); the Web keeps the characters without the spacing.
3. The specification table title 【Jackery ポータブル電源 2000】 is the HB-TABLE-SPEC section title; the printed colon after each label is kept. The DC入力ポート and 保存温度 values' two print lines are one wrapped value.
4. 2.同梱品 ①–④ become the numbered cards of HB-SPECIAL-INBOX (the shared component draws the numbers); the card captions are native text. The ※ notes, the ■ change notice and the recycling box that the print sets under the cards stay in that order after the cards.
5. Each 液晶画面 description block (icon, bold title, text) becomes a row of HB-TABLE-LCD-ICON (unnumbered), in printed order, in two tables (p03 and p03–p04 groups) with the 省エネモード table and the OFF/ON and frequency notes between them as printed.
6. The ①–⑲ LCD legend printed in three columns is one HB-TABLE-REFERENCE/lcd-descriptions list in number order.
7. The 絵表示について box prints only the two signal rows; the shared HB-TABLE-SYMBOL-SIGNAL draws its 表示/意味 header, and HB-TABLE-SYMBOL-ICON its 記号/意味 header (JE-1000D JP V2 component chrome, not source text).
8. Each banded 警告/注意 item becomes one HB-CALLOUT-STRIP with the band label; the item's pictogram (prohibition, disassembly, wet, wet-hand, mandatory, unplug and the ground mark ⏚ of the last 警告 item) is not repeated (the symbol meanings are in the symbol table, as in JE-1000D JP V2).
9. 9.使用上のご注意: the first paragraph prints a 「・」 bullet and the four paragraphs after it do not; the Web keeps that as a one-item list followed by plain paragraphs, then the ・ list.
10. The App download paragraph and the App Store / Google Play badge pair printed after 10.免責事項 (p09) stay at the end of that chapter; the badge pair is one complete source panel.
11. 備考 lines in the App manual become HB-CALLOUT-STRIP/note with label 備考 (the printed 「備考：」 prefix is the label).
12. The 2.1 「+」 add-device glyph is native text in HB-SPECIAL-APP/inline-control.
13. Figure captions and leader labels printed inside panels stay in the panel art and are carried as alt text and IR metadata, not repeated as visible text. The 3.各部の名称 panel is rendered without the outlined 4.液晶画面 heading glyphs that sit inside its rectangle (in-memory redaction; the stored PDF is unchanged).
14. Bullet glyphs (・, ·, grey dots) are list markers of shared lists.
15. On phones, the overview and LCD map pan sideways inside the figure; the 省エネモード table and recycling box scroll inside the shared table wrapper.
16. Encoding of the outlined print: U+2393 ⎓ for the DC symbol, U+FF5E ～ for body wave dashes, U+007E ~ for the specification table's small tilde, U+00B0 + C/F for every degree sign (printed as two glyphs), U+FF65 ･ for the half-width middle dot, U+00D7 × where the multiplication sign is printed. Multiple spaces visible in the print (「2.4　 デバイス」, 「下の  QR  コード」, 「電源コード  (ACアダプター)」) are recorded as one.
