from __future__ import annotations

import copy
import datetime as dt
import io
import json
import shutil
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import yaml

from tools import rtd_portal
from tools import rtd_system_workspace as sw
from tools.utils.path_utils import repo_root

REPO = repo_root()
TODAY = dt.date(2026, 9, 24)
LEDGER = """\
| ID | 所属工作 | 前置依赖 | 退出证据 | 状态 | 执行人 |
|---|---|---|---|---|---|
| <a id="rev-01"></a>REV-01 | WP1 | — | x | done | a |
| <a id="rev-02"></a>REV-02 | WP1 | REV-01 | x | verifying | a |
| <a id="rev-03"></a>REV-03 | WP2 | G1 | x | planned | a |
| <a id="rev-04"></a>REV-04 | WP2 | G1 | x | deferred | a |

| 门 | 范围与通过条件 | 当前记录 |
|---|---|---|
| G1 发布基线 | REV-01–02 验收 | 未验收 |
| G2 维护试点 | G1 通过且 REV-03 验收；另需 REV-04 | 未验收 |
"""


def contract() -> dict:
    """A small valid contract whose evidence resolves inside the test root."""
    return {
        "schema": sw.SCHEMA,
        "verified_on": TODAY,
        "stale_after_days": 30,
        "repositories": {"auto-manual": "https://github.com/o/auto-manual",
                         "hello-docs": "https://github.com/o/Hello-Docs"},
        "vocabulary": {"status": {name: name for name in sw.STATUS_ORDER},
                       "mode": {"automated": "a", "manual": "m"}},
        "hero": {"title": "T", "subtitle": "S", "stage": "St", "stage_note": "N",
                 "evidence": ["file:auto-manual:ledger.md"]},
        "snapshot": [
            {"key": "books", "label": "在线手册", "source": "publications"},
            {"key": "outputs", "label": "输出格式", "items": ["prod.web", "prod.idml"]},
            {"key": "prod", "label": "生产", "card": "prod"},
            {"key": "time", "label": "快照时间", "source": "build_date"},
        ],
        "capabilities": [{
            "id": "prod", "title": "生产", "en": "Production", "status": "in_progress", "summary": "s",
            "items": [
                {"id": "web", "label": "网页手册", "short": "网页", "status": "available", "note": "n",
                 "evidence": ["file:auto-manual:tool.py", "pr:auto-manual#7"]},
                {"id": "idml", "label": "IDML", "status": "in_progress",
                 "evidence": ["rev:REV-03=planned", "url:https://example.test/x"]},
            ],
        }],
        "flow": [{"from": "a", "to": "b", "status": "available", "mode": "manual",
                  "evidence": ["pr:hello-docs#3"]}],
        "now_next": {
            "source": "file:auto-manual:ledger.md",
            "gates": [{"id": "G1", "label": "发布基线", "revs": ["REV-01..REV-02"]},
                      {"id": "G2", "label": "维护试点", "revs": ["REV-03"]}],
            "now_labels": {"REV-02": "在验项"},
        },
        "working_today": [
            {"id": "center", "label": "手册中心", "page": "index"},
            {"id": "manual", "label": "代表手册", "publication": {"model": "JE-TEST", "region": "US", "lang": "en"}},
        ],
    }


def manifest() -> dict:
    target = {"model": "JE-TEST", "region": "US", "route": "JE-TEST/US/en/md",
              "manual": "manual_je_test_us.md", "version": "9.9"}
    return {"targets": [
        {**target, "lang": "en", "built_at": "2026-09-20T01:00:00+00:00"},
        {**target, "lang": "fr", "built_at": "2026-09-22T01:00:00+00:00"},
        {"model": "JE-OTHER", "region": "EU", "lang": "en", "built_at": "2026-09-01T00:00:00+00:00"},
    ]}


class SystemWorkspaceContractTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "ledger.md").write_text(LEDGER, encoding="utf-8")
        (self.root / "tool.py").write_text("", encoding="utf-8")

    def findings(self, data: dict, *, today: dt.date = TODAY) -> list[sw.Finding]:
        return sw.check_contract(data, root=self.root, today=today)

    def test_minimal_contract_is_clean(self):
        self.assertEqual(self.findings(contract()), [])

    def test_each_authoring_error_is_reported(self):
        def card(data):
            return data["capabilities"][0]

        def item(data, index=0):
            return card(data)["items"][index]

        mutations = {
            "status 'finished' not in vocabulary": lambda d: item(d).update(status="finished"),
            "above its weakest implemented item": lambda d: card(d).update(status="available"),
            "planned needs a rev": lambda d: item(d).update(status="planned"),
            "retired entries do not belong": lambda d: item(d).update(status="retired"),
            "cannot be the only evidence": lambda d: item(d).update(evidence=["ack:someone 2026-09-24「ok」"]),
            "no evidence": lambda d: item(d).update(evidence=[]),
            "unknown evidence kind": lambda d: item(d).update(evidence=["note:anything"]),
            "pr evidence wants": lambda d: item(d).update(evidence=["pr:auto-manual#seven"]),
            "file evidence wants": lambda d: item(d).update(evidence=["file:auto-manual:../escape.py"]),
            "must be an https URL": lambda d: item(d).update(evidence=["url:http://example.test"]),
            "rev evidence wants": lambda d: item(d).update(evidence=["rev:REV-03=finished"]),
            "ack evidence wants": lambda d: item(d, 1).update(evidence=["rev:REV-03=planned", "ack:someone「ok」"]),
            "unknown repository": lambda d: item(d).update(evidence=["pr:elsewhere#1"]),
            "mode 'sometimes' not in vocabulary": lambda d: d["flow"][0].update(mode="sometimes"),
            "unknown card": lambda d: d["snapshot"][2].update(card="missing"),
            "unknown item": lambda d: d["snapshot"][1].update(items=["prod.missing"]),
            "needs exactly one of source / items / card": lambda d: d["snapshot"][0].update(card="prod"),
            "missing from the ledger": lambda d: d["now_next"]["gates"][1].update(revs=["REV-09"]),
            "does not name": lambda d: d["now_next"]["gates"][0].update(revs=["REV-01..REV-03"]),
            "no such gate": lambda d: d["now_next"]["gates"][1].update(id="G9"),
            "is not in the ledger": lambda d: d["now_next"].update(now_labels={"REV-99": "x"}),
            "needs exactly one of page / publication": lambda d: d["working_today"][0].update(publication={}),
            "must be a site docname": lambda d: d["working_today"][0].update(page="../outside"),
            "expected hello-docs-system-workspace": lambda d: d.update(schema="other/v0"),
        }
        for fragment, mutate in mutations.items():
            with self.subTest(fragment):
                data = contract()
                mutate(data)
                errors = [f for f in self.findings(data) if f.severity == "error"]
                self.assertTrue(any(fragment in f.message for f in errors), errors)

    def test_quantity_in_text_is_only_a_warning(self):
        data = contract()
        data["capabilities"][0]["items"][0]["note"] = "已有 4 个骨架"
        findings = self.findings(data)
        self.assertEqual([f.severity for f in findings], ["warning"])
        self.assertIn("quantity", findings[0].message)

    def test_drift_is_graded_broken_references_fail_moved_states_warn(self):
        data = contract()
        data["capabilities"][0]["items"][0]["evidence"] = ["file:auto-manual:gone.py"]
        self.assertEqual([(f.severity, f.message) for f in self.findings(data)],
                         [("error", "证据文件不存在：gone.py")])

        (self.root / "ledger.md").write_text(LEDGER.replace("| x | planned |", "| x | done |"), encoding="utf-8")
        moved = self.findings(contract())
        self.assertEqual([f.severity for f in moved], ["warning"])
        self.assertIn("REV-03 在台账中已变为 done", moved[0].message)

        stale = self.findings(contract(), today=TODAY + dt.timedelta(days=31))
        self.assertTrue(stale and all(f.severity == "warning" for f in stale))
        self.assertTrue(all("超过 30 天未复核" in f.message for f in stale if "REV-03" not in f.message))

    def test_business_plane_files_resolve_only_in_a_tree_with_publications(self):
        data = contract()
        data["capabilities"][0]["items"][0]["evidence"].append("file:hello-docs:docs/publish/publish_manifest.json")
        self.assertEqual(self.findings(data), [])
        (self.root / "docs" / "publish").mkdir(parents=True)
        self.assertEqual([f.severity for f in self.findings(data)], ["error"])
        (self.root / "docs" / "publish" / "publish_manifest.json").write_text("{}", encoding="utf-8")
        self.assertEqual(self.findings(data), [])

    def test_unreadable_ledger_is_an_error_for_check(self):
        (self.root / "ledger.md").unlink()
        self.assertIn("execution ledger is not readable", [f.message for f in self.findings(contract())])

    def test_parse_ledger_expands_gate_ranges(self):
        ledger = sw.parse_ledger(LEDGER)
        self.assertEqual(ledger.statuses, {"REV-01": "done", "REV-02": "verifying",
                                           "REV-03": "planned", "REV-04": "deferred"})
        self.assertEqual(ledger.gates, {"G1": {"REV-01", "REV-02"}, "G2": {"REV-03", "REV-04"}})

    def test_publication_facts_count_books_by_model_and_region(self):
        path = self.root / "publish_manifest.json"
        path.write_text(json.dumps(manifest()), encoding="utf-8")
        facts = sw.publication_facts(path)
        self.assertEqual((facts["books"], facts["editions"], facts["last_published"]), (2, 3, "2026-09-22"))
        path.write_text("not json", encoding="utf-8")
        self.assertIsNone(sw.publication_facts(path))
        path.write_text(json.dumps({"targets": []}), encoding="utf-8")
        self.assertIsNone(sw.publication_facts(path))
        self.assertIsNone(sw.publication_facts(self.root / "missing.json"))

    def test_online_checks_use_merge_state_and_http_status(self):
        data = contract()
        data["capabilities"][0]["items"][0]["evidence"].append("file:hello-docs:docs/publish/publish_manifest.json")
        with patch.object(sw, "_get_json", return_value={"merged": True}), \
                patch.object(sw, "_http_status", return_value=200):
            self.assertEqual(sw.online_findings(data), [])
        with patch.object(sw, "_get_json", return_value={"merged": False}) as pulls, \
                patch.object(sw, "_http_status", return_value=404) as probes:
            findings = sw.online_findings(data)
        self.assertEqual(sorted(f.where for f in findings), [
            "file:hello-docs:docs/publish/publish_manifest.json",
            "pr:auto-manual#7", "pr:hello-docs#3", "url:https://example.test/x",
        ])
        self.assertEqual(sorted(call.args[0] for call in pulls.call_args_list),
                         ["https://api.github.com/repos/o/Hello-Docs/pulls/3",
                          "https://api.github.com/repos/o/auto-manual/pulls/7"])
        # Engineering-plane files are checked offline against the tree; only
        # business-plane files and plain URLs go over the network.
        self.assertEqual(sorted(call.args[0] for call in probes.call_args_list), [
            "https://api.github.com/repos/o/Hello-Docs/contents/docs/publish/publish_manifest.json?ref=main",
            "https://example.test/x",
        ])


class SystemWorkspaceContextTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "ledger.md").write_text(LEDGER, encoding="utf-8")
        (self.root / "tool.py").write_text("", encoding="utf-8")
        (self.root / "publish_manifest.json").write_text(json.dumps(manifest()), encoding="utf-8")

    def context(self, data=None, facts="default"):
        data = data or contract()
        if facts == "default":
            facts = sw.publication_facts(self.root / "publish_manifest.json")
        return sw.build_context(data, root=self.root, ledger=sw.parse_ledger(LEDGER), facts=facts, today=TODAY)

    def test_tiles_come_from_the_manifest_cards_and_build_date(self):
        tiles = {tile["label"]: tile for tile in self.context()["tiles"]}
        self.assertEqual((tiles["在线手册"]["value"], tiles["在线手册"]["sub"]), (2, "3 个语言版"))
        self.assertEqual([(e["label"], e["note"]) for e in tiles["输出格式"]["entries"]],
                         [("网页", ""), ("IDML", "建设中")])
        self.assertEqual(tiles["生产"]["status_label"], "建设中")
        self.assertEqual((tiles["快照时间"]["value"], tiles["快照时间"]["sub"]), ("2026-09-24", "最近发布 2026-09-22"))

    def test_missing_publications_render_as_no_data(self):
        view = self.context(facts=None)
        self.assertEqual(view["tiles"][0]["kind"], "no_data")
        self.assertEqual(view["working"][1]["docname"], "")

    def test_gates_and_now_items_read_the_ledger(self):
        view = self.context()
        g1, g2 = view["gates"]
        self.assertEqual((g1["done"], g1["total"], g1["percent"], g1["state"], g1["tally"]),
                         (1, 2, 50, "active", "完成 1 · 在验 1"))
        self.assertEqual((g2["state"], g2["tally"]), ("idle", "待做 1"))
        self.assertEqual(view["now"], [{"rev": "REV-02", "label": "在验项", "status": "verifying",
                                        "status_label": "在验",
                                        "href": "https://github.com/o/auto-manual/blob/main/ledger.md#rev-02"}])

    def test_working_entries_link_site_pages_and_resolve_publications(self):
        center, manual = self.context()["working"]
        self.assertEqual(center["docname"], "index")
        self.assertEqual((manual["docname"], manual["meta"]), ("JE-TEST/US/en/md/manual_je_test_us", "版本 9.9"))

    def test_evidence_links_map_every_kind(self):
        repos = {"auto-manual": "https://github.com/o/auto-manual", "hello-docs": "https://github.com/o/Hello-Docs"}
        ledger_url = "https://github.com/o/auto-manual/blob/main/ledger.md"
        cases = {
            "pr:auto-manual#7": ("#7", "https://github.com/o/auto-manual/pull/7"),
            "pr:hello-docs#3": ("HD#3", "https://github.com/o/Hello-Docs/pull/3"),
            "file:auto-manual:tools/a.py": ("a.py", "https://github.com/o/auto-manual/blob/main/tools/a.py"),
            "url:https://example.test/x/": ("example.test/x", "https://example.test/x/"),
            "rev:REV-03=planned": ("REV-03", ledger_url + "#rev-03"),
            "ack:夏冰 2026-09-24「在用」": ("操作者确认 2026-09-24", ""),
        }
        for ref, (label, href) in cases.items():
            with self.subTest(ref):
                view = sw.evidence_view(ref, repos, ledger_url)
                self.assertEqual((view["label"], view["href"]), (label, href))

    def test_drifted_entries_carry_their_reasons(self):
        data = contract()
        data["capabilities"][0]["items"][1]["evidence"][0] = "rev:REV-03=done"
        idml = self.context(data)["cards"][0]["entries"][1]
        self.assertEqual(idml["stale"], ["REV-03 在台账中已变为 planned（记录为 done）"])


