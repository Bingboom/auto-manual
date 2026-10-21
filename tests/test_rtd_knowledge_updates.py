from __future__ import annotations

import datetime as dt
import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from tools.rtd import knowledge_updates as ku
from tools.rtd import design_system, market_policy, product_learning, product_matrix
from tools.rtd.deliverables import DELIVERABLES_PAGE
from tools.rtd.portal import ASSETS
from tools.rtd.system_workspace import SYSTEM_PAGE

SHIPPED = yaml.safe_load((ASSETS / ku.UPDATES_NAME).read_text(encoding="utf-8"))
_EVIDENCE = re.compile(r"pr:[a-z][a-z-]*#[1-9][0-9]*")


def entry(page="system", date=dt.date(2026, 10, 1), title="T", note="N", **extra):
    return {"date": date, "title": title, "note": note, "page": page, **extra}


class LoadUpdatesTests(unittest.TestCase):
    def load(self, data):
        with TemporaryDirectory() as temp:
            text = data if isinstance(data, str) else yaml.safe_dump(data, allow_unicode=True)
            (Path(temp) / ku.UPDATES_NAME).write_text(text, encoding="utf-8")
            return ku.load_updates(Path(temp))

    def test_shipped_file_is_sound_dated_and_evidenced(self):
        entries, problems = ku.load_updates(ASSETS)
        self.assertEqual(problems, [])
        self.assertEqual(len(entries), len(SHIPPED["updates"]))
        templates = "".join(path.read_text(encoding="utf-8") for path in ASSETS.glob("*.html"))
        for raw in SHIPPED["updates"]:
            with self.subTest(raw["title"]):
                # The merge day, unquoted so YAML reads a date; never a timestamp.
                self.assertIs(type(raw["date"]), dt.date)
                refs = raw["evidence"] if isinstance(raw["evidence"], list) else [raw["evidence"]]
                self.assertTrue(refs)
                for ref in refs:
                    self.assertRegex(ref, _EVIDENCE)
                if raw.get("anchor"):
                    self.assertIn(f'id="{raw["anchor"]}"', templates)

    def test_page_keys_name_the_pages_the_portal_builds(self):
        self.assertEqual(ku.PAGES, {
            "share": None, "product-knowledge": product_learning.PAGE, "product-matrix": product_matrix.PAGE,
            "market-policy": market_policy.PAGE, "deliverables": DELIVERABLES_PAGE, "system": SYSTEM_PAGE,
            "design-system": design_system.PAGE,
        })

    def test_bad_entries_are_dropped_and_undated_ones_kept(self):
        entries, problems = self.load({"schema": ku.UPDATES_SCHEMA, "updates": [
            entry(title="kept", anchor="work-map"),
            entry(page="matrix", title="unknown page"),
            entry(page=["system"], title="unhashable page"),
            entry(title="  "),
            entry(title="no note", note=""),
            entry(title="bad anchor", anchor="Work Map"),
            "not a mapping",
            entry(title="quoted date", date="2026-10-01"),
            entry(title="timestamp", date=dt.datetime(2026, 10, 1, 9, 30)),
            entry(title="no date", date=None),
        ]})
        self.assertEqual([(e["title"], e["date"], e["anchor"]) for e in entries], [
            ("kept", "2026-10-01", "work-map"), ("quoted date", "", ""), ("timestamp", "", ""), ("no date", "", ""),
        ])
        self.assertEqual(len(problems), 9)
        for wanted in ("updates[1] (unknown page): unknown page 'matrix'", "updates[2] (unhashable page): unknown page",
                       "updates[3]: needs title", "updates[4] (no note): needs note",
                       "updates[5] (bad anchor): anchor 'Work Map'", "updates[6] is not a mapping",
                       "updates[7] (quoted date): date '2026-10-01' is not an unquoted YYYY-MM-DD"):
            self.assertTrue(any(problem.startswith(wanted) for problem in problems), wanted)
        self.assertTrue(all("日期未记录" in problem for problem in problems[-3:]))

    def test_unreadable_file_or_wrong_shape_gives_no_entries(self):
        with TemporaryDirectory() as temp:
            entries, problems = ku.load_updates(Path(temp))
        self.assertEqual(entries, [])
        self.assertIn(f"cannot read {ku.UPDATES_NAME}", problems[0])
        for data, reason in (("updates: [unclosed", "cannot read"),
                             ({"schema": "other/v1", "updates": []}, "schema is 'other/v1'"),
                             (["not", "a", "mapping"], "schema is None"),
                             ({"schema": ku.UPDATES_SCHEMA, "updates": {"a": 1}}, "updates must be a list")):
            with self.subTest(reason):
                entries, problems = self.load(data)
                self.assertEqual(entries, [])
                self.assertEqual(len(problems), 1)
                self.assertIn(reason, problems[0])


