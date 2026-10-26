<style>
/* JS-100I (SolarSaga 100 Air) JP manual: page-local geometry and typography only.
   Colours, borders and panels come from the shared Web theme (prepared-document shared-style gate). */

/* Print bullets are "・" lines, as in the PDF. */
#furo-main-content ul > li { list-style-type: "・"; }
#furo-main-content ul { padding-left: 1.2rem; }
#furo-main-content li > p { margin: .15rem 0; }

/* Grey note panels keep their print lines. */
#furo-main-content div.hb-text-panel { margin: .4rem 0 1.2rem; }
#furo-main-content div.hb-text-panel > p { margin: 0; }

/* Step and connection figures keep the print width of their frames. */
#furo-main-content img[alt^="手順"], #furo-main-content img[alt^="収納手順"], #furo-main-content img[alt="ゴムプラグの図"] {
  display: block; width: min(100%, 40rem) !important; margin: .4rem auto 1.2rem;
}
#furo-main-content .hb-reference-figure { width: min(100%, 40rem); margin-inline: auto; }

/* 同梱品 and indicator close-ups keep their print size. */
#furo-main-content img[alt^="正しい"], #furo-main-content img[alt^="正しくない"] { width: 10rem !important; height: auto; margin: .6rem 0 .2rem; }

/* Headings keep the printed letter case (Jackery, SolarSaga, Pro/Plus/New). */
#furo-main-content h2:not(.hb-spec-section) { text-transform: none; }

/* "1630 x 423 x 17mm" keeps the printed letter x (no contextual × substitution). */
#furo-main-content :is(.hb-spec-value, table.manual-spec-table td) { font-variant-ligatures: no-contextual; font-feature-settings: "calt" 0; }

/* The three-column 電気データ table scrolls inside its own wrapper on narrow screens. */
#furo-main-content div.table-wrapper { overflow-x: auto; }

/* Figure labels keep their printed lines on the art; two print-wrapped labels wrap. */
@media (min-width: 761px) {
  #furo-main-content .hb-reference-live-label { white-space: nowrap; }
  #furo-main-content [data-reference-id="rear-view"] .hb-reference-live-label[data-source-line="0"],
  #furo-main-content [data-reference-id="device"] .hb-reference-live-label[data-source-line="5"] { white-space: normal; }
}

/* Back-cover QR code keeps its print size. */
#furo-main-content img[alt="原稿裏表紙のQRコード"] { width: 96px !important; height: auto; margin: 1rem 0; }

</style>

<p><strong>お買い上げありがとうございます。</strong></p>




<ul class="simple">
<li><p>ご使用の前にこの「取扱説明書」をよくお読みのうえ、正しくお使いください。</p></li>
<li><p>特に「安全上のご注意」は、必ずお読みいただき、安全にお使いください。</p></li>
<li><p>お読みになったあとは、すぐに取り出せる場所に大切に保管してください。</p></li>
<li><p>本製品の取扱説明書は随時更新されますので、最新の取扱説明書は公式サイトでご確認ください。</p></li>
</ul>

# 使用ガイド（ご使用前の注意事項）

<table class="manual-callout-table" style="width:100%; border-collapse:collapse; margin:0 0 16px 0;"><tbody><tr><td class="manual-callout-label" style="width:16%; border:1px solid #000; padding:6px 8px; vertical-align:top;"><p><strong>警告</strong></p></td><td class="manual-callout-body" style="border:1px solid #000; padding:6px 8px; vertical-align:top;"><div class="line-block">
<div class="line">本製品をご使用になる前に、必ず『当該取扱説明書』をお読みください。</div>
<div class="line">以下の注意事項を守り、安全かつ正しくお使いください。</div>
</div>
</td></tr></tbody></table>

<p><strong>■ ソーラーパネルの取り扱いについて</strong></p>




<ul class="simple">
<li><p>折りたたみ時に、鋭利な物で傷をつけないようご注意ください。</p></li>
<li><p>ソーラーパネルを分解・取り外ししないでください。</p></li>
<li><p>腐食性物質はパネル上に置かないでください。</p></li>
<li><p>製品の品質保持のため、落下・曲げ・踏みつけ・加重はお控えください。</p></li>
</ul>




<p>※内部損傷により、使用不能となるおそれがあります。</p>




<p><strong>■ 使用環境に関する注意</strong></p>




<ul class="simple">
<li><p>ソーラーパネルは木・建物・その他の影になる場所で使用しないでください。</p></li>
<li><p>発電効率が大きく低下するため、パネルはガラス越しの場所では使用しないでください。</p></li>
<li><p>曇り、雨の日や夕方など、日差しが弱いときは充電ケーブルを外してください。接続したままにすると、本体の電力が減る場合があります。</p></li>
<li><p>水や液体に浸さないでください。</p></li>
</ul>




