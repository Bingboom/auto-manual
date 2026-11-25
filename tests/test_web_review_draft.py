"""Review draft (审核稿) → Web candidate conversion and its release gate."""
import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bs4 import BeautifulSoup
from PIL import Image

from tools.manual_ir.hashing import file_sha256
from tools.web import review_draft_web
from tools.web.review_draft_blocks import column_texts, lines_of
from tools.web.review_draft_overlay import strip_review_layer

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


def write_draft(root: Path, html: str = DRAFT, **manifest) -> Path:
    root.mkdir(parents=True)
    (root / "draft.html").write_text(html, encoding="utf-8")
    for shade, name in enumerate(("symbol1", "symbol2", "card1", "card2", "card3", "figure1")):
        _png(root / "assets" / f"{name}.png", 20 * shade)
    (root / "issues.json").write_text(json.dumps({"schema": "review-issues/1", "issues": [
        {"id": "Q1", "title": "open question", "kind": "rd", "status": "open"},
        {"id": "Q2", "title": "settled", "kind": "rd", "status": "confirmed"},
    ]}), encoding="utf-8")
    fields = {"model": "XX-1", "region": "JP", "language": "ja", "version": "v0.02", "date": "2026-11-01",
              "status": "审阅中", "html": "draft.html", "issues": "issues.json", "tools_sha": "1a2b3c4", **manifest}
    (root / "draft.json").write_text(json.dumps(fields, ensure_ascii=False), encoding="utf-8")
    return root


class ReviewLayerTests(unittest.TestCase):
    def test_strips_the_review_layer_and_lists_what_blocks_release(self):
        soup = BeautifulSoup(DRAFT, "html.parser")
        article = soup.select_one("article")
        report = strip_review_layer(article)
        text = article.get_text(" ", strip=True)
        for review_copy in ("安全注意事项", "审阅备注", "新句子", "图注", "XX · JP", "【未入力】"):
            self.assertNotIn(review_copy, text)
        for manual_copy in ("安全上のご注意", "新しい文です。", "注意の本文です。"):
            self.assertIn(manual_copy, text)
        self.assertEqual(report.pending, [{"marker": ".jp-parameter", "text": "【未入力】"}])
        self.assertEqual(report.unreviewed, {"new_translations": 1, "draft_inserts": 0})
        self.assertEqual(report.unmarked["jp-original"], 1)
        self.assertIsNone(article.select_one("[style], [title], [data-previous-english], [lang]"))
        self.assertIsNone(article.select_one(".en-new, .jp-original, .us-review-figure"))


class HelperTests(unittest.TestCase):
    def test_lines_end_at_breaks_and_paragraphs(self):
        cell = BeautifulSoup("<td>一行目<br/>二行目<p>三行目</p></td>", "html.parser").td
        self.assertEqual(lines_of(cell), ["一行目", "二行目", "三行目"])

    def test_column_texts_follow_row_spans(self):
        table = BeautifulSoup(
            "<table><tbody><tr><td>a1</td><td>b1</td></tr><tr><td rowspan='2'>a2</td><td>b2</td></tr>"
            "<tr><td>b3</td></tr><tr><td>a3</td><td>b4</td></tr></tbody></table>", "html.parser").table
        self.assertEqual(column_texts(table, 2), [["a1", "a2", "a3"], ["b1", "b2", "b3", "b4"]])


