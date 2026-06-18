#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for approval-gated source-table sync (Milestone F, PR F6)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.source_table_sync import (  # noqa: E402
    apply_change_requests,
    build_change_requests,
    plan_apply,
)


def _resolved_request(delta_hash: str = "h1") -> dict:
    return {
        "delta_hash": delta_hash,
        "table": "Spec_Master",
        "field": "Value_uk",
        "record_id": "recAAA",
        "resolution_status": "resolved",
        "new_text": "DC 12 В",
    }


class _FakeTransport:
    def __init__(self) -> None:
        self.store: dict = {}

    def upsert(self, *, table, record_id, field, value) -> None:
        self.store[(table, record_id, field)] = value

    def get(self, *, table, record_id, field):
        return self.store.get((table, record_id, field))


class _NoOpTransport:
    def upsert(self, **_kwargs) -> None:
        pass

    def get(self, **_kwargs):
        return "STALE"


class BuildChangeRequestsTests(unittest.TestCase):
    def test_emits_only_class_d_deltas(self) -> None:
        diff_report = {
            "deltas": [
                {
                    "route_class": "source_table_suggestion",
                    "delta_hash": "h1",
                    "source_ref": {"table": "Spec_Master", "field": "Value_uk", "row_key": "dc12_port"},
                    "old_text": "DC 12 V",
                    "new_text": "DC 12 В",
                },
                {"route_class": "repo_review_text", "delta_hash": "h2", "old_text": "a", "new_text": "b"},
            ]
        }
        requests = build_change_requests(diff_report)
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]["table"], "Spec_Master")
        self.assertIsNone(requests[0]["record_id"])  # no sidecar -> snapshot_only
        self.assertFalse(requests[0]["external_write"])


class PlanApplyTests(unittest.TestCase):
    def test_approved_and_resolved_is_applied(self) -> None:
        plan = plan_apply([_resolved_request()], approved_hashes={"h1"})
        self.assertEqual(plan[0]["action"], "apply")

    def test_not_approved_is_skipped(self) -> None:
        plan = plan_apply([_resolved_request()], approved_hashes=set())
        self.assertEqual(plan[0]["action"], "skip")
        self.assertIn("not approved", plan[0]["reason"])

    def test_unresolved_record_id_abstains(self) -> None:
        req = {**_resolved_request(), "record_id": None, "resolution_status": "unresolved"}
        plan = plan_apply([req], approved_hashes={"h1"})
        self.assertEqual(plan[0]["action"], "skip")
        self.assertIn("exact-or-abstain", plan[0]["reason"])

    def test_duplicate_delta_hash_is_idempotent(self) -> None:
        plan = plan_apply([_resolved_request(), _resolved_request()], approved_hashes={"h1"})
        self.assertEqual(plan[0]["action"], "apply")
        self.assertEqual(plan[1]["action"], "skip")
        self.assertIn("idempotent", plan[1]["reason"])


class ApplyTests(unittest.TestCase):
    def test_dry_run_plans_without_writing(self) -> None:
        report = apply_change_requests([_resolved_request()], approved_hashes={"h1"})
        self.assertFalse(report["external_write"])
        self.assertEqual(report["summary"]["written"], 0)
        self.assertEqual(report["applied"][0]["status"], "planned")

    def test_write_with_transport_writes_and_verifies(self) -> None:
        transport = _FakeTransport()
        report = apply_change_requests(
            [_resolved_request()], approved_hashes={"h1"}, transport=transport, write=True
        )
        self.assertTrue(report["external_write"])
        self.assertEqual(report["summary"]["written"], 1)
        self.assertTrue(report["applied"][0]["verified"])
        self.assertEqual(transport.store[("Spec_Master", "recAAA", "Value_uk")], "DC 12 В")

    def test_get_verify_failure_is_flagged(self) -> None:
        report = apply_change_requests(
            [_resolved_request()], approved_hashes={"h1"}, transport=_NoOpTransport(), write=True
        )
        self.assertEqual(report["applied"][0]["status"], "verify_failed")
        self.assertEqual(report["summary"]["written"], 0)

    def test_unapproved_is_never_written(self) -> None:
        transport = _FakeTransport()
        apply_change_requests([_resolved_request()], approved_hashes=set(), transport=transport, write=True)
        self.assertEqual(transport.store, {})


if __name__ == "__main__":
    unittest.main()
