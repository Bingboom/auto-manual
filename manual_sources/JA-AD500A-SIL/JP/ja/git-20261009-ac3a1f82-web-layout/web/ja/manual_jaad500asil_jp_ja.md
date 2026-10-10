<style>
/* JA-AD500A-SIL JP Web-layout edition: page-local presentation following the PDF.
   Shared components and web_manual.css stay unchanged; these rules only restyle them. */

/* Print bullets are "・" lines, as in the PDF. */
#furo-main-content ul > li { list-style-type: "・"; }
#furo-main-content ul { padding-left: 1.2rem; }
#furo-main-content ul.jpad-tight { margin: .2rem 0 .5rem; }
#furo-main-content ul.jpad-tight > li > p { margin: 0; }
#furo-main-content p.jpad-hang { padding-left: 1em; text-indent: -1em; }
#furo-main-content p.jpad-small { font-size: .88rem; }

/* p.1: the welcome lead opens the Web edition (the printed cover is not part of it). */
#furo-main-content p.jpad-welcome-lead { margin: 0 0 .3rem; font-size: 1.05rem; }

/* p.5: connection notes keep their print lines; continuation lines are indented. */
#furo-main-content li > .line-block { margin: 0 0 .4rem; }
#furo-main-content li > .line-block > .line + .line { padding-left: .9em; }
#furo-main-content li > .line-block > .line:has(> br:only-child) { height: .45rem; overflow: hidden; }

/* p.5–6: the ご注意 label is large print type; 「例：」 is a bold sub-heading. */
#furo-main-content .manual-callout-label p { font-size: 1.3rem; }
#furo-main-content .manual-callout-body > p > strong { font-size: 1.05rem; }

/* p.6: the five car-charging precautions sit in one grey panel. */
#furo-main-content div.jpad-panel {
  margin: .4rem 0 1.2rem;
  padding: .7rem 1rem .7rem .9rem;
  border-radius: .88rem;
  background: var(--hb-surface);
}
#furo-main-content div.jpad-panel ul { margin: 0; }
#furo-main-content div.jpad-panel li > p { margin: .1rem 0; }

/* p.7: "170 x 90 x 52" keeps the printed letter x (no contextual × substitution). */
#furo-main-content .hb-spec-value { font-variant-ligatures: no-contextual; font-feature-settings: "calt" 0; }

/* p.7: the warranty introduction is one grey panel including its last line. */
#furo-main-content .hb-warranty-intro-panel { border-radius: .88rem .88rem 0 0; padding-bottom: .2rem; }
#furo-main-content .hb-warranty-local-note {
  margin: 0;
  padding: .2rem 1.05rem .9rem;
  border-radius: 0 0 .88rem .88rem;
  background: var(--hb-surface);
  font-size: 1rem;
}
#furo-main-content .hb-warranty-intro-panel p + p,
#furo-main-content .hb-warranty-local-note p { margin-top: .2rem; }

/* p.7–9: notes are grey capsules; 購入チャネルについて keeps its detail line. */
#furo-main-content .hb-warranty-card p.jpad-note {
  display: table;
  margin: .5rem 0 0;
  padding: .2rem .65rem;
  border-radius: .45rem;
  background: var(--hb-surface);
  font-size: .84rem;
}
#furo-main-content .hb-warranty-card li > .line-block { margin: 0; }
#furo-main-content .hb-warranty-card li > .line-block > .line + .line { padding-left: 0; }

/* p.8–9: 保証内容 numbers and remedy headings are bold, each remedy a separate block. */
#furo-main-content figure[aria-label="保証内容"] > ol { padding-left: 1.3rem; }
#furo-main-content figure[aria-label="保証内容"] > ol > li::marker { font-weight: 700; }
#furo-main-content figure[aria-label="保証内容"] > ol > li + li { margin-top: .9rem; }
#furo-main-content figure[aria-label="保証内容"] > ol > li > ul { margin-top: .15rem; }

/* p.9: 免責事項 is a grey panel with a plain bold heading. */
#furo-main-content section:has(> figure[aria-label="免責事項"]) {
  padding-top: 1rem;
  border-color: transparent;
  background: var(--hb-surface);
}
#furo-main-content section:has(> figure[aria-label="免責事項"]) > h2:first-child,
#furo-main-content section:target:has(> figure[aria-label="免責事項"]) > h2:first-child {
  position: static;
  margin: 0 0 .55rem;
  padding: 0;
  background: transparent !important;
  color: var(--hb-text);
  font-size: 1.15rem;
}
#furo-main-content section:has(> figure[aria-label="免責事項"]) > h2:first-child .headerlink { color: var(--hb-text-muted); }
#furo-main-content figure[aria-label="免責事項"] .jpad-closing { margin: 0 0 0 1.3rem; }