<p>※清掃の際は、湿らせた布で優しく拭いてください。</p>




<ul>
<li><p>明火や可燃物の近くでの使用・保管は禁止です。</p></li>
<li><p>折りたたみ式ソーラーパネルは取り付け用に固定できません。</p></li>
<li><p>製品の損傷やその他の危険を避けるため、強風・雹悪天候時には必ず収納してください。</p></li>
<li><p>ソーラーパネル本体（パネル面）は防塵・防水仕様となっておりますが、出力端子および充電ケーブルの端子部分には防水機能がございません。</p>
<p>そのため、雨天時のご使用は故障の原因となる可能性がございます。</p>
<p>誤作動や製品破損を防ぐためにも、雨の日の使用はお控えくださいますようお願い申し上げます。</p>
</li>
</ul>




<p><strong>■ 接続・安全性について</strong></p>




<ul class="simple">
<li><p>感電防止のため、濡れた手でソーラーパネルや接続機器に触れないでください。</p></li>
<li><p>パネルとポータブル電源のモデルにより接続方法が異なるため、「使用方法」をご確認のうえ接続してください。</p></li>
<li><p>破損がある場合は使用しないでください。感電や火災の原因となるおそれがあります。</p></li>
<li><p>人工的なスポットライトをパネルに当てて使用しないでください。</p></li>
<li><p>モジュールが破損すると、感電や火災の原因となる可能性があります。</p></li>
</ul>




<p><strong>■ 電気的仕様に関する注意</strong></p>




<ul class="simple">
<li><p>通常の状況下では、PVモジュールは標準的な試験条件よりも高い電流または電圧にさらされることがありますそのため、コンポーネントの定格電圧、導体の定格電流、PV出力に接続された制御デバイスの大きさを計算する際には、コンポーネントにマークされた短絡電流（I<sub>sc</sub>）と開放電圧（V<sub>oc</sub>）の値を1.25倍する必要があります。</p></li>
</ul>




<p>■ 逆電流および過電圧からの保護が備わっていない限り、本製品を他のPVモジュールや電源に接続しないでください。</p>

# 同梱品

<figure aria-label="同梱品" class="hb-inbox-composition" data-card-count="4" data-component-id="HB-SPECIAL-INBOX" data-inbox-variant="responsive-card-grid"><ol class="hb-inbox-grid"><li class="hb-inbox-card" data-item-number="1"><img alt="Jackery SolarSaga 100 Air" class="hb-inbox-art" src="assets/ir/bfe453b396d7c30b52136317f6e3ca084f4ad6e9e59abe908772de525244f58a/inbox_panel.png"/><div class="hb-inbox-label">
<p>Jackery SolarSaga 100 Air</p>
</div></li><li class="hb-inbox-card" data-item-number="2"><img alt="収納バッグ" class="hb-inbox-art" src="assets/ir/7995365a1852cadaa0a34a5d758a299a6e0415179c657fe6a57166b515f3c515/inbox_bag.png"/><div class="hb-inbox-label">
<p>収納バッグ</p>
</div></li><li class="hb-inbox-card" data-item-number="3"><img alt="多機能充電ケーブル(3m)" class="hb-inbox-art" src="assets/ir/0d1e2c82ce86e51eeb4a1001096fb5073c867927d8f4c86ec29cff2a86f8014f/inbox_cable.png"/><div class="hb-inbox-label">
<p>多機能充電ケーブル(3m)</p>
</div></li><li class="hb-inbox-card" data-item-number="4"><img alt="取扱説明書" class="hb-inbox-art" src="assets/ir/ec88b051c036047e604555e86872e96b4cabdfe37d37f590c61fac7cf1c5806c/inbox_manual.png"/><div class="hb-inbox-label">
<p>取扱説明書</p>
</div></li></ol></figure>




<p>※付属品を故障、紛失等してしまった場合はカスタマーサポートまでご連絡ください。</p>

# 使い方

