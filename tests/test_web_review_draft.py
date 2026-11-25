"""Review draft (审核稿) → Web candidate conversion and its release gate."""
import base64
import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bs4 import BeautifulSoup

from tests.review_draft_fixture import CARD, CLEAN, DRAFT, EMBEDDED_PNG, RENDERED, write_draft
from tools.manual_ir.hashing import file_sha256
from tools.web import review_draft_web
from tools.web.review_draft_blocks import DraftChapter, column_texts, lcd_icon_tables, lines_of, spec_tables
from tools.web.review_draft_changes import CHANGES_JSON, changes_record, compare, pages_of, previous_version
from tools.web.review_draft_overlay import strip_review_layer

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


class NewerShellLayerTests(unittest.TestCase):
    def test_renderer_attributes_survive_only_inside_components(self):
        root = BeautifulSoup(
            '<main><figure data-component-id="X" aria-label="A" style="--hb-x:1%" data-v12="1">'
            '<span class="hb-reference-live-label ref-change" style="--hb-y:2%">copy</span></figure>'
            '<p aria-label="B" style="color:red">plain <span class="us-parameter">value</span></p>'
            '<p data-status="pending-parameters">(— months)</p><p><span class="v004-pending">later</span></p>'
            '<div data-art-status="first-generation-reference-only"><img alt="Old art" src="a.png"/></div>'
            '<del>struck</del><span hidden="">hidden</span><aside class="chapter-review review-only">note</aside></main>',
            "html.parser").main
        report = strip_review_layer(root)
        figure = root.figure
        self.assertEqual((figure["data-component-id"], figure["aria-label"], figure["style"]), ("X", "A", "--hb-x:1%"))
        self.assertNotIn("data-v12", figure.attrs)
        self.assertEqual((figure.span["class"], figure.span["style"]), (["hb-reference-live-label"], "--hb-y:2%"))
        self.assertIsNone(root.select_one("p[aria-label], p[style], .ref-change, .us-parameter"))
        self.assertEqual([row["marker"] for row in report.pending],
                         ["pending parameters", "reference-only artwork", "copy to confirm (.v004-pending)"])
        self.assertEqual(report.pending[1]["text"], "Old art")
        for gone in ("struck", "hidden", "note"):
            self.assertNotIn(gone, root.get_text())


class HelperTests(unittest.TestCase):
    def test_lines_end_at_breaks_and_paragraphs(self):
        cell = BeautifulSoup("<td>一行目<br/>二行目<p>三行目</p></td>", "html.parser").td
        self.assertEqual(lines_of(cell), ["一行目", "二行目", "三行目"])

    def test_lcd_rows_keep_spanned_numbers_and_descriptions(self):
        chapter = DraftChapter(root=BeautifulSoup(
            '<h1>LCD</h1><figure class="hb-lcd-table-composition"><table class="hb-lcd-icon-table"><tbody>'
            '<tr><td class="hb-lcd-number" rowspan="2">1</td><td><img src="a.png" alt=""/></td>'
            '<td class="hb-lcd-name">Wi-Fi</td><td class="hb-lcd-description" rowspan="2">Connected</td></tr>'
            '<tr><td><img src="b.png" alt=""/></td><td class="hb-lcd-name">Bluetooth</td></tr>'
            '</tbody></table></figure>', "html.parser"), page_id="lcd", language="en", image_key_prefix="XX/US")
        lcd_icon_tables(chapter)
        spec = chapter.claims[0].spec
        self.assertEqual(spec.metadata, {"number_cell_layout": "span-adjacent-equal",
                                         "description_cell_layout": "span-adjacent-equal"})
        self.assertEqual([row["description_text"] for row in spec.slot("rows").content], ["Connected", "Connected"])

    def test_tables_without_their_own_heading_or_two_columns_are_declared(self):
        chapter = DraftChapter(root=BeautifulSoup(
            '<h1>Specs</h1><figure class="hb-spec-table-composition"><table class="hb-spec-table"><tbody>'
            '<tr><th>Weight</th><td>1 kg</td></tr></tbody></table></figure>'
            '<h2>Compare</h2><figure class="hb-spec-table-composition"><table class="manual-spec-table">'
            '<thead><tr><th></th><th>A</th><th>B</th></tr></thead><tbody><tr><th>Size</th><td>1</td><td>2</td></tr>'
            '</tbody></table></figure>', "html.parser"), page_id="specs", language="en", image_key_prefix="XX/US")
        spec_tables(chapter)
        self.assertEqual(chapter.claims, [])
        self.assertEqual([row["reason"].split(":")[0] for row in chapter.exceptions],
                         ["Label/value table without its own section heading",
                          "Specification-style table with a header row or more than two columns"])

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
            write_draft(root, CLEAN, issues=False, web_title="テスト取扱説明書")
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


