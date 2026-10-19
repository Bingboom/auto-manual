<style>
/* Source-local dimensions only; shared component geometry and tokens remain authoritative. */
#furo-main-content .hb-reference-figure[data-reference-id="cover-unit"] { max-width: 12rem; margin-inline: auto; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-control"] { max-width: 10rem; margin-inline: auto; }
#furo-main-content .hb-reference-figure[data-reference-id="stand-installed"],
#furo-main-content .hb-reference-figure[data-reference-id="wood-installed"] { max-width: 13rem; margin-inline: auto; }
#furo-main-content .hb-reference-figure[data-reference-id="wood-installed"] .hb-reference-live-label { font-size: .65rem; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map"] .hb-reference-live-label { font-size: .8rem; }
#furo-main-content .hb-callout-copy img { width: 1em; height: auto; vertical-align: middle; }

/* Preserve native table semantics while making this Japanese source readable without panning. */
@media (max-width: 760px) {
 #furo-main-content .hb-lcd-table-composition[aria-label="液晶画面"] table,
 #furo-main-content .hb-troubleshooting-composition[aria-label="エラーコード / 対処方法"] table { min-width: 0 !important; width: 100% !important; }
 #furo-main-content .hb-lcd-table-composition[aria-label="液晶画面"] .hb-lcd-col-number { width: 8%; }
 #furo-main-content .hb-lcd-table-composition[aria-label="液晶画面"] .hb-lcd-col-icon { width: 14%; }
 #furo-main-content .hb-lcd-table-composition[aria-label="液晶画面"] .hb-lcd-col-name { width: 28%; }
 #furo-main-content .hb-lcd-table-composition[aria-label="液晶画面"] .hb-lcd-col-description { width: 50%; }
 #furo-main-content .hb-troubleshooting-composition[aria-label="エラーコード / 対処方法"] .hb-troubleshooting-col-code { width: 22%; }
 #furo-main-content .hb-troubleshooting-composition[aria-label="エラーコード / 対処方法"] .hb-troubleshooting-col-measures { width: 78%; }
}

</style>

<span id="preface"></span>

## Jackery Battery Pack 取扱説明書

<p>型番：JBP-1000B-WH</p>

<p>国内専用/For use only in Japan</p>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="cover-unit" data-source-fragment-sha256="f13eac3367dc4c3b03fd59a642e10324f3aad0548ad7a8354b92ab67a00db370"><div class="hb-reference-semantic" data-reference-id="cover-unit.semantic"><img alt="cover-unit" class="hb-reference-art hb-composite-art" src="assets/cover-unit.png"/></div></figure>

<p>写真はイメージです。実際の商品とは異なる場合があります。</p>

<p>カスタマーサポート: jackery.jp@jackery.com</p>

<p>お買い上げありがとうございます。</p>

<p>ご使用の前にこの「取扱説明書」をよくお読みのうえ、正しくお使いください。特に「安全上のご注意」は、必ずお読みいただき、安全にお使いください。お読みになったあとは、すぐに取り出せる場所に大切に保管してください。本製品の取扱説明書は随時更新されますので、最新の取扱説明書は公式サイトでご確認ください。</p>

<span id="safety"></span>

## 使用上のご注意

<p>本製品を使用する際、以下の注意事項を守ってください。</p>

<ul><li><p>本製品を使用する前に取扱説明書をよくお読みください。</p></li><li><p>危険防止のため、お子様の近くで本製品を使用する時は、お子様から目を離さないようにしてください。</p></li><li><p>メーカーが保証していない推奨外の付属品を使用すると、感電の恐れがあります。</p></li><li><p>製品を使用しない場合は、プラグを抜いてください。</p></li><li><p>火災、爆発、感電などの予測できない危険が発生する恐れがありますので、本製品を解体しないでください。</p></li><li><p>感電の危険があるため、破損したコードやプラグ、またはケーブルを使用しないでください。</p></li><li><p>製品の充電は風通しの良い場所で行い、風通しの悪い場所での充電はおやめください。</p></li><li><p>雨に濡れないよう、風通しのよい乾燥した場所に保管してください。本製品は濡れると感電の危険があります。</p></li><li><p>火災、爆発などの事故の原因となるため、本製品を火気に近づけないでください。</p></li><li><p>高温の下 (直射日光や猛暑の車内) で使用したり放置しないでください。内蔵のバッテリーが過熱して発火したり、機能しなくなったり、寿命が短くなる可能性があります。</p></li><li><p>本製品を初めてご使用になる時は、十分に充電してからご使用ください。本製品を電池が切れた状態で長期間 (3 ヶ月～6 ヶ月) 放置すると、性能が低下し、過放電により充電ができなくなる場合があります。</p></li></ul>

<span id="symbols"></span>

## 絵表示について

<p>製品を安全に正しくお使いいただき、お客様や他の方々への危害や財産への損害を未然に防止するための表示です。内容をよく理解してから本文をお読みください。</p>

<figure aria-label="絵表示について" class="hb-symbol-signal-composition" data-component-id="HB-TABLE-SYMBOL-SIGNAL"><table class="hb-symbol-signal-table"><colgroup><col class="hb-symbol-signal-col-label"/><col class="hb-symbol-signal-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-signal-label-heading" scope="col">表示</th><th class="hb-symbol-signal-meaning-heading" scope="col">意味</th></tr></thead><tbody><tr><td class="hb-symbol-signal-label-cell"><span aria-label="警告" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">警告</span></span></td><td class="hb-symbol-signal-meaning-cell">この表示を無視して、誤った取り扱いをすると、人が死亡または重傷を負う可能性が想定される内容を示しています。</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="ご注意" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">ご注意</span></span></td><td class="hb-symbol-signal-meaning-cell">この表示を無視して、誤った取り扱いをすると、人が傷害を負う可能性が想定される内容または物的損害の発生が想定される内容を示しています。</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="説明" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">説明</span></span></td><td class="hb-symbol-signal-meaning-cell">この表示を無視して誤った取り扱いをすると、機器の損傷、データの消失、性能の低下、または予期しない動作が発生する可能性があることを示しています。</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="ヒント" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">ヒント</span></span></td><td class="hb-symbol-signal-meaning-cell">文章内の重要な情報や操作のヒントを補足する内容を示しています。</td></tr></tbody></table></figure>

