<style>
/* Source-point label sizes; all paint comes from the shared theme. */
@media (min-width: 641px) {
.hb-reference-figure[data-reference-id="overview-front"] .hb-reference-live-label {font-size: .68rem; line-height: 1.15;}
.hb-reference-figure[data-reference-id="overview-front"] .hb-reference-live-label[data-source-line="5"],
.hb-reference-figure[data-reference-id="overview-front"] .hb-reference-live-label[data-source-line="7"],
.hb-reference-figure[data-reference-id="overview-front"] .hb-reference-live-label[data-source-line="9"],
.hb-reference-figure[data-reference-id="overview-front"] .hb-reference-live-label[data-source-line="16"],
.hb-reference-figure[data-reference-id="overview-front"] .hb-reference-live-label[data-source-line="17"] {font-size: .56rem; line-height: 1.15;}
.hb-reference-figure[data-reference-id="overview-right"] .hb-reference-live-label {font-size: .66rem; line-height: 1.2;}
.hb-reference-figure[data-reference-id="solar-four"] .hb-reference-live-label {font-size: .65rem; line-height: 1.2;}
}

/* Keep two-state operations in a two-column footer; the LED panel has three steps. */
.hb-operation-layout-footer-panel:not([data-operation-id="led-light"]) .hb-operation-steps {grid-template-columns:repeat(2,minmax(0,1fr));}

</style>

# Jackery ポータブル電源 2000 Plus

<p>取扱説明書｜JE-2000E｜日本語</p>

<p>国内専用/For use only in Japan</p>

<p>カスタマーサポート: jackery.jp@jackery.com</p>

<p>お買い上げありがとうございます。</p>

<p>ご使用の前にこの「取扱説明書」をよくお読みのうえ、正しくお使いください。</p>

<p>特に「安全上のご注意」は、必ずお読みいただき、安全にお使いください。</p>

<p>お読みになったあとは、すぐに取り出せる場所に大切に保管してください。</p>

<p>本製品の取扱説明書は随時更新されますので、最新の取扱説明書は公式サイトでご確認ください。</p>

<span id="safety"></span>

## 安全上のご注意

<p>ご使用の前にこの「安全上のご注意」をよくお読みのうえ、正しくお使いください。</p>

### 絵表示について

<p>製品を安全に正しくお使いいただき、お客様や他の方々への危害や財産への損害を未然に防止するための表示です。内容をよく理解してから本文をお読みください。</p>

<figure aria-label="絵表示について" class="hb-symbol-signal-composition" data-component-id="HB-TABLE-SYMBOL-SIGNAL"><table class="hb-symbol-signal-table"><colgroup><col class="hb-symbol-signal-col-label"/><col class="hb-symbol-signal-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-signal-label-heading" scope="col">表示</th><th class="hb-symbol-signal-meaning-heading" scope="col">意味</th></tr></thead><tbody><tr><td class="hb-symbol-signal-label-cell"><span aria-label="警告" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">警告</span></span></td><td class="hb-symbol-signal-meaning-cell">この表示を無視して、誤った取り扱いをすると、人が死亡または重傷を負う可能性が想定される内容を示しています。</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="注意" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">注意</span></span></td><td class="hb-symbol-signal-meaning-cell">この表示を無視して、誤った取り扱いをすると、人が傷害を負う可能性が想定される内容または物的損害の発生が想定される内容を示しています。</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="説明" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">説明</span></span></td><td class="hb-symbol-signal-meaning-cell">この表示を無視して誤った取り扱いをすると、機器の損傷、データの消失、性能の低下、または予期しない動作が発生する可能性があることを示しています。</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="ヒント" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">ヒント</span></span></td><td class="hb-symbol-signal-meaning-cell">文章内の重要な情報や操作のヒントを補足する内容を示しています。</td></tr></tbody></table></figure>

### 絵表示の説明

<figure aria-label="絵表示の説明" class="hb-symbol-pair-composition" data-component-id="HB-TABLE-SYMBOL-ICON"><div class="hb-symbol-pair-grid"><div class="hb-symbol-panel hb-symbol-panel-1"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">記号</th><th class="hb-symbol-meaning-heading" scope="col">説明</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="潜在的な危険やリスクについて注意喚起するために、必ずお読みください。" class="hb-symbol-art" src="assets/h1-jp-warning_triangle.svg"/></td><td class="hb-symbol-meaning">潜在的な危険やリスクについて注意喚起するために、必ずお読みください。</td></tr><tr><td class="hb-symbol-icon"><img alt="操作の前に取扱説明書をお読みください。" class="hb-symbol-art" src="assets/h1-jp-read_manual.svg"/></td><td class="hb-symbol-meaning">操作の前に取扱説明書をお読みください。</td></tr><tr><td class="hb-symbol-icon"><img alt="本製品を火気の近くに置かないでください。" class="hb-symbol-art" src="assets/h1-jp-no_open_flame.svg"/></td><td class="hb-symbol-meaning">本製品を火気の近くに置かないでください。</td></tr><tr><td class="hb-symbol-icon"><img alt="小さなお子様の手の届かない場所に保管してください。" class="hb-symbol-art" src="assets/h1-jp-keep_away_from_children.svg"/></td><td class="hb-symbol-meaning">小さなお子様の手の届かない場所に保管してください。</td></tr><tr><td class="hb-symbol-icon"><img alt="製品を分解、改造を禁止する記号" class="hb-symbol-art" src="assets/h1-jp-do_not_dismantle.svg"/></td><td class="hb-symbol-meaning">製品を分解、改造を禁止する記号</td></tr></tbody></table></div><div class="hb-symbol-panel hb-symbol-panel-2"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">記号</th><th class="hb-symbol-meaning-heading" scope="col">説明</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="コンセントから電源プラグを抜く記号" class="hb-symbol-art" src="assets/h1-jp-unplug.svg"/></td><td class="hb-symbol-meaning">コンセントから電源プラグを抜く記号</td></tr><tr><td class="hb-symbol-icon"><img alt="製品に濡れた手で触れることを禁止する記号" class="hb-symbol-art" src="assets/h1-jp-no_wet_hands.svg"/></td><td class="hb-symbol-meaning">製品に濡れた手で触れることを禁止する記号</td></tr><tr><td class="hb-symbol-icon"><img alt="製品を濡らすことを禁止する記号" class="hb-symbol-art" src="assets/h1-jp-keep_dry.svg"/></td><td class="hb-symbol-meaning">製品を濡らすことを禁止する記号</td></tr><tr><td class="hb-symbol-icon"><img alt="行為を指示する記号" class="hb-symbol-art" src="assets/h1-jp-mandatory.svg"/></td><td class="hb-symbol-meaning">行為を指示する記号</td></tr><tr><td class="hb-symbol-icon"><img alt="行為を禁止する記号" class="hb-symbol-art" src="assets/h1-jp-prohibited.svg"/></td><td class="hb-symbol-meaning">行為を禁止する記号</td></tr></tbody></table></div></div></figure>

<figure aria-label="充電式電池のリサイクルと廃棄" class="hb-symbol-pair-composition" data-component-id="HB-TABLE-SYMBOL-ICON"><div class="hb-symbol-pair-grid"><div class="hb-symbol-panel hb-symbol-panel-1"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">記号</th><th class="hb-symbol-meaning-heading" scope="col">説明</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="充電式電池のリサイクル" class="hb-symbol-art" src="assets/h1-jp-battery_recycle.svg"/></td><td class="hb-symbol-meaning">充電式電池のリサイクルについて本機はリサイクル可能な充電池を内蔵しています。この商品を廃棄する場合は、当社のカスタマーサポートにご連絡ください。充電池の取りはずしはお客様自身では行わないでください。</td></tr></tbody></table></div><div class="hb-symbol-panel hb-symbol-panel-2"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">記号</th><th class="hb-symbol-meaning-heading" scope="col">説明</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="廃棄とリサイクル" class="hb-symbol-art" src="assets/h1-jp-weee.svg"/></td><td class="hb-symbol-meaning">このシンボルは、本製品を一般家庭ごみとして廃棄せず、リサイクルのために指定の回収施設に持ち込む必要があることを示しています。適切な廃棄およびリサイクルは、環境保護に役立ちます。本製品の廃棄やリサイクルについての詳細は、お住まいの自治体、廃棄物処理業者、または販売店にお問い合わせください。</td></tr></tbody></table></div></div></figure>

### 警告

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">警告</td><td class="manual-callout-body"><p>火のそばや炎天下の車内、熱器具の周辺など高温（45℃以上）になる場所で使用したり、放置しない発熱や発火、破裂する原因になります。</p></td></tr></tbody></table>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">警告</td><td class="manual-callout-body"><p>強い衝撃を与えたり、投げつけたりしない発熱や発火、破裂する原因になります。</p></td></tr></tbody></table>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">警告</td><td class="manual-callout-body"><p>水など、液体を入れたり、濡らしたりしない発熱や発火の原因になります。</p></td></tr></tbody></table>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">警告</td><td class="manual-callout-body"><p>濡れた手で本体や接続するケーブルを触らない火災や感電の原因になります。</p></td></tr></tbody></table>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">警告</td><td class="manual-callout-body"><p>端子部にケーブル以外の金属類を差し込まない発熱や発火の原因になります。</p></td></tr></tbody></table>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">警告</td><td class="manual-callout-body"><p>雷が鳴りだしたら、電源プラグにふれない (充電をしない)感電の原因になります。</p></td></tr></tbody></table>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">警告</td><td class="manual-callout-body"><p>各接続端子には確実に差し込む差し込みが不十分だと、発熱したりほこりが付着して火災や感電の原因になります。</p></td></tr></tbody></table>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">警告</td><td class="manual-callout-body"><p>接地接続は必ず、電源プラグを電源につなぐ前に行って下さいまた、接地接続を外す場合は、必ず電源プラグを切り離してから行って下さい。</p></td></tr></tbody></table>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">警告</td><td class="manual-callout-body"><p>万が一、次のような異常が発生したときはすぐに使用をやめる煙が出ている、異臭がする落としたり、破損したとき異音がする内部に水や異物が入ったとき電源コード (AC充電ケーブル) が傷んだときこのような異常が発生したまま使用していると、火災や感電の原因になります。すぐにAC充電ケーブルをコンセントから抜いてください。また、本製品に接続されている機器もすべて外してください。万が一発煙や発火したら、大量の水で消火して煙が見えなくなるまで本製品を水浸しにしてください。煙が出なくなることを確認してからカスタマーサポートにご連絡ください。お客様による修理は危険ですので絶対におやめください。</p></td></tr></tbody></table>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">警告</td><td class="manual-callout-body"><p>分解、改造しない。故障、発熱、火災·感電の原因になります。</p></td></tr></tbody></table>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">警告</td><td class="manual-callout-body"><p>表示された電源電圧以外で使用しない故障、発熱、火災·感電の原因になります。また、本製品を使用できるのは日本国内のみです。</p></td></tr></tbody></table>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">警告</td><td class="manual-callout-body"><p>付属品と本製品が破損した場合は、ご自身で修理をしない</p></td></tr></tbody></table>

