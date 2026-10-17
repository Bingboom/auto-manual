# Corpus search and reuse rules

## Search order (all read-only)

1. **JP RST templates** — `docs/templates/page_jp/*.rst` (safety, symbols, box,
   operations, UPS, charging, troubleshooting, warranty, App). Parameters such as
   `|UPS_BYPASS_OUTPUT_TEXT|` become magenta placeholders until a value is known.
2. **Translation_Memory** (canonical base `Ji1hb5ub1aUbewsTljGccvx5nhc`):
   terms `tblzerRpOEuDIkKA`, sentence pairs `tblqtvNbgjDwR4ya` (`en`/`jp` fields).
   Dump with `feishu_api.py bitable-dump`, then `jp_corpus.py tm-grep / tm-match`.
   The skill script `bitable-translation-memory/.../query_live_translation_memory.py`
   needs a configured lark-cli; the API dump works without it.
3. **Live spec and LCD tables** (文档构建 base `LD3lb4G1ua4GOVs1vxAc9W2enje`):
   内容源_规格参数明细 `tblPUFJqt2uGGvTT` (rows per `document_key`, e.g.
   `JE-1000F_JP`, `JE-1800B_JP`, `JBP-2000B_JP`; JP wording is in `Value_source`
   / `Row_label_source`), 内容源_LCD icons `tblW5fCuJ6YdAcND` (`icon_jp`, `icon_desc_jp`).
4. **Published JP web manuals** — every `/<MODEL>/JP/ja/` link on the RTD root
   (2026-10: JA-AD500A-SIL, JBP-1000B-WH, JBP-5000A, JE-1000E-WH, JE-1000F,
   JE-5000A; the same packages live under `manual_sources/` and
   `data/manual_sources/`). `jp_corpus.py pool` builds one sentence pool.
   Prefer a sibling with the same hardware: JE-5000A JP has 100V/200V
   L14-30R, 6-20 and 5-20 port wording, AC input 1500W, DC 拡張ポート,
   battery-pack and UPS sentences.

## Reuse decision

- **Reuse (black)** when a corpus sentence/label states the same thing and only
  a slot changes: number, model or accessory name, port name, product name
  placeholder. Examples: 「…に接続する（別売り）」 for `CONNECT TO ATS — SOLD SEPARATELY`;
  「停電時には家庭用電源からポータブル電源の切り替え時間が10ミリ秒で行われます。」;
  「使用方法の詳細については、<X>の取扱説明書を参照してください。」.
- **Keep English (green)** when the Japanese would need added or dropped
  meaning (e.g. US also requires "disconnected from power sources"). Put the
  nearest Japanese into `data-reference-jp` for the translator.
- **No invented Japanese terms.** If no corpus has the term (并机口, 并机通讯口),
  use the US English label (`AC Expansion Port`, `Parallel Communication`) in
  green; candidate Japanese may only appear in an orange note, never as text.
- Corpus English that the JP manuals keep in English is black (e.g.
  「※USB Type-C® and USB-C® are registered trademarks of USB Implementers Forum.」).
- Callout labels: CAUTION → 注意, NOTE → 説明 (TM); WARNING → 警告.

## Spec-sheet fill

- Group rows like JE-1000F/JE-5000A: 基本情報 / 入力ポート / 出力ポート / 温度範囲,
  labels from the live JP spec rows or the sibling manual (製品の名称, 型番,
  定格容量, バッテリータイプ, サイズ＆重量, サイクル寿命, UPS, AC入力,
  AC出力(パススルー), 2×DC8020ポート, AC 出力(NEMA …), AC Total 出力, 認証：).
- Values only from the JP spec sheet; derived values (e.g. 21.5kWh ÷ 3584Wh → 5
  packs) only when the arithmetic is exact and noted. Never derive panel counts
  from wattage alone (voltage window decides).
- US values (Ah/V, surge, per-voltage DC input, temperatures, altitude) stay in
  the orange note as "美规值：…，未代入".

## Markup contract

| Purpose | Markup |
| --- | --- |
| reused Japanese | `class="jp-original" data-jp-original-source="<file/row/manual>" lang="ja"` |
| new translation | `class="en-new" data-needs-translation="heading|term|name|sentence" lang="en"` (+ `data-reference-jp`, `data-unmatched-reason`) |
| Chinese gloss | `<span class="zh-translation" lang="zh-CN">` inside the unit |
| placeholder | `<span class="us-difference jp-parameter">【…：未入力】</span>` |
| spec value | plain text inside the Japanese cell (`jp-spec-filled` keeps provenance, renders black) |
| review note | `<div class="jp-review" lang="zh-CN"><strong>审阅：</strong>…<small class="jp-review-source">…</small></div>` |
| US figure | `<figure class="us-review-figure" data-us-image-source="…">` + orange figcaption |
