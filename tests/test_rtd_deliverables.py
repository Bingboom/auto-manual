from __future__ import annotations

import copy
import datetime as dt
import io
import json
import os
import shutil
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tools import rtd_deliverables as dl
from tools import rtd_portal
from tools.rtd_source_registry import load_registry
from tools.utils.path_utils import repo_root

REPO = repo_root()
TODAY = dt.date(2026, 9, 25)
LABELS = {"EU": "欧规", "US": "美规", "JP": "日规", "BR": "巴西规"}
ORDER = json.loads((rtd_portal.ASSETS / "settings.json").read_text(encoding="utf-8"))["language_labels"]
FEISHU = load_registry(rtd_portal.ASSETS)[0][dl.FEISHU_DOMAIN]
SNAPSHOT_NAME = FEISHU["snapshot"]


def link(url: str) -> str:
    """The build table's text form of a hyperlink."""
    return f"[{url}]({url})"


def snapshot() -> dict:
    return {
        "schema": dl.SNAPSHOT_SCHEMA,
        "exported_at": "2026-09-25",
        "documents": [
            {"key": "JE-1000F_US", "model": "JE-1000F", "region": "US", "lang": "",
             "formats": {"print": {"version": "2.2", "url": "https://t.feishu.cn/wiki/print-us"},
                         "word": {"version": "1.0", "url": "https://t.feishu.cn/wiki/word-us"}}},
            {"key": "JE-1000F_pt-BR", "model": "JE-1000F", "region": "pt-BR", "lang": "",
             "formats": {"print": {"version": "0.5", "url": "https://t.feishu.cn/wiki/print-br"}}},
            {"key": "JE-1800B_JP", "model": "JE-1800B", "region": "JP", "lang": "",
             "formats": {"word": {"version": "0.5", "url": "https://t.feishu.cn/wiki/word-jp"}}},
        ],
    }


def target(model: str, region: str, lang: str, version: str = "2.5") -> dict:
    stem = f"manual_{model.lower().replace('-', '')}_{region.lower()}"
    return {"model": model, "region": region, "lang": lang, "version": version,
            "route": f"{model}/{region}/{lang}/md", "manual": f"{stem}.md",
            "built_at": "2026-09-24T12:00:00+00:00"}


class FakeFeishu:
    """``run(args)`` over two in-memory tables, paging like ``+record-list``."""

    def __init__(self, tables: dict[str, tuple[list[str], list[tuple[str, list]]]]):
        self.tables = tables
        self.calls: list[list[str]] = []

    def __call__(self, args: list[str]) -> dict:
        self.calls.append(args)
        table = args[args.index("--table-id") + 1]
        offset = int(args[args.index("--offset") + 1])
        fields, rows = self.tables[table]
        page = rows[offset:offset + 200]
        return {"data": {"fields": fields, "data": [row for _, row in page],
                         "record_id_list": [record_id for record_id, _ in page]}}


BUILD_FIELDS = ["Document_Key", "Lang", "Version", "idml_file", "飞书云文档", "HTML_link"]


class FeishuLinkTests(unittest.TestCase):
    def test_reads_link_shapes_and_refuses_other_hosts(self):
        url = "https://x.feishu.cn/wiki/abc"
        self.assertEqual(dl.feishu_url(link(url)), url)
        self.assertEqual(dl.feishu_url({"link": "https://x.larksuite.com/docx/1", "text": "doc"}),
                         "https://x.larksuite.com/docx/1")
        self.assertEqual(dl.feishu_url([{"text": url}]), url)
        for refused in ("http://x.feishu.cn/wiki/a", "https://example.com/wiki/a",
                        "https://feishu.cn.example.com/a", "javascript:alert(1)", None, ""):
            self.assertEqual(dl.feishu_url(refused), "", refused)

    def test_versions_order_numerically(self):
        self.assertEqual(sorted(["1.10", "1.2", "0.5", ""], key=dl.version_key), ["", "0.5", "1.2", "1.10"])