/* p.9: the contact lines are bold grey capsules. */
#furo-main-content .hb-manual-page-end p {
  width: fit-content;
  max-width: 100%;
  margin: .45rem 0 0;
  padding: .3rem .8rem;
  border-radius: .45rem;
  background: var(--hb-surface);
  font-weight: 700;
}

</style>

<p class="jpad-welcome-lead"><strong>お買い上げありがとうございます。</strong></p>




<ul class="jpad-tight simple">
<li><p>ご使用の前にこの「取扱説明書」をよくお読みのうえ、正しくお使いください。</p></li>
<li><p>特に「安全上のご注意」は、必ずお読みいただき、安全にお使いください。</p></li>
<li><p>お読みになったあとは、すぐに取り出せる場所に大切に保管してください。</p></li>
<li><p>本製品の取扱説明書は随時更新されますので、最新の取扱説明書は公式サイトでご確認ください。</p></li>
</ul>

# 同梱品

<figure aria-label="同梱品" class="hb-inbox-composition" data-card-count="2" data-component-id="HB-SPECIAL-INBOX" data-inbox-variant="responsive-card-grid"><ol class="hb-inbox-grid"><li class="hb-inbox-card" data-item-number="1"><img alt="本体" class="hb-inbox-art" src="assets/ir/3c140171d4ae33f68026b81db880318d28ccf3ecd4d4d201c0ec9015080db49d/inbox-module.png"/><div class="hb-inbox-label">
<p>本体</p>
</div></li><li class="hb-inbox-card" data-item-number="2"><img alt="取扱説明書" class="hb-inbox-art" src="assets/ir/f01512af441ad341022a4116ac908c865d15f29660688fc2801c8b46c7b4dcfa/inbox-manual.png"/><div class="hb-inbox-label">
<p>取扱説明書</p>
</div></li></ol></figure>




<p><strong>本機の仕様および外観は、改善のため予告なく変更することがあります。</strong></p>

# 各部の名称

<div style="width:min(100%,40rem);margin-inline:auto"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="product-overview" data-source-fragment-sha256="ce934ab4ce71eaa014b8e0698dbe853724b36f83bb4fc6c2faee91db0923e571" data-web-base-art-ref="../../assets/overview-textless.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.product-overview"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="product-overview.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "product-overview", "web_replace_key": "reference.product-overview", "capture_following_lines": 5, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "910a6ce8542f5be9df214a28699b57df6c5abb97c788f1efd72c3b6507f967c2", "panel_top": 0, "panel_fill": "#ffffff", "preserve_frame": true, "mobile_labels": "overlay", "labels": [{"line": 0, "rect": [58, 0.3, 34, 4.2]}, {"line": 1, "rect": [2, 4.5, 90, 4.4]}, {"line": 2, "rect": [32, 8.8, 60, 4.2]}, {"line": 3, "rect": [65, 30.2, 27, 5]}, {"line": 4, "rect": [71, 51.8, 21, 5]}]}}' src="assets/ir/910a6ce8542f5be9df214a28699b57df6c5abb97c788f1efd72c3b6507f967c2/overview-textless.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:58%;--hb-y:0.3%;--hb-width:34%;--hb-height:4.2%"><span style="display:block;width:100%;text-align:right;font-size:clamp(12px,1.2em,18px);line-height:1.15;font-weight:700">DC入力ポート</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:2%;--hb-y:4.5%;--hb-width:90%;--hb-height:4.4%"><span style="display:block;width:100%;text-align:right;font-size:clamp(10px,0.8em,12px);line-height:1.15;color:#8a8a8a">PV：16V-60V⎓最大13A，2ポート最大24A，最大500W</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:32%;--hb-y:8.8%;--hb-width:60%;--hb-height:4.2%"><span style="display:block;width:100%;text-align:right;font-size:clamp(10px,0.8em,12px);line-height:1.15;color:#8a8a8a">ｼｶﾞｰｿｹｯﾄ ：11V-16V⎓最大8A</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:65%;--hb-y:30.2%;--hb-width:27%;--hb-height:5%"><span style="display:block;width:100%;text-align:right;font-size:clamp(12px,1.2em,18px);line-height:1.15;font-weight:700">LEDライト</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:71%;--hb-y:51.8%;--hb-width:21%;--hb-height:5%"><span style="display:block;width:100%;text-align:right;font-size:clamp(12px,1.2em,18px);line-height:1.15;font-weight:700">プラグ</span></span></div></div></figure></div>