class UpdatesViewTests(unittest.TestCase):
    def entries(self, *raws):
        with TemporaryDirectory() as temp:
            (Path(temp) / ku.UPDATES_NAME).write_text(
                yaml.safe_dump({"schema": ku.UPDATES_SCHEMA, "updates": list(raws)}, allow_unicode=True),
                encoding="utf-8")
            entries, _ = ku.load_updates(Path(temp))
        return entries

    def test_newest_first_ties_in_file_order_undated_last(self):
        entries = self.entries(entry(title="undated", date=None), entry(title="old", date=dt.date(2026, 9, 1)),
                               entry(title="tie-a"), entry(title="new", date=dt.date(2026, 10, 9)),
                               entry(title="tie-b"))
        view = ku.updates_view(entries, dict.fromkeys(ku.PAGES, True))
        self.assertEqual([row["title"] for row in view], ["new", "tie-a", "tie-b", "old", "undated"])
        self.assertEqual(view[0], {"date": "2026-10-09", "title": "new", "note": "N", "page": "system",
                                   "docname": SYSTEM_PAGE, "anchor": ""})

    def test_hides_unbuilt_pages_and_keeps_the_newest_limit(self):
        entries = self.entries(*(entry(page="system", title=f"s{day}", date=dt.date(2026, 10, day))
                                 for day in range(1, 11)),
                               entry(page="share", title="share", date=dt.date(2026, 10, 20)),
                               entry(page="product-matrix", title="matrix", date=dt.date(2026, 10, 21)))
        built = {**dict.fromkeys(ku.PAGES, True), "product-matrix": False}
        view = ku.updates_view(entries, built)
        self.assertEqual([row["title"] for row in view], ["share", "s10", "s9", "s8", "s7", "s6", "s5", "s4"])
        self.assertIsNone(view[0]["docname"])
        self.assertEqual([row["title"] for row in ku.updates_view(entries, built, limit=2)], ["share", "s10"])
        self.assertEqual(ku.updates_view(entries, {}), [])


class HomeTemplateTests(unittest.TestCase):
    def render(self, **context):
        base = {"share_entry": "", "system_entry": True, "deliverables_entry": True, "design_entry": True,
                "matrix_entry": True, "updates": []}
        template = Environment(loader=FileSystemLoader(ASSETS)).get_template("workspace_portal.html")
        page = template.render(**{**base, **context}, pathto=lambda name, *args: name)
        return BeautifulSoup(page, "html.parser")

    def test_cards_follow_the_entries_and_carry_no_numbers(self):
        soup = self.render(matrix_entry=False, system_entry=False)
        groups = [(s.h2.text, [c.strong.text for c in s.select(".home-card")]) for s in soup.select(".home-group")]
        self.assertEqual(groups, [("产品与市场", ["产品知识", "市场与政策"]),
                                  ("说明书生产", ["说明书工作台", "设计规范"])])
        self.assertFalse(re.search(r"\d", "".join(c.text for c in soup.select(".home-card"))))
        self.assertIsNone(soup.select_one("#shares"))

    def test_rows_link_their_page_and_undated_rows_say_so(self):
        updates = [{"date": "2026-10-04", "title": "工作入口", "note": "n", "page": "deliverables",
                    "docname": DELIVERABLES_PAGE, "anchor": "work-map"},
                   {"date": "2026-09-22", "title": "分享", "note": "n", "page": "share", "docname": None, "anchor": ""},
                   {"date": "", "title": "无日期", "note": "n", "page": "system", "docname": SYSTEM_PAGE, "anchor": ""}]
        soup = self.render(share_entry="../ai-share/00_打开分享.html", updates=updates)
        rows = soup.select("#updates .updates-list > a")
        self.assertEqual([a["href"] for a in rows],
                         [f"{DELIVERABLES_PAGE}#work-map", "../ai-share/00_打开分享.html", SYSTEM_PAGE])
        self.assertEqual([a.time["datetime"] for a in rows[:2]], ["2026-10-04", "2026-09-22"])
        self.assertIsNone(rows[2].time)
        self.assertEqual(rows[2].select_one(".updates-undated").text, "日期未记录")
        self.assertIsNotNone(soup.select_one("#shares .share-card"))

    def test_no_rows_shows_the_empty_note(self):
        soup = self.render()
        self.assertIsNone(soup.select_one("#updates .updates-list"))
        self.assertEqual(soup.select_one("#updates .updates-empty").text, "暂无更新记录。")


if __name__ == "__main__":
    unittest.main()
