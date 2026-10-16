# JE-3600A / JP — Shared-component edition (ja)

Operator review, 2026-10-15, of the released [Web-layout edition](../git-20261013-fd06cd04-web-layout/README.md): 「这些样式 都没用公共的 底色都填不满」, 「框框缺了」, 「样式不要自己画 你验收校对一遍」, 「明明有共享的」. Scope chosen by the operator: 「日文+中文一起改」.

The Web-layout edition drew its symbol, LCD, button, troubleshooting and specification tables, its inbox cards and its in-figure ご注意 and energy-saving tables with source-local `ht-*` CSS. Its manifest declares `source: prepared-document`, which `tools/web/frozen_web_component_coverage.py` (native sources only) does not check, so nothing stopped it. This edition rebuilds the same content on the shared components the JE-3600A EU edition uses. The released edition, its PDF and its release evidence remain immutable.

Same PDF: `Jackery ポータブル電源 3600 Plus 取扱説明書.pdf`, SHA-256 `fd06cd04653d0c336dfa119ccfb29cbee79fecf4508feee9ccda61df5eeb8dd6`. The CN edition [`../../CN/git-20261015-caa5370a-shared`](../../CN/git-20261015-caa5370a-shared/README.md) is derived by the same script.

**Status: `git-only-source-candidate`.** Not publication-eligible until the operator accepts it on the review pages; `rebuild.py` keeps the IR `pending_source_review` until `source/approval.json` binds that acceptance.

## What changed

Every change is logged with its chapter in `source/ja/shared_components.json`.

| Print block | Web-layout edition | This edition |
| --- | --- | --- |
| 絵表示について signal table | `ht-signal-table` | HB-TABLE-SYMBOL-SIGNAL |
| 絵表示の説明, 警告 symbol pairs; 警告 / 注意 icon lists | `ht-symbol-pair`, `ht-safety-table` | HB-TABLE-SYMBOL-ICON (5 tables) |
| 同梱品 cards | one drawn panel, right frame clipped | HB-SPECIAL-INBOX; each card's art cropped from the print panel |
| 液晶画面 glossary | `ht-lcd-icons` | HB-TABLE-LCD-ICON |
| LCDスクリーン modes | `ht-lcd-pair` | HB-TABLE-LCD-MODE |
| ボタン操作 | `ht-key-combinations` | HB-TABLE-KEY-COMBINATIONS |
| トラブルシューティング | `ht-troubleshooting` | HB-TABLE-TROUBLESHOOTING |
| 主な仕様 (4 groups) | `ht-spec-grid` | HB-TABLE-SPEC |
| USB ご注意 box drawn inside the p13 figure | white label box over the art | HB-CALLOUT-STRIP after the figure |
| 省エネモード prose and table drawn in the figure | live labels on the art | paragraphs and a table in print order; the art keeps the drawing only |
| App download (p28) | labels on the art | HB-SPECIAL-APP download (store badges and QR cropped from the art) |
| App ＋ button (2.1) | inline picture | HB-SPECIAL-APP inline control |
| Labelled figures | live labels | unchanged shared reference figures; one-line print labels stay on one line |

`source/presentation.css` is generated and holds geometry only: each figure's print label size, `nowrap` for one-line labels, and text-height inline pictograms. It sets no colour, border or fill.

Additions the shared components require, all logged:

- Header rows 記号 / 意味 on the signal and symbol tables (the print has none).
- The two print table cells the LCD glossary spans over two rows (④, ⑲) repeat their number on each row.
- Where one icon spans several rows of a 警告 / 注意 list, those rows merge into one row; the list splits into the component's two panels in reading order.
- A specification label the print spans over two rows (1×AC入力ポート, 2×DC8020入力ポート) keeps one row with its values on separate lines.
- The button and clock glyphs beside the ボタン操作 words are dropped: the shared table is text-only, as in EU.
- The inline 並列 icon (p18) reuses this edition's LCD glyph `lcd-parallel.png`: the old vector extraction painted a filled box over the glyph.
- The 省エネモード threshold table (p14) has no shared component; it is a plain shared table, declared with its reason in `source_manifest.json` → `shared_component_exceptions` for the prepared-document shared-style gate.

Visible copy equals the Web-layout edition's, apart from: the added headers; the repeated LCD numbers; ⚠ in the signal badges; the ＋ of the inline control; the inbox numbers, which the shared cards draw; and "Li-ion", which is part of the shared recycling symbol. `tests/test_je3600a_cn_jp_shared.py` asserts this exactly.

## Symbol admission

`source/symbol_admission.py` binds every symbol-table row to its printed row (caption words, glyph drawings, caption pixels). It writes `symbol_asset_admission` into the manifest and runs each row through the shared gate's own checks into `audit/symbol-admission.json`. 18 of 29 rows are admitted; 11 are blocked and stay recorded, not waived:

- **5 rows, text order:** the gate compares the PDF's stream-order text. This print draws the bold row heading after its body text (and adds "•" list bullets), so a correct reading-order caption never matches.
- **6 rows, glyph variant:** the shared catalog has no print-exact variant for the outline ⊘ without a grey disc (警告, p4 right column, ×2), this print's mandatory and unplug marks, the WEEE bin, or the grounding mark (`native-grounding-p4.svg`, not in the catalog). The ⊘ rows show a real fidelity gap inherited from the released edition: print has no grey disc there.

Both are shared-side changes (gate text order, catalog variants) and need operator approval; they are not made here. JP prepared-document publication does not run this gate today (`component_admission` covers EU/UK; `seal_frozen_web_evidence` has no caller).

## Reconstruction

```sh
PKG=data/manual_sources/JE-3600A/JP/git-20261015-fd06cd04-shared
python3 "$PKG/derive_shared.py"
python3 "$PKG/source/refresh_manifest.py"
PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/rebuild.py" --language ja --output tmp/je3600a-jp-shared
python3 "$PKG/source/symbol_admission.py" tmp/je3600a-jp-shared
python3 -m sphinx -n -W --keep-going -b html tmp/je3600a-jp-shared tmp/je3600a-jp-shared-site
```

`derive_shared.py` reads the Web-layout edition's `source/ja/content.json` and writes `source/ja/content.json`, `source/ja/shared_components.json`, `source/presentation.css` and `assets/` (referenced files only; cropped art written from the source SVG with only its viewBox changed). To re-freeze: remove `web/ja`, run `derive_shared.py` and `source/refresh_manifest.py`, rebuild into a scratch directory and run `source/symbol_admission.py` on it, run `source/refresh_manifest.py`, rebuild into `web/ja`, and run `source/refresh_manifest.py` again.

Test: `python3 -m unittest tests.test_je3600a_cn_jp_shared`.

## Boundaries

Git-only: no Feishu/Base/source-table, queue, asset-registry, build/link or HTML_link writes; no phase2 or print target. Shared renderers, components, gates and the symbol catalog are unchanged.