### 絵表示の説明

<figure aria-label="絵表示の説明" class="hb-symbol-pair-composition" data-component-id="HB-TABLE-SYMBOL-ICON"><div class="hb-symbol-pair-grid"><div class="hb-symbol-panel hb-symbol-panel-1"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">記号</th><th class="hb-symbol-meaning-heading" scope="col">説明</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="製品を分解、改造を禁止する記号" class="hb-symbol-art" src="assets/symbol_do_not_dismantle.svg"/></td><td class="hb-symbol-meaning">製品を分解、改造を禁止する記号</td></tr><tr><td class="hb-symbol-icon"><img alt="潜在的な危険やリスクについて注意喚起するために、必ずお読みください。" class="hb-symbol-art" src="assets/symbol_warning_triangle.svg"/></td><td class="hb-symbol-meaning">潜在的な危険やリスクについて注意喚起するために、必ずお読みください。</td></tr><tr><td class="hb-symbol-icon"><img alt="操作の前に取扱説明書をお読みください。" class="hb-symbol-art" src="assets/symbol_read_manual.svg"/></td><td class="hb-symbol-meaning">操作の前に取扱説明書をお読みください。</td></tr><tr><td class="hb-symbol-icon"><img alt="本製品を火気の近くに置かないでください。" class="hb-symbol-art" src="assets/symbol_no_open_flame.svg"/></td><td class="hb-symbol-meaning">本製品を火気の近くに置かないでください。</td></tr><tr><td class="hb-symbol-icon"><img alt="小さなお子様の手の届かない場所に保管してください。" class="hb-symbol-art" src="assets/symbol_keep_away_from_children.svg"/></td><td class="hb-symbol-meaning">小さなお子様の手の届かない場所に保管してください。</td></tr></tbody></table></div><div class="hb-symbol-panel hb-symbol-panel-2"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">記号</th><th class="hb-symbol-meaning-heading" scope="col">説明</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="充電式電池のリサイクルについて本機はリサイクル可能な充電池を内蔵しています。この商品を廃棄する場合は、当社のカスタマーサポートにご連絡ください。充電池の取りはずしはお客様自身では行わないでください。" class="hb-symbol-art" src="assets/native-li_ion.svg"/></td><td class="hb-symbol-meaning">充電式電池のリサイクルについて本機はリサイクル可能な充電池を内蔵しています。この商品を廃棄する場合は、当社のカスタマーサポートにご連絡ください。充電池の取りはずしはお客様自身では行わないでください。</td></tr><tr><td class="hb-symbol-icon"><img alt="このシンボルは、本製品を一般家庭ごみとして廃棄せず、リサイクルのために指定の回収施設に持ち込む必要があることを示しています。適切な廃棄およびリサイクルは、環境保護に役立ちます。本製品の廃棄やリサイクルについての詳細は、お住まいの自治体、廃棄物処理業者、または販売店にお問い合わせください。" class="hb-symbol-art" src="assets/symbol_weee.svg"/></td><td class="hb-symbol-meaning">このシンボルは、本製品を一般家庭ごみとして廃棄せず、リサイクルのために指定の回収施設に持ち込む必要があることを示しています。適切な廃棄およびリサイクルは、環境保護に役立ちます。本製品の廃棄やリサイクルについての詳細は、お住まいの自治体、廃棄物処理業者、または販売店にお問い合わせください。</td></tr></tbody></table></div></div></figure>

<span id="in_the_box"></span>

## 同梱品

<figure aria-label="同梱品" class="hb-inbox-composition" data-card-count="4" data-component-id="HB-SPECIAL-INBOX" data-inbox-variant="responsive-card-grid"><ol class="hb-inbox-grid"><li class="hb-inbox-card" data-item-number="1"><img alt="本体" class="hb-inbox-art" src="assets/inbox-unit.png"/><div class="hb-inbox-label"><p>本体</p></div></li><li class="hb-inbox-card" data-item-number="2"><img alt="拡張ケーブル" class="hb-inbox-art" src="assets/inbox-cable.png"/><div class="hb-inbox-label"><p>拡張ケーブル</p></div></li><li class="hb-inbox-card" data-item-number="3"><img alt="取扱説明書" class="hb-inbox-art" src="assets/inbox-manual.png"/><div class="hb-inbox-label"><p>取扱説明書</p></div></li><li class="hb-inbox-card" data-item-number="4"><img alt="スタンド" class="hb-inbox-art" src="assets/inbox-stand.png"/><div class="hb-inbox-label"><p>スタンド</p></div></li></ol></figure>

<p>※  付属品を故障、紛失等してしまった場合はカスタマーサポートまでご連絡ください。※  本拡張ケーブルは、同梱されている本体以外には使用しないでください。</p>

<p>本機の仕様および外観は、改善のため予告なく変更することがあります。</p>

<span id="product_overview"></span>

## 各部の名称

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview" data-source-fragment-sha256="ace4c972fafabcb8c792039c4c0b4e2b55c307e1372b4f835d646135cad7c577" data-web-base-art-ref="overview" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="overview.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/overview.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:71.9603%;--hb-y:0.13%;--hb-width:20.8667%;--hb-height:15.9963%">DC 拡張ポートDC入力: 40V-57.6V⎓24A DC出力: 40V-57.6V⎓50A</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:75.9853%;--hb-y:34.8155%;--hb-width:16.4185%;--hb-height:9.9323%">主電源ボタン</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:71.0697%;--hb-y:50.4906%;--hb-width:21.3342%;--hb-height:9.9323%">LCD ディスプレイ</span></div></div></figure>

