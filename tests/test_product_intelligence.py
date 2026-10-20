"""Research rules preserve source authority, missingness and immutable input snapshots."""
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.rtd.intelligence_events import content_hash, load_cases
from tools.rtd.product_intelligence import CASES, compare_research_snapshots, research_context


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
        capability["evidence"][0].update(path="data/model_capabilities.csv", locator=f"{model}_{region}/{key}")
    for specification in value["specifications"].values():
        specification["evidence"][0].update(path=f"{route}/manual.md", url=f"{route}/manual.html")
    return value


def knowledge(*products):
    return {"schema_version": "product-knowledge/v1", "content_sha256": content_hash(products),
            "products": list(products)}


def association(result, event="us-outage-resilience-research", index=0):
    return [row for row in result["associations"] if row["event_id"] == event][index]


class ResearchContractTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.cases = self.root / "cases.json"
        self.data = json.loads(CASES.read_text(encoding="utf-8"))

    def write_cases(self):
        self.cases.write_text(json.dumps(self.data), encoding="utf-8")
        return self.cases

    def write_policy(self, *, status="verified", summary="Policy snapshot fact", official=True):
        directory = self.root / "market-policy"
        directory.mkdir(exist_ok=True)
        record = {key: "recorded basis" for key in (
            "title", "country", "region", "timeline", "mechanism", "impact", "boundary", "reviewed")}
        record.update(id="nl-net-metering", status=status, change=summary, reviewed="2026-10-06",
                      tags=["solar"], sources=[{
                          "kind": "official" if official else "commentary", "title": "Policy",
                          "url": "https://example.org/policy", "note": "Source verification scope",
                      }])
        (directory / "records.json").write_text(json.dumps({
            "schema_version": 1, "reviewed": "2026-10-06", "records": [record],
        }), encoding="utf-8")
        return record

    def test_official_event_with_four_distinct_dimensions_is_candidate_not_reviewed(self):
        result = research_context(knowledge(product()), self.root)
        row = association(result)
        self.assertEqual(row["status"], "candidate")
        self.assertEqual(row["source_type"], "rule_inference")
        self.assertEqual(row["provenance"]["evidence_sha256"], content_hash(row["evidence"]))
        self.assertEqual(row["provenance"]["product_sha256"], content_hash(product()))
        self.assertEqual(row["provenance"]["rule_source"]["path"], "tools/rtd_portal_assets/product_intelligence_cases.json")
        self.assertEqual({reason["dimension"] for reason in row["reasons"]},
                         {"market", "category", "capability", "evidence", "verification"})
        self.assertEqual({item["source_type"] for item in row["evidence"]},
                         {"curated_configuration", "capability_registry", "published_manual"})
        event = result["events"][1]
        self.assertEqual(event["review"], {
            "status": "pending", "decision": None, "reviewed_by": None, "reviewed_on": None,
        })
        self.assertEqual(event["revision"], 2)
        self.assertEqual(len(event["history"]), 2)
        self.assertNotEqual(event["history"][0]["content_sha256"], event["history"][1]["content_sha256"])

    def test_policy_facts_are_joined_by_id_and_source_file_is_not_changed(self):
        record = self.write_policy()
        source = self.root / "market-policy" / "records.json"
        before = source.read_bytes()
        result = research_context(knowledge(product(region="EU")), self.root)
        event = result["events"][0]
        self.assertEqual((event["summary"], event["policy_record_sha256"]),
                         (record["change"], content_hash(record)))
        self.assertEqual(association(result, event["id"])["status"], "candidate")
        self.assertEqual(source.read_bytes(), before)

    def test_absent_policy_cannot_fall_back_to_demo_verified_facts(self):
        result = research_context(knowledge(product(region="EU")), self.root)
        event = result["events"][0]
        self.assertEqual(event["status"], "missing")
        self.assertEqual(event["sources"], [])
        self.assertEqual(association(result, event["id"])["status"], "unknown")

    def test_region_mismatch_and_category_mismatch_are_explicit_exclusions(self):
        for candidate in (product(region="EU"), product(category="solar")):
            with self.subTest(product=candidate["id"]):
                row = association(research_context(knowledge(candidate), self.root))
                self.assertEqual(row["status"], "excluded")
                self.assertEqual(row["hypotheses"], [])
                self.assertIn("no_match", {reason["state"] for reason in row["reasons"]})

    def test_registry_false_is_not_the_same_as_missing_registry(self):
        for value, state, expected in ((False, "known", "excluded"), (None, "unknown", "unknown")):
            with self.subTest(value=value):
                candidate = product()
                candidate["capabilities"]["UPS功能"].update(value=value, state=state)
                self.assertEqual(association(research_context(knowledge(candidate), self.root))["status"], expected)

    def test_known_capability_without_bound_registry_evidence_is_unknown(self):
        for change in (
            {"evidence": []},
            {"evidence": [{"source_type": "capability_registry", "sha256": "a" * 64}]},
            {"source_type": "published_manual"},
        ):
            with self.subTest(change=change):
                candidate = product()
                candidate["capabilities"]["UPS功能"].update(change)
                self.assertEqual(association(research_context(knowledge(candidate), self.root))["status"], "unknown")
        for field, value in (("sha256", ""), ("locator", "JE-A_EU/UPS功能"),
                             ("path", "other.csv"), ("source_type", "published_manual")):
            with self.subTest(field=field):
                candidate = product()
                candidate["capabilities"]["UPS功能"]["evidence"][0][field] = value
                self.assertEqual(association(research_context(knowledge(candidate), self.root))["status"], "unknown")

    def test_foreign_manual_evidence_cannot_be_injected_into_current_variant(self):
        for field, value in (
            ("path", "JE-A/EU/en/md/manual.md"), ("url", "JE-A/EU/en/md/manual.html"),
            ("sha256", "b" * 64), ("source_type", "capability_registry"),
        ):
            with self.subTest(field=field):
                candidate = product()
                candidate["specifications"]["ac_output_w"]["evidence"][0][field] = value
                self.assertEqual(association(research_context(knowledge(candidate), self.root))["status"], "unknown")
        candidate = product()
        candidate["specifications"]["ac_output_w"] = product(region="EU")["specifications"]["ac_output_w"]
        self.assertEqual(association(research_context(knowledge(candidate), self.root))["status"], "unknown")
        self.assertEqual(association(research_context(knowledge(product()), self.root))["status"], "candidate")

    def test_positive_number_without_direct_traceable_manual_evidence_is_unknown(self):
        for change in (
            {"value": None, "state": "unknown"}, {"value": 0}, {"value": True},
            {"evidence": []}, {"evidence": [fact(2000, "capability_registry")["evidence"][0]]},
            {"evidence": [{"source_type": "published_manual", "quote": "2000 W", "sha256": None}]},
        ):
            with self.subTest(change=change):
                candidate = product()
                candidate["specifications"]["ac_output_w"].update(change)
                row = association(research_context(knowledge(candidate), self.root))
                self.assertEqual(row["status"], "unknown")
                self.assertTrue(any("ac_output_w" in unknown for unknown in row["unknowns"]))

    def test_unverified_event_remains_unknown_even_with_an_official_link(self):
        self.data["cases"][1]["revisions"][-1]["status"] = "unverified"
        result = research_context(knowledge(product()), self.root, cases_path=self.write_cases())
        self.assertEqual(association(result)["status"], "unknown")
        self.assertEqual(result["events"][1]["review"]["status"], "pending")

    def test_unverified_policy_and_demand_do_not_become_verified_from_rules(self):
        for state in ("unverified", "demand"):
            with self.subTest(state=state):
                self.write_policy(status=state)
                result = research_context(knowledge(product(region="EU")), self.root)
                self.assertEqual(association(result, "nl-self-consumption-research")["status"], "unknown")

    def test_policy_change_changes_hash_without_rewriting_previous_results(self):
        self.write_policy(summary="Earlier supported source statement")
        inputs = knowledge(product(region="EU"))
        previous = research_context(inputs, self.root)
        preserved = deepcopy(previous)
        self.write_policy(summary="New source statement with changed scope")
        current = research_context(inputs, self.root)
        receipt = compare_research_snapshots(previous, current)
        self.assertEqual(previous, preserved)
        self.assertNotEqual(receipt["previous_snapshot_id"], receipt["current_snapshot_id"])
        self.assertFalse(receipt["knowledge_changed"])
        self.assertEqual(receipt["event_changes"][0]["id"], "nl-self-consumption-research")
        self.assertEqual(receipt["review_status"], "pending")

    def test_removed_product_evidence_recomputes_candidate_to_unknown_with_receipt(self):
        candidate = product()
        previous = research_context(knowledge(candidate), self.root)
        saved = deepcopy(previous)
        candidate["specifications"]["ac_output_w"]["evidence"] = []
        current = research_context(knowledge(candidate), self.root)
        receipt = compare_research_snapshots(previous, current)
        self.assertTrue(receipt["knowledge_changed"])
        change = next(row for row in receipt["association_changes"] if row["event_id"].startswith("us-"))
        self.assertEqual((change["previous_status"], change["current_status"]), ("candidate", "unknown"))
        self.assertEqual(previous, saved)
        self.assertEqual(current["events"][1]["history"], previous["events"][1]["history"])

    def test_rebuild_is_deterministic_and_does_not_mutate_inputs(self):
        inputs = knowledge(product())
        before = deepcopy(inputs)
        first = research_context(inputs, self.root)
        second = research_context(inputs, self.root)
        self.assertEqual(first, second)
        self.assertEqual(inputs, before)
        self.assertEqual(compare_research_snapshots(first, second)["association_changes"], [])

    def test_invalid_source_urls_verification_and_revision_order_fail_loudly(self):
        revisions = self.data["cases"][1]["revisions"]
        for url in ("javascript:alert(1)", "http://example.org", "https://user:secret@example.org"):
            with self.subTest(url=url):
                revisions[-1]["sources"][0]["url"] = url
                with self.assertRaisesRegex(ValueError, "HTTPS"):
                    load_cases(self.write_cases())
        revisions[-1]["sources"][0]["url"] = "https://example.org"
        revisions[-1]["sources"][0]["kind"] = "commentary"
        with self.assertRaisesRegex(ValueError, "official"):
            load_cases(self.write_cases())
        revisions[-1]["sources"][0]["kind"] = "official"
        revisions[-1]["revision"] = 1
        with self.assertRaisesRegex(ValueError, "consecutive"):
            load_cases(self.write_cases())

    def test_human_decisions_are_explicit_and_not_overwritten_by_evaluation(self):
        review = {
            "status": "reviewed", "decision": "Research scope reviewed; no product applicability decision.",
            "reviewed_by": "Fixture reviewer", "reviewed_on": "2026-10-20",
        }
        self.data["cases"][1]["revisions"][-1]["review"] = review
        result = research_context(knowledge(product()), self.root, cases_path=self.write_cases())
        self.assertEqual(result["events"][1]["review"], review)
        historical = result["events"][1]["history"][-1]
        for key in ("decision", "reviewed_by", "reviewed_on"):
            self.assertEqual(historical[key], review[key])
        self.assertEqual(association(result)["status"], "candidate")
        self.assertEqual(result["events"][1]["history"][0]["review_status"], "pending")
        self.assertIsNone(result["events"][1]["history"][0]["decision"])

    def test_reviewed_revisions_require_identity_and_iso_date(self):
        for changes in (
            {"reviewed_by": None}, {"reviewed_by": " "}, {"reviewed_on": None},
            {"reviewed_on": "2026/10/20"}, {"reviewed_on": "20261020"}, {"reviewed_on": "2026-02-30"},
        ):
            with self.subTest(changes=changes):
                self.data["cases"][1]["revisions"][-1]["review"] = {
                    "status": "reviewed", "decision": "Fixture scope decision.",
                    "reviewed_by": "Fixture reviewer", "reviewed_on": "2026-10-20", **changes,
                }
                with self.assertRaises(ValueError):
                    load_cases(self.write_cases())

    def test_pending_reviews_reject_decision_identity_or_date(self):
        for field in ("decision", "reviewed_by", "reviewed_on"):
            with self.subTest(field=field):
                self.data["cases"][1]["revisions"][-1]["review"] = {"status": "pending", field: "2026-10-20"}
                with self.assertRaisesRegex(ValueError, "pending"):
                    load_cases(self.write_cases())

    def test_later_pending_revision_preserves_prior_human_judgment_in_history(self):
        review = {
            "status": "reviewed", "decision": "Fixture: needs target load evidence.",
            "reviewed_by": "Fixture reviewer", "reviewed_on": "2026-10-20",
        }
        self.data["cases"][1]["revisions"][0]["review"] = review
        result = research_context(knowledge(product()), self.root, cases_path=self.write_cases())
        event = result["events"][1]
        self.assertEqual(event["review"], {
            "status": "pending", "decision": None, "reviewed_by": None, "reviewed_on": None,
        })
        historical = next(row for row in result["history"] if row["event_id"] == event["id"])
        self.assertEqual(historical["review_status"], "reviewed")
        for key in ("decision", "reviewed_by", "reviewed_on"):
            self.assertEqual(historical[key], review[key])


if __name__ == "__main__":
    unittest.main()
