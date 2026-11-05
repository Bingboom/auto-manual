"""Learning references must remain tied to actual publication identities."""
import json
import re
import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from jinja2 import Environment, FileSystemLoader
from markupsafe import escape

from tools.rtd.portal import ASSETS
from tools.rtd.product_learning import learning_context
from tools.rtd.product_matrix import ProductMatrixError


class LearningFixtures:
    """Settings, products, a changeable copy of the assets and the page renderer, for both test classes."""

    def setUp(self):
        self.settings = json.loads((ASSETS / "settings.json").read_text())

    def product(self, model, region, language):
        return {"model": model, "region": region, "name": model,
                "url": f"{model}/{region}/{language}/real.html",
                "language_options": [{"code": language, "label": language,
                                      "url": f"{model}/{region}/{language}/real.html"}]}

    def assets(self):
        """The shipped curriculum, product-matrix config and teaching circuits, in a folder a test may change."""
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        for name in ("product_knowledge.json", "product_matrix.json"):
            shutil.copy(ASSETS / name, Path(temp.name, name))
        (Path(temp.name) / "_static").mkdir()
        for circuit in (ASSETS / "_static").glob("circuit-*.svg"):
            shutil.copy(circuit, Path(temp.name, "_static", circuit.name))
        return Path(temp.name)

    def render(self, context):
        template = Environment(loader=FileSystemLoader(ASSETS)).get_template("product_knowledge.html")
        return template.render(**context, pathto=lambda path, *args: path, site_nav={})


class ProductLearningTests(LearningFixtures, unittest.TestCase):
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
            with self.subTest(field=field, value=value):
                folder = self.assets()
                data = json.loads((folder / "product_knowledge.json").read_text())
                data["topics"][0][field] = value
                (folder / "product_knowledge.json").write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    learning_context(folder, self.settings, [])

    def test_every_model_the_navigation_or_the_matrix_places_has_knowledge(self):
        matrix = json.loads((ASSETS / "product_matrix.json").read_text())
        models = sorted({model for rows in self.settings["navigation"].values() for row in rows
                         for model in row["models"]} | set(matrix["assign"]))
        context = learning_context(ASSETS, self.settings, [self.product(model, "US", "en") for model in models])
        topics = {model: [t["id"] for t in context["topics"] if model in t["models"]] for model in models}
        self.assertEqual([model for model in models if not topics[model]], [])
        # Models the navigation does not list reach their topics through the matrix config.
        for model in ("JHP-3600C", "JE-1500C", "JBP-5000A"):
            self.assertGreater(len(topics[model]), 0, model)
        self.assertEqual(len(context["learning_products"]), len(models))

    def test_the_product_selector_offers_only_products_with_knowledge(self):
        products = [self.product("JE-1500C", "US", "en"), self.product("JE-NOT-LISTED", "EU", "en")]
        context = learning_context(ASSETS, self.settings, products)
        self.assertEqual([p["model"] for p in context["learning_products"]], ["JE-1500C"])
        page = self.render(context)
        self.assertIn('<option value="JE-1500C" data-region="US">', page)
        self.assertNotIn('value="JE-NOT-LISTED"', page)

    def test_an_unusable_matrix_config_falls_back_to_the_navigation_with_a_warning(self):
        shipped = json.loads((ASSETS / "product_matrix.json").read_text())
        configs = {"missing": None, "corrupted": "{not json", "not an object": "[]",
                   "no tiers": json.dumps({key: value for key, value in shipped.items() if key != "tiers"}),
                   "unknown group": json.dumps({**shipped, "assign": {"JE-1500C": "nowhere"}})}
        products = [self.product("JE-1000F", "EU", "en"), self.product("JE-1500C", "US", "en"),
                    self.product("JHP-3600C", "US", "en")]
        for label, config in configs.items():
            with self.subTest(label), patch("sphinx.util.logging.getLogger") as get_logger:
                folder = self.assets()
                if config is None:
                    (folder / "product_matrix.json").unlink()
                else:
                    (folder / "product_matrix.json").write_text(config, encoding="utf-8")
                context = learning_context(folder, self.settings, products)
                warning = get_logger.return_value.warning
                warning.assert_called_once()
                message, error, empty = warning.call_args.args
                self.assertIn("navigation groups only", message)
                self.assertIsInstance(error, ProductMatrixError)
                # A group only the matrix config defines is empty instead of failing the build.
                self.assertEqual(empty, "homebackup")
                inverter = next(t for t in context["topics"] if t["id"] == "inverter")
                self.assertEqual([r["model"] for r in inverter["references"]], ["JE-1000F"])
                self.assertEqual([p["model"] for p in context["learning_products"]], ["JE-1000F"])

    def test_the_homepower_case_renders_only_with_its_published_route(self):
        others = [self.product("JE-1000F", "EU", "en"), self.product("JHP-3600C", "JP", "ja")]
        context = learning_context(ASSETS, self.settings, others)
        self.assertIsNone(context["backup_case"])
        page = self.render(context)
        self.assertNotIn('class="backup-example', page)
        self.assertNotIn("JHP-3600C/US", page)
        context = learning_context(ASSETS, self.settings, [*others, self.product("JHP-3600C", "US", "en")])
        self.assertEqual(context["backup_case"]["url"], "JHP-3600C/US/en/real.html")
        page = self.render(context)
        self.assertIn('class="backup-example pk-case"', page)
        self.assertIn('<a href="JHP-3600C/US/en/real">HomePower 3600 Pro Max 说明书（美规 · 英文）</a>', page)