<span id="lcd_display"></span>

## 液晶画面

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="lcd-map" data-source-fragment-sha256="502527165ee07efebabd5b0f840480c1559395ad089931b35e6db4a096a705b7" data-web-base-art-ref="lcd-map" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="lcd-map.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/lcd-map.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:22.0703%;--hb-y:3.0483%;--hb-width:12%;--hb-height:5%">2</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:38.7021%;--hb-y:3.0483%;--hb-width:12%;--hb-height:5%">3</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:89.0388%;--hb-y:3.0483%;--hb-width:10.9612%;--hb-height:5%">3</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:7.892%;--hb-y:3.4142%;--hb-width:12%;--hb-height:5%">1</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:58.229%;--hb-y:3.4142%;--hb-width:12%;--hb-height:5%">1</span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:38.7471%;--hb-y:92.6011%;--hb-width:12%;--hb-height:5%">7</span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:2.243%;--hb-y:93.4316%;--hb-width:12%;--hb-height:5%">4</span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:9.9575%;--hb-y:93.4316%;--hb-width:12%;--hb-height:5%">5</span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:23.2877%;--hb-y:93.4316%;--hb-width:12%;--hb-height:5%">6</span></div></div></figure>

<figure aria-label="液晶画面" class="hb-lcd-table-composition" data-component-id="HB-TABLE-LCD-ICON" tabindex="0"><table class="hb-lcd-icon-table"><colgroup><col class="hb-lcd-col-number"/><col class="hb-lcd-col-icon"/><col class="hb-lcd-col-name"/><col class="hb-lcd-col-description"/></colgroup><tbody><tr><td class="hb-lcd-number" rowspan="2">1</td><td class="hb-lcd-icon"><img alt="入力電力表示" class="hb-lcd-icon-art" src="assets/10_Input_Power_BiBvbNteAoNsHqxoMICc11cjnHc.png"/></td><td class="hb-lcd-name">入力電力表示</td><td class="hb-lcd-description">入力電力と残り充電時間を交互に表示します。</td></tr><tr><td class="hb-lcd-icon"><img alt="充電残り時間" class="hb-lcd-icon-art" src="assets/11_Remaining_Charge_Time_VeBobGZMDoYpBuxLRcFcti9cnlc.png"/></td><td class="hb-lcd-name">充電残り時間</td><td class="hb-lcd-description">入力電力と残り充電時間を交互に表示します。</td></tr><tr><td class="hb-lcd-number">2</td><td class="hb-lcd-icon"><img alt="バッテリー残量(%)" class="hb-lcd-icon-art" src="assets/18_Remaining_Battery_Percentage_F7gbbsgPKo4mdkx4JqccMfQRngc.png"/></td><td class="hb-lcd-name">バッテリー残量(%)</td><td class="hb-lcd-description">バッテリー残量を表示します。</td></tr><tr><td class="hb-lcd-number" rowspan="2">3</td><td class="hb-lcd-icon"><img alt="消費電力" class="hb-lcd-icon-art" src="assets/26_Output_Power_PviebR618oofvKxcKVRcHLlInqd.png"/></td><td class="hb-lcd-name">消費電力</td><td class="hb-lcd-description">出力電力と残り放電時間を交互に表示します。</td></tr><tr><td class="hb-lcd-icon"><img alt="バッテリー使用可能時間" class="hb-lcd-icon-art" src="assets/27_Remaining_Discharge_Time_QvCQbFmEhoQR3kxgWt4c6H9zn0b.png"/></td><td class="hb-lcd-name">バッテリー使用可能時間</td><td class="hb-lcd-description">出力電力と残り放電時間を交互に表示します。</td></tr><tr><td class="hb-lcd-number">4</td><td class="hb-lcd-icon"><img alt="充電インジケーター" class="hb-lcd-icon-art" src="assets/lcd-charge.svg"/></td><td class="hb-lcd-name">充電インジケーター</td><td class="hb-lcd-description">オン: Jackery SlimPower H1は充電状態です。
オフ: Jackery SlimPower H1は充電状態ではありません。</td></tr><tr><td class="hb-lcd-number">5</td><td class="hb-lcd-icon"><img alt="バッテリーレベルパーセントタグ" class="hb-lcd-icon-art" src="assets/lcd-ring.svg"/></td><td class="hb-lcd-name">バッテリーレベルパーセントタグ</td><td class="hb-lcd-description">オレンジの円は残バッテリーレベルを示しています。</td></tr><tr><td class="hb-lcd-number">6</td><td class="hb-lcd-icon"><img alt="DC 入力" class="hb-lcd-icon-art" src="assets/lcd-dc.svg"/></td><td class="hb-lcd-name">DC 入力</td><td class="hb-lcd-description">オン：Jackery DC Input Moduleが接続されています。
オフ：Jackery DC Input Moduleが切断されています。</td></tr><tr><td class="hb-lcd-number">7</td><td class="hb-lcd-icon"><img alt="エラーコード" class="hb-lcd-icon-art" src="assets/lcd-error.svg"/></td><td class="hb-lcd-name">エラーコード</td><td class="hb-lcd-description">製品エラーが発生しました。詳細については、トラブルシューティングのセクションを参照してください。</td></tr></tbody></table></figure>

<span id="operations"></span>

## 製品の使用方法について

### オン/オフ

