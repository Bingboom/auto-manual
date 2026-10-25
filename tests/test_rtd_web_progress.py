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
from tools.rtd import web_reviews as wr
from tools.rtd.source_registry import load_registry

TODAY = dt.date(2026, 10, 19)
LABELS = {"EU": "欧规", "US": "美规", "JP": "日规", "KR": "韩规"}
ORDER = ["en", "de", "fr", "ja"]
SITE = "https://ht-docs-ht-manuals.readthedocs-hosted.com/en/latest"
REVIEW_SITE = "https://ht-docs-review-doc-lib.readthedocs-hosted.com"
BASE_URL = "https://tenant.feishu.cn/wiki/node"
REVIEW_FIELDS = list(wr.FIELDS.values())


def target(model: str, region: str, lang: str, scope: str = "single") -> dict:
    return {"model": model, "region": region, "lang": lang, "route": f"{model}/{region}/{lang}/md",
            "manual": f"manual_{model.lower()}_{region.lower()}_{lang}.md", "language_scope": scope}


def snapshot(**overrides) -> dict:
    value = {"schema": wp.SNAPSHOT_SCHEMA, "exported_at": "2026-10-19", "checked": ["JE-A/EU/en"],
             "sold": {"JE-A": ["EU", "US", "KR"], "JS-B": ["EU"]},
             "timeline": [{"date": "2026-10-01", "added": 2, "langs": 2, "editions": 1, "models": 1},
                          {"date": "2026-10-03", "added": 2, "langs": 4, "editions": 3, "models": 2}]}
    return {**value, **overrides}


def runner(fields: list[str], rows: list[list], tables: dict | None = None):
    """A lark-cli +record-list stand-in; ``tables`` maps other table ids to their (fields, rows)."""
    def run(args):
        table_fields, table_rows = (tables or {}).get(args[args.index("--table-id") + 1], (fields, rows))
        offset = int(args[args.index("--offset") + 1])
        page = table_rows[offset:offset + 200]
        return {"code": 0, "data": {"fields": table_fields, "data": page, "total": len(table_rows), "has_more": False,
                                    "record_id_list": [f"rec{offset + i}" for i in range(len(page))]}}
    return run


def review(model: str, market: str, **overrides) -> dict:
    value = {"record": "recR1", "model": model, "name": f"{model} name", "market": market, "market_label": "",
             "language": "en", "version": "v0.10", "date": "2026-10-18", "status": "审核中", "open": 2,
             "draft": f"{REVIEW_SITE}/{model}/{market}/index.html", "page": f"{REVIEW_SITE}/{model}/{market}.html"}
    return {**value, **overrides}


