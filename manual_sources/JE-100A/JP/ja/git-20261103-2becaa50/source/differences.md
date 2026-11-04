# Deliberate Web layout differences from the printed JE-100A JP manual

Wording is never changed. These are layout decisions only.

1. The cover (p1, including its support e-mail, the read-first notes and the QR code) and the printed page numbers are not on the Web page.
2. 「1. 技術仕様」 is the HB-TABLE-SPEC section title (the print has no separate table title); the 認証 UN38.3 line printed under the table is its last row. Labels keep their printed colons.
3. The other chapter titles are shared h2 headings (the shared theme sets Latin letters in capitals; the print letter-spaces 7–9); ● sub-headings are h3 and the bold solar guide titles h4. The ● bullet itself is theme chrome.
4. The 充電式電池のリサイクルについて box is a declared plain two-cell table (`shared_component_exceptions`), as in JE-1000D JP V2.
5. 同梱物 cards are HB-SPECIAL-INBOX; the shared cards draw 1–3 ordinals the print does not show.
6. The LCD icon blocks are two unnumbered HB-TABLE-LCD-ICON tables in printed order, with the two 低電力モード ON/OFF paragraphs between them.
7. The ご注意 boxed list under 充電時の注意事項 is a shared caution callout labelled ご注意.
8. 絵表示について: the 警告/注意 box is HB-TABLE-SYMBOL-SIGNAL and the six-symbol grid HB-TABLE-SYMBOL-ICON (two panels: left column, right column) with the shared 表示/意味 and 記号/意味 headers that the components require (JE-1000D JP V2 chrome).
9. Each icon-led item under the grey 警告 / 注意 bands is a shared warning / caution callout labelled with the band word; the per-item pictograms are not repeated (the meaning is in the symbol grid and the callout variant). The 注意 CPAP item keeps its printed leading 「・」.
10. 使用上のご注意 and 免責事項 「・」 items are shared lists; the 「・」 marker is drawn by `geometry.css`. Sub-paragraphs under 入出力の電力(W), 低/高温警報 and 容量表示 stay inside their list item.
11. Figure captions and leader labels printed inside panels stay in the panel art and are carried as alt text and IR metadata, not repeated as visible text.
12. On phones the product appearance and LCD map pan sideways inside the figure; LCD and recycle tables scroll inside the shared component.