<section id="jackery">
<h2>Jackeryポータブル電源を充電します</h2>
<p>ソーラーパネルをマルチ充電ケーブルでポータブル電源のDC入力ポートに接続します。</p>
<table class="manual-callout-table" style="width:100%; border-collapse:collapse; margin:0 0 16px 0;"><tbody><tr><td class="manual-callout-label" style="width:16%; border:1px solid #000; padding:6px 8px; vertical-align:top;"><p><strong>ヒント</strong></p></td><td class="manual-callout-body" style="border:1px solid #000; padding:6px 8px; vertical-align:top;"><div class="line-block">
<div class="line">1. ソーラーパネルの充電ケーブル端子は DC8020 です。</div>
<div class="line">2. ご使用のポータブル電源の入力端子の種類により、変換アダプターの必要有無が異なります。</div>
</div>
</td></tr></tbody></table><p><strong>本体前面</strong></p>
<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="front-view" data-source-fragment-sha256="c5c459cc452e8c5beb186ec9eb627c6b835cf891ad1e701aec941346bfbcbf89" data-web-base-art-ref="../../assets/front_view.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.front-view"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="front-view.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "front-view", "web_replace_key": "reference.front-view", "capture_following_lines": 1, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "a57148194fe8782e278bed01fb1c34ad953ffff63293629782176036fbf23e72", "panel_top": 0, "panel_fill": "#ffffff", "preserve_frame": true, "labels": [{"line": 0, "rect": [74.0, 23.8, 26.0, 12.1]}]}}' src="assets/ir/a57148194fe8782e278bed01fb1c34ad953ffff63293629782176036fbf23e72/front_view.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:74%;--hb-y:23.8%;--hb-width:26%;--hb-height:12.1%">太陽角度インジケーター</span></div></div></figure><p><strong>本体背面</strong></p>
<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="rear-view" data-source-fragment-sha256="fb1f218dba83087bfcc2e7ce09c56f71578596d1416790ebc3c36055d26762b0" data-web-base-art-ref="../../assets/rear_view.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.rear-view"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="rear-view.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "rear-view", "web_replace_key": "reference.rear-view", "capture_following_lines": 4, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "a103f77845247623218dd4912bb12ed9b479db370891b3dd1a557871dd307e62", "panel_top": 0, "panel_fill": "#ffffff", "preserve_frame": true, "labels": [{"line": 0, "rect": [76.9, 12.3, 23.1, 15.3]}, {"line": 1, "rect": [0.8, 28.6, 22.6, 6.2]}, {"line": 2, "rect": [29.8, 65.8, 10.9, 5.8]}, {"line": 3, "rect": [84.5, 92.1, 15.5, 6.1]}]}}' src="assets/ir/a103f77845247623218dd4912bb12ed9b479db370891b3dd1a557871dd307e62/rear_view.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:76.9%;--hb-y:12.3%;--hb-width:23.1%;--hb-height:15.3%">ペグで固定するためのあらかじめ開けられた穴</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:0.8%;--hb-y:28.6%;--hb-width:22.6%;--hb-height:6.2%">アダプターボックス</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:29.8%;--hb-y:65.8%;--hb-width:10.9%;--hb-height:5.8%">スタンド</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:84.5%;--hb-y:92.1%;--hb-width:15.5%;--hb-height:6.1%">穴の直径：10mm</span></div></div></figure></section>




<section id="section-2">
<h2>ソーラーパネルの展開方法</h2>
<p>1. 収納バッグからソーラーパネルを取り出します。</p>
<img alt="手順1の図" src="assets/ir/401a4aed8b6e8e2a9b4fa0270f3694c9db7cee1ed78f0cd3834a67a45d642460/unfold_1.png"/>
<p>2. 図のように、折り目に沿って順番に展開します。</p>
<img alt="手順2の図" src="assets/ir/95df14639a15683e1f5c090cce932974689c2ab8c68db78a6a39167bd5b061b2/unfold_2.png"/>
<p>3. 背面のスタンドを2本とも立てます。</p>
<img alt="手順3の図" src="assets/ir/a697833ed68f7079e7a170d7b3c0b283ea70ffd4d52b307ec0dc85d87232cbc8/unfold_3.png"/>
<p>4. ソーラーパネルを太陽の方向に向け、ポータブル電源に接続します。</p>
<img alt="手順4の図" src="assets/ir/aec21f12ad61e0f316a477735a31ea4092c16e2525a0a700e3b4db6b8fef33e7/unfold_4.png"/>
</section>




<section id="section-3">
<h2>ソーラーパネルの収納方法</h2>
<p>1.多機能充電ケーブルを取り外し、スタンドをたたみます。</p>
<img alt="収納手順1の図" src="assets/ir/a8d513b1f34f4da33e8e69cf448de72e858ca6fa1b82f72f1d4b10379810ae4b/fold_1.png"/>
<p>2. 図のように、折り目に沿ってソーラーパネルを順番に折りたたみます。</p>
<img alt="収納手順2の図" src="assets/ir/816b24b43a0d59ca1dad4ea8aaa21e6f322ee6ed42e9ec66e33666a1c9f48d03/fold_2.png"/>
<p>3. ソーラーパネルを収納バッグに戻します。</p>
<img alt="収納手順3の図" src="assets/ir/fc656fd4c6dc8256b9e2de7fde93b775993f23f73e310bc71d3b5d3e1d8d1bdb/fold_3.png"/>
</section>




