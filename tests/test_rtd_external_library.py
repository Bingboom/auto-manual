"""The external library demo reads one snapshot, as of its own date, and renders it as literal text."""
import copy
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import jinja2

from tools.rtd import portal
from tools.rtd.external_library import CONTENT_DIR, SNAPSHOT, library_context

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = json.loads((ROOT / "tests" / "fixtures" / "external_library" / SNAPSHOT).read_text(encoding="utf-8"))
ASSETS = ROOT / "tools" / "rtd_portal_assets"


def write(root: Path, data: dict) -> Path:
    folder = root / CONTENT_DIR
    folder.mkdir(parents=True, exist_ok=True)
    (folder / SNAPSHOT).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return root


def context(data: dict) -> dict:
    with TemporaryDirectory() as temporary:
        return library_context(write(Path(temporary), data))


def product(data: dict, key: str) -> dict:
    return next(item for item in data["competitor"]["products"] if item["id"] == key)


class SnapshotTests(unittest.TestCase):
    def test_the_sample_reads_as_of_its_own_date(self):
        view = context(SAMPLE)
        self.assertEqual(view["summary"], {"competitors": 3, "ends_done": 4, "ends_total": 9, "documents": 5, "todos": 7})
        states = {item["name"]: [(end["name"], end["state"], end["label"]) for end in item["ends"]]
                  for item in view["competitors"]}
        self.assertEqual(states["竞品 B"], [("营销端", "stale", "需更新"), ("软件端", "due-soon", "6 天后到期"),
                                           ("硬件端（拆解）", "overdue", "逾期 1 天")])
        self.assertEqual([end["state"] for end in view["competitors"][2]["ends"]], ["due-soon", "waiting", "waiting"])
        self.assertEqual([step["state"] for step in view["competitors"][0]["steps"]], ["done"] * 6)
        self.assertEqual([step["state"] for step in view["competitors"][2]["steps"]],
                         ["done", "current", "todo", "todo", "todo", "todo"])

    def test_todos_put_what_is_late_first_and_name_who_owes_it(self):
        todos = context(SAMPLE)["todos"]
        self.assertEqual([todo["state"] for todo in todos],
                         ["overdue", "stale", "stale", "pending", "pending", "due-soon", "due-soon"])
        self.assertEqual((todos[0]["what"], todos[0]["who"]), ("竞品 B · 拆解报告", "研发部 王五"))
        self.assertEqual(todos[2]["who"], "行业研究 赵六")

    def test_sources_count_what_each_channel_has_supplied(self):
        counts = {source["name"]: (source["count"], source["status_label"]) for source in context(SAMPLE)["sources"]}
        self.assertEqual(counts["竞品官网"], (10, "在用"))
        self.assertEqual(counts["付费数据接口"], (0, "候选，未接入"))
        self.assertEqual(sum(count for count, _ in counts.values()), 26)

    def test_runs_are_newest_first_and_name_their_job(self):
        runs = context(SAMPLE)["runs"]
        self.assertEqual(runs[0], {"at": "2026-11-04 09:00", "job": "测评文章检索", "result": "找到竞品 B 的新测评 1 篇，生成 1 条待审核"})
        self.assertEqual([run["at"] for run in runs], sorted((run["at"] for run in runs), reverse=True))

    def test_an_earlier_date_changes_the_states_not_the_content(self):
        earlier = copy.deepcopy(SAMPLE)
        earlier["as_of"] = "2026-11-01"
        view = context(earlier)
        self.assertEqual([end["label"] for end in view["competitors"][1]["ends"]], ["已入库", "进行中", "4 天后到期"])
        self.assertEqual(view["summary"]["todos"], 4)

    def test_without_a_snapshot_there_is_no_page(self):
        with TemporaryDirectory() as temporary:
            self.assertIsNone(library_context(Path(temporary)))
        self.assertIsNone(library_context(None))

    def test_malformed_snapshots_name_what_is_wrong(self):
        def broken(change):
            data = copy.deepcopy(SAMPLE)
            change(data)
            return data

        cases = {
            "schema_version": broken(lambda d: d.update(schema_version="external-library/v0")),
            "known source": broken(lambda d: product(d, "competitor-a")["ends"]["marketing"]["findings"][0]
                                   .update(source="nowhere")),
            "stage from the flow": broken(lambda d: product(d, "competitor-a").update(stage="上市")),
            "one entry for each end": broken(lambda d: product(d, "competitor-c")["ends"].pop("hardware")),
            "public HTTPS URL": broken(lambda d: d["industry"]["documents"][0].update(url="http://eur-lex.europa.eu")),
            "unique lower-case ids": broken(lambda d: d["sources"].append(dict(d["sources"][0]))),
            "ISO date": broken(lambda d: product(d, "competitor-b")["ends"]["hardware"].update(due="11月5日")),
            "0-5 rating": broken(lambda d: product(d, "competitor-a")["ends"]["marketing"]["metrics"][0]
                                 .update(rating=9)),
            "known job": broken(lambda d: d["schedule"]["runs"].append({"job": "nowhere", "at": "2026-11-05 09:00",
                                                                        "result": "x"})),
            "known library and status": broken(lambda d: d["schedule"]["jobs"][0].update(status="live")),
        }
        for message, data in cases.items():
            with self.subTest(message), self.assertRaisesRegex(ValueError, message):
                context(data)


