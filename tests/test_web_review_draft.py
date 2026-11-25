"""Review draft (审核稿) → Web candidate conversion and its release gate."""
import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bs4 import BeautifulSoup

from tests.review_draft_fixture import CARD, CLEAN, DRAFT, write_draft
from tools.manual_ir.hashing import file_sha256
from tools.web import review_draft_web
from tools.web.review_draft_blocks import column_texts, lines_of
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