<section id="section-4">
<h2>ポータブル電源の入力端子が8020の場合</h2>
<p>アダプターDC8020 - DC7909は不要です。ケーブルをそのまま接続してください。</p>
<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="dc8020" data-source-fragment-sha256="16f1ab2e14b49eabb5ebc7c22f82681cfbdb72f4875920fe301e758e02ad65cb" data-web-base-art-ref="../../assets/dc8020.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.dc8020"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="dc8020.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "dc8020", "web_replace_key": "reference.dc8020", "capture_following_lines": 2, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "424b6844a1e03880f1e1bb37fd2df7dcee5610725d1a60379e6009cc3e18981d", "panel_top": 0, "panel_fill": "#ffffff", "preserve_frame": true, "labels": [{"line": 0, "rect": [60.0, 4.1, 9.8, 4.6]}, {"line": 1, "rect": [43.9, 72.0, 56.1, 18.3]}]}}' src="assets/ir/424b6844a1e03880f1e1bb37fd2df7dcee5610725d1a60379e6009cc3e18981d/dc8020.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:60%;--hb-y:4.1%;--hb-width:9.8%;--hb-height:4.6%">DC8020</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:43.9%;--hb-y:72%;--hb-width:56.1%;--hb-height:18.3%">※一般的に、以下のモデルが該当します：<br/>1500PTB / Proシリーズ / NEWシリーズ(240NEWを除く） /<br/>Plusシリーズ(300Plus/100Plusを除く)</span></div></div></figure></section>




<section id="section-5">
<h2>ポータブル電源の入力端子が7909の場合</h2>
<p>別売りの「アダプターDC8020 - DC7909」を使用し、アダプターを接続したうえでポータブル電源に差し込んでください。</p>
<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="dc7909" data-source-fragment-sha256="b8d61875a8adb6b8b9062484dbefe57611554996fb76d767f4d8679f097dc99e" data-web-base-art-ref="../../assets/dc7909.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.dc7909"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="dc7909.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "dc7909", "web_replace_key": "reference.dc7909", "capture_following_lines": 2, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "10dc4ceb4e1dfa1c9b39b3ac3043fbed7ce47a43d9f99c3cbe1f654fda93e2bd", "panel_top": 0, "panel_fill": "#ffffff", "preserve_frame": true, "labels": [{"line": 0, "rect": [44.3, 3.9, 31.6, 4.5]}, {"line": 1, "rect": [54.6, 81.0, 44.3, 11.1]}]}}' src="assets/ir/10dc4ceb4e1dfa1c9b39b3ac3043fbed7ce47a43d9f99c3cbe1f654fda93e2bd/dc7909.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:44.3%;--hb-y:3.9%;--hb-width:31.6%;--hb-height:4.5%">アダプターDC8020 - DC7909</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:54.6%;--hb-y:81%;--hb-width:44.3%;--hb-height:11.1%">※旧モデルである以下の機種が該当します：<br/>240Wh / 400Wh / 700 / 708Wh / 1000Wh</span></div></div></figure></section>




<section id="usb-c">
<h2>ポータブル電源の入力端子はUSB-Cの場合</h2>
<div class="line-block">
<div class="line">別売りの「アダプター DC8020 - USB-C」をご使用ください。</div>
<div class="line">ケーブル8020端子 → アダプター DC8020 - USB-C → 本体USB-C (in/out)端子へ接続</div>
</div>
<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="usbc" data-source-fragment-sha256="6e0fed4e2710a93026c038a8b52fcda5b5fae7209ac5c0e40ad36d7813a4e88e" data-web-base-art-ref="../../assets/usbc.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.usbc"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="usbc.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "usbc", "web_replace_key": "reference.usbc", "capture_following_lines": 2, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "813d1260d0c1d584bcd1b46a4e696d438119afae10bde75ddba2fafa22fd4973", "panel_top": 0, "panel_fill": "#ffffff", "preserve_frame": true, "labels": [{"line": 0, "rect": [49.2, 7.2, 30.8, 3.9]}, {"line": 1, "rect": [49.3, 75.1, 48.5, 15.3]}]}}' src="assets/ir/813d1260d0c1d584bcd1b46a4e696d438119afae10bde75ddba2fafa22fd4973/usbc.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:49.2%;--hb-y:7.2%;--hb-width:30.8%;--hb-height:3.9%">アダプター DC8020 - USB-C</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:49.3%;--hb-y:75.1%;--hb-width:48.5%;--hb-height:15.3%">※ 一般的に、以下のモデルが該当します：<br/>100Plus、240New、300Plusなど、入力端子が<br/>USB-C（in/out）のモデル。</span></div></div></figure></section>




