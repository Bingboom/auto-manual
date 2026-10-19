from __future__ import annotations

import copy
import datetime as dt
import io
import json
import subprocess
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.rtd import web_progress as wp
from tools.rtd.source_registry import load_registry

TODAY = dt.date(2026, 10, 19)
LABELS = {"EU": "欧规", "US": "美规", "JP": "日规", "KR": "韩规"}
ORDER = ["en", "de", "fr", "ja"]
SITE = "https://ht-docs-ht-manuals.readthedocs-hosted.com/en/latest"


def target(model: str, region: str, lang: str, scope: str = "single") -> dict:
    return {"model": model, "region": region, "lang": lang, "route": f"{model}/{region}/{lang}/md",
            "manual": f"manual_{model.lower()}_{region.lower()}_{lang}.md", "language_scope": scope}


def snapshot(**overrides) -> dict:
    value = {"schema": wp.SNAPSHOT_SCHEMA, "exported_at": "2026-10-19", "checked": ["JE-A/EU/en"],
             "sold": {"JE-A": ["EU", "US", "KR"], "JS-B": ["EU"]},
             "timeline": [{"date": "2026-10-01", "added": 2, "langs": 2, "editions": 1, "models": 1},
                          {"date": "2026-10-03", "added": 2, "langs": 4, "editions": 3, "models": 2}]}
    return {**value, **overrides}


def runner(fields: list[str], rows: list[list]):
    def run(args):
        offset = int(args[args.index("--offset") + 1])
        page = rows[offset:offset + 200]
        return {"code": 0, "data": {"fields": fields, "data": page, "total": len(rows), "has_more": False,
                                    "record_id_list": [f"rec{offset + i}" for i in range(len(page))]}}
    return run


class CellTests(unittest.TestCase):
    def test_route_comes_from_the_manual_link(self):
        url = f"{SITE}/JA-AD01A/EU/en/md/manual_jaad01a_eu_en.html"
        self.assertEqual(wp.route_of({"link": url, "text": url}), "JA-AD01A/EU/en")
        self.assertEqual(wp.route_of(f"[{url}]({url})"), "JA-AD01A/EU/en")
        self.assertEqual(wp.route_of(f"{SITE}/JE-3600A/CN/zh/md/manual.html"), "JE-3600A/CN/zh")
        self.assertEqual(wp.route_of("https://example.com/about"), "")
        self.assertEqual(wp.route_of(None), "")

    def test_sku_markets_skip_retired_and_sample_skus(self):
        cell = [{"text": "HTO847A-CA-JAK Jackery 加规 （JA-AD01A) 102W充电器", "type": "text"}, {"text": ","},
                {"text": "HTO728B-US/EU/UK/TW/AU-JAK 美欧英台澳规（JA-CA05B）"},
                {"text": "【停用】HTE099-JP-JAK 日规"}, {"text": "HTO847A-JP-JAK 日规 样品"},
                {"text": "HTE109-PH-JAK 菲律宾"}]
        self.assertEqual(wp.sku_markets(cell), {"US", "EU", "TW", "AU"})
        self.assertEqual(wp.sku_markets("HTO1-KR-JAK 韩规,HTO1-CN-DX2 中规"), {"KR", "CN"})

    def test_checkbox_shapes(self):
        self.assertTrue(wp.is_checked(True))
        self.assertTrue(wp.is_checked("true"))
        self.assertFalse(wp.is_checked(None))
        self.assertFalse(wp.is_checked(False))