<figure class="hb-operation-figure hb-operation-layout-status-right" data-component-id="HB-SPECIAL-OPERATION" data-operation-id="power" data-source-fragment-sha256="7c50ab040d12f3deedaabd2e10d02b0f73ed5efa9eeab0dfbd0824e4ff2737a0" data-web-replace-key="operation.power"><div class="hb-operation-stage"><img alt="オン/オフ" class="hb-operation-art" src="assets/power.png"/><div class="line-block hb-operation-steps" data-callout-id="operation.power.steps" style="--hb-x:77%;--hb-y:5%;--hb-width:20%;--hb-height:40%"><div class="hb-operation-step" data-callout-id="operation.power.off" data-step-id="off"><div class="line" data-step-id="off" data-step-part="label"><strong>オフ</strong></div><div class="line" data-step-id="off" data-step-part="instruction">1回押す</div></div><div class="hb-operation-step" data-callout-id="operation.power.on" data-step-id="on"><div class="line" data-step-id="on" data-step-part="label"><strong>オン</strong></div><div class="line" data-step-id="on" data-step-part="instruction">3秒</div></div></div><div class="hb-operation-supporting-copy" data-callout-id="operation.power.supporting-copy"><div class="line">3s</div></div></div></figure>

### LCDスクリーン

<figure aria-label="LCDスクリーン" class="hb-lcd-mode-composition hb-lcd-mode-portrait" data-component-id="HB-TABLE-LCD-MODE"><div class="hb-lcd-mode-art-panel"><img alt="LCDスクリーン" class="hb-lcd-mode-art" src="assets/lcd-control.png"/></div><div class="hb-lcd-mode-table-panel"><table class="hb-lcd-mode-table"><colgroup><col class="hb-lcd-mode-col-state"/><col class="hb-lcd-mode-col-action"/><col class="hb-lcd-mode-col-copy"/></colgroup><tbody><tr><td class="hb-lcd-mode-state" rowspan="3">一時点灯</td><td class="hb-lcd-mode-action">オンにする</td><td class="hb-lcd-mode-copy">主電源ボタンを押すか、充電入力がある場合。</td></tr><tr><td class="hb-lcd-mode-action">オフにする</td><td class="hb-lcd-mode-copy">主電源ボタンを押します。</td></tr><tr><td class="hb-lcd-mode-action">自動オフ</td><td class="hb-lcd-mode-copy">2分後にLCDは自動的に消灯し、スリープモードになります。</td></tr><tr><td class="hb-lcd-mode-state" rowspan="3">常時点灯</td><td class="hb-lcd-mode-action">オンにする</td><td class="hb-lcd-mode-copy">デバイスが起動している状態で主電源ボタンを2回押します。</td></tr><tr><td class="hb-lcd-mode-action">オフにする</td><td class="hb-lcd-mode-copy">主電源ボタンを押します。</td></tr><tr><td class="hb-lcd-mode-action">自動オフ</td><td class="hb-lcd-mode-copy">常時点灯ディスプレイモードは、2時間操作がないと自動的に消灯します。</td></tr></tbody></table></div></figure>

<span id="placement"></span>

## Jackery Battery Pack と 本体の設置方法

### 並列配置

<p>Jackery Battery Pack と Jackery SlimPower H1 本体を横並びに配置します。</p>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="parallel" data-source-fragment-sha256="22a90c1b2e23fdadf5129d9b482ebbec2887e0dd0100f024182e30afaf6c2dee"><div class="hb-reference-semantic" data-reference-id="parallel.semantic"><img alt="parallel" class="hb-reference-art hb-composite-art" src="assets/parallel.png"/></div></figure>

### 積層配置

<p>Jackery Battery Pack と Jackery SlimPower H1 本体を上下に積み重ねて配置します。</p>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="stacked" data-source-fragment-sha256="25c918891aae75ad49507ea5111f8e5e59838fc4bc2a35c64493bf4bbc54393d"><div class="hb-reference-semantic" data-reference-id="stacked.semantic"><img alt="stacked" class="hb-reference-art hb-composite-art" src="assets/stacked.png"/></div></figure>

### ブラケット取付の場合

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ご注意</td><td class="manual-callout-body"><p>· 石膏ボード、断熱壁、中空レンガなどの耐荷重構造ではない場所には設置しないでください。製品が落下するおそれがあります。</p><p>· 壁内の配線（電線・水道管・ガス管など）を避けて設置してください。</p></td></tr></tbody></table>

<span id="stand"></span>

## 縦置

<p>スタンドに取り付けられた Jackery Battery Packは、地面に設置することができます。以下の設置手順に従ってください。</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="stand-preparation" data-source-fragment-sha256="e8ab40e650ed27fbf529bd2dfd5c43802f95ae42b7ede1c03fd2b4fe8040daed" data-web-base-art-ref="stand-preparation" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="stand-preparation.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/stand-preparation.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:6.1106%;--hb-y:1.873%;--hb-width:25.7907%;--hb-height:22.4629%">設置前の準備。</span></div></div></figure>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="stand-installed" data-source-fragment-sha256="8c7a4e65950918894d8f0eead715264b5963495cb8a2961659ba31726f172af8"><div class="hb-reference-semantic" data-reference-id="stand-installed.semantic"><img alt="stand-installed" class="hb-reference-art hb-composite-art" src="assets/stand-installed.png"/></div></figure>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="stand-1" data-source-fragment-sha256="fff410e32d344d5552c745b4688659db05fe19dcb832a4120c2d8587bd39dc19" data-web-base-art-ref="stand-1" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="stand-1.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/stand-1.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:2.7927%;--hb-y:3.4325%;--hb-width:44.3133%;--hb-height:19.7941%">1. 製品底面のネジを2本外してください。</span></div></div></figure>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="stand-2" data-source-fragment-sha256="a7d7557b5fb68f1a58e894be09715796828e3d5b9de9a9d3b7fd78657150fbec" data-web-base-art-ref="stand-2" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="stand-2.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/stand-2.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:3.1265%;--hb-y:0.874%;--hb-width:71.9822%;--hb-height:16.66%">2. 製品底面の取り付け穴を縦置きスタンドの穴と合わせてください。</span></div></div></figure>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="stand-3" data-source-fragment-sha256="1c4bda8512ac8cd4a176e321e37a41aa9efd0fe716d5d4d71419590a692b3ffe" data-web-base-art-ref="stand-3" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="stand-3.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/stand-3.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:3.1486%;--hb-y:3.9908%;--hb-width:27.0422%;--hb-height:19.2231%">3.ネジを締め付けます。</span></div></div></figure>

