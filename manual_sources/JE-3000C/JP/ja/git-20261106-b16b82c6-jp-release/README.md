# JE-3000C JP V2 — Git-only Web release

Released edition of the reviewed draft `../git-20261019-b16b82c6-jp-native` (#1577), which stays unchanged.

## Source

- Authoritative PDF: `source/original.pdf`, *Jackery ポータブル電源 3000 New 取扱説明書*, 26 physical pages, printed **V2**. SHA-256 `b16b82c6c6b2ac86bf4dd438cd597e7d0be66344a9da3e2b7ea9c2d561d61a7b`.
- Feishu record: 发布文档管理 「说明书物料编码」 `reczz28SOwwEiFsd`, 子物料编码 16-0102-000341 (HTE156). Its attachment *16-0102-000341 竖版竖版说明书 HTE1563000A-JP-JAK.pdf* (`b01379c0…`) has identical text and renders on all 26 pages. The two files differ only in non-visible bytes. The operator confirmed they are the same manual.
- The draft's README describes the page map, outlined-text recovery and asset provenance, all of which carry over.

## Changes from the draft

1. **Symbol table.** All 12 rows bind their source glyphs on physical page 3 (`source/symbol-bindings.json`).
   - Six rows keep the draft assets within the fixed 2% tolerance.
   - Six rows bind their group canonicals, per the operator decisions SCG-20261103/SCG-20261104:
     - warning
     - read manual
     - keep away from children
     - no wet hands
     - Li-ion (the print has no "32")
     - WEEE
2. **Footnote ① on the specification page** (physical page 21, printed 19). The source stops at 「…給電することができま」. With operator approval it reads 「…できます。」 on the Web. This is recorded in `source_errata` and the IR metadata; the PDF is unchanged.

No other copy, layout or artwork changes. `derive_release.py` regenerates the Web IR and Markdown from the draft, and `refresh_manifest.py` binds the manifest.

## Release authority

`source/approval.json`: the operator said 「2，上线提交发布：JE-3000C」 on 2026-11-06, after reviewing the full 1280/390 renders.

## Rebuild and verify

```sh
python3 manual_sources/JE-3000C/JP/ja/git-20261106-b16b82c6-jp-release/derive_release.py
python3 manual_sources/JE-3000C/JP/ja/git-20261106-b16b82c6-jp-release/refresh_manifest.py
python3 -m sphinx -n -W --keep-going -b html manual_sources/JE-3000C/JP/ja/git-20261106-b16b82c6-jp-release/web/ja /tmp/je3000c-jp-html
python3 -m unittest tests.test_je3000c_jp_web
```
