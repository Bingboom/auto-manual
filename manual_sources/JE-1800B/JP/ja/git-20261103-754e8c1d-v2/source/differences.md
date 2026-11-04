# Deliberate Web layout differences from the printed JE-1800B JP V2 manual

Wording is never changed. These are layout decisions only.

1. Cover (p1), paper TOC (p2) and back cover (p27) are not on the Web page; printed page numbers are dropped.
2. Chapter titles are shared h2 strips; ● sub-headings are h3, ■ bold sub-headings h4 (the ●/■ marks become heading markup). The shared theme may set Latin letters in headings in capitals (「50HZ/60HZ」, 「JACKERY」); the characters in the source are unchanged.
3. The 絵表示について legend is HB-TABLE-SYMBOL-SIGNAL (表示/意味 header) and the symbol rows HB-TABLE-SYMBOL-ICON (記号/意味 headers): JE-1500D JP V2 component chrome, not source text.
4. The three p02 recycling boxes are one two-panel HB-TABLE-SYMBOL-ICON. The bold box title 「充電式電池のリサイクルについて」 is an h4 before it, because the admitted symbol meaning is the caption text printed beside the glyph.
5. Each banded 警告/注意 item becomes one HB-CALLOUT-STRIP with the band label; the item pictogram is not repeated (the symbol meanings are in the symbol table). The first 警告 group keeps its five conditions as a list.
6. Printed •/◦ list markers are list markup; 「・」 lines in the UPS text and warranty are kept as printed characters.
7. The 液晶画面 ①–㉕ map is a complete panel; the description table is HB-TABLE-LCD-ICON in printed order. ㉒ is printed once for two rows (高温/低温インジケーター); both rows carry number 22.
8. The 88H glyph inside the 省エネモード copy is the shared energy-saving LCD icon inline in the printed gap.
9. The 省エネモード port table is a declared plain table; its default cell spans both port rows as printed.
10. ボタン操作 is HB-TABLE-KEY-COMBINATIONS with shared button art; the drawn ＋ and clock are component chrome.
11. The App 2.1 step's drawn + control is native text in HB-SPECIAL-APP/inline-control.
12. Warranty pill titles are headings before HB-WARRANTY-SECTION cards; the lead, 免責事項 and contact boxes are the shared hb-text-panel.
13. Figure captions and leader labels printed inside panels stay in the panel art and are carried as alt text and IR metadata, not repeated as visible text.
14. The two ® marks of the trademark line are separate 4 pt text lines printed in the gaps after Type-C and USB-C; the Web line places them there.
15. On phones, the overview drawings and LCD map pan sideways inside the figure; the port table scrolls inside the shared table wrapper.