class KnowledgeMapTests(LearningFixtures, unittest.TestCase):
    """The 2026-11 layout: the energy-flow and theme maps lead into the cards; circuits only where named."""

    def setUp(self):
        super().setUp()
        products = [self.product(model, region, "en")
                    for model, region in (("JE-1000F", "EU"), ("JE-1000F", "US"), ("JS-100I", "EU"))]
        self.context = learning_context(ASSETS, self.settings, products)
        self.page = self.render(self.context)

    def test_each_theme_lists_its_topics_by_short_label(self):
        topics, themes = self.context["topics"], self.context["themes"]
        self.assertEqual([theme["id"] for theme in themes], [tag["id"] for tag in self.context["tags"]])
        for theme in themes:
            with self.subTest(theme=theme["id"]):
                self.assertEqual([item["id"] for item in theme["topics"]],
                                 [topic["id"] for topic in topics if theme["id"] in topic["tags"]])
                self.assertEqual(self.context["tag_counts"][theme["id"]], len(theme["topics"]))
        labels = {item["id"]: item["label"] for theme in themes for item in theme["topics"]}
        self.assertEqual(labels["watts"], "能不能启动")
        self.assertEqual(labels["ports-pd"], next(t["title"] for t in topics if t["id"] == "ports-pd"))
        self.assertEqual(self.context["latest_added"], max(t["added"] for t in topics if t.get("added")))

    def test_the_maps_lead_to_cards_and_set_themes(self):
        cards = set(re.findall(r'<article class="pk-card knowledge-item[^"]*" id="([a-z0-9-]+)"', self.page))
        self.assertEqual(cards, {topic["id"] for topic in self.context["topics"]})
        self.assertTrue(set(re.findall(r'data-topic-link="([a-z0-9-]+)"', self.page)) <= cards)
        tag_ids = {tag["id"] for tag in self.context["tags"]}
        flow = re.findall(r'data-flow-tag="([a-z]+)"', self.page)
        self.assertEqual(flow, ["charging", "battery", "inverter", "expansion", "backup"])
        self.assertTrue(set(flow) <= tag_ids)
        self.assertEqual(set(re.findall(r'data-theme="([a-z]+)"', self.page)), tag_ids)
        self.assertIn(f"{self.context['tag_titles']['battery']} · {self.context['tag_counts']['battery']} 条", self.page)

    def test_each_card_shows_its_circuit_drawing_or_chain(self):
        """Circuits only where a topic names one (that card puts it above the text); the hand-drawn diagrams stay
        svg; every other topic's nodes become a chain of HTML steps, legible in the narrow figure column."""
        circuits = {topic["id"]: topic["circuit"] for topic in self.context["topics"] if topic.get("circuit")}
        self.assertEqual(circuits, {"inverter": "circuit-inverter.svg", "ac-total": "circuit-parallel.svg",
                                    "ups": "circuit-transfer.svg"})
        drawn = {"split-phase", "nema-sockets", "region-grid", "transfer-switch"}
        for topic in self.context["topics"]:
            card = re.search(r'<article [^>]*id="%s".*?</article>' % re.escape(topic["id"]), self.page, re.S).group(0)
            with self.subTest(topic=topic["id"]):
                self.assertEqual(card.startswith('<article class="pk-card knowledge-item is-circuit"'),
                                 topic["id"] in circuits)
                if topic["id"] in circuits:
                    self.assertIn(f'src="_static/{circuits[topic["id"]]}"', card)
                    self.assertNotIn("<svg viewBox", card)
                    self.assertNotIn("pk-chain", card)
                elif topic["id"] in drawn:
                    self.assertIn("<svg viewBox", card)
                    self.assertNotIn("pk-chain", card)
                else:
                    steps = "</li><li>".join(str(escape(node)) for node in topic["diagram_nodes"])
                    self.assertIn(f'<ol class="pk-chain"><li class="is-source">{steps}</li></ol>', card)
                    self.assertNotIn("<svg viewBox", card)
                    self.assertNotIn("circuit-art", card)

    def test_an_unknown_circuit_blocks_authoring(self):
        for circuit in ("circuit-missing.svg", "../site-shell.css", "inverter.png"):
            with self.subTest(circuit=circuit):
                folder = self.assets()
                data = json.loads((folder / "product_knowledge.json").read_text())
                data["topics"][0]["circuit"] = circuit
                (folder / "product_knowledge.json").write_text(json.dumps(data))
                with self.assertRaisesRegex(ValueError, "unknown circuit"):
                    learning_context(folder, self.settings, [])

    def test_each_card_lists_its_manuals_with_their_region(self):
        card = re.search(r'id="inverter".*?</article>', self.page, re.S).group(0)
        refs = re.findall(r'<a class="pk-ref" data-region="([A-Z]+)" data-model="([A-Z0-9-]+)"', card)
        self.assertEqual(refs, [("EU", "JE-1000F"), ("US", "JE-1000F")])
        self.assertIn('<span class="reference-count">2</span> 本', card)


if __name__ == "__main__":
    unittest.main()