### 注意

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">注意</td><td class="manual-callout-body"><p>本製品の上に物を載せたり、不安定な場所に置かない倒れたり、落ちたりしてけがの原因になります。</p></td></tr></tbody></table>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">注意</td><td class="manual-callout-body"><p>データサーバや医療機器など、非常時に不具合が起こると人命 / 財産に重大な危険を及ぼしうる用途でのご使用はお控えください。次のようなような機器では、万が一使用中に給電ができなくなった場合、人命 / 財産にかかわる被害が想定されます。• 医療機器や使用上、生命に関わるような機器• 社会的、公共的に重要な機器など• 重要な事業用機器など</p></td></tr></tbody></table>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">注意</td><td class="manual-callout-body"><p>心臓にペースメーカーを装着している方は使用しないペースメーカーが、本製品の影響を受ける恐れがあります。</p></td></tr></tbody></table>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">注意</td><td class="manual-callout-body"><p>格納式ハンドルを使用してJackery ポータブル電源 2000 Plus を移動するときは、積み重ねたり、上に他の物を置いたりしないでください。落下して怪我をする場合があります。</p></td></tr></tbody></table>

<span id="usage-notes"></span>

## 使用上のご注意

<p>Jackery ポータブル電源 2000 Plus は、定格出力2400Wです。通常時で消費電力が2400Wまでの機器に給電ができるため、多くの電化製品や端末に対応可能です。ただし、電気モーターを搭載している製品（掃除機、ポンプ、冷蔵庫、電動丸ノコ、エアコン、洗濯機、電子レンジ、ドライヤーなど)は、起動時に「誘導負荷」が発生し、公称電力の3~7倍の電力が必要となります。定格出力2400Wは、一定の電力で動く機器への出力可能範囲を指しています。2400Wの出力を超えた場合は、電気回路が自動的に調整され、電力が低減、または保護機能が作動し自動で遮断することがあります。またAC出力ポート4つ搭載されておりますが、2つ同時にご利用頂く場合、合計して2400W以内であることをご確認の上ご利用ください。</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ご注意</td><td class="manual-callout-body"><p>始動電力が出力上限値( 定格出力) を大幅に超える可能性のある製品のご利用や、定格出力を超え給電がストップした製品を繰り返し利用することはポータブル電源のバッテリーが損傷するリスクがありますのでお控えください。</p></td></tr></tbody></table>

### ■ 給電に関する注意事項

<p>出力上限値を超える電化製品は使用しないでください。</p>

<ul><li>特に、始動電力が公称電力の3~7 倍になる誘導負荷（ポンプ、ヒーター、掃除機、冷蔵庫、エアコン、電気丸ノコなどの電動道具、洗濯機、電子レンジなど）の使用にはご注意ください。</li><li>接続機器の消費電力が本製品の出力範囲内であることをご確認の上、出力ボタンを押してください。</li><li>給電中、機器の制御や環境により、急速充電にならない・給電できない場合があります。</li><li>充電または給電中、ラジオ・チューナー・テレビなどに雑音が入る場合があります。その際は、それらの機器から離してご使用ください。</li></ul>

### ■ 使用環境について

<ul><li>本製品は防塵・防水仕様ではありません。ほこり、水、海水などがかからないようご注意ください。</li><li>ほこりの多い場所や高温多湿の場所での充電・使用・放置は避けてください。</li><li>平坦で安定した場所に設置し、不安定な場所に置かないでください。</li><li>本製品の通風孔は、安全上絶対にふさがないでください。各面から5cm 以上スペースを確保してください。</li><li>充電・給電中は本体が温かくなります。周囲に物を置かないでください。</li></ul>

### ■ 接続時の注意事項

<ul><li>ケーブルを接続する際は、まっすぐに差し込んでください。</li><li>抜く際は必ずプラグ部分を持って抜いてください。ケーブルを引っ張ったり折り曲げたりしないでください。</li><li>この機器に同梱した指定の電源コードセットだけを使用する。</li></ul>

### ■ お手入れについて

<ul><li>本体が汚れた場合は、電源プラグを抜いた状態で、柔らかい布で乾拭きしてください。</li><li>汚れがひどい場合は、水または薄めた中性洗剤で拭き取ってください。</li><li>シンナーやベンジンなどの使用は絶対に使わないでください。</li></ul>

### ■ 入出力・温度・表示に関するご注意

<ul><li>接続機器の入力が本製品の出力上限を超えている場合、自動で電源が遮断されます。</li><li>本機は -10°C~45°C の温度範囲でお使いの機器に電力供給が可能となり、本機の蓄電は-10°C~45°C で行えます。</li><li>動作温度が上記範囲外にある場合、本製品が温度異常マークが表示され、動作しない可能性があります。</li><li>温度異常マークが表示された場合は、本製品を2 時間以上、動作温度範囲内の環境に置いてください。</li><li>容量表示は参考値であり、電圧により表示数値と実際の容量に差異が出る場合があります。</li></ul>

<span id="disclaimer"></span>

## 免責事項

<ul><li>火災、地震、第三者による行為、その他の事故、お客様の故意または過失誤用・誤動作・その他の異常な条件下での使用により生じた損害に関して、当社は一切責任を負いません。</li><li>付属品と本製品が破損した場合は、ご自身で修理を行わないでください。ご自身で分解・修理したことにより生じた損害に関し、当社は一切責任を負いません。</li><li>保証範囲は利用規約に適用され、記載されていない内容は当社の保証範囲外となります。</li><li>取扱説明書の記載事項が遵守されないことにより生じた不適合について当社は責任を負いかねます。</li><li>本製品の使用、または使用不能から発生する付随的な損害( 事業利益損失含む)、当社が関与しない接続機器との組み合わせによる誤動作などから生じた損害に関して、当社は一切の責任を負いません。</li><li>本製品は病院仕様のシーパップ（CPAP）、エクモ（ECMO）、ペースメーカなど、身の安全に関わる医療救急機械の電源としての使用、または、消費電力の大きいな設備、例えば核施設設備、スペースシャトル製造などの使用は推薦されません。上記設備の使用後、火災、機器故障など個人安全を脅かす事故の責任を取りません。</li></ul>

<span id="in-the-box"></span>

## 同梱品

<figure aria-label="同梱品" class="hb-inbox-composition" data-card-count="3" data-component-id="HB-SPECIAL-INBOX" data-inbox-variant="three-card-responsive"><ol class="hb-inbox-grid"><li class="hb-inbox-card" data-item-number="1"><img alt="本体" class="hb-inbox-art" src="assets/inbox-main.png"/><div class="hb-inbox-label">本体</div></li><li class="hb-inbox-card" data-item-number="2"><img alt="AC充電ケーブル" class="hb-inbox-art" src="assets/inbox-cable.png"/><div class="hb-inbox-label">AC充電ケーブル</div></li><li class="hb-inbox-card" data-item-number="3"><img alt="取扱説明書一式" class="hb-inbox-art" src="assets/inbox-manual.png"/><div class="hb-inbox-label">取扱説明書一式</div></li></ol></figure>

<p>※ 付属品を故障、紛失等してしまった場合はカスタマーサポートまでご連絡ください。</p>

<p>※ AC充電ケーブルは、同梱されている本体以外には使用しないでください。</p>

<p>※ シガーソケット充電ケーブルは別売りです。Jackery公式サイトよりご購入いただけます。サポートが必要な場合は、Jackeryカスタマーサポートまでお問い合わせください。</p>

<p>本機の仕様および外観は、改善のため予告なく変更することがあります。</p>

<span id="overview"></span>

## 各部の名称

### 正面

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview-front" data-source-fragment-sha256="ef29c3fbe7fd58aaf5fa161d4f6fbba7834956fd5b4fa89d34c859032f781ee5" data-web-base-art-ref="overview-front" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-reference-id="overview-front.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/overview-front.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:0.9346%;--hb-y:2.9762%;--hb-width:26.4798%;--hb-height:11.9048%">主電源ボタン</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:0.9346%;--hb-y:20.8333%;--hb-width:26.7913%;--hb-height:10.7143%">シガーソケット出力ポート</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:0.9346%;--hb-y:30.3571%;--hb-width:26.4798%;--hb-height:7.7381%">12V⎓最大10A</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:0.9346%;--hb-y:36.9048%;--hb-width:26.1682%;--hb-height:11.3095%">DC/USB出力ボタン</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:0.9346%;--hb-y:48.2143%;--hb-width:26.1682%;--hb-height:9.5238%">USB-C 30W出力ポート</span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:0.9346%;--hb-y:57.1429%;--hb-width:28.0374%;--hb-height:8.9286%">5V⎓3A, 9V⎓3A, 12V⎓2.5A，15V⎓2A，20V⎓1.5A，最大30W</span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:0.9346%;--hb-y:65.4762%;--hb-width:26.4798%;--hb-height:9.5238%">USB-A 18W出力ポート</span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:0.9346%;--hb-y:75%;--hb-width:27.7259%;--hb-height:8.9286%">5-6V⎓3A, 6-9V⎓2A, 9-12V⎓1.5A，最大18W</span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:0.9346%;--hb-y:82.7381%;--hb-width:39.8754%;--hb-height:8.9286%">USB-C 140W出力ポート</span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:0.9346%;--hb-y:90.4762%;--hb-width:41.433%;--hb-height:9.5238%">5V⎓3A，9V⎓3A，12V⎓3A，15V⎓3A，20V⎓5A，28V⎓5A，最大140W</span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:75.0779%;--hb-y:2.9762%;--hb-width:24.6106%;--hb-height:8.3333%">LCDディスプレイ</span><span class="hb-reference-live-label" data-source-line="11" style="--hb-x:75.0779%;--hb-y:12.5%;--hb-width:24.6106%;--hb-height:9.5238%">LEDライトボタン</span><span class="hb-reference-live-label" data-source-line="12" style="--hb-x:78.5047%;--hb-y:26.7857%;--hb-width:21.1838%;--hb-height:8.9286%">LEDライト</span><span class="hb-reference-live-label" data-source-line="13" style="--hb-x:76.6355%;--hb-y:36.9048%;--hb-width:23.053%;--hb-height:8.9286%">AC1出力ボタン</span><span class="hb-reference-live-label" data-source-line="14" style="--hb-x:76.6355%;--hb-y:47.619%;--hb-width:23.053%;--hb-height:9.5238%">AC2出力ボタン</span><span class="hb-reference-live-label" data-source-line="15" style="--hb-x:75.3894%;--hb-y:59.5238%;--hb-width:24.2991%;--hb-height:7.7381%">AC出力ポート</span><span class="hb-reference-live-label" data-source-line="16" style="--hb-x:74.4548%;--hb-y:67.2619%;--hb-width:25.2336%;--hb-height:8.9286%">100V~ 50Hz/60Hz，最大20A，定格2000W，4ポート合計2400W，</span><span class="hb-reference-live-label" data-source-line="17" style="--hb-x:78.5047%;--hb-y:76.1905%;--hb-width:21.1838%;--hb-height:8.3333%">瞬間最大4800W</span></div></div></figure>

### 左側面

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview-left" data-source-fragment-sha256="84439ae2f50ae3f5bd2f4712b5e7e5082c3e6f64e2a9d7189b07c7f5a0e69d35" data-web-base-art-ref="overview-left" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-reference-id="overview-left.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/overview-left.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:0.627%;--hb-y:2.0619%;--hb-width:38.558%;--hb-height:20.6186%">ハンドル</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:0.627%;--hb-y:46.3918%;--hb-width:38.558%;--hb-height:18.5567%">DC拡張ポート端子</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:0.627%;--hb-y:65.9794%;--hb-width:38.558%;--hb-height:14.433%">バッテリーパックに接続</span></div></div></figure>