<span id="wall_wood"></span>

## 木製の壁の場合。

<p>Jackery Wall-Mounted Bracket（別売）を使用すると、Jackery Battery Pack を壁に設置することができます。以下の設置手順に従ってください。</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="wood-preparation" data-source-fragment-sha256="226518b8699ca30f96259e2b3061bdae2ca5bc8051fb7f42b22d1b57341431ee" data-web-base-art-ref="wood-preparation" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="wood-preparation.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/wood-preparation.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:5.9107%;--hb-y:1.7918%;--hb-width:25.5599%;--hb-height:14.7651%">設置前の準備。</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:66.0267%;--hb-y:22.0155%;--hb-width:12%;--hb-height:18.9572%">別売</span></div></div></figure>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="wood-installed" data-source-fragment-sha256="36e38fde10beb3d60eb680adf57932904292b81a4201dafa658bcc93b4a944c4" data-web-base-art-ref="wood-installed" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="wood-installed.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/wood-installed.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:6.4734%;--hb-y:0%;--hb-width:89.8447%;--hb-height:8.3048%">壁の中にある細い柱(間柱)</span></div></div></figure>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="wood-1-2" data-source-fragment-sha256="2362c95656e0f92fcad00dbc40c1b84e0cbd1b0bc568db64038d06f660a2eb06" data-web-base-art-ref="wood-1-2" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="wood-1-2.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/wood-1-2.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:3.45%;--hb-y:4.5171%;--hb-width:70.9248%;--hb-height:13.7025%">1. Jackery SlimPower H1本体を、取扱説明書に従って設置します。</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:3.45%;--hb-y:13.4266%;--hb-width:42.3786%;--hb-height:13.7025%">2. 製品底面のネジ2本を取り外します。</span></div></div></figure>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="wood-3" data-source-fragment-sha256="9fa35ef223d87b97a05eb3bbc7adc73eb85ede832ef8089a346b8d29a48b001b" data-web-base-art-ref="wood-3" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="wood-3.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/wood-3.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:39.0788%;--hb-y:3.3627%;--hb-width:56.9703%;--hb-height:11.9558%">3. 上下のマウントブラケットを製品背面にしっかり取り付けます。</span></div></div></figure>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="wood-4" data-source-fragment-sha256="a9772aff436a99e4f755e1f4249d6c229284873e2e8f6a1cd963918c881ba912" data-web-base-art-ref="wood-4" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="wood-4.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/wood-4.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:10.1246%;--hb-y:3.9281%;--hb-width:89.087%;--hb-height:17.7385%">4. 壁の内側にある間柱を探すには、下地探しセンサーを使用してください。</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:68.4438%;--hb-y:29.1267%;--hb-width:15.6812%;--hb-height:12.4483%">間柱</span></div></div></figure>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="wood-5" data-source-fragment-sha256="c8b3f4ace103e8e874533852db212370ccba31109897d9c03a71a063ac8e1a45" data-web-base-art-ref="wood-5" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="wood-5.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/wood-5.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:3.4118%;--hb-y:2.3691%;--hb-width:95.9511%;--hb-height:28.6101%">5. Jackery SlimPower H1本体のボルト位置から水平方向に455mm離れた場所を測定し、壁の間柱上に取付ポイントをマーキングします。*  455 mmは推奨距離であり、実際の距離は壁の状態に依存します。</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:61.1798%;--hb-y:24.4923%;--hb-width:12%;--hb-height:12.8154%">間柱</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:36.1264%;--hb-y:25.0576%;--hb-width:12%;--hb-height:12.8154%">間柱</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:48.464%;--hb-y:50.8651%;--hb-width:12%;--hb-height:12.8154%">455mm</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:6.1753%;--hb-y:75.9037%;--hb-width:18.4573%;--hb-height:5%">Jackery SlimPower H1</span></div></div></figure>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="wood-6" data-source-fragment-sha256="06ebffb8a51b39ec7285d3adccb3a57d2f2fdfd3e6f440371f64864aae1ab79c" data-web-base-art-ref="wood-6" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="wood-6.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/wood-6.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:3.3692%;--hb-y:3.5188%;--hb-width:96.6308%;--hb-height:15.1225%">6. 取付ポイントに木ねじを壁にねじ込み、ねじと壁の間に2～4mmの隙間を残してください。</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:59.7596%;--hb-y:16.4319%;--hb-width:12%;--hb-height:15.1225%">間柱</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:77.7087%;--hb-y:38.8482%;--hb-width:12%;--hb-height:5.4463%">2~4mm</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:2.7455%;--hb-y:71.641%;--hb-width:18.6561%;--hb-height:5%">Jackery SlimPower H1</span></div></div></figure>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="wood-7" data-source-fragment-sha256="a21908aa9ac3b78ec94789ef1bc29ad1f38ec188f9c040161d28a2a2bad80c9a" data-web-base-art-ref="wood-7" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="wood-7.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/wood-7.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:3.6923%;--hb-y:2.7141%;--hb-width:91.9822%;--hb-height:19.6375%">7. 製品をネジに垂直に掛けます。下部ブラケットの取付穴から壁面にタッピングネジを打ち込み、締め付けます。その後、木ネジを完全に締め付けます。</span></div></div></figure>

<span id="wall_concrete"></span>