def review_row(model, market, version="v0.92", date=1792598400000, status="审核中", open_="3", draft=None):
    link = {"link": draft or f"{REVIEW_SITE}/{model}/JP/draft.html", "text": f"{model} {version} 审核稿"}
    # In wr.FIELDS order: 型号, 商品名称, 市场, 语言, 当前版本, 更新日期, 状态, 待研发确认, 审核稿, 审核页.
    return [model, f"{model} 商品", market, "ja", version, date, status, open_, link,
            {"link": f"{REVIEW_SITE}/{model}/JP.html", "text": "审核页"}]


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

    def test_review_cell_shapes(self):
        self.assertEqual(wr.text_of([{"text": "v0.", "type": "text"}, {"text": "92"}]), "v0.92")
        self.assertEqual(wr.text_of(" 日规 "), "日规")
        self.assertEqual(wr.link_of({"link": f"{REVIEW_SITE}/A/US.html", "text": "A 审核页"}), f"{REVIEW_SITE}/A/US.html")
        self.assertEqual(wr.link_of([{"text": f"见 {REVIEW_SITE}/A/US.html"}]), f"{REVIEW_SITE}/A/US.html")
        self.assertEqual(wr.link_of("none"), "")
        # Feishu keeps the epoch milliseconds of midnight in the tenant's zone (UTC+8).
        self.assertEqual(wr.day_of(1792598400000), "2026-10-22")
        self.assertEqual(wr.day_of("1792598400000"), "2026-10-22")
        self.assertEqual(wr.day_of("2026/10/21"), "2026-10-21")
        self.assertEqual(wr.day_of(None), "")
        self.assertEqual((wr.count_of("20"), wr.count_of(3.0), wr.count_of("-"), wr.count_of(None)), (20, 3, 0, 0))


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

    def test_reads_reviews_records_and_feishu_addresses(self):
        rows = [["JE-A", {"link": f"{SITE}/JE-A/EU/en/md/manual.html"}, None, []],
                ["JE-A", {"link": f"{SITE}/JE-A/EU/en/md/manual.html"}, None, []]]
        reviews = [review_row("JHP-B", "日规"), review_row("JE-A", "未知规", open_="x"), ["", None, "", "", "", "", None, "", "", None]]
        run = runner(self.FIELDS, rows, {"review": (REVIEW_FIELDS, reviews)})
        result = wp.export_snapshot(run=run, base_token="b", table_id="web", timeline=[], today=TODAY,
                                    review_table="review", base_url=BASE_URL + "?table=old&view=v")
        self.assertEqual(result["records"], {"JE-A/EU/en": "rec0"})
        self.assertEqual(result["feishu"], {"web": f"{BASE_URL}?table=web", "reviews": f"{BASE_URL}?table=review"})
        self.assertEqual([(r["model"], r["market"], r["market_label"], r["open"]) for r in result["reviews"]],
                         [("JE-A", "", "未知规", 0), ("JHP-B", "JP", "日规", 3)])
        first = result["reviews"][1]
        self.assertEqual((first["version"], first["date"], first["record"]), ("v0.92", "2026-10-22", "rec0"))
        self.assertEqual(first["draft"], f"{REVIEW_SITE}/JHP-B/JP/draft.html")
        self.assertEqual(wp.snapshot_problems(result), [])
        bare = wp.export_snapshot(run=runner(self.FIELDS, rows), base_token="b", table_id="web", timeline=[], today=TODAY)
        self.assertFalse({"reviews", "records", "feishu"} & set(bare))

    def test_refuses_a_review_table_without_its_columns_or_with_a_bad_model(self):
        rows = [["JE-A", {"link": f"{SITE}/JE-A/EU/en/md/manual.html"}, None, []]]
        with self.assertRaisesRegex(RuntimeError, "missing columns"):
            wp.export_snapshot(run=runner(self.FIELDS, rows, {"review": (["型号"], [["JE-A"]])}), base_token="b",
                               table_id="web", timeline=[], today=TODAY, review_table="review")
        with self.assertRaisesRegex(RuntimeError, "not a model code"):
            wp.export_snapshot(run=runner(self.FIELDS, rows, {"review": (REVIEW_FIELDS, [review_row("新 型号", "日规")])}),
                               base_token="b", table_id="web", timeline=[], today=TODAY, review_table="review")

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
            "reviews is not": dict(reviews={}),
            "needs exactly": dict(reviews=[{"model": "JE-A"}]),
            "unknown market": dict(reviews=[review("JE-A", "XX")]),
            "待研发确认": dict(reviews=[review("JE-A", "US", open=-1)]),
            "https": dict(reviews=[review("JE-A", "US", draft="http://insecure")]),
            "come together": dict(records={"JE-A/EU/en": "recA"}),
            "record ids": dict(records={"JE-A/EU/en": "nope"}, feishu={"web": f"{BASE_URL}?table=w", "reviews": ""}),
            "table addresses": dict(records={}, feishu={"web": "ftp://x", "reviews": ""}),
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

    def with_reviews(self):
        return snapshot(reviews=[review("JE-A", "US", date="2026-10-17", open=4),
                                 review("JE-A", "EU", record="recR2", version="v0.30", date="2026-10-18", open=0),
                                 review("FG-2", "US", record="recR3", name="FridgeGuard 2", date="2026-10-19"),
                                 review("FG-2", "", record="recR4", market_label="新规", date="2026-10-10")],
                        records={"JE-A/EU/en": "recW1", "JS-B/EU/en": "recW2"},
                        feishu={"web": f"{BASE_URL}?table=web", "reviews": f"{BASE_URL}?table=rev"})

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

    def test_drafts_in_review_take_their_cells(self):
        view = self.view(self.with_reviews())
        self.assertEqual([r["model"] for r in view["rows"]], ["FG-2", "JE-A", "JS-B"])
        self.assertEqual(view["rows"][0]["category"], wp.REVIEW_CATEGORY)
        self.assertEqual(view["rows"][0]["name"], "FridgeGuard 2")
        self.assertEqual([c["label"] for c in view["categories"]], [wp.REVIEW_CATEGORY, "电源主机", "太阳能板"])
        rows = {row["model"]: {c["market"]: c for c in row["cells"]} for row in view["rows"]}
        us = rows["JE-A"]["US"]
        self.assertEqual((us["state"], us["text"], us["href"]), ("review", "v0.10", f"{REVIEW_SITE}/JE-A/US/index.html"))
        self.assertIn("待研发确认 4 项", us["title"])
        self.assertEqual(rows["JE-A"]["KR"]["state"], "gap")
        # An online edition keeps its chip and shows the newer draft beside it.
        self.assertEqual((rows["JE-A"]["EU"]["state"], rows["JE-A"]["EU"]["review"]["text"]), ("full", "v0.30"))
        self.assertEqual(rows["FG-2"]["US"]["state"], "review")
        self.assertEqual(rows["FG-2"]["EU"]["state"], "")
        self.assertEqual([r["reviews"] for r in view["rows"]], [1, 2, 0])
        self.assertEqual({k: view["kpis"][k] for k in ("gaps", "reviews", "open", "latest")},
                         {"gaps": 1, "reviews": 4, "open": 8, "latest": "2026-10-19"})
        bars = {m["code"]: m for m in view["market_rows"]}
        self.assertEqual((bars["US"]["review"], bars["US"]["gap"]), (2, 0))

    def test_reviews_and_feishu_links(self):
        view = self.view(self.with_reviews())
        self.assertEqual([(r["model"], r["date"]) for r in view["reviews"]],
                         [("FG-2", "2026-10-19"), ("JE-A", "2026-10-18"), ("JE-A", "2026-10-17"), ("FG-2", "2026-10-10")])
        self.assertEqual(view["reviews"][0]["feishu"], f"{BASE_URL}?table=rev&record=recR3")
        self.assertEqual((view["reviews"][0]["market_text"], view["reviews"][3]["market_text"]), ("美规", "新规"))
        self.assertEqual(view["record_links"], {"JE-A/EU/en/md/manual_je-a_eu_en": f"{BASE_URL}?table=web&record=recW1",
                                                "JS-B/EU/en/md/manual_js-b_eu_en": f"{BASE_URL}?table=web&record=recW2"})
        self.assertEqual(view["feishu"]["web"], f"{BASE_URL}?table=web")
        plain = self.view()
        self.assertEqual((plain["reviews"], plain["record_links"], plain["feishu"], plain["kpis"]["reviews"]), ([], {}, {}, None))

    def test_counts_and_bars(self):
        view = self.view()
        self.assertEqual(view["kpis"], {"models": 2, "editions": 3, "routes": 4, "checked": 1, "gaps": 2, "partial": 1,
                                        "reviews": None, "open": 0, "latest": ""})
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