<section id="solarsaga-pro-plus-new">
<h2>SolarSaga アダプター (Pro/Plus/New専用)使用ガイド</h2>
<p>SolarSaga アダプター (Pro/Plus/New専用)を使用すると、2枚または3枚のソーラーパネルをまとめて、本体のDC入力ポートに接続できます。</p>
<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="parallel" data-source-fragment-sha256="ffa8461da2870375cf863fa9fd63c7ff9d1a6cef90ec28a4afc9ddb4ba632b19" data-web-base-art-ref="../../assets/parallel.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.parallel"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="parallel.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "parallel", "web_replace_key": "reference.parallel", "capture_following_lines": 3, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "a9d86035eae122d74fe873563b0572c52266b73ae67026712f10ae4b78888274", "panel_top": 0, "panel_fill": "#ffffff", "preserve_frame": true, "labels": [{"line": 0, "rect": [56.2, 9.4, 10.1, 4.1]}, {"line": 1, "rect": [43.1, 85.1, 41.5, 5.4]}, {"line": 2, "rect": [58.5, 92.1, 8.5, 4.7]}]}}' src="assets/ir/a9d86035eae122d74fe873563b0572c52266b73ae67026712f10ae4b78888274/parallel.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:56.2%;--hb-y:9.4%;--hb-width:10.1%;--hb-height:4.1%">DC8020</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:43.1%;--hb-y:85.1%;--hb-width:41.5%;--hb-height:5.4%">SolarSaga アダプター (Pro/Plus/New専用)</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:58.5%;--hb-y:92.1%;--hb-width:8.5%;--hb-height:4.7%">別売り</span></div></div></figure><table class="manual-callout-table" style="width:100%; border-collapse:collapse; margin:0 0 16px 0;"><tbody><tr><td class="manual-callout-label" style="width:16%; border:1px solid #000; padding:6px 8px; vertical-align:top;"><p><strong>ご注意</strong></p></td><td class="manual-callout-body" style="border:1px solid #000; padding:6px 8px; vertical-align:top;"><div class="line-block">
<div class="line">接続できるソーラーパネルの最大枚数は、ポータブル電源のモデルによって異なります。</div>
<div class="line">必ず各モデルの接続ルールをご確認のうえ、正しく接続してください。</div>
<div class="line">SolarSaga アダプター (Pro/Plus/New専用)のメス端子は8020のため、パネル充電ケーブ8020端子を接続してください。</div>
</div>
</td></tr></tbody></table></section>




<section id="section-6">
<h2>太陽角度インジケーター</h2>
<div class="line-block">
<div class="line">太陽光パネル正面には太陽角度インジケータが付いています。</div>
<div class="line">日光が表面に当たると、その下部に影が表示されます。</div>
</div>
<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="angle" data-source-fragment-sha256="03ddbef835545048027d38a3ebe2e2ac7a5fd7e156b7944941b208f9c7af55a2" data-web-base-art-ref="../../assets/angle.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.angle"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="angle.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "angle", "web_replace_key": "reference.angle", "capture_following_lines": 3, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "cc6c96c9b5ff68b0f45e79bc9194664e4191ae9884e3e34095864790511b965e", "panel_top": 0, "panel_fill": "#ffffff", "preserve_frame": true, "labels": [{"line": 0, "rect": [55.8, 35.3, 29.1, 5.1]}, {"line": 1, "rect": [72.4, 64.0, 27.6, 5.0]}, {"line": 2, "rect": [72.5, 71.6, 10.1, 4.8]}]}}' src="assets/ir/cc6c96c9b5ff68b0f45e79bc9194664e4191ae9884e3e34095864790511b965e/angle.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:55.8%;--hb-y:35.3%;--hb-width:29.1%;--hb-height:5.1%">太陽角度インジケーター</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:72.4%;--hb-y:64%;--hb-width:27.6%;--hb-height:5%">インジケーターポイント</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:72.5%;--hb-y:71.6%;--hb-width:10.1%;--hb-height:4.8%">シャドウ</span></div></div></figure><p>影が下部の白い内側の円に落ちる場合は、ソーラーパネルが太陽に直接向いていることを意味し、最適な発電を得ることができます。そうでない場合は、そうなるまで角度を調整することをお勧めします。</p>
<img alt="正しい状態の図" src="assets/ir/ea9307d45f0616cd0de6bd14243799c9675c03cc17219ced4a5d7cfd07fa9f11/angle_choice_1.png"/>
<p>影が白いインナーサークルに落ちている</p>
<img alt="正しくない状態の図" src="assets/ir/fcec905512471cea168c085300b11b806e34a19f5cc1fb4b4f2a2889dcf59bb8/angle_choice_2.png"/>
<p>影が白いインナーサークルに入ってない</p>
<table class="manual-callout-table" style="width:100%; border-collapse:collapse; margin:0 0 16px 0;"><tbody><tr><td class="manual-callout-label" style="width:16%; border:1px solid #000; padding:6px 8px; vertical-align:top;"><p><strong>ご注意</strong></p></td><td class="manual-callout-body" style="border:1px solid #000; padding:6px 8px; vertical-align:top;"><p>発電量を最大化するため、パネル表面が直射日光にしっかり当たるように設置してください。</p></td></tr></tbody></table></section>