class ExportTests(unittest.TestCase):
    FIELDS = ["型号", wp.LINK_FIELD, wp.CHECK_FIELD, wp.SKU_FIELD]

    def test_reads_ticks_and_markets_of_published_models_only(self):
        rows = [
            ["JE-A", {"link": f"{SITE}/JE-A/EU/en/md/manual.html"}, True, [{"text": "HTE1-EU-JAK"}, {"text": "HTE1-CA-JAK"}]],
            ["JE-A", {"link": f"{SITE}/JE-A/EU/de/md/manual.html"}, None, []],
            ["", None, None, [{"text": "HTE9-KR-JAK 未上线"}]],
        ]
        result = wp.export_snapshot(run=runner(self.FIELDS, rows), base_token="b", table_id="t",
                                    timeline=[], today=TODAY)
        self.assertEqual(result["checked"], ["JE-A/EU/en"])
        self.assertEqual(result["sold"], {"JE-A": ["EU", "US"]})
        self.assertEqual(wp.snapshot_problems(result), [])

    def test_refuses_a_table_without_its_columns_or_a_checked_row_without_link(self):
        with self.assertRaisesRegex(RuntimeError, "missing columns"):
            wp.export_snapshot(run=runner(["型号"], [["JE-A"]]), base_token="b", table_id="t", timeline=[], today=TODAY)
        with self.assertRaisesRegex(RuntimeError, "no Web manual link"):
            wp.export_snapshot(run=runner(self.FIELDS, [["JE-A", None, True, []]]), base_token="b", table_id="t",
                               timeline=[], today=TODAY)

    def test_history_dates_each_current_route_by_its_first_name(self):
        with TemporaryDirectory() as temp:
            repo = Path(temp)
            manifest = repo / "docs" / "publish" / "publish_manifest.json"
            manifest.parent.mkdir(parents=True)

            def commit(targets, when):
                manifest.write_text(json.dumps({"targets": targets}), encoding="utf-8")
                env = {"GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when, "GIT_AUTHOR_NAME": "t",
                       "GIT_AUTHOR_EMAIL": "t@example.com", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com",
                       "PATH": "/usr/bin:/bin"}
                subprocess.run(["git", "-C", temp, "add", "-A"], check=True, env=env)
                subprocess.run(["git", "-C", temp, "commit", "-qm", "c"], check=True, env=env)

            subprocess.run(["git", "init", "-q", temp], check=True)
            legacy = dict(target("JE-A", "EU", "en"), route="JE-A/EU/md")
            commit([legacy], "2026-10-01T08:00:00+00:00")
            renamed = dict(target("JE-A", "EU", "en"), legacy_route="JE-A/EU/md")
            commit([renamed, target("JE-A", "US", "en")], "2026-10-03T08:00:00+00:00")
            commit([renamed, target("JE-A", "US", "en"), target("JS-B", "EU", "en")], "2026-10-05T08:00:00+00:00")
            rows = wp.manifest_history(repo)
        self.assertEqual(rows, [
            {"date": "2026-10-01", "added": 1, "langs": 1, "editions": 1, "models": 1},
            {"date": "2026-10-03", "added": 1, "langs": 2, "editions": 2, "models": 1},
            {"date": "2026-10-05", "added": 1, "langs": 3, "editions": 3, "models": 2},
        ])
        self.assertEqual(wp._timeline_problems(rows), [])


class SnapshotTests(unittest.TestCase):
    def test_committed_snapshot_is_sound(self):
        registry, problems = load_registry(wp.ASSETS)
        self.assertEqual(problems, [])
        data, problems = wp.load_snapshot(wp.ASSETS / registry[wp.DOMAIN]["snapshot"])
        self.assertEqual(problems, [])
        self.assertTrue(data["timeline"])

    def test_flags_each_unsound_part(self):
        cases = {
            "schema": dict(schema="other"),
            "ISO date": dict(exported_at="yesterday"),
            "checked must": dict(checked=["not a route"]),
            "sold must": dict(sold={"JE-A": ["XX"]}),
            "follow": dict(timeline=[{"date": "2026-10-03", "added": 1, "langs": 1, "editions": 1, "models": 1},
                                     {"date": "2026-10-01", "added": 1, "langs": 2, "editions": 1, "models": 1}]),
            "whole counts": dict(timeline=[{"date": "2026-10-03", "added": -1, "langs": 1, "editions": 1, "models": 1}]),
        }
        self.assertEqual(wp.snapshot_problems(snapshot()), [])
        for needle, change in cases.items():
            with self.subTest(needle):
                self.assertTrue(any(needle in p for p in wp.snapshot_problems(snapshot(**change))))
        self.assertTrue(wp.snapshot_problems([]))


