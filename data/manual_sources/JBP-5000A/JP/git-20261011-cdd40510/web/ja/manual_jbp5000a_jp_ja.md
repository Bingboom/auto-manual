<style>
/* Shared styles own components; native geometry and authored title case follow the PDF. */
#furo-main-content h2.hb-spec-group{text-transform:none;}
#furo-main-content h2.hb-spec-group::before{content:none;}
.native-figure{max-width:680px;margin:1rem auto;min-width:0;}
.native-figure .hb-reference-figure{max-width:none;margin:0;}
#furo-main-content .native-figure img{width:100%!important;height:auto!important;max-height:none;}
.native-figure .hb-reference-live-label{font-family:Arial,"Hiragino Sans","Noto Sans JP",sans-serif;line-height:1.25;align-items:flex-start;justify-content:flex-start;text-align:left;padding:0;white-space:nowrap;overflow:visible!important;}
.native-figure .hb-reference-live-label>span{width:100%;}
.native-figure .hb-reference-live-label strong{font-weight:700;}
.native-lcd-map{max-width:480px;}
/* Full native circle bounds center the live LCD numerals at every scale. */
#furo-main-content .native-lcd-map .hb-reference-live-label{align-items:center;justify-content:center;text-align:center;line-height:1;}
/* Lock/unlock step numbers use their full native circle bounds too. */
#furo-main-content .native-locking-connection :is([data-source-line="2"],[data-source-line="3"],[data-source-line="4"],[data-source-line="5"]){align-items:center;justify-content:center;text-align:center;line-height:1;}
.native-overview [data-source-line="1"]>span{text-align:right;}
.native-locking-connection [data-source-line="2"] span,.native-locking-connection [data-source-line="3"] span,.native-locking-connection [data-source-line="4"] span,.native-locking-connection [data-source-line="5"] span{color:#fff!important;}
.native-recycle{display:flex;align-items:center;gap:1rem;}
.native-recycle>img{width:65px!important;}
/* Native pages 8–9 keep their shared panels and original clause grouping. */
#furo-main-content .native-warranty-intro{margin:1rem 0 1.4rem;font-size:.9rem;line-height:1.5;}
#furo-main-content .native-warranty-terms{margin:1rem 0;padding:0;border-width:1px;font-size:.9rem;line-height:1.5;}
#furo-main-content .native-warranty-clause{padding:.55rem .75rem;}
#furo-main-content .native-warranty-clause+.native-warranty-clause{border-top:1px solid var(--hb-line-soft);}
#furo-main-content .native-warranty-clause p{margin:0;}
#furo-main-content .native-warranty-clause p+p{margin-top:.75rem;}
.native-warranty-note{background:var(--hb-fill-soft,#e7e7e8);border-radius:var(--hb-panel-radius);padding:1rem;margin:1rem 0;}
#furo-main-content .native-warranty-note{font-size:.9rem;line-height:1.5;}
#furo-main-content .native-warranty-note p{margin:0;}
#furo-main-content .native-warranty-note p+p{margin-top:.6rem;}
.native-service{max-width:180px;margin-left:auto;}
.native-service p{font-size:.75rem;line-height:1.45;margin:.25rem 0;}
.native-service .native-figure{width:100%;margin:0 0 .5rem;}
.native-app-download-row{display:flex;align-items:flex-end;justify-content:space-between;gap:1rem;max-width:680px;margin:1.5rem auto;}
.native-app-download-row>div:first-child{max-width:350px;}
.native-app-download-row p{font-size:.85rem;line-height:1.5;}
.native-app-download{max-width:300px;margin:0;}
.native-app-qr{width:86px;margin:0;flex:none;}
.hb-callout img{width:2.5em!important;height:auto;display:inline-block;vertical-align:middle;}
@media(max-width:760px){
.native-dense{overflow-x:auto;padding-bottom:.5rem;}
.native-dense>.hb-reference-figure{min-width:620px;}
.native-app-download-row>div:first-child{max-width:calc(100% - 102px);}
}
.native-overview [data-source-line="0"]{font-size:2.2152cqw!important;}
.native-overview [data-source-line="1"]{font-size:2.2152cqw!important;}
.native-overview [data-source-line="2"]{font-size:2.2152cqw!important;}
.native-overview [data-source-line="3"]{font-size:2.0570cqw!important;}
.native-overview [data-source-line="4"]{font-size:2.2152cqw!important;}
.native-overview [data-source-line="5"]{font-size:2.0570cqw!important;}
.native-overview [data-source-line="6"]{font-size:2.2152cqw!important;}
.native-lcd-map [data-source-line="0"]{font-size:3.2479cqw!important;}
.native-lcd-map [data-source-line="1"]{font-size:3.2479cqw!important;}
.native-power [data-source-line="0"]{font-size:2.5316cqw!important;}
.native-power [data-source-line="1"]{font-size:2.2152cqw!important;}
.native-power [data-source-line="2"]{font-size:2.5316cqw!important;}
.native-power [data-source-line="3"]{font-size:2.2152cqw!important;}
.native-battery-packs [data-source-line="0"]{font-size:1.9232cqw!important;}
.native-battery-packs [data-source-line="1"]{font-size:1.9232cqw!important;}
.native-locking-connection [data-source-line="0"]{font-size:2.5316cqw!important;}
.native-locking-connection [data-source-line="1"]{font-size:2.5316cqw!important;}
.native-locking-connection [data-source-line="2"]{font-size:1.5757cqw!important;}
.native-locking-connection [data-source-line="3"]{font-size:1.5757cqw!important;}
.native-locking-connection [data-source-line="4"]{font-size:1.6639cqw!important;}
.native-locking-connection [data-source-line="5"]{font-size:1.6639cqw!important;}
.native-locking-connection [data-source-line="6"]{font-size:1.8147cqw!important;}
.native-ac-charge [data-source-line="0"]{font-size:1.8204cqw!important;}
.native-ac-charge [data-source-line="1"]{font-size:1.8204cqw!important;}
.native-solar-portable [data-source-line="0"]{font-size:1.8147cqw!important;}
.native-solar-portable [data-source-line="1"]{font-size:1.8147cqw!important;}
.native-solar-house [data-source-line="0"]{font-size:1.8089cqw!important;}

/* Native Japanese font metrics: keep display label inside source right edge. */
.native-overview [data-source-line="1"]{font-size:2.10cqw!important;}

</style>

<span id="native-specifications"></span>

## 主な仕様

<h2 class="hb-spec-group">【Jackery Battery Pack 5000 Plus】</h2>

<figure aria-label="【Jackery Battery Pack 5000 Plus】" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">製品の名称</th><td class="manual-spec-value hb-spec-value">Jackery Battery Pack 5000 Plus</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">型番</th><td class="manual-spec-value hb-spec-value">JBP-5000A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">定格容量</th><td class="manual-spec-value hb-spec-value">45Ah/112Vdc (5040Wh)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">バッテリータイプ</th><td class="manual-spec-value hb-spec-value">LiFePO4（リン酸鉄リチウムイオン電池）</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">サイズ＆重量</th><td class="manual-spec-value hb-spec-value">約418 x 344 x 336 mm (約37kg）</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">DC拡張ポート（入力）</th><td class="manual-spec-value hb-spec-value">80.5V-126V⎓41A Max,電流制限41A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">DC拡張ポート（出力）</th><td class="manual-spec-value hb-spec-value">80.5V-126V⎓98A Max,電流制限98A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">充電温度</th><td class="manual-spec-value hb-spec-value">0°C~45°C (32°F~113°F)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">動作温度</th><td class="manual-spec-value hb-spec-value">-15°C~45°C (5°F~113°F)</td></tr><tr><th class="manual-spec-label hb-spec-label" rowspan="2" scope="row">保存温度</th><td class="manual-spec-value hb-spec-value">1年間 0~25℃ (32~77℉)；3ヶ月 0~45℃ (32~113℉)</td></tr><tr><td class="manual-spec-value hb-spec-value">1ヶ月 -20~45℃ (-4~113℉)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">認証</th><td class="manual-spec-value hb-spec-value">UN38.3</td></tr></tbody></table></figure>

<p>本製品はJackery ポータブル電源 5000 Plus専用となります。他の機器には接続しないでください。</p>

<p><strong>本機の仕様および外観は、改善のため予告なく変更することがあります。</strong></p>

### 充電式電池のリサイクルについて

<div class="native-recycle"><img alt="Li-ion" src="assets/symbol-li-ion.svg"/><p>本機はリサイクル可能な充電池を内蔵しています。この商品を廃棄する場合は、当社のカスタマーサポートにご連絡ください。充電池の取りはずしはお客様自身では行わないでください。</p></div>

<span id="native-inbox"></span>

## 同梱品

<figure aria-label="同梱品" class="hb-inbox-composition" data-card-count="3" data-component-id="HB-SPECIAL-INBOX" data-inbox-variant="three-card-responsive"><ol class="hb-inbox-grid"><li class="hb-inbox-card" data-item-number="1"><img alt="本体" class="hb-inbox-art" src="assets/inbox-main.svg"/><div class="hb-inbox-label"><p>本体</p></div></li><li class="hb-inbox-card" data-item-number="2"><img alt="拡張ケーブル" class="hb-inbox-art" src="assets/inbox-cable.png"/><div class="hb-inbox-label"><p>拡張ケーブル</p></div></li><li class="hb-inbox-card" data-item-number="3"><img alt="取扱説明書" class="hb-inbox-art" src="assets/inbox-manual.svg"/><div class="hb-inbox-label"><p>取扱説明書</p></div></li></ol></figure>

<p>付属品を故障、紛失等してしまった場合はカスタマーサポートまでご連絡ください。</p>

<span id="native-overview"></span>

## 各部の名称

<div class="native-figure native-overview native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview" data-source-fragment-sha256="5cdc93745a922ff0b6c0755834701a3545cc685c06a005d91395d534a619f393" data-web-base-art-ref="overview" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="overview.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/overview.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:0.3828%;--hb-y:4.2942%;--hb-width:8.9731%;--hb-height:5.0943%"><span><span style="font-size:1.000000em;color:#404041"><strong>ハンドル</strong></span></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:87.2427%;--hb-y:4.8456%;--hb-width:12.7586%;--hb-height:5.0943%"><span><span style="font-size:1.000000em;color:#404041"><strong>ディスプレイ</strong></span></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:0.4825%;--hb-y:37.7605%;--hb-width:16.7752%;--hb-height:5.0943%"><span><span style="font-size:1.000000em;color:#404041"><strong>DC 拡張ポート B</strong></span></span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:0.4481%;--hb-y:42.7749%;--hb-width:26.9234%;--hb-height:8.5384%"><span><span style="font-size:1.000000em;color:#404041">バッテリーパック接続ケーブル</span><br/><span style="font-size:1.000000em;color:#404041">のプラグBに接続</span></span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:0.3984%;--hb-y:75.5324%;--hb-width:16.6866%;--hb-height:5.0943%"><span><span style="font-size:1.000000em;color:#404041"><strong>DC 拡張ポート A</strong></span></span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:0.372%;--hb-y:80.4596%;--hb-width:26.9234%;--hb-height:8.5384%"><span><span style="font-size:1.000000em;color:#404041">バッテリーパック接続ケーブル</span><br/><span style="font-size:1.000000em;color:#404041">のプラグAに接続</span></span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:85.5524%;--hb-y:84.5548%;--hb-width:13.6006%;--hb-height:5.0943%"><span><span style="font-size:1.000000em;color:#404041"><strong>主電源ボタン</strong></span></span></span></div></div></figure></div>

<span id="native-lcd"></span>

## 液晶画面

<div class="native-figure native-lcd-map"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="lcd-map" data-source-fragment-sha256="228699c172c82197f1850966411f16b68b4fc9ff1063059df5c41fc297e3dc23" data-web-base-art-ref="lcd-map" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="lcd-map.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/lcd-map.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:2.4665%;--hb-y:67.6887%;--hb-width:4.1304%;--hb-height:14.2581%"><span><span style="font-size:1.000000em;color:#ffffff">1</span></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:93.5183%;--hb-y:69.0397%;--hb-width:4.1304%;--hb-height:14.2581%"><span><span style="font-size:1.000000em;color:#ffffff">2</span></span></span></div></div></figure></div>

<figure aria-label="液晶画面の表示" class="hb-lcd-table-composition" data-component-id="HB-TABLE-LCD-ICON" tabindex="0"><table class="hb-lcd-icon-table"><colgroup><col class="hb-lcd-col-number"/><col class="hb-lcd-col-icon"/><col class="hb-lcd-col-name"/><col class="hb-lcd-col-description"/></colgroup><tbody><tr><td class="hb-lcd-number">1</td><td class="hb-lcd-icon"><img alt="1" class="hb-lcd-icon-art" src="assets/lcd-percentage.svg"/></td><td class="hb-lcd-name">バッテリー残量(%)／エラーコード</td><td class="hb-lcd-description">バッテリー残量(%)のところに現在の電力値が表示されますが、システム障害が発生した場合、エラーコードの「F0-FF」と表示されます。しばらく本製品を放置した後、自動的に回復することができますが、回復しない場合は、カスタマーサービスにご連絡ください。他のエラーコードが表示された場合はカスタマーサービスにご連絡ください。</td></tr><tr><td class="hb-lcd-number">2</td><td class="hb-lcd-icon"><img alt="2" class="hb-lcd-icon-art" src="assets/lcd-charge.svg"/></td><td class="hb-lcd-name">充電マーク</td><td class="hb-lcd-description">充電のための接続が行われると、このマークが表示され、満充電になると消えます。</td></tr></tbody></table></figure>

<span id="native-operations"></span>

## 製品の使用方法について

### オン/オフ

<p>「主電源ボタン」を短く押し、製品の電源を入れ、LCDを点灯させます。「主電源ボタン」を3秒間長押しして電源を切ります。</p>

<div class="native-figure native-power native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="power" data-source-fragment-sha256="6b9a9b2122e3d3021cc5b3d62ea65feeb8f05bcb5f8dafcf3d9d17db2cbb7c29" data-web-base-art-ref="power" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="power.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/power.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:85.4265%;--hb-y:12.3524%;--hb-width:5.4835%;--hb-height:10.991%"><span><span style="font-size:1.000000em;color:#404041"><strong>オン</strong></span></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:85.5639%;--hb-y:22.0732%;--hb-width:8.3883%;--hb-height:9.7297%"><span><span style="font-size:1.000000em;color:#404041">1回押す</span></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:85.3329%;--hb-y:35.8984%;--hb-width:5.443%;--hb-height:10.991%"><span><span style="font-size:1.000000em;color:#404041"><strong>オフ</strong></span></span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:89.7524%;--hb-y:47.5685%;--hb-width:4.0775%;--hb-height:9.7297%"><span><span style="font-size:1.000000em;color:#404041">3秒</span></span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">注釈</td><td class="manual-callout-body"><p>Jackery ポータブル電源 5000 Plusと併用する場合、Jackery ポータブル電源 5000 Plusの「主電源ボタン」からJackery Battery Pack 5000 Plusの電源の<strong>オン</strong>/<strong>オフ</strong>を制御できます。</p><p>充電されていないか、負荷が2時間接続されていないと、製品は自動的にシャットダウンします。</p></td></tr></tbody></table>

### LCDディスプレイのオン/オフ

<p>「主電源ボタン」を押した時や充電中はLCDディスプレイが点灯し、もう一度押すとLCDディスプレイが消灯します。</p>

<span id="native-battery-packs"></span>

## ポータブル電源との併用

<p>これらの製品は、Jackery ポータブル電源 5000 Plusとともに最大5セットまで使用することができ、容量の増加に対応することができます。  </p>

<div class="native-figure native-battery-packs native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="battery-packs" data-source-fragment-sha256="a0e467e4d4f123729e0000803843e327f8f16c0d3877f3466c09cedad5d1ba51" data-web-base-art-ref="battery-packs" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="battery-packs.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/battery-packs.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:32.5986%;--hb-y:89.7545%;--hb-width:6.5468%;--hb-height:6.0951%"><span><span style="font-size:1.000000em;color:#404041">≥20cm</span></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:59.0975%;--hb-y:89.7818%;--hb-width:6.5468%;--hb-height:6.0951%"><span><span style="font-size:1.000000em;color:#404041">≥20cm</span></span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">注釈</td><td class="manual-callout-body"><p>製品が適切に動作するよう、両側の吸気口と排気口が遮られていないことを確認してください。適切な放熱を確保するため、通気口と物との間に少なくとも20cmの空間を空けてください。</p></td></tr></tbody></table>

<div class="native-figure native-locking-connection native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="locking-connection" data-source-fragment-sha256="5cd0f0d942bf6e950c59b7bfb2b9a74d6fb0a332ede3021d0df17e14c299dd7b" data-web-base-art-ref="locking-connection" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="locking-connection.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/locking-connection.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:4.3908%;--hb-y:4.4579%;--hb-width:7.7927%;--hb-height:5.3043%"><span><span style="font-size:1.000000em;color:#404041"><strong>ロック</strong></span></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:56.7275%;--hb-y:4.4579%;--hb-width:12.6661%;--hb-height:5.3043%"><span><span style="font-size:1.000000em;color:#404041"><strong>ロック解除</strong></span></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:4.6249%;--hb-y:11.96%;--hb-width:1.8282%;--hb-height:2.5122%"><span><span style="font-size:1.000000em;color:#404041">1</span></span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:26.6946%;--hb-y:11.96%;--hb-width:1.8282%;--hb-height:2.5122%"><span><span style="font-size:1.000000em;color:#404041">2</span></span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:57.3401%;--hb-y:11.964%;--hb-width:1.9304%;--hb-height:2.6522%"><span><span style="font-size:1.000000em;color:#404041">1</span></span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:78.0148%;--hb-y:11.964%;--hb-width:1.9304%;--hb-height:2.6522%"><span><span style="font-size:1.000000em;color:#404041">2</span></span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:47.4752%;--hb-y:78.6088%;--hb-width:10.9566%;--hb-height:3.9252%"><span><span style="font-size:1.000000em;color:#404041">拡張ケーブル</span></span></span></div></div></figure></div>

<div class="native-figure native-stack-limits native-dense"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="stack-limits" data-source-fragment-sha256="a8553cde7b43cdc66e2de2dbc5d7d2149572c7f857b3336020e6d750acc04aab"><div class="hb-reference-semantic" data-reference-id="stack-limits.semantic"><img alt="stack-limits" class="hb-reference-art hb-composite-art" src="assets/stack-limits.svg"/></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">使用上のご注意</td><td class="manual-callout-body"><p><strong>バッテリーパックをJackery ポータブル電源 5000 Plusに接続する前に、両方の電源</strong><br/><strong>が</strong><strong>オフ</strong><strong>になっていることを確認してください。 </strong></p><p>LCD 画面(Jackery ポータブル電源 5000 Plus)に<img alt="接続バッテリー数" src="assets/connected-batteries.svg"/>アイコンが表示されたら、バッテリーパックと Jackery ポータブル電源 5000 Plus の接続が成功したことを示します。</p><p>本製品を使用する際は、バッテリーパックが落下して怪我をするのを防ぐため、バッテリーパックを3つ以上重ねないでください。  </p><p>Jackery ポータブル電源 5000 Plusの上に本製品を積み重ねないでください。</p></td></tr></tbody></table>

<span id="native-charging"></span>

## 充電方法

### AC充電

<p>AC充電の場合、本製品はJackery ポータブル電源 5000 Plusと一緒にお使いください。</p>

<div class="native-figure native-ac-charge native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ac-charge" data-source-fragment-sha256="6c355bde99738f06744477312d027edbae6646efc33311fac1001aca8ddfe8ed" data-web-base-art-ref="ac-charge" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="ac-charge.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/ac-charge.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:61.4648%;--hb-y:33.1531%;--hb-width:9.5968%;--hb-height:6.0591%"><span><span style="font-size:1.000000em;color:#404041">ACケーブル</span></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:44.342%;--hb-y:91.0041%;--hb-width:10.9911%;--hb-height:6.0591%"><span><span style="font-size:1.000000em;color:#404041">拡張ケーブル</span></span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">警告</td><td class="manual-callout-body"><p>バッテリーパックをJackery ポータブル電源 5000 Plusに接続する前に、両方の電源がオフになっていることを確認してください。</p></td></tr></tbody></table>

### ソーラー充電

<p>下図のように、ソーラーパネルとJackery ポータブル電源 5000 Plusを使って製品を充電します。詳細については、Jackery ポータブル電源 5000 Plusの取扱説明書を参照してください。</p>

<div class="native-figure native-solar-portable native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="solar-portable" data-source-fragment-sha256="e000f0afd55444076cbf672859209b8a3b861c79c9d3cd0587f1084e15e0f103" data-web-base-art-ref="solar-portable" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="solar-portable.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/solar-portable.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:65.8531%;--hb-y:80.8532%;--hb-width:10.9567%;--hb-height:5.6425%"><span><span style="font-size:1.000000em;color:#404041">拡張ケーブル</span></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:17.8229%;--hb-y:81.8424%;--hb-width:12.6076%;--hb-height:5.6425%"><span><span style="font-size:1.000000em;color:#404041">SolarSaga 200</span></span></span></div></div></figure></div>

<div class="native-figure native-solar-house native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="solar-house" data-source-fragment-sha256="892af8b2a3239f9fd8922645e842bac9a6818cd8f6ab7b6828dd07723a3193aa" data-web-base-art-ref="solar-house" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="solar-house.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/solar-house.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:32.5063%;--hb-y:91.2441%;--hb-width:10.9221%;--hb-height:3.9424%"><span><span style="font-size:1.000000em;color:#404041">拡張ケーブル</span></span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">警告</td><td class="manual-callout-body"><p>バッテリーパックを本体に接続する前に、High-PV入力を外すか、High-PVスイッチをOFFにする必要があります。</p></td></tr></tbody></table>

<span id="native-warranty"></span>

## 保証サービス

<div class="hb-warranty-intro-panel native-warranty-intro"><p>本書は、株式会社 Jackery Japan（以下、当社）製品の交換・修理にかかる保証サービスの内容を説明するものです。</p></div>

<div class="hb-source-warranty native-warranty-terms"><div class="native-warranty-clause"><p>1. 当社は、当社が運営するJackery Japan 公式オンラインストア、当社もしくは正規販売代理店が販売元として販売した当社のポータブル電源・ソーラーパネル、その他の付属製品について保証期間中に、当社が定める条件に従って保証サービスを提供しております。</p></div><div class="native-warranty-clause"><p>2. 当社は、保証期間中に、当社が定める「保証条件」に合致した場合、Jackery 製品を交換・無償修理するものとします。</p><p>保証期間内に当社に有効な請求が行われた場合、当社は、同じJackery 製品を交換もしくは価値の等しい製品と交換いたします。無償修理については、当社ポータブル電源の新品のご購入日から30 日以上5 年間以内の製品を対象といたします。</p></div><div class="native-warranty-clause"><p>3. 取扱説明書、本体貼付ラベルなどの注意書に従った使用状態で、保証期間内に製品が故障した場合のみ無償交換· 無償修理をさせていただきます。</p></div><div class="native-warranty-clause"><p>4. 当社は、日本国内に居住または滞在中のお客様のみを対象として、日本国内においてのみ本サービスを提供いたします。</p></div><div class="native-warranty-clause"><p>5. 保証期間内でも次の場合には保証対象外となります。</p><p class="native-warranty-exclusion">(1) 保証期間中に発生した故障について、保証期間終了後に請求された場合</p><p class="native-warranty-exclusion">(2) 使用上の誤り( 取扱説明書、本体貼付ラベル等の注意書きに従った正常な使用をしなかった場合を含む) による故障· 損傷</p><p class="native-warranty-exclusion">(3) 他の機器から受けた障害または不当な修理、改造による故障· 損傷</p><p class="native-warranty-exclusion">(4) お買上げ後の移設、輸送、落下などによる故障· 損傷</p><p class="native-warranty-exclusion">(5) 火災や地震、風水害、落雷その他の天災地変、公害、塩害、異常電圧などによる故障· 損傷</p><p class="native-warranty-exclusion">(6) 業務用など一般家庭用以外での使用による故障損傷</p><p class="native-warranty-exclusion">(7) 消耗· 摩耗した部品の交換、汚損した部分の交換</p></div><div class="native-warranty-clause"><p>6. 在庫切れや販売終了など当社都合で新品製品が調達できなかった場合返金にて対応することがあります。</p></div><div class="native-warranty-clause"><p>7. 本書に基づく交換・修理製品については、最初のご購入時の保証期間、または交換日から90 日間のどちらか長い期間で保証されます。</p></div></div>

<div class="hb-source-warranty native-warranty-terms"><div class="native-warranty-clause"><p>8. お客様の修理依頼品の状態、故障部分あるいは当社の事情により、修理による対応が不可能、困難または合理的でないと判断した場合、かつ保証期間内と確認できた場合に、当社が選定する同等程度の機能・性能を有する製品（修理依頼品と類似の製品・異機種を含みます）と修理依頼品との交換をさせていただく場合がございます。</p></div><div class="native-warranty-clause"><p>9. 当社は、保証期間が過ぎた製品及び保証対象外の製品について、修理すれば使用できる場合は、ご希望により有償修理にて承ります。　</p></div><div class="native-warranty-clause"><p>10. 当社の製品または製品のご使用から起因して生じた障害・損傷により、直接または間接的に発生した製品以外への損失、その他の金銭的損害につきまして、弊社はその一切の責任は負わないものとします。</p></div><div class="native-warranty-clause"><p>11. 本書は再発行いたしませんので紛失しないよう大切に保管してください。</p></div></div>

<div class="native-warranty-note"><p>※保証期間はお買い上げ日より5 年間となります。</p><p>※本書は、本書記載内容（上記記載）で無償製品交換・無償修理を行うことをお約束するものです。故障による保証サービスを受ける際は、当社もしくは当社製品正規取扱店が運営するショップでの購入が証明できるもの（インターネットでの購入は注文番号、それ以外はレシートや領収書など）をお手元にご用意の上、JackeryJapan カスタマーサービス、もしくは販売店へお問い合わせください。</p><p>※故障による保証サービスを受ける際は、当社もしくは当社製品正規取扱店が運営するショップでの購入が証明できるもの（インターネットでの購入は注文番号、それ以外はレシートや領収書など）が必須となりますのでご注意ください。当社製品正規取扱店につきましては、当社公式HP をご確認ください。</p><p>※本書によって保証責任者、及びそれ以外の事業者に対するお客様の法律上の権利を制限するものではありません。</p><p>※保証内容は都合により予告なく変更する場合がございますのでご了承ください。</p></div>

<div class="native-service"><div class="native-figure native-service-logo"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="service-logo" data-source-fragment-sha256="65f796594cc68c86dea0fcfc0e2810ec79cf1ee2d28d94270162f6e3f315a8e8"><div class="hb-reference-semantic" data-reference-id="service-logo.semantic"><img alt="service-logo" class="hb-reference-art hb-composite-art" src="assets/service-logo.svg"/></div></figure></div><div><p>公式サイト</p><p>http://www.jackery.jp</p><p>カスタマーサービス</p><p>jackery.jp@jackery.com </p></div></div>

<span id="native-safety"></span>

## 使用上のご注意

<p><strong>本製品を使用する際、以下の注意事項を守ってください。</strong></p>

<ul><li><p>本製品を使用する前に取扱説明書をよくお読みください。</p></li><li><p>危険防止のため、お子様の近くで本製品を使用する時は、お子様から目を離さないようにしてください。</p></li><li><p>メーカーが保証していない推奨外の付属品を使用すると、感電の恐れがあります。</p></li><li><p>製品を使用しない場合は、プラグを抜いてください。</p></li><li><p>火災、爆発、感電などの予測できない危険が発生する恐れがありますので、本製品を解体しないでください。</p></li><li><p>感電の危険があるため、破損したコードやプラグ、またはケーブルを使用しないでください。</p></li><li><p>製品の充電は風通しの良い場所で行い、風通しの悪い場所での充電はおやめください。</p></li><li><p>雨に濡れないよう、風通しのよい乾燥した場所に保管してください。本製品は濡れると感電の危険があります。</p></li><li><p>火災、爆発などの事故の原因となるため、本製品を火気に近づけないでください。</p></li><li><p>高温の下（直射日光や猛暑の車内）で使用したり放置しないでください。内蔵のバッテリーが過熱して発火したり、機能しなくなったり、寿命が短くなる可能性があります。</p></li><li><p>本製品を初めてご使用になる時は、十分に充電してからご使用ください。本製品を電池が切れた状態で長期間（3ヶ月～6ヶ月）放置すると、性能が低下し、過放電により充電ができなくなる場合があります。</p></li></ul>

<div class="native-app-download-row"><div><p>本製品はJackeryアプリケーションによるスマートコントロールに対応しています。</p><p>ご利用いただくには、下記のアプリストアより「Jackery」で検索して「Jackery アプリ」をダウンロードしてください。</p><div class="native-figure native-app-download"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-download" data-source-fragment-sha256="a3179ffeb93e642d99fdb499785db82c7c7502fe8845c0d89ca551d41bfef2b7"><div class="hb-reference-semantic" data-reference-id="app-download.semantic"><img alt="app-download" class="hb-reference-art hb-composite-art" src="assets/app-download.svg"/></div></figure></div></div><div class="native-figure native-app-qr"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-qr" data-source-fragment-sha256="5eb43642300c375dc4eec76824daccd3cad4d079b319cc9ab3b03081bd37e22a"><div class="hb-reference-semantic" data-reference-id="app-qr.semantic"><img alt="app-qr" class="hb-reference-art hb-composite-art" src="assets/app-qr.svg"/></div></figure></div></div>