<section id="section-7">
<h2>デバイスへの電力供給</h2>
<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="device" data-source-fragment-sha256="da4649c4099202da4c972a18c9e53cebcef653aa85b892449125a4970b218e40" data-web-base-art-ref="../../assets/device.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.device"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="device.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "device", "web_replace_key": "reference.device", "capture_following_lines": 6, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "602ae8ad9a234fcee0a41d749e0fbabc975e6c9764551c03c3ca1d85369ab883", "panel_top": 0, "panel_fill": "#ffffff", "preserve_frame": true, "labels": [{"line": 0, "rect": [53.2, 6.6, 20.0, 3.8]}, {"line": 1, "rect": [6.6, 46.5, 30.9, 4.2]}, {"line": 2, "rect": [27.4, 68.5, 11.5, 3.8]}, {"line": 3, "rect": [38.6, 68.5, 15.5, 3.8]}, {"line": 4, "rect": [53.0, 68.5, 11.8, 3.8]}, {"line": 5, "rect": [6.1, 82.2, 93.9, 8.7]}]}}' src="assets/ir/602ae8ad9a234fcee0a41d749e0fbabc975e6c9764551c03c3ca1d85369ab883/device.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:53.2%;--hb-y:6.6%;--hb-width:20%;--hb-height:3.8%">多機能アダプター</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:6.6%;--hb-y:46.5%;--hb-width:30.9%;--hb-height:4.2%">Jackery  SolarSaga 100 Air</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:27.4%;--hb-y:68.5%;--hb-width:11.5%;--hb-height:3.8%">携帯電話</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:38.6%;--hb-y:68.5%;--hb-width:15.5%;--hb-height:3.8%">電源グループ</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:53%;--hb-y:68.5%;--hb-width:11.8%;--hb-height:3.8%">タブレット</span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:6.1%;--hb-y:82.2%;--hb-width:93.9%;--hb-height:8.7%">※ この多機能充電ケーブルは本製品にのみ対応しており、他のモデルのソーラーパネルには使用しないでください。</span></div></div></figure><div class="hb-text-panel">
<p>※ USBポートを使用していないときは、ホコリを防ぐためにゴムプラグを挿入してください。</p>
</div><img alt="ゴムプラグの図" src="assets/ir/1e26a0f690a8de068b5ab04d92371332099c0241eddf9425645cc6b02dedc70b/dust.png"/>
</section>

# 主な仕様

<span id="jp-spec-panel"></span>

## Jackery SolarSaga 100 Air




## 基本情報

<figure aria-label="基本情報" class="hb-spec-table-composition"><table class="manual-spec-table manual-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody>
<tr><th class="manual-spec-label hb-spec-label" scope="row">製品名称</th><td class="manual-spec-value hb-spec-value">Jackery SolarSaga 100 Air</td></tr>
<tr><th class="manual-spec-label hb-spec-label" scope="row">型番</th><td class="manual-spec-value hb-spec-value">JS-100I</td></tr>
<tr><th class="manual-spec-label hb-spec-label" scope="row">寸法（展開）</th><td class="manual-spec-value hb-spec-value">1630 x 423 x 17mm</td></tr>
<tr><th class="manual-spec-label hb-spec-label" scope="row">寸法（折りたたみ）</th><td class="manual-spec-value hb-spec-value">423.5 x 423 x 47mm</td></tr>
<tr><th class="manual-spec-label hb-spec-label" scope="row">正味重量</th><td class="manual-spec-value hb-spec-value">3.2kg±0.2kg</td></tr>
<tr><th class="manual-spec-label hb-spec-label" scope="row">防塵防水レベル</th><td class="manual-spec-value hb-spec-value">IP68</td></tr>
<tr><th class="manual-spec-label hb-spec-label" scope="row">動作温度範囲</th><td class="manual-spec-value hb-spec-value">-20°C~65°C</td></tr>
</tbody></table></figure>




