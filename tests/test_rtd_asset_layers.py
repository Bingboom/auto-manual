"""四类资产 pages (tools/rtd/asset_layers.py, tools/rtd/asset_media.py): views read only what exists, and say so."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from tools.rtd import asset_layer_data as ald
from tools.rtd import asset_layers as al
from tools.rtd import asset_pages as ap
from tools.rtd import system_workspace as sw
from tools.rtd import asset_media as am
from tools.rtd.design_assets import REGISTRIES
from tools.rtd.portal import ASSETS
from tools.utils.path_utils import repo_root

SHA_A, SHA_B, SHA_C = "a" * 64, "b" * 64, "c" * 64
REGISTRY = """asset_key,override_for,类别,语言维度,状态,待无字化,适用机型,适用区域,导出物路径,语言变体,内容哈希,备注
web/x/eu/en/one,,插图,按语言,✅成品,FALSE,JE-X,EU,p,en,one.png:{a},source note stays off the page
web/all/icon,,图标,中立,✅成品,FALSE,ALL,ALL,p,,icon.svg:{b},
web/y/us/multi,,插图,按语言,🔧临时替代,FALSE,JE-Y,US,p,"en,fr",,
""".format(a=SHA_A, b=SHA_B)


def publication(model: str, region: str, lang: str, url: str) -> dict:
    return {"model": model, "region": region, "lang": lang, "language_scope": "single", "url": url}


def render(template: str, **context) -> BeautifulSoup:
    env = Environment(loader=FileSystemLoader(ASSETS))
    nav = {"system": True, "deliverables": True, "design": True, "matrix": True}
    if template == INVENTORY:
        # 视觉媒体's inventory is a macro shown at the foot of 设计规范 › 图标与素材.
        source = env.from_string('{% import "_media_inventory.html" as inv with context %}'
                                 "{{ inv.media_inventory(layer) }}")
    else:
        source = env.get_template(template)
    page = source.render(site_nav=nav, pathto=lambda name, *args: name, **context)
    return BeautifulSoup(page, "html.parser")


INVENTORY = "_media_inventory.html"


class MediaTests(unittest.TestCase):
    def test_registry_counts_scopes_and_keeps_notes_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / am.ASSET_REGISTRY_CSV
            path.write_text(REGISTRY, encoding="utf-8")
            view = am.registry_view(path)
            self.assertIsNone(am.registry_view(Path(tmp) / "missing.csv"))
        self.assertEqual((view["total"], view["finished"], view["neutral"], view["every_model"], view["hashed"]),
                         (3, 2, 1, 1, 2))
        self.assertEqual(view["filters"]["language"], ["en", "fr"])
        self.assertEqual(view["filters"]["model"], ["ALL", "JE-X", "JE-Y"])
        items = {item["key"]: item for item in view["items"]}
        self.assertEqual(items["web/y/us/multi"]["status"], "临时替代")
        self.assertEqual(items["web/x/eu/en/one"]["hash"], SHA_A[:12])
        self.assertEqual(view["items"][-1]["key"], "web/y/us/multi")  # unfinished rows come last
        self.assertNotIn("source note", json.dumps(view, ensure_ascii=False))

    def test_symbol_use_is_counted_from_the_published_pages_by_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, src = Path(tmp) / "repo", Path(tmp) / "src"
            manifest = root / REGISTRIES["symbols"][0]
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({"assets": [
                {"key": "warning/a", "path": "native-v1/a.svg", "sha256": SHA_A, "status": "ok",
                 "provenance": {"source": "x"}},
                {"key": "unused/c", "path": "native-v1/c.svg", "sha256": SHA_C, "status": "ok"}],
                "withdrawn": [SHA_B]}), encoding="utf-8")
            pages = [publication("JE-X", "EU", "en", "JE-X/EU/en/md/m_en.html"),
                     publication("JE-X", "EU", "de", "JE-X/EU/de/md/m_de.html"),
                     publication("JE-Y", "US", "en", "JE-Y/US/en/md/m.html")]
            for item, body in zip(pages, [f'<img src="../../_static/manual-assets/_pool/aa/{SHA_A}.svg">'] * 2
                                  + [f"_pool/bb/{SHA_B}.svg"], strict=True):
                path = (src / item["url"]).with_suffix(".md")
                path.parent.mkdir(parents=True)
                path.write_text(body, encoding="utf-8")
            view = am.symbols_view(root, src, pages + [publication("JE-Z", "JP", "ja", "missing.html")])
            without_pages = am.symbols_view(root, src, [])
            self.assertIsNone(am.symbols_view(Path(tmp), src, pages))
        self.assertEqual((view["total"], view["with_source"], view["withdrawn"], view["pages"], view["used"]),
                         (2, 1, 1, 3, 1))
        self.assertEqual([(r["key"], r["versions"], r["editions"]) for r in view["rows"]],
                         [("warning/a", 2, 1), ("unused/c", 0, 0)])
        # Nothing published to read: no count at all, never 0.
        self.assertEqual((without_pages["counted"], without_pages["used"]), (False, None))
        self.assertEqual({row["versions"] for row in without_pages["rows"]}, {None})


class LayerViewTests(unittest.TestCase):
    def test_layers_follow_the_priority_order(self):
        self.assertEqual([(layer["order"], layer["title"]) for layer in al.LAYERS],
                         [(1, "产品信息"), (2, "内容与表现"), (3, "视觉媒体"), (4, "语料库")])
        self.assertEqual(al.layer_entries(False)[0]["page"], "products/knowledge")

    def test_corpus_page_without_the_snapshot_says_so_plainly(self):
        view = al.language_view(None)
        self.assertIsNone(view["corpus"])
        page = render("asset_language.html", layer=view)
        self.assertEqual(page.select_one(".fr-head h1").get_text(), "语料库")
        self.assertEqual(page.select_one(".fr-empty").get_text(), "暂时没有可显示的语料数字。")
        self.assertIsNone(page.select_one("section.al-block"))

    def test_corpus_page_shows_counts_dated_once_and_each_language(self):
        # 语料库 方案甲 (step 13): pairs and terms with how many are approved, the languages, then per language.
        corpus = {"exported_at": "2026-11-01",
                  "counts": {"pairs": 1200, "pairs_approved": 900, "terms": 30, "terms_approved": 20, "languages": 1},
                  "rows": [{"label": "English", "count": 5, "count_text": "5", "percent": 100, "terms": 3,
                            "terms_text": "3"},
                           {"label": "Deutsch", "count": 0, "count_text": "0", "percent": 0, "terms": 0,
                            "terms_text": "0"}]}
        page = render("asset_language.html", layer=al.language_view({"corpus": corpus}))
        self.assertEqual(page.select_one(".fr-head p").get_text(), "已批准的术语和标准句，多语言对照 · 更新于 2026-11-01")
        self.assertEqual([d.get_text(" ") for d in page.select(".fr-figs div")],
                         ["1,200 组句子，其中 900 组已批准", "30 个术语，其中 20 个已批准", "1 种语言"])
        rows = page.select(".fr-langs tbody tr")
        self.assertEqual([(r.th.get_text(), r.select("td")[0].get_text(), r.select("td")[2].get_text()) for r in rows],
                         [("English", "5", "3")])
        self.assertNotIn("%", "".join(td.get_text() for td in page.select(".fr-langs td")))
        # How agents use the corpus: the operator's three uses today and one example ask, no skill names.
        uses = page.select_one("#agent-uses")
        self.assertEqual([li.b.get_text() for li in uses.select("li")], ["改飞书云文档", "改 AI 格式文件", "自己调用代码"])
        self.assertIn("「按语料库把这篇飞书云文档改成韩语」", uses.get_text())
        self.assertNotIn("Markdown", uses.get_text())

    def test_the_language_figure_is_the_number_of_languages_listed(self):
        # The export counts languages with pairs; the table also lists a language that has only terms. The figure
        # follows the table, whatever the export's own count says.
        row = {"count_text": "", "percent": 0, "terms_text": ""}
        corpus = {"exported_at": "2026-11-01",
                  "counts": {"pairs": 5, "pairs_approved": 5, "terms": 4, "terms_approved": 4, "languages": 1},
                  "rows": [{**row, "label": "English", "count": 5, "terms": 3}, {**row, "label": "Deutsch", "count": 0, "terms": 1},
                           {**row, "label": "Français", "count": 0, "terms": 0}]}
        page = render("asset_language.html", layer=al.language_view({"corpus": corpus}))
        rows = page.select(".fr-langs tbody tr")
        self.assertEqual([r.th.get_text() for r in rows], ["English", "Deutsch"])
        self.assertEqual(page.select(".fr-figs div")[2].get_text(" "), f"{len(rows)} 种语言")

    def test_corpus_languages_are_named_as_the_manual_library_names_them(self):
        corpus = {"rows": [{"code": "en", "label": "英语"}, {"code": "jp", "manual": "ja", "label": "日语"},
                           {"code": "xx", "label": "未列语言"}]}
        view = al.language_view({"corpus": corpus}, {"en": "English", "ja": "日本語"})
        self.assertEqual([row["label"] for row in view["corpus"]["rows"]], ["English", "日本語", "未列语言"])
        self.assertEqual(corpus["rows"][0]["label"], "英语")  # 系统建设's own copy is untouched


class TemplateTests(unittest.TestCase):
    def test_pages_render_without_data_and_never_show_zero_for_unknown(self):
        media = {**al.layer("media"), "build_date": "2026-11-16", "registry": None, "symbols": None}
        for template, view in ((INVENTORY, media),):
            page = render(template, layer=view)
            figures = [fig.strong.get_text() for fig in page.select("#scale .al-fig")]
            self.assertTrue(figures and set(figures) == {"待统计"}, (template, figures))
            self.assertIn("无数据", page.select_one("#inventory").get_text())

    def test_media_list_carries_its_filter_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / am.ASSET_REGISTRY_CSV
            path.write_text(REGISTRY, encoding="utf-8")
            view = {**al.layer("media"), "build_date": "2026-11-16", "registry": am.registry_view(path),
                    "symbols": None}
        page = render(INVENTORY, layer=view)
        rows = page.select("[data-al-list] tbody tr")
        self.assertEqual([row["data-languages"] for row in rows], ["", "en", "en fr"])  # finished first, by type
        self.assertEqual(rows[0]["data-neutral"], "true")
        self.assertTrue(page.select_one("[data-al-filters]").has_attr("hidden"))  # shown by the script only
        self.assertNotIn("ALL", [o.get_text() for o in page.select('[data-al-filter="model"] option')])
        self.assertIn("没有版本字段", page.select_one("#gaps").get_text())

    def test_media_front_shows_types_tiles_and_no_maintenance_detail(self):
        library = {"groups": [
            {"id": "symbols", "title": "通用符号", "items": [
                {"ref": "symbols/a.svg", "note": "警告与注意符号：提醒读者。", "ground": "paper", "key": "warning/a"},
                {"ref": "symbols/b.svg", "note": None, "ground": "paper", "key": "other/b"}]},
            {"id": "buttons", "title": "按键", "items": [
                {"ref": "buttons/c.svg", "note": "<code>电源</code>键。", "ground": "dark", "key": None}]}]}
        symbols = {"rows": [{"key": "warning/a", "editions": 3}, {"key": "other/b", "editions": None}]}
        view = am.front_view(library, {"paper": "#fff", "dark": "#222"}, symbols, build_date="2026-11-17")
        self.assertEqual([(i["label"], i["editions"], i["background"]) for i in view["items"]],
                         [("警告与注意符号", 3, "#fff"), ("", None, "#fff"), ("电源键", None, "#222")])
        page = render("asset_media.html", media=view)
        self.assertEqual(page.select_one(".fr-head p").get_text(), "说明书里共用的图标和插图 · 更新于 2026-11-17")
        self.assertEqual([d.get_text(" ") for d in page.select(".fr-figs div")], ["2 通用符号", "1 按键"])
        tiles = page.select(".mf-grid > li")
        self.assertEqual([(t["data-type"], t.img["src"]) for t in tiles],
                         [("symbols", "workspace/design/assets/symbols/a.svg"),
                          ("symbols", "workspace/design/assets/symbols/b.svg"),
                          ("buttons", "workspace/design/assets/buttons/c.svg")])
        self.assertEqual(tiles[0].button["data-mf-used"], "3")
        self.assertTrue(page.select_one("[data-mf-filters]").has_attr("hidden"))
        text = page.select_one("main").get_text()
        for word in ("哈希", "warning/a", ".svg", "REV-", "成品", "规模"):
            self.assertNotIn(word, text, word)
        self.assertIsNone(page.select_one("section.al-block, .al-eyebrow, .al-chip"))
        self.assertIsNone(am.front_view(None, {}, None, build_date="2026-11-17"))
        empty = render("asset_media.html", media=None)
        self.assertEqual(empty.select_one(".fr-empty").get_text(), "暂时没有可显示的素材。")


if __name__ == "__main__":
    unittest.main()


class LayerDataTests(unittest.TestCase):
    """asset_layers.yaml: chips only from ledger rows, regrouping moves items only, the path cites rows or quotes."""

    LEDGER = "\n".join(f'| <a id="rev-{n:02d}"></a>REV-{n:02d} | x | — | y | {state} | z |' for n, state in
                       ((11, "done"), (15, "planned"), (18, "planned"), (35, "planned"), (36, "planned"),
                        (37, "planned"), (38, "planned"), (41, "done"), (42, "deferred"), (43, "deferred"),
                        (50, "planned"), (52, "planned"), (60, "deferred")))

    def data(self):
        return ald.load_layer_data(ASSETS)

    def test_chips_come_from_ledger_rows_only(self):
        ledger = sw.parse_ledger(self.LEDGER)
        chips = ald.layer_chips(self.data(), ledger)
        self.assertEqual({layer: chip and chip["status_label"] for layer, chip in chips.items()},
                         {"product": "已规划", "content": "建设中", "media": None, "language": "建设中"})
        self.assertIsNone(ald.chip(["REV-60"], ledger))  # every row deferred: no chip
        self.assertEqual(ald.chip(["REV-11"], ledger)["status"], "validated")
        self.assertEqual(ald.layer_chips(self.data(), None), dict.fromkeys(ald.LAYER_IDS))
        with self.assertRaises(ald.LayerDataError):
            ald.chip(["REV-99"], ledger)  # a row the ledger lacks is an authoring error
        # Only the portal's status words.
        self.assertTrue(set(ald.CHIP_STATUS.values()) <= set(sw.STATUS_LABELS))

    def test_regrouping_places_every_item_once_and_changes_nothing(self):
        contract = sw.load_contract(ASSETS / sw.CONTRACT_NAME)
        cards = [{"id": card["id"], "entries": [{"id": item["id"], "status": item["status"],
                                                 "evidence": item["evidence"]} for item in card["items"]]}
                 for card in contract["capabilities"]]
        result = ald.capability_map(self.data(), cards)
        regrouped = [(e["card"], e["id"], e["status"], tuple(e["evidence"]))
                     for layer in ald.LAYER_IDS for e in result["layers"][layer]["entries"]]
        kept = [(card["id"], e["id"], e["status"], tuple(e["evidence"]))
                for card in result["production"] for e in card["entries"]]
        original = [(card["id"], e["id"], e["status"], tuple(e["evidence"])) for card in cards for e in card["entries"]]
        self.assertEqual(sorted(regrouped + kept), sorted(original))
        self.assertEqual(result["layers"]["language"]["anchors"], ["language"])
        self.assertEqual(result["layers"]["content"]["anchors"], ["content_foundation"])
        broken = self.data()
        broken["items"]["media"] = []  # content_foundation.asset_library now placed nowhere
        with self.assertRaises(ald.LayerDataError):
            ald.capability_map(broken, cards)

    def test_path_stages_without_rows_quote_the_positioning_document(self):
        ledger = sw.parse_ledger(self.LEDGER)
        path = ald.path_view(self.data(), ledger, "https://example.invalid/doc")
        self.assertTrue(path["link"].startswith("https://example.invalid/doc#"))
        chips = {stage["id"]: stage["chip"] for stage in path["stages"]}
        self.assertIsNone(chips["web"])
        self.assertEqual(chips["matrix"]["revs"], ["REV-50"])

    def test_wording_is_kept_once(self):
        text = (ASSETS / ald.DATA_NAME).read_text(encoding="utf-8")
        data = self.data()
        self.assertEqual(text.count(data["main_line"]), 1)
        self.assertEqual(sum(line.startswith("umbrella:") for line in text.splitlines()), 1)


class PositioningQuoteTests(unittest.TestCase):
    def test_path_quotes_are_word_for_word_from_the_positioning_document(self):
        doc = (repo_root() / "code-as-doc" / "architecture" / "Hello_Docs_Positioning.md").read_text(encoding="utf-8")
        if "### 4.2" not in doc:
            self.skipTest("positioning §4.2 not on this branch yet (#1734)")
        plain = doc.replace("**", "")
        data = ald.load_layer_data(ASSETS)
        for stage in data["path"]["stages"]:
            self.assertIn(stage["quote"], plain, stage["id"])
        joined = plain.replace("\n", "")
        self.assertIn(yaml_value("boundary"), joined)
        self.assertIn(data["main_line"], joined)
        # The operator's value statement, both of its sentences, as §4.1 carries it.
        for sentence in statement().split("。")[:-1]:
            self.assertIn(sentence + "。", joined)
        self.assertIn(sw.load_contract(ASSETS / sw.CONTRACT_NAME)["hero"]["subtitle"], joined)


def yaml_value(key: str) -> str:
    import yaml

    return yaml.safe_load((ASSETS / ald.DATA_NAME).read_text(encoding="utf-8"))["path"][key]


def statement() -> str:
    """The operator's value statement, read from the data file itself: no code loads it any more."""
    import yaml

    return yaml.safe_load((ASSETS / ald.DATA_NAME).read_text(encoding="utf-8"))["product_value"].strip()