class ExportTests(unittest.TestCase):
    def tables(self, build_rows):
        keys = [(f"rec{i}", [f"PAD-{i}_US", "x"]) for i in range(200)]  # forces a second page
        keys += [("rec-us", ["JE-1000F_US", "否"]), ("rec-br", ["JE-1000F_pt-BR", ""])]
        return FakeFeishu({
            "tblKEY": (["Document_key", "产品名称"], keys),
            "tblBUILD": (BUILD_FIELDS, [(f"b{i}", row) for i, row in enumerate(build_rows)]),
        })

    def test_keeps_the_latest_link_per_document_language_and_format(self):
        us, br = [{"id": "rec-us"}], [{"id": "rec-br"}]
        run = self.tables([
            [us, None, ["1.2"], link("https://t.feishu.cn/wiki/p12"), link("https://t.feishu.cn/wiki/w12"), None],
            [us, None, ["1.10"], link("https://t.feishu.cn/wiki/p110"), None, None],
            [us, None, ["0.9"], None, link("https://t.feishu.cn/wiki/w09"), None],
            [us, ["en"], ["2.0"], None, "https://t.feishu.cn/wiki/w-en", link("https://ht-doc.readthedocs.io/x.html")],
            [br, None, ["0.5"], "https://t.feishu.cn/wiki/p-br", None, None],
            [[{"id": "rec-missing"}], None, ["9.9"], "https://t.feishu.cn/wiki/orphan", None, None],
            [us, None, ["3.0"], "https://example.com/not-feishu", None, None],
            [None, None, ["1.0"], "https://t.feishu.cn/wiki/no-key", None, None],
        ])
        result = dl.export_snapshot(run=run, base_token="base", build_table="tblBUILD", key_table="tblKEY", today=TODAY)
        self.assertEqual(result["schema"], dl.SNAPSHOT_SCHEMA)
        self.assertEqual(result["exported_at"], "2026-09-25")
        self.assertEqual(result["documents"], [
            {"key": "JE-1000F_US", "model": "JE-1000F", "region": "US", "lang": "",
             "formats": {"print": {"version": "1.10", "url": "https://t.feishu.cn/wiki/p110"},
                         "word": {"version": "1.2", "url": "https://t.feishu.cn/wiki/w12"}}},
            {"key": "JE-1000F_US", "model": "JE-1000F", "region": "US", "lang": "en",
             "formats": {"word": {"version": "2.0", "url": "https://t.feishu.cn/wiki/w-en"}}},
            {"key": "JE-1000F_pt-BR", "model": "JE-1000F", "region": "pt-BR", "lang": "",
             "formats": {"print": {"version": "0.5", "url": "https://t.feishu.cn/wiki/p-br"}}},
        ])
        self.assertEqual(dl.snapshot_problems(result), [])
        # The key table spans two pages; the product names it carries are not copied.
        key_offsets = [c[c.index("--offset") + 1] for c in run.calls if "tblKEY" in c]
        self.assertEqual(key_offsets, ["0", "200"])
        self.assertNotIn("否", json.dumps(result, ensure_ascii=False))

    def test_refuses_a_table_without_the_needed_columns(self):
        run = self.tables([])
        run.tables["tblBUILD"] = (["Document_Key", "Lang", "Version", "飞书云文档"], [])
        with self.assertRaisesRegex(RuntimeError, "missing columns \\['idml_file'\\]"):
            dl.export_snapshot(run=run, base_token="base", build_table="tblBUILD", key_table="tblKEY", today=TODAY)


