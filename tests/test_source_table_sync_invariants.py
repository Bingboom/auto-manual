#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""F6 write-side safety invariants (L4 of the closed-loop test plan).

``tests/test_source_table_sync.py`` covers the F6 write path by *example*. This
module adds the *adversarial / property* layer over the three functions whose
failure silently corrupts a source table:

- :func:`_resolve_written_value` — extracts the precise NEW cell value for a
  table-row delta. The #460 bug class (a cell mapped to the wrong position) lives
  here, so it is fuzzed exhaustively over cell counts and changed positions.
- :func:`plan_apply` — the pure R9 gate stack. Tested as a full boolean matrix:
  a request must be applied **iff** every gate passes.
- :func:`apply_change_requests` — the live drift guard. Tested with a
  call-recording transport to prove the no-clobber, no-write-in-dry-run, and
  batch-isolation invariants (i.e. the cell is physically never touched on the
  ``already_applied`` / ``drift_abstained`` / dry-run paths).

These tests assert *invariants over many inputs*, not single hand-picked cases,
so a regression that only shows up at, say, the 4th cell of a 5-cell row is caught.
"""
from __future__ import annotations

import itertools
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.source_table_sync import (  # noqa: E402
    _resolve_written_value,
    apply_change_requests,
    plan_apply,
)


def _row(cells: list[str]) -> str:
    """A markdown table-row text from ordered cell values."""
    return "| " + " | ".join(cells) + " |"


def _resolved_request(
    *,
    delta_hash: str = "h1",
    table: str = "Spec_Master",
    field: str = "Value_uk",
    record_id: str | None = "recAAA",
    resolution_status: str = "resolved",
    old_value: str | None = "DC 12 V",
    new_value: str | None = "DC 12 В",
) -> dict:
    return {
        "delta_hash": delta_hash,
        "table": table,
        "field": field,
        "record_id": record_id,
        "resolution_status": resolution_status,
        "old_text": old_value,
        "new_text": new_value,
        "old_value": old_value,
        "new_value": new_value,
    }


class _SpyTransport:
    """Records every get/upsert so tests can assert a cell was NEVER written.

    ``current`` seeds the value each cell reads as. ``swallow_upsert`` makes upsert
    a no-op (the cell does not change) to exercise the verify-failure path.
    ``raise_get_for`` / ``raise_upsert_for`` raise for the given record_ids to
    exercise per-request error isolation.
    """

    def __init__(
        self,
        current: dict | None = None,
        *,
        swallow_upsert: bool = False,
        raise_get_for: set[str] | None = None,
        raise_upsert_for: set[str] | None = None,
    ) -> None:
        self.current = dict(current or {})
        self.swallow_upsert = swallow_upsert
        self.raise_get_for = raise_get_for or set()
        self.raise_upsert_for = raise_upsert_for or set()
        self.get_calls: list[tuple] = []
        self.upsert_calls: list[tuple] = []

    def get(self, *, table, record_id, field):
        self.get_calls.append((table, record_id, field))
        if record_id in self.raise_get_for:
            raise RuntimeError("get failed")
        return self.current.get((table, record_id, field))

    def upsert(self, *, table, record_id, field, value):
        self.upsert_calls.append((table, record_id, field, value))
        if record_id in self.raise_upsert_for:
            raise RuntimeError("upsert failed")
        if not self.swallow_upsert:
            self.current[(table, record_id, field)] = value


class WrittenValueAlignmentFuzzTests(unittest.TestCase):
    """Exhaustive coverage of the cell-alignment value extraction (#460 class)."""

    def test_single_changed_cell_resolves_at_every_position(self) -> None:
        # For any row width and any single changed cell, the extracted value must be
        # exactly the NEW value at that position — never a neighbour's value.
        for width in range(1, 7):
            for pos in range(width):
                with self.subTest(width=width, pos=pos):
                    old_cells = [f"old{i}" for i in range(width)]
                    new_cells = list(old_cells)
                    new_cells[pos] = f"NEW{pos}"
                    matched = old_cells[pos]
                    got = _resolve_written_value(_row(old_cells), _row(new_cells), matched)
                    self.assertEqual(got, f"NEW{pos}")

    def test_br_joined_subvalues_align_like_pipe_cells(self) -> None:
        old = "alpha<br/>beta<br/>gamma"
        new = "alpha<br/>BETA<br/>gamma"
        self.assertEqual(_resolve_written_value(old, new, "beta"), "BETA")

    def test_cjk_and_parenthesized_cell_value_is_extracted_verbatim(self) -> None:
        old = _row(["IN1", "DC 12V点烟口", "label"])
        new = _row(["IN1", "DC 12V车载口", "label"])
        self.assertEqual(_resolve_written_value(old, new, "DC 12V点烟口"), "DC 12V车载口")

    def test_whole_text_bare_value_returns_whole_new_text(self) -> None:
        self.assertEqual(_resolve_written_value("DC 12 V", "DC 24 V", "DC 12 V"), "DC 24 V")

    def test_abstains_on_cell_count_mismatch(self) -> None:
        old = _row(["a", "b", "c"])
        new = _row(["a", "b"])
        self.assertIsNone(_resolve_written_value(old, new, "c"))

    def test_abstains_when_matched_cell_did_not_change(self) -> None:
        # cell 1 changed, but the matched value points at the unchanged cell 0.
        old = _row(["keep", "old", "tail"])
        new = _row(["keep", "new", "tail"])
        self.assertIsNone(_resolve_written_value(old, new, "keep"))

    def test_abstains_when_matched_value_is_absent(self) -> None:
        old = _row(["a", "b"])
        new = _row(["a", "c"])
        self.assertIsNone(_resolve_written_value(old, new, "zzz"))

    def test_abstains_when_matched_value_changed_in_two_cells(self) -> None:
        # The matched value occupies two cells, both changed to different values:
        # there is no unique changed position -> abstain rather than guess.
        old = _row(["dup", "mid", "dup"])
        new = _row(["A", "mid", "B"])
        self.assertIsNone(_resolve_written_value(old, new, "dup"))

    def test_resolves_unique_changed_duplicate(self) -> None:
        # Same value in two cells but only ONE changed -> unambiguous.
        old = _row(["dup", "mid", "dup"])
        new = _row(["dup", "mid", "CHANGED"])
        self.assertEqual(_resolve_written_value(old, new, "dup"), "CHANGED")

    def test_abstains_on_empty_matched_value(self) -> None:
        self.assertIsNone(_resolve_written_value("a", "b", ""))


# The R9 gates that plan_apply enforces; a request applies iff ALL of these pass.
_GATES = ("approved", "resolved", "record_id", "table", "field", "new_value")


class PlanApplyGateMatrixTests(unittest.TestCase):
    """plan_apply must yield action=apply iff every gate passes (full 2^N matrix)."""

    def _request_for(self, flags: dict[str, bool]) -> dict:
        return _resolved_request(
            resolution_status="resolved" if flags["resolved"] else "unresolved",
            record_id="recAAA" if flags["record_id"] else None,
            table="Spec_Master" if flags["table"] else "",
            field="Value_uk" if flags["field"] else "",
            new_value="DC 12 В" if flags["new_value"] else "",
        )

    def test_full_gate_matrix(self) -> None:
        for combo in itertools.product((False, True), repeat=len(_GATES)):
            flags = dict(zip(_GATES, combo))
            with self.subTest(**flags):
                request = self._request_for(flags)
                approved = {"h1"} if flags["approved"] else set()
                plan = plan_apply([request], approved_hashes=approved)
                should_apply = all(flags.values())
                action = plan[0]["action"]
                self.assertEqual(
                    action,
                    "apply" if should_apply else "skip",
                    f"flags={flags} -> action={action}",
                )
                if should_apply:
                    self.assertEqual(plan[0]["value"], "DC 12 В")

    def test_duplicate_delta_hash_is_idempotent(self) -> None:
        reqs = [_resolved_request(delta_hash="dup"), _resolved_request(delta_hash="dup")]
        plan = plan_apply(reqs, approved_hashes={"dup"})
        self.assertEqual(plan[0]["action"], "apply")
        self.assertEqual(plan[1]["action"], "skip")
        self.assertIn("duplicate", plan[1]["reason"])

    def test_apply_set_is_order_independent(self) -> None:
        reqs = [
            _resolved_request(delta_hash="a"),
            _resolved_request(delta_hash="b"),
            _resolved_request(delta_hash="c"),
        ]
        approved = {"a", "b", "c"}
        baseline = {
            entry["delta_hash"]
            for entry in plan_apply(reqs, approved_hashes=approved)
            if entry["action"] == "apply"
        }
        for ordering in (list(reversed(reqs)), reqs[1:] + reqs[:1]):
            applied = {
                entry["delta_hash"]
                for entry in plan_apply(ordering, approved_hashes=approved)
                if entry["action"] == "apply"
            }
            self.assertEqual(applied, baseline)


class ApplyDriftGuardInvariantTests(unittest.TestCase):
    """The live write path must never clobber, never write in dry-run, and isolate errors."""

    _KEY = ("Spec_Master", "recAAA", "Value_uk")

    def _apply(self, transport, *, write=True, requests=None):
        requests = requests or [_resolved_request()]
        return apply_change_requests(
            requests,
            approved_hashes={r["delta_hash"] for r in requests},
            transport=transport,
            write=write,
        )

    def test_already_applied_does_not_write(self) -> None:
        spy = _SpyTransport({self._KEY: "DC 12 В"})  # already the target
        report = self._apply(spy)
        self.assertEqual(report["summary"]["already_applied"], 1)
        self.assertEqual(spy.upsert_calls, [])

    def test_drift_abstained_does_not_write(self) -> None:
        spy = _SpyTransport({self._KEY: "DC 99 V"})  # neither old nor target
        report = self._apply(spy)
        self.assertEqual(report["summary"]["drift_abstained"], 1)
        self.assertEqual(spy.upsert_calls, [])

    def test_empty_cell_where_old_expected_abstains(self) -> None:
        spy = _SpyTransport({})  # cell reads empty; expected old is "DC 12 V"
        report = self._apply(spy)
        self.assertEqual(report["summary"]["drift_abstained"], 1)
        self.assertEqual(spy.upsert_calls, [])

    def test_clean_old_value_is_written_and_verified(self) -> None:
        spy = _SpyTransport({self._KEY: "DC 12 V"})  # the expected old value
        report = self._apply(spy)
        self.assertEqual(report["summary"]["written"], 1)
        self.assertEqual(len(spy.upsert_calls), 1)
        self.assertEqual(spy.current[self._KEY], "DC 12 В")

    def test_missing_expected_old_skips_drift_guard(self) -> None:
        # No matched old_value -> no drift guard; a differing cell is still written.
        spy = _SpyTransport({self._KEY: "anything"})
        report = self._apply(spy, requests=[_resolved_request(old_value=None)])
        self.assertEqual(report["summary"]["written"], 1)
        self.assertEqual(len(spy.upsert_calls), 1)

    def test_verify_failure_when_write_does_not_persist(self) -> None:
        spy = _SpyTransport({self._KEY: "DC 12 V"}, swallow_upsert=True)
        report = self._apply(spy)
        self.assertEqual(report["summary"]["verify_failed"], 1)
        self.assertEqual(report["summary"]["written"], 0)

    def test_dry_run_never_touches_the_transport(self) -> None:
        spy = _SpyTransport({self._KEY: "DC 12 V"})
        report = self._apply(spy, write=False)
        self.assertEqual(spy.upsert_calls, [])
        self.assertEqual(spy.get_calls, [])
        self.assertFalse(report["external_write"])

    def test_no_transport_plans_without_writing(self) -> None:
        report = apply_change_requests(
            [_resolved_request()], approved_hashes={"h1"}, transport=None, write=True
        )
        self.assertFalse(report["external_write"])
        self.assertTrue(all(entry["status"] == "planned" for entry in report["applied"]))

    def test_one_failing_request_does_not_abort_the_batch(self) -> None:
        reqs = [
            _resolved_request(delta_hash="h1", record_id="recA"),
            _resolved_request(delta_hash="h2", record_id="recBAD"),
            _resolved_request(delta_hash="h3", record_id="recC"),
        ]
        spy = _SpyTransport(
            {
                ("Spec_Master", "recA", "Value_uk"): "DC 12 V",
                ("Spec_Master", "recC", "Value_uk"): "DC 12 V",
            },
            raise_get_for={"recBAD"},
        )
        report = self._apply(spy, requests=reqs)
        self.assertEqual(report["summary"]["written"], 2)
        self.assertEqual(report["summary"]["error"], 1)
        statuses = {entry["record_id"]: entry["status"] for entry in report["applied"]}
        self.assertEqual(statuses["recA"], "written")
        self.assertEqual(statuses["recBAD"], "error")
        self.assertEqual(statuses["recC"], "written")


if __name__ == "__main__":
    unittest.main()
