# JVC ポータブル電源 BN-RB15 — 日本語 Web 候補

物料 **38-0001-000027**、印刷型名 **BN-RB15**。現在の竖版说明书添付 **38-0001-000027 说明书 HTE0821500B-JP-JVC(BN-RB15-C) 说明书 RoHS REACH_竖版.pdf**（16 physical pages）を原稿とし、SHA-256 `f24215296cf4a3544d48dbbce5df3c6cf489ec829ad4b2a192926d94afaff670` で固定しています。技術的な採番はソース取り込み識別子であり、印刷版の改訂番号を推定していません。

`source/original.pdf` が原文の根拠です。PDF／Illustrator の文字はアウトライン（抽出可能文字 0、Illustrator textFrames 0）であり、`source/ocr/` は誤認識を含む下書きです（認識内容は未修正、行末空白と末尾の空行のみ除去）。実際の入力は原稿画像と照合した `source/transcription.json`。各物理ページの章・ブロック・コンポーネント対応と省略理由は `source/page_review.json`、原印の疑問は同ファイルと転記 JSON の `source_concerns` に記録しています。翻訳や別機種の仕様流用はしていません。

既存素材の棚卸しを `source/discovery.json` に記録してから、`source/asset_recipes.json` で素材の共用／新規切り出しを決定しています。日本語図記号は共有ライブラリの実バイトを共用。製品図と充電図は当該原稿から、同梱品は図だけを切り出し、番号とキャプションは共有コンポーネントが表示します。本文や意味表を画像化していません。独立回収マークは操作者の明示指示により共通 canonical を使用し、原稿の Li-ion 20 は source/page_review.json の標準化差異に残しています。切り出し範囲・由来・ハッシュは `source/asset_decisions.json` に残しています。

`render.py` は既存の SourcePage → ManualIR → 共有コンポーネント／共有テーマを使用します。パッケージ固有の本文 CSS、色、枠線、`ht-*` クラスはありません。印刷ブロックの全体対応は `source_manifest.json` の `component_map`。例外の意味表は理由と内容ハッシュを同 manifest に宣言し、共有スタイルだけで描画します。成果物は `web/ja/`、経路識別子は `BN-RB15/JP/ja/md` です。

## 再生成

リポジトリ直下から、ロック済み Python 環境で実行します。出力先は未作成のディレクトリにしてください。

```sh
PKG=manual_sources/BN-RB15/JP/ja/git-20261112-f2421529-material-web
python "$PKG/derive_assets.py"
python "$PKG/refresh_manifest.py"
python "$PKG/render.py" /tmp/bnrb15-jp-candidate
python -m sphinx -n -W --keep-going -b html /tmp/bnrb15-jp-candidate /tmp/bnrb15-jp-html
```

本文のブラウザー入口は `/tmp/bnrb15-jp-html/manual_bnrb15_jp_ja.html`。`index.html` は目次です。原稿入力の変更後は、新しい生成物で `web/ja` を置き換えてから `refresh_manifest.py` を再実行します。`source_manifest.json` は入力と共用素材を固定し、`frozen_source_manifest.json` は生成物／検証証拠まで固定します。

## 検証と状態

`evidence/validation.json` に strict Sphinx、入力照合、IR／CSS／素材だけによる冷再生、改変検知を記録します。`evidence/browser-qa.json` は本文の 1280／390 px 表示、全ページ幅、壊れた画像、コンポーネント実在確認。`full-*.png` はページ全体、個別画像は主要表／同梱品／図記号／保修です。個別コンポーネントの近景では Sphinx の固定ナビゲーションのみ非表示にして読める証拠を採っています。

`evidence/review.html` は原 PDF、候補、既存の日本語共有参照版を並べるローカル比較入口です。同モデルの既存 Web はありません。共通の参照は JS-CONNECTION-GUIDE JP 版です。

これは **原稿確認待ちの候補** です。`publication_eligible=false`。人による原稿承認、公開承認、マージ、RTD 公開は本パッケージの検証とは別です。ライブ表、ソーステーブル、ビルドキュー、公開リンクは更新していません。

印刷型名 **BN-RB15** を採用し、添付名の **BN-RB15-C** は出典情報のみに保持しています。JVC の連絡先、保証書、国内限定、JIS 表記、商標、ユーザー登録を原稿どおり残しています。

独立回收标志按用户明确指示复用公共 canonical `li-ion/recycle-li-ion`，实际文件 SHA-256 为 `317b9e9feb7747092569a1074d5e05e43bca5ddb96e9404f8e33746df9da7a8e`。四包的 `assets/recycle.svg` 与公共 SVG 字节完全一致。原稿图内“Li-ion 20”与公共图仅有“Li-ion”的差异记录在 `source/page_review.json` / `source_manifest.json`，alt 准确描述公共图，不新增20的可见正文。此前私有20 SVG及其提取/像素阈值决策已停用；当前 evidence/recycle-transparency* 展示公共图，原稿白底图片仅为 source-only 历史对照。