### 右側面

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview-right" data-source-fragment-sha256="7ae8e21d81e46b856004c5450935851f57e91c9818a7759d8cb81ee9bab46dce" data-web-base-art-ref="overview-right" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-reference-id="overview-right.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/overview-right.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:0.627%;--hb-y:1.7857%;--hb-width:46.7085%;--hb-height:41.0714%">DC入力ポート（DC8020）PV：16V-60V⎓12A, 2ポート最大21A，最大800Wｼｶﾞｰｿｹｯﾄ ：11V-16V⎓最大8A, 2ポート最大8A</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:0.627%;--hb-y:51.7857%;--hb-width:46.7085%;--hb-height:26.7857%">AC入力ポート100V-120V~ 50Hz/60Hz，最大15A</span></div></div></figure>

<span id="lcd-display"></span>

## 液晶画面

<figure class="hb-reference-figure hb-has-composite-art" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="lcd-overview" data-source-fragment-sha256="8ece172f3ecf648f5f6ef102cda6361fb8776bb6d02b42988586ebc01d6d7a39" data-step-captions="embedded" data-web-composite-asset-key="frozen-source/lcd-overview" data-web-composite-locale="ja" data-web-composite-sha256="b70995d4868cd7005c23b74dc0449079e63939deed0e24ff783a2e22f2684949" data-web-replace-key="reference.lcd-overview"><div aria-hidden="true" class="hb-composite-stage"><img alt="" class="hb-composite-art" loading="lazy" src="assets/lcd-overview.png"/></div><div class="hb-reference-semantic" data-reference-id="lcd-overview.semantic"><img alt="液晶画面：表示番号と各表示の位置" class="hb-reference-art hb-composite-art" src="assets/lcd-overview.png"/></div></figure>

<figure aria-label="液晶画面のアイコン" class="hb-lcd-table-composition" data-component-id="HB-TABLE-LCD-ICON" tabindex="0"><table class="hb-lcd-icon-table"><colgroup><col class="hb-lcd-col-number"/><col class="hb-lcd-col-icon"/><col class="hb-lcd-col-name"/><col class="hb-lcd-col-description"/></colgroup><tbody><tr><td class="hb-lcd-number">1</td><td class="hb-lcd-icon"><img alt="Wi-Fi" class="hb-lcd-icon-art" src="assets/1_Wi-Fi_KCcAbdDk7o4RjKx82micuKJ5nyf.png"/></td><td class="hb-lcd-name">Wi-Fi</td><td class="hb-lcd-description">オン： Wi-Fi接続済。点滅： Wi-Fiに接続する準備ができました。オフ： Wi-Fi接続解除済。</td></tr><tr><td class="hb-lcd-number">2</td><td class="hb-lcd-icon"><img alt="Bluetooth" class="hb-lcd-icon-art" src="assets/2_Bluetooth_HVgvbJhq5o4EDKxhm7McCF4FnjB.png"/></td><td class="hb-lcd-name">Bluetooth</td><td class="hb-lcd-description">オン： Bluetooth接続済。点滅： Bluetoothに接続する準備ができました。オフ： Bluetooth接続解除済。</td></tr><tr><td class="hb-lcd-number">3</td><td class="hb-lcd-icon"><img alt="静音充電モード" class="hb-lcd-icon-art" src="assets/3_Quiet_Charging_Mode_WLkMbiHS1oGsOtxUCp7cRhFAn1g.png"/></td><td class="hb-lcd-name">静音充電モード</td><td class="hb-lcd-description">オン：充電中のノイズが大幅に低減され、充電電力が低下し、充電速度が低減します。オフ：静音充電モードが無効になっています。（Jackeryアプリで有効/無効にできます。電源オフ時も設定は保持されます。）</td></tr><tr><td class="hb-lcd-number">4</td><td class="hb-lcd-icon"><img alt="計画充電モード" class="hb-lcd-icon-art" src="assets/4_Charging_Plan_M96RbyZQxoGjRRxQHsuczeIln1b.png"/></td><td class="hb-lcd-name">計画充電モード</td><td class="hb-lcd-description">Jackery ポータブル電源 2000 Plus の充電時間をカスタマイズすることで、電気料金のピーク時間とオフピーク時間に基づいた充電プランを選択。これにより月々の電気料金を削減することができます。（Jackeryアプリで設定してください。電源オフ時も設定は保持されます。）</td></tr><tr><td class="hb-lcd-number">5</td><td class="hb-lcd-icon"><img alt="自家発電モード" class="hb-lcd-icon-art" src="assets/5_Self-powered_Mode_FYTnb9vttoexjbxVMchcJaobnCg.png"/></td><td class="hb-lcd-name">自家発電モード</td><td class="hb-lcd-description">点灯時：自家発電モードがオンになっており、太陽光エネルギーの利用を最大化し、電力会社からの電力消費を削減して電気代を節約します。消灯時：自家発電モードがオフ、または未設定の状態です。（Jackeryアプリで設定してください。電源オフ時も設定は保持されます。）</td></tr><tr><td class="hb-lcd-number">6</td><td class="hb-lcd-icon"><img alt="TOUモード" class="hb-lcd-icon-art" src="assets/6_TOU_Mode_BjEkbz0rFo6Bw4xiwNpcod9qnnc.png"/></td><td class="hb-lcd-name">TOUモード</td><td class="hb-lcd-description">オン：TOUモードが有効です（デフォルトバックアップSOC：60%）。ピーク時間帯に、蓄積エネルギーがバックアップSOCを上回ると、本製品はバッテリーの放電を優先し、ピーク時の電力コストを削減します。 オフピーク時間帯には、系統からバッテリーを充電し、ピークカットと谷埋めを実現します。オフ：TOUモードは無効になります。 本デバイスはTOU（時間帯別料金）戦略に従わず、デフォルトの電力供給および充電ロジックに基づいて動作します。（Jackeryアプリで設定してください。電源オフ時も設定は保持されます。）</td></tr><tr><td class="hb-lcd-number">7</td><td class="hb-lcd-icon"><img alt="UPS機能" class="hb-lcd-icon-art" src="assets/7_UPS_Lgdgb8pvvoGwaLxSf8ec2QeHn3c.png"/></td><td class="hb-lcd-name">UPS機能</td><td class="hb-lcd-description">点灯時：製品が給電と充電を同時に行う「パススルー充電」状態にあります。停電時には家庭用電源からポータブル電源の切り替え時間が10ミリ秒で行われます。消灯時：製品がパススルー充電状態ではありません。</td></tr><tr><td class="hb-lcd-number">8</td><td class="hb-lcd-icon"><img alt="交流電源による出力マーク（正弦波)" class="hb-lcd-icon-art" src="assets/8_AC_Power_Indicator_HFPSbvWBgosvCux69jMcuWe6nnh.png"/></td><td class="hb-lcd-name">交流電源による出力マーク（正弦波)</td><td class="hb-lcd-description">AC出力（純正弦波）がオンになっています。</td></tr><tr><td class="hb-lcd-number">9</td><td class="hb-lcd-icon"><img alt="出力電圧と周波数" class="hb-lcd-icon-art" src="assets/9_Output_Voltage_and_Frequency_Jh3JbmBDBoKlmOxaRJDcIMJAn6b.png"/></td><td class="hb-lcd-name">出力電圧と周波数</td><td class="hb-lcd-description">出力される電圧と周波数を表示します。</td></tr><tr><td class="hb-lcd-number">10</td><td class="hb-lcd-icon"><img alt="入力電力表示" class="hb-lcd-icon-art" src="assets/10_Input_Power_LOAZbnxfqoHFwIxx2Myc532jnzb.png"/></td><td class="hb-lcd-name">入力電力表示</td><td class="hb-lcd-description">入力電力をワットで表示します。</td></tr><tr><td class="hb-lcd-number">11</td><td class="hb-lcd-icon"><img alt="充電残り時間" class="hb-lcd-icon-art" src="assets/11_Remaining_Charge_Time_KIWHbHFOvotGuBxJsxlcunSDnPf.png"/></td><td class="hb-lcd-name">充電残り時間</td><td class="hb-lcd-description">充電残り時間を表示します。</td></tr><tr><td class="hb-lcd-number">12</td><td class="hb-lcd-icon"><img alt="AC入力電力表示" class="hb-lcd-icon-art" src="assets/12_AC_Wall_Charging_Indicator_ZpOmbCjx8oYUTVxyl4JcvcTanPe.png"/></td><td class="hb-lcd-name">AC入力電力表示</td><td class="hb-lcd-description">製品は、系統電力を使用し、AC入力を介して充電されます。</td></tr><tr><td class="hb-lcd-number">13</td><td class="hb-lcd-icon"><img alt="シガーソケット入力電力表示" class="hb-lcd-icon-art" src="assets/13_Car_Charging_Indicator_DLkibYaP1ot6d5x1S0jcUr1knlb.png"/></td><td class="hb-lcd-name">シガーソケット入力電力表示</td><td class="hb-lcd-description">製品は、DC 12V（カーチャージ）を使用し、8020入力ポートを介して充電されています。</td></tr><tr><td class="hb-lcd-number">14</td><td class="hb-lcd-icon"><img alt="ソーラー(グリーンエネルギー)充電接続" class="hb-lcd-icon-art" src="assets/14_Solar_Charging_Indicator_RgAUbPXNWoRxiHxKNgkc2gqDnEb.png"/></td><td class="hb-lcd-name">ソーラー(グリーンエネルギー)充電接続</td><td class="hb-lcd-description">製品は、ソーラーパネルを使用し、8020入力ポートを介して充電されています。</td></tr><tr><td class="hb-lcd-number">15</td><td class="hb-lcd-icon"><img alt="バッテリー節約モードJackeryアプリで有効/無効にできます" class="hb-lcd-icon-art" src="assets/15_Battery_Saving_Mode_ClYfbtOGSoK5q2xySXCcgehVn8f.png"/></td><td class="hb-lcd-name">バッテリー節約モードJackeryアプリで有効/無効にできます</td><td class="hb-lcd-description">バッテリー節約モード設定時は、バッテリー残量が既定値に設定されるため、バッテリーの寿命を延ばすことが可能です。（Jackeryアプリで設定してください。電源オフ時も設定は保持されます。）この機能が有効な場合、本製品はSOCを較正するために、時折フル充放電サイクルを実行します。</td></tr><tr><td class="hb-lcd-number">16</td><td class="hb-lcd-icon"><img alt="充電速度制限" class="hb-lcd-icon-art" src="assets/16_Charging_Power_Limit_VLf2bJfrkoCL0CxJoMNcL5ZxnCt.png"/></td><td class="hb-lcd-name">充電速度制限</td><td class="hb-lcd-description">点灯時：アプリ側で充電速度制限が有効になっています。消灯時：アプリ側で充電速度制限が無効になっています。（Jackeryアプリで設定してください。電源オフ時も設定は保持されます。）</td></tr><tr><td class="hb-lcd-number">17</td><td class="hb-lcd-icon"><img alt="バッテリーアイコン" class="hb-lcd-icon-art" src="assets/17_Battery_Power_Indicator_VLufb9exvoVLfgxz47pcfnRGnaf.png"/></td><td class="hb-lcd-name">バッテリーアイコン</td><td class="hb-lcd-description">製品の充電中は、バッテリーのパーセンテージを囲むオレンジ色の円が順番に点灯します。他のデバイスの充電時には、オレンジ色の円は点灯したままになります。</td></tr><tr><td class="hb-lcd-number">18</td><td class="hb-lcd-icon"><img alt="バッテリー残量警告灯" class="hb-lcd-icon-art" src="assets/19_Low_Battery_Indicator_KDk9bhs8poHUBdx96PLckPganhd.png"/></td><td class="hb-lcd-name">バッテリー残量警告灯</td><td class="hb-lcd-description">オン：バッテリー残量が20％未満です。点滅：バッテリー残量が5％未満です。オフ：製品は充電中です。</td></tr><tr><td class="hb-lcd-number">19</td><td class="hb-lcd-icon"><img alt="バッテリーレベルパーセントタグ" class="hb-lcd-icon-art" src="assets/18_Remaining_Battery_Percentage_VkJcbUDbUoYC1hxrU6rc168OnJe.png"/></td><td class="hb-lcd-name">バッテリーレベルパーセントタグ</td><td class="hb-lcd-description">バッテリー残量を表示します。</td></tr><tr><td class="hb-lcd-number">20</td><td class="hb-lcd-icon"><img alt="放電タイマー" class="hb-lcd-icon-art" src="assets/20_Discharge_Timer_DHPMbkjSWoiuALxJyJ8cWyQOn0e.png"/></td><td class="hb-lcd-name">放電タイマー</td><td class="hb-lcd-description">オン：放電タイマーが設定されています。オフ：放電タイマーは設定されていません。Jackeryアプリで設定してください。本設定は、デバイスの電源を切ると保持されません。</td></tr><tr><td class="hb-lcd-number">21</td><td class="hb-lcd-icon"><img alt="バッテリーパックインジケータと接続された量" class="hb-lcd-icon-art" src="assets/21_Connected_Batteries_ZeHlbv3HEoRcq2xIXacchUcTndg.png"/></td><td class="hb-lcd-name">バッテリーパックインジケータと接続された量</td><td class="hb-lcd-description">本製品に接続されているバッテリーパックの台数を表示します。</td></tr><tr><td class="hb-lcd-number">22</td><td class="hb-lcd-icon"><img alt="省エネモード" class="hb-lcd-icon-art" src="assets/22_Energy_Saving_Mode_O4Jdb5pUQoCBAqx0sfQcm9Nbntd.png"/></td><td class="hb-lcd-name">省エネモード</td><td class="hb-lcd-description">AC1/2またはDC/USB出力ボタンを押して出力をオンにしたとき：アイコン表示：省エネモードがオンになっています。アイコン消える：省エネモードがオフになっています。</td></tr><tr><td class="hb-lcd-number" rowspan="2">23</td><td class="hb-lcd-icon"><img alt="高温インジケーター" class="hb-lcd-icon-art" src="assets/23_High_Temperature_Indicator_UmkEbOgCKoKyxoxDSINcfO6LnQd.png"/></td><td class="hb-lcd-name">高温インジケーター</td><td class="hb-lcd-description">高温保護が作動しました。製品の温度が通常の動作範囲に戻るまで、製品の機能が停止する場合があります。</td></tr><tr><td class="hb-lcd-icon"><img alt="低温インジケーター" class="hb-lcd-icon-art" src="assets/24_Low_Temperature_Indicator_JDMEbD96noSbyWxbOnVcgip1nab.png"/></td><td class="hb-lcd-name">低温インジケーター</td><td class="hb-lcd-description">低温保護が作動しました。製品の温度が通常の動作範囲に戻るまで、製品の機能が停止する場合があります。</td></tr><tr><td class="hb-lcd-number">24</td><td class="hb-lcd-icon"><img alt="エラーコード" class="hb-lcd-icon-art" src="assets/25_Fault_code_Oz87bX3BGo8H7Zxe0XvcTd7FnJL.png"/></td><td class="hb-lcd-name">エラーコード</td><td class="hb-lcd-description">製品エラーが発生しました。詳細については、トラブルシューティングのセクションを参照してください。</td></tr><tr><td class="hb-lcd-number">25</td><td class="hb-lcd-icon"><img alt="消費電力" class="hb-lcd-icon-art" src="assets/26_Output_Power_PviebR618oofvKxcKVRcHLlInqd.png"/></td><td class="hb-lcd-name">消費電力</td><td class="hb-lcd-description">出力電力をワットで表示します。</td></tr><tr><td class="hb-lcd-number">26</td><td class="hb-lcd-icon"><img alt="バッテリー使用可能時間" class="hb-lcd-icon-art" src="assets/27_Remaining_Discharge_Time_JEpobf59DoBV4dxWlnxcNtIinke.png"/></td><td class="hb-lcd-name">バッテリー使用可能時間</td><td class="hb-lcd-description">接続した機器の使用可能な時間を表示します。</td></tr></tbody></table></figure>

