# Deliberate Web layout differences from the printed JE-76A JP manual

Wording is never changed. These are layout decisions only.

1. The cover (p1) with its support address, greeting and QR code is not on the Web page; printed page numbers are dropped.
2. Chapter titles are shared h2 strips; the print letter-spaces some of them (「2.同 梱 品」, 「9. 使 用 上 の ご 注 意」) and the Web keeps the characters without the spacing.
3. 1.主な仕様 is HB-TABLE-SPEC; the printed chapter title is the shared spec section heading. The 出力 and 同時出力(最大) group rows keep an empty value cell; label colons are kept as printed. The 認証 row continues on printed page 2 (physical p3) as the 認証： label and one complete mark-cluster figure after the table.
4. 同梱品 cards are HB-SPECIAL-INBOX (four cards); the shared cards draw the ①–④ ordinals.
5. The 充電式電池のリサイクルについて box, both LCD on/off tables and the エラーコード table are declared plain tables on the shared manual-table classes (`shared_component_exceptions`); printed row spans are kept as row spans.
6. The 3.使用製品 drawing is one complete panel with its A–G leader letters; the A–G legend stays as paragraphs. 【Jackery Power Bank】 and the ● sub-headings are shared h3 headings; the shared heading style displays their Latin letters in capitals (「POWER BANK」), the characters are unchanged.
7. The % and charging-lamp blocks are one HB-TABLE-LCD-ICON (unnumbered); the one-line 充電表示ランプ（…） block is split at its bracket into the row name and description.
8. Each banded 警告/注意 item becomes one HB-CALLOUT-STRIP with the band label; the item pictograms are not repeated (no symbol table is printed; the bold titles carry the meaning). The warning triangle beside the FF notice is likewise not repeated.
9. 「・」/「●」 bullets are the shared list; geometry.css draws 「・」 markers as in the print.
10. On phones the 使用製品 drawing pans sideways inside the figure; tables scroll inside the shared table wrapper.