<span id="jp-spec-electrical"></span>

## 電気データ




<div class="table-wrapper"><table class="manual-spec-table"><thead>
<tr><th></th><th>STC<sup>*</sup></th><th>BNPI<sup>*</sup></th></tr>
</thead><tbody>
<tr><th>最大出力 (P<sub>max</sub>)</th><td>100W±5%</td><td>110W±5%</td></tr>
<tr><th>開放電圧 (V<sub>oc</sub>)</th><td>26.0V±5%</td><td>26.3V±5%</td></tr>
<tr><th>短絡電流 (I<sub>sc</sub>)</th><td>4.95A±5%</td><td>5.38A±5%</td></tr>
<tr><th>動作電圧 (V<sub>mp</sub>)</th><td>21.7V±5%</td><td>22.0V±5%</td></tr>
<tr><th>動作電流 (I<sub>mp</sub>)</th><td>4.67A±5%</td><td>5.08A±5%</td></tr>
<tr><th>最大システム電圧</th><td colspan="2">80V</td></tr>
<tr><th>最大逆電流</th><td colspan="2">15A</td></tr>
<tr><th>両面係数(背面/前面)</th><td colspan="2">P<sub>max</sub>: &gt;65%, V<sub>oc</sub>: &gt;97%, I<sub>sc</sub>: &gt;65%</td></tr>
<tr><th>電圧温度係数</th><td colspan="2">-0.27%/°C</td></tr>
<tr><th>出力温度係数</th><td colspan="2">-0.33%/°C</td></tr>
<tr><th>感電保護クラス</th><td colspan="2">クラスII</td></tr>
<tr><th>消費財カテゴリー</th><td colspan="2">IEC TS 63163、消費財タイプ 2</td></tr>
</tbody></table></div>

<p class="manual-spec-note">* STC-標準試験条件(1000W/m², 25°C, AM 1.5)</p>




<p class="manual-spec-note">* BNPI-両面公称照度(前面1000W/m²,背面135W/m², 25°C, AM 1.5)</p>




<p class="manual-spec-note">ブラケットを開き、平らな面に置きます。設計荷重は1600 Pa、安全率は1.5倍です。</p>




## 多機能アダプタ

<figure aria-label="多機能アダプタ" class="hb-spec-table-composition"><table class="manual-spec-table manual-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody>
<tr><th class="manual-spec-label hb-spec-label" scope="row">USB-A 出力</th><td class="manual-spec-value hb-spec-value">5V⎓2.4A</td></tr>
<tr><th class="manual-spec-label hb-spec-label" scope="row">USB-C 出力</th><td class="manual-spec-value hb-spec-value">5V⎓3A</td></tr>
</tbody></table></figure>




# 保証について

<div class="hb-text-panel">
<p>Jackery 製品をご購入いただき、誠にありがとうございます。本保証書は、Jackery のソーラーパネル製品に関する保証内容を明確にご案内するものです。以下の内容をよくお読みのうえ、大切に保管してください。</p>
</div>

<p><strong>■ 保証期間</strong></p>




<div class="line-block">
<div class="line">1. 保証期間はご購入日から 1 年間です。</div>
<div class="line">2. また、延長保証にご登録いただくと、さらに 2 年間の保証が追加されます。詳しくは Jackery 公式サイトをご確認ください。</div>
<div class="line">3. Jackery 公式オンラインストアまたは正規代理店以外での購入品は保証対象外となります。</div>
</div>




<p><strong>■ 保証対象</strong></p>




<div class="line-block">
<div class="line">1. 購入チャネル</div>
<div class="line-block">
<div class="line">本保証は、Jackery 公式オンラインストアおよび正規販売代理店で購入された製品に限り有効です。</div>
</div>
<div class="line">2. 保証の提供範囲</div>
<div class="line-block">
<div class="line">日本国内に居住されているお客様を対象とし、日本国内での使用に限り保証を提供します。</div>
</div>
<div class="line">3. 保証適用条件</div>
<div class="line-block">
<div class="line">以下すべての条件を満たす場合に限り、本保証が適用されます：</div>
<div class="line">- 取扱説明書および注意書きに従った正常な使用</div>
<div class="line">- 改造・不適切な使用・事故等によらない自然故障</div>
<div class="line">- 保証申請時に購入証明の提示があること</div>
</div>
<div class="line">4. 購入証明の提示について</div>
<div class="line-block">
<div class="line">保証対応を受ける際には、以下のいずれかの購入証明が必要です：</div>
<div class="line">- Jackery 公式オンラインストア：注文番号（注文履歴または注文確認メールなど）</div>
<div class="line">- Jackery 正規代理店：領収書、納品書など購入日・店舗名が確認できる書類</div>
<div class="line">- Jackery 公式オンラインストアおよび正規代理店以外でご購入された製品は保証対象外となりますので、らかじめご了承ください。</div>
</div>
</div>