<span id="operations"></span>

## 使い方

### 主電源ボタン/オフ

<figure class="hb-operation-figure hb-operation-layout-footer-panel" data-component-id="HB-SPECIAL-OPERATION" data-operation-id="main-power" data-source-fragment-sha256="67d12cb0cc5ea6ac6eebaa3cdbb5d96b226efb5f1dfd67d20932109519d1a7b0"><div class="hb-operation-stage"><img alt="主電源ボタン" class="hb-operation-art" src="assets/main-power.png"/><div class="line-block hb-operation-steps" data-callout-id="operation.main-power.steps"><div class="hb-operation-step" data-callout-id="operation.main-power.1" data-step-id="1"><div class="line" data-step-id="1" data-step-part="label"><strong>オン</strong></div><div class="line" data-step-id="1" data-step-part="instruction">1回押す</div></div><div class="hb-operation-step" data-callout-id="operation.main-power.2" data-step-id="2"><div class="line" data-step-id="2" data-step-part="label"><strong>オフ</strong></div><div class="line" data-step-id="2" data-step-part="instruction">3秒間長押し</div></div></div></div></figure>

<p>本製品のデフォルトの待機時間は2時間です（充電または放電がない場合、2時間後に自動的にシャットダウンします）。 待機時間はJackeryアプリで設定できます。</p>

<p>省エネモードがオンのとき、AC出力またはDC/USB出力がオンでも、12時間連続して充放電が行われない場合は、自動的に電源がオフになります。</p>

<span id="ac"></span>

### AC出力のオン/オフ

<p>前提：主電源ボタンがオンになっていることを確認してください。</p>

<p>AC1およびAC2電源ボタンは、2組の独立したACコンセントを制御します。 各ボタンを押すと、対応するACコンセントペアのオン/オフが切り替わります。</p>

<figure class="hb-operation-figure hb-operation-layout-footer-panel" data-component-id="HB-SPECIAL-OPERATION" data-operation-id="ac-output" data-source-fragment-sha256="cedd6048ef1b405a34a7c07b5a9011e2a9d1bdc086fcde75a2afc8833fee8173"><div class="hb-operation-stage"><img alt="AC出力" class="hb-operation-art" src="assets/ac-output.png"/><div class="line-block hb-operation-steps" data-callout-id="operation.ac-output.steps"><div class="hb-operation-step" data-callout-id="operation.ac-output.1" data-step-id="1"><div class="line" data-step-id="1" data-step-part="label"><strong>オン</strong></div><div class="line" data-step-id="1" data-step-part="instruction">1回押す</div></div><div class="hb-operation-step" data-callout-id="operation.ac-output.2" data-step-id="2"><div class="line" data-step-id="2" data-step-part="label"><strong>オフ</strong></div><div class="line" data-step-id="2" data-step-part="instruction">1回押す</div></div></div></div></figure>

<span id="50hz60hz"></span>

### 50Hz/60Hz周波数の切り替え:

<p>※ 工場出荷時のデフォルト設定は60Hzに設定されています。自動識別: お客様のお住まいの地域に応じて周波数を自動的に識別し、対応する出力に自動調整されます。手動調整：AC出力がオンの状態で、AC1またはAC2出力ボタンを5秒間長押しすることで周波数を切り替えることができ、対応する周波数が画面に表示されます。</p>

<figure class="hb-reference-figure hb-has-composite-art" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="frequency" data-source-fragment-sha256="5840bfada797f05f5f6b746d11cc849a7a6d0d8d8e6daf53e21c3083d95b7399" data-step-captions="embedded" data-web-composite-asset-key="frozen-source/frequency" data-web-composite-locale="ja" data-web-composite-sha256="192c13b469811a698256498c0c6ada2417424aba4d6351bd971a6cb6e12421c5" data-web-replace-key="reference.frequency"><div aria-hidden="true" class="hb-composite-stage"><img alt="" class="hb-composite-art" loading="lazy" src="assets/frequency.png"/></div><div class="hb-reference-semantic" data-reference-id="frequency.semantic"><img alt="50Hz と 60Hz の表示" class="hb-reference-art hb-composite-art" src="assets/frequency.png"/></div></figure>

<span id="usb"></span>

### USB/カーポート出力オン/オフ

<p>前提：主電源ボタンがオンになっていることを確認してください。</p>

<figure class="hb-operation-figure hb-operation-layout-footer-panel" data-component-id="HB-SPECIAL-OPERATION" data-operation-id="dc-output" data-source-fragment-sha256="01798b928b5b606cf792a3d070f0cbd0f78fc2f04c60309df3a79fe1049b7997"><div class="hb-operation-stage"><img alt="DC/USB出力" class="hb-operation-art" src="assets/dc-output.png"/><div class="line-block hb-operation-steps" data-callout-id="operation.dc-output.steps"><div class="hb-operation-step" data-callout-id="operation.dc-output.1" data-step-id="1"><div class="line" data-step-id="1" data-step-part="label"><strong>オン</strong></div><div class="line" data-step-id="1" data-step-part="instruction">1回押す</div></div><div class="hb-operation-step" data-callout-id="operation.dc-output.2" data-step-id="2"><div class="line" data-step-id="2" data-step-part="label"><strong>オフ</strong></div><div class="line" data-step-id="2" data-step-part="instruction">1回押す</div></div></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ご注意</td><td class="manual-callout-body"><p>USB-C 140W は、USB-PD Power Source 3 (PS3) の高出力ポートです。接続されたユーザーデバイスまたはアクセサリーが安全基準を満たしていない場合、火災の危険性があります。これらのポートを使用する前に、接続するデバイスまたはアクセサリーに耐火安全保護が備わっていることを確認してください。Jackery ポータブル電源 2000 Plus は、IEC/EN/UL 62368-1（または同等の規格）の6.3、6.4、6.5 条に準拠したデバイスまたはアクセサリーのみに接続してください。最大出力を得るためには、USB-C to USB-C 5A ケーブル（20V DC/5A、100W；28V DC/5A、140W）を使用してください。</p></td></tr></tbody></table>

<p>本製品は、別売のJackery 12V 自動車用バッテリー充電ケーブルを使用することで、車のバッテリーへの充電が可能です。</p>

<p>※Jackery 12V 自動車用バッテリー充電ケーブルは付属しておりません。Jackery 公式サイトよりお求めいただけます。</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ご注意</td><td class="manual-callout-body"><p>12V 車専用であり、24V 車には対応しておりません。本製品の12V DC 出力（シガーソケット）から車のバッテリーへ充電中は、エンジンを始動しないでください。製品の故障につながる恐れがあります。この機能はあくまで車のバッテリーの緊急補助用であり、深刻なバッテリー上がりや故障したバッテリーには対応しておりません。</p></td></tr></tbody></table>