<p id="led-light"><strong>LEDライト</strong></p>




<div class="table-wrapper docutils" style="--hb-line-soft:var(--hb-brand-dark);border:1.5px solid var(--hb-brand-dark);border-radius:16px;overflow:hidden;"><table class="manual-table" style="table-layout:fixed;min-width:0!important;">
<colgroup>
<col style="width: 25.0%"/>
<col style="width: 20.0%"/>
<col style="width: 55.0%"/>
</colgroup>
<thead>
<tr><th class="head" scope="col" style="padding:0.25rem 0.6rem!important;text-align:center!important;border-bottom:1px solid var(--hb-line-soft)!important;background:var(--hb-surface-strong)!important;"><p>LEDライトの状態</p></th>
<th class="head" scope="col" style="padding:0.25rem 0.6rem!important;text-align:center!important;border-bottom:1px solid var(--hb-line-soft)!important;background:var(--hb-surface-strong)!important;"><p>ライトの色</p></th>
<th class="head" scope="col" style="padding:0.25rem 0.6rem!important;text-align:center!important;border-bottom:1px solid var(--hb-line-soft)!important;background:var(--hb-surface-strong)!important;"><p>製品の状態</p></th>
</tr>
</thead>
<tbody>
<tr><td style="padding:0.25rem 0.6rem!important;text-align:center!important;"><p>点滅</p></td>
<td style="padding:0.25rem 0.6rem!important;text-align:center!important;"><p>緑色</p></td>
<td style="padding:0.25rem 0.6rem!important;text-align:center!important;"><p>充電中</p></td>
</tr>
<tr><td style="padding:0.25rem 0.6rem!important;text-align:center!important;"><p>点灯</p></td>
<td style="padding:0.25rem 0.6rem!important;text-align:center!important;"><p>赤色</p></td>
<td style="padding:0.25rem 0.6rem!important;text-align:center!important;"><p>異常状態</p></td>
</tr>
<tr><td style="padding:0.25rem 0.6rem!important;text-align:center!important;"><p>点灯</p></td>
<td style="padding:0.25rem 0.6rem!important;text-align:center!important;"><p>緑色</p></td>
<td style="padding:0.25rem 0.6rem!important;text-align:center!important;"><p>接続成功、充電準備完了</p></td>
</tr>
<tr><td style="padding:0.25rem 0.6rem!important;text-align:center!important;"><p>消灯</p></td>
<td style="padding:0.25rem 0.6rem!important;text-align:center!important;"><p>なし</p></td>
<td style="padding:0.25rem 0.6rem!important;text-align:center!important;"><p>電源オフ</p></td>
</tr>
</tbody>
</table></div>

# 接続

<span id="jp-solar-charging"></span>

## ソーラー充電

<p>ソーラーパネル接続用のDC入力ポート（8020メス）×2を搭載しており、合計最大入力電力は500Wです。</p>




<p>■ 必要なアクセサリー</p>




<ul class="jpad-tight simple">
<li><p>1枚または2枚接続時：直接本体に接続可能です。</p></li>
<li><p>4枚接続時：別売りの「SolarSagaアダプター（Pro/Plus/New専用）」を2個ご用意いただく必要があります。</p></li>
</ul>




<p class="jpad-hang">※Jackery SolarSagaアダプターを使って3枚接続はできません（電圧が許容範囲を超え、故障のリスクがあります）。</p>




<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="solar-connection" data-source-fragment-sha256="18e99e15d3199ca456843d250cb4d53f9be9a8d37c64f7692aa000dbc7260299" data-web-base-art-ref="../../assets/solar.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.solar-connection"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="solar-connection.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "solar-connection", "web_replace_key": "reference.solar-connection", "capture_following_lines": 1, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "434a3768abbb54d3f148e55fbe2475ce1a38906a18518ce96f266538e72080d8", "panel_top": 0, "panel_fill": "#ffffff", "preserve_frame": true, "mobile_labels": "overlay", "labels": [{"line": 0, "rect": [76, 68, 12, 3]}]}}' src="assets/ir/434a3768abbb54d3f148e55fbe2475ce1a38906a18518ce96f266538e72080d8/solar.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:76%;--hb-y:68%;--hb-width:12%;--hb-height:3%"><span style="display:block;width:100%;text-align:right;font-size:clamp(10px,0.95em,14px);line-height:1.15">DC8020</span></span></div></div></figure>