def corpus_contract() -> dict:
    data = contract()
    data["corpus"] = {"snapshot": "corpus.json", "stale_after_days": 45,
                      "languages": [{"code": "en", "label": "英语"}, {"code": "fr", "label": "法语"}]}
    return data


def corpus_snapshot() -> dict:
    return {
        "schema": sw.CORPUS_SCHEMA, "exported_at": "2026-09-24",
        "sentence_pairs": {"total": 10, "by_language": {"en": 4, "fr": 9},
                           "by_status": {"Approved": 7, "Draft": 3}},
        "terms": {"total": 2, "by_language": {"en": 2, "fr": 1}, "by_status": {"Approved": 2}},
    }


class CorpusSnapshotTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "ledger.md").write_text(LEDGER, encoding="utf-8")
        (self.root / "tool.py").write_text("", encoding="utf-8")

    def write_snapshot(self, snapshot) -> None:
        (self.root / "corpus.json").write_text(json.dumps(snapshot), encoding="utf-8")

    def test_sound_snapshot_passes_and_malformed_ones_are_named(self):
        self.assertEqual(sw.corpus_problems(corpus_snapshot(), ["en", "fr"]), [])

        def pairs(s):
            return s["sentence_pairs"]

        mutations = {
            "schema must be": lambda s: s.update(schema="other/v0"),
            "exported_at must be an ISO date": lambda s: s.update(exported_at="24/09/2026"),
            "aggregates only": lambda s: s.update(rows=[{"en": "text"}]),
            "must list exactly the contract languages": lambda s: pairs(s)["by_language"].pop("fr"),
            "between 0 and total": lambda s: pairs(s)["by_language"].update(fr=11),
            "sum to total": lambda s: pairs(s)["by_status"].update(Draft=9),
            "total must be a non-negative integer": lambda s: pairs(s).update(total=-1),
        }
        for fragment, mutate in mutations.items():
            with self.subTest(fragment):
                snapshot = corpus_snapshot()
                mutate(snapshot)
                problems = sw.corpus_problems(snapshot, ["en", "fr"])
                self.assertTrue(any(fragment in p for p in problems), problems)

    def test_export_pages_every_table_and_keeps_counts_only(self):
        from tools.lang_asset_sweep import TM_SENTENCE_TABLE, TM_TERMS_TABLE

        header = ["en", "fr", "Status", "Source"]
        sentence_rows = [["Hi", "Salut", "Approved", "x"]] * 200 + [["Bye", "", ["Draft"], "x"], ["", None, None, "x"]]
        terms_rows = [["Term", "Terme", "Approved", "x"]]
        calls = []

        def run(args):
            table, offset = args[args.index("--table-id") + 1], int(args[args.index("--offset") + 1])
            calls.append((table, offset))
            rows = sentence_rows if table == TM_SENTENCE_TABLE else terms_rows
            return {"code": 0, "data": {"fields": header, "data": rows[offset:offset + 200]}}

        snapshot = sw.corpus_export(corpus_contract(), base_token="base", run=run, today=TODAY)
        self.assertEqual(calls, [(TM_SENTENCE_TABLE, 0), (TM_SENTENCE_TABLE, 200), (TM_TERMS_TABLE, 0)])
        self.assertEqual(snapshot["sentence_pairs"], {"total": 202, "by_language": {"en": 201, "fr": 200},
                                                      "by_status": {"(未标注)": 1, "Approved": 200, "Draft": 1}})
        self.assertEqual(snapshot["terms"]["total"], 1)
        self.assertEqual(sw.corpus_problems(snapshot, ["en", "fr"]), [])
        self.assertNotIn("Salut", json.dumps(snapshot, ensure_ascii=False))

        def run_without_fr(args):
            return {"code": 0, "data": {"fields": ["en", "Status"], "data": [["Hi", "Approved"]]}}

        with self.assertRaisesRegex(RuntimeError, r"missing columns \['fr'\]"):
            sw.corpus_export(corpus_contract(), base_token="base", run=run_without_fr, today=TODAY)

    def test_view_sorts_languages_and_marks_an_old_snapshot(self):
        view = sw.corpus_view(corpus_contract(), corpus_snapshot(), TODAY)
        self.assertEqual([(r["label"], r["count"], r["percent"]) for r in view["rows"]],
                         [("法语", 9, 90), ("英语", 4, 40)])
        self.assertEqual([t["value"] for t in view["tiles"]], ["10", "2", "2", "70%"])
        self.assertEqual(view["stale"], [])
        old = sw.corpus_view(corpus_contract(), corpus_snapshot(), TODAY + dt.timedelta(days=46))
        self.assertEqual(old["stale"], ["语料快照已超过 45 天（导出于 2026-09-24）"])

    def test_check_reports_broken_and_stale_snapshots(self):
        data = corpus_contract()
        self.write_snapshot(corpus_snapshot())
        self.assertEqual(sw.check_contract(data, root=self.root, today=TODAY, assets=self.root), [])
        stale = sw.check_contract(data, root=self.root, today=TODAY + dt.timedelta(days=46), assets=self.root)
        self.assertIn(("warning", "corpus"), {(f.severity, f.where) for f in stale})
        broken = corpus_snapshot()
        broken["terms"]["by_status"] = {"Approved": 1}
        self.write_snapshot(broken)
        findings = sw.check_contract(data, root=self.root, today=TODAY, assets=self.root)
        self.assertEqual([(f.severity, f.where) for f in findings], [("error", "corpus")])
        (self.root / "corpus.json").unlink()
        self.assertIn("cannot read corpus.json",
                      sw.check_contract(data, root=self.root, today=TODAY, assets=self.root)[0].message)

    def test_corpus_config_errors_are_structural(self):
        for fragment, mutate in {
            "must name a .json file": lambda c: c.update(snapshot="../corpus.json"),
            "needs unique codes": lambda c: c["languages"].append({"code": "en", "label": "again"}),
            "must be a positive integer": lambda c: c.update(stale_after_days=0),
        }.items():
            with self.subTest(fragment):
                data = corpus_contract()
                mutate(data["corpus"])
                errors = [f.message for f in sw.structural_findings(data, sw.parse_ledger(LEDGER))]
                self.assertTrue(any(fragment in m for m in errors), errors)

    def test_corpus_export_cli_writes_the_snapshot(self):
        path = self.root / "contract.yaml"
        path.write_text(yaml.safe_dump(corpus_contract(), allow_unicode=True), encoding="utf-8")

        def run(args):
            return {"code": 0, "data": {"fields": ["en", "fr", "Status"], "data": [["Hi", "Salut", "Approved"]]}}

        with redirect_stdout(io.StringIO()) as out, patch.dict("os.environ", {}, clear=False):
            self.assertEqual(sw.main(["corpus-export", "--contract", str(path), "--base-token", ""]), 1)
        self.assertIn("need --base-token", out.getvalue())
        with redirect_stdout(io.StringIO()) as out, patch.object(sw, "lark_runner", return_value=run):
            self.assertEqual(sw.main(["corpus-export", "--contract", str(path), "--base-token", "base",
                                      "--today", "2026-09-24"]), 0)
        written = json.loads((self.root / "corpus.json").read_text(encoding="utf-8"))
        self.assertEqual((written["exported_at"], written["sentence_pairs"]["total"]), ("2026-09-24", 1))
        self.assertIn("1 sentence pairs", out.getvalue())