### 省エネモード

<p>省エネモードは、出力ボタンの消し忘れによる無駄なバッテリー消耗を防ぐための機能で、初期設定ではオンになっています。AC出力が25W以下、またはDC/USB出力が2W以下の状態が12時間続くと、自動的に出力がオフになります。ACまたはDC/USB出力がオンの状態では、画面に省エネアイコン が表示されます。アイコンの表示時間は、設定された省エネ時間に応じて変わります。</p>

<table class="manual-table"><tbody><tr><th>出力ポートタイプ</th><th>電力設定値</th><th>デフォルト設定</th></tr><tr><td>AC出力ポート</td><td>≤25W</td><td>12時間経つとすべての出力は自動的にオフになります</td></tr><tr><td>DC/USB 出力ポート</td><td>≤2W</td><td>12時間経つとすべての出力は自動的にオフになります</td></tr></tbody></table>

<p>※ 交流25Wおよび直流2W以下の低消費電力機器をご使用の場合、出力が途中で自動的にオフにならないように、省エネモードをオフにしてください。省エネモードをオフにすると、画面上のアイコンは表示されなくなります。</p>

<p>AC出力ボタンがオンの状態で、AC1出力ボタンと主電源ボタンを同時に長押しし、省エネアイコンの表示（オン）／非表示（オフ）が切り替わるまで押し続けてください。</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="energy-saving" data-source-fragment-sha256="e23b44caeb3036674f0c155bff8f4286315f155f564c928839775c4933a497ad" data-web-base-art-ref="energy-saving" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-reference-id="energy-saving.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/energy-saving.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:47.482%;--hb-y:41.3793%;--hb-width:21.5827%;--hb-height:16.3793%">主電源ボタン</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:74.1007%;--hb-y:41.3793%;--hb-width:24.1007%;--hb-height:16.3793%">AC1出力ボタン</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:63.3094%;--hb-y:67.2414%;--hb-width:21.9424%;--hb-height:14.6552%">オン/オフ</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:58.6331%;--hb-y:84.4828%;--hb-width:36.3309%;--hb-height:13.7931%">両方を3秒間長押し</span></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">説明</td><td class="manual-callout-body"><p>省エネモードは電源投入後に前回の状態を維持します。モード変更には手動での切り替えが必要です。</p></td></tr></tbody></table>

<span id="led"></span>

### LEDライト

<p>LEDライトには、照明モードとSOSモードの2つのモードがあります。いずれのモードでも、LEDスイッチを長押しすることでLEDライトを消灯できます。</p>

<figure class="hb-operation-figure hb-operation-layout-footer-panel" data-component-id="HB-SPECIAL-OPERATION" data-operation-id="led-light" data-source-fragment-sha256="85dc14f3ea4beb022419ea58593d8532cec1526ed09fd04cac639980180a6883"><div class="hb-operation-stage"><img alt="LEDライト" class="hb-operation-art" src="assets/led-light.png"/><div class="line-block hb-operation-steps" data-callout-id="operation.led-light.steps"><div class="hb-operation-step" data-callout-id="operation.led-light.1" data-step-id="1"><div class="line" data-step-id="1" data-step-part="label"><strong>1</strong></div><div class="line" data-step-id="1" data-step-part="instruction">LEDスイッチを短く押すとLEDライトが点灯し</div></div><div class="hb-operation-step" data-callout-id="operation.led-light.2" data-step-id="2"><div class="line" data-step-id="2" data-step-part="label"><strong>2 SOS</strong></div><div class="line" data-step-id="2" data-step-part="instruction">再度短く押すとSOSモードに切り替わります。</div></div><div class="hb-operation-step" data-callout-id="operation.led-light.3" data-step-id="3"><div class="line" data-step-id="3" data-step-part="label"><strong>3</strong></div><div class="line" data-step-id="3" data-step-part="instruction">再度短く押すとでライトが消灯します。</div></div></div></div></figure>

<span id="lcd"></span>

### LCDスクリーン

<figure aria-label="LCDスクリーン" class="hb-lcd-mode-composition" data-component-id="HB-TABLE-LCD-MODE"><div class="hb-lcd-mode-art-panel"><img alt="LCDスクリーン" class="hb-lcd-mode-art" src="assets/lcd-mode.png"/></div><div class="hb-lcd-mode-table-panel"><table class="hb-lcd-mode-table"><colgroup><col class="hb-lcd-mode-col-state"/><col class="hb-lcd-mode-col-action"/><col class="hb-lcd-mode-col-copy"/></colgroup><tbody><tr><td class="hb-lcd-mode-state" rowspan="3">短くオン</td><td class="hb-lcd-mode-action">オンにする</td><td class="hb-lcd-mode-copy">主電源ボタンを押すか、充電入力がある場合。</td></tr><tr><td class="hb-lcd-mode-action">オフにする</td><td class="hb-lcd-mode-copy">主電源ボタンを押します。</td></tr><tr><td class="hb-lcd-mode-action">自動オフ</td><td class="hb-lcd-mode-copy">2分後にLCDは自動的に消灯し、スリープモードになります。</td></tr><tr><td class="hb-lcd-mode-state" rowspan="3">常時オン</td><td class="hb-lcd-mode-action">オンにする</td><td class="hb-lcd-mode-copy">デバイスが起動している状態で主電源ボタンを2回押します。</td></tr><tr><td class="hb-lcd-mode-action">オフにする</td><td class="hb-lcd-mode-copy">主電源ボタンを押します。</td></tr><tr><td class="hb-lcd-mode-action">自動オフ</td><td class="hb-lcd-mode-copy">常時点灯ディスプレイモードは、2時間操作がないと自動的に消灯します。</td></tr></tbody></table></div></figure>

<p>Jackeryアプリで画面表示モードを設定することもできます。</p>

### ボタン操作

<figure aria-label="ボタン / 操作 / 機能" class="hb-key-combination-composition" data-component-id="HB-TABLE-KEY-COMBINATIONS" tabindex="0"><table class="hb-key-combination-table"><colgroup><col class="hb-key-col-buttons"/><col class="hb-key-col-operation"/><col class="hb-key-col-function"/></colgroup><thead><tr><th class="hb-key-buttons" scope="col">ボタン</th><th class="hb-key-operation" scope="col">操作</th><th class="hb-key-function" scope="col">機能</th></tr></thead><tbody><tr><td class="hb-key-buttons"><div class="hb-key-button-pair"><span class="hb-key-button"><img alt="" src="assets/power.svg"/><span class="hb-key-button-label">主電源ボタン</span></span><span class="hb-key-button-plus">＋</span><span class="hb-key-button"><img alt="" src="assets/dc_usb.svg"/><span class="hb-key-button-label">DC/USB出力ボタン</span></span></div></td><td class="hb-key-operation"><span class="hb-key-duration" data-duration-icon="clock">両方を3秒間長押し</span></td><td class="hb-key-function">Wi-Fiのリセット</td></tr><tr><td class="hb-key-buttons"><div class="hb-key-button-pair"><span class="hb-key-button"><img alt="" src="assets/power.svg"/><span class="hb-key-button-label">主電源ボタン</span></span><span class="hb-key-button-plus">＋</span><span class="hb-key-button"><img alt="" src="assets/ac1-native.svg"/><span class="hb-key-button-label">AC1出力ボタン</span></span></div></td><td class="hb-key-operation"><span class="hb-key-duration" data-duration-icon="clock">両方を3秒間長押し</span></td><td class="hb-key-function">省エネモードのオン / オフを切り替えます</td></tr><tr><td class="hb-key-buttons"><div class="hb-key-button-pair"><span class="hb-key-button"><img alt="" src="assets/ac1-native.svg"/><span class="hb-key-button-label">AC1出力ボタン</span></span><span class="hb-key-button-plus">＋</span><span class="hb-key-button"><img alt="" src="assets/dc_usb.svg"/><span class="hb-key-button-label">DC/USB出力ボタン</span></span></div></td><td class="hb-key-operation"><span class="hb-key-duration" data-duration-icon="clock">両方を1秒間長押し</span></td><td class="hb-key-function">Wi-Fi＆Bluetooth オン / オフ</td></tr><tr><td class="hb-key-buttons"><div class="hb-key-button-pair"><span class="hb-key-button"><img alt="" src="assets/power.svg"/><span class="hb-key-button-label">主電源ボタン</span></span><span class="hb-key-button-plus">＋</span><span class="hb-key-button"><img alt="" src="assets/led.svg"/><span class="hb-key-button-label">ライトボタン</span></span></div></td><td class="hb-key-operation"><span class="hb-key-duration" data-duration-icon="clock">両方を1秒間長押し</span></td><td class="hb-key-function">緊急充電モードのオン／オフを切り替えます</td></tr></tbody></table></figure>

<span id="acdc"></span>

### ACおよびDC出力の復帰機能

<p>ACおよびDC出力の復帰機能はデフォルトでオフになっています。本機能を使用するには、アプリで有効にしてください。有効にすると、本機はACおよびDCの出力状態を記憶し、所定の条件下でACおよびDC出力を自動的に再開します。</p>

<figure aria-label="自動復帰する条件 / 自動復帰しない条件" class="hb-auto-resume-composition" data-component-id="HB-TABLE-AUTO-RESUME" tabindex="0"><table class="hb-auto-resume-table"><colgroup><col class="hb-auto-resume-col"/><col class="hb-auto-resume-col"/></colgroup><thead><tr><th class="hb-auto-resume-left" scope="col">自動復帰する条件</th><th class="hb-auto-resume-right" scope="col">自動復帰しない条件</th></tr></thead><tbody><tr><td class="hb-auto-resume-left">シャットダウンまたは再起動後の電源オン／再起動</td><td class="hb-auto-resume-right">手動で出力をオフにした場合（ボタン／アプリ）</td></tr><tr><td class="hb-auto-resume-left" rowspan="2">バッテリーSOCが放電制限に達した後、制限値＋10％以上に回復した場合</td><td class="hb-auto-resume-right">省エネモードによる出力オフ</td></tr><tr><td class="hb-auto-resume-right">保護動作による出力オフ</td></tr><tr><td class="hb-auto-resume-left">OTAアップグレード完了後</td><td class="hb-auto-resume-right">放電タイマーによる出力オフ</td></tr></tbody></table></figure>

<span id="ups"></span>

## UPS 機能

<figure class="hb-reference-figure hb-has-composite-art" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ups" data-source-fragment-sha256="90d4ac4c449bf1396f08194d088fdf4a32afdda4df33cfc8e06d77f3f685b74d" data-step-captions="embedded" data-web-composite-asset-key="frozen-source/ups" data-web-composite-locale="ja" data-web-composite-sha256="566fa7fa87f451f2d01f0794280f2ae24dc303031758b24ca975fbf1edd141b8" data-web-replace-key="reference.ups"><div aria-hidden="true" class="hb-composite-stage"><img alt="" class="hb-composite-art" loading="lazy" src="assets/ups.png"/></div><div class="hb-reference-semantic" data-reference-id="ups.semantic"><img alt="UPSの接続方法" class="hb-reference-art hb-composite-art" src="assets/ups.png"/></div></figure>