class ConversionTests(unittest.TestCase):
    def test_candidate_binds_blocks_to_shared_components_and_is_not_releasable(self):
        with TemporaryDirectory() as temp:
            draft = write_draft(Path(temp) / "draft")
            output = Path(temp) / "candidate"
            report = review_draft_web.convert(draft, output, title="テスト取扱説明書")
            self.assertEqual(report["component_inventory"], {
                "HB-CALLOUT-STRIP": 2, "HB-SPECIAL-INBOX": 1, "HB-SPECIAL-REFERENCE-FIGURE": 1,
                "HB-TABLE-SPEC": 1, "HB-TABLE-SYMBOL-ICON": 1, "HB-TABLE-SYMBOL-SIGNAL": 1,
            })
            self.assertEqual(report["shared_style"]["issues"], [])
            self.assertFalse(report["publication_eligible"])
            blockers = "\n".join(report["release_blockers"])
            for expected in ("open issue Q1", "pending marker .jp-parameter", "1 new translations await",
                             "symbol_signal_headers uses fallback copy", "no 定稿 approval", "no web_title",
                             "typeset_compare", "parameter_check"):
                self.assertIn(expected, blockers)
            self.assertNotIn("Q2", blockers)
            ir = json.loads((output / "manual.ir.json").read_text(encoding="utf-8"))
            self.assertEqual(ir["metadata"]["pending_source_review"], report["release_blockers"])
            self.assertFalse(ir["metadata"]["publication_eligible"])
            self.assertEqual(ir["metadata"]["source_authority"]["html_sha256"], file_sha256(draft / "draft.html"))
            markdown = (output / "manual_xx1_jp_ja.md").read_text(encoding="utf-8")
            for manual_copy in ("警告の意味です。", "火災の原因になります。", "品目2", "ケーブルを接続します。", "最大15A"):
                self.assertIn(manual_copy, markdown)
            for review_copy in ("审阅", "新句子", "连接图", "审阅用图", "style="):
                self.assertNotIn(review_copy, markdown)
            self.assertNotIn('src="assets/card', markdown)
            for relative, digest in ir["metadata"]["asset_sha256"].items():
                self.assertEqual(file_sha256(output / relative), digest)

    def test_release_is_refused_while_anything_blocks(self):
        with TemporaryDirectory() as temp:
            draft = write_draft(Path(temp) / "draft")
            with self.assertRaisesRegex(ValueError, "release refused: open issue Q1"):
                review_draft_web.convert(draft, Path(temp) / "out", title="テスト", release=True)
            self.assertFalse((Path(temp) / "out" / "manual.ir.json").exists())
            self.assertIn("open issue Q1 (rd): open question", review_draft_web.gate(draft))

    def test_an_approved_draft_with_evidence_converts_publication_eligible(self):
        with TemporaryDirectory() as temp:
            root = Path(temp) / "draft"
            write_draft(root, CLEAN, issues="", web_title="テスト取扱説明書")
            html_sha = hashlib.sha256((root / "draft.html").read_bytes()).hexdigest()
            for name in ("typeset_compare", "parameter_check"):
                (root / f"{name}.json").write_text(json.dumps({"status": "pass"}), encoding="utf-8")
            manifest = json.loads((root / "draft.json").read_text(encoding="utf-8"))
            manifest.update(approval={"operator": "operator", "date": "2026-11-02", "quote": "定稿",
                                      "html_sha256": html_sha},
                            release_evidence={name: f"{name}.json" for name in ("typeset_compare", "parameter_check")})
            (root / "draft.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(review_draft_web.gate(root), [])
            report = review_draft_web.convert(root, Path(temp) / "release", release=True)
            self.assertTrue(report["publication_eligible"])
            ir = json.loads((Path(temp) / "release" / "manual.ir.json").read_text(encoding="utf-8"))
            self.assertTrue(ir["metadata"]["publication_eligible"])
            self.assertEqual(ir["metadata"]["operator_source_acceptance"]["quote"], "定稿")

    def test_refuses_a_used_output_and_images_outside_the_draft(self):
        with TemporaryDirectory() as temp:
            draft = write_draft(Path(temp) / "draft")
            (Path(temp) / "used").mkdir()
            with self.assertRaisesRegex(ValueError, "unused output"):
                review_draft_web.convert(draft, Path(temp) / "used", title="テスト")
            html = (draft / "draft.html").read_text(encoding="utf-8").replace("assets/figure1.png", "../secret.png")
            (draft / "draft.html").write_text(html, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not a packaged local asset"):
                review_draft_web.convert(draft, Path(temp) / "out", title="テスト")


if __name__ == "__main__":
    unittest.main()
