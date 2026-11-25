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
