# Deliberate Web layout differences from the printed JE-240A JP V2 manual

Wording is never changed. These are layout decisions only.

1. The cover (p1, with its thank-you and read-first notes, support e-mail and QR code) and printed page numbers are not on the Web page.
2. Chapter titles are shared h2 strips. The print letter-spaces them (「7.安 全 上 の ご 注 意」); the Web keeps the characters without the spacing. Headings keep print case (`source/geometry.css` sets text-transform: none).
3. The specification table title 【Jackery ポータブル電源 240】 is the HB-TABLE-SPEC section title; the printed colon after each label is kept. The shared table carries plain text, so 「LiFePO4」 has no subscript (as printed).
4. The ①–⑰ LCD legend printed in three columns is one HB-TABLE-REFERENCE/lcd-descriptions list in number order.
5. Each 液晶画面 description block (icon, bold title, text) becomes a row of HB-TABLE-LCD-ICON (unnumbered), in printed order, in two tables (p03 and p03–p04 groups) with the 省エネモード table and the frequency notes between them as printed. The 省エネモード table and the recycling box are declared plain tables.
6. The 絵表示について box prints only the two signal rows; the shared HB-TABLE-SYMBOL-SIGNAL draws its 表示/意味 header, and HB-TABLE-SYMBOL-ICON its 記号/意味 header (JE-1000D / JE-1500D JP V2 component chrome, not source text).
7. Each banded 警告/注意 item becomes one HB-CALLOUT-STRIP with the band label; the item's pictogram is not repeated (the symbol meanings are in the symbol table).
8. ● sub-headings are shared h3 headings; the bold 「Jackery SolarSaga 60/100 接続説明」 guide title and the 4.1–4.3 App items are h4.
9. The p11 App smart-control lead and its App Store / Google Play badges open the Jackeryアプリ ユーザーマニュアル chapter, directly after its h2 (in print they stand above the chapter title, after 10.免責事項).
10. 備考 lines in the App manual become HB-CALLOUT-STRIP/note with label 備考 (the printed 「備考：」 prefix is the label).
11. The 2.1 「+」 add-device glyph is native text in HB-SPECIAL-APP/inline-control.
12. 同梱品 cards are HB-SPECIAL-INBOX; the shared cards draw their own 1–4 ordinals (the printed ①–④ are cropped out of the card art).
13. Figure captions and leader labels printed inside panels stay in the panel art and are carried as alt text and IR metadata, not repeated as visible text.
14. On phones, the overview and LCD map pan sideways inside the figure; the 省エネモード table and recycling box scroll inside the shared table wrapper.