<ul>
<li><div class="line-block">
<div class="line">直接接続可能です。</div>
<div class="line">追加のアクセサリーは不要です。</div>
<div class="line">本製品のDC入力ポートは「8020メス」です。ソーラーパネル側の「8020オス」と接続してください。</div>
</div>
</li>
<li><div class="line-block">
<div class="line">別売りの「Jackery SolarSaga アダプター(Pro/Plus/New専用)」が必要です。</div>
<div class="line"><br/></div>
<div class="line">「Jackery SolarSaga アダプター(Pro/Plus/New専用)」（オス・メス）とも8020端子です。</div>
<div class="line">ソーラーパネルの8020オス端子を「Jackery SolarSaga アダプター(Pro/Plus/New専用)」の8020メス端子に接続してください。</div>
</div>
</li>
</ul>




<table class="manual-callout-table" style="width:100%; border-collapse:collapse; margin:0 0 16px 0;"><tbody><tr><td class="manual-callout-label" style="width:16%; border:1px solid #000; padding:6px 8px; vertical-align:top;"><p><strong>ご注意</strong></p></td><td class="manual-callout-body" style="border:1px solid #000; padding:6px 8px; vertical-align:top;"><p>DC入力ポートの電圧を一致させてください2つのDC入力ポートに接続する電源の電圧は必ず一致させてください。電圧が異なると、製品の異常動作や故障の原因となる可能性があります。</p>
<p><strong>例：</strong></p>
<ul class="simple">
<li><p>2つのDC8020入力ポートにソーラーパネルを接続する際は、同じ型番のJackery製ソーラーパネルを使用し、接続する枚数も揃えてください。異なる型番や接続枚数で接続すると、電圧が不均一になり、製品が故障するおそれがあります。</p></li>
<li><p>車載充電器とソーラーパネルを同時に使用して製品を充電しないでください。車のヒューズが切れたり、充電が正常に行われなかったりする可能性があります。</p></li>
</ul>
</td></tr></tbody></table>

<p>Jackeryブランド以外の付属品を使用して充電しないでください。ソーラーパネルの開放電圧（Voc）が、Jackery SlimPower H1 のDC入力範囲（36.8V～56V）または Jackery Battery PackのDC入力範囲（40V～57.6V）内であることを確認してください。他社ソーラーパネルで充電することによる損失について、当社は一切の責任を負いません。</p>




<span id="jp-car-charging"></span>

## シガーソケット充電

<p>Jackery DC Input Moduleに接続することで、Jackery SlimPower H1/Jackery Battery Pack は12V/10A車載充電器で充電できます。</p>




<p><strong>ご使用の際は、以下にご注意ください：</strong></p>




<div class="jpad-panel docutils container">
<ul class="simple">
<li><p>必ず車のエンジンを始動させてから接続してください。エンジン停止状態で使用すると、車両のバッテリーが上がる恐れがあります。</p></li>
<li><p>車の充電ポートとシガーソケット充電ケーブルの接触状態をご確認ください。</p></li>
<li><p>ケーブルが確実に奥まで差し込まれていることをご確認ください。</p></li>
<li><p>悪路などで車両の振動が激しい場合は、接触不良や発熱・焼損の恐れがあるため、充電を中止してください。</p></li>
<li><p>誤使用による故障・損傷については、弊社では責任を負いかねます。あらかじめご了承ください。</p></li>
</ul>
</div>




<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="car-connection" data-source-fragment-sha256="1b24721c23d37addaabddebaa00e2d3db0f972558ef4c9fae4ac3333a02a8312" data-web-base-art-ref="../../assets/car.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.car-connection"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="car-connection.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "car-connection", "web_replace_key": "reference.car-connection", "capture_following_lines": 3, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "29f7b772d7e313cac5527f2d81b82b00716586375fa6bfd562556030a50319fb", "panel_top": 0, "panel_fill": "#ffffff", "preserve_frame": true, "mobile_labels": "overlay", "labels": [{"line": 0, "rect": [69, 26, 10, 4]}, {"line": 1, "rect": [47, 89, 14, 4]}, {"line": 2, "rect": [62, 81.5, 36, 14], "fill": "#f2f3f3"}]}}' src="assets/ir/29f7b772d7e313cac5527f2d81b82b00716586375fa6bfd562556030a50319fb/car.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:69%;--hb-y:26%;--hb-width:10%;--hb-height:4%"><span style="display:block;width:100%;text-align:right;font-size:clamp(10px,0.95em,14px);line-height:1.15">車</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:47%;--hb-y:89%;--hb-width:14%;--hb-height:4%"><span style="display:block;width:100%;text-align:right;font-size:clamp(10px,0.95em,14px);line-height:1.15">DC8020</span></span><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="2" style="--hb-x:62%;--hb-y:81.5%;--hb-width:36%;--hb-height:14%;--hb-fill:#f2f3f3"><span style="display:block;width:100%;text-align:left;padding-left:1em;text-indent:-1em;font-size:clamp(10px,0.95em,14px);line-height:1.15">※ シガーソケット充電ケーブルは別売りです。</span></span></div></div></figure>

