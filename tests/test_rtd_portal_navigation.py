"""Homepage navigation groups manuals by curated power need, per region."""
import copy
import json
import unittest

from jinja2 import Environment, FileSystemLoader

from tools.rtd.portal import ASSETS
from tools.rtd.portal_navigation import navigation_view

SETTINGS = json.loads((ASSETS / "settings.json").read_text(encoding="utf-8"))


def product(model, region="EU", name=None):
    return {"model": model, "region": region, "name": name or model, "category": "Power stations",
            "url": f"{model}/{region}/md/manual.html", "image": "", "edition": region, "version": None,
            "language_scope": "legacy_unspecified", "language_options": [], "publications": []}


class NavigationViewTests(unittest.TestCase):
    def test_every_product_lands_in_one_group_in_table_order(self):
        products = [product("JE-3000C"), product("JE-500A"), product("JBP-2000B"), product("JE-NEW")]
        view = navigation_view(SETTINGS, products)
        self.assertEqual([p["nav"] for p in products], ["appliance", "appliance", "battery", "other"])
        self.assertLess(products[1]["nav_rank"], products[0]["nav_rank"])
        self.assertEqual(view["other"]["models"], ["JE-NEW"])
        self.assertIsNone(navigation_view(SETTINGS, [product("JE-500A")])["other"])

    def test_without_navigation_the_category_layout_is_kept(self):
        settings = {k: v for k, v in SETTINGS.items() if k != "navigation"}
        self.assertIsNone(navigation_view(settings, [product("JE-500A")]))

    def test_the_curated_table_is_checked(self):
        for mutate, message in (
                (lambda n: n["needs"][1]["models"].append("JE-100C"), "two navigation groups"),
                (lambda n: n["ecosystem"].append(dict(n["ecosystem"][0], models=["X-1"])), "duplicate"),
                (lambda n: n["needs"][0].update(note=""), "needs rows need"),
                (lambda n: n["needs"][0].update(models=[]), "needs models"),
                (lambda n: n["ecosystem"][0].update(id="Bad Id"), "lower-case"),
                (lambda n: n.update(needs=[]), "non-empty")):
            with self.subTest(message=message):
                settings = copy.deepcopy(SETTINGS)
                mutate(settings["navigation"])
                with self.assertRaisesRegex(ValueError, message):
                    navigation_view(settings, [])


class HomepageTemplateTests(unittest.TestCase):
    def render(self, settings, products):
        env = Environment(loader=FileSystemLoader(ASSETS))
        template = env.get_template("manual_portal.html")
        return template.render(portal=settings, products=products, navigation=navigation_view(settings, products),
                               pathto=lambda path, *args: path, site_nav={}, metatags="", product_voc="")

    def test_needs_tiles_groups_and_filters_follow_the_table(self):
        products = [product("JE-1000F", "EU", "Explorer 1000"), product("JE-500A", "EU", "Explorer 500"),
                    product("JE-1000E-SIL", "US", "FridgeGuard"), product("JS-100F", "EU", "SolarSaga 100"),
                    product("JE-NEW", "EU", "New One")]
        page = self.render(SETTINGS, products)
        self.assertEqual(page.count('class="need"'), 4)
        self.assertLess(page.index("<i data-region=\"EU\">Explorer 500</i>"),
                        page.index("<i data-region=\"EU\">Explorer 1000</i>"))
        self.assertIn('<i data-region="US" hidden>FridgeGuard</i>', page)
        self.assertIn('data-group="appliance"', page)
        self.assertIn('data-filters="ecosystem|solar"', page)
        self.assertIn('class="family" data-family="ecosystem"', page)
        self.assertIn('data-group="other"', page)
        self.assertIn('data-category="dedicated"', page)
        self.assertNotIn('data-group="battery"', page)

    def test_without_navigation_the_page_groups_by_category(self):
        settings = {k: v for k, v in SETTINGS.items() if k != "navigation"}
        page = self.render(settings, [dict(product("JE-500A"), nav="x")])
        self.assertNotIn('class="needs"', page)
        self.assertIn('data-group="Power stations"', page)
        self.assertIn('data-filters="Power stations"', page)


if __name__ == "__main__":
    unittest.main()