class ViewTests(unittest.TestCase):
    TARGETS = [target("JE-A", "EU", "en"), target("JE-A", "EU", "de"), target("JS-B", "EU", "en", "legacy_unspecified"),
               target("JE-A", "JP", "ja")]

    def view(self, data=snapshot(), targets=TARGETS):
        return wp.progress_view(targets, data, labels=LABELS, names={("JE-A", "EU"): "Explorer A"},
                                language_order=ORDER, today=TODAY, domain={"label": "网页说明书进度", "stale_after_days": 7})

    def test_cells_count_languages_against_their_market(self):
        view = self.view()
        self.assertEqual([m["code"] for m in view["markets"]], ["EU", "US", "JP", "KR"])
        rows = {row["model"]: {c["market"]: c for c in row["cells"]} for row in view["rows"]}
        self.assertEqual((rows["JE-A"]["EU"]["state"], rows["JE-A"]["EU"]["text"]), ("full", "2/2"))
        self.assertEqual(rows["JE-A"]["EU"]["docname"], "JE-A/EU/en/md/manual_je-a_eu_en")
        self.assertEqual((rows["JS-B"]["EU"]["state"], rows["JS-B"]["EU"]["text"]), ("partial", "1/2"))
        self.assertTrue(rows["JS-B"]["EU"]["legacy"])
        self.assertIn("缺 DE", rows["JS-B"]["EU"]["title"])
        self.assertEqual((rows["JE-A"]["US"]["state"], rows["JE-A"]["KR"]["state"]), ("gap", "gap"))
        self.assertEqual(rows["JE-A"]["JP"]["text"], "1/1")
        self.assertEqual(rows["JS-B"]["US"]["state"], "")
        self.assertEqual(view["rows"][0]["name"], "Explorer A")
        self.assertEqual([c["label"] for c in view["categories"]], ["电源主机", "太阳能板"])

    def test_counts_and_bars(self):
        view = self.view()
        self.assertEqual(view["kpis"], {"models": 2, "editions": 3, "routes": 4, "checked": 1, "gaps": 2, "partial": 1})
        bars = {m["code"]: m for m in view["market_rows"]}
        self.assertEqual((bars["EU"]["full"], bars["EU"]["partial"], bars["EU"]["gap"]), (1, 1, 0))
        self.assertEqual(bars["EU"]["widths"]["full"], 50.0)
        self.assertEqual(bars["KR"]["online"], 0)
        self.assertEqual(len(view["timeline"]), 2)

    def test_without_a_snapshot_only_its_parts_go(self):
        view = self.view(data=None)
        self.assertIsNone(view["kpis"]["gaps"])
        self.assertIsNone(view["kpis"]["checked"])
        self.assertEqual([m["code"] for m in view["markets"]], ["EU", "JP"])
        self.assertEqual(view["timeline"], [])
        self.assertFalse(self.view(targets=None)["available"])

    def test_old_snapshot_reads_as_due_for_review(self):
        stale = wp.progress_view(self.TARGETS, snapshot(exported_at="2026-10-01"), labels=LABELS, names={},
                                 language_order=ORDER, today=TODAY,
                                 domain={"label": "网页说明书进度", "stale_after_days": 7})
        self.assertTrue(stale["stale"])


class CliTests(unittest.TestCase):
    def test_check_reports_the_committed_snapshot(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = wp.main(["check", "--today", "2026-10-19"])
        self.assertEqual(code, 0, out.getvalue())
        self.assertIn("web progress snapshot", out.getvalue())

    def test_check_refuses_an_unsound_file(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "bad.json"
            path.write_text(json.dumps(copy.deepcopy(snapshot(schema="x"))), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(wp.main(["check", "--snapshot", str(path)]), 1)

    def test_export_needs_the_table_coordinates(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = wp.main(["export", "--base-token", "", "--table-id", ""])
        self.assertEqual(code, 1)
        self.assertIn("--base-token", out.getvalue())


if __name__ == "__main__":
    unittest.main()