## コンクリート壁面の場合

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="concrete-preparation" data-source-fragment-sha256="b92f7646f03e15872dcd68d2a18e3a956ce0f4195888704300226290f2232498" data-web-base-art-ref="concrete-preparation" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="concrete-preparation.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/concrete-preparation.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:3.6062%;--hb-y:12.6719%;--hb-width:18.4574%;--hb-height:12.8154%">取付前の準備：</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:43.7212%;--hb-y:31.9115%;--hb-width:12%;--hb-height:16.4538%">別売</span></div></div></figure>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="concrete-1-2" data-source-fragment-sha256="f11e128e6db1e128915d5234697a0c3bd3aaf2e87387aff57abcd924a2d7f2a4" data-web-base-art-ref="concrete-1-2" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="concrete-1-2.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/concrete-1-2.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:3.4602%;--hb-y:5.5495%;--hb-width:70.9031%;--hb-height:16.6739%">1. Jackery SlimPower H1本体を、取扱説明書に従って設置します。</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:3.4602%;--hb-y:16.3911%;--hb-width:42.366%;--hb-height:16.6739%">2. 製品底面のネジ2本を取り外します。</span></div></div></figure>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="concrete-3" data-source-fragment-sha256="3811cd0ca4634af8186f9ee3f749c3adc0a5d3f0053b918e229789de90a7f328" data-web-base-art-ref="concrete-3" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="concrete-3.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/concrete-3.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:40.7373%;--hb-y:8.4532%;--hb-width:54.5316%;--hb-height:17.4279%">3. 上下のマウントブラケットを製品背面にしっかり取り付けます。</span></div></div></figure>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="concrete-4" data-source-fragment-sha256="b3ad0adefc634c577b31b4bc6889205ad0e0fc7e5129b701c01fa2edd11de61c" data-web-base-art-ref="concrete-4" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="concrete-4.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/concrete-4.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:5.9204%;--hb-y:1.8515%;--hb-width:91.4301%;--hb-height:25.7534%">4. Jackery SlimPower H1本体のボルト位置から水平方向に455mm離れた場所を測定し、取付ポイントをマーキングします。*   455 mmは推奨距離であり、実際の距離は壁の状態に依存します。</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:35.019%;--hb-y:37.683%;--hb-width:14.5645%;--hb-height:5%">455mm</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:41.6791%;--hb-y:79.9202%;--hb-width:36.6567%;--hb-height:5%">Jackery SlimPower H1</span></div></div></figure>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="concrete-5" data-source-fragment-sha256="53938fed56456254527c9879941b564f82b5cf2f5cdbc4c77e88d0a7db760177" data-web-base-art-ref="concrete-5" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="concrete-5.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/concrete-5.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:8.0968%;--hb-y:2.1967%;--hb-width:89.4035%;--hb-height:26.6082%">5. 8mmのコンクリート用インパクトドリルを使用し、取付位置に深さ約70mmの穴をあけます。エクスパンションボルトを挿入し、ナットを2～4mm緩めます。</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:55.6309%;--hb-y:48.0632%;--hb-width:15.6041%;--hb-height:5%">70mm</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:74.7129%;--hb-y:57.8534%;--hb-width:13.1157%;--hb-height:5%">8mm</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:49.2974%;--hb-y:76.2573%;--hb-width:18.3043%;--hb-height:5%">2~4mm</span></div></div></figure>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="concrete-6" data-source-fragment-sha256="07e384517fd9ea301207d6b379736fa3ee9b52c58b36d282b417fa898609c1ef" data-web-base-art-ref="concrete-6" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="concrete-6.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/concrete-6.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:8.724%;--hb-y:3.4922%;--hb-width:86.2364%;--hb-height:20.1005%">6. 製品をエクスパンションボルトに垂直に掛け、壁面の取り付け位置をマーキングします。</span></div></div></figure>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="concrete-7" data-source-fragment-sha256="cf1a1ae5bb42c25933aef4f63fe5e67aa804da096108d9939dd6ba8f2e01b567" data-web-base-art-ref="concrete-7" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="concrete-7.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/concrete-7.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:6.6379%;--hb-y:3.1751%;--hb-width:85.3142%;--hb-height:20.1269%">7. 製品を取り外します。取付ポイントに穴を開け、ナットとワッシャーを使わずにボルトを穴に差し込んでください。</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:62.8942%;--hb-y:39.5562%;--hb-width:12.3304%;--hb-height:5%">70mm</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:77.0199%;--hb-y:50.5032%;--hb-width:12%;--hb-height:5%">8mm</span></div></div></figure>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="concrete-8" data-source-fragment-sha256="11219c7624c6768bdeaf1cc65b0dd9c0473221511e4ad53f6aa7ae22ffcbde13" data-web-base-art-ref="concrete-8" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="concrete-8.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/concrete-8.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:10.3728%;--hb-y:2.3554%;--hb-width:81.6459%;--hb-height:14.6627%">8.製品を上側のボルトに掛けてください。</span></div></div></figure>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="concrete-9" data-source-fragment-sha256="ee36fd559402827175703cfb078c459b305e398fea36ccf21fb9e25fafd3a80c" data-web-base-art-ref="concrete-9" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="concrete-9.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/concrete-9.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:5.6549%;--hb-y:2.3554%;--hb-width:88.2985%;--hb-height:14.6627%">9. 製品を持ち上げ、予め設置されたボルトに合わせてから下ろして設置します。ナットを締めます。</span></div></div></figure>

<span id="connection"></span>

## ポータブル電源との併用

<p>Jackery Battery Pack は、Jackery SlimPower H1 と併用することで、より大きな容量ニーズに対応できます。</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ご注意</td><td class="manual-callout-body"><p>バッテリーパックをJackery SlimPower H1に接続する前に、両方の電源がオフになっていることを確認してください。</p></td></tr></tbody></table>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="connection" data-source-fragment-sha256="821376c0efc8a52e0af426b48a0ac6903ba48520910cec8e36fff9add165d4a4" data-web-base-art-ref="connection" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="connection.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/connection.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:78.4771%;--hb-y:52.7698%;--hb-width:14.3924%;--hb-height:5.3217%">拡張ケーブル</span></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ご注意</td><td class="manual-callout-body"><p>LCD 画面（Jackery SlimPower H1）に<img alt="接続アイコン" src="assets/native-connected-batteries.svg"/>アイコンが表示されたら、バッテリーパックと Jackery SlimPower H1 の接続が成功したことを示します。</p></td></tr></tbody></table>

