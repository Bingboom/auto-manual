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
    page = env.get_template(template).render(site_nav=nav, pathto=lambda name, *args: name, **context)
    return BeautifulSoup(page, "html.parser")


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
                         [(1, "产品信息"), (2, "内容与表现"), (3, "视觉媒体"), (4, "语言")])
        self.assertEqual(al.layer_entries(False)[0]["page"], "products/knowledge")
        self.assertEqual([page for page, _ in al.product_tabs(False)], ["products/attributes", "products/knowledge"])

    def test_attribute_dictionary_reads_the_shipped_definitions(self):
        view = al.attributes_view()
        self.assertGreater(view["total"], 0)
        self.assertTrue(all(item["key"] and item["definition"] for item in view["items"]))
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(al.attributes_view(Path(tmp) / "missing.json"))

    def test_content_view_reads_chapters_by_language(self):
        with tempfile.TemporaryDirectory() as tmp:
            templates = Path(tmp)
            for lang, stems in {"en": ["11_warranty", "02_whats_in_the_box"], "de": ["11_warranty"]}.items():
                (templates / "page_shared" / lang).mkdir(parents=True)
                for stem in stems:
                    (templates / "page_shared" / lang / f"{stem}.rst").write_text("x", encoding="utf-8")
            view = al.shared_chapters(templates)
            self.assertIsNone(al.shared_chapters(templates / "nowhere"))
        self.assertEqual((view["pages"], view["languages"]), (3, ["de", "en"]))
        self.assertEqual([(c["label"], c["langs"]) for c in view["chapters"]],
                         [("包装清单", ["en"]), ("保修", ["de", "en"])])

    def test_language_view_without_the_system_page_says_why(self):
        pubs = [publication("JE-X", "EU", "en", "a"), publication("JE-X", "EU", "de", "b"),
                publication("JE-Y", "US", "en", "c"), {"lang": None, "language_scope": "legacy_unspecified"}]
        view = al.language_view(None, pubs, root=repo_root(), labels={"en": "English"}, build_date="2026-11-16")
        self.assertIsNone(view["corpus"])
        self.assertEqual([(w["code"], w["label"], w["versions"]) for w in view["web"]],
                         [("en", "English", 2), ("de", "de", 1)])
        self.assertGreater(view["rules"]["total"], 0)
        page = render("asset_language.html", layer=view)
        self.assertIn("语料快照当前不可读", page.select_one("#inventory").get_text())
        self.assertEqual([b["id"] for b in page.select("section.al-block")],
                         ["scale", "maintained", "inventory", "used-by", "sources", "gaps"])


class TemplateTests(unittest.TestCase):
    def test_pages_render_without_data_and_never_show_zero_for_unknown(self):
        content = {**al.layer("content"), "build_date": "2026-11-16", "chapters": None, "skeletons": None,
                   "recipes": None, "recipe_sets": [], "families": None, "components": None,
                   "design_tabs": al.DESIGN_TABS, "web_languages": None}
        media = {**al.layer("media"), "build_date": "2026-11-16", "registry": None, "symbols": None}
        for template, view in (("asset_content.html", content), ("asset_media.html", media)):
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
        page = render("asset_media.html", layer=view)
        rows = page.select("[data-al-list] tbody tr")
        self.assertEqual([row["data-languages"] for row in rows], ["", "en", "en fr"])  # finished first, by type
        self.assertEqual(rows[0]["data-neutral"], "true")
        self.assertTrue(page.select_one("[data-al-filters]").has_attr("hidden"))  # shown by the script only
        self.assertNotIn("ALL", [o.get_text() for o in page.select('[data-al-filter="model"] option')])
        self.assertIn("没有版本字段", page.select_one("#gaps").get_text())


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
        self.assertIn(yaml_value("boundary"), plain)
        self.assertIn(data["main_line"].rstrip("。"), plain.replace("\n", ""))


def yaml_value(key: str) -> str:
    import yaml

    return yaml.safe_load((ASSETS / ald.DATA_NAME).read_text(encoding="utf-8"))["path"][key]


class CuratedTests(unittest.TestCase):
    def test_an_unreadable_ledger_warns_and_shows_no_chip(self):
        from tools.rtd import asset_pages

        warnings = []
        with tempfile.TemporaryDirectory() as tmp:  # a repository root without the ledger file
            view = asset_pages.curated(ASSETS, Path(tmp), None, lambda *args: warnings.append(args[0] % args[1:]))
        self.assertEqual(view["chips"], dict.fromkeys(ald.LAYER_IDS))
        self.assertTrue(any("ledger" in warning for warning in warnings), warnings)


class ProductValueTests(unittest.TestCase):
    def test_the_operator_statement_leads_the_product_pages_only(self):
        data = ald.load_layer_data(ASSETS)
        value = data["product_value"]
        self.assertEqual((ASSETS / ald.DATA_NAME).read_text(encoding="utf-8").count(value), 1)
        product = {**al.product_layer(None, {"total": 9}, topics=None, build_date="2026-11-16"), "value": value}
        page = render("product_attributes.html", product=product, attributes=None)
        self.assertEqual(page.select_one(".al-head-text > p:not(.al-eyebrow)").get_text(), value)
        # The page still says that the project index and the dates are not there yet.
        self.assertIn("建设中", page.select_one(".al-lead-note").get_text())
        cards = al.home_cards(product, {**al.layer("content")}, {**al.layer("media")}, {**al.layer("language")},
                              dict.fromkeys(ald.LAYER_IDS))
        self.assertNotIn(value, json.dumps(cards, ensure_ascii=False))
