#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for approval-gated source-table sync (Milestone F, PR F6)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.source_record_index import build_index  # noqa: E402
from tools.source_table_sync import (  # noqa: E402
    apply_change_requests,
    build_change_request_report,
    build_change_requests,
    collect_translation_suggestions,
    load_change_requests,
    plan_apply,
    source_table_apply_markdown,
    write_change_request_report,
    write_source_table_apply_report,
)


def _resolved_request(delta_hash: str = "h1") -> dict:
    return {
        "delta_hash": delta_hash,
        "table": "Spec_Master",
        "field": "Value_uk",
        "record_id": "recAAA",
        "resolution_status": "resolved",
        "old_text": "DC 12 V",
        "new_text": "DC 12 В",
        "old_value": "DC 12 V",
        "new_value": "DC 12 В",
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


class _RaisingTransport:
    """upsert raises for one table (e.g. no writable binding), writes others."""

    def __init__(self, *, fail_table: str) -> None:
        self.fail_table = fail_table
        self.store: dict = {}

    def upsert(self, *, table, record_id, field, value) -> None:
        if table == self.fail_table:
            raise RuntimeError(f"no writable binding for table {table!r}")
        self.store[(table, record_id, field)] = value

    def get(self, *, table, record_id, field):
        return self.store.get((table, record_id, field))


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


class CopyWriteTargetTests(unittest.TestCase):
    def _copy_diff(self, *, lang, source_lang, copy_key="k1"):
        return {
            "deltas": [
                {
                    "route_class": "source_table_suggestion",
                    "delta_hash": "c1",
                    "source_ref": {
                        "table": "Localized_Copy",
                        "field": f"text_{lang}",
                        "copy_key": copy_key,
                        "lang": lang,
                        "source_lang": source_lang,
                        "matched_value": "Old",
                    },
                    "old_text": "Old",
                    "new_text": "New",
                    "old_normalized": "Old",
                    "new_normalized": "New",
                }
            ]
        }

    def _sidecar(self, copy_key="k1", record_id="recMCS"):
        # Manual_Copy_Source index so the copy_key resolves to its authoring row.
        return build_index({"Manual_Copy_Source": [({"copy_key": copy_key}, record_id)]})

    def test_source_language_copy_writes_authoring_source_text(self) -> None:
        reqs = build_change_requests(self._copy_diff(lang="en", source_lang="en"), sidecar_index=self._sidecar())
        self.assertEqual(reqs[0]["table"], "Manual_Copy_Source")
        self.assertEqual(reqs[0]["field"], "source_text")
        self.assertEqual(reqs[0]["record_id"], "recMCS")
        self.assertEqual(reqs[0]["resolution_status"], "resolved")
        plan = plan_apply(reqs, approved_hashes={"c1"})
        self.assertEqual(plan[0]["action"], "apply")

    def test_translation_copy_abstains_at_write_boundary(self) -> None:
        reqs = build_change_requests(self._copy_diff(lang="it", source_lang="en"), sidecar_index=self._sidecar())
        self.assertIsNone(reqs[0]["record_id"])
        self.assertEqual(reqs[0]["resolution_status"], "translation_abstain")
        plan = plan_apply(reqs, approved_hashes={"c1"})
        self.assertEqual(plan[0]["action"], "skip")

    def test_unknown_source_lang_abstains(self) -> None:
        # A snapshot without Source_lang -> empty source_lang -> safe abstain.
        reqs = build_change_requests(self._copy_diff(lang="en", source_lang=""), sidecar_index=self._sidecar())
        self.assertEqual(reqs[0]["resolution_status"], "translation_abstain")

    def test_source_lang_without_sidecar_is_not_a_translation_suggestion(self) -> None:
        # Source-language edit whose record_id did not resolve stays a normal
        # unresolved request, NOT mislabeled as a translation suggestion.
        reqs = build_change_requests(self._copy_diff(lang="en", source_lang="en"))  # no sidecar
        self.assertNotEqual(reqs[0]["resolution_status"], "translation_abstain")
        self.assertEqual(collect_translation_suggestions(reqs), [])


class TranslationSuggestionTests(unittest.TestCase):
    def _translation_diff(self):
        return {
            "deltas": [
                {
                    "route_class": "source_table_suggestion",
                    "delta_hash": "t1",
                    "source_ref": {
                        "table": "Localized_Copy",
                        "field": "text_it",
                        "copy_key": "k1",
                        "lang": "it",
                        "source_lang": "en",
                    },
                    "old_text": "Vecchio",
                    "new_text": "Nuovo",
                }
            ]
        }

    def test_apply_report_surfaces_translation_suggestions_without_writing(self) -> None:
        reqs = build_change_requests(self._translation_diff())
        report = apply_change_requests(reqs, approved_hashes={"t1"})
        self.assertEqual(report["summary"]["translation_suggestions"], 1)
        self.assertEqual(report["summary"]["written"], 0)
        suggestion = report["translation_suggestions"][0]
        self.assertEqual(suggestion["copy_key"], "k1")
        self.assertEqual(suggestion["lang"], "it")
        self.assertEqual(suggestion["new_text"], "Nuovo")
        self.assertEqual(suggestion["routing_hint"], "translation_memory")

    def test_change_request_report_surfaces_translation_suggestions(self) -> None:
        report = build_change_request_report(self._translation_diff())
        self.assertEqual(report["summary"]["translation_suggestions"], 1)
        self.assertEqual(report["translation_suggestions"][0]["copy_key"], "k1")

    def test_markdown_includes_translation_section(self) -> None:
        reqs = build_change_requests(self._translation_diff())
        report = {**apply_change_requests(reqs, approved_hashes={"t1"}), "run_id": "r"}
        md = source_table_apply_markdown(report)
        self.assertIn("Translation suggestions", md)
        self.assertIn("k1", md)


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

    def test_one_request_error_does_not_abort_the_batch(self) -> None:
        # A request whose table has no writable binding (transport raises) is
        # isolated as `error`; the other approved request still writes.
        good = _resolved_request("good")
        bad = {**_resolved_request("bad"), "table": "Localized_Copy"}
        transport = _RaisingTransport(fail_table="Localized_Copy")
        report = apply_change_requests(
            [good, bad], approved_hashes={"good", "bad"}, transport=transport, write=True
        )
        statuses = {entry["delta_hash"]: entry["status"] for entry in report["applied"]}
        self.assertEqual(statuses["good"], "written")
        self.assertEqual(statuses["bad"], "error")
        self.assertEqual(report["summary"]["written"], 1)
        self.assertEqual(report["summary"]["error"], 1)
        self.assertEqual(transport.store[("Spec_Master", "recAAA", "Value_uk")], "DC 12 В")


class ReportIoTests(unittest.TestCase):
    def test_load_change_requests_round_trips_run_review_report(self) -> None:
        diff_report = {
            "run_id": "rr",
            "deltas": [
                {
                    "route_class": "source_table_suggestion",
                    "delta_hash": "h1",
                    "source_ref": {"table": "Spec_Master", "field": "Value_uk"},
                    "old_text": "DC 12 V",
                    "new_text": "DC 12 В",
                }
            ],
        }
        report = build_change_request_report(diff_report)
        with tempfile.TemporaryDirectory() as tmp:
            path = write_change_request_report(report, Path(tmp))
            requests, run_id = load_change_requests(path)
        self.assertEqual(run_id, "rr")
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]["delta_hash"], "h1")

    def test_load_change_requests_rejects_malformed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text("[]", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                load_change_requests(path)

    def test_apply_markdown_and_report_io(self) -> None:
        report = apply_change_requests([_resolved_request()], approved_hashes={"h1"})
        report = {**report, "run_id": "rr", "approved_count": 1}
        md = source_table_apply_markdown(report)
        self.assertIn("source-table apply", md)
        self.assertIn("dry-run", md)
        with tempfile.TemporaryDirectory() as tmp:
            written = write_source_table_apply_report(report, Path(tmp))
            self.assertTrue(written["json"].exists())
            self.assertTrue(written["markdown"].exists())
            payload = json.loads(written["json"].read_text(encoding="utf-8"))
            self.assertEqual(payload["run_id"], "rr")


class CellWriteValueTests(unittest.TestCase):
    """F6 precise write-back: a table-ROW Class D delta must write the changed CELL value
    into the cell field, not the whole row markup (and abstain when it can't be aligned)."""

    def test_table_row_delta_carries_cell_value_not_row(self) -> None:
        diff = {
            "deltas": [
                {
                    "route_class": "source_table_suggestion",
                    "delta_hash": "t1",
                    "source_ref": {"table": "Spec_Master", "field": "Value_source", "matched_value": "12V⎓最大10A"},
                    "old_text": "| **12V⎓最大10A**  <br/>12V⎓最大10A | **LED 灯按键** |",
                    "new_text": "| **IN1 (DC 12V点烟口)**  <br/>12V⎓最大10A | **LED 灯按键** |",
                    "old_normalized": "| 12V⎓最大10A <br/>12V⎓最大10A | LED 灯按键 |",
                    "new_normalized": "| IN1 (DC 12V点烟口) <br/>12V⎓最大10A | LED 灯按键 |",
                }
            ]
        }
        req = build_change_requests(diff)[0]
        self.assertEqual(req["new_value"], "IN1 (DC 12V点烟口)")  # the changed cell value...
        self.assertNotIn("|", req["new_value"])  # ...not the whole row markup
        self.assertEqual(req["old_value"], "12V⎓最大10A")

    def test_unalignable_cell_change_abstains(self) -> None:
        diff = {
            "deltas": [
                {
                    "route_class": "source_table_suggestion",
                    "delta_hash": "t2",
                    "source_ref": {"table": "Spec_Master", "field": "Value_source", "matched_value": "12V⎓最大10A"},
                    "old_normalized": "| 12V⎓最大10A | LED |",          # 2 cells
                    "new_normalized": "| IN1 | LED | extra cell |",      # 3 cells -> can't align
                    "old_text": "x",
                    "new_text": "y",
                }
            ]
        }
        self.assertIsNone(build_change_requests(diff)[0]["new_value"])  # abstain, no guess

    def test_plan_apply_skips_when_value_not_resolved(self) -> None:
        plan = plan_apply([{**_resolved_request(), "new_value": None}], approved_hashes={"h1"})
        self.assertEqual(plan[0]["action"], "skip")
        self.assertIn("not resolved", plan[0]["reason"])

    def test_plan_apply_writes_the_cell_value(self) -> None:
        plan = plan_apply([{**_resolved_request(), "new_value": "IN1 (DC 12V点烟口)"}], approved_hashes={"h1"})
        self.assertEqual(plan[0]["action"], "apply")
        self.assertEqual(plan[0]["value"], "IN1 (DC 12V点烟口)")


if __name__ == "__main__":
    unittest.main()
