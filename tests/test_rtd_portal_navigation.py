"""说明书资料库 groups manuals by the 网页文档 table's 产品类别, then 产品系列."""
import copy
import json
import unittest

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from tools.rtd.portal import ASSETS
from tools.rtd.portal_navigation import library_view
from tools.rtd.product_catalog import classify

SETTINGS = json.loads((ASSETS / "settings.json").read_text(encoding="utf-8"))
CATALOG = {
    "categories": [{"name": "便携电源", "series": ["标准", "Plus"]}, {"name": "家庭备电", "series": ["HomePower"]},
                   {"name": "新类别", "series": ["新系列"]}],
    "models": {"JE-1000F": {"category": "便携电源", "series": "标准", "short": "E1000V2"},
               "JE-100C": {"category": "便携电源", "series": "标准", "short": "E100D"},
               "JE-1000H": {"category": "便携电源", "series": "Plus", "short": "E1000Plusv2"},
               "JHP-3000D": {"category": "家庭备电", "series": "HomePower", "short": "HP3000"},
               "JX-1": {"category": "新类别", "series": "新系列", "short": "X1"}},
}


def product(model, region="EU", name=None, category="Power stations"):
    return {"model": model, "region": region, "name": name or model, "category": category,
            "url": f"{model}/{region}/md/manual.html", "image": "", "edition": region, "version": None,
            "language_scope": "legacy_unspecified", "language_options": [], "publications": []}


def products():
    items = [product("JE-1000F", "EU", "Explorer 1000"), product("JE-100C", "EU", "Explorer 100D"),
             product("JE-1000H", "EU", "Explorer 1000 Plus"), product("JHP-3000D", "US", "HomePower 3000"),
             product("JX-1", "EU", "X One"), product("JE-NEW", "EU", "New One")]
    classify(items, CATALOG)
    return items


class LibraryViewTests(unittest.TestCase):
    def test_categories_and_series_keep_the_table_order_and_unlisted_models_go_to_other(self):
        view = library_view(SETTINGS, products(), CATALOG)
        self.assertTrue(view["classified"])
        self.assertEqual([(c["id"], c["title"], c["icon"]) for c in view["categories"]],
                         [("portable", "便携电源", "portable"), ("home", "家庭备电", "home"),
                          ("category-3", "新类别", "other"), ("other", "其他说明书", "other")])
        portable = view["categories"][0]
        self.assertEqual([(s["id"], s["title"]) for s in portable["series"]], [("portable-1", "标准"), ("portable-2", "Plus")])
        # Natural model order inside a series: JE-100C before JE-1000F.
        self.assertEqual([p["model"] for p in portable["series"][0]["products"]], ["JE-100C", "JE-1000F"])
        self.assertEqual(portable["models"], 3)
        self.assertEqual([p["model"] for p in view["categories"][-1]["series"][0]["products"]], ["JE-NEW"])
        self.assertEqual(view["categories"][-1]["series"][0]["title"], "")

    def test_an_empty_series_or_category_is_left_out(self):
        view = library_view(SETTINGS, [p for p in products() if p["model"] != "JE-1000H"], CATALOG)
        self.assertEqual([s["title"] for s in view["categories"][0]["series"]], ["标准"])
        view = library_view(SETTINGS, [p for p in products() if p["model"] in ("JE-1000F",)], CATALOG)
        self.assertEqual([c["title"] for c in view["categories"]], ["便携电源"])

    def test_without_a_snapshot_the_page_groups_by_product_type(self):
        items = [product("JE-500A"), product("JS-100F", category="Solar panels")]
        view = library_view(SETTINGS, items, None)
        self.assertFalse(view["classified"])
        self.assertEqual([(c["title"], c["series"][0]["title"]) for c in view["categories"]],
                         [("便携储能", ""), ("太阳能板", "")])

    def test_the_category_styles_are_checked(self):
        for mutate, message in (
                (lambda s: s["catalog_categories"]["便携电源"].update(id="Bad Id"), "lower-case id"),
                (lambda s: s["catalog_categories"]["便携电源"].update(icon=""), "icon"),
                (lambda s: s["catalog_categories"]["家庭备电"].update(id="portable"), "unique"),
                (lambda s: s["catalog_categories"]["家庭备电"].update(id="other"), "unique"),
                (lambda s: s.update(catalog_categories=[]), "map a category")):
            with self.subTest(message=message):
                settings = copy.deepcopy(SETTINGS)
                mutate(settings)
                with self.assertRaisesRegex(ValueError, message):
                    library_view(settings, products(), CATALOG)


class LibraryTemplateTests(unittest.TestCase):
    def render(self, items, catalog, internal=True):
        env = Environment(loader=FileSystemLoader(ASSETS))
        page = env.get_template("manual_portal.html").render(
            portal=SETTINGS, products=items, library=library_view(SETTINGS, items, catalog),
            pathto=lambda path, *args: path, site_nav={}, metatags="", product_voc="", internal_shell=internal)
        return BeautifulSoup(page, "html.parser")

    def test_a_chip_per_category_links_to_its_section_of_series_groups(self):
        page = self.render(products(), CATALOG)
        chips = page.select(".cat-chips .cat-chip")
        self.assertEqual([(a["href"], a.get_text(strip=True)) for a in chips],
                         [("#cat-portable", "便携电源"), ("#cat-home", "家庭备电"), ("#cat-category-3", "新类别"),
                          ("#cat-other", "其他说明书")])
        portable = page.select_one("section.family#cat-portable")
        self.assertEqual(portable["data-models"], "3")
        self.assertEqual([h.get_text() for h in portable.select(".group-head h3")], ["标准", "Plus"])
        cards = portable.select(".card")
        self.assertEqual({card["data-family"] for card in cards}, {"portable"})
        # Search also finds a manual by its series and category.
        self.assertIn("plus 便携电源", cards[-1]["data-search"])
        self.assertIsNotNone(portable.select_one("p.family-empty[hidden]"))
        # The unlisted model's group has no series heading.
        self.assertIsNone(page.select_one("#cat-other .group-head"))
        self.assertIsNone(page.select_one(".needs, .categories, button[data-category]"))

    def test_the_source_note_is_internal_and_needs_the_snapshot(self):
        self.assertIn("产品分类快照", self.render(products(), CATALOG).select_one(".catalog-source").get_text())
        self.assertIsNone(self.render(products(), CATALOG, internal=False).select_one(".catalog-source"))
        page = self.render([product("JE-500A")], None)
        self.assertIsNone(page.select_one(".catalog-source"))
        self.assertEqual([a.get_text(strip=True) for a in page.select(".cat-chip")], ["便携储能"])


if __name__ == "__main__":
    unittest.main()
