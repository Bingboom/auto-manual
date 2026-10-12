"""Learning references must remain tied to actual publication identities."""
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.rtd.portal import ASSETS
from tools.rtd.product_learning import learning_context


class ProductLearningTests(unittest.TestCase):
    def setUp(self):
        self.settings = json.loads((ASSETS / "settings.json").read_text())

    def product(self, model, region, language):
        return {"model": model, "region": region, "name": model,
                "url": f"{model}/{region}/{language}/real.html",
                "language_options": [{"code": language, "label": language,
                                      "url": f"{model}/{region}/{language}/real.html"}]}

    def test_references_use_published_locale_and_region_only(self):
        products = [self.product("JE-1000F", "JP", "ja"), self.product("JE-1000F", "EU", "en"),
                    self.product("JS-100I", "EU", "en"), self.product("JE-NOT-LISTED", "EU", "en")]
        context = learning_context(ASSETS, self.settings, products)
        inverter = next(t for t in context["topics"] if t["id"] == "inverter")
        self.assertEqual([(r["region"], r["language"]) for r in inverter["references"]],
                         [("JP", "ja"), ("EU", "en")])
        self.assertNotIn("JS-100I", [r["model"] for r in inverter["references"]])
        published = {p["url"] for p in products}
        self.assertTrue(all(r["url"] in published for t in context["topics"] for r in t["references"]))

    def test_invalid_scope_and_tags_block_authoring(self):
        for field, value in (("tags", ["missing-tag"]), ("groups", ["missing-model-group"]),
                             ("groups", []), ("tags", [])):
            with self.subTest(field=field, value=value), TemporaryDirectory() as folder:
                data = json.loads((ASSETS / "product_knowledge.json").read_text())
                data["topics"][0][field] = value
                Path(folder, "product_knowledge.json").write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    learning_context(Path(folder), self.settings, [])


if __name__ == "__main__":
    unittest.main()