class ShippedSystemWorkspaceTests(unittest.TestCase):
    def test_shipped_contract_passes_the_offline_check(self):
        data = sw.load_contract(sw.DEFAULT_CONTRACT)
        # Pin "today" to the contract's own verification date so staleness never flakes;
        # a moved REV status is a warning by design, a broken reference is an error.
        errors = [f for f in sw.check_contract(data, root=REPO, today=data["verified_on"])
                  if f.severity == "error"]
        self.assertEqual(errors, [])

    def test_cli_exit_codes(self):
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(sw.main(["check", "--today", "2026-09-24"]), 0)
        self.assertIn("0 error(s)", out.getvalue())
        with TemporaryDirectory() as temp:
            broken = contract()
            broken["capabilities"][0]["status"] = "finished"
            path = Path(temp) / "contract.yaml"
            path.write_text(yaml.safe_dump(broken, allow_unicode=True), encoding="utf-8")
            (Path(temp) / "ledger.md").write_text(LEDGER, encoding="utf-8")
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(sw.main(["check", "--contract", str(path), "--root", temp,
                                          "--today", "2026-09-24"]), 1)
            self.assertIn("card status 'finished' not in vocabulary", out.getvalue())
        with redirect_stdout(io.StringIO()), patch("sys.stderr", io.StringIO()), \
                self.assertRaises(SystemExit):
            sw.main(["check", "--today", "24/09/2026"])

    def test_real_sphinx_renders_the_page_and_drops_only_it_on_contract_error(self):
        with TemporaryDirectory() as temp:
            base = Path(temp)
            web = base / "site" / "web"
            web.mkdir(parents=True)
            (web / "index.md").write_text("# Manual Center\n", encoding="utf-8")
            target = {"model": "JE-1000F", "region": "US", "lang": "en", "route": "JE-1000F/US/en/md",
                      "manual": "manual_je1000f_us.md", "version": "9.9", "built_at": "2026-09-20T00:00:00+00:00"}
            (base / "site" / "publish_manifest.json").write_text(json.dumps({"targets": [target]}), encoding="utf-8")
            share = base / "knowledge" / "ai-share"
            share.mkdir(parents=True)
            (share / "00_打开分享.html").write_text("<!doctype html><p>分享</p>", encoding="utf-8")
            assets = base / "assets"
            shutil.copytree(rtd_portal.ASSETS, assets)
            settings = json.loads((assets / "settings.json").read_text(encoding="utf-8"))
            (assets / "settings.json").write_text(json.dumps(dict(settings, product_voc_endpoint="")), encoding="utf-8")
            (web / "conf.py").write_text(
                "project = 'manual'\nroot_doc = 'index'\n"
                "from pathlib import Path\nfrom tools import rtd_portal as portal\n"
                f"portal.ASSETS = Path({str(assets)!r})\n"
                f"rtd_knowledge_dir = {str(base / 'knowledge')!r}\n"
                "rtd_system_workspace_date = '2026-09-24'\n",
                encoding="utf-8",
            )

            def build(name):
                return subprocess.run(
                    [sys.executable, "-m", "sphinx", "-q", "-b", "html",
                     "-D", "extensions=myst_parser,tools.rtd_portal", str(web), str(base / name)],
                    cwd=REPO, capture_output=True, text=True,
                )

            result = build("good")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            page = (base / "good" / "workspace" / "system" / "index.html").read_text(encoding="utf-8")
            for heading in ("能力地图", "生产流程与连接", "正在做与下一步", "现在就能用"):
                self.assertIn(heading, page)
            self.assertIn("1 个语言版", page)
            self.assertIn("版本 9.9", page)
            self.assertIn('href="../../JE-1000F/US/en/md/manual_je1000f_us.html"', page)
            self.assertNotIn("Jackery", page)
            self.assertIn("语言资产", page)
            self.assertIn('class="sw-corpus-bars"', page)
            self.assertTrue((base / "good" / "_static" / "system-workspace.css").is_file())
            workspace = (base / "good" / "workspace" / "index.html").read_text(encoding="utf-8")
            self.assertIn('href="system/index.html"', workspace)

            snapshot = assets / sw.load_contract(assets / sw.CONTRACT_NAME)["corpus"]["snapshot"]
            snapshot.write_text("{not json", encoding="utf-8")
            result = build("no-corpus")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("corpus block shows no data", result.stderr)
            page = (base / "no-corpus" / "workspace" / "system" / "index.html").read_text(encoding="utf-8")
            self.assertIn("语料快照当前不可读", page)
            self.assertIn("能力地图", page)

            broken = sw.load_contract(assets / sw.CONTRACT_NAME)
            broken = copy.deepcopy(broken)
            broken["capabilities"][0]["status"] = "finished"
            (assets / sw.CONTRACT_NAME).write_text(yaml.safe_dump(broken, allow_unicode=True), encoding="utf-8")
            result = build("broken")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("System workspace page skipped", result.stderr)
            self.assertFalse((base / "broken" / "workspace" / "system" / "index.html").exists())
            workspace = (base / "broken" / "workspace" / "index.html").read_text(encoding="utf-8")
            self.assertNotIn("system/index.html", workspace)
            self.assertIn("分享资料", workspace)


if __name__ == "__main__":
    unittest.main()
