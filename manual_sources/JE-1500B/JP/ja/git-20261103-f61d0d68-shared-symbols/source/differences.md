# Deliberate Web layout differences from the printed JE-1500B JP manual

Wording is never changed. These are layout decisions only.

1. The cover (p1) is not on the Web page (brand, model, Jackery-UM-002, title, 国内専用/For use only in Japan,
   support e-mail, reading notes, QR); printed page numbers are dropped. The page title
   「Jackery ポータブル電源 1500 Pro 取扱説明書」 is composed from the cover lines.
2. Chapter titles are shared h2 strips. The print letter-spaces them (「6.安 全 上 の ご 注 意」); the Web keeps the
   characters without the spacing. ● sub-titles (AC充電ケーブル, ソーラー充電, シガーソケット充電, 絵表示について) and
   電源ON/OFF, LCDディスプレイのON/OFF, LEDライトのON/OFF, 充電に関する安全上のご注意 are shared h3 headings; the
   SolarSaga 60/100/200, SolarSaga 80 and DC7909-DC8020 sub-titles are h4. The ● is the print bullet.
3. The specification table title 【Jackery ポータブル電源 1500 Pro】 is the HB-TABLE-SPEC section title (the shared
   theme shows it in capitals); the printed colon after each label is kept; two-line values keep their line break.
   The Quick Charge 3.0 mark printed after UN38.3 in the 認証 row is a complete source crop directly after the table.
4. The 充電式電池のリサイクルについて box is a declared plain two-cell table (Li-ion 20 mark beside the copy).
5. The ①–⑮ LCD legend printed in three columns is one HB-TABLE-REFERENCE/lcd-descriptions list in number order.
6. Each 「名称（LCD icon）：」 title + text block becomes a row of HB-TABLE-LCD-ICON (unnumbered): the glyph printed
   inside the brackets is the row icon and the name is the row title, so the brackets and colon around the glyph
   are not repeated. Three tables in printed order: battery icon / low battery / low power mode (p3), fault code
   (p3, after the 低電力モード table and frequency notes), high / low temperature (p5, in 5.充電方法 as printed).
7. The 低電力モード table is a declared plain table inside the shared table wrapper.
8. The p5 ご注意 framed box becomes HB-CALLOUT-STRIP/caution with label ご注意; its ・ lines are a list and the
   closing 保管時の残量… line a paragraph. The run-in 「ご注意：」 (p6) and 「注意：」 (p7) notes become
   HB-CALLOUT-STRIP/caution with the printed word as label (the shared callout shows the label without the colon).
   The plain 「ご注意：…」 paragraph on p11 stays a paragraph, as printed.
9. The 警告/注意 box prints only the two signal rows; HB-TABLE-SYMBOL-SIGNAL draws its 表示/意味 header
   (JE-1000D JP V2 component chrome, not source text).
10. The 絵表示の説明 six symbols are HB-TABLE-SYMBOL-ICON (two panels, printed column order) with the shared 記号/意味
    header; each glyph is its operator-confirmed shared group canonical, which can differ in detail from the print
    (unplug outer ring, do-not-dismantle screwdriver shape, prohibited grey disc; see `source/discovery.md`).
11. Each banded 警告/注意 item becomes one HB-CALLOUT-STRIP with the band label; the item's pictogram is not
    repeated.
12. ・ bullets of 使用上のご注意, ▼本体寿命… and 免責事項 are lists (geometry.css draws 「・」 as the marker);
    continuation lines printed under a bullet are paragraphs of the same item. The bold lead lines
    「・最大何Wまでの機器に給電できますか？」 and 「▼本体寿命を少しでも伸ばすための注意点」 stay bold paragraphs with their
    printed mark.
13. 同梱品 uses HB-SPECIAL-INBOX (responsive card grid); the printed ①–⑦ are the component's card numbers.
14. Figure captions and leader labels printed inside panels stay in the panel art and are carried as alt text and
    IR metadata, not repeated as visible text.
15. On phones, the overview and LCD map pan sideways inside the figure; the LCD icon tables and the 低電力モード
    table scroll inside their shared components.