<table class="manual-callout-table" style="width:100%; border-collapse:collapse; margin:0 0 16px 0;"><tbody><tr><td class="manual-callout-label" style="width:16%; border:1px solid #000; padding:6px 8px; vertical-align:top;"><p><strong>ご注意</strong></p></td><td class="manual-callout-body" style="border:1px solid #000; padding:6px 8px; vertical-align:top;"><ul class="simple">
<li><p>シガーソケット充電とソーラー充電を同時に使用しないでください。同時に使用すると、車のヒューズが損傷する可能性があります。</p></li>
<li><p>シガーソケット充電は 12V, 10A 車専用で、24V 車は充電できません。人身傷害や物的損害を避けるため、本製品の充電に 24V 車を使用しないでください。</p></li>
</ul>
</td></tr></tbody></table>

# 主な仕様

## 基本情報

<figure aria-label="基本情報" class="hb-spec-table-composition"><table class="manual-spec-table manual-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody>
<tr><th class="manual-spec-label hb-spec-label" scope="row">製品の名称</th><td class="manual-spec-value hb-spec-value">Jackery DC Input Module</td></tr>
<tr><th class="manual-spec-label hb-spec-label" scope="row">型番</th><td class="manual-spec-value hb-spec-value">JA-AD500A-SIL</td></tr>
<tr><th class="manual-spec-label hb-spec-label" scope="row">サイズ＆重量</th><td class="manual-spec-value hb-spec-value">約 170 x 90 x 52 mm (約 0.5kg)</td></tr>
</tbody></table></figure>




## 入力/出カポート

<figure aria-label="入力/出カポート" class="hb-spec-table-composition"><table class="manual-spec-table manual-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody>
<tr><th class="manual-spec-label hb-spec-label" rowspan="2" scope="row">DC 入力</th><td class="manual-spec-value hb-spec-value">11V-16V⎓最大8A</td></tr>
<tr><td class="manual-spec-value hb-spec-value">16V-60V⎓最大13A, 2ポート最大24A，最大500W</td></tr>
<tr><th class="manual-spec-label hb-spec-label" scope="row">DC 出カ</th><td class="manual-spec-value hb-spec-value">42V-58V⎓最大10.7A</td></tr>
</tbody></table></figure>




<p class="jpad-small">本製品はJackery SlimPower H1およびJackery Battery Packとの組み合わせ専用となります。他の機器には接続しないでください。</p>

# 保証について

<figure aria-label="保証について" class="hb-warranty-intro-composition" data-component-id="HB-WARRANTY-LEAD"><div class="hb-warranty-intro-panel"><p>このたびはJackery製品をご購入いただき、誠にありがとうございます。</p>
<p>本保証書は、Jackeryポータブル電源製品に関する保証内容を明確にご案内するものです。</p></div><div class="hb-warranty-local-note"><p>ご使用前に必ずご確認のうえ、大切に保管してください。</p></div></figure>




<section id="section-2">
<h2>保証期間</h2>
<figure aria-label="保証期間" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="1"><p>保証期間はご購入日から1年間です。</p><p class="jpad-hang">※ Jackery公式オンラインストアまたは正規代理店以外での購入品は保証対象外となります。</p></figure>
</section>




<section id="section-3">
<h2>保証の適用範囲</h2>
<figure aria-label="保証の適用範囲" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="2"><ol class="arabic">
<li><div class="line-block">
<div class="line">購入チャネルについて</div>
<div class="line">本保証は、Jackery公式オンラインストアまたは正規代理店で購入された製品に限り有効です。</div>
</div>
</li>
<li><p>保証提供地域保証は、日本国内に在住の方が、日本国内で使用する場合に限り有効です。</p></li>
</ol></figure>
</section>




