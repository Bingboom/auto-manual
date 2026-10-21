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
- **Reuse half a sentence** when only part of a US sentence has corpus
  Japanese: split the unit into a green new-translation span (its English
  only in `data-previous-english`) and a black corpus span with its source.
  Example (JHP-3600C v0.64, UPS): 「UPSモードでは、…によって変わり、」(new) +
  「停電時には定格出力に戻ります。」(06_ups_mode.rst, JE-3600A/JE-5000A/JE-1000F).
  Do not take a corpus clause that contradicts this model (the template's
  「最大出力電流は…に制限」 did not fit a 200V-input unit).
- **New translation (green)** when the Japanese would need added or dropped
  meaning (e.g. US also requires "disconnected from power sources"). Since
  JHP-3600C v0.51 every green unit holds a first-pass Japanese draft for the
  native reviewer, with the US English in `data-previous-english`; put the
  nearest corpus Japanese into `data-reference-jp` for the translator.
- **Terms:** check `data/terminology_rules.csv` first — its `deprecated_regex`
  rows are retired wording the docs terminology gate reports (e.g. JA-BYPASS:
  「バイパス」 → 「パススルー」, even though older JP manuals still contain
  「バイパス時の最大出力」). A term with no corpus at all (并机口, 并机通讯口)
  started as the US English label; once the operator accepts a Japanese term
  it is new translation like any other unit, and the review note lists it for
  native review.
- Corpus English that the JP manuals keep in English is black (e.g.
  「※USB Type-C® and USB-C® are registered trademarks of USB Implementers Forum.」).
- Callout labels: CAUTION → 注意, NOTE → 説明 (TM); WARNING → 警告.

## Operator wording decisions (JHP-3600C, apply to new copy)

| Topic | Rule | Version |
| --- | --- | --- |
| product name | full name once, in the opening sentence of 「使用上のご注意」: 「<名称>（以下、「本製品」）は、定格出力…」 (JE-1000F opens that sentence with the full name); title and preface keep the full name without the reference; elsewhere 「本製品」 in `.jp-name-ref`; the spec table 「製品の名称」 keeps the full name | v0.24, v0.69 |
| 別売り vs 市販の | 「別売り」 only for Jackery-sold accessories; third-party equipment Jackery does not sell (MTS) is 「市販の…」 and the heading drops 「（別売り）」 even when the US says SOLD SEPARATELY | v0.65 |
| equipment full names | headings spell the Japanese name with the abbreviation: 「手動切替スイッチ（MTS）に接続する」 | v0.64 |
| JP-only legal notes | add what Japanese law requires even if the US has nothing (MTS: 「MTSの設置と分電盤への配線工事は、必ず電気工事士に依頼してください。」); green `jp-draft-insert`, not counted, flagged for native review | v0.66 |
| LCD states | 点灯時／点滅時／消灯時, not オン／オフ (JPD-01) | v0.37, v0.54 |
| katakana | full-width (シガーソケット); half-width ｼｶﾞｰｿｹｯﾄ in a JP PDF is a print-layout squeeze, not the wording | v0.68 |
| restored JP sections | sibling JP sections the US lacks (50Hz/60Hz switching, 省エネモード panel) are restored from JE-1000F with its components when the operator asks; their figures are placeholders until redrawn | v0.56, v0.57 |

## Spec-sheet fill

- Group rows like JE-1000F/JE-5000A: 基本情報 / 入力ポート / 出力ポート / 温度範囲,
  labels from the live JP spec rows or the sibling manual (製品の名称, 型番,
  定格容量, バッテリータイプ, サイズ＆重量, サイクル寿命, UPS, AC入力,
  AC出力(パススルー), 2×DC8020ポート, AC 出力(NEMA …), AC Total 出力, 認証：).
- Row wording follows the sibling JP table, not the US label words: the AC
  input row is 「100V-120V ~ 50/60Hz, 最大15A，最大1500W」 + 「パススルー①：…」
  (no 「充電モード」/「パススルーモード」); the DC8020 row carries
  「シガーソケット: 」 and 「PV: 」. Port counts and footnote marks follow the US table.
- The spec table is the single-unit specification (e.g. UPS 10ms); parallel
  or system figures (parallel 20ms, cascade total 6000W) belong in the body
  section that describes that setup.
- Values only from the JP spec sheet or R&D answers, purple with source and
  date; derived values (e.g. 21.5kWh ÷ 3584Wh → 5 packs) only when the
  arithmetic is exact and noted. Never derive panel counts from wattage alone
  (voltage window decides), and never fill a value R&D did not state
  (JHP-3600C v0.62 removed an inferred "MTS 最大4000W").
- US values (Ah/V, surge, per-voltage DC input, temperatures, altitude) stay in
  the orange note as "美规值：…，未代入".

## Markup contract

| Purpose | Markup |
| --- | --- |
| reused Japanese | `class="jp-original" data-jp-original-source="<file/row/manual>" lang="ja"` |
| new translation | `class="en-new" data-needs-translation="heading|term|name|sentence" data-previous-english="<US English>" data-translated="v0.NN" lang="ja"` (+ `data-reference-jp`, `data-unmatched-reason`) |
| small new insert / JP-only addition | `class="en-new jp-draft-insert" lang="ja" title="vX.YY 新加…"` (not counted) |
| spec / R&D value | `class="jp-spec-updated" data-previous-value="…" data-spec-ref="…" data-spec-source="<A0 规格书 / 研发答复 date>"` or `jp-spec-filled` + `data-jp-spec-source`; both render purple |
| product-name reference | `<span class="jp-name-ref" lang="ja">本製品</span>` (amber) |
| Chinese gloss | `<span class="zh-translation" lang="zh-CN">` inside the unit |
| placeholder | `<span class="us-difference jp-parameter">【…：未入力】</span>` (magenta) |
| review note | `<div class="jp-review" data-vNNN="true" lang="zh-CN"><strong>审阅：</strong>…<small class="jp-review-source">…</small></div>` |
| US figure | `<figure class="us-review-figure" data-us-image-source="…">` + orange figcaption |
