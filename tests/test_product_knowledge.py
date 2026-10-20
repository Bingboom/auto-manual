"""Behavioral contract for downstream product knowledge consumers."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.product_knowledge import SCHEMA_VERSION, build_product_knowledge
from tools.rtd.product_matrix import matrix_context
from tools.utils.path_utils import Paths


class ProductKnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.paths = Paths(self.root)
        self.paths.data_dir.mkdir()
        self.registry = self.paths.data_dir / "model_capabilities.csv"
        self.registry.write_text("Document_key,Project,UPS功能,加电包扩容\n"
                                 "M_EU,P1,TRUE,FALSE\nM_US,P1,FALSE,TRUE\n", encoding="utf-8")
        (self.paths.data_dir / "model_languages.csv").write_text(
            "Document_key,languages\nM_EU,en;fr\nM_US,en\n", encoding="utf-8")
        self.assets = self.root / "assets"
        self.assets.mkdir()
        self.config = {"region_order": ["US", "EU"], "language_order": ["en", "fr"],
                       "lines": [{"id": "appliance"}, {"id": "homebackup", "title": "Home", "evidence": True}],
                       "accessories": [], "assign": {"H": {"line": "homebackup", "evidence": "home circuits"}},
                       "tiers": [{"label": "all"}], "pairings": [
                           {"model": "M", "parts": [{"label": "Battery Pack (B1)", "match": "Battery Pack"}]}]}
        self.write_config()
        self.settings = {"navigation": {"needs": [{"id": "appliance", "title": "Appliances", "models": ["M"]}]}}
        self.catalog = [{"model": "M", "region": "EU", "name": "European product"},
                        {"model": "M", "region": "US", "name": "US product"}]
        self.web = self.root / "frozen" / "web"
        self.targets = []
        for model, region, lang, capacity in (("M", "EU", "en", 1024), ("M", "EU", "fr", 768),
                                             ("M", "US", "en", 512), ("H", "EU", "en", 2048)):
            target = {"model": model, "region": region, "lang": lang, "version": "1.2",
                      "language_scope": "single", "route": f"{model}/{region}/{lang}/md",
                      "manual": "manual.md", "built_at": "2026-10-01T00:00:00Z", "git_ref": "abc123"}
            self.targets.append(target)
            path = self.web / target["route"] / target["manual"]
            path.parent.mkdir(parents=True)
            body = ("# SPECIFICATIONS\n<table>"
                    f"<tr><th>Capacity</th><td>{capacity} Wh</td></tr>"
                    f"<tr><th>Total AC Output</th><td>{capacity}W Rated, {capacity * 2}W Surge</td></tr>"
                    "<tr><th>Weight</th><td>12 kg</td></tr></table>\n")
            if region == "EU":
                body += "Use the Battery Pack. Supply backup power to home circuits."
            path.write_text(body, encoding="utf-8")
        self.manifest = {"built_at": "2026-10-02T00:00:00Z", "targets": self.targets}

    def write_config(self):
        (self.assets / "product_matrix.json").write_text(json.dumps(self.config), encoding="utf-8")

    def build(self):
        return build_product_knowledge(self.root, self.web, self.manifest, self.assets, self.settings, self.catalog)

    def product(self, snapshot, model="M", region="EU", language="en"):
        return next(p for p in snapshot["products"]
                    if (p["model"], p["region"], p["language"]) == (model, region, language))

    def test_market_and_language_facts_are_never_promoted_to_other_variants(self):
        snapshot = self.build()
        self.assertEqual(snapshot["schema_version"], SCHEMA_VERSION)
        self.assertEqual(len(snapshot["products"]), 4)
        self.assertEqual(self.product(snapshot)["specifications"]["capacity_wh"]["value"], 1024)
        self.assertEqual(self.product(snapshot, region="US")["specifications"]["capacity_wh"]["value"], 512)
        self.assertEqual(self.product(snapshot, language="fr")["specifications"]["capacity_wh"]["value"], 768)
        self.assertEqual(self.product(snapshot)["name"], "European product")
        self.assertEqual(self.product(snapshot, region="US")["name"], "US product")

    def test_manual_evidence_names_exact_route_hash_label_and_value(self):
        product = self.product(self.build())
        source = product["source"]
        expected_url = "M/EU/en/md/manual.html"
        self.assertEqual(source["url"], expected_url)
        self.assertEqual(source["sha256"], hashlib.sha256((self.web / "M/EU/en/md/manual.md").read_bytes()).hexdigest())
        fact = product["specifications"]["capacity_wh"]
        self.assertEqual((fact["state"], fact["unit"], fact["source_type"]), ("known", "Wh", "published_manual"))
        self.assertEqual(fact["evidence"], [{"source_type": "published_manual", "path": "M/EU/en/md/manual.md",
                                            "url": expected_url, "sha256": source["sha256"],
                                            "locator": "specifications/Capacity", "quote": "Capacity: 1024 Wh"}])

    def test_curated_placement_is_not_a_manual_fact(self):
        snapshot = self.build()
        category = self.product(snapshot)["category"]
        self.assertEqual((category["value"], category["source_type"]), ("appliance", "curated_configuration"))
        self.assertEqual(category["evidence"][0]["source_type"], "curated_configuration")
        home = self.product(snapshot, model="H")["category"]
        self.assertEqual(home["value"], "homebackup")
        self.assertEqual([e["source_type"] for e in home["evidence"]],
                         ["curated_configuration", "published_manual"])
        self.assertIn("home circuits", home["evidence"][1]["quote"])

    def test_classification_quote_disappearing_invalidates_only_that_publication(self):
        path = self.web / "H/EU/en/md/manual.md"
        path.write_text(path.read_text().replace("home circuits", "a portable appliance"))
        home = self.product(self.build(), model="H")
        self.assertEqual((home["category"]["value"], home["category"]["state"]), (None, "unknown"))

    def test_registry_false_and_absence_have_different_meanings(self):
        snapshot = self.build()
        eu, us, missing = self.product(snapshot), self.product(snapshot, region="US"), self.product(snapshot, model="H")
        self.assertIs(eu["capabilities"]["UPS功能"]["value"], True)
        self.assertIs(us["capabilities"]["UPS功能"]["value"], False)
        self.assertEqual(us["capabilities"]["UPS功能"]["state"], "known")
        self.assertEqual(us["capabilities"]["UPS功能"]["source_type"], "capability_registry")
        self.assertIsNone(missing["capabilities"]["UPS功能"]["value"])
        self.assertEqual(missing["capabilities"]["UPS功能"]["state"], "unknown")
        self.assertTrue(any(u["field"] == "capabilities.UPS功能" for u in missing["unknowns"]))

    def test_absent_specification_is_unknown_and_has_no_fabricated_evidence(self):
        product = self.product(self.build())
        for key in ("cycle_life", "solar_peak_w", "ip_rating", "output_w"):
            fact = product["specifications"][key]
            self.assertEqual((fact["value"], fact["state"], fact["evidence"]), (None, "unknown", []))
            self.assertTrue(fact["reason"])

    def test_named_products_require_each_variants_own_manual_quote(self):
        snapshot = self.build()
        relation = self.product(snapshot)["relations"][0]
        self.assertEqual((relation["kind"], relation["label"]), ("named_companion", "Battery Pack (B1)"))
        self.assertIn("Use the Battery Pack.", relation["evidence"][1]["quote"])
        self.assertEqual(self.product(snapshot, region="US")["relations"], [])
        self.assertEqual(relation["source_type"], "curated_configuration")
        self.assertEqual([e["source_type"] for e in relation["evidence"]],
                         ["curated_configuration", "published_manual"])

    def test_exact_companion_name_keeps_manual_authority(self):
        self.config["pairings"][0]["parts"] = ["Battery Pack"]
        self.write_config()
        relation = self.product(self.build())["relations"][0]
        self.assertEqual(relation["source_type"], "published_manual")
        self.assertEqual(len(relation["evidence"]), 1)

    def test_missing_manual_does_not_create_links_or_negative_product_facts(self):
        (self.web / "M/EU/en/md/manual.md").unlink()
        product = self.product(self.build())
        self.assertIsNone(product["source"]["url"])
        self.assertIsNone(product["source"]["sha256"])
        self.assertTrue(all(f["state"] == "unknown" for f in product["specifications"].values()))
        self.assertEqual(product["relations"], [])

    def test_missing_version_and_legacy_language_remain_explicit(self):
        self.targets[0].pop("version")
        self.targets[0]["language_scope"] = "legacy_unspecified"
        product = self.product(self.build())
        self.assertEqual(product["id"], "M/EU/en@unversioned")
        self.assertIsNone(product["version"])
        self.assertEqual(product["source"]["language_scope"], "legacy_unspecified")
        self.assertEqual({u["field"] for u in product["unknowns"]} & {"language", "version"}, {"language", "version"})

    def test_deterministic_hash_records_all_dependency_bytes(self):
        first, second = self.build(), self.build()
        self.assertEqual(first, second)
        payload = {key: value for key, value in first.items() if key != "content_sha256"}
        expected = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False,
                                             separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(first["content_sha256"], expected)
        paths = {entry["path"] for entry in first["snapshot"]["inputs"]}
        self.assertTrue({"data/model_capabilities.csv", "data/model_languages.csv",
                         "portal/product_matrix.json", "portal/settings.json",
                         "portal/catalog.json", "M/EU/en/md/manual.md"} <= paths)

    def test_evidence_changes_recompute_without_mutating_the_previous_snapshot(self):
        first = self.build()
        preserved = copy.deepcopy(first)
        path = self.web / "M/EU/en/md/manual.md"
        path.write_text(path.read_text().replace("1024 Wh", "1536 Wh"), encoding="utf-8")
        second = self.build()
        self.assertNotEqual(first["content_sha256"], second["content_sha256"])
        self.assertEqual(self.product(second)["specifications"]["capacity_wh"]["value"], 1536)
        self.assertEqual(first, preserved)
        self.registry.write_text(self.registry.read_text().replace("M_EU,P1,TRUE", "M_EU,P1,FALSE"))
        third = self.build()
        self.assertNotEqual(second["content_sha256"], third["content_sha256"])
        self.assertFalse(self.product(third)["capabilities"]["UPS功能"]["value"])
        self.config["notes"] = {"M": "Updated curated note"}
        self.write_config()
        self.assertNotEqual(third["content_sha256"], self.build()["content_sha256"])

    def test_corrupt_registry_degrades_to_unknown_without_erasing_manual_facts(self):
        self.registry.write_text(self.registry.read_text().replace("M_EU,P1,TRUE", "M_EU,P1,MAYBE"))
        snapshot = self.build()
        product = self.product(snapshot)
        self.assertEqual(product["capabilities"]["UPS功能"]["state"], "unknown")
        self.assertEqual(product["specifications"]["capacity_wh"]["value"], 1024)
        self.assertTrue(any("registry unavailable" in warning for warning in snapshot["warnings"]))

    def test_duplicate_variants_and_unsafe_paths_are_rejected(self):
        self.targets.append(dict(self.targets[0]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.build()
        self.targets.pop()
        self.targets[0]["route"] = "../../outside"
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            self.build()

    def test_external_symlinks_cannot_become_publication_evidence(self):
        path = self.web / "M/EU/en/md/manual.md"
        external = self.root / "outside.md"
        external.write_text("Not a published manual")
        path.unlink()
        path.symlink_to(external)
        with self.assertRaisesRegex(ValueError, "escapes"):
            self.build()

    def test_existing_matrix_view_and_frozen_inputs_are_unchanged(self):
        manifest_path = self.web.parent / "publish_manifest.json"
        manifest_path.write_text(json.dumps(self.manifest))
        args = (self.root, self.web, manifest_path, self.assets, self.settings, self.catalog)
        before = matrix_context(*args)
        files = {path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        self.build()
        self.assertEqual(before, matrix_context(*args))
        self.assertEqual(files, {path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()})


if __name__ == "__main__":
    unittest.main()