class SnapshotTests(unittest.TestCase):
    def test_flags_each_unsound_part(self):
        self.assertEqual(dl.snapshot_problems(snapshot()), [])
        cases = {
            "schema is": lambda s: s.update(schema="other/v1"),
            "not an ISO date": lambda s: s.update(exported_at="25/09/2026"),
            "documents is not a list": lambda s: s.update(documents={}),
            "repeats": lambda s: s["documents"].append(copy.deepcopy(s["documents"][0])),
            "unknown format": lambda s: s["documents"][0]["formats"].update(pdf={"version": "1", "url": "https://t.feishu.cn/x"}),
            "not an https Feishu link": lambda s: s["documents"][0]["formats"]["print"].update(url="https://example.com/x"),
            "has no formats": lambda s: s["documents"][0].update(formats={}),
        }
        for expected, mutate in cases.items():
            data = snapshot()
            mutate(data)
            self.assertTrue(any(expected in problem for problem in dl.snapshot_problems(data)), expected)
        self.assertEqual(dl.snapshot_problems([]), ["the snapshot is not a JSON object"])

    def test_load_reports_unreadable_files(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / SNAPSHOT_NAME
            path.write_text("{not json", encoding="utf-8")
            data, problems = dl.load_snapshot(path)
            self.assertIsNone(data)
            self.assertIn("cannot read", problems[0])

    def test_committed_snapshot_is_sound(self):
        data, problems = dl.load_snapshot(dl.ASSETS / SNAPSHOT_NAME)
        self.assertEqual(problems, [])
        self.assertTrue(data["documents"])


class ViewTests(unittest.TestCase):
    def view(self, *, targets=None, data=None, today=TODAY):
        return dl.deliverables_view(
            [target("JE-1000F", "US", "fr"), target("JE-1000F", "US", "en"), target("JE-1000F", "EU", "en", "2.1"),
             target("JE-2000F", "EU", "de")] if targets is None else targets,
            snapshot() if data is None else data,
            names={("JE-1000F", "US"): "Explorer 1000", ("JE-2000F", "EU"): "Explorer 2000"},
            labels=LABELS, language_order=ORDER, today=today, feishu_domain=FEISHU,
        )

    def test_one_row_per_region_under_each_model(self):
        view = self.view()
        self.assertEqual([m["model"] for m in view["models"]], ["JE-1000F", "JE-1800B", "JE-2000F"])
        first = view["models"][0]
        self.assertEqual(first["name"], "Explorer 1000")
        self.assertEqual([(r["region"], r["region_label"]) for r in first["rows"]],
                         [("EU", "欧规"), ("US", "美规"), ("pt-BR", "巴西规")])
        self.assertEqual(view["models"][1]["name"], "")  # not in the manual center: code only
        us = first["rows"][1]
        self.assertEqual([chip["label"] for chip in us["web"]], ["EN", "FR"])
        self.assertEqual(us["web"][0]["docname"], "JE-1000F/US/en/md/manual_je1000f_us")
        self.assertIn("发布于 2026-09-24", us["web"][0]["title"])
        self.assertEqual([(c["label"], c["version"], c["url"]) for c in us["print"]],
                         [("整本", "2.2", "https://t.feishu.cn/wiki/print-us")])
        self.assertEqual(first["rows"][0]["print"], [])
        self.assertEqual([r["code"] for r in view["regions"]], ["EU", "US", "JP", "pt-BR"])

    def test_tiles_count_each_format(self):
        tiles = {tile["label"]: (tile["value"], tile["sub"]) for tile in self.view()["tiles"]}
        self.assertEqual(tiles, {
            "型号": ("3", "5 个型号 × 区域"),
            "网页": ("4", "覆盖 3 个型号 × 区域"),
            "印刷交付包": ("2", "覆盖 2 个型号 × 区域"),
            "Word 云文档": ("2", "覆盖 2 个型号 × 区域"),
        })

    def test_staleness_and_missing_inputs(self):
        view = self.view()
        self.assertEqual((view["snapshot_date"], view["stale"], view["last_published"]), ("2026-09-25", [], "2026-09-24"))
        self.assertIn("超过 45 天", self.view(today=TODAY + dt.timedelta(days=46))["stale"][0])
        bare = dl.deliverables_view(None, None, names={}, labels=LABELS, language_order=ORDER, today=TODAY,
                                    feishu_domain=FEISHU)
        self.assertEqual((bare["models"], bare["web_missing"], bare["feishu_missing"]), ([], True, True))
        web_only = dl.deliverables_view([target("JE-1000F", "US", "en")], None, names={}, labels={},
                                        language_order=ORDER, today=TODAY, feishu_domain=FEISHU)
        self.assertEqual(web_only["models"][0]["rows"][0]["region_label"], "US")  # no labels: the code
        self.assertTrue(web_only["feishu_missing"])

    def test_locale_style_key_regions_read_as_their_region(self):
        self.assertEqual([dl.region_code(r, LABELS) for r in ("pt-BR", "US", "en-XX", "")], ["BR", "US", "en-XX", ""])

    def test_region_labels_come_from_the_system_contract(self):
        labels = dl.region_labels(rtd_portal.ASSETS)
        self.assertEqual((labels["EU"], labels["US"], labels["BR"]), ("欧规", "美规", "巴西规"))
        with TemporaryDirectory() as temp:
            self.assertEqual(dl.region_labels(Path(temp)), {})


class CliTests(unittest.TestCase):
    def test_check_reports_coverage_staleness_and_errors(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / SNAPSHOT_NAME
            path.write_text(json.dumps(snapshot()), encoding="utf-8")
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(dl.main(["check", "--snapshot", str(path), "--today", "2026-09-25"]), 0)
            self.assertIn("3 documents across 2 models; 印刷交付包 2, Word 云文档 2", out.getvalue())
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(dl.main(["check", "--snapshot", str(path), "--today", "2026-11-20"]), 0)
            self.assertIn("WARNING", out.getvalue())
            path.write_text("[]", encoding="utf-8")
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(dl.main(["check", "--snapshot", str(path)]), 1)
            self.assertIn("ERROR", out.getvalue())

    def test_export_needs_the_table_coordinates(self):
        cleared = {k: v for k, v in os.environ.items() if not k.startswith("FEISHU_PHASE2_")}
        with patch.dict(os.environ, cleared, clear=True), redirect_stdout(io.StringIO()) as out:
            self.assertEqual(dl.main(["export", "--output", os.devnull]), 1)
        self.assertIn("need --base-token, --build-table, --key-table", out.getvalue())


class RealSphinxTests(unittest.TestCase):
    def test_renders_the_page_and_links_it_from_the_workspace(self):
        with TemporaryDirectory() as temp:
            base = Path(temp)
            web = base / "site" / "web"
            web.mkdir(parents=True)
            (web / "index.md").write_text("# Manual Center\n", encoding="utf-8")
            manifest = base / "site" / "publish_manifest.json"
            manifest.write_text(json.dumps({"targets": [target("JE-1000F", "US", "en")]}), encoding="utf-8")
            assets = base / "assets"
            shutil.copytree(rtd_portal.ASSETS, assets)
            (assets / SNAPSHOT_NAME).write_text(json.dumps(snapshot()), encoding="utf-8")
            settings = json.loads((assets / "settings.json").read_text(encoding="utf-8"))
            (assets / "settings.json").write_text(json.dumps(dict(settings, product_voc_endpoint="")), encoding="utf-8")
            (web / "conf.py").write_text(
                "project = 'manual'\nroot_doc = 'index'\n"
                "from pathlib import Path\nfrom tools import rtd_portal as portal\n"
                f"portal.ASSETS = Path({str(assets)!r})\n"
                f"rtd_knowledge_dir = {str(base / 'knowledge')!r}\n"
                "rtd_system_workspace_date = '2026-09-25'\n",
                encoding="utf-8",
            )

            def build(name):
                result = subprocess.run(
                    [sys.executable, "-m", "sphinx", "-q", "-b", "html",
                     "-D", "extensions=myst_parser,tools.rtd_portal", str(web), str(base / name)],
                    cwd=REPO, capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                page = (base / name / "workspace" / "deliverables" / "index.html").read_text(encoding="utf-8")
                return result, page

            _, page = build("good")
            self.assertIn("<h1>交付物", page)
            self.assertIn('<tbody data-model="JE-1000F">', page)
            self.assertIn('<tr data-region="pt-BR">', page)
            # Web manuals link to their page on this site; Feishu links open in a new tab.
            self.assertIn('href="../../JE-1000F/US/en/md/manual_je1000f_us.html"', page)
            self.assertIn('href="https://t.feishu.cn/wiki/print-us"', page)
            self.assertEqual(page.count('target="_blank" rel="noopener"'), 4)
            self.assertIn('<option value="JE-1800B">JE-1800B</option>', page)
            self.assertIn("飞书快照 2026-09-25", page)
            self.assertTrue((base / "good" / "_static" / "deliverables.css").is_file())
            workspace = (base / "good" / "workspace" / "index.html").read_text(encoding="utf-8")
            self.assertEqual(workspace.count('href="deliverables/index.html"'), 2)  # nav and 最近更新
            system = (base / "good" / "workspace" / "system" / "index.html").read_text(encoding="utf-8")
            self.assertIn('href="../deliverables/index.html"', system)
            self.assertIn('href="../system/index.html"', page)

            # An unsound snapshot empties only the Feishu columns.
            (assets / SNAPSHOT_NAME).write_text("{not json", encoding="utf-8")
            result, page = build("no-snapshot")
            self.assertIn("Deliverables page shows no Feishu links", result.stderr)
            self.assertIn("飞书快照当前不可读", page)
            self.assertIn('href="../../JE-1000F/US/en/md/manual_je1000f_us.html"', page)
            self.assertNotIn("t.feishu.cn", page)

            # Without a publish manifest the page still renders; with neither input it says so.
            manifest.unlink()
            _, page = build("nothing")
            self.assertIn("发布清单和飞书快照当前都不可读", page)
            self.assertIn("网页手册：发布清单当前不可读", page)


if __name__ == "__main__":
    unittest.main()