class CuratedTests(unittest.TestCase):
    def test_an_unreadable_ledger_warns_and_shows_no_chip(self):
        from tools.rtd import asset_pages

        warnings = []
        with tempfile.TemporaryDirectory() as tmp:  # a repository root without the ledger file
            view = asset_pages.curated(ASSETS, Path(tmp), None, lambda *args: warnings.append(args[0] % args[1:]))
        self.assertEqual(view["chips"], dict.fromkeys(ald.LAYER_IDS))
        self.assertTrue(any("ledger" in warning for warning in warnings), warnings)


class ProductValueTests(unittest.TestCase):
    def test_the_operator_statement_is_shown_on_no_page(self):
        # Operator, 2026-11-17: 「我写的那段价值定位不用显示在页面上」. The data file keeps it, once.
        value = statement()
        self.assertTrue(value)
        self.assertEqual((ASSETS / ald.DATA_NAME).read_text(encoding="utf-8").count(value), 1)
        self.assertNotIn(value, json.dumps(ald.load_layer_data(ASSETS), ensure_ascii=False))
        cards = json.dumps(ap.front_cards({"facts": {"products": 3}, "built_on": "2026-11-17"}, None, None),
                           ensure_ascii=False)
        self.assertNotIn(value, cards)
        page = render("product_matrix.html", built=False, problem="还没有产品数据。")
        self.assertNotIn(value[:12], page.get_text())
        self.assertEqual(page.select_one(".fr-head").get_text(), "产品库")


class HeadlineTests(unittest.TestCase):
    def test_system_headline_is_the_approved_sentence_without_its_removed_clause(self):
        hero = sw.load_contract(ASSETS / sw.CONTRACT_NAME)["hero"]
        self.assertEqual(hero["subtitle"], "以网页说明书为入口，把产品信息、内容与表现、视觉媒体、语言管成有来源、可核实的资产。")
        self.assertIn("ack:操作者 2026-11-16「都按建议」", hero["evidence"])
