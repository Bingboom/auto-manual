"""The optional product lens keeps source authority, missingness and immutable snapshots."""
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.product_knowledge import NUMERIC_FACTS, REGISTRY_PATH
from tools.rtd.intelligence_events import CONTENT_DIR, EVENTS_FILE, content_hash, load_events
from tools.rtd.product_intelligence import compare_lens_snapshots, product_lens_context

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "external_intel" / "events.json"
US, NL = "us-outage-resilience-research", "nl-self-consumption-research"


def fact(value, source_type, *, state="known"):
    return {
        "value": value, "unit": None, "state": state, "source_type": source_type, "reason": None,
        "evidence": [{"source_type": source_type, "path": "snapshot/manual.md",
                      "url": "JE-A/US/en/md/manual.html" if source_type == "published_manual" else None,
                      "sha256": "a" * 64, "locator": "table/Capacity", "quote": str(value)}],
    }


def product(*, model="JE-A", region="US", category="homebackup"):
    route = f"{model}/{region}/en/md"
    value = {
        "id": f"{model}/{region}/en/1.0", "model": model, "name": "Product A", "region": region,
        "language": "en", "version": "1.0", "category": fact(category, "curated_configuration"),
        "source": {"route": route, "manual": "manual.md", "url": f"{route}/manual.html",
                   "sha256": "a" * 64, "language_scope": "single"},
        "capabilities": {key: fact(True, "capability_registry") for key in ("自发自用模式", "UPS功能")},
        "specifications": {"capacity_wh": fact(1024, "published_manual"),
                           "ac_output_w": fact(2000, "published_manual")},
    }
    for key, capability in value["capabilities"].items():
        capability["evidence"][0].update(path=REGISTRY_PATH, locator=f"{model}_{region}/{key}")
    for name, specification in value["specifications"].items():
        specification["unit"] = "Wh" if name == "capacity_wh" else "W"
        specification["evidence"][0].update(path=f"{route}/manual.md", url=f"{route}/manual.html")
    return value


def knowledge(*products, capabilities=("自发自用模式", "UPS功能")):
    return {"schema_version": "product-knowledge/v1", "content_sha256": content_hash(products),
            "vocabulary": {"categories": ["appliance", "expandable", "homebackup", "dedicated", "solar"],
                           "capabilities": list(capabilities), "facts": list(NUMERIC_FACTS)},
            "products": list(products)}


def association(result, event=US, index=0):
    return [row for row in result["associations"] if row["event_id"] == event][index]


class ProductLensTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / CONTENT_DIR).mkdir()
        self.data = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def intel(self):
        (self.root / CONTENT_DIR / EVENTS_FILE).write_text(json.dumps(self.data, ensure_ascii=False), encoding="utf-8")
        return load_events(self.root)

    def lens(self, *products, **options):
        return product_lens_context(knowledge(*products, **options), self.intel())

    def write_policy(self, *, status="verified", summary="Policy snapshot fact"):
        directory = self.root / "market-policy"
        directory.mkdir(exist_ok=True)
        record = {key: "recorded basis" for key in (
            "title", "country", "region", "timeline", "mechanism", "impact", "boundary", "reviewed")}
        record.update(id="nl-net-metering", status=status, change=summary, reviewed="2026-10-06", tags=["solar"],
                      sources=[{"kind": "official", "title": "Policy", "url": "https://example.org/policy",
                                "note": "Source verification scope"}])
        (directory / "records.json").write_text(json.dumps({
            "schema_version": 1, "reviewed": "2026-10-06", "records": [record],
        }), encoding="utf-8")

    def test_official_event_with_every_dimension_is_candidate_not_reviewed(self):
        result = self.lens(product())
        row = association(result)
        self.assertEqual((row["status"], row["source_type"]), ("candidate", "rule_inference"))
        self.assertEqual(row["provenance"]["evidence_sha256"], content_hash(row["evidence"]))
        self.assertEqual(row["provenance"]["product_sha256"], content_hash(product()))
        self.assertEqual((row["provenance"]["rule_source"]["path"], row["provenance"]["rule_source"]["locator"]),
                         (f"{CONTENT_DIR}/{EVENTS_FILE}", f"events/{US}/product_lens"))
        self.assertEqual({reason["dimension"] for reason in row["reasons"]},
                         {"market", "category", "capability", "evidence", "verification"})
        self.assertEqual({item["source_type"] for item in row["evidence"]},
                         {"curated_configuration", "capability_registry", "published_manual"})
        self.assertNotIn("hypotheses", row)
        self.assertEqual(result["lenses"], [{"event_id": NL, "status": "evaluated", "problems": []},
                                            {"event_id": US, "status": "evaluated", "problems": []}])

    def test_events_without_a_lens_are_not_evaluated(self):
        del self.data["events"][1]["product_lens"]
        result = self.lens(product())
        self.assertEqual([entry["event_id"] for entry in result["lenses"]], [NL])
        self.assertFalse([row for row in result["associations"] if row["event_id"] == US])

    def test_unknown_rule_terms_mark_the_lens_invalid_instead_of_matching_nothing(self):
        rule = self.data["events"][1]["product_lens"]["rule"]
        for field, term in (("categories", "home-backup"), ("required_capabilities", "UPS 功能"),
                            ("required_facts", "ip_rating"), ("required_facts", "capacity_kwh")):
            with self.subTest(term=term):
                original = list(rule[field])
                rule[field] = [*original, term]
                result = self.lens(product())
                entry = next(entry for entry in result["lenses"] if entry["event_id"] == US)
                self.assertEqual(entry["status"], "invalid")
                self.assertEqual(len(entry["problems"]), 1)
                self.assertIn(f"「{term}」", entry["problems"][0])
                self.assertFalse([row for row in result["associations"] if row["event_id"] == US])
                rule[field] = original

    def test_a_vocabulary_the_snapshot_lacks_is_not_checked(self):
        result = self.lens(product(), capabilities=())
        self.assertEqual({entry["status"] for entry in result["lenses"]}, {"evaluated"})

    def test_policy_lens_follows_the_joined_policy_status(self):
        self.assertEqual(association(self.lens(product(region="EU")), NL)["status"], "unknown")
        self.write_policy()
        self.assertEqual(association(self.lens(product(region="EU")), NL)["status"], "candidate")
        for state in ("unverified", "demand"):
            with self.subTest(state=state):
                self.write_policy(status=state)
                self.assertEqual(association(self.lens(product(region="EU")), NL)["status"], "unknown")

    def test_region_mismatch_and_category_mismatch_are_explicit_exclusions(self):
        for candidate in (product(region="EU"), product(category="solar")):
            with self.subTest(product=candidate["id"]):
                row = association(self.lens(candidate))
                self.assertEqual(row["status"], "excluded")
                self.assertIn("no_match", {reason["state"] for reason in row["reasons"]})

    def test_registry_false_is_not_the_same_as_missing_registry(self):
        for value, state, expected in ((False, "known", "excluded"), (None, "unknown", "unknown")):
            with self.subTest(value=value):
                candidate = product()
                candidate["capabilities"]["UPS功能"].update(value=value, state=state)
                self.assertEqual(association(self.lens(candidate))["status"], expected)

    def test_known_capability_without_bound_registry_evidence_is_unknown(self):
        for change in (
            {"evidence": []},
            {"evidence": [{"source_type": "capability_registry", "sha256": "a" * 64}]},
            {"source_type": "published_manual"},
        ):
            with self.subTest(change=change):
                candidate = product()
                candidate["capabilities"]["UPS功能"].update(change)
                self.assertEqual(association(self.lens(candidate))["status"], "unknown")
        for field, value in (("sha256", ""), ("locator", "JE-A_EU/UPS功能"),
                             ("path", "other.csv"), ("source_type", "published_manual")):
            with self.subTest(field=field):
                candidate = product()
                candidate["capabilities"]["UPS功能"]["evidence"][0][field] = value
                self.assertEqual(association(self.lens(candidate))["status"], "unknown")

    def test_foreign_manual_evidence_cannot_be_injected_into_current_variant(self):
        for field, value in (
            ("path", "JE-A/EU/en/md/manual.md"), ("url", "JE-A/EU/en/md/manual.html"),
            ("sha256", "b" * 64), ("source_type", "capability_registry"),
        ):
            with self.subTest(field=field):
                candidate = product()
                candidate["specifications"]["ac_output_w"]["evidence"][0][field] = value
                self.assertEqual(association(self.lens(candidate))["status"], "unknown")
        candidate = product()
        candidate["specifications"]["ac_output_w"] = product(region="EU")["specifications"]["ac_output_w"]
        self.assertEqual(association(self.lens(candidate))["status"], "unknown")
        self.assertEqual(association(self.lens(product()))["status"], "candidate")

    def test_positive_number_without_direct_traceable_manual_evidence_is_unknown(self):
        for change in (
            {"value": None, "state": "unknown"}, {"value": 0}, {"value": True},
            {"evidence": []}, {"evidence": [fact(2000, "capability_registry")["evidence"][0]]},
            {"evidence": [{"source_type": "published_manual", "quote": "2000 W", "sha256": None}]},
        ):
            with self.subTest(change=change):
                candidate = product()
                candidate["specifications"]["ac_output_w"].update(change)
                row = association(self.lens(candidate))
                self.assertEqual(row["status"], "unknown")
                self.assertTrue(any("ac_output_w" in unknown for unknown in row["unknowns"]))

    def test_manual_fact_reasons_use_the_matrix_number_format(self):
        for value in (1024, 1024.0):
            with self.subTest(value=value):
                candidate = product()
                candidate["specifications"]["capacity_wh"]["value"] = value
                messages = [reason["message"] for reason in association(self.lens(candidate))["reasons"]]
                self.assertIn("发布手册直接事实：capacity_wh=1,024 Wh。", messages)

    def test_unverified_event_remains_unknown_even_with_an_official_link(self):
        self.data["events"][1]["revisions"][-1]["status"] = "unverified"
        self.assertEqual(association(self.lens(product()))["status"], "unknown")

    def test_removed_product_evidence_recomputes_candidate_to_unknown_with_receipt(self):
        candidate = product()
        previous = self.lens(candidate)
        saved = deepcopy(previous)
        candidate["specifications"]["ac_output_w"]["evidence"] = []
        current = self.lens(candidate)
        receipt = compare_lens_snapshots(previous, current)
        self.assertTrue(receipt["knowledge_changed"])
        self.assertFalse(receipt["events_changed"])
        change = next(row for row in receipt["association_changes"] if row["event_id"] == US)
        self.assertEqual((change["previous_status"], change["current_status"]), ("candidate", "unknown"))
        self.assertEqual(previous, saved)
        self.assertEqual(receipt["review_status"], "pending")

    def test_event_change_is_reported_without_knowledge_change(self):
        previous = self.lens(product())
        self.write_policy(summary="New source statement")
        receipt = compare_lens_snapshots(previous, self.lens(product()))
        self.assertEqual((receipt["knowledge_changed"], receipt["events_changed"]), (False, True))

    def test_rebuild_is_deterministic_and_does_not_mutate_inputs(self):
        inputs, intel = knowledge(product()), self.intel()
        before = deepcopy((inputs, intel))
        first = product_lens_context(inputs, intel)
        self.assertEqual(first, product_lens_context(inputs, intel))
        self.assertEqual((inputs, intel), before)
        self.assertEqual(compare_lens_snapshots(first, first)["association_changes"], [])

    def test_lens_requires_bound_snapshots(self):
        intel = self.intel()
        for broken_knowledge, broken_intel in (
            ({**knowledge(product()), "schema_version": "product-knowledge/v2"}, intel),
            ({**knowledge(product()), "content_sha256": ""}, intel),
            (knowledge(product()), {**intel, "schema_version": "product-intelligence/v1"}),
            (knowledge(product()), {**intel, "snapshot_id": ""}),
        ):
            with self.subTest(), self.assertRaises(ValueError):
                product_lens_context(broken_knowledge, broken_intel)


if __name__ == "__main__":
    unittest.main()
