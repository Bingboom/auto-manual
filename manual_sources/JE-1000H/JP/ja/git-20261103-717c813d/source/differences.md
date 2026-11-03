# Deliberate Web layout differences from the printed JE-1000H JP manual

Wording is never changed. These are layout decisions only.

1. Cover (p1), paper TOC (p2) and back cover (p28) are not on the Web page; printed page numbers are dropped.
2. Chapter title bands are shared h2 strips and ● / pill sub-titles are h3 headings. The shared theme sets these headings in upper case, so Latin letters display as capitals (「50HZ/60HZ…」, 「JACKERYアプリ…」); the stored text keeps the printed case.
3. 絵表示について prints four signal rows (警告, 注意, 説明, ヒント) without a header; the shared HB-TABLE-SYMBOL-SIGNAL draws its 表示/意味 header and the triangle only for 警告/注意. HB-TABLE-SYMBOL-ICON draws 記号/意味 headers (JE-1000D JP V2 component chrome, not source text).
4. 絵表示の説明 keeps 8 of its 10 rows; 「操作の前に取扱説明書をお読みください。」 and 「製品を濡らすことを禁止する記号」 are **pending** a shared symbol variant (`source_manifest.json:pending_symbols`). The 充電式電池のリサイクルについて box is a declared plain two-cell table with the operator-chosen canonical shared Li-ion 32 icon (as JE-1000D JP V2), title first; the WEEE and battery-disposal boxes are a second HB-TABLE-SYMBOL-ICON.
5. Each 警告/注意 item becomes one HB-CALLOUT-STRIP with the band label; its pictogram is not repeated (the meanings are in the symbol table). The second 警告 band (p03) is the label of its items.
6. Grey prose boxes (使用上のご注意 lead, 50Hz/60Hz notes, 必要なアクセサリー, UPS text, warranty lead/免責事項/contact) are the shared hb-text-panel; framed ご注意 / 説明 / 備考 boxes are HB-CALLOUT-STRIP caution / note.
7. Operation panels (主電源, AC, DC/USB, frequency, 省エネ, LED) are complete source panels with their button labels and steps in the art, alt text and IR; the grey note under each panel and the 前提： pill are paragraphs.
8. The LCD icon table is HB-TABLE-LCD-ICON (numbered). The merged number 23 cell (high/low temperature) is shown on both rows.
9. The 88H mark printed inline in the 省エネモード sentences is the reused LCD icon inline; the mark after the 省エネモード sub-title is not repeated.
10. LCDスクリーン modes are HB-TABLE-LCD-MODE with the product/button part of the panel as its art; ボタン操作 is HB-TABLE-KEY-COMBINATIONS (the ＋ sign is component chrome; the clock icon is the shared duration mark, followed by the printed 3s/1s). The shared table keeps a 44rem minimum and scrolls inside its frame.
11. ACおよびDC出力の復帰機能 is HB-TABLE-AUTO-RESUME; the troubleshooting table is HB-TABLE-TROUBLESHOOTING (F0 / F1 and F2 / F3 printed in one cell stay in one cell).
12. The four specification groups are HB-TABLE-SPEC tables titled by the printed group name; a second value line continues its label.
13. Warranty titled cards are a heading (the printed pill) plus HB-WARRANTY-SECTION; bold run-in titles (1. 初期不良による交換 …) stay bold.
14. The 2.1 「+」 add-device glyph is native text in HB-SPECIAL-APP/inline-control; the App download columns are HB-SPECIAL-APP/download.
15. Figure captions and leader labels printed inside panels stay in the panel art and are carried as alt text and IR metadata, not repeated as visible text.
16. On phones, the front/right overview and LCD map pan sideways inside the figure; tables scroll inside their shared components.
