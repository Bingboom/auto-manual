# Deliberate Web layout differences from the printed JE-100C JP Japanese manual

Wording is never changed. These are layout decisions only.

1. The cover (p1, including its 型番 line, support pill and お買い上げありがとうございます notes), the back-cover QR page (p16), printed page numbers and the contact-pill icons are not on the Web page.
2. Chapter strips are shared h2 headings; the pill sub-headings 絵表示について / 絵表示の説明 and every ● sub-heading are shared h3 headings.
3. The 警告 / ご注意 / 説明 / ヒント box is HB-TABLE-SYMBOL-SIGNAL; the shared component draws the triangle badge on all four rows, as printed, and requires the header pair 表示 / 意味, which the print does not show (JE-1000D JP precedent).
4. 絵表示の説明 is HB-TABLE-SYMBOL-ICON in its two printed panels (7 + 4 rows); the shared component requires the header row 記号 / 意味 / 記号 / 意味, which the print does not show. The multi-line Li-ion and WEEE texts keep their printed line breaks.
5. Each 警告 / 注意 item is one HB-CALLOUT-STRIP with its band label (警告, 警告, 注意); the item's pictogram is not repeated (the symbol meanings are in the symbol table), following JE-1000D JP. The four-point list of the second 警告 band stays one callout with its lead, list and follow-up paragraphs.
6. The ご注意 / 注意 grey label boxes are HB-CALLOUT-STRIP/caution with the printed label.
7. The five ■ boxes of 使用上のご注意, the 免責事項 box and the ※ notes box of 同梱品 are shared hb-text-panel groups; the printed divider lines between the ■ boxes are the gaps between panels. The ◦ sub-items of the temperature bullet are a nested list.
8. 同梱品 cards are HB-SPECIAL-INBOX; the shared cards draw the 1–3 ordinals the print shows.
9. 出力オン/オフ: the sentence printed in a grey pill inside the drawing panel is a native paragraph above the drawing. 省エネモード: the three paragraphs printed inside the panel are native paragraphs above the drawing.
10. The 「※ …は別売りです。」 pills printed inside the USB-C charger, solar and car panels are native paragraphs after each figure; the reused charger and solar panels and the new car crop end above the pill.
11. LCD rows are HB-TABLE-LCD-ICON. Printed circled numbers are the shared number column; the F8 / 高温 / 低温 rows (printed 07, without numbers) are an unnumbered table; the 緑/黄/赤 bullets are a list inside the description cell.
12. LCDスクリーン: the drawing printed in the table's left column is a figure above the shared HB-TABLE-REFERENCE/lcd-actions-compact 機能 / 説明 table.
13. Each ● specification table is one HB-TABLE-SPEC; the three USB-C1 input rows continue under the same label. 「LiFePO₄」 keeps the subscript as the Unicode character.
14. 保証について pills are h3 headings followed by HB-WARRANTY-SECTION cards (JE-1000D JP precedent); the 電話 / メール lines are one paragraph with the printed line break; the three contact pills close the chapter in a shared text panel.
15. Figure captions and leader labels printed inside panels stay in the panel art and are carried as alt text and IR metadata, not repeated as visible text.
16. On phones the product overview pans sideways inside the figure; LCD tables scroll inside the shared component.