class TemplateTests(unittest.TestCase):
    def render(self, data: dict, nav: dict) -> str:
        # Sphinx's template environment does not autoescape; the page escapes every value itself.
        environment = jinja2.Environment(loader=jinja2.FileSystemLoader(ASSETS), autoescape=False)
        environment.globals["pathto"] = lambda name, *args: name
        return environment.get_template("external_library.html").render(**context(data), site_nav=nav)

    def test_snapshot_text_is_rendered_as_text(self):
        hostile = copy.deepcopy(SAMPLE)
        product(hostile, "competitor-a")["name"] = "<script>alert(1)</script>"
        product(hostile, "competitor-a")["ends"]["software"]["findings"][0]["value"] = '"><img src=x onerror=alert(1)>'
        hostile["rules"][0] = "<b>规则</b>"
        page = self.render(hostile, {"library": True})
        for raw in ("<script>alert(1)", "<img src=x", "<b>规则</b>"):
            self.assertNotIn(raw, page)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", page)

    def test_the_page_has_its_four_tabs_and_marks_its_sidebar_entry(self):
        page = self.render(SAMPLE, {"library": True})
        for tab in ("tab-competitor", "tab-industry", "tab-sources", "tab-maintenance"):
            self.assertIn(f'id="{tab}"', page)
        self.assertIn('href="research/external-library" class="app-nav-link active" aria-current="page"', page)
        self.assertNotIn("research/external-library", self.render(SAMPLE, {"library": False}).split("<main")[0])


class PortalTests(unittest.TestCase):
    def app(self, knowledge: Path, flag: str) -> SimpleNamespace:
        return SimpleNamespace(builder=SimpleNamespace(format="html"), config=SimpleNamespace(
            rtd_site_role="combined", rtd_product_intelligence_demo=flag, rtd_knowledge_dir=str(knowledge)))

    def test_the_page_follows_the_research_opt_in_and_skips_a_broken_snapshot(self):
        with TemporaryDirectory() as temporary:
            knowledge = write(Path(temporary), SAMPLE)
            for flag, expected in (("true", True), ("false", False)):
                with self.subTest(flag=flag):
                    app = self.app(knowledge, flag)
                    portal.prepare_library(app)
                    self.assertEqual(portal.library_available(app), expected)
            write(knowledge, {**SAMPLE, "schema_version": "external-library/v0"})
            app = self.app(knowledge, "true")
            with self.assertLogs(level="WARNING") as logs:
                portal.prepare_library(app)
            self.assertFalse(portal.library_available(app))
            self.assertIn("External library demo skipped", "\n".join(logs.output))


if __name__ == "__main__":
    unittest.main()