<span id="charging"></span>

## 充電方法

### AC充電

<p>AC充電の場合、本製品はJackery SlimPower H1と一緒にお使いください。</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">警告</td><td class="manual-callout-body"><p>バッテリーパックをJackery SlimPower H1に接続する前に、両方の電源がオフになっていることを確認してください。</p></td></tr></tbody></table>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ac-charge" data-source-fragment-sha256="c585725660d2e424eeb54154a932c9db8f7accdebb459c166b13858941756370" data-web-base-art-ref="ac-charge" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="ac-charge.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/ac-charge.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:65.8205%;--hb-y:5.6947%;--hb-width:14.4286%;--hb-height:10.2611%">拡張ケーブル</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:10.0798%;--hb-y:78.9179%;--hb-width:12.9905%;--hb-height:10.2611%">ACケーブル</span></div></div></figure>

### ソーラー充電

<p>下図のように、ソーラーパネルとJackery DC Input Moduleを使って製品を充電します。詳細については、Jackery DC Input Moduleの取扱説明書を参照してください。</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="solar-charge" data-source-fragment-sha256="09a95301bcd4392379163334a0278cf5e54e8cf527281b066b7430bcfd644995" data-web-base-art-ref="solar-charge" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="solar-charge.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/solar-charge.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:64.0919%;--hb-y:70.5343%;--hb-width:12%;--hb-height:5%">DC8020</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:3.3584%;--hb-y:90.1234%;--hb-width:52.8897%;--hb-height:6.3181%">*ソーラーパネルとJackery DC Input Moduleは別売りです。</span></div></div></figure>

### シガーソケット充電

<p>Jackery DC Input Moduleに接続することで、Jackery Battery Pack は12V/10A車載充電器で充電できます。使用方法の詳細については、Jackery DC Input Moduleのユーザーマニュアルを参照してください。</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="car-charge" data-source-fragment-sha256="324bd439cfe166341ebba43a2a68a58833723050c0a94f2b597373caa932368b" data-web-base-art-ref="car-charge" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="car-charge.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/car-charge.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:23.7931%;--hb-y:61.4917%;--hb-width:12%;--hb-height:11.1211%">車</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:62.4819%;--hb-y:71.665%;--hb-width:12%;--hb-height:5%">DC8020</span><span class="hb-reference-live-label hb-reference-live-pill hb-reference-source-badge" data-source-line="2" style="--hb-x:7.7841%;--hb-y:72.7047%;--hb-width:40.3598%;--hb-height:16.7722%;--hb-fill:#ebebec;--hb-label-color:#333333">※ 車載充電ケーブルとJackery DC Input Moduleは別売りです。</span></div></div></figure>

<span id="troubleshooting"></span>

## トラブルシューティング

<p>次のいずれかのエラーコードが表示された場合は、記載されている対処方法に従って問題を解決してください。問題が解決しない場合は、Jackeryカスタマーサポートまでご連絡ください。</p>

<figure aria-label="エラーコード / 対処方法" class="hb-troubleshooting-composition" data-component-id="HB-TABLE-TROUBLESHOOTING" tabindex="0"><table class="hb-troubleshooting-table"><colgroup><col class="hb-troubleshooting-col-code"/><col class="hb-troubleshooting-col-measures"/></colgroup><thead><tr><th class="hb-troubleshooting-code" scope="col">エラーコード</th><th class="hb-troubleshooting-measures" scope="col">対処方法</th></tr></thead><tbody><tr><td class="hb-troubleshooting-code">F0 /F2<br/>F3</td><td class="hb-troubleshooting-measures">製品を再起動してください。</td></tr><tr><td class="hb-troubleshooting-code">F1 /F6<br/>F7/F8</td><td class="hb-troubleshooting-measures">Jackeryカスタマーサポートまでご連絡ください。</td></tr><tr><td class="hb-troubleshooting-code">F4</td><td class="hb-troubleshooting-measures">製品に負荷を接続してバッテリーを放電し、エラーが消えるまで続けてください。</td></tr><tr><td class="hb-troubleshooting-code">F5</td><td class="hb-troubleshooting-measures">ソーラーパネルまたはAC電源コンセントを使用して、エラーが消えるまで製品を充電してください。</td></tr><tr><td class="hb-troubleshooting-code">FF</td><td class="hb-troubleshooting-measures"><p>高温環境下で</p><p>1.製品へのすべての充電・放電ケーブル（壁用充電器、ソーラーパネル、車載充電器、負荷機器を含む）を切り離してください。</p><p>2.製品を日陰で風通しの良い場所に設置し、周囲温度が45°C以下であることを確認してください。</p><p>3. 製品をアイドル状態にし、故障が消えるまで待ってください。</p><p>低温環境下で</p><p>1.製品を0℃以上の暖かい環境へ移動させてください。</p><p>2.極端に寒い屋外での使用や充電は行わないでください。必要に応じて、室内で予熱してください。</p><p>3.製品を寒い環境から室内に移動させた場合は、使用前にしばらく放置してください。</p><p>4.低温インジケーターが表示された場合は、製品をアイドル状態にして、システムが自動的に回復するのを待ってください。</p></td></tr></tbody></table></figure>

<span id="specifications"></span>

## 主な仕様

## 基本情報

<figure aria-label="基本情報" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">製品の名称</th><td class="manual-spec-value hb-spec-value">Jackery Battery Pack</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">型番</th><td class="manual-spec-value hb-spec-value">JBP-1000B-WH</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">バッテリータイプ</th><td class="manual-spec-value hb-spec-value">LiFePO₄ （リン酸鉄リチウムイオン電池）</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">定格容量</th><td class="manual-spec-value hb-spec-value">20Ah / 51.2Vdc (1024 Wh)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">サイズ＆重量</th><td class="manual-spec-value hb-spec-value">約 600 x 325 x 60 mm (約 9 kg)</td></tr></tbody></table></figure>