<p>電気製品のコンセントをポータブル電源のAC 出力ポートに接続し、ポータブル電源のAC入力ポートを家庭のコンセントにつなぐことで、停電時などにポータブル電源を予備電源として活用できます。</p>

<p>本製品は、電気系統（家庭内の電源など）が突然停止した場合、自動的にバッテリー給電モードに切り替わるUPS（無停電電源装置）機能を備えています。切替時間は約10 ミリ秒（0.010 秒）以内です。ただし、本機能は0ms での完全な無停止給電には対応しておりません。そのため、以下のような高精度な連続電源供給を必要とする機器への接続はお控えください。・データサーバー・ワークステーション・医療機器など・その他、停電・瞬断の許容時間が10ms 以下の精密機器/ 業務機器全般</p>

<p>これらの機器でご使用を希望される場合は、事前に複数回の動作テストを実施し、機器との互換性をご確認の上でご使用ください。</p>

<p>※記載の手順に従わずに機器が正常に動作しなかったり、データ消失などの損害が発生した場合、弊社では責任を負いかねます。あらかじめご了承ください。UPS として使用している際はパススルー機能により充電と出力が同時に行われている状態のため、ポータブル電源の最大出力電流は15A に制限され、停電時には定格出力に戻ります。複数の機器をUPS モードで同時に接続する場合は、合計負荷電流が15A を超えないようにしてください。超えると、機器が過負荷保護により停止するおそれがあります。</p>

<span id="connection"></span>

## 接続

### バッテリーパック（別売）に接続

<p>本製品は最大5個のバッテリーパックに対応し、大容量電源のニーズに応えることができます。使用方法の詳細については、Jackery Battery Pack 2000の取扱説明書を参照してください。</p>

<figure class="hb-reference-figure hb-has-composite-art" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="expansion" data-source-fragment-sha256="08eca0e34e041af3f83b91f532138d96f997f99129d6066bc2e2d5a75d8f1d79" data-step-captions="embedded" data-web-composite-asset-key="frozen-source/expansion" data-web-composite-locale="ja" data-web-composite-sha256="ef5a44c3441ef0bc629d9f5787d58185b1210942f43ed357523667a515479a95" data-web-replace-key="reference.expansion"><div aria-hidden="true" class="hb-composite-stage"><img alt="" class="hb-composite-art" loading="lazy" src="assets/expansion.png"/></div><div class="hb-reference-semantic" data-reference-id="expansion.semantic"><img alt="バッテリーパック接続：通気口と物との間は20cm以上" class="hb-reference-art hb-composite-art" src="assets/expansion.png"/></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ご注意</td><td class="manual-callout-body"><p>Battery packを Jackery ポータブル電源 2000 Plus に接続する前に、両方の電源がオフになっていることを確認してください。製品が適切に動作するよう、両側の吸気口と排気口が遮られていないことを確認してください。適切な放熱を確保するため、通気口と物との間に少なくとも20cmの空間を空けてください。製品をバッテリーパックと接続して使用する場合、積み重ねるバッテリーパックの最大数はデフォルトで 3台 とし、製品は平坦で安定しており、十分な耐荷重性のある床面に設置してください。4台以上 のバッテリーパックを積み重ねる必要がある場合は、製品を壁際で外力による衝突を受けにくい安定した場所に設置し、必要な転倒防止固定措置を講じてください。</p></td></tr></tbody></table>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="expansion-accessories" data-source-fragment-sha256="5284c0eaf6df67f4e62e38a562d26d4eab4971f8cf4f4109d408b19fab38f9c7" data-web-base-art-ref="expansion-accessories" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-reference-id="expansion-accessories.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/expansion-accessories.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:0%;--hb-y:66.129%;--hb-width:38%;--hb-height:29.0323%">Jackery Battery Pack 2000</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:41.6667%;--hb-y:66.129%;--hb-width:17.3333%;--hb-height:29.0323%">拡張ケーブル</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:64.3333%;--hb-y:66.129%;--hb-width:16.3333%;--hb-height:29.0323%">取扱説明書</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:85%;--hb-y:22.5806%;--hb-width:15%;--hb-height:40.3226%">（別売）</span></div></div></figure>

<span id="charging"></span>

## 充電方法

