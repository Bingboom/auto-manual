<style>
/* Source-derived artwork geometry only; shared theme owns headings/tables. */
.native-figure{max-width:720px;margin:1rem auto;min-width:0;}
.native-figure .hb-reference-figure{max-width:none;margin:0;}
#furo-main-content .native-figure img{width:100%!important;height:auto!important;max-height:none;}
.native-figure .hb-reference-live-label{font-family:Arial,"Hiragino Sans","Noto Sans JP",sans-serif;line-height:1.25;align-items:flex-start;justify-content:flex-start;text-align:left;padding:0;white-space:nowrap;overflow:visible!important;}
.native-figure .hb-reference-live-label>span{width:100%;}
.native-figure .hb-reference-live-label strong{font-weight:700;}
.native-lcd-map{max-width:660px;}
.native-app-add{max-width:390px;}
.native-app-results{max-width:680px;}
.native-app-control{max-width:580px;}
.native-lcd-controls{display:grid;grid-template-columns:44% 56%;align-items:stretch;gap:0;}
.native-lcd-controls .native-figure{margin:0;display:flex;align-items:center;}
.native-lcd-actions .manual-table{height:100%;margin:0;table-layout:fixed;width:100%;min-width:0!important;}
.native-lcd-actions{border:1px solid var(--hb-line-soft);border-radius:var(--hb-panel-radius);overflow:hidden;}
#furo-main-content .native-lcd-actions table.manual-table td{padding:.28rem!important;font-size:.7rem!important;line-height:1.35;}
.native-lcd-actions tr:first-child td:nth-child(2){width:20%;}
.native-lcd-actions td[rowspan]{width:26%;font-weight:700;}
.native-lcd-actions td{white-space:normal!important;}
.native-lcd-actions{min-width:0;}
.native-recycle{display:flex;align-items:center;gap:1rem;}
.native-service{max-width:180px;margin-left:auto;}
.native-service p{font-size:.75rem;line-height:1.45;margin:.25rem 0;}
.native-recycle>img{width:65px!important;}
.native-service .native-figure{width:100%;margin:0 0 .5rem;}
.native-app-download-row{display:flex;align-items:center;justify-content:space-between;max-width:580px;}
.native-app-download-row .native-app-download{max-width:140px;margin:0;}
.native-app-download-row .native-app-qr{width:100px;margin:0;}
.native-safety-columns{display:grid;grid-template-columns:1fr 1fr;gap:.5rem;}
.native-safety-columns table{height:100%;margin:0;}
.native-safety-signals img{width:35px!important;display:inline-block;vertical-align:middle;}
.native-safety-signals th{white-space:nowrap;width:7rem;}
.native-safety-signals{width:100%!important;min-width:0!important;table-layout:fixed;}
.native-safety-signals td{white-space:normal!important;overflow-wrap:anywhere;}
.native-safety-table{width:100%!important;min-width:0!important;table-layout:fixed;}
.native-safety-table td:first-child{width:45px;padding:8px;vertical-align:middle;}
.native-safety-table td:first-child img{width:26px!important;min-width:26px;height:auto;}
.native-safety-table td:last-child{white-space:normal!important;overflow-wrap:anywhere;}
.native-key-buttons{display:flex;align-items:center;justify-content:center;gap:.6rem;}
.native-key-button{width:5.5rem;flex:none;text-align:center;}
.native-key-button img{width:3.5rem!important;height:auto;}
.native-key-button p{font-size:.65rem;white-space:nowrap;}
.native-key-plus{font-weight:700;font-size:1.5rem;}
.native-key-buttons p{margin:0!important;}
.native-inline-plus{display:inline-flex;width:1em;height:1em;align-items:center;justify-content:center;background:#d0d2d4;border-radius:50%;margin:0 .2em;font-weight:700;}
.native-power [data-source-line="6"]::before{content:"";position:absolute;top:-2.4cqw;left:3cqw;width:3.6cqw;height:2.5cqw;background:#e7e7e8;clip-path:polygon(50% 0,100% 100%,0 100%);}
@media(max-width:760px){
.native-dense{overflow-x:auto;padding-bottom:.5rem;}
.native-dense>.hb-reference-figure{min-width:660px;}
.native-lcd-scroll{overflow-x:auto;padding-bottom:.5rem;}
.native-lcd-controls{min-width:660px;}
.native-safety-columns{grid-template-columns:1fr;}
}
.native-overview-front [data-source-line="0"]{font-size:2.2082cqw!important;}
.native-overview-front [data-source-line="1"]{font-size:2.2082cqw!important;}
.native-overview-front [data-source-line="2"]{font-size:2.2082cqw!important;}
.native-overview-front [data-source-line="3"]{font-size:1.5773cqw!important;}
.native-overview-front [data-source-line="4"]{font-size:2.2082cqw!important;}
.native-overview-front [data-source-line="5"]{font-size:2.2082cqw!important;}
.native-overview-front [data-source-line="6"]{font-size:1.5773cqw!important;}
.native-overview-front [data-source-line="7"]{font-size:2.2082cqw!important;}
.native-overview-front [data-source-line="8"]{font-size:1.5773cqw!important;}
.native-overview-front [data-source-line="9"]{font-size:2.2082cqw!important;}
.native-overview-front [data-source-line="10"]{font-size:2.2082cqw!important;}
.native-overview-front [data-source-line="11"]{font-size:1.8927cqw!important;}
.native-overview-front [data-source-line="12"]{font-size:1.5773cqw!important;}
.native-overview-front [data-source-line="13"]{font-size:1.5773cqw!important;}
.native-overview-front [data-source-line="14"]{font-size:1.5773cqw!important;}
.native-overview-front [data-source-line="15"]{font-size:1.5773cqw!important;}
.native-overview-front [data-source-line="16"]{font-size:2.2082cqw!important;}
.native-overview-front [data-source-line="17"]{font-size:2.2082cqw!important;}
.native-overview-front [data-source-line="18"]{font-size:2.2082cqw!important;}
.native-overview-left [data-source-line="0"]{font-size:2.2293cqw!important;}
.native-overview-left [data-source-line="1"]{font-size:2.2293cqw!important;}
.native-overview-left [data-source-line="2"]{font-size:1.9108cqw!important;}
.native-overview-left [data-source-line="3"]{font-size:1.5924cqw!important;}
.native-overview-left [data-source-line="4"]{font-size:2.2293cqw!important;}
.native-overview-left [data-source-line="5"]{font-size:1.5924cqw!important;}
.native-overview-left [data-source-line="6"]{font-size:2.2293cqw!important;}
.native-overview-left [data-source-line="7"]{font-size:2.2293cqw!important;}
.native-overview-right [data-source-line="0"]{font-size:2.2222cqw!important;}
.native-overview-right [data-source-line="1"]{font-size:2.2222cqw!important;}
.native-overview-right [data-source-line="2"]{font-size:1.5873cqw!important;}
.native-overview-right [data-source-line="3"]{font-size:2.2222cqw!important;}
.native-overview-right [data-source-line="4"]{font-size:1.5873cqw!important;}
.native-overview-right [data-source-line="5"]{font-size:2.2222cqw!important;}
.native-overview-right [data-source-line="6"]{font-size:1.5873cqw!important;}
.native-overview-right [data-source-line="7"]{font-size:2.2222cqw!important;}
.native-overview-right [data-source-line="8"]{font-size:1.5873cqw!important;}
.native-overview-right [data-source-line="9"]{font-size:2.2222cqw!important;}
.native-overview-right [data-source-line="10"]{font-size:1.5873cqw!important;}
.native-overview-right [data-source-line="11"]{font-size:2.2222cqw!important;}
.native-lcd-map [data-source-line="0"]{font-size:2.2206cqw!important;}
.native-lcd-map [data-source-line="1"]{font-size:2.2206cqw!important;}
.native-lcd-map [data-source-line="2"]{font-size:2.2206cqw!important;}
.native-lcd-map [data-source-line="3"]{font-size:2.2206cqw!important;}
.native-lcd-map [data-source-line="4"]{font-size:2.2206cqw!important;}
.native-lcd-map [data-source-line="5"]{font-size:2.2206cqw!important;}
.native-lcd-map [data-source-line="6"]{font-size:2.2206cqw!important;}
.native-lcd-map [data-source-line="7"]{font-size:2.2206cqw!important;}
.native-lcd-map [data-source-line="8"]{font-size:2.2206cqw!important;}
.native-lcd-map [data-source-line="9"]{font-size:2.2206cqw!important;}
.native-lcd-map [data-source-line="10"]{font-size:2.2206cqw!important;}
.native-lcd-map [data-source-line="11"]{font-size:2.2206cqw!important;}
.native-lcd-map [data-source-line="12"]{font-size:2.2206cqw!important;}
.native-lcd-map [data-source-line="13"]{font-size:2.2206cqw!important;}
.native-lcd-map [data-source-line="14"]{font-size:2.2206cqw!important;}
.native-lcd-map [data-source-line="15"]{font-size:2.2206cqw!important;}
.native-lcd-map [data-source-line="16"]{font-size:2.2206cqw!important;}
.native-lcd-map [data-source-line="17"]{font-size:2.2206cqw!important;}
.native-lcd-map [data-source-line="18"]{font-size:2.2206cqw!important;}
.native-lcd-map [data-source-line="19"]{font-size:2.2206cqw!important;}
.native-lcd-map [data-source-line="20"]{font-size:2.2206cqw!important;}
.native-power [data-source-line="0"]{font-size:1.9048cqw!important;}
.native-power [data-source-line="0"]{padding:0.9514cqw 1.7432cqw!important;border-radius:1.7cqw!important;}
.native-power [data-source-line="1"]{font-size:2.2222cqw!important;}
.native-power [data-source-line="2"]{font-size:1.9048cqw!important;}
.native-power [data-source-line="3"]{font-size:2.2222cqw!important;}
.native-power [data-source-line="4"]{font-size:1.9048cqw!important;}
.native-power [data-source-line="5"]{font-size:2.2222cqw!important;}
.native-power [data-source-line="6"]{font-size:1.9048cqw!important;}
.native-power [data-source-line="6"]{padding:2.3095cqw 2.7493cqw!important;border-radius:1.7cqw!important;}
.native-ac-output [data-source-line="0"]{font-size:1.9048cqw!important;}
.native-ac-output [data-source-line="0"]{padding:0.9513cqw 1.7432cqw!important;border-radius:1.7cqw!important;}
.native-ac-output [data-source-line="1"]{font-size:2.2222cqw!important;}
.native-ac-output [data-source-line="2"]{font-size:1.9048cqw!important;}
.native-ac-output [data-source-line="3"]{font-size:2.2222cqw!important;}
.native-ac-output [data-source-line="4"]{font-size:1.9048cqw!important;}
.native-usb-output [data-source-line="0"]{font-size:1.9048cqw!important;}
.native-usb-output [data-source-line="0"]{padding:0.9514cqw 1.7431cqw!important;border-radius:1.7cqw!important;}
.native-usb-output [data-source-line="1"]{font-size:2.2222cqw!important;}
.native-usb-output [data-source-line="2"]{font-size:1.9048cqw!important;}
.native-usb-output [data-source-line="3"]{font-size:2.2222cqw!important;}
.native-usb-output [data-source-line="4"]{font-size:1.9048cqw!important;}
.native-dc-output [data-source-line="0"]{font-size:1.9048cqw!important;}
.native-dc-output [data-source-line="0"]{padding:0.9514cqw 1.7431cqw!important;border-radius:1.7cqw!important;}
.native-dc-output [data-source-line="1"]{font-size:2.2222cqw!important;}
.native-dc-output [data-source-line="2"]{font-size:1.9048cqw!important;}
.native-dc-output [data-source-line="3"]{font-size:2.2222cqw!important;}
.native-dc-output [data-source-line="4"]{font-size:1.9048cqw!important;}
.native-ups [data-source-line="0"]{font-size:1.9048cqw!important;}
.native-ups [data-source-line="0"]{padding:1.1961cqw 2.7683cqw!important;border-radius:1.7cqw!important;}
.native-battery-packs [data-source-line="0"]{font-size:1.9232cqw!important;}
.native-battery-packs [data-source-line="1"]{font-size:1.9232cqw!important;}
.native-ac-charge [data-source-line="0"]{font-size:1.9048cqw!important;}
.native-low-pv [data-source-line="0"]{font-size:1.7732cqw!important;}
.native-high-pv [data-source-line="0"]{font-size:2.2222cqw!important;}
.native-high-pv-lock [data-source-line="0"]{font-size:2.0701cqw!important;}
.native-high-pv-lock [data-source-line="1"]{font-size:2.0701cqw!important;}
.native-high-pv-lock [data-source-line="2"]{font-size:2.0701cqw!important;}
.native-high-pv-lock [data-source-line="3"]{font-size:2.0701cqw!important;}
.native-high-pv-lock [data-source-line="4"]{font-size:2.0701cqw!important;}
.native-high-pv-lock [data-source-line="5"]{font-size:2.0701cqw!important;}
.native-car-charge [data-source-line="0"]{font-size:2.2222cqw!important;}
.native-car-charge [data-source-line="1"]{font-size:1.9392cqw!important;}
.native-car-charge [data-source-line="1"]{padding:0.5498cqw 1.3076cqw!important;border-radius:1.7cqw!important;}
.native-app-add [data-source-line="0"]{font-size:3.6145cqw!important;}
.native-app-add [data-source-line="1"]{font-size:3.6145cqw!important;}
.native-app-control [data-source-line="0"]{font-size:3.2864cqw!important;}
.native-app-control [data-source-line="1"]{font-size:3.2864cqw!important;}
.native-app-control [data-source-line="2"]{font-size:3.2864cqw!important;}
.native-app-control [data-source-line="3"]{font-size:3.2864cqw!important;}
.native-app-results [data-source-line="0"]{font-size:2.0408cqw!important;}
.native-app-results [data-source-line="1"]{font-size:2.0408cqw!important;}
.native-app-results [data-source-line="2"]{font-size:2.0408cqw!important;}

</style>

<span id="native-specifications"></span>

## 主な仕様

<h2 class="hb-spec-group">【Jackery ポータブル電源 5000 Plus】</h2>

<figure aria-label="【Jackery ポータブル電源 5000 Plus】" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">製品の名称</th><td class="manual-spec-value hb-spec-value">Jackery ポータブル電源 5000 Plus</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">型番</th><td class="manual-spec-value hb-spec-value">JE-5000A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">定格容量</th><td class="manual-spec-value hb-spec-value">45Ah/112Vdc (5040Wh)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">バッテリータイプ</th><td class="manual-spec-value hb-spec-value">LiFePO4（リン酸鉄リチウムイオン電池）</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">サイズ＆重量</th><td class="manual-spec-value hb-spec-value">約420×390×635 mm  (約60 kg）</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">UPS</th><td class="manual-spec-value hb-spec-value">バックアップUPS:20ms、オンラインUPS:0ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">入力ポート</th><td class="manual-spec-value hb-spec-value"></td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">AC入力</th><td class="manual-spec-value hb-spec-value">100V-120V ~ 50/60Hz, 最大15A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">パススルー充電  AC入力/出力</th><td class="manual-spec-value hb-spec-value">100V-120V ~ 50/60Hz, 最大15A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">DC 入力</th><td class="manual-spec-value hb-spec-value"></td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 x DC 拡張ポート（入力）</th><td class="manual-spec-value hb-spec-value">80.5V-126V⎓98A 最大98A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">高電圧入力</th><td class="manual-spec-value hb-spec-value">135V-450V⎓15A 最大15A， 最大4000W</td></tr><tr><th class="manual-spec-label hb-spec-label" rowspan="2" scope="row">低電圧入力</th><td class="manual-spec-value hb-spec-value">2 x DC 8mm ポート; 16V-60V⎓10.5A 最大21A/1200Wに倍増</td></tr><tr><td class="manual-spec-value hb-spec-value">11V-16V（動作電圧）⎓8A 最大8Aに倍増</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">出力ポート</th><td class="manual-spec-value hb-spec-value"></td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">AC 出力(NEMA L14-30R)</th><td class="manual-spec-value hb-spec-value">100V/200V ~ 50/60Hz, 最大30A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">AC 出力(NEMA 6-20)</th><td class="manual-spec-value hb-spec-value">200V ~ 50/60Hz, 最大20A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">パススルー充電  AC入力/出力</th><td class="manual-spec-value hb-spec-value">100V-120V ~ 50/60Hz, 最大15A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">4 × AC 出力</th><td class="manual-spec-value hb-spec-value">100V ~ 50/60Hz, 20A, 2000W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">AC Total 出力</th><td class="manual-spec-value hb-spec-value">最大6000W, 瞬間最大12000W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × USB-C 出力</th><td class="manual-spec-value hb-spec-value">5V⎓3A, 9V⎓3A, 12V⎓3A, 15V⎓3A, 20V⎓5A, 最大100W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × USB-A 出力</th><td class="manual-spec-value hb-spec-value">5-6V⎓3A, 6-9V⎓2A, 9-12V⎓1.5A, 最大18W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">シガーソケット出力</th><td class="manual-spec-value hb-spec-value">12V⎓10A 最大10A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × DC 拡張ポート(出力)</th><td class="manual-spec-value hb-spec-value">80.5V-126V⎓41A 最大41A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">充電温度</th><td class="manual-spec-value hb-spec-value">0°C~45°C (32°F~113°F)</td></tr><tr><th class="manual-spec-label hb-spec-label" rowspan="2" scope="row">動作温度</th><td class="manual-spec-value hb-spec-value">-15°C~45°C (5°F~113°F)</td></tr><tr><td class="manual-spec-value hb-spec-value">-15°C~-10°C (5°F~14°F) 出力電力：3000W</td></tr><tr><th class="manual-spec-label hb-spec-label" rowspan="2" scope="row">保存温度</th><td class="manual-spec-value hb-spec-value">1ヶ月 -20℃~45℃ (-4℉~113℉); 3ヶ月 0℃~45℃ (32℉~113℉);</td></tr><tr><td class="manual-spec-value hb-spec-value">1年 0℃~25℃ (32℉~77℉)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">認証</th><td class="manual-spec-value hb-spec-value">UN38.3</td></tr></tbody></table></figure>

<p>※USB Type-C® and USB-C® are registered trademarks of USB Implementers Forum.</p>

<p>本機の仕様および外観は、改善のため予告なく変更することがあります。</p>

### 充電式電池のリサイクルについて

<div class="native-recycle"><img alt="Li-ion" src="assets/symbol-li-ion.svg"/><p>本機はリサイクル可能な充電池を内蔵しています。この商品を廃棄する場合は、当社のカスタマーサポートにご連絡ください。充電池の取りはずしはお客様自身では行わないでください。</p></div>

<span id="native-inbox"></span>

## 同梱品

<figure aria-label="同梱品" class="hb-inbox-composition" data-card-count="4" data-component-id="HB-SPECIAL-INBOX" data-inbox-variant="responsive-card-grid"><ol class="hb-inbox-grid"><li class="hb-inbox-card" data-item-number="1"><img alt="本体" class="hb-inbox-art" src="assets/inbox-main.svg"/><div class="hb-inbox-label"><p>本体</p></div></li><li class="hb-inbox-card" data-item-number="2"><img alt="AC充電ケーブル" class="hb-inbox-art" src="assets/inbox-cable.svg"/><div class="hb-inbox-label"><p>AC充電ケーブル</p></div></li><li class="hb-inbox-card" data-item-number="3"><img alt="MC4レンチ" class="hb-inbox-art" src="assets/inbox-mc4.svg"/><div class="hb-inbox-label"><p>MC4レンチ</p></div></li><li class="hb-inbox-card" data-item-number="4"><img alt="取扱説明書" class="hb-inbox-art" src="assets/inbox-manual.svg"/><div class="hb-inbox-label"><p>取扱説明書</p></div></li></ol></figure>

<p>付属品を故障、紛失等してしまった場合はカスタマーサポートまでご連絡ください。</p>

<p>シガーソケット充電ケーブルは別売りです。Jackery公式サイトよりご購入いただけます。サポートが必要な場合は、Jackeryカスタマーサポートまでお問い合わせください。</p>

<span id="native-overview"></span>

## 各部の名称

### 前面

<div class="native-figure native-overview-front native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview-front" data-source-fragment-sha256="be610f0ae1a4207fbfab2408bc7510b59e3896009c561182e315dc66ae6e6bc5" data-web-base-art-ref="overview-front" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="overview-front.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/overview-front.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:0.4796%;--hb-y:3.2972%;--hb-width:16.8722%;--hb-height:4.6552%"><span><span style="font-size:1.000000em"><strong>LCDディスプレイ</strong></span></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:85.9967%;--hb-y:3.8192%;--hb-width:13.5577%;--hb-height:4.6552%"><span><span style="font-size:1.000000em"><strong>主電源ボタン</strong></span></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:80.9995%;--hb-y:11.7877%;--hb-width:18.5836%;--hb-height:4.6552%"><span><span style="font-size:1.000000em"><strong>USB-C 出力ポート</strong></span></span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:78.4564%;--hb-y:15.6399%;--hb-width:21.0331%;--hb-height:6.1207%"><span><span style="font-size:1.000000em">5V</span><span style="font-size:1.000000em">⎓</span><span style="font-size:1.000000em">3A, 9V</span><span style="font-size:1.000000em">⎓</span><span style="font-size:1.000000em">3A, 12V</span><span style="font-size:1.000000em">⎓</span><span style="font-size:1.000000em">3A, </span><br/><span style="font-size:1.000000em">15V</span><span style="font-size:1.000000em">⎓</span><span style="font-size:1.000000em">3A, 20V</span><span style="font-size:1.000000em">⎓</span><span style="font-size:1.000000em">5A, 最大100W</span></span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:0.4796%;--hb-y:17.1071%;--hb-width:14.3772%;--hb-height:4.6552%"><span><span style="font-size:1.000000em"><strong>DC出力ボタン</strong></span></span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:81.0348%;--hb-y:29.0614%;--hb-width:18.5483%;--hb-height:4.6552%"><span><span style="font-size:1.000000em"><strong>USB-A 出力ポート</strong></span></span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:83.2119%;--hb-y:32.8532%;--hb-width:16.276%;--hb-height:6.1207%"><span><span style="font-size:1.000000em">5-6V</span><span style="font-size:1.000000em">⎓</span><span style="font-size:1.000000em">3A, 6-9V</span><span style="font-size:1.000000em">⎓</span><span style="font-size:1.000000em">2A, </span><br/><span style="font-size:1.000000em">9-12V</span><span style="font-size:1.000000em">⎓</span><span style="font-size:1.000000em">1.5A, 最大18W</span></span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:0.2411%;--hb-y:33.6869%;--hb-width:13.3965%;--hb-height:8.2759%"><span><span style="font-size:1.000000em"><strong>シガーソケッ</strong></span><br/><span style="font-size:1.000000em"><strong>ト出力ポート</strong></span></span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:0.4797%;--hb-y:41.6617%;--hb-width:13.5489%;--hb-height:3.4483%"><span><span style="font-size:1.000000em">12V</span><span style="font-size:1.000000em">⎓</span><span style="font-size:1.000000em">10A 最大10A</span></span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:83.6979%;--hb-y:41.1756%;--hb-width:15.8565%;--hb-height:4.6552%"><span><span style="font-size:1.000000em"><strong>USB出力ボタン</strong></span></span></span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:85.4358%;--hb-y:47.6205%;--hb-width:14.1473%;--hb-height:4.6552%"><span><span style="font-size:1.000000em"><strong>AC出力ポート</strong></span></span></span><span class="hb-reference-live-label" data-source-line="11" style="--hb-x:88.1824%;--hb-y:51.1197%;--hb-width:11.3646%;--hb-height:4.0517%"><span><span style="font-size:1.000000em">(NEMA 5-20)</span></span></span><span class="hb-reference-live-label" data-source-line="12" style="--hb-x:91.7647%;--hb-y:54.023%;--hb-width:7.7823%;--hb-height:3.4483%"><span><span style="font-size:1.000000em">1*AC出力:</span></span></span><span class="hb-reference-live-label" data-source-line="13" style="--hb-x:78.9603%;--hb-y:56.6954%;--hb-width:20.5867%;--hb-height:3.4483%"><span><span style="font-size:1.000000em">100V~ 50/60Hz, 20A, 2000W</span></span></span><span class="hb-reference-live-label" data-source-line="14" style="--hb-x:87.4082%;--hb-y:59.3678%;--hb-width:12.139%;--hb-height:3.4483%"><span><span style="font-size:1.000000em">4*AC Total 出力:</span></span></span><span class="hb-reference-live-label" data-source-line="15" style="--hb-x:78.0722%;--hb-y:62.0402%;--hb-width:21.4749%;--hb-height:3.4483%"><span><span style="font-size:1.000000em">最大6000W, 瞬間最大12000W</span></span></span><span class="hb-reference-live-label" data-source-line="16" style="--hb-x:0.4796%;--hb-y:62.0308%;--hb-width:14.1893%;--hb-height:4.6552%"><span><span style="font-size:1.000000em"><strong>AC出力ボタン</strong></span></span></span><span class="hb-reference-live-label" data-source-line="17" style="--hb-x:0.6047%;--hb-y:79.877%;--hb-width:17.945%;--hb-height:10.3398%"><span><span style="font-size:1.000000em"><strong>合計出力</strong></span><br/><span style="font-size:0.714286em">100V, 30A, 最大3000W、</span><br/><span style="font-size:0.714286em">瞬間最大6000W</span></span></span><span class="hb-reference-live-label" data-source-line="18" style="--hb-x:82.2936%;--hb-y:79.877%;--hb-width:17.9448%;--hb-height:10.3398%"><span><span style="font-size:1.000000em"><strong>合計出力</strong></span><br/><span style="font-size:0.714286em">100V, 30A, 最大3000W、</span><br/><span style="font-size:0.714286em">瞬間最大6000W</span></span></span></div></div></figure></div>

### 左側面

<div class="native-figure native-overview-left native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview-left" data-source-fragment-sha256="21037296347e333207165e8bf2f1ba63671dd6061457a2b4f528f407988c212b" data-web-base-art-ref="overview-left" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="overview-left.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/overview-left.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:0.5603%;--hb-y:3.0317%;--hb-width:9.0303%;--hb-height:4.9564%"><span><span style="font-size:1.000000em"><strong>ハンドル</strong></span></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:0.5432%;--hb-y:26.4071%;--hb-width:30.5521%;--hb-height:4.9564%"><span><span style="font-size:1.000000em"><strong>NEMA L14-30R AC出力ポート</strong></span></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:0.5433%;--hb-y:30.529%;--hb-width:27.1134%;--hb-height:4.3139%"><span><span style="font-size:1.000000em">100V/200V ~ 50/60Hz, 最大30A</span></span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:0.6069%;--hb-y:34.6185%;--hb-width:44.9285%;--hb-height:6.5168%"><span><span style="font-size:1.000000em">高出力機器に電力を供給し、家庭用電源のインレットボックスまた</span><br/><span style="font-size:1.000000em">は切替スイッチに接続します。</span></span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:0.5432%;--hb-y:50.5104%;--hb-width:26.4322%;--hb-height:9.042%"><span><span style="font-size:1.000000em"><strong>NEMA 6-20 AC出力ポート</strong></span><br/><span style="font-size:0.857143em">200V ~ 50/60Hz, 最大20A</span></span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:0.5433%;--hb-y:58.625%;--hb-width:39.1404%;--hb-height:3.6714%"><span><span style="font-size:1.000000em">200Vの入力電圧を必要とする機器と互換性があります。</span></span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:0.6138%;--hb-y:77.6642%;--hb-width:17.6712%;--hb-height:4.9564%"><span><span style="font-size:1.000000em"><strong>ホイールブレーキ</strong></span></span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:0.6138%;--hb-y:86.0841%;--hb-width:9.2177%;--hb-height:4.9564%"><span><span style="font-size:1.000000em"><strong>ホイール</strong></span></span></span></div></div></figure></div>

### 右側面

<div class="native-figure native-overview-right native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview-right" data-source-fragment-sha256="4acabde64979bc735b44f1fd9bedf9f33cf0380e426baf99c11e9c8619d9ac1d" data-web-base-art-ref="overview-right" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="overview-right.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/overview-right.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:0.3407%;--hb-y:10.8279%;--hb-width:28.1805%;--hb-height:7.115%"><span><span style="font-size:1.000000em"><strong>リトラクタブルハンドル</strong></span><br/><span style="font-size:0.714286em">ボタンを押し、引っ張ると長さが伸びます</span></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:0.472%;--hb-y:19.5586%;--hb-width:18.046%;--hb-height:4.2688%"><span><span style="font-size:1.000000em"><strong>低電圧入力ポート</strong></span></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:0.4718%;--hb-y:23.5646%;--hb-width:42.5206%;--hb-height:5.6126%"><span><span style="font-size:1.000000em">2 x DC 8mm ポート; 16V-60V</span><span style="font-size:1.000000em">⎓</span><span style="font-size:1.000000em">10.5A 最大21A/1200Wに倍増</span><br/><span style="font-size:1.000000em">11V-16V（動作電圧）</span><span style="font-size:1.000000em">⎓</span><span style="font-size:1.000000em">8A 最大8Aに倍増</span></span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:0.472%;--hb-y:33.2847%;--hb-width:18.046%;--hb-height:4.2688%"><span><span style="font-size:1.000000em"><strong>高電圧入力ポート</strong></span></span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:0.4718%;--hb-y:37.4836%;--hb-width:27.83%;--hb-height:3.1621%"><span><span style="font-size:1.000000em">135V-450V</span><span style="font-size:1.000000em">⎓</span><span style="font-size:1.000000em">15A 最大15A， 最大4000W</span></span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:0.472%;--hb-y:42.4068%;--hb-width:13.1883%;--hb-height:4.2688%"><span><span style="font-size:1.000000em"><strong>電圧スイッチ</strong></span></span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:0.4718%;--hb-y:46.2899%;--hb-width:32.6622%;--hb-height:5.6126%"><span><span style="font-size:1.000000em">電圧スイッチの<strong>オン</strong>/<strong>オフ</strong>により、高電圧ソーラー</span><br/><span style="font-size:1.000000em">充電の有効/無効を切り替えます。</span></span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:0.472%;--hb-y:53.9665%;--hb-width:7.9371%;--hb-height:4.2688%"><span><span style="font-size:1.000000em"><strong>AC入力</strong></span></span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:0.4718%;--hb-y:57.9599%;--hb-width:31.4921%;--hb-height:3.1621%"><span><span style="font-size:1.000000em">100V-120V ~ 50/60Hz, 最大15A，最大1500W</span></span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:0.472%;--hb-y:66.4696%;--hb-width:20.1751%;--hb-height:4.2688%"><span><span style="font-size:1.000000em"><strong>DC拡張ポート端子A</strong></span></span></span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:0.4226%;--hb-y:70.6318%;--hb-width:16.5952%;--hb-height:3.1621%"><span><span style="font-size:1.000000em">バッテリーパックに接続</span></span></span><span class="hb-reference-live-label" data-source-line="11" style="--hb-x:0.5187%;--hb-y:81.8558%;--hb-width:13.3929%;--hb-height:4.2688%"><span><span style="font-size:1.000000em"><strong>底部ハンドル</strong></span></span></span></div></div></figure></div>

<span id="native-lcd"></span>

## 液晶画面

<div class="native-figure native-lcd-map"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="lcd-map" data-source-fragment-sha256="3cbf4f1ffdf505697ae370f394fec58b3768f6700dc490d741acb61f4561f44e" data-web-base-art-ref="lcd-map" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="lcd-map.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/lcd-map.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:15.7931%;--hb-y:1.3857%;--hb-width:1.394%;--hb-height:6.1671%"><span><span style="font-size:1.000000em">1</span></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:19.8272%;--hb-y:1.3865%;--hb-width:1.8048%;--hb-height:6.1671%"><span><span style="font-size:1.000000em">2</span></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:24.0461%;--hb-y:1.3865%;--hb-width:1.8159%;--hb-height:6.1671%"><span><span style="font-size:1.000000em">3</span></span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:27.8225%;--hb-y:1.3865%;--hb-width:1.9269%;--hb-height:6.1671%"><span><span style="font-size:1.000000em">4</span></span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:31.906%;--hb-y:1.3865%;--hb-width:1.8381%;--hb-height:6.1671%"><span><span style="font-size:1.000000em">5</span></span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:35.904%;--hb-y:1.3865%;--hb-width:1.8159%;--hb-height:6.1671%"><span><span style="font-size:1.000000em">6</span></span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:60.1062%;--hb-y:1.3865%;--hb-width:1.7271%;--hb-height:6.1671%"><span><span style="font-size:1.000000em">7</span></span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:1.0416%;--hb-y:45.07%;--hb-width:1.8559%;--hb-height:6.1671%"><span><span style="font-size:1.000000em">8</span></span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:97.0413%;--hb-y:45.4168%;--hb-width:3.2038%;--hb-height:6.1671%"><span><span style="font-size:1.000000em">20</span></span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:97.3524%;--hb-y:56.979%;--hb-width:2.582%;--hb-height:6.1671%"><span><span style="font-size:1.000000em">21</span></span></span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:0.9506%;--hb-y:57.5929%;--hb-width:1.8159%;--hb-height:6.1671%"><span><span style="font-size:1.000000em">9</span></span></span><span class="hb-reference-live-label" data-source-line="11" style="--hb-x:15.4277%;--hb-y:93.6501%;--hb-width:2.8596%;--hb-height:6.1671%"><span><span style="font-size:1.000000em">10</span></span></span><span class="hb-reference-live-label" data-source-line="12" style="--hb-x:20.19%;--hb-y:93.6501%;--hb-width:2.2156%;--hb-height:6.1671%"><span><span style="font-size:1.000000em">11</span></span></span><span class="hb-reference-live-label" data-source-line="13" style="--hb-x:25.4195%;--hb-y:93.6501%;--hb-width:2.6264%;--hb-height:6.1671%"><span><span style="font-size:1.000000em">12</span></span></span><span class="hb-reference-live-label" data-source-line="14" style="--hb-x:43.5082%;--hb-y:93.6501%;--hb-width:2.6375%;--hb-height:6.1671%"><span><span style="font-size:1.000000em">13</span></span></span><span class="hb-reference-live-label" data-source-line="15" style="--hb-x:48.5826%;--hb-y:93.6501%;--hb-width:2.7486%;--hb-height:6.1671%"><span><span style="font-size:1.000000em">14</span></span></span><span class="hb-reference-live-label" data-source-line="16" style="--hb-x:53.0442%;--hb-y:93.6501%;--hb-width:2.6597%;--hb-height:6.1671%"><span><span style="font-size:1.000000em">15</span></span></span><span class="hb-reference-live-label" data-source-line="17" style="--hb-x:61.34%;--hb-y:93.6501%;--hb-width:2.6375%;--hb-height:6.1671%"><span><span style="font-size:1.000000em">16</span></span></span><span class="hb-reference-live-label" data-source-line="18" style="--hb-x:71.709%;--hb-y:93.6501%;--hb-width:2.5487%;--hb-height:6.1671%"><span><span style="font-size:1.000000em">17</span></span></span><span class="hb-reference-live-label" data-source-line="19" style="--hb-x:76.361%;--hb-y:93.6501%;--hb-width:2.6775%;--hb-height:6.1671%"><span><span style="font-size:1.000000em">18</span></span></span><span class="hb-reference-live-label" data-source-line="20" style="--hb-x:81.6934%;--hb-y:93.6501%;--hb-width:2.5931%;--hb-height:6.1671%"><span><span style="font-size:1.000000em">19</span></span></span></div></div></figure></div>

<figure aria-label="液晶画面の表示" class="hb-lcd-table-composition" data-component-id="HB-TABLE-LCD-ICON" tabindex="0"><table class="hb-lcd-icon-table"><colgroup><col class="hb-lcd-col-number"/><col class="hb-lcd-col-icon"/><col class="hb-lcd-col-name"/><col class="hb-lcd-col-description"/></colgroup><tbody><tr><td class="hb-lcd-number">1</td><td class="hb-lcd-icon"><img alt="Wi-Fi" class="hb-lcd-icon-art" src="assets/lcd-01.svg"/></td><td class="hb-lcd-name">Wi-Fi</td><td class="hb-lcd-description"><strong>オン</strong>： Wi-Fi接続済。<strong>点滅</strong>： Wi-Fiに接続する準備ができました。<strong>オフ</strong>： Wi-Fi接続解除済。</td></tr><tr><td class="hb-lcd-number">2</td><td class="hb-lcd-icon"><img alt="Bluetooth" class="hb-lcd-icon-art" src="assets/lcd-02.svg"/></td><td class="hb-lcd-name">Bluetooth</td><td class="hb-lcd-description"><strong>オン</strong>： Bluetooth接続済。<strong>点滅</strong>： Bluetoothに接続する準備ができました。<strong>オフ</strong>： Bluetooth接続解除済。</td></tr><tr><td class="hb-lcd-number">3</td><td class="hb-lcd-icon"><img alt="静音充電モードJackeryアプリで有効/無効にできます" class="hb-lcd-icon-art" src="assets/lcd-03.svg"/></td><td class="hb-lcd-name">静音充電モードJackeryアプリで有効/無効にできます</td><td class="hb-lcd-description"><strong>オン</strong>： 充電中の騒音が大幅に低減され、充電電力が低下し、充電速度が低減します。<strong>オフ</strong>： 静音充電モードが無効になっています。</td></tr><tr><td class="hb-lcd-number">4</td><td class="hb-lcd-icon"><img alt="バッテリー節約モードJackeryアプリで有効/無効にできます" class="hb-lcd-icon-art" src="assets/lcd-04.svg"/></td><td class="hb-lcd-name">バッテリー節約モードJackeryアプリで有効/無効にできます</td><td class="hb-lcd-description"><strong>オン</strong>：製品の電力使用量を削減して、バッテリー寿命を延ばします。<strong>オフ</strong>：バッテリー節約モードが無効になっています。</td></tr><tr><td class="hb-lcd-number">4</td><td class="hb-lcd-icon"><img alt="自家発電モードJackeryアプリで有効/無効にできます" class="hb-lcd-icon-art" src="assets/lcd-05.svg"/></td><td class="hb-lcd-name">自家発電モードJackeryアプリで有効/無効にできます</td><td class="hb-lcd-description">太陽光エネルギーの利用を最大化し、蓄電された太陽光エネルギーを優先することで、ご家庭の電力からの供給量を削減します。</td></tr><tr><td class="hb-lcd-number">5</td><td class="hb-lcd-icon"><img alt="計画充電モードJackeryアプリで設定してください" class="hb-lcd-icon-art" src="assets/lcd-06.svg"/></td><td class="hb-lcd-name">計画充電モードJackeryアプリで設定してください</td><td class="hb-lcd-description">Jackery ポータブル電源 5000 Plusの充電時間をカスタマイズすることで、電気料金オフピーク時間に基づいた充電プランを選択。これにより月々の電気料金を削減することができます。</td></tr><tr><td class="hb-lcd-number">6</td><td class="hb-lcd-icon"><img alt="オンラインUPSJackeryアプリで設定できます" class="hb-lcd-icon-art" src="assets/lcd-07.svg"/></td><td class="hb-lcd-name">オンラインUPSJackeryアプリで設定できます</td><td class="hb-lcd-description"><strong>オン</strong>： 製品はオンラインUPSモードです（0 ms）。<strong>オフ</strong>： バックアップUPSモード（デフォルト）。</td></tr><tr><td class="hb-lcd-number">7</td><td class="hb-lcd-icon"><img alt="交流電源による出力マーク（正弦波）" class="hb-lcd-icon-art" src="assets/lcd-08.svg"/></td><td class="hb-lcd-name">交流電源による出力マーク（正弦波）</td><td class="hb-lcd-description">AC出力（純正弦波）がオンになっています。</td></tr><tr><td class="hb-lcd-number">8</td><td class="hb-lcd-icon"><img alt="入力電力表示" class="hb-lcd-icon-art" src="assets/lcd-09.svg"/></td><td class="hb-lcd-name">入力電力表示</td><td class="hb-lcd-description">入力電力をワットで表示します。</td></tr><tr><td class="hb-lcd-number">9</td><td class="hb-lcd-icon"><img alt="充電残り時間" class="hb-lcd-icon-art" src="assets/lcd-10.svg"/></td><td class="hb-lcd-name">充電残り時間</td><td class="hb-lcd-description">充電残り時間を表示します。</td></tr><tr><td class="hb-lcd-number">10</td><td class="hb-lcd-icon"><img alt="AC入力電力表示" class="hb-lcd-icon-art" src="assets/lcd-11.svg"/></td><td class="hb-lcd-name">AC入力電力表示</td><td class="hb-lcd-description">製品は、系統電力を使用し、AC入力を介して充電されます。</td></tr><tr><td class="hb-lcd-number">11</td><td class="hb-lcd-icon"><img alt="シガーソケット入力電力表示" class="hb-lcd-icon-art" src="assets/lcd-12.svg"/></td><td class="hb-lcd-name">シガーソケット入力電力表示</td><td class="hb-lcd-description">製品は、DC 12V（カーチャージ）を使用し、低PV入力（8020）を介して充電されています。</td></tr><tr><td class="hb-lcd-number">12</td><td class="hb-lcd-icon"><img alt="高電圧入力インジケーター" class="hb-lcd-icon-art" src="assets/lcd-13.svg"/></td><td class="hb-lcd-name">高電圧入力インジケーター</td><td class="hb-lcd-description">製品は、高PV入力（MC4）を介し、ソーラーパネルを使用して充電されます。</td></tr><tr><td class="hb-lcd-number">12</td><td class="hb-lcd-icon"><img alt="低電圧入力インジケーター" class="hb-lcd-icon-art" src="assets/lcd-14.svg"/></td><td class="hb-lcd-name">低電圧入力インジケーター</td><td class="hb-lcd-description">製品は、ソーラーパネルを使用し、低PV入力（8020）を介して充電されています。</td></tr><tr><td class="hb-lcd-number">13</td><td class="hb-lcd-icon"><img alt="バッテリーアイコン" class="hb-lcd-icon-art" src="assets/lcd-15.svg"/></td><td class="hb-lcd-name">バッテリーアイコン</td><td class="hb-lcd-description">製品の充電中は、バッテリーのパーセンテージを囲むオレンジ色の円が順番に点灯します。他のデバイスの充電時には、オレンジ色の円は点灯したままになります。</td></tr><tr><td class="hb-lcd-number">14</td><td class="hb-lcd-icon"><img alt="バッテリー残量警告灯" class="hb-lcd-icon-art" src="assets/lcd-16.svg"/></td><td class="hb-lcd-name">バッテリー残量警告灯</td><td class="hb-lcd-description"><strong>オン</strong>：バッテリー残量が20％未満です。<strong>点滅</strong>：バッテリー残量が5％未満です。<strong>オフ</strong>：製品は充電中です。</td></tr><tr><td class="hb-lcd-number">15</td><td class="hb-lcd-icon"><img alt="バッテリーレベルパーセントタグ" class="hb-lcd-icon-art" src="assets/lcd-17.svg"/></td><td class="hb-lcd-name">バッテリーレベルパーセントタグ</td><td class="hb-lcd-description">バッテリー残量を表示します。</td></tr><tr><td class="hb-lcd-number">16</td><td class="hb-lcd-icon"><img alt="バッテリーパックインジケータと接続された量" class="hb-lcd-icon-art" src="assets/lcd-18.svg"/></td><td class="hb-lcd-name">バッテリーパックインジケータと接続された量</td><td class="hb-lcd-description">本製品が指定された数の5000 Plusバッテリーパックに接続されていることを示します。</td></tr><tr><td class="hb-lcd-number">17</td><td class="hb-lcd-icon"><img alt="エラーコード" class="hb-lcd-icon-art" src="assets/lcd-19.svg"/></td><td class="hb-lcd-name">エラーコード</td><td class="hb-lcd-description">製品エラーが発生しました。詳細については、トラブルシューティングのセクションを参照してください。</td></tr><tr><td class="hb-lcd-number">18</td><td class="hb-lcd-icon"><img alt="高温インジケーター" class="hb-lcd-icon-art" src="assets/lcd-20.svg"/></td><td class="hb-lcd-name">高温インジケーター</td><td class="hb-lcd-description">高温保護が作動しました。製品の温度が通常の動作範囲に戻るまで、製品の機能が停止する場合があります。</td></tr><tr><td class="hb-lcd-number">18</td><td class="hb-lcd-icon"><img alt="低温インジケーター" class="hb-lcd-icon-art" src="assets/lcd-21.svg"/></td><td class="hb-lcd-name">低温インジケーター</td><td class="hb-lcd-description">低温保護が作動しました。製品の温度が通常の動作範囲に戻るまで、製品の機能が停止する場合があります。</td></tr><tr><td class="hb-lcd-number">19</td><td class="hb-lcd-icon"><img alt="省エネモード" class="hb-lcd-icon-art" src="assets/lcd-22.svg"/></td><td class="hb-lcd-name">省エネモード</td><td class="hb-lcd-description">出力の消し忘れによる不要なバッテリー消費を防ぐため、製品はデフォルトで省エネモードを有効にしています。デバイスが接続されていない場合、または接続されているデバイスの消費電力が特定のしきい値（AC出力≤25W、USB出力≤2W、カー出力≤2W）を下回っている場合、デバイスは12時間後にすべての出力を自動的にオフにします。<strong>オン</strong>/<strong>オフ</strong>：AC電源ボタンと主電源ボタンの両方を長押しします</td></tr><tr><td class="hb-lcd-number">20</td><td class="hb-lcd-icon"><img alt="出力電力" class="hb-lcd-icon-art" src="assets/lcd-23.svg"/></td><td class="hb-lcd-name">出力電力</td><td class="hb-lcd-description">出力電力をワットで表示します。</td></tr><tr><td class="hb-lcd-number">21</td><td class="hb-lcd-icon"><img alt="残り放電時間" class="hb-lcd-icon-art" src="assets/lcd-24.svg"/></td><td class="hb-lcd-name">残り放電時間</td><td class="hb-lcd-description">放電残りの時間を表示します。</td></tr></tbody></table></figure>

<span id="native-operations"></span>

## 使い方

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">重要</td><td class="manual-callout-body"><p>省エネモードでは、DC出力またはAC出力をオンにするか、充電入力または放電出力がない場合、12時間後に自動的にシャットダウンします。</p></td></tr></tbody></table>

### 出力オン/オフ

<div class="native-figure native-power native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="power" data-source-fragment-sha256="6904ed96a806dab986a5298eb738a751ae25041063a14291e9d56dc3f051f0c9" data-web-base-art-ref="power" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="power.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/power.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:2.6684%;--hb-y:4.3807%;--hb-width:41.7651%;--hb-height:7.6927%;--hb-fill:#e7e7e8"><span><span style="font-size:1.000000em"><strong>前提：</strong></span><span style="font-size:1.000000em">主電源ボタンのみが<strong>オン</strong>になっています。</span></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:75.9893%;--hb-y:20.2354%;--hb-width:4.8927%;--hb-height:6.0674%"><span><span style="font-size:1.000000em"><strong>オン</strong></span></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:76.1229%;--hb-y:25.7276%;--hb-width:7.4063%;--hb-height:5.2809%"><span><span style="font-size:1.000000em">1回押す</span></span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:75.8959%;--hb-y:34.9158%;--hb-width:4.8571%;--hb-height:6.0674%"><span><span style="font-size:1.000000em"><strong>オフ</strong></span></span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:76.1229%;--hb-y:39.7939%;--hb-width:11.2159%;--hb-height:5.2809%"><span><span style="font-size:1.000000em">3秒間長押し</span></span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:80.3131%;--hb-y:46.0417%;--hb-width:3.0927%;--hb-height:6.0674%"><span><span style="font-size:1.000000em">3S</span></span></span><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="6" style="--hb-x:43.3112%;--hb-y:63.5843%;--hb-width:51.6971%;--hb-height:27.5236%;--hb-fill:#e7e7e8"><span><span style="font-size:1.000000em">本製品のデフォルトの待機時間は2時間です。(充電また</span><br/><span style="font-size:1.000000em">は放電がない場合、2時間後に自動的にシャットダウン</span><br/><span style="font-size:1.000000em">します）。 自動シャットダウン時間はJackeryアプリで設</span><br/><span style="font-size:1.000000em">定できます。</span></span></span></div></div></figure></div>

### AC出力のオン/オフ

<div class="native-figure native-ac-output native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ac-output" data-source-fragment-sha256="f1b275463c04b92c40c6dfc8da82cac3627e126eedc123c0a3d8d7a95cc4b4bd" data-web-base-art-ref="ac-output" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="ac-output.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/ac-output.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:2.6684%;--hb-y:4.1113%;--hb-width:54.6864%;--hb-height:7.245%;--hb-fill:#e7e7e8"><span><span style="font-size:1.000000em"><strong>前提：</strong></span><span style="font-size:1.000000em">主電源ボタンが<strong>オン</strong>になっていることを確認してください。</span></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:88.2358%;--hb-y:11.8973%;--hb-width:4.8927%;--hb-height:5.7143%"><span><span style="font-size:1.000000em"><strong>オン</strong></span></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:88.3695%;--hb-y:17.0693%;--hb-width:7.4063%;--hb-height:4.9735%"><span><span style="font-size:1.000000em">1回押す</span></span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:88.1425%;--hb-y:25.7232%;--hb-width:4.8571%;--hb-height:5.7143%"><span><span style="font-size:1.000000em"><strong>オフ</strong></span></span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:88.3695%;--hb-y:30.3138%;--hb-width:7.4063%;--hb-height:4.9735%"><span><span style="font-size:1.000000em">1回押す</span></span></span></div></div></figure></div>

### USB出力オン/オフ

<div class="native-figure native-usb-output native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="usb-output" data-source-fragment-sha256="9885fb0c7c1fc27e86bb332fddc487a88c33765f5fc2779a502ba73426324487" data-web-base-art-ref="usb-output" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="usb-output.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/usb-output.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:2.59%;--hb-y:5.096%;--hb-width:54.6864%;--hb-height:10.2955%;--hb-fill:#e7e7e8"><span><span style="font-size:1.000000em"><strong>前提：</strong></span><span style="font-size:1.000000em">主電源ボタンが<strong>オン</strong>になっていることを確認してください。</span></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:84.579%;--hb-y:18.5441%;--hb-width:4.8927%;--hb-height:8.1203%"><span><span style="font-size:1.000000em"><strong>オン</strong></span></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:84.7126%;--hb-y:25.8938%;--hb-width:7.4063%;--hb-height:7.0677%"><span><span style="font-size:1.000000em">1回押す</span></span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:84.4856%;--hb-y:38.1915%;--hb-width:4.8571%;--hb-height:8.1203%"><span><span style="font-size:1.000000em"><strong>オフ</strong></span></span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:84.7126%;--hb-y:44.7148%;--hb-width:7.4063%;--hb-height:7.0677%"><span><span style="font-size:1.000000em">1回押す</span></span></span></div></div></figure></div>

### DC出力オン/オフ

<div class="native-figure native-dc-output native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="dc-output" data-source-fragment-sha256="8dfc9c69e11521c54506b030b0ea656b57151e55a8c349ca7e16b33212abdf1d" data-web-base-art-ref="dc-output" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="dc-output.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/dc-output.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:2.59%;--hb-y:5.5492%;--hb-width:54.6864%;--hb-height:10.2955%;--hb-fill:#e7e7e8"><span><span style="font-size:1.000000em"><strong>前提：</strong></span><span style="font-size:1.000000em">主電源ボタンが<strong>オン</strong>になっていることを確認してください。</span></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:84.579%;--hb-y:18.4009%;--hb-width:4.8927%;--hb-height:8.1203%"><span><span style="font-size:1.000000em"><strong>オン</strong></span></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:84.7126%;--hb-y:25.7514%;--hb-width:7.4063%;--hb-height:7.0677%"><span><span style="font-size:1.000000em">1回押す</span></span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:84.4856%;--hb-y:38.0483%;--hb-width:4.8571%;--hb-height:8.1203%"><span><span style="font-size:1.000000em"><strong>オフ</strong></span></span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:84.7126%;--hb-y:44.5724%;--hb-width:7.4063%;--hb-height:7.0677%"><span><span style="font-size:1.000000em">1回押す</span></span></span></div></div></figure></div>

### LCDスクリーン

<div class="native-lcd-scroll"><div class="native-lcd-controls"><div class="native-figure native-lcd-button"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="lcd-button" data-source-fragment-sha256="22165c38b79163050bee2321f09215d035560c75a005b9667f54c316d9fff84d"><div class="hb-reference-semantic" data-reference-id="lcd-button.semantic"><img alt="lcd-button" class="hb-reference-art hb-composite-art" src="assets/lcd-button.svg"/></div></figure></div><div class="native-lcd-actions"><table class="manual-table"><tbody><tr><td rowspan="3">LCDスクリーン</td><td><strong>オン</strong>にする</td><td>主電源ボタンを押すか、充電入力がある場合。</td></tr><tr><td><strong>オフ</strong>にする</td><td>主電源ボタンを押します。</td></tr><tr><td>自動<strong>オフ</strong></td><td>2分間操作がないとLCDは自動的に消灯し、スリープモードになります。</td></tr><tr><td rowspan="3">常時点灯表示モード（充電中または放電中）</td><td><strong>オン</strong>にする</td><td>LCD画面が<strong>オン</strong>のときに主電源ボタンをダブルクリックします。</td></tr><tr><td><strong>オフ</strong>にする</td><td>主電源ボタンを押します。</td></tr><tr><td>自動<strong>オフ</strong></td><td>常時点灯ディスプレイモードは、2時間操作がないと自動的に消灯します。</td></tr></tbody></table></div></div></div>

### キーの組み合わせ

<figure aria-label="ボタン / 操作 / 機能" class="hb-key-combination-composition" data-component-id="HB-TABLE-KEY-COMBINATIONS" tabindex="0"><table class="hb-key-combination-table"><colgroup><col class="hb-key-col-buttons"/><col class="hb-key-col-operation"/><col class="hb-key-col-function"/></colgroup><thead><tr><th class="hb-key-buttons" scope="col">ボタン</th><th class="hb-key-operation" scope="col">操作</th><th class="hb-key-function" scope="col">機能</th></tr></thead><tbody><tr><td class="hb-key-buttons"><div class="native-key-buttons"><div class="native-key-button"><img alt="" src="assets/button-power-bottom.svg"/><p>主電源ボタン</p></div><span class="native-key-plus"> + </span><div class="native-key-button"><img alt="" src="assets/button-usb-bottom.svg"/><p>USB電源ボタン</p></div></div></td><td class="hb-key-operation"><p>3S</p><p>両方を3秒間長押し</p></td><td class="hb-key-function">Wi-FiとBluetoothをリセット</td></tr><tr><td class="hb-key-buttons"><div class="native-key-buttons"><div class="native-key-button"><img alt="" src="assets/button-power-bottom.svg"/><p>主電源ボタン</p></div><span class="native-key-plus"> + </span><div class="native-key-button"><img alt="" src="assets/button-ac-bottom.svg"/><p>AC電源ボタン</p></div></div></td><td class="hb-key-operation"><p>3S</p><p>両方を3秒間長押し</p></td><td class="hb-key-function">省エネモードのオン/オフを切り替えます</td></tr><tr><td class="hb-key-buttons"><div class="native-key-buttons"><div class="native-key-button"><img alt="" src="assets/button-usb-bottom.svg"/><p>USB電源ボタン</p></div><span class="native-key-plus"> + </span><div class="native-key-button"><img alt="" src="assets/button-ac-bottom.svg"/><p>AC電源ボタン</p></div></div></td><td class="hb-key-operation"><p>3S</p><p>両方を3秒間長押し</p></td><td class="hb-key-function">Wi-FiとBluetoothをオンにします</td></tr><tr><td class="hb-key-buttons"><div class="native-key-buttons"><div class="native-key-button"><img alt="" src="assets/button-dc.svg"/><p>DC電源ボタン</p></div><span class="native-key-plus"> + </span><div class="native-key-button"><img alt="" src="assets/button-ac-bottom.svg"/><p>AC電源ボタン</p></div></div></td><td class="hb-key-operation"><p>3S</p><p>両方を3秒間長押し</p></td><td class="hb-key-function">オンラインUPSまたはバックアップUPSに切り替えます</td></tr></tbody></table></figure>

<span id="native-troubleshooting"></span>

## トラブルシューティング

<figure aria-label="トラブルシューティング" class="hb-reference-composition hb-reference-lcd-legend" data-component-id="HB-TABLE-REFERENCE" data-component-variant="lcd-legend" tabindex="0"><table class="hb-reference-table"><thead><tr><th scope="col">エラーコード</th><th scope="col">名前</th><th scope="col">説明（内部故障メンテナンス専用）</th></tr></thead><tbody><tr><td>F0</td><td>BMSデータ通信エラー</td><td>BMSとメインボード間のデータ通信障害</td></tr><tr><td>F1</td><td>インバーターデータ通信エラー</td><td>インバーターとメインボード間のデータ通信障害</td></tr><tr><td>F2</td><td>DC入力データ通信エラー</td><td>DC充電モジュールとBMS間のデータ通信障害</td></tr><tr><td>F3</td><td>BMSまたはバッテリーの故障</td><td>BMSまたはバッテリーの故障</td></tr><tr><td>F4</td><td>バッテリー過電圧</td><td>バッテリー過電圧</td></tr><tr><td>F5</td><td>バッテリー低電圧</td><td>バッテリー低電圧</td></tr><tr><td>F6</td><td>インバーターの故障</td><td>AC出力過電流 / 過負荷 / 短絡；系統電力入力過電圧 / 低電圧 / 過周波数 / 低周波数；インバーター過熱保護オン（起動）絶縁検出障害</td></tr><tr><td>F7</td><td>DC入力障害</td><td>PV入力過電圧；DC充電モジュール過熱保護オン / 起動；DC充電モジュールの出力過電流保護オン / 起動</td></tr><tr><td>F8</td><td>バッテリーの充電 / 放電 過電流 / 短絡</td><td>BMS過電流 / 短絡保護オン / 起動</td></tr><tr><td>F9</td><td>DC出力過電流 / 短絡</td><td>USB短絡保護オン / 起動</td></tr><tr><td>FA</td><td>並列ユニット通信エラー</td><td>2つの5000 Plusの欠陥が原因で発生した両ユニット間のデータ通信障害。</td></tr><tr><td>FC</td><td>バッテリーパック通信エラー</td><td>5000 Plusとバッテリーパック間のデータ通信障害</td></tr></tbody></table></figure>

<span id="native-ups"></span>

## UPS機能

<p>UPS（無停電電源装置）は、停電などが発生した時に電気の供給を自動で切り替え、自動バックアップ電力を供給する継続的な電源システムです。</p>

<div class="native-figure native-ups native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ups" data-source-fragment-sha256="82c10ca65c817b6fa7dbf2255986e1f2d0abbfe6068ab1f07ff5038015e7dbc5" data-web-base-art-ref="ups" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="ups.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/ups.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:46.4051%;--hb-y:68.4446%;--hb-width:48.1346%;--hb-height:21.501%;--hb-fill:#e7e7e8"><span><span style="font-size:1.000000em">本製品をAC充電ケーブルでコンセントに接続し、AC</span><br/><span style="font-size:1.000000em">出力ボタンを押して、同時に電化製品に電力を供給</span><br/><span style="font-size:1.000000em">してください。</span></span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">重要</td><td class="manual-callout-body"><p>·本製品のNEMA L14-30RおよびNEMA 6-20 コンセントは、製品が AC 充電ケーブルを使用して壁のコンセントに接続されている場合、パススルー機能により100V 出力を提供します。·システム設定は、製品がオンラインUPSモードで再起動すると、バックアップUPSモードに戻ります。·オンラインUPSモードでは、NEMA 5-20出力ポートのみが動作し、0ミリ秒スイッチングをサポートし、最大出力電力は3000Wです。·バックアップUPSとして使用している際はパススルー機能により充電と出力が同時に行われている状態のため、ポータブル電源の最大出力は1500Wに制限され、停電時には定格出力に戻ります。</p></td></tr></tbody></table>

<p>本製品はバックアップUPS（20ミリ秒切り替え）とオンラインUPS（0ミリ秒切り替え）に対応しています。</p>

### バックアップUPS

<p>デフォルトではバックアップUPS機能が有効になっています。主電源が突然失われた場合、このデバイスは20ミリ秒以内に自動的に電源供給を切り替え、電化製品の電源を入れます。</p>

### オンラインUPS

<p>オンラインUPSモード(0ミリ秒電源切り替え)に変更する方法は2通りあります。</p>

<p>1. JackeryアプリでオンラインUPS機能を有効にする。</p>

<p>2. ディスプレイ画面にオンラインUPSのアイコンが表示されるまで、DCボタンとACボタンを同時に押してください。</p>

<span id="native-battery-packs"></span>

## バッテリーパック（別売）に接続

<p>本製品は最大5個のバッテリーパックに対応し、大容量電源のニーズに応えることができます。使用方法の詳細については、Jackery Battery Pack 5000 Plusの取扱説明書を参照してください。</p>

<div class="native-figure native-battery-packs native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="battery-packs" data-source-fragment-sha256="6f20ad957c444b28707c222d17b03ffe6c48fc4ab12fca33381df1d53fe45fe2" data-web-base-art-ref="battery-packs" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="battery-packs.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/battery-packs.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:55.2002%;--hb-y:88.6581%;--hb-width:6.5468%;--hb-height:6.0951%"><span><span style="font-size:1.000000em">≥20cm</span></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:28.2792%;--hb-y:89.4857%;--hb-width:6.5468%;--hb-height:6.0951%"><span><span style="font-size:1.000000em">≥20cm</span></span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">重要</td><td class="manual-callout-body"><p>Battery packを Jackery Explorer 5000 Plus に接続する前に、両方の電源がオフになっていることを確認してください。製品が適切に動作するよう、両側の吸気口と排気口が遮られていないことを確認してください。適切な放熱を確保するため、通気口と物との間に少なくとも20cmの空間を空けてください。</p></td></tr></tbody></table>

<span id="native-charging"></span>

## 充電方法

<p>最初に使用する前に、デバイスを完全に充電してください。</p>

<p>グリーンエネルギー優先モード:本製品はグリーンエネルギー優先モードを搭載しており、ソーラーパネルとAC充電ケーブルを使って同時に充電できます。同時に充電すると、ソーラーが優先されますが、バッテリーの最大許容電力で同時に充電されます。</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ご注意</td><td class="manual-callout-body"><p>・製品の充電動作温度範囲は0℃～45℃、放電動作温度範囲は-15℃～45℃です。上限・下限温度を超えた場合、充放電が制限され、または充放電不可の可能性があります。・温度によって、製品の充電効率と実際の容量は異なります。・周囲温度が-15℃～-10℃の場合、最大出力は3000Wに低下します。</p></td></tr></tbody></table>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ご注意</td><td class="manual-callout-body"><p>・はじめてお使いになるときは、本製品をフル充電してからご使用ください。・充電池は空の状態で長期保管(3カ月～6カ月）すると、性能が劣化したり、充電できなくなる場合があります。・本機を長期保管する場合には、3ヵ月に１度を目安に本体にACアダプターやソーラーパネルを通して蓄電が可能か、他製品に給電可能かなど動作確認をお願い致します。長期保管の際は満充電(電池残量100%)で保管することを推奨します。</p></td></tr></tbody></table>

### AC充電ケーブル

<p>コンセントよりJackery ポータブル電源 5000 Plus 本体に充電する場合、電流容量が大きいため、他機器と併用したり途中接続をすると、コンセントの電流上限値を超え充電停止したり、配線やコンセント・接続部が発熱し、火災の原因となる恐れがあります。電源タップなどを使って他の電気製品と併用しないでください。</p>

<div class="native-figure native-ac-charge native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ac-charge" data-source-fragment-sha256="cc12d1a7574709d1b21c98785e131055bbb60b7d5f5d341b1bd7df875add7cd5" data-web-base-art-ref="ac-charge" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="ac-charge.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/ac-charge.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:60.1408%;--hb-y:48.2747%;--hb-width:37.273%;--hb-height:7.0677%"><span><span style="font-size:1.000000em">付属のAC充電ケーブルをご使用ください。</span></span></span></div></div></figure></div>

### ソーラー充電

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ご注意</td><td class="manual-callout-body"><p>ソーラーパネルを直列に接続する場合、すべてのパネルの最大電圧出力が低電圧入力ポートでは16V～60V、高電圧入力ポートでは135V～450Vの範囲内にあることを確認してください。</p></td></tr></tbody></table>

### 低電圧入力ポートに接続

<p>低電圧入力電圧範囲：16V &lt; ソーラー入力合計 &lt; 60VJackery ポータブル電源 5000 Plusには2つの低電圧入力ポートがあり、各ポートはJackery SolarSaga200を3枚まで直接接続することができます。1つの低電圧入力ポートに2つ以上のソーラーパネルを同時に接続する必要がある場合は、下図を参照してSolarsagaアダプター（別売り）を介して充電してください。</p>

<div class="native-figure native-low-pv native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="low-pv" data-source-fragment-sha256="044731176c1bc31ffe08e2d37c13cff5403f3381a02a4ddd8bffb0683a9de5ba" data-web-base-art-ref="low-pv" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="low-pv.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/low-pv.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:76.2544%;--hb-y:88.2467%;--hb-width:15.471%;--hb-height:5.5279%"><span><span style="font-size:1.000000em">SolarSaga 200 × 6</span></span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ご注意</td><td class="manual-callout-body"><p>2つの入力を同時に使用する場合、2つのチャンネルの電圧の不一致による機器の損傷や充電の問題を避けるため、必ず同じ種類のソーラーパネルを使用し、2つの入力のソーラーパネルの数は同じでなければなりません。</p></td></tr></tbody></table>

### 高電圧入力ポートに接続

<p>高電圧入力電圧範囲：135V &lt; 総太陽光入力 &lt; 450V</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ご注意</td><td class="manual-callout-body"><p>・高電圧入力を接続する前またはメンテナンス中には、高電圧スイッチをオフにしておきます。・高電圧入力ポートを使用する前に、電圧スイッチがオンになっていることを確認してください。・付属のMC4レンチを使用してMC4コネクタを分解する前に高電圧スイッチが「OFF」または「LOCK」の位置にあることを確認してください。</p></td></tr></tbody></table>

<div class="native-figure native-high-pv native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="high-pv" data-source-fragment-sha256="7bb26ab6706b3124db5c315d363f60f3d650d05d2fec6c9f0048804fd8997225" data-web-base-art-ref="high-pv" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="high-pv.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/high-pv.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:7.0908%;--hb-y:8.7068%;--hb-width:30.4929%;--hb-height:9.3287%"><span><span style="font-size:1.000000em">付属の MC4 レンチで MC4 コネ</span><br/><span style="font-size:1.000000em">クタを分解します。</span></span></span></div></div></figure></div>

<div class="native-figure native-high-pv-lock native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="high-pv-lock" data-source-fragment-sha256="2355f95179d69ae04037f74e787914ff2a04f5462f2ff15b6b873be1fc194e3b" data-web-base-art-ref="high-pv-lock" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="high-pv-lock.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/high-pv-lock.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:3.9968%;--hb-y:8.4097%;--hb-width:6.4911%;--hb-height:8.6325%"><span><span style="font-size:1.000000em"><strong>ロック</strong></span></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:53.966%;--hb-y:9.1653%;--hb-width:10.476%;--hb-height:8.6325%"><span><span style="font-size:1.000000em"><strong>ロック解除</strong></span></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:3.7897%;--hb-y:19.293%;--hb-width:41.8519%;--hb-height:8.6325%"><span><span style="font-size:1.000000em">高電圧スイッチを「LOCK」位置に回し、ロック機</span></span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:53.9163%;--hb-y:20.0486%;--hb-width:39.0309%;--hb-height:8.6325%"><span><span style="font-size:1.000000em">ロック機構を解除すると、スイッチは「OFF」</span></span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:3.7897%;--hb-y:27.8375%;--hb-width:14.1048%;--hb-height:8.6325%"><span><span style="font-size:1.000000em">構を押します。</span></span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:53.9474%;--hb-y:28.5931%;--hb-width:16.6946%;--hb-height:8.6325%"><span><span style="font-size:1.000000em">位置 に戻ります。</span></span></span></div></div></figure></div>

### 高電圧＋低電圧入力

<p>低電圧入力用の電圧範囲：16V &lt; 総太陽光入力 &lt; 60V高電圧入力の電圧範囲：135V &lt; 総太陽光入力 &lt; 450V</p>

<div class="native-figure native-dual-pv native-dense"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="dual-pv" data-source-fragment-sha256="0c66ccafa23616c19ca1e92a43b633566946a182d8ab4130ddfc6de832746e75"><div class="hb-reference-semantic" data-reference-id="dual-pv.semantic"><img alt="dual-pv" class="hb-reference-art hb-composite-art" src="assets/dual-pv.svg"/></div></figure></div>

### 車載シガーソケットからの充電について

<p>・  本製品は12V / 10A対応の車のシガーソケットから充電が可能です。</p>

<p>・  必ずエンジンを始動した後にシガーソケットをご使用ください。車のバッテリー上がりを防止するためです。</p>

<p>・  ご使用前に、車側の充電ポートとシガーライターケーブルの接触に問題がないかをご確認ください。しっかりと所定の位置に差し込まれているかもご確認ください。</p>

<p>・  悪路などで車の振動が大きい場合は、接触不良により発熱・焼損の恐れがあります。その場合は、安全のためシガーソケットでの充電を中止してください。</p>

<p>※本製品の誤った取り扱いにより生じた損害について、当社では一切の責任を負いかねます。あらかじめご了承ください。</p>

<div class="native-figure native-car-charge native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="car-charge" data-source-fragment-sha256="4ddf75613ed737ca334ab6b3480ab54d0f7ed62892bcd976f808ce5831d3f7b8" data-web-base-art-ref="car-charge" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="car-charge.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/car-charge.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:69.1211%;--hb-y:20.4215%;--hb-width:2.8571%;--hb-height:9.9083%"><span><span style="font-size:1.000000em">車</span></span></span><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="1" style="--hb-x:49.619%;--hb-y:82.2453%;--hb-width:39.6876%;--hb-height:10.9624%;--hb-fill:#ffffff"><span><span style="font-size:1.000000em">*シガーソケット充電ケーブルは別売りです。</span></span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">充電に関する安全上のご注意</td><td class="manual-callout-body"><p>シガーソケット充電とソーラー充電を同時に使用しないでください。同時に使用すると、車のヒューズが損傷する可能性があります。シガーソケット充電は12V, 10A車専用で、24V車は充電できません。人身傷害や物的損害を避けるため、本製品の充電に24V車を使用しないでください。Jackeryブランド以外の付属品を使用して充電しないでください。特に、ソーラーパネルで充電する際は、Jackeryのソーラーパネルを使用することをお勧めします。他社ソーラーパネルで充電することによる損失について、当社は一切の責任を負いません。</p></td></tr></tbody></table>

<span id="native-safety"></span>

## 安全上のご注意

<p>ご使用の前にこの「安全上のご注意」をよくお読みのうえ、正しくお使いください。</p>

### 絵表示について

<p>製品を安全に正しくお使いいただき、お客様や他の方々への危害や財産への損害を未然に防止するための表示です。内容をよく理解してから本文をお読みください。</p>

<table class="manual-table native-safety-signals"><tbody><tr><th><img alt="警告" src="assets/symbol-warning_triangle.svg"/><strong>警告</strong></th><td>この表示を無視して、誤った取り扱いをすると、人が死亡または重傷を負う可能性が想定される内容を示しています。</td></tr><tr><th><img alt="注意" src="assets/symbol-warning_triangle.svg"/><strong>注意</strong></th><td>この表示を無視して、誤った取り扱いをすると、人が傷害を負う可能性が想定される内容または物的損害の発生が想定される内容を示しています。</td></tr></tbody></table>

### 絵表示の説明

<div class="native-safety-columns"><table class="manual-table native-safety-table"><tbody><tr><td><img alt="unplug" src="assets/symbol-unplug.svg"/></td><td>コンセントから電源プラグを抜く記号</td></tr><tr><td><img alt="do_not_dismantle" src="assets/symbol-do_not_dismantle.svg"/></td><td>製品を分解、改造を禁止する記号</td></tr><tr><td><img alt="no_wet_hands" src="assets/symbol-no_wet_hands.svg"/></td><td>製品に濡れた手で触れることを禁止する記号</td></tr></tbody></table><table class="manual-table native-safety-table"><tbody><tr><td><img alt="mandatory" src="assets/symbol-mandatory.svg"/></td><td>行為を指示する記号</td></tr><tr><td><img alt="keep_dry" src="assets/symbol-keep_dry.svg"/></td><td>製品を濡らすことを禁止する記号</td></tr><tr><td><img alt="prohibited" src="assets/symbol-prohibited.svg"/></td><td>行為を禁止する記号</td></tr></tbody></table></div>

### 警告

<div class="native-safety-columns"><table class="manual-table native-safety-table"><tbody><tr><td><img alt="no_open_flame" src="assets/symbol-no_open_flame.svg"/></td><td><strong>火のそばや炎天下の車内、熱器具</strong><br/><strong>の周辺など高温（45℃以上）にな</strong><br/><strong>る場所で使用したり、放置しない</strong>発熱や発火、破裂する原因になります。</td></tr><tr><td><img alt="prohibited" src="assets/symbol-prohibited.svg"/></td><td><strong>強い衝撃を与えたり、投げつけた</strong><br/><strong>りしない</strong>発熱や発火、破裂する原因になります。</td></tr><tr><td><img alt="keep_dry" src="assets/symbol-keep_dry.svg"/></td><td><strong>水など、液体を入れたり、濡ら</strong><br/><strong>したりしない</strong>発熱や発火の原因になります。</td></tr><tr><td><img alt="no_wet_hands" src="assets/symbol-no_wet_hands.svg"/></td><td><strong>濡れた手で本体や接続するケー</strong><br/><strong>ブルを触らない</strong>火災や感電の原因になります。</td></tr></tbody></table><table class="manual-table native-safety-table"><tbody><tr><td><img alt="prohibited" src="assets/symbol-prohibited.svg"/></td><td><strong>端子部にケーブル以外の金属類を</strong><br/><strong>差し込まない</strong>発熱や発火の原因になります。</td></tr><tr><td><img alt="prohibited" src="assets/symbol-prohibited.svg"/></td><td><strong>雷が鳴りだしたら、電源プラグに</strong><br/><strong>ふれない  (充電をしない)</strong>感電の原因になります。</td></tr><tr><td><img alt="mandatory" src="assets/symbol-mandatory.svg"/></td><td><strong>各接続端子には確実に差し込む</strong>差し込みが不十分だと、発熱したりほこりが付着して火災や感電の原因になります。</td></tr><tr><td><img alt="ground" src="assets/symbol-ground.svg"/></td><td><strong>接地接続は必ず、電源プラグを電</strong><br/><strong>源につなぐ前に行って下さい</strong>また、接地接続を外す場合は、必ず電源プラグを切り離してから行って下さい。</td></tr></tbody></table></div>

### 警告

<table class="manual-table native-safety-table"><tbody><tr><td><img alt="unplug" src="assets/symbol-unplug.svg"/></td><td><strong>万が一、次のような異常が発生したときはすぐに使用をやめる</strong>煙が出ている、異臭がする落としたり、破損したとき 異音がする 内部に水や異物が入ったとき電源コード  (ACアダプター)  が傷んだときこのような異常が発生したまま使用していると、火災や感電の原因になります。すぐにACアダプターをコンセントから抜いてください。また、本製品に接続されている機器もすべて外してください。<br/><strong>万が一発煙や発火したら、大量の水で消火して煙が見えなくなるまで本製品を水浸</strong><br/><strong>しにしてください。</strong>煙が出なくなることを確認してからカスタマーサポートにご連絡ください。お客様による修理は危険ですので絶対におやめください。</td></tr><tr><td><img alt="do_not_dismantle" src="assets/symbol-do_not_dismantle.svg"/></td><td><strong>分解、改造しない</strong>故障、発熱、火災·感電の原因になります。</td></tr><tr><td><img alt="prohibited" src="assets/symbol-prohibited.svg"/></td><td><strong>表示された電源電圧以外で使用しない</strong>故障、発熱、火災·感電の原因になります。また、本製品を使用できるのは日本国内のみです。</td></tr><tr><td><img alt="prohibited" src="assets/symbol-prohibited.svg"/></td><td><strong>付属品と本製品が破損した場合は、ご自身で修理をしない</strong></td></tr></tbody></table>

### 注意

<table class="manual-table native-safety-table"><tbody><tr><td><img alt="prohibited" src="assets/symbol-prohibited.svg"/></td><td><strong>本製品の上に物を載せたり、不安定な場所に置かない</strong>倒れたり、落ちたりしてけがの原因になります。</td></tr><tr><td><img alt="prohibited" src="assets/symbol-prohibited.svg"/></td><td><strong>データサーバや医療機器など、非常時に不具合が起こると人命 / 財産に重大な危険を</strong><br/><strong>及ぼしうる用途でのご使用はお控えください。次のようなような機器では、万が一</strong><br/><strong>使用中に給電ができなくなった場合、人命 / 財産にかかわる被害が想定されます。</strong>· 医療機器や使用上、生命に関わるような機器· 社会的、公共的に重要な機器など· 重要な事業用機器など</td></tr><tr><td><img alt="prohibited" src="assets/symbol-prohibited.svg"/></td><td><strong>心臓にペースメーカーを装着している方は使用しない </strong>ペースメーカーが、本製品の影響を受ける恐れがあります。</td></tr><tr><td><img alt="prohibited" src="assets/symbol-prohibited.svg"/></td><td><strong>格納式ハンドルを使用してJackery ポータブル電源 2000 を移動するときは、積み</strong><br/><strong>重ねたり、上に他の物を置いたりしないでください。落下して怪我をする場合があ</strong><br/><strong>ります。</strong></td></tr></tbody></table>

<span id="native-precautions"></span>

## 使用上のご注意

<p>Jackery ポータブル電源 5000 Plusは、定格出力6000Wです。通常時で消費電力が6000Wまでの機器に給電ができるため、多くの電化製品や端末に対応可能です。ただし、電気モーターを搭載している製品については、例(ヒーター、掃除機、ポンプ、冷蔵庫、電動丸ノコ、エアコン、洗濯機、電子レンジ、ドライヤーなど)起動時に「誘導負荷」が発生し、公称電力の3～7倍の電力が必要となります。定格出力6000Wは、一定の電力で動く機器への出力可能範囲を指しています。</p>

<p>6000Wの出力を超えた場合は、電気回路が自動的に調整され、電力が低減、または保護機能が作動し自動で遮断することがあります。</p>

<p>またAC出力ポート6つ搭載されておりますが、6つ同時にご利用頂く場合、合計して6000W以内であることをご確認の上ご利用ください。</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ご注意</td><td class="manual-callout-body"><p>始動電力が出力上限値(定格出力)を大幅に超える可能性のある製品のご利用や、定格出力を超え給電がストップした製品を繰り返し利用することはポータブル電源のバッテリーが損傷するリスクがありますのでお控えください。</p></td></tr></tbody></table>

<p>・出力上限値を超えた電化製品を利用しない(始動電力が公称電力3倍～7倍の誘導負荷のヒーター、掃除機、冷蔵庫、エアコン、電子レンジ、洗濯機、電動丸、ポンプなどは特にご注意下さい) 。</p>

<p>・本製品は、充電ケーブル、DCケーブル、USBケーブルの差し込みが緩い状態で使用した場合、発火や発煙などの恐れがあります。確実に奥まで差し込んでから、ご使用くださ い。</p>

<p>・本製品は防塵·防水仕様ではありませんので、ほこりや水、海水などがかからないように注意してください。</p>

<p>・ほこりが多い場所や高温多湿の場所での充電および使用、放置をしないでください。</p>

<p>・本製品を不安定な場所に置かないでください。必ず、平坦で安定した場所に置いて使用してください。</p>

<p>・本製品の通風孔は、安全上絶対にふさがないでください。また、本製品の各面から5cm以上スペースを空けてください。</p>

<p>・充電または給電中は本製品が温かくなります(故障ではありません)、周囲には物を置かないでください。</p>

<p>・本製品接続機器のケーブルを差すときは、真っすぐな向きに差してください。</p>

<p>・接続機器のケーブルを抜くときは、必ずプラグ部分を持って抜いてください。ケーブルを引っ張ったり折り曲げると、断線などの原因となります。</p>

<p>・給電する機器の充電制御や充電状況、環境などにより給電できない、または急速充電にならない場合があります。</p>

<p>・充電または給電中はラジオやチューナー、テレビなどに雑音が入る場合があります。雑音が入る場合には、それらの製品から離れた場所でお使いください。</p>

<p>・本体が汚れたらコンセントから電源プラグを抜き、柔らかい布で乾拭きしてください。</p>

<p>汚れがひどいときは、水または薄めた中性洗剤でふきとってください。シンナーやベンジンなどは絶対に使わないでください。</p>

<p>・入出力の電力(W)</p>

<p>接続機器の消費電力が本製品の出力上限値を超えている場合、電源を自動的に遮断します。消費電力が仕様以下であることを確認してから出力ボタンを押してください。</p>

<p>・低/高温警報</p>

<p>本機は-15℃～45℃(5°F～113°F)の温度範囲でお使いの機器に電力供給が可能となり、本機への蓄電は0℃～45℃℃(32°F～113°F)で行えます。</p>

<p>動作温度が上記範囲外にある場合、本製品が温度異常マークが表示され動作しない可能性がございます。</p>

<p>温度異常マークを解除するには、動作温度範囲内の環境に2時間以上置くようにお願い致します。</p>

<p>・容量表示に関しては、あくまで参考値となり、電圧により電力が算出され、表示数値にズレが発生することがあります。</p>

<span id="native-disclaimer"></span>

## 免 責 事 項

<p>・火災、地震、第三者による行為、その他の事故、お客様の故意または過失誤用・誤動作・その他の異常な条件下での使用により生じた損害に関して、当社は一切責任を負いません。</p>

<p>・付属品と本製品が破損した場合は、ご自身で修理を行わないでください。</p>

<p>ご自身で分解・修理したことにより生じた損害に関し、当社は一切責任を負いません。</p>

<p>・保証範囲は利用規約に適用され、記載されていない内容は当社の保証範囲外となります。</p>

<p>・取扱説明書の記載事項が遵守されないことにより生じた不適合について当社は責任を負いかねます。</p>

<p>・本製品の使用、または使用不能から発生する付随的な損害(事業利益損失含む)、当社が関与しない接続機器との組み合わせによる誤動作などから生じた損害に関して、当社は一切の責任を負いません。</p>

<p>・本製品は病院仕様のCPAP（シーバップ）、ECMO（エクモ）、ペースメーカなど、身の安全に関わる医療救急機械の電源としての使用、または、消費電力の大きいな設備、例えば核施設設備、スペースシャトル製造などの使用は推薦されません。上記設備の使用後、火災、機器故障など個人安全を脅かす事故の責任を取りません。</p>

<span id="native-app"></span>

## Jackeryアプリ ユーザーマニュアル

### 1. アプリをダウンロードしてログインするには

<p>Google PlayまたはApp Storeで「Jackery」と検索し、アプリをインストールしてください。その後、登録とログインを行ってください。</p>

<p>または、下の QR コードをスキャンしてアプリをダウンロードし、インストールしてください。</p>

<div class="native-app-download-row"><div class="native-figure native-app-download"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-download" data-source-fragment-sha256="a3179ffeb93e642d99fdb499785db82c7c7502fe8845c0d89ca551d41bfef2b7"><div class="hb-reference-semantic" data-reference-id="app-download.semantic"><img alt="app-download" class="hb-reference-art hb-composite-art" src="assets/app-download.svg"/></div></figure></div><div class="native-figure native-app-qr"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-qr" data-source-fragment-sha256="5eb43642300c375dc4eec76824daccd3cad4d079b319cc9ab3b03081bd37e22a"><div class="hb-reference-semantic" data-reference-id="app-qr.semantic"><img alt="app-qr" class="hb-reference-art hb-composite-art" src="assets/app-qr.svg"/></div></figure></div></div>

### 2. デバイスを追加するには

<p>2.1  APPの右上にあるデバイス追加ボタン<span class="native-inline-plus">+</span>をクリックします；</p>

<p>2.2 デバイスの主電源ボタンを長押しして電源をいれると、ディスプレー画面にWi-FiとBluetoothのアイコンが点滅し、デバイスがネットワーク設定モードに入ったことを示します。アイコン点滅中ボタンをクリックし、アプリが近くのデバイスに接続し、Bluetoothのアクセス許可を開くことを許可します；</p>

<div class="native-figure native-app-add"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-add" data-source-fragment-sha256="c135a7ab979be6ae97b969b4ee888942b86ae61e37b446aaf8da4fe4deb80b95" data-web-base-art-ref="app-add" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="app-add.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/app-add.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:18.4623%;--hb-y:90.3958%;--hb-width:6.2217%;--hb-height:5.9119%"><span><span style="font-size:1.000000em">2.1</span></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:74.2009%;--hb-y:90.3958%;--hb-width:6.2217%;--hb-height:5.9119%"><span><span style="font-size:1.000000em">2.2</span></span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">備考</td><td class="manual-callout-body"><p>電源を入れた後、アプリが2時間以内接続されていないと、デバイスは自動的にWi-FiとBluetoothをオフにします。再度Wi-FiとBluetoothをオンにするには、「USBボタン」と「ACボタン」を同時長押しする必要があります。</p></td></tr></tbody></table>

<div class="native-figure native-app-control native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-control" data-source-fragment-sha256="59701e8c035828b742a3c39561faa4a087d1c864935930aee0ab4a0fa9811071" data-web-base-art-ref="app-control" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="app-control.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/app-control.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:18.7115%;--hb-y:8.1148%;--hb-width:14.9159%;--hb-height:13.1707%"><span><span style="font-size:0.857143em">DC </span><span style="font-size:1.000000em">ボタン</span></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:68.5941%;--hb-y:9.2467%;--hb-width:20.7441%;--hb-height:13.1707%"><span><span style="font-size:0.857143em">POWER </span><span style="font-size:1.000000em">ボタン</span></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:83.4094%;--hb-y:52.2988%;--hb-width:16.0172%;--hb-height:13.1707%"><span><span style="font-size:0.857143em">USB </span><span style="font-size:1.000000em">ボタン</span></span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:0.7189%;--hb-y:63.2215%;--hb-width:14.6623%;--hb-height:13.1707%"><span><span style="font-size:0.857143em">AC </span><span style="font-size:1.000000em">ボタン</span></span></span></div></div></figure></div>

<p>2.3 検出されたデバイスアイコンをクリックすると、アプリは自動的にBluetoothでデバイスを接続します。</p>

<p>備考：バインド処理中に「デバイスがバインドされました」と表示された場合は、以下の2つの方法で接続できます：</p>

<p>デバイス所有者は、アプリを通じてこのデバイスを他のユーザーと共有します。</p>

<p>「POWERボタン」と「USBボタン」を3秒間長押ししてデバイスをリセットし、再度バインドしてくだい。</p>

<p>2.4 デバイスが正常に接続されると、デバイスが接続するWi-Fiの名前とパスワードを入力する必要があり、デバイスは自動的にWi-Fiネットワークに接続します。</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">備考</td><td class="manual-callout-body"><p>2.4GHz帯のWi-Fiネットワークを選択してください。デバイスは、5GHz帯のWi-Fiネットワークには対応していません。</p></td></tr></tbody></table>

<p>2.5 デバイスのホーム画面でデバイスが正常に追加されると、デバイスのWi-Fi アイコンは常にオンになります。</p>

<div class="native-figure native-app-results"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-results" data-source-fragment-sha256="8e7d1f11063b852065b583a06247fd5236b1ea68699bd1e72db1cd3762ed7462" data-web-base-art-ref="app-results" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="app-results.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/app-results.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:11.6337%;--hb-y:90.5438%;--hb-width:3.5129%;--hb-height:5.1366%"><span><span style="font-size:1.000000em">2.3</span></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:48.4848%;--hb-y:90.5438%;--hb-width:3.5129%;--hb-height:5.1366%"><span><span style="font-size:1.000000em">2.4</span></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:84.9746%;--hb-y:90.5438%;--hb-width:3.5129%;--hb-height:5.1366%"><span><span style="font-size:1.000000em">2.5</span></span></span></div></div></figure></div>

<p>上記のスクリーンショットはご参考まで。</p>

### 3. デバイスのバインドを解除するには

<p>デバイスのメインインターフェースの右上隅にある「設定」ボタンをクリックして設定ページに入り、ページの下部にある「バインド解除」ボタンをクリックしてデバイスのバインドを解除します。</p>

### 4. ご確認

<p>4.1 Wi-FiとBluetoothをオンにするには（ディスプレーにWi-FiとBluetoothのアイコンが点灯）：</p>

<p>デバイスがオンになれば自動的にオンになり、ディスプレーにWi-FiとBluetoothのアイコンが点灯します；</p>

<p>上記アイコンが点灯しない場合、ディスプレーにWi-FiとBluetoothのアイコンが点灯するまで、USB出力ボタンとAC出力ボタンを同時長押しします。</p>

<p>4.2 Wi-FiとBluetoothをオフにするには（ディスプレーにWi-FiとBluetoothのアイコンが消える）：</p>

<p>ディスプレーにWi-FiとBluetoothのアイコンが消えるまで、USB出力ボタンとAC出力ボタンを同時長押しします；</p>

<p>2 時間以内にデバイスが接続されない場合、Wi-FiとBluetooth は自動的にオフになります。</p>

<p>4.3 Wi-FiとBluetoothをリセットするには：</p>

<p>主電源ボタンとUSBボタンを同時に3秒間押すと、Wi-FiとBluetoothが初期化され、システムが再起動します。接続されているアプリアカウントはバインド解除されます。</p>

<span id="native-warranty"></span>

## 保証サービス

<p>本書は、株式会社 Jackery Japan（以下、当社）製品の交換・修理にかかる保証サービスの内容を説明するものです。</p>

<p>1. 当社は、当社が運営するJackery Japan 公式オンラインストア、当社もしくは正規販売代理店が販売元として販売した当社のポータブル電源・ソーラーパネル、その他の付属製品について保証期間中に、当社が定める条件に従って保証サービスを提供しております。</p>

<p>2. 当社は、保証期間中に、当社が定める「保証条件」に合致した場合、Jackery 製品を交換・無償修理するものとします。</p>

<p>保証期間内に当社に有効な請求が行われた場合、当社は、同じJackery 製品を交換もしくは価値の等しい製品と交換いたします。無償修理については、当社ポータブル電源の新品のご購入日から30 日以上5 年間以内の製品を対象といたします。</p>

<p>3. 取扱説明書、本体貼付ラベルなどの注意書に従った使用状態で、保証期間内に製品が故障した場合のみ無償交換· 無償修理をさせていただきます。</p>

<p>4. 当社は、日本国内に居住または滞在中のお客様のみを対象として、日本国内においてのみ本サービスを提供いたします。</p>

<p>5. 保証期間内でも次の場合には保証対象外となります。</p>

<p>(1) 保証期間中に発生した故障について、保証期間終了後に請求された場合</p>

<p>(2) 使用上の誤り( 取扱説明書、本体貼付ラベル等の注意書きに従った正常な使用をしなかった場合を含む) による故障· 損傷</p>

<p>(3) 他の機器から受けた障害または不当な修理、改造による故障· 損傷</p>

<p>(4) お買上げ後の移設、輸送、落下などによる故障· 損傷</p>

<p>(5) 火災や地震、風水害、落雷その他の天災地変、公害、塩害、異常電圧などによる故障· 損傷</p>

<p>(6) 業務用など一般家庭用以外での使用による故障損傷</p>

<p>(7) 消耗· 摩耗した部品の交換、汚損した部分の交換</p>

<p>6. 在庫切れや販売終了など当社都合で新品製品が調達できなかった場合返金にて対応することがあります。</p>

<p>7. 本書に基づく交換・修理製品については、最初のご購入時の保証期間、または交換日から90 日間のどちらか長い期間で保証されます。</p>

<p>8. お客様の修理依頼品の状態、故障部分あるいは当社の事情により、修理による対応が不可能、困難または合理的でないと判断した場合、かつ保証期間内と確認できた場合に、当社が選定する同等程度の機能・性能を有する製品（修理依頼品と類似の製品・異機種を含みます）と修理依頼品との交換をさせていただく場合がございます。</p>

<p>9. 当社は、保証期間が過ぎた製品及び保証対象外の製品について、修理すれば使用できる場合は、ご希望により有償修理にて承ります。</p>

<p>10. 当社の製品または製品のご使用から起因して生じた障害・損傷により、直接または間接的に発生した製品以外への損失、その他の金銭的損害につきまして、弊社はその一切の責任は負わないものとします。</p>

<p>11. 本書は再発行いたしませんので紛失しないよう大切に保管してください。</p>

<p>※保証期間はお買い上げ日より5 年間となります。</p>

<p>※本書は、本書記載内容（上記記載）で無償製品交換・無償修理を行うことをお約束するものです。故障による保証サービスを受ける際は、当社もしくは当社製品正規取扱店が運営するショップでの購入が証明できるもの（インターネットでの購入は注文</p>

<p>番号、それ以外はレシートや領収書など）をお手元にご用意の上、JackeryJapan カスタマーサービス、もしくは販売店へお問い合わせください。</p>

<p>※故障による保証サービスを受ける際は、当社もしくは当社製品正規取扱店が運営するショップでの購入が証明できるもの（インターネットでの購入は注文番号、それ以外はレシートや領収書など）が必須となりますのでご注意ください。当社製品正規取</p>

<p>扱店につきましては、当社公式HP をご確認ください。</p>

<p>※本書によって保証責任者、及びそれ以外の事業者に対するお客様の法律上の権利を制限するものではありません。</p>

<p>※保証内容は都合により予告なく変更する場合がございますのでご了承ください。</p>

<div class="native-service"><div class="native-figure native-service-logo"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="service-logo" data-source-fragment-sha256="65f796594cc68c86dea0fcfc0e2810ec79cf1ee2d28d94270162f6e3f315a8e8"><div class="hb-reference-semantic" data-reference-id="service-logo.semantic"><img alt="service-logo" class="hb-reference-art hb-composite-art" src="assets/service-logo.svg"/></div></figure></div><div><p>公式サイト</p><p>http://www.jackery.jp</p><p>カスタマーサービス</p><p>jackery.jp@jackery.com</p></div></div>
