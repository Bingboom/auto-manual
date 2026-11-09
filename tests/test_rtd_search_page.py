"""搜索说明书正文: the search page's filters (regions, the library's categories, language display codes)."""
import json
import unittest

from tools.rtd.portal import ASSETS
from tools.rtd.portal_navigation import library_view
from tools.rtd.portal_search import search_page_context

SETTINGS = {
    "regions": {"US": "US", "EU": "EU", "UK": "EU", "JP": "JP"},
    "categories": ["Power stations", "Accessories"],
    "category_labels": {"Power stations": "便携储能", "Accessories": "配件"},
    "catalog_categories": {"便携电源": {"id": "portable", "icon": "portable"}},
    "language_labels": {"en": "English", "fr": "Français", "ja": "日本語"},
    "language_display_codes": {"en": "en-US", "fr": "fr-FR", "ja": "ja-JP"},
}
CATALOG = {"categories": [{"name": "便携电源", "series": ["标准", "Plus"]}, {"name": "家庭备电", "series": ["HomePower"]}]}


def product(model, region, category="", series=""):
    return {"model": model, "region": region, "category": "Power stations", "product_category": category,
            "product_series": series}


class SearchPageContextTests(unittest.TestCase):
    def test_filters_follow_the_settings_and_the_library_grouping(self):
        products = [product("JE-1000F", "US", "便携电源", "标准"), product("JE-1000F", "EU", "便携电源", "标准"),
                    product("JE-1000H", "US", "便携电源", "Plus"), product("JHP-3000D", "US", "家庭备电", "HomePower"),
                    product("JA-NEW", "US")]
        context = search_page_context(SETTINGS, library_view(SETTINGS, products, CATALOG))
        # UK reads the EU manuals, so it is no filter of its own.
        self.assertEqual(context["regions"], ["US", "EU", "JP"])
        self.assertEqual(context["categories"], [
            {"id": "portable", "title": "便携电源", "icon": "portable"},
            {"id": "category-2", "title": "家庭备电", "icon": "other"},
            {"id": "other", "title": "其他说明书", "icon": "other"},
        ])
        config = context["config"]
        self.assertEqual(config["models"], {
            "JE-1000F": {"category": "portable", "series": "标准"}, "JE-1000H": {"category": "portable", "series": "Plus"},
            "JHP-3000D": {"category": "category-2", "series": "HomePower"}, "JA-NEW": {"category": "other", "series": ""},
        })
        self.assertEqual(config["categories"], {"portable": "便携电源", "category-2": "家庭备电", "other": "其他说明书"})
        # Languages keep the settings order (it picks the edition a manual shows) and carry the display codes.
        self.assertEqual(config["languages"], [["en", "en-US"], ["fr", "fr-FR"], ["ja", "ja-JP"]])
        self.assertEqual(context["languages"][2], {"code": "ja", "display": "ja-JP", "label": "日本語"})
        self.assertEqual(config["legacy"], "语言待确认")
        json.dumps(config)  # the template embeds it as JSON

    def test_without_a_snapshot_the_product_types_are_the_categories(self):
        context = search_page_context(SETTINGS, library_view(SETTINGS, [product("JE-1000F", "US")], None))
        self.assertEqual([item["title"] for item in context["categories"]], ["便携储能"])
        self.assertEqual(context["config"]["models"], {"JE-1000F": {"category": "category-1", "series": ""}})

    def test_the_shipped_settings_give_every_language_a_display_code(self):
        settings = json.loads((ASSETS / "settings.json").read_text(encoding="utf-8"))
        context = search_page_context(settings, {"categories": []})
        self.assertEqual([code for code, _ in context["config"]["languages"]], list(settings["language_labels"]))
        # A language without a display code would show its bare code (zh-TW's code is its display code).
        self.assertLessEqual(set(settings["language_labels"]), set(settings["language_display_codes"]))


if __name__ == "__main__":
    unittest.main()