class RenderedShellTests(unittest.TestCase):
    """A newer shell copies the published Web manual: its blocks are rendered shared components."""

    def test_rendered_components_are_read_back_into_shared_specs(self):
        with TemporaryDirectory() as temp:
            draft = write_draft(Path(temp) / "draft", RENDERED, language="en", region="US")
            output = Path(temp) / "candidate"
            report = review_draft_web.convert(draft, output, title="Test manual")
            self.assertEqual(report["component_inventory"], {
                "HB-CALLOUT-STRIP": 1, "HB-SPECIAL-APP": 2, "HB-SPECIAL-FCC": 1, "HB-SPECIAL-INBOX": 1,
                "HB-SPECIAL-OPERATION": 1, "HB-SPECIAL-REFERENCE-FIGURE": 3, "HB-TABLE-AUTO-RESUME": 1,
                "HB-TABLE-KEY-COMBINATIONS": 1, "HB-TABLE-SYMBOL-ICON": 1, "HB-TABLE-SYMBOL-SIGNAL": 1,
                "HB-WARRANTY-SECTION": 1, "HB-WARRANTY-YEARS": 1,
            })
            self.assertEqual(report["shared_style"]["issues"], [])
            # a preface heading opens its own page; a loose note joins the next chapter
            self.assertEqual(report["pages"], ["preface", "safety", "box", "overview", "operations", "fcc", "app",
                                               "warranty"])
            markdown = (output / "manual_xx1_us_en.md").read_text(encoding="utf-8")
            for manual_copy in ("Read this manual first.", "INSTRUCTIONS ABOUT RISKS", "Follow these precautions.",
                                "This note applies to both models.", "Severe injury may result.", "Keep the box.",
                                "The side has two ports.", "Hold for 3s", "MODIFICATION:", "Or scan the code.",
                                "The warranty does not cover:", "Misuse.", "The standard period is 36 months."):
                self.assertIn(manual_copy, markdown)
            for review_copy in ("中文对照", "审阅", "Struck copy.", "Hidden copy.", "开机", "临时图", "已定", "data:image"):
                self.assertNotIn(review_copy, markdown)
            # live labels keep the rectangles, pill tone and panel the base-art renderer wrote
            for placement in ("--hb-x:12%;--hb-y:30%;--hb-width:20%;--hb-height:0%", "--hb-fill:#e0e0e0",
                              "--hb-panel-top:4%;--hb-panel-fill:#f4f4f4"):
                self.assertIn(placement, markdown)
            blockers = "\n".join(report["release_blockers"])
            for expected in ("copy to confirm: To be confirmed", "pending parameters: Store it for",
                             "figure front renders without the dense label type",
                             "operation main-power renders without its Web presentation"):
                self.assertIn(expected, blockers)
            embedded = hashlib.sha256(base64.b64decode(EMBEDDED_PNG)).hexdigest()
            ir = json.loads((output / "manual.ir.json").read_text(encoding="utf-8"))
            self.assertIn(f"assets/ir/{embedded}/image.png", ir["metadata"]["asset_sha256"])

    def test_changes_read_the_newer_shell(self):
        head = RENDERED.replace("Useful information.", "Helpful information.")
        pages = compare(pages_of(RENDERED), pages_of(head))
        self.assertEqual([(page["page_id"], [change["kind"] for change in page["changes"]]) for page in pages],
                         [("safety", ["changed"])])


class ChangesTests(unittest.TestCase):
    def test_compare_reports_changed_added_and_removed_blocks(self):
        head = (DRAFT.replace("警告の意味です。", "警告の意味を示します。")
                .replace('<p class="en-new"', '<p>追加の段落です。</p><p class="en-new"')
                .replace(CARD.format(n=3), ""))
        pages = compare(pages_of(DRAFT), pages_of(head))
        kinds = [(page["page_id"], change["kind"]) for page in pages for change in page["changes"]]
        self.assertEqual(kinds, [("safety", "changed"), ("safety", "added"),
                                 ("box", "removed"), ("box", "removed"), ("box", "removed")])
        changed = pages[0]["changes"][0]
        self.assertEqual(changed["segments"], [["=", "警告の意味"], ["-", "で"], ["+", "を示しま"], ["=", "す。"]])
        self.assertEqual([change["before"] for change in pages[1]["changes"]], ["3", "［図］card3.png", "品目3"])
        self.assertNotIn("审阅备注", json.dumps(pages, ensure_ascii=False))  # the review layer never counts

    def test_previous_version_is_the_newest_commit_naming_another_version(self):
        with TemporaryDirectory() as temp:
            top = Path(temp).resolve()
            relative = "docs/review-drafts/XX-1/JP"
            line = write_draft(top / relative, issues=False, version="v0.03")
            calls = {
                ("rev-parse", "--show-toplevel"): f"{top}\n",
                ("log", "--format=%H", "--", f"{relative}/draft.json"): "c3\nc2\nc1\n",
                ("show", f"c3:{relative}/draft.json"): json.dumps({"version": "v0.03", "html": "draft.html"}),
                ("show", f"c2:{relative}/draft.json"): json.dumps({"version": "v0.02", "html": "draft.html"}),
                ("show", f"c2:{relative}/draft.html"): DRAFT.replace("警告の意味です。", "警告の意味です（旧）。"),
            }

            def git(args, cwd):
                # The top-level lookup runs in the line; history reads run at the top.
                self.assertEqual(Path(cwd).resolve(), line.resolve() if args[0] == "rev-parse" else top)
                return calls[tuple(args)]

            self.assertEqual(previous_version(line, git=git)[0], "c2")
            record = changes_record(line, git=git)
            self.assertEqual(record["base"], {"version": "v0.02", "from": "git c2"})
            self.assertEqual(record["head"]["version"], "v0.03")
            self.assertEqual(record["counts"], {"changed": 1, "added": 0, "removed": 0})

    def test_changes_command_writes_the_record_beside_the_draft(self):
        with TemporaryDirectory() as temp:
            line = write_draft(Path(temp) / "line", issues=False, version="v0.03")
            previous = write_draft(Path(temp) / "previous", DRAFT.replace("品目2", "品目二"), issues=False, version="v0.02")
            self.assertEqual(review_draft_web.main(["changes", str(line), "--base-dir", str(previous), "--write"]), 0)
            record = json.loads((line / CHANGES_JSON).read_text(encoding="utf-8"))
            self.assertEqual((record["base"]["version"], record["base"]["from"]), ("v0.02", "directory"))
            self.assertEqual(record["counts"]["changed"], 1)


if __name__ == "__main__":
    unittest.main()
