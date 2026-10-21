"""External events are collected and complete on their own, without any product data."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.rtd.intelligence_events import (
    CONTENT_DIR, EVENTS_FILE, SCHEMA_VERSION, compare_event_snapshots, content_hash, load_events,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "external_intel" / "events.json"


def write_policy(root, *, status="verified", summary="Policy snapshot fact", official=True):
    directory = root / "market-policy"
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


class IntakeTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.path = self.root / CONTENT_DIR / EVENTS_FILE
        self.path.parent.mkdir()
        self.data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.nl, self.us = self.data["events"]

    def load(self):
        self.path.write_text(json.dumps(self.data, ensure_ascii=False), encoding="utf-8")
        return load_events(self.root)

    def rejects(self, pattern):
        with self.assertRaisesRegex(ValueError, pattern):
            self.load()

    def event(self, snapshot, key="us-outage-resilience-research"):
        return next(event for event in snapshot["events"] if event["id"] == key)

    def test_missing_intake_is_an_empty_collection_not_an_error(self):
        for root in (self.root, None):
            with self.subTest(root=root):
                snapshot = load_events(root)
                self.assertEqual((snapshot["schema_version"], snapshot["events"], snapshot["source"]),
                                 (SCHEMA_VERSION, [], None))
        self.assertEqual(load_events(self.root)["snapshot_id"], load_events(None)["snapshot_id"])

    def test_event_is_complete_without_a_product_lens(self):
        del self.us["product_lens"]
        event = self.event(self.load())
        self.assertIsNone(event["product_lens"])
        self.assertEqual(event["status"], "verified")
        self.assertTrue(event["summary"] and event["sources"] and event["boundary"])
        self.assertEqual(event["decision"], {
            "question": "是否按州、负载和停电时长分组，启动美国家庭备电需求验证？", "owner": None, "due_on": None,
        })
        self.assertEqual((event["revision"], event["recorded_on"]), (3, "2026-10-21"))
        self.assertFalse({"associations", "candidates", "knowledge_snapshot_id"} & set(event))

    def test_source_names_the_business_file_and_its_bytes(self):
        snapshot = self.load()
        expected = {"path": f"{CONTENT_DIR}/{EVENTS_FILE}", "sha256": hashlib.sha256(self.path.read_bytes()).hexdigest()}
        self.assertEqual(snapshot["source"], expected)
        self.assertEqual(self.event(snapshot)["source"], {**expected, "locator": "events/us-outage-resilience-research"})

    def test_policy_facts_are_joined_by_id_and_source_file_is_not_changed(self):
        record = write_policy(self.root)
        source = self.root / "market-policy" / "records.json"
        before = source.read_bytes()
        event = self.event(self.load(), "nl-self-consumption-research")
        self.assertEqual((event["summary"], event["policy_record_sha256"], event["checked_on"]),
                         (record["change"], content_hash(record), "2026-10-06"))
        self.assertEqual(source.read_bytes(), before)

    def test_absent_policy_cannot_fall_back_to_intake_facts(self):
        event = self.event(self.load(), "nl-self-consumption-research")
        self.assertEqual((event["status"], event["sources"]), ("missing", []))

    def test_policy_revisions_cannot_state_their_own_facts(self):
        for field, value in (("summary", "copied policy text"), ("status", "verified"), ("sources", [])):
            with self.subTest(field=field):
                self.data = json.loads(FIXTURE.read_text(encoding="utf-8"))
                self.data["events"][0]["revisions"][-1][field] = value
                self.rejects("unknown fields")

    def test_revisions_cannot_replace_identity_or_lens(self):
        for field, value in (("id", "other-event"), ("market", "JP"), ("product_lens", {}),
                             ("catalog_markets", ["JP"]), ("rule", {})):
            with self.subTest(field=field):
                self.data = json.loads(FIXTURE.read_text(encoding="utf-8"))
                self.data["events"][1]["revisions"][-1][field] = value
                self.rejects("unknown fields")

    def test_previous_intake_shape_is_rejected_loudly(self):
        self.data = {"schema_version": "product-intelligence-cases/v1", "cases": self.data["events"]}
        self.rejects("external-intel-events/v1")
        self.data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.us["rule"] = self.us.pop("product_lens")["rule"]
        self.data["events"][1] = self.us
        self.rejects("unknown fields: rule")

    def test_decision_owner_and_due_date_are_optional_but_well_formed(self):
        latest = self.us["revisions"][-1]
        latest.update(decision_owner="市场研究负责人", decide_by="2026-11-15")
        self.assertEqual(self.event(self.load())["decision"]["owner"], "市场研究负责人")
        for field, value in (("decision_owner", " "), ("decide_by", "2026/11/15"), ("decide_by", "2026-02-30")):
            with self.subTest(field=field, value=value):
                latest.update(decision_owner="市场研究负责人", decide_by="2026-11-15")
                latest[field] = value
                self.rejects(field)

    def test_hypotheses_and_open_questions_are_optional(self):
        for key in ("hypotheses", "unknowns"):
            self.us["revisions"][-1].pop(key)
        event = self.event(self.load())
        self.assertEqual((event["hypotheses"], event["unknowns"]), ([], []))
        self.us["revisions"][-1]["unknowns"] = [""]
        self.rejects("unknowns")

    def test_product_lens_is_optional_but_complete_when_present(self):
        for change in ({"catalog_markets": []}, {"market_mapping_note": " "}, {"extra": True}):
            with self.subTest(change=change):
                self.data = json.loads(FIXTURE.read_text(encoding="utf-8"))
                self.data["events"][1]["product_lens"].update(change)
                with self.assertRaises(ValueError):
                    self.load()
        for field in ("categories", "required_capabilities", "required_facts"):
            with self.subTest(field=field):
                self.data = json.loads(FIXTURE.read_text(encoding="utf-8"))
                self.data["events"][1]["product_lens"]["rule"][field] = []
                self.rejects(field)

    def test_only_policy_events_join_a_policy_record(self):
        self.us["source_record_id"] = "nl-net-metering"
        self.rejects("only market_policy")

    def test_invalid_source_urls_verification_and_revision_order_fail_loudly(self):
        revisions = self.us["revisions"]
        for url in ("javascript:alert(1)", "http://example.org", "https://user:secret@example.org"):
            with self.subTest(url=url):
                revisions[-1]["sources"][0]["url"] = url
                self.rejects("HTTPS")
        revisions[-1]["sources"][0]["url"] = "https://example.org"
        revisions[-1]["sources"][0]["kind"] = "commentary"
        self.rejects("official")
        revisions[-1]["sources"][0]["kind"] = "official"
        revisions[-1]["revision"] = 1
        self.rejects("consecutive")

    def test_unverified_signal_needs_no_source_to_be_collected(self):
        self.us["revisions"][-1].update(status="unverified", sources=[])
        event = self.event(self.load())
        self.assertEqual((event["status"], event["sources"]), ("unverified", []))

    def test_human_decisions_are_explicit_and_kept_per_revision(self):
        review = {
            "status": "reviewed", "decision": "Research scope reviewed; no product applicability decision.",
            "reviewed_by": "Fixture reviewer", "reviewed_on": "2026-10-22",
        }
        self.us["revisions"][-1]["review"] = review
        event = self.event(self.load())
        self.assertEqual(event["review"], review)
        for key in ("decision", "reviewed_by", "reviewed_on"):
            self.assertEqual(event["history"][-1][key], review[key])
        self.assertEqual(event["history"][0]["review_status"], "pending")
        self.assertIsNone(event["history"][0]["decision"])

    def test_reviewed_revisions_require_identity_and_iso_date(self):
        for changes in (
            {"reviewed_by": None}, {"reviewed_by": " "}, {"reviewed_on": None},
            {"reviewed_on": "2026/10/20"}, {"reviewed_on": "20261020"}, {"reviewed_on": "2026-02-30"},
        ):
            with self.subTest(changes=changes):
                self.us["revisions"][-1]["review"] = {
                    "status": "reviewed", "decision": "Fixture scope decision.",
                    "reviewed_by": "Fixture reviewer", "reviewed_on": "2026-10-20", **changes,
                }
                with self.assertRaises(ValueError):
                    self.load()

    def test_pending_reviews_reject_decision_identity_or_date(self):
        for field in ("decision", "reviewed_by", "reviewed_on"):
            with self.subTest(field=field):
                self.us["revisions"][-1]["review"] = {"status": "pending", field: "2026-10-20"}
                self.rejects("pending")

    def test_later_pending_revision_preserves_prior_human_judgment_in_history(self):
        review = {
            "status": "reviewed", "decision": "Fixture: needs target load evidence.",
            "reviewed_by": "Fixture reviewer", "reviewed_on": "2026-10-20",
        }
        self.us["revisions"][0]["review"] = review
        snapshot = self.load()
        event = self.event(snapshot)
        self.assertEqual(event["review"], {"status": "pending", "decision": None, "reviewed_by": None,
                                           "reviewed_on": None})
        historical = next(row for row in snapshot["history"] if row["event_id"] == event["id"])
        self.assertEqual(historical["review_status"], "reviewed")
        for key in ("decision", "reviewed_by", "reviewed_on"):
            self.assertEqual(historical[key], review[key])

    def test_policy_change_changes_hash_without_rewriting_previous_snapshot(self):
        write_policy(self.root, summary="Earlier supported source statement")
        previous = self.load()
        preserved = deepcopy(previous)
        write_policy(self.root, summary="New source statement with changed scope")
        current = self.load()
        receipt = compare_event_snapshots(previous, current)
        self.assertEqual(previous, preserved)
        self.assertNotEqual(receipt["previous_snapshot_id"], receipt["current_snapshot_id"])
        self.assertEqual([row["id"] for row in receipt["event_changes"]], ["nl-self-consumption-research"])
        self.assertEqual(receipt["review_status"], "pending")
        self.assertEqual(compare_event_snapshots(current, self.load())["event_changes"], [])

    def test_rebuild_is_deterministic_and_does_not_mutate_the_intake(self):
        first = self.load()
        before = self.path.read_bytes()
        self.assertEqual(first, load_events(self.root))
        self.assertEqual(self.path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