<p><strong>■ 保証内容</strong></p>




<div class="line-block">
<div class="line">保証期間内に自然故障が確認された場合、以下のいずれかの方法で対応いたします：</div>
<div class="line">1. 同一製品または同等品への交換（中古品の可能性を顧慮）</div>
<div class="line">2. 販売終了・在庫切れ等により交換が困難な場合は、（購入年数に応じての一部）返金での対応となることがあります</div>
<div class="line-block">
<div class="line">※ソーラーパネル製品は修理サービス対象外のため、修理対応は行っておりません。</div>
</div>
</div>




<p><strong>■ 保証対象外となる場合</strong></p>




<div class="line-block">
<div class="line">以下の場合、保証期間内であっても保証の対象外となります：</div>
<div class="line">1. 保証期間中に発生した故障であっても、保証期間終了後に請求された場合</div>
<div class="line">2. 使用上の誤り（取扱説明書や本体ラベルなどの注意書きに従わなかった使用）による故障・損傷</div>
<div class="line">3. 他機器からの影響、または不当な修理・改造による故障・損傷</div>
<div class="line-block">
<div class="line">移設・輸送・落下等による物理的な故障・損傷</div>
</div>
<div class="line">4. 火災・地震・風水害・落雷等の天災地変、公害・塩害・異常電圧などによる故障・損傷</div>
<div class="line">5. 業務用等、家庭用途以外での使用による故障・損傷</div>
<div class="line">6. 消耗・摩耗部品の交換、または外観の汚損による対応要求</div>
<div class="line">7. ソーラーパネル本体は防水仕様ですが、接続端子およびケーブル部分は防水ではありません。雨水の浸入、濡れた状態での使用などにより発生した故障・腐食は保証対象外となります。</div>
<div class="line">8. 発電効率は天候状況、設置方法、温度に応じて変化するため、合理範囲内での発電が可能な場合</div>
<div class="line">9. Jackery のソーラーパネルは、Jackery 製ポータブル電源に合わせて設計されています。他社製ポータブル電源と組み合わせて使用される場合は、必ずソーラーパネルの電圧・電流が接続先機器の仕様範囲内であることをご確認ください。</div>
<div class="line-block">
<div class="line">互換性の検証は行っておらず、適合しない組み合わせによって生じた製品故障は保証対象外となります。また、それに伴う経済的損失や安全上の問題についても、当社では一切の責任を負いかねますので、あらかじめご了承ください。</div>
</div>
</div>




<p><strong>■ 保管に関する注意</strong></p>




<div class="line-block">
<div class="line">製品は直射日光・高温多湿・雨風・ホコリの多い場所を避けて保管してください。</div>
<div class="line">長期保管時には、重い物を上に置かず、変形や破損が起きないようご注意ください。</div>
<div class="line">定期的に清掃・点検を行うことで、安全に長期間ご使用いただけます。</div>
</div>




<p><strong>■ お問い合わせ</strong></p>




<div class="line-block">
<div class="line">保証に関するご不明点がございましたら、Jackery カスタマーサービスまでお問い合わせください。</div>
<div class="line">最新の保証条件は Jackery 公式サイトでもご確認いただけます。</div>
</div>




<p><strong>■ ご注意（法的および規約面）</strong></p>




<div class="line-block">
<div class="line">※ 本書によって保証責任者、及びそれ以外の事業者に対するお客様の法律上の権利を制限するものではありません。</div>
<div class="line">※ 保証内容は都合により予告なく変更する場合がございますのでご了承ください。</div>
</div>

<div class="hb-text-panel">
<p><strong>公式サイト: <a href="http://www.jackery.jp">http://www.jackery.jp</a></strong></p>
<p><strong>カスタマーサポート: <a href="mailto:jackery.jp@jackery.com">jackery.jp@jackery.com</a></strong></p>
<p><strong>お問い合わせ電話番号: <a href="tel:05031989007">050-3198-9007</a></strong></p>
</div>

<p><strong>株式会社Jackery Japan</strong></p>




<p>© 株式会社Jackery Japanは全ての権利を留保します。</p>




<img alt="原稿裏表紙のQRコード" src="assets/ir/3ef838c9c927d420ede815853601097192e85a207d7e1bc56d871e4f25702b91/contact_qr.png"/>