## 入力/出カポート

<figure aria-label="入力/出カポート" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">DC 拡張ポート (入力)</th><td class="manual-spec-value hb-spec-value">40V-57.6V⎓最大 24A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">DC 拡張ポート (出力)</th><td class="manual-spec-value hb-spec-value">40V-57.6V⎓最大 50A</td></tr></tbody></table></figure>

## 温度範囲

<figure aria-label="温度範囲" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">充電温度</th><td class="manual-spec-value hb-spec-value">-20°C～45°C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">動作温度</th><td class="manual-spec-value hb-spec-value">-20°C～45°C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">保存温度</th><td class="manual-spec-value hb-spec-value">1 年間 0～25°C<br/>3 ヶ月 0～45°C<br/>1 ヶ月 - 20～45°C</td></tr></tbody></table></figure>

<p>本製品はJackery SlimPower H1専用となります。他の機器には接続しないでください。</p>

<span id="warranty"></span>

## 保証について

<figure aria-label="保証について" class="hb-warranty-intro-composition" data-component-id="HB-WARRANTY-LEAD"><div class="hb-warranty-intro-panel"><p>このたびはJackery 製品をご購入いただき、誠にありがとうございます。本保証書は、Jackery ポータブル電源製品に関する保証内容を明確にご案内するものです。</p></div><div class="hb-warranty-local-note"><p>ご使用前に必ずご確認のうえ、大切に保管してください。</p></div></figure>

<span id="warranty-1"></span>

### 保証期間

<figure aria-label="保証期間" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="1"><p>1. 保証期間はご購入日から3 年間です。</p><p>2. また、延長保証にご登録いただくと、さらに2 年間の保証が追加されます。詳しくはJackery公式サイトをご確認ください。</p><p>※ Jackery 公式オンラインストアまたは正規代理店以外での購入品は保証対象外となります。</p></figure>

<span id="warranty-2"></span>

### 保証の適用範囲

<figure aria-label="保証の適用範囲" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="2"><p>1. 購入チャネルについて本保証は、Jackery公式オンラインストアまたは正規代理店で購入された製品に限り有効です。</p><p>2. 保証提供地域保証は、日本国内に在住の方が、日本国内で使用する場合に限り有効です。</p></figure>

<span id="warranty-3"></span>

### 保証の適用条件

<figure aria-label="保証の適用条件" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="3"><p>以下のすべての条件を満たす場合に、保証の適用対象となります：</p><p>・Jackery公式オンラインストアまたは正規代理店にてご購入されたこと</p><p>・保証期間内であること</p><p>・下記の「保証対象外」に該当しないこと</p></figure>

<span id="warranty-4"></span>

### 保証対象外となる場合

<figure aria-label="保証対象外となる場合" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="4"><p>以下のいずれかに該当する場合、保証期間内であっても保証の対象外となります：</p><p>1.故障・損傷が保証期間内に発生していても、保証期間終了後に申請された場合</p><p>2.使用上の誤り（取扱説明書や本体ラベルに記載の注意事項に従わなかった使用）による故障・損傷</p><p>3.他機器からの影響、不適切な修理または改造による故障・損傷</p><p>4.移設・輸送・落下などに起因する故障・損傷</p><p>5.火災・地震・風水害・落雷などの天災、または公害・塩害・異常電圧などによる故障・損傷</p><p>6.消耗部品の劣化や摩耗、または外観の汚損など</p></figure>

<span id="warranty-5"></span>

### 購入証明について

<figure aria-label="購入証明について" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="5"><p>保証をご利用の際には、以下いずれかの購入証明書類をご提示いただく必要があります：</p><p>・Jackery公式オンラインストアでの購入：注文番号（注文履歴画面または確認メール）</p><p>・正規代理店での購入：購入日・販売店名の記載された領収書または納品書</p><p>※  ご提示がない場合、保証対応いたしかねます。</p></figure>

<span id="warranty-6"></span>

### 保証内容

<figure aria-label="保証内容" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="6"><p>1. 初期不良による交換（ご購入日から30日以内）</p><p>・取扱説明書に従った正常な使用中に不具合が発生した場合、同一製品の新品と交換いたします。</p><p>・在庫切れや販売終了の場合は、同等品への交換または返金にて対応いたします。</p><p>2. 無償修理（ご購入日から31日以上～保証期間内）</p><p>・保証条件を満たす自然故障については、無料で修理対応いたします。</p><p>・修理が困難な場合は、同等品（同モデルまたは同等スペック品）への交換にて対応いたします。</p><p>3. 有償修理以下に該当する場合は、有償での修理対応となります：</p><p>・保証期間を超えた製品</p><p>・保証対象外と判断された場合</p><p>・Jackery公式オンラインストアまたは正規代理店以外で購入された製品</p><p>有償修理後の保証期間は、修理完了日より90日間です。</p><p>*無償修理の場合、残りの保証期間が90日未満であれば「90日間」、90日以上であれば「元の保証期間に準じます」。</p></figure>

<span id="warranty-7"></span>

### 免責事項

<figure aria-label="免責事項" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="7"><p>1. 弊社では、いかなる場合においても、間接的損害または付随的損害（データの損失・逸失利益など）に対して責任を負いません。</p><p>2. 本保証書は、お客様が法律上有する権利を制限するものではありません。</p><p>3. 保証内容は、予告なく変更される場合がございます。あらかじめご了承ください。Jackery 製品を安心してご使用いただくために、本保証書の内容をご確認のうえ、ご活用くださいますようお願いいたします。ご不明点がございましたら、Jackery カスタマーサービスまでお問い合わせください。</p></figure>

<span id="contact"></span>

## お問い合わせ

<p>公式サイト: https://www.jackery.jp</p>

<p>カスタマーサポート: jackery.jp@jackery.com</p>

<p>お問い合わせ電話番号: 050-3198-9007</p>
