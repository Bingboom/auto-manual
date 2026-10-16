# JE-3600A / CN — Shared-component edition (zh)

Operator review, 2026-10-15, of the released JE-3600A Web-layout editions: 「样式不要自己画 你验收校对一遍」, 「明明有共享的」; scope 「日文+中文一起改」. The JP edition [`../../JP/git-20261015-fd06cd04-shared`](../../JP/git-20261015-fd06cd04-shared/README.md) explains why the Web-layout editions could ship source-drawn styles. This CN edition is derived by the same `derive_shared.py` from the released [Web-layout edition](../git-20261013-caa5370a-web-layout/README.md), which stays immutable.

Same PDF: `电小二户外电源 3600 Plus.pdf`, SHA-256 `caa5370acac00f053f8a62b02ea0cd60b5efe4fd5c7e7be56c65cc97493681bb`.

**Status: `git-only-source-candidate`.** Not publication-eligible until the operator accepts it on the review pages.

## What changed

Every change is logged with its chapter in `source/zh/shared_components.json`.

| Print block | Web-layout edition | This edition |
| --- | --- | --- |
| 包装清单 cards and notes | one drawn panel; notes panel clipped | HB-SPECIAL-INBOX (card art cropped from the print panel); the two notes as paragraphs |
| 显示屏界面 glossary | `ht-lcd-icons` | HB-TABLE-LCD-ICON |
| 屏幕显示 modes | `ht-lcd-pair` | HB-TABLE-LCD-MODE |
| 组合按键 | `ht-key-combinations` | HB-TABLE-KEY-COMBINATIONS |
| 故障处理 | `ht-troubleshooting` | HB-TABLE-TROUBLESHOOTING |
| 技术参数 (4 groups) | `ht-spec-grid` | HB-TABLE-SPEC |
| APP download copy and QR | `ht-native-app-download` | HB-SPECIAL-APP QR-only download |
| APP ＋ button (2.1) | inline picture | HB-SPECIAL-APP inline control |
| 合格证 | `ht-certificate` stamp layout | heading, plain table (the QC stamp lines read as one cell), company line |

Callouts were already the shared HB-CALLOUT-STRIP; labelled figures, including the p2 registration panel, stay shared reference figures. `source/presentation.css` is generated geometry only: figure label sizes, `nowrap` for one-line labels, text-height inline pictograms and the footer QR size.

Additions and removals the shared components require, all logged:

- The LCD glossary repeats the number of the two cells the print spans over two rows (④, ⑲).
- The LCD-mode table drops its header row 分类 / 操作 / 说明: the shared table has none.
- Button and clock glyphs beside the 组合按键 words are dropped: the shared table is text-only.
- The APP download copy drops the print's line indents.
- The 合格证 table (p23) has no shared component; it is a plain shared table, declared with its reason in `source_manifest.json` → `shared_component_exceptions` for the prepared-document shared-style gate.

Visible copy otherwise equals the Web-layout edition's. The other differences are the ＋ of the inline control and the inbox numbers, which the shared cards draw. `tests/test_je3600a_cn_jp_shared.py` asserts this exactly.

CN has no symbol table, so symbol admission does not apply (`audit/symbol-admission.json` is empty).

## Reconstruction

```sh
PKG=data/manual_sources/JE-3600A/CN/git-20261015-caa5370a-shared
python3 "$PKG/derive_shared.py"
python3 "$PKG/source/refresh_manifest.py"
PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/rebuild.py" --language zh --output tmp/je3600a-cn-shared
python3 "$PKG/source/symbol_admission.py" tmp/je3600a-cn-shared
python3 -m sphinx -n -W --keep-going -b html tmp/je3600a-cn-shared tmp/je3600a-cn-shared-site
```

To re-freeze: remove `web/zh`, run `derive_shared.py` and `source/refresh_manifest.py`, rebuild into a scratch directory and run `source/symbol_admission.py` on it, run `source/refresh_manifest.py`, rebuild into `web/zh`, and run `source/refresh_manifest.py` again.

## Boundaries

Git-only: no Feishu/Base/source-table, queue, asset-registry, build/link or HTML_link writes; no phase2 or print target. Shared renderers, components, gates and the symbol catalog are unchanged.
