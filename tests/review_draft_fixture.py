"""A synthetic review draft (审核稿) for the review-draft Web tests; no business content."""
import json
from pathlib import Path

from PIL import Image

CARD = ('<figure class="jp-inbox-card"><span class="jp-inbox-number">{n}</span>'
        '<div class="jp-inbox-art"><img src="assets/card{n}.png" alt="审阅用图"/></div>'
        '<figcaption>品目{n}</figcaption></figure>')

DRAFT = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>审核稿</title></head><body>
<header class="preview-toolbar">工具栏</header><div class="preview-layout"><aside class="toc"><a href="#safety">目录</a></aside>
<div class="reading-column"><div class="draft-banner"><strong>v0.02</strong></div><p class="print-note">打印说明</p>
<article id="furo-main-content"><nav class="manual-locale-nav"><span>XX · JP</span></nav><div>
<section id="safety"><h1 class="jp-original" data-jp-original-source="t.rst" title="来源">安全上のご注意<span class="zh-translation" lang="zh-CN">安全注意事项</span></h1>
<div class="jp-review" lang="zh-CN"><strong>审阅：</strong>审阅备注<small class="jp-review-source">来源</small></div>
<h2 class="jp-safety-band">絵表示について</h2>
<div class="jp-signal-wrap"><table class="jp-signal-table"><tbody>
<tr class="row-even"><th><p><svg class="jp-alert-icon" viewBox="0 0 1 1"></svg><strong>警告</strong></p></th><td><p>警告の意味です。</p></td></tr>
<tr class="row-odd"><th><p>説明</p></th><td><p>説明の意味です。</p></td></tr></tbody></table></div>
<section id="symbols"><h2 class="jp-safety-band">絵表示の説明</h2><div class="jp-symbol-grid">
<table class="jp-symbol-panel"><tbody><tr><td><img src="assets/symbol1.png" alt="x"/></td><td><p>記号一の説明です。</p></td></tr></tbody></table>
<table class="jp-symbol-panel"><tbody><tr><td><img src="assets/symbol2.png" alt="x"/></td><td><p>記号二の説明です。</p></td></tr></tbody></table></div></section>
<section id="warning"><h2 class="jp-warning-heading"><svg class="jp-alert-icon" viewBox="0 0 1 1"></svg>警告</h2>
<table class="jp-symbol-panel jp-safety-detail"><tbody><tr><td><img src="assets/symbol1.png" alt=""/></td>
<td class="jp-safety-copy"><p>分解しない</p><p>火災の原因になります。</p></td></tr></tbody></table></section>
<table class="manual-callout-table"><tbody><tr><td class="manual-callout-label"><p>注意</p><span class="manual-callout-label-sizer">ご注意</span></td>
<td class="manual-callout-body"><p>注意の本文です。<span class="jp-parameter">【未入力】</span></p></td></tr></tbody></table>
<p class="en-new" data-needs-translation="sentence" data-previous-english="A new sentence." style="color:red">新しい文です。<span class="zh-translation">新句子。</span></p>
</section>
<section id="box"><h1>同梱品</h1><div><div class="jp-inbox-grid">{CARD.format(n=1)}{CARD.format(n=2)}{CARD.format(n=3)}</div></div></section>
<section id="specifications"><h1>主な仕様</h1><div><section><h2>基本情報</h2><figure class="hb-spec-table-composition">
<table class="hb-spec-table manual-table manual-spec-table"><tbody>
<tr><th class="hb-spec-label manual-spec-label">型番</th><td class="hb-spec-value manual-spec-value">XX-1</td></tr>
<tr><th class="hb-spec-label manual-spec-label">入力</th><td class="hb-spec-value manual-spec-value">100V ~ 50/60Hz<br/>最大15A</td></tr>
</tbody></table></figure></section>
<h2>接続図</h2><figure class="us-review-figure"><div class="jp-ts-art"><img src="assets/figure1.png" alt="连接图"/>
<div class="jp-ts-slot jp-ts-caption" style="left:1%"><p>ケーブルを接続します。</p></div></div>
<figcaption class="jp-review">审阅：图注</figcaption></figure></div></section>
</div></article></div></div><details class="change-log"><summary>记录</summary></details><script>void 0</script></body></html>"""

CLEAN = """<!DOCTYPE html><html><body><article id="furo-main-content"><div>
<section id="symbols"><h1>安全上のご注意</h1><h2>絵表示について</h2>
<div class="jp-signal-wrap"><table class="jp-signal-table"><thead><tr><th>表示</th><th>意味</th></tr></thead><tbody>
<tr><th><p><strong>警告</strong></p></th><td><p>警告の意味です。</p></td></tr></tbody></table></div>
<table class="manual-callout-table"><tbody><tr><td class="manual-callout-label"><p>説明</p></td>
<td class="manual-callout-body"><p>説明の本文です。</p></td></tr></tbody></table></section>
</div></article></body></html>"""


# A tiny PNG a single-file draft embeds as a data: URI.
EMBEDDED_PNG = ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")

_ZH = '<span class="zh-translation" lang="zh-CN">中文对照</span>'
_LABEL = '<span class="hb-reference-live-label" data-source-line="{n}" style="--hb-x:{x}%;--hb-y:{y}%;--hb-width:20%;--hb-height:0%{fill}">{text}</span>'

# A newer shell (``main#furo-main-content``) built from rendered shared components.
RENDERED = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>审核稿</title>
<style>.native-dense {{ font-size: 70%; }}</style></head><body>
<main id="furo-main-content"><style>.x {{}}</style>
<aside class="chapter-review review-only review-note">本章审阅备注</aside>
<h1 id="preface" class="hb-preface-heading">IMPORTANT</h1><div class="hb-preface-prose"><p>Read this manual first.{_ZH}</p></div>
<section id="safety"><h1>SAFETY</h1>
<table class="manual-two-col-table" style="width:100%"><tbody><tr><td style="width:50%">
<figure class="hb-symbol-signal-composition hb-safety-instruction"><table class="hb-symbol-signal-table"><tbody><tr>
<td><img src="assets/symbol1.png" alt=""/></td><td><p><strong>INSTRUCTIONS ABOUT RISKS</strong></p></td></tr></tbody></table></figure>
<figure class="hb-symbol-signal-composition hb-safety-lead"><table class="hb-symbol-signal-table"><tbody><tr>
<td class="hb-symbol-signal-label-cell"><span class="hb-signal-badge"><img src="assets/symbol1.png" alt=""/></span></td>
<td class="hb-symbol-signal-meaning-cell"><p><strong>WARNING</strong>{_ZH}</p><p><strong>Follow these precautions.</strong></p></td></tr></tbody></table></figure>
<ul><li>Read the instructions.</li></ul></td>
<td style="width:50%"><ul><li>Keep it dry.<del class="g-rose" title="删除">Struck copy.</del></li></ul></td></tr></tbody></table>
<p data-status="pending-parameters" data-unit-id="T1">Store it for (— months).</p>
<p>Open the <span class="us-parameter">Example App</span><span class="review-pending" title="待确认"> To be confirmed</span>.</p>
<span hidden="">Hidden copy.</span>
<figure aria-label="Signal words" class="hb-symbol-signal-composition" data-component-id="HB-TABLE-SYMBOL-SIGNAL">
<table class="hb-symbol-signal-table"><thead><tr><th class="hb-symbol-signal-label-heading" scope="col">Symbol{_ZH}</th>
<th class="hb-symbol-signal-meaning-heading" scope="col">Meaning</th></tr></thead><tbody>
<tr><td class="hb-symbol-signal-label-cell"><span aria-label="WARNING" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">WARNING</span></span></td>
<td class="hb-symbol-signal-meaning-cell">Severe injury may result.{_ZH}</td></tr>
<tr><td class="hb-symbol-signal-label-cell"><span aria-label="TIP" class="hb-signal-badge"><span class="hb-signal-label">TIP</span></span></td>
<td class="hb-symbol-signal-meaning-cell">Useful information.</td></tr></tbody></table></figure>
<figure aria-label="Safety symbols" class="hb-symbol-pair-composition" data-component-id="HB-TABLE-SYMBOL-ICON"><div class="hb-symbol-pair-grid">
<div class="hb-symbol-panel hb-symbol-panel-1"><table class="hb-symbol-panel-table"><thead><tr><th class="hb-symbol-icon-heading" scope="col">Symbol</th>
<th class="hb-symbol-meaning-heading" scope="col">Meaning</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="Read the manual." class="hb-symbol-art" src="assets/symbol1.png"/></td>
<td class="hb-symbol-meaning">Read the manual.</td></tr></tbody></table></div>
<div class="hb-symbol-panel hb-symbol-panel-2"><table class="hb-symbol-panel-table"><thead><tr><th class="hb-symbol-icon-heading" scope="col">Symbol</th>
<th class="hb-symbol-meaning-heading" scope="col">Meaning</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="Recycle it." class="hb-symbol-art" src="assets/symbol2.png"/></td>
<td class="hb-symbol-meaning">Recycle it.</td></tr></tbody></table></div></div></figure>
</section>
<div class="model-intro"><p>This note applies to both models.</p></div>
<section id="box"><h1>IN THE BOX</h1>
<figure aria-label="IN THE BOX" class="hb-inbox-composition" data-component-id="HB-SPECIAL-INBOX" data-card-count="2"><ol class="hb-inbox-grid">
<li class="hb-inbox-card" data-item-number="1"><img alt="Unit" class="hb-inbox-art" src="assets/card1.png"/><div class="hb-inbox-label"><p>Unit{_ZH}</p></div></li>
<li class="hb-inbox-card" data-item-number="2"><img alt="Cable" class="hb-inbox-art" src="assets/card2.png"/><div class="hb-inbox-label"><p>Cable</p></div></li></ol>
<div class="hb-inbox-tip"><div class="hb-inbox-tip-label"><p>TIP</p></div><div class="hb-inbox-tip-body"><p>Keep the box.</p></div></div></figure>
</section>
<section id="overview"><h1>OVERVIEW</h1>
<div class="native-figure native-overview native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="front" data-web-presentation-mode="base-art-live-copy">
<div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="front.semantic">
<div class="hb-reference-art-panel" style="--hb-panel-top:4%;--hb-panel-fill:#f4f4f4"><img alt="" class="hb-reference-art hb-composite-art" src="assets/figure1.png"/>
{_LABEL.format(n=0, x=12, y=30, fill='', text='<span class="live-label-copy"><b>Power</b> button</span>')}
{_LABEL.format(n=1, x=70, y=55, fill=';--hb-fill:#e0e0e0', text='<span class="ref-change">USB</span> port' + _ZH)}
</div></div></figure></div>
<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="side">
<div class="hb-reference-semantic"><img alt="Side view" class="hb-reference-art hb-composite-art" src="assets/symbol2.png"/><p>The side has two ports.</p></div></figure>
<div class="figure-gloss zh-translation" lang="zh-CN"><div>开机</div></div>
<figure class="magd-figure"><img alt="Embedded view" src="data:image/png;base64,{EMBEDDED_PNG}"/><figcaption class="review-note">临时图</figcaption></figure>
</section>
<section id="operations"><h1>OPERATIONS</h1>
<figure class="hb-operation-figure hb-operation-layout-status-right hb-base-art-live-copy" data-component-id="HB-SPECIAL-OPERATION"
 data-operation-id="main-power" data-web-presentation-mode="base-art-live-copy"><div class="hb-operation-stage"><div class="hb-operation-canvas">
<div class="hb-operation-art-box"><img alt="" class="hb-operation-art" src="assets/card3.png"/>
<div aria-hidden="true" class="hb-operation-duration" style="--hb-x:82%;--hb-y:43%">3s</div></div>
<div class="line-block hb-operation-steps" data-callout-id="operation.main-power.steps">
<div class="hb-operation-step" data-step-id="on" style="--hb-step-x:76.5%;--hb-step-y:21%;--hb-step-width:22.5%">
<div class="line hb-operation-step-label" data-step-part="label" data-source-unit="M1"><strong>On</strong><span class="zh-translation" lang="zh-CN">开机</span></div>
<div class="line hb-operation-step-instruction" data-step-part="instruction">Press once</div></div>
<div class="hb-operation-step" data-step-id="off" style="--hb-step-x:76.5%;--hb-step-y:34%;--hb-step-width:22.5%">
<div class="line hb-operation-step-label" data-step-part="label"><strong>Off</strong></div>
<div class="line hb-operation-step-instruction" data-step-part="instruction">Press and hold for 3s</div></div></div>
<div class="hb-operation-supporting-copy hb-operation-supporting-panels" style="--hb-x:43%;--hb-y:57%;--hb-width:52%">
<div class="line">It turns off after an idle period.</div></div></div></div></figure>
<figure aria-label="Buttons" class="hb-key-combination-composition" data-component-id="HB-TABLE-KEY-COMBINATIONS"><table class="hb-key-combination-table"><thead><tr>
<th class="hb-key-buttons" scope="col">Buttons</th><th class="hb-key-operation" scope="col">Operation</th><th class="hb-key-function" scope="col">Function</th></tr></thead><tbody>
<tr><td class="hb-key-buttons"><div class="hb-key-button"><img alt="" src="assets/symbol1.png"/><p>A button</p></div></td><td class="hb-key-operation"><span class="hb-key-duration spec-value">3s</span><p>Hold for 3s</p></td><td class="hb-key-function">Saves energy</td></tr>
<tr><td class="hb-key-buttons">B button</td><td class="hb-key-operation">Hold</td><td class="hb-key-function">Resets the network</td></tr>
<tr><td class="hb-key-buttons">C button</td><td class="hb-key-operation">Press</td><td class="hb-key-function">Turns the light on</td></tr></tbody></table></figure>
<figure aria-label="Resume" class="hb-auto-resume-composition" data-component-id="HB-TABLE-AUTO-RESUME"><table class="hb-auto-resume-table"><thead><tr>
<th class="hb-auto-resume-left" scope="col">Resumes</th><th class="hb-auto-resume-right" scope="col">Does not resume</th></tr></thead><tbody>
<tr><td class="hb-auto-resume-left">After a restart</td><td class="hb-auto-resume-right">Manual off</td></tr>
<tr><td class="hb-auto-resume-left" rowspan="2">After charging</td><td class="hb-auto-resume-right">Saving mode off</td></tr>
<tr><td class="hb-auto-resume-right">Protection off</td></tr>
<tr><td class="hb-auto-resume-left">After an update</td><td class="hb-auto-resume-right">Timer off</td></tr></tbody></table></figure>
</section>
<section id="fcc"><h1>FCC</h1>
<figure aria-label="FCC" class="hb-fcc-composition" data-component-id="HB-SPECIAL-FCC"><div class="hb-fcc-grid"><div class="hb-fcc-column hb-fcc-column-left">
<div class="hb-fcc-opening"><img alt="FCC" class="hb-fcc-mark" src="assets/symbol2.png"/><div class="hb-fcc-opening-copy"><div class="line-block">
<div class="line">This device complies with the rules.</div><div class="line">(1) It causes no interference.</div></div></div></div>
<p><strong>NOTE:</strong> This equipment was tested.</p></div>
<div class="hb-fcc-column hb-fcc-column-right"><p>Try these measures:</p><ul class="simple"><li><p>Move the antenna.</p></li><li><p>Use another outlet.</p></li></ul>
<p><strong>MODIFICATION:</strong> Changes void the authority.</p></div></div></figure>
</section>
<section id="app"><h1>APP</h1>
<figure aria-label="Download the App" class="hb-app-download-composition" data-component-id="HB-SPECIAL-APP"><div class="hb-app-download-grid">
<div class="hb-app-download-column hb-app-download-column-store"><div class="hb-app-download-art-frame"><img alt="" class="hb-app-download-art hb-app-download-art-store" src="assets/card1.png"/></div>
<div class="hb-app-download-copy hb-app-download-copy-store"><p>Search the store.</p></div></div>
<div class="hb-app-download-column hb-app-download-column-qr"><div class="hb-app-download-art-frame"><img alt="" class="hb-app-download-art hb-app-download-art-qr" src="assets/card2.png"/></div>
<div class="hb-app-download-copy hb-app-download-copy-qr"><p>Or scan the code.</p></div></div></div>
<div class="hb-app-download-semantic"><img alt="Download panel" class="hb-app-download-semantic-art" src="assets/figure1.png"/></div></figure>
<p>2. Tap <span aria-label="+" class="hb-inline-add-device-icon" data-component-id="HB-SPECIAL-APP" role="img">+</span> to add the device.</p>
</section>
<section id="warranty"><h1>WARRANTY</h1>
<figure aria-label="Warranty Period" class="hb-warranty-period-card" data-component-id="HB-WARRANTY-YEARS"><div class="hb-warranty-period-grid">
<div class="hb-warranty-period-item"><div class="hb-warranty-period-heading"><span class="hb-warranty-year-badge">3</span><div class="hb-warranty-period-title">
<strong class="hb-warranty-years-unit">YEARS</strong><strong class="hb-warranty-period-label">Standard</strong></div></div>
<div class="hb-warranty-period-copy">The standard period is 36 months.</div></div></div></figure>
<h2>Exclusions</h2><figure aria-label="Exclusions" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION">The warranty does not cover:{_ZH}<ul><li>Misuse.</li><li>Accidents.</li></ul></figure>
</section>
<section id="review-appendix" class="review-note review-appendix"><section class="issue" id="Q01"><h3>Q01</h3><span class="pending">已定</span></section></section>
</main></body></html>"""


def _png(path: Path, shade: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (6, 4), (shade, 40, 90)).save(path)


def write_draft(root: Path, html: str = DRAFT, *, issues: bool = True, **manifest) -> Path:
    root.mkdir(parents=True)
    (root / "draft.html").write_text(html, encoding="utf-8")
    for shade, name in enumerate(("symbol1", "symbol2", "card1", "card2", "card3", "figure1")):
        _png(root / "assets" / f"{name}.png", 20 * shade)
    fields = {"model": "XX-1", "region": "JP", "language": "ja", "version": "v0.02", "date": "2026-11-01",
              "status": "审阅中", "html": "draft.html", "tools_sha": "1a2b3c4", **manifest}
    if issues:
        (root / "issues.json").write_text(json.dumps({"schema": "review-issues/1", "issues": [
            {"id": "Q1", "title": "open question", "kind": "rd", "status": "open"},
            {"id": "Q2", "title": "settled", "kind": "rd", "status": "confirmed",
             "resolution": {"by": "R&D", "date": "2026-11-02", "evidence": "reply"}},
        ]}), encoding="utf-8")
        fields.setdefault("issues", "issues.json")
    (root / "draft.json").write_text(json.dumps(fields, ensure_ascii=False), encoding="utf-8")
    return root