<p>グリーンエネルギー優先モード:本製品はグリーンエネルギー優先モードを搭載していますが、ソーラーパネルとAC充電ケーブルを使って同時に充電できます。同時に充電すると、ソーラーが優先されますが、バッテリーの最大許容電力で同時に充電されます。</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ご注意</td><td class="manual-callout-body"><p>製品の充電動作温度範囲は-10°C~45°C、放電動作温度範囲は-10℃~45℃です。上限・下限温度を超えた場合、充放電が制限され、または充放電不可の可能性があります。温度によって、製品の充電効率と実際の容量は異なります。</p></td></tr></tbody></table>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ご注意</td><td class="manual-callout-body"><p>はじめてお使いになるときは、本製品をフル充電してからご使用ください。充電池は空の状態で長期保管(3カ月~6カ月）すると、性能が劣化したり、充電できなくなる場合があります。長期保管中は、電池残量が0％にならないよう、3か月に一度の充電をおすすめします。</p></td></tr></tbody></table>

<span id="ac"></span>

### AC充電ケーブル

<p>コンセントからJackeryポータブル電源2000 Plus本体へ充電する際は、電流容量が大きいため、他の機器との併用や途中での抜き差しはお控えください。コンセントの定格を超えることで充電停止が発生したり、配線やコンセント・接続部の発熱、火災の原因となるおそれがあります。電源タップの使用や他の電気製品との併用は避けてご使用ください。</p>

<figure class="hb-reference-figure hb-has-composite-art" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ac-charge" data-source-fragment-sha256="e7a579088a9c8e4de3515aad5415d2be269d71e4a9b223869af8dfe825a589ea" data-step-captions="embedded" data-web-composite-asset-key="frozen-source/ac-charge" data-web-composite-locale="ja" data-web-composite-sha256="c64cd5f4e83991d30c65d44371f31c949a7f09cb1e53d09035bb038116f0a3e8" data-web-replace-key="reference.ac-charge"><div aria-hidden="true" class="hb-composite-stage"><img alt="" class="hb-composite-art" loading="lazy" src="assets/ac-charge.png"/></div><div class="hb-reference-semantic" data-reference-id="ac-charge.semantic"><img alt="AC充電の接続方法" class="hb-reference-art hb-composite-art" src="assets/ac-charge.png"/></div></figure>

<p>付属のAC充電ケーブルをご使用ください。</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ご注意</td><td class="manual-callout-body"><p>AC充電ケーブルのプラグが製品のAC入力ポートにしっかりと、かつ完全に差し込まれていることを確認してください。差し込みが不完全な場合、電流の不安定、発熱、接触不良などが発生し、機器の正常な動作に支障をきたす恐れがあります。</p></td></tr></tbody></table>

<p>緊急充電モード：ACコンセントからの充電時、お急ぎの場合には緊急充電モードを使って充電することができます。使用するには「Jackery App」でこの機能を「有効」または「無効」に設定してください。緊急充電モードでは、バッテリーの残量(SOC)を示す円形のライトの点滅速度が速くなります。※バッテリーは通常の速度で充電すことでバッテリーを最大限に保護できるよう設計されているため、緊急充電は必要場合にのみ使用し、常時使用することはお勧めしません。</p>

### ソーラー充電

<p>ソーラーパネル接続用のDC入力ポート（8020メス）×2を搭載しており、合計最大入力電力は800Wです。そのため、ソーラーパネル200Wの場合は最大4枚まで。</p>

<p>■ 必要なアクセサリー1枚または2枚接続時：アクセサリー不要、直接本体に接続可能です。4枚接続時：別売りの「SolarSagaアダプター（Pro/Plus/New専用）」を2個ご用意いただく必要があります。※Jackery SolarSagaアダプターを使って3枚接続はできません（電圧が許容範囲を超え、故障のリスクがあります）。</p>

<span id="12"></span>

### ■ 1枚または2枚接続時

<p>直接接続可能です。追加のアクセサリーは不要です。本製品のDC入力ポートは「8020メス」です。ソーラーパネル側の「8020オス」と接続してください。</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="solar-two" data-source-fragment-sha256="43f7e8fcecb62d53dc08e0bc13bb0c8a88f450aa8089bcb1e1c5dea13455b61c" data-web-base-art-ref="solar-two" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-reference-id="solar-two.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/solar-two.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:44.898%;--hb-y:50%;--hb-width:13.6054%;--hb-height:13.6986%">取り外す</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:73.4694%;--hb-y:82.8767%;--hb-width:20.4082%;--hb-height:8.9041%">SolarSaga 200 × 2</span></div></div></figure>

<span id="4"></span>

### ■ 4枚接続時

<p>別売りの「Jackery SolarSaga アダプター(Pro/Plus/New専用)」が必要です。◦「Jackery SolarSaga アダプター(Pro/Plus/New専用)」（オス・メス）とも8020端子です。◦ソーラーパネルの8020オス端子を「Jackery SolarSaga アダプター(Pro/Plus/New専用)」の8020メス端子に接続してください。</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="solar-four" data-source-fragment-sha256="067db09f37420fd173ad05ca373a70e0c4d6f29ac4bddf42819235ac0f91665b" data-web-base-art-ref="solar-four" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-reference-id="solar-four.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ebecec"><img alt="" class="hb-reference-art hb-composite-art" src="assets/solar-four.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:52.9605%;--hb-y:48.3696%;--hb-width:13.1579%;--hb-height:11.413%">取り外す</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:70.3947%;--hb-y:77.7174%;--hb-width:22.0395%;--hb-height:5.9783%">SolarSaga 200 × 4</span><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="2" style="--hb-x:39.9342%;--hb-y:83.5326%;--hb-width:49.2105%;--hb-height:6.413%;--hb-fill:#ffffff">SolarSaga アダプター（Pro/Plus/New専用）別売り</span></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ご注意</td><td class="manual-callout-body"><p>DC入力ポートの電圧を一致させてください2つのDC入力ポートに接続する電源の電圧は必ず一致させてください。電圧が異なると、製品の異常動作や故障の原因となる可能性があります。例：2つのDC8020入力ポートにソーラーパネルを接続する際は、同じ型番のJackery製ソーラーパネルを使用し、接続する枚数も揃えてください。異なる型番や接続枚数で接続すると、電圧が不均一になり、製品が故障するおそれがあります。車載充電器とソーラーパネルを同時に使用して製品を充電しないでください。車のヒューズが切れたり、充電が正常に行われなかったりする可能性があります。</p></td></tr></tbody></table>

<p>Jackeryブランド以外の付属品を使用して充電しないでください。特に、ソーラーパネルで充電する際は、Jackeryのソーラーパネルを使用することをお勧めします。ソーラーパネルの開放電圧（Voc ）が、Jackeryポータブル電源 2000 Plus のDC入力電圧範囲（16V～60V）内に収まっていることを確認してください。他社ソーラーパネルで充電することによる損失について、当社は一切の責任を負いません。</p>

### シガーソケット充電

<p>■本製品は、12V/10A 出力の車載シガーソケットからの充電に対応しています。ご使用の際は、以下にご注意ください：• 必ず車のエンジンを始動させてから接続してください。エンジン停止状態で使用すると、車両のバッテリーが上がる恐れがあります。• 車の充電ポートとシガーソケット充電ケーブルの接触状態をご確認ください。• ケーブルが確実に奥まで差し込まれていることをご確認ください。• 悪路などで車両の振動が激しい場合は、接触不良や発熱・焼損の恐れがあるため、充電を中止してください。• 誤使用による故障・損傷については、弊社では責任を負いかねます。あらかじめご了承ください。</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="car-charge" data-source-fragment-sha256="e7c9160d077ab0750e8b9b554e3acb353d93723d612e5f282c0f912b771d33cb" data-web-base-art-ref="car-charge" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-reference-id="car-charge.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ebecec"><img alt="" class="hb-reference-art hb-composite-art" src="assets/car-charge.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:69.5946%;--hb-y:4.2553%;--hb-width:8.4459%;--hb-height:15.6028%">車</span><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="1" style="--hb-x:50.4392%;--hb-y:78.3688%;--hb-width:45.3041%;--hb-height:10.5674%;--hb-fill:#ffffff">※ シガーソケット充電ケーブルは別売りです。</span></div></div></figure>

<p>※ シガーソケット充電ケーブルは別売りです。</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ご注意</td><td class="manual-callout-body"><p>シガーソケット充電とソーラー充電を同時に使用しないでください。同時に使用すると、車のヒューズが損傷する可能性があります。シガーソケット充電は 12V, 10A 車専用で、24V 車は充電できません。人身傷害や物的損害を避けるため、本製品の充電に 24V 車を使用しないでください。</p></td></tr></tbody></table>

<span id="troubleshooting"></span>

## トラブルシューティング

<p>次のいずれかのエラーコードが表示された場合は、記載されている対処方法に従って問題を解決してください。</p>

<p>問題が解決しない場合は、Jackeryカスタマーサポートまでご連絡ください。</p>

<figure aria-label="エラーコード / 対処方法" class="hb-troubleshooting-composition" data-component-id="HB-TABLE-TROUBLESHOOTING" tabindex="0"><table class="hb-troubleshooting-table"><colgroup><col class="hb-troubleshooting-col-code"/><col class="hb-troubleshooting-col-measures"/></colgroup><thead><tr><th class="hb-troubleshooting-code" scope="col">エラーコード</th><th class="hb-troubleshooting-measures" scope="col">対処方法</th></tr></thead><tbody><tr><td class="hb-troubleshooting-code">F0</td><td class="hb-troubleshooting-measures">製品を再起動してください。</td></tr><tr><td class="hb-troubleshooting-code">F1</td><td class="hb-troubleshooting-measures">製品を再起動してください。</td></tr><tr><td class="hb-troubleshooting-code">F2</td><td class="hb-troubleshooting-measures">製品を再起動してください。</td></tr><tr><td class="hb-troubleshooting-code">F3</td><td class="hb-troubleshooting-measures">製品を再起動してください。</td></tr><tr><td class="hb-troubleshooting-code">F4</td><td class="hb-troubleshooting-measures">製品に負荷を接続してバッテリーを放電し、エラーが消えるまで続けてください。</td></tr><tr><td class="hb-troubleshooting-code">F5</td><td class="hb-troubleshooting-measures">ソーラーパネルまたはAC電源コンセントを使用して、エラーが消えるまで製品を充電してください。</td></tr><tr><td class="hb-troubleshooting-code">F6</td><td class="hb-troubleshooting-measures">1. AC 電源コンセントから充電する前に、電源供給が安定するのを待ってください。2. 吸気口および排気口が塞がれていないか確認し、製品の両側に20cm のスペースを確保してください。3. 製品は日陰で通気の良い場所に設置し、周囲温度が45℃未満であることを確認してください。4. 製品からすべての負荷を取り外し、アイドル状態にして、エラーが消えるまで待ってください。ご使用の機器の起動時消費電力が本製品の出力範囲を超えていないかをご確認ください。5. 製品を再起動してください。</td></tr><tr><td class="hb-troubleshooting-code">F7</td><td class="hb-troubleshooting-measures">1. 製品からすべてのDC入力を取り外してください。2. ソーラーパネルで充電する場合は、接続されたソーラーパネルの開放電圧（Voc）を確認してください。本製品の最大DC入力電圧は60Vです。3. 製品を再起動し、アイドル状態を保ってください。エラーが消えるまで待ってください。</td></tr><tr><td class="hb-troubleshooting-code">F8</td><td class="hb-troubleshooting-measures">販売店またはJackeryカスタマーサポートにお問い合わせください。</td></tr><tr><td class="hb-troubleshooting-code">F9</td><td class="hb-troubleshooting-measures">製品のDC/USB ポートに接続されている負荷を取り外してください。故障が消えるまで待機してください。</td></tr><tr><td class="hb-troubleshooting-code">FC</td><td class="hb-troubleshooting-measures">1. バッテリーパックとポータブル電源 2000 Plus をそれぞれ再起動します。2. 障害が続く場合は、バッテリーパックをポータブル電源 2000 Plus から切断し、再度接続してください。</td></tr><tr><td class="hb-troubleshooting-code">FE</td><td class="hb-troubleshooting-measures">販売店またはJackery カスタマーサポートにお問い合わせください。</td></tr></tbody></table></figure>

<span id="specifications"></span>

## 主な仕様

## 基本情報

<figure aria-label="基本情報" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">製品の名称</th><td class="manual-spec-value hb-spec-value">Jackery ポータブル電源 2000 Plus</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">型番</th><td class="manual-spec-value hb-spec-value">JE-2000E</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">定格容量</th><td class="manual-spec-value hb-spec-value">2048Wh (40Ah/51.2V DC)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">バッテリータイプ</th><td class="manual-spec-value hb-spec-value">LiFePO₄（リン酸鉄リチウムイオン電池）</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">サイクル寿命</th><td class="manual-spec-value hb-spec-value">6000回（6000回の充放電後も容量の70％以上を維持）</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">サイズ＆重量</th><td class="manual-spec-value hb-spec-value">約366×255×272 mm (約18.8 kg）</td></tr></tbody></table></figure>

## 入力ポート

<figure aria-label="入力ポート" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">1×AC入力ポート</th><td class="manual-spec-value hb-spec-value">100V-120V~ 50Hz/60Hz，最大15Aパススルー<sup class="hb-spec-reference">①</sup>：100V-120V~ 50Hz/60Hz，最大15A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2×DC8020入力ポート</th><td class="manual-spec-value hb-spec-value">PV：16V-60V⎓12A, 2ポート最大21A，最大800Wｼｶﾞｰｿｹｯﾄ ：11V-16V⎓最大8A，2ポート最大8A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1×DC拡張ポ一卜（入力）</th><td class="manual-spec-value hb-spec-value">36.8V-57.6V⎓最大75A</td></tr></tbody></table></figure>

## 出力ポート

<figure aria-label="出力ポート" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">4×AC出力ポート</th><td class="manual-spec-value hb-spec-value">100V~ 50Hz/60Hz，最大20A，1ポートあたり定格2000W，合計2400W，瞬間最大4800W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">AC出力（パススルー）<sup class="hb-spec-reference">①</sup></th><td class="manual-spec-value hb-spec-value">100V-120V~ 50Hz/60Hz，最大15A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1×USB-A出力ポート</th><td class="manual-spec-value hb-spec-value">5-6V⎓3A，6-9V⎓2A，9-12V⎓1.5A，最大18W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1×USB-C 30W出力ポート</th><td class="manual-spec-value hb-spec-value">5V⎓3A，9V⎓3A，12V⎓2.5A，15V⎓2A，20V⎓1.5A，最大30W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1×USB-C 140W出力ポート</th><td class="manual-spec-value hb-spec-value">5V⎓3A，9V⎓3A，12V⎓3A，15V⎓3A，20V⎓5A，28V⎓5A，最大140W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">シガーソケット出力</th><td class="manual-spec-value hb-spec-value">12V⎓最大10A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1×DC拡張ポ一卜（出力）</th><td class="manual-spec-value hb-spec-value">36.8V-57.6V⎓最大55A</td></tr></tbody></table></figure>

## 温度範囲

<figure aria-label="温度範囲" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">充電温度</th><td class="manual-spec-value hb-spec-value">-10°C ~ 45°C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">動作温度</th><td class="manual-spec-value hb-spec-value">-10°C ~ 45°C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">保存温度</th><td class="manual-spec-value hb-spec-value">1ヶ月 -20℃ ~ 45℃ ;3ヶ月 0℃ ~ 45℃ ;1年間 0℃ ~ 25℃</td></tr></tbody></table></figure>

<p>※ USB Type-C® and USB-C® are registered trademarks of USB Implementers Forum.</p>

<p>① 本製品は、ACコンセントからバッテリーを充電しながら、AC出力ポートを通じて給電することができます。</p>

<span id="warranty"></span>

## 保証について

<figure aria-label="保証について" class="hb-warranty-intro-composition" data-component-id="HB-WARRANTY-LEAD"><div class="hb-warranty-intro-panel"><p>このたびはJackery 製品をご購入いただき、誠にありがとうございます。本保証書は、Jackery ポータブル電源製品に関する保証内容を明確にご案内するものです。</p></div><div class="hb-warranty-local-note"><p>ご使用前に必ずご確認のうえ、大切に保管してください。</p></div></figure>

### 保証期間

<figure aria-label="保証期間" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="1"><p>本製品の保証期間は以下の通りです。</p><p>・電源本体：ご購入日より3 年間</p><p>・付属品（AC 充電ケーブルなど）：ご購入日より1 年間</p><p>なお、延長保証にご登録いただいた場合、電源本体の保証期間はさらに2 年間延長されます。</p><p>※付属品（AC 充電ケーブルなど）は延長保証の対象外です。</p><p>詳細につきましては、公式サイトをご確認ください。</p></figure>

<figure aria-label="保証期間" class="hb-warranty-period-card" data-component-id="HB-WARRANTY-YEARS"><div class="hb-warranty-period-grid"><div aria-label="3 年間 電源本体" class="hb-warranty-period-item"><div class="hb-warranty-period-heading"><span class="hb-warranty-year-badge">3</span><div class="hb-warranty-period-title"><strong class="hb-warranty-years-unit">年間</strong><strong class="hb-warranty-period-label">電源本体</strong></div></div><div class="hb-warranty-period-copy"><p>ご購入日より3年間</p></div></div><div aria-label="2 年間 延長保証" class="hb-warranty-period-item"><div class="hb-warranty-period-heading"><span class="hb-warranty-year-badge">2</span><div class="hb-warranty-period-title"><strong class="hb-warranty-years-unit">年間</strong><strong class="hb-warranty-period-label">延長保証</strong></div></div><div class="hb-warranty-period-copy"><p>延長保証にご登録いただいた場合、さらに2年間延長</p></div></div></div></figure>

### 保証の適用範囲

<figure aria-label="保証の適用範囲" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="2"><p>1. 購入チャネルについて本保証は、Jackery公式オンラインストアまたは正規代理店で購入された製品に限り有効です。</p><p>※ Jackery 公式オンラインストアまたは正規代理店以外での購入品は保証対象外となります。</p><p>2. 保証提供地域保証は、日本国内に在住の方が、日本国内で使用する場合に限り有効です。</p></figure>

### 保証の適用条件

<figure aria-label="保証の適用条件" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="3"><p>以下のすべての条件を満たす場合に、保証の適用対象となります：</p><p>・Jackery公式オンラインストアまたは正規代理店にてご購入されたこと・保証期間内であること・下記の「保証対象外」に該当しないこと</p></figure>

### 保証対象外となる場合

<figure aria-label="保証対象外となる場合" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="4"><p>以下のいずれかに該当する場合、保証期間内であっても保証の対象外となります：1.故障・損傷が保証期間内に発生していても、保証期間終了後に申請された場合2.使用上の誤り（取扱説明書や本体ラベルに記載の注意事項に従わなかった使用）による故障・損傷3.他機器からの影響、不適切な修理または改造による故障・損傷4.移設・輸送・落下などに起因する故障・損傷5.火災・地震・風水害・落雷などの天災、または公害・塩害・異常電圧などによる故障・損傷6.消耗部品の劣化や摩耗、または外観の汚損など</p></figure>

### 購入証明について

<figure aria-label="購入証明について" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="5"><p>保証をご利用の際には、以下いずれかの購入証明書類をご提示いただく必要があります：・Jackery公式オンラインストアでの購入：注文番号（注文履歴画面または確認メール）・正規代理店での購入：購入日・販売店名の記載された領収書または納品書</p><p>※ ご提示がない場合、保証対応いたしかねます。</p></figure>

### 保証内容

<figure aria-label="保証内容" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="6"><p>1. 初期不良による交換（ご購入日から30日以内）・取扱説明書に従った正常な使用中に不具合が発生した場合、同一製品の新品と交換いたします。・在庫切れや販売終了の場合は、同等品への交換または返金にて対応いたします。</p><p>2. 無償修理（ご購入日から31日以上～保証期間内）・保証条件を満たす自然故障については、無料で修理対応いたします。・修理が困難な場合は、同等品（同モデルまたは同等スペック品）への交換にて対応いたします。</p><p>3. 有償修理以下に該当する場合は、有償での修理対応となります：・保証期間を超えた製品・保証対象外と判断された場合・Jackery公式オンラインストアまたは正規代理店以外で購入された製品有償修理後の保証期間は、修理完了日より90日間です。</p><p>*無償修理の場合、残りの保証期間が90日未満であれば「90日間」、90日以上であれば「元の保証期間に準じます」。</p></figure>

### 免責事項

<figure aria-label="免責事項" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="7"><p>1. 弊社では、いかなる場合においても、間接的損害または付随的損害（データの損失・逸失利益</p><p>など）に対して責任を負いません。</p><p>2. 本保証書は、お客様が法律上有する権利を制限するものではありません。</p><p>3. 保証内容は、予告なく変更される場合がございます。あらかじめご了承ください。</p><p>Jackery 製品を安心してご使用いただくために、本保証書の内容をご確認のうえ、ご活用くださいますようお願いいたします。</p><p>ご不明点がございましたら、Jackery カスタマーサービスまでお問い合わせください。</p></figure>

<p>公式サイト: https://www.jackery.jp</p>

<p>カスタマーサポート: jackery.jp@jackery.com</p>

<p>お問い合わせ電話番号: 050-3198-9007</p>

<span id="app-setup"></span>

## Jackeryアプリ ユーザーマニュアル

<span id="1"></span>

### 1. アプリをダウンロードしてログインするには

<p>Google PlayまたはApp Storeで「Jackery」と検索し、アプリをインストールしてください。その後、登録とログインを行ってください。</p>

<p>または、下の QR コードをスキャンしてアプリをダウンロードし、インストールしてください。</p>

<figure class="hb-reference-figure hb-has-composite-art" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-download" data-source-fragment-sha256="734055530c13d515f76bef9d2eec1598369077635924a8f52d1ce1247f153c16" data-step-captions="embedded" data-web-composite-asset-key="frozen-source/app-download" data-web-composite-locale="ja" data-web-composite-sha256="8aa17f304240e0a4f8db14586e7a14640e83c234540fbd0f86b21c12963f191d" data-web-replace-key="reference.app-download"><div aria-hidden="true" class="hb-composite-stage"><img alt="" class="hb-composite-art" loading="lazy" src="assets/app-download.png"/></div><div class="hb-reference-semantic" data-reference-id="app-download.semantic"><img alt="App Store、Google Play、アプリダウンロードQRコード" class="hb-reference-art hb-composite-art" src="assets/app-download.png"/></div></figure>

<span id="2"></span>

### 2. デバイスを追加するには

<p>2.1 APPの右上にあるデバイス追加ボタン <span aria-label="+" class="hb-inline-add-device-icon" data-component-id="HB-SPECIAL-APP" role="img">+</span> をクリックします。</p>

<p>2.2 デバイスの主電源ボタンを長押しして電源をいれると、ディスプレー画面にWi-FiとBluetoothのアイコンが点滅し、デバイスがネットワーク設定モードに入ったことを示します。アイコン点滅中ボタンをクリックし、アプリが近くのデバイスに接続し、Bluetoothのアクセス許可を開くことを許可します。</p>

<figure class="hb-reference-figure hb-has-composite-art" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-add-phones" data-source-fragment-sha256="ba61f7d8dbfe563061a77c416c016463cdd87af048b620ce7c4b237244e02b0c" data-step-captions="embedded" data-web-composite-asset-key="frozen-source/app-add-phones" data-web-composite-locale="ja" data-web-composite-sha256="f0a6cdc87cd75c0bd86d70b952d054b0fcdab39b8d97641576e95ab4f754064c" data-web-replace-key="reference.app-add-phones"><div aria-hidden="true" class="hb-composite-stage"><img alt="" class="hb-composite-art" loading="lazy" src="assets/app-add-phones.png"/></div><div class="hb-reference-semantic" data-reference-id="app-add-phones.semantic"><img alt="2.1 デバイス追加、2.2 Bluetooth 接続の許可" class="hb-reference-art hb-composite-art" src="assets/app-add-phones.png"/></div></figure>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-control" data-source-fragment-sha256="72c25d7b8aacc6d062916dd77bc8731a55f944f1207231f23e94d27ee980745b" data-web-base-art-ref="app-control" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-reference-id="app-control.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/app-control.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:0.3636%;--hb-y:17.3913%;--hb-width:21.8182%;--hb-height:23.913%">主電源ボタン</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:0.3636%;--hb-y:55.4348%;--hb-width:21.8182%;--hb-height:26.087%">DC/USB出力ボタン</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:81.8182%;--hb-y:30.4348%;--hb-width:17.8182%;--hb-height:22.8261%">AC1出力ボタン</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:81.8182%;--hb-y:55.4348%;--hb-width:17.8182%;--hb-height:23.913%">AC2出力ボタン</span></div></div></figure>

<p>2.3 検出されたデバイスアイコンをクリックすると、アプリは自動的にBluetoothでデバイスを接続します。</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">備考</td><td class="manual-callout-body"><p>バインド処理中に「デバイスがバインドされました」と表示された場合は、以下の2つの方法で接続できます：デバイス所有者は、アプリを通じてこのデバイスを他のユーザーと共有します。主電源ボタンとDC/USB出力ボタンを同時に3秒間押すと、Wi-FiとBluetoothが初期化され。</p></td></tr></tbody></table>

<p>2.4 デバイスが正常に接続されると、デバイスが接続するWi-Fiの名前とパスワードを入力する必要があり、デバイスは自動的にWi-Fiネットワークに接続します。</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">備考</td><td class="manual-callout-body"><p>2.4GHz帯のWi-Fiネットワークを選択してください。デバイスは、5GHz帯のWi-Fiネットワークには対応していません。</p></td></tr></tbody></table>

<p>2.5 デバイスのホーム画面でデバイスが正常に追加されると、デバイスのWi-Fi アイコンは常にオンになります。</p>

<figure class="hb-reference-figure hb-has-composite-art" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-connect" data-source-fragment-sha256="497bb0617ba00d60c302c93db85f4e67effa0b95b887dc40cbb8b4575108baf9" data-step-captions="embedded" data-web-composite-asset-key="frozen-source/app-connect" data-web-composite-locale="ja" data-web-composite-sha256="8309200f5106429e6fa7bfbcb93519c32e7d1d7efc9bc258bc06c4249e4d6cd4" data-web-replace-key="reference.app-connect"><div aria-hidden="true" class="hb-composite-stage"><img alt="" class="hb-composite-art" loading="lazy" src="assets/app-connect.png"/></div><div class="hb-reference-semantic" data-reference-id="app-connect.semantic"><img alt="2.3 Bluetooth 接続、2.4 Wi-Fi 設定、2.5 デバイス追加完了" class="hb-reference-art hb-composite-art" src="assets/app-connect.png"/></div></figure>

<p>上記のスクリーンショットはご参考まで。</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">備考</td><td class="manual-callout-body"><p>Jackeryアプリは、一度に1台のポータブル電源としかBluetooth接続できません。 デバイスリストに戻ると、自動的にBluetoothが切断されます。 リスト内のポータブル電源をもう一度タップすると、自動的に再接続されます。</p></td></tr></tbody></table>

<span id="3"></span>

### 3. デバイスのバインドを解除するには

<p>デバイスのメインインターフェースの右上隅にある「設定」ボタンをクリックして設定ページに入り、ページの下部にある「バインド解除」ボタンをクリックしてデバイスのバインドを解除します。</p>

<span id="4"></span>

### 4. ご確認

<p>4.1 Wi-FiとBluetoothをオンにするには（ディスプレーにWi-FiとBluetoothのアイコンが点灯）：</p>

<p>デバイスがオンになれば自動的にオンになり、ディスプレーにWi-FiとBluetoothのアイコンが点灯します。上記アイコンが点灯しない場合、ディスプレーにWi-FiとBluetoothのアイコンが点灯するまで、DC/USB出力ボタンとAC1出力ボタンを同時長押しします。</p>

<p>4.2 Wi-FiとBluetoothをオフにするには（ディスプレーにWi-FiとBluetoothのアイコンが消える）：</p>

<p>ディスプレーにWi-FiとBluetoothのアイコンが消えるまで、DC/USB出力ボタンとAC1出力ボタンを同時長押しします。</p>

<p>4.3 Wi-FiとBluetoothをリセットするには：</p>

<p>主電源ボタンとDC/USB出力ボタンを同時に3秒間押すと、Wi-FiとBluetoothが初期化され。接続されているはバンド解除されます。</p>

<p>本製品はJackeryアプリケーションによるスマートコントロールに対応しています。ご利用いただくには、下記のアプリストアより「Jackery」で検索して「Jackery アプリ」をダウンロードしてください。</p>

<figure class="hb-reference-figure hb-has-composite-art" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-footer" data-source-fragment-sha256="95fd3cd60a93bca01511d53805bd0ef5df46cab5ce2d7655059adc59885c2554" data-step-captions="embedded" data-web-composite-asset-key="frozen-source/app-footer" data-web-composite-locale="ja" data-web-composite-sha256="ded8a95a733d8c1dc963f372360438f5aac22ad9919bee98a8f8c72a5d9eb0a8" data-web-replace-key="reference.app-footer"><div aria-hidden="true" class="hb-composite-stage"><img alt="" class="hb-composite-art" loading="lazy" src="assets/app-footer.png"/></div><div class="hb-reference-semantic" data-reference-id="app-footer.semantic"><img alt="App Store、Google Play、アプリダウンロードQRコード" class="hb-reference-art hb-composite-art" src="assets/app-footer.png"/></div></figure>