<section id="section-4">
<h2>保証対象外となる場合</h2>
<figure aria-label="保証対象外となる場合" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="3"><p>以下のいずれかに該当する場合、保証期間内であっても保証の対象外となります：</p><ol class="arabic simple">
<li><p>故障・損傷が保証期間内に発生していても、保証期間終了後に申請された場合</p></li>
<li><p>使用上の誤り（取扱説明書や本体ラベルに記載の注意事項に従わなかった使用）による故障・損傷</p></li>
<li><p>他機器からの影響、不適切な修理または改造による故障・損傷</p></li>
<li><p>移設・輸送・落下などに起因する故障・損傷</p></li>
<li><p>火災・地震・風水害・落雷などの天災、または公害・塩害・異常電圧などによる故障・損傷</p></li>
<li><p>消耗部品の劣化や摩耗、または外観の汚損など</p></li>
</ol></figure>
</section>




<section id="section-5">
<h2>購入証明について</h2>
<figure aria-label="購入証明について" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="4"><p>保証をご利用の際には、以下いずれかの購入証明書類をご提示いただく必要があります：</p><ul class="simple">
<li><p>Jackery公式オンラインストアでの購入：注文番号（注文履歴画面または確認メール）</p></li>
<li><p>正規代理店での購入：購入日・販売店名の記載された領収書または納品書</p></li>
</ul><p class="jpad-note">※ ご提示がない場合、保証対応いたしかねます。</p></figure>
</section>




<section id="section-6">
<h2>保証内容</h2>
<figure aria-label="保証内容" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="5"><ol class="arabic">
<li><p><strong>初期不良による交換</strong>（ご購入日から30日以内）</p>
<ul class="simple">
<li><p>取扱説明書に従った正常な使用中に不具合が発生した場合、同一製品の新品と交換いたします。</p></li>
<li><p>在庫切れや販売終了の場合は、同等品への交換または返金にて対応いたします。</p></li>
</ul>
</li>
<li><p><strong>無償修理</strong>（ご購入日から31日以上～保証期間内）</p>
<ul class="simple">
<li><p>保証条件を満たす自然故障については、無料で修理対応いたします。</p></li>
<li><p>修理が困難な場合は、同等品（同モデルまたは同等スペック品）への交換にて対応いたします。</p></li>
</ul>
</li>
<li><p><strong>有償修理</strong></p>
<p>以下に該当する場合は、有償での修理対応となります：</p>
<ul class="simple">
<li><p>保証期間を超えた製品</p></li>
<li><p>保証対象外と判断された場合</p></li>
<li><p>Jackery公式オンラインストアまたは正規代理店以外で購入された製品</p></li>
</ul>
<p>有償修理後の保証期間は、修理完了日より90日間です。</p>
</li>
</ol><p class="jpad-note">* 無償修理の場合、残りの保証期間が90日未満であれば「90日間」、90日以上であれば「元の保証期間に準じます」。</p></figure>
</section>




<section id="section-7">
<h2>免責事項</h2>
<figure aria-label="免責事項" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="6"><ol class="arabic simple">
<li><p>弊社では、いかなる場合においても、間接的損害または付随的損害（データの損失・逸失利益など）に対して責任を負いません。</p></li>
<li><p>本保証書は、お客様が法律上有する権利を制限するものではありません。</p></li>
<li><p>保証内容は、予告なく変更される場合がございます。あらかじめご了承ください。</p></li>
</ol><div class="jpad-closing line-block">
<div class="line">Jackery製品を安心してご使用いただくために、本保証書の内容をご確認のうえ、ご活用くださいますようお願いいたします。</div>
<div class="line">ご不明点がございましたら、Jackeryカスタマーサービスまでお問い合わせください。</div>
</div></figure>
</section>

<div class="hb-manual-page-end">
<p>公式サイト: <a href="https://www.jackery.jp">https://www.jackery.jp</a></p>
<p>カスタマーサポート: <a href="mailto:jackery.jp@jackery.com">jackery.jp@jackery.com</a></p>
<p>お問い合わせ電話番号: <a href="tel:05031989007">050-3198-9007</a></p>
<div style="width:96px;margin:1rem 0"><img alt="原稿裏表紙のQRコード" src="assets/ir/aaa58d773ab76092d7d3236a2a90ebcad33f992eaeb6491e37bb1c51c5c2ba10/contact-qr.png" style="width:100%;height:auto"/></div>
</div>
