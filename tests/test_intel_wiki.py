"""The Markdown view is rebuilt from the intake, literal, linkable by file name and never edits people's files."""
import contextlib
from copy import deepcopy
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.intel import cli, wiki
from tools.intel.events import CONTENT_DIR, EVENTS_FILE, encode_intake, events_snapshot

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "external_intel" / "events.json"
US = "us-outage-resilience-research"
NL = "nl-self-consumption-research"
POLICY = {"id": "nl-net-metering", "status": "verified", "change": "荷兰 2027 年起取消净计量。", "boundary": "不等于必须配储。",
          "reviewed": "2026-10-06", "sources": [{"kind": "official", "title": "荷兰政府", "url": "https://www.government.nl/n",
                                                "note": "核对结束日期"}]}


def fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def view(data: dict | None = None, policies=(POLICY,)) -> dict[str, str]:
    return wiki.wiki_pages(events_snapshot(encode_intake(data or fixture()), list(policies)))


def frontmatter(page: str) -> dict:
    head = page.split("---\n")[1]
    return {key: json.loads(value) for key, value in (line.split(": ", 1) for line in head.splitlines())}


def us_event(**changes) -> dict:
    data = fixture()
    data["events"][1]["revisions"][-1].update(changes)
    return data


class PageTests(unittest.TestCase):
    def test_every_page_is_generated(self):
        self.assertEqual(sorted(view()), sorted([
            "wiki/index.md", "wiki/overview.md", "wiki/log.md", f"wiki/events/{US}.md", f"wiki/events/{NL}.md",
            "wiki/markets/market-nl.md", "wiki/markets/market-us.md"]))

    def test_pages_are_deterministic(self):
        reordered = fixture()
        reordered["events"].reverse()
        self.assertEqual(view(), view())

        def unsourced(pages):
            return {path: "\n".join(line for line in page.splitlines() if not line.startswith("source_sha256:"))
                    for path, page in pages.items()}
        # Only the intake file's own hash may follow its byte order.
        self.assertEqual(unsourced(view(reordered)), unsourced(view()))
        self.assertNotEqual(frontmatter(view(reordered)["wiki/overview.md"])["source_sha256"],
                            frontmatter(view()["wiki/overview.md"])["source_sha256"])

    def test_event_page_carries_the_decision_sources_judgment_and_history(self):
        page = view()[f"wiki/events/{US}.md"]
        meta = frontmatter(page)
        self.assertEqual((meta["type"], meta["id"], meta["decision_state"], meta["related"]),
                         ("event", US, "pending", ["market-us"]))
        self.assertTrue(meta["sources"] and all(url.startswith("https://") for url in meta["sources"]))
        self.assertIn("市场变化 · [[market-us|US]] · 事件要点已核实 · 发生／生效 2024-06-01", page)
        self.assertIn("## 需要决策\n\n是否按州、负载和停电时长分组，启动美国家庭备电需求验证？", page)
        self.assertIn("- 决策人：待指派\n- 截止：未设定\n- 状态：待决策", page)
        self.assertIn("](<https://www.eia.gov/todayinenergy/detail.php?id=66744>)（官方来源 · 核实 2026-10-20", page)
        self.assertIn("## 人工判断\n\n待人工判断。", page)
        self.assertEqual(page.count("\n| "), 2 + len(fixture()["events"][1]["revisions"]))

    def test_policy_events_show_the_joined_policy_facts(self):
        page = view()[f"wiki/events/{NL}.md"]
        self.assertIn("荷兰 2027 年起取消净计量。", page)
        self.assertEqual(frontmatter(page)["policy_record"], "nl-net-metering")
        self.assertIn("来源资料缺失", view(policies=())[f"wiki/events/{NL}.md"])

    def test_judged_events_quote_the_judgment(self):
        review = {"status": "reviewed", "decision": "先按州收集停电数据", "reviewed_by": "李四", "reviewed_on": "2026-10-22"}
        pages = view(us_event(review=review))
        self.assertIn("> 先按州收集停电数据\n>\n> — 李四，2026-10-22", pages[f"wiki/events/{US}.md"])
        self.assertIn("判断：先按州收集停电数据（李四，2026-10-22）", pages["wiki/overview.md"])
        self.assertEqual(frontmatter(pages["wiki/overview.md"])["reviewed"], 1)

    def test_intake_text_cannot_add_markup_links_or_tags(self):
        hostile = "# 标题 [[index|首页]] [链接](https://evil.example) <b>粗</b> #标签 $x$ %%隐藏%% ==亮== `码` - 列"
        data = fixture()
        data["events"][1]["title"] = hostile
        data["events"][1]["revisions"][-1].update(summary=hostile, boundary="1. " + hostile,
                                                  hypotheses=["- " + hostile], reason=hostile)
        for path, page in view(data).items():
            body = page.split("---\n", 2)[2]
            with self.subTest(path):
                for raw in ("[[index|首页]]", "[链接](https", "<b>", " #标签", "$x$", "%%隐藏", "==亮", "`码`"):
                    self.assertNotIn(raw, body)
                for link in body.split("[[")[1:]:
                    target, _, rest = link.partition("]]")
                    self.assertEqual(target.count("|"), 1, target)
        page = view(data)[f"wiki/events/{US}.md"]
        self.assertIn("\\# 标题 \\[\\[index\\|首页\\]\\]", page)
        self.assertIn("\n1\\. \\# 标题", page)
        self.assertIn("[[" + US + "|＃ 标题 ［［index｜首页］］ ［链接］(https://evil.example) ＜b＞粗＜/b＞ ＃标签 ＄x＄ "
                      "％％隐藏％％ ＝＝亮＝＝ ｀码｀ - 列]]", view(data)["wiki/index.md"])

    def test_unsafe_source_urls_are_never_links(self):
        source = {"kind": "brief", "title": "传闻", "url": "https://ok.example/a", "checked_on": "2026-10-20",
                  "note": "线索"}
        data = us_event(status="unverified", sources=[source])
        snapshot = events_snapshot(encode_intake(data), [POLICY])
        snapshot["events"][1 if snapshot["events"][1]["id"] == US else 0]["sources"][0]["url"] = "javascript:alert(1)"
        page = wiki.wiki_pages(snapshot)[f"wiki/events/{US}.md"]
        self.assertIn("- 传闻（链接不可用）（二手资料 · 核实 2026-10-20） — 线索", page)
        self.assertNotIn("javascript:", page)
        self.assertEqual(frontmatter(page)["sources"], [])

    def test_the_view_holds_no_product_data(self):
        text = "\n".join(view().values())
        for term in ("product_lens\"", "required_capabilities", "UPS功能", "catalog_markets", "capacity_wh"):
            self.assertNotIn(term, text)

    def test_page_names_are_unique_across_the_view(self):
        for name in ("index", "purpose", "market-us"):
            data = fixture()
            data["events"][0]["id"] = name
            with self.subTest(name), self.assertRaisesRegex(ValueError, "collide"):
                view(data)

    def test_market_pages_group_spellings_and_stay_safe_file_names(self):
        self.assertEqual(wiki.market_page("NL"), "market-nl")
        self.assertEqual(wiki.market_page("../../etc/passwd"), "market-etc-passwd")
        self.assertEqual(wiki.market_page("荷兰 / 比利时"), "market-荷兰-比利时")
        self.assertRegex(wiki.market_page("!!!"), r"^market-[0-9a-f]{8}$")
        data = fixture()
        data["events"][0]["market"] = "us"
        pages = view(data)
        self.assertNotIn("wiki/markets/market-nl.md", pages)
        self.assertEqual(frontmatter(pages["wiki/markets/market-us.md"])["markets"], ["US", "us"])

    def test_log_lists_every_revision_newest_first_with_a_greppable_heading(self):
        log = view()["wiki/log.md"]
        headings = [line for line in log.splitlines() if line.startswith("## [")]
        revisions = sum(len(case["revisions"]) for case in fixture()["events"])
        self.assertEqual(len(headings), revisions)
        self.assertEqual([line[4:14] for line in headings], sorted((line[4:14] for line in headings), reverse=True))
        self.assertTrue(any(heading.endswith(" · r1") and "] 录入 | " in heading for heading in headings))

    def test_overview_puts_pending_decisions_in_decision_order(self):
        overview = view(us_event(decide_by="2026-11-01"))["wiki/overview.md"]
        self.assertLess(overview.index(f"[[{US}|"), overview.index(f"[[{NL}|"))
        self.assertIn("  - 需要决策：", overview)
        self.assertEqual(frontmatter(overview)["pending"], 2)


class WriteTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / CONTENT_DIR
        self.pages = view()

    def write(self, pages=None):
        pages = pages or self.pages
        changes = wiki.plan(self.root, pages)
        wiki.apply(self.root, pages, changes)
        return changes

    def test_a_written_view_plans_no_changes(self):
        changes = self.write()
        self.assertEqual((sorted(changes["write"]), changes["templates"]), (sorted(self.pages), ["purpose.md", "schema.md"]))
        self.assertEqual(wiki.plan(self.root, self.pages), {"write": [], "delete": [], "templates": []})
        self.assertEqual((self.root / "wiki/index.md").read_text(encoding="utf-8"), self.pages["wiki/index.md"])

    def test_stale_generated_pages_go_and_other_files_stay(self):
        self.write()
        for path in ("wiki/events/retired.md", "wiki/markets/market-old.md", "wiki/queries/saved-answer.md",
                     "wiki/sources/clipping.md", "wiki/events/picture.png"):
            (self.root / path).parent.mkdir(parents=True, exist_ok=True)
            (self.root / path).write_text("kept?", encoding="utf-8")
        changes = self.write()
        self.assertEqual(changes["delete"], ["wiki/events/retired.md", "wiki/markets/market-old.md"])
        self.assertTrue(all((self.root / path).exists() for path in (
            "wiki/queries/saved-answer.md", "wiki/sources/clipping.md", "wiki/events/picture.png")))

    def test_templates_are_created_once_and_never_overwritten(self):
        self.write()
        (self.root / "purpose.md").write_text("# 我们的目的\n", encoding="utf-8")
        self.write()
        self.assertEqual((self.root / "purpose.md").read_text(encoding="utf-8"), "# 我们的目的\n")
        self.assertIn("type: \"schema\"", (self.root / "schema.md").read_text(encoding="utf-8"))

    def test_an_edited_page_is_planned_and_restored(self):
        self.write()
        (self.root / "wiki/overview.md").write_text("hand edit", encoding="utf-8")
        self.assertEqual(self.write()["write"], ["wiki/overview.md"])
        self.assertEqual((self.root / "wiki/overview.md").read_text(encoding="utf-8"), self.pages["wiki/overview.md"])


class CliTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.knowledge = Path(temp.name)
        self.folder = self.knowledge / CONTENT_DIR
        self.folder.mkdir()
        (self.folder / EVENTS_FILE).write_bytes(FIXTURE.read_bytes())

    def main(self, *flags):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = cli.main(["wiki", "--knowledge-dir", str(self.knowledge), *flags])
        return code, stream.getvalue()

    def test_dry_run_lists_pages_and_writes_nothing(self):
        code, output = self.main()
        self.assertEqual(code, 0)
        self.assertIn("wiki: 7 pages, 7 to write, 0 to remove; missing templates: purpose.md, schema.md", output)
        self.assertIn("dry run; add --write to write the view", output)
        self.assertFalse((self.folder / "wiki").exists() or (self.folder / "purpose.md").exists())

    def test_check_fails_until_written_and_after_a_hand_edit(self):
        self.assertEqual(self.main("--check")[0], 1)
        self.assertEqual(self.main("--write")[0], 0)
        code, output = self.main("--check")
        self.assertEqual((code, output.splitlines()[-1]), (0, "  up to date"))
        (self.folder / "wiki" / "log.md").write_text("edited", encoding="utf-8")
        self.assertEqual(self.main("--check")[0], 1)
        data = fixture()
        data["events"][0]["title"] = "荷兰净计量终止（标题更新）"
        (self.folder / EVENTS_FILE).write_bytes(encode_intake(data))
        code, output = self.main("--check")
        self.assertEqual(code, 1)
        self.assertIn(f"  write   wiki/events/{NL}.md", output)

    def test_no_intake_is_nothing_to_generate_and_a_bad_one_is_an_error(self):
        (self.folder / EVENTS_FILE).unlink()
        self.assertEqual(self.main("--write"), (0, f"wiki: nothing to generate without {self.folder / EVENTS_FILE}\n"))
        self.assertFalse((self.folder / "wiki").exists())
        (self.folder / EVENTS_FILE).write_text("{", encoding="utf-8")
        code, output = self.main("--write")
        self.assertEqual(code, 1)
        self.assertIn("ERROR   cannot build the wiki view", output)

    def test_write_and_check_are_exclusive(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.main("--write", "--check")

    def test_unchanged_data_regenerates_byte_for_byte(self):
        self.main("--write")
        before = {path: path.read_bytes() for path in sorted((self.folder / "wiki").rglob("*.md"))}
        self.main("--write")
        self.assertEqual({path: path.read_bytes() for path in sorted((self.folder / "wiki").rglob("*.md"))}, before)
        self.assertEqual(deepcopy(before), before)


if __name__ == "__main__":
    unittest.main()
