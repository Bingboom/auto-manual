#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for approval-gated Translation_Memory write-back (Milestone F follow-up)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.translation_memory_sync import (  # noqa: E402
    apply_translation_suggestions,
    plan_translation_writes,
    tm_column_for_lang,
)


def _sug(delta_hash="t1", lang="it", old="Vecchio", new="Nuovo", copy_key="k1"):
    return {
        "delta_hash": delta_hash,
        "copy_key": copy_key,
        "lang": lang,
        "source_lang": "en",
        "old_text": old,
        "new_text": new,
        "routing_hint": "translation_memory",
    }


class _FakeTm:
    def __init__(self, records):
        self.records = records
        self.writes = []

    def list_records(self):
        return self.records

    def write(self, *, record_id, field, value):
        self.writes.append((record_id, field, value))
        for record in self.records:
            if record.get("record_id") == record_id:
                record.setdefault("fields", {})[field] = value

    def get(self, *, record_id, field):
        for record in self.records:
            if record.get("record_id") == record_id:
                return (record.get("fields") or {}).get(field)
        return None


def _tm(record_id, **fields):
    return {"record_id": record_id, "fields": fields}


class TmColumnTests(unittest.TestCase):
    def test_lang_maps_to_tm_column(self) -> None:
        self.assertEqual(tm_column_for_lang("it"), "it")
        self.assertEqual(tm_column_for_lang("ja"), "jp")
        self.assertEqual(tm_column_for_lang("pt-BR"), "pt-BR")
        self.assertEqual(tm_column_for_lang("UK"), "uk")


class PlanTests(unittest.TestCase):
    def test_approved_and_resolved_is_applied(self) -> None:
        records = [_tm("recIT", it="Vecchio", en="Old")]
        plan = plan_translation_writes([_sug()], approved_hashes={"t1"}, records=records)
        self.assertEqual(plan[0]["action"], "apply")
        self.assertEqual(plan[0]["record_id"], "recIT")
        self.assertEqual(plan[0]["field"], "it")
        self.assertEqual(plan[0]["value"], "Nuovo")

    def test_not_approved_is_skipped(self) -> None:
        records = [_tm("recIT", it="Vecchio")]
        plan = plan_translation_writes([_sug()], approved_hashes=set(), records=records)
        self.assertEqual(plan[0]["action"], "skip")
        self.assertIn("not approved", plan[0]["reason"])

    def test_unresolved_old_text_abstains(self) -> None:
        records = [_tm("recIT", it="Different")]
        plan = plan_translation_writes([_sug()], approved_hashes={"t1"}, records=records)
        self.assertEqual(plan[0]["action"], "skip")
        self.assertIn("unresolved", plan[0]["reason"])

    def test_ambiguous_old_text_abstains(self) -> None:
        records = [_tm("recA", it="Vecchio"), _tm("recB", it="Vecchio")]
        plan = plan_translation_writes([_sug()], approved_hashes={"t1"}, records=records)
        self.assertEqual(plan[0]["action"], "skip")
        self.assertIn("ambiguous", plan[0]["reason"])

    def test_unknown_language_is_skipped(self) -> None:
        records = [_tm("recIT", it="Vecchio")]
        plan = plan_translation_writes([_sug(lang="")], approved_hashes={"t1"}, records=records)
        self.assertEqual(plan[0]["action"], "skip")
        self.assertIn("language", plan[0]["reason"])

    def test_empty_new_translation_is_skipped(self) -> None:
        records = [_tm("recIT", it="Vecchio")]
        plan = plan_translation_writes([_sug(new="  ")], approved_hashes={"t1"}, records=records)
        self.assertEqual(plan[0]["action"], "skip")

    def test_duplicate_delta_hash_is_idempotent(self) -> None:
        records = [_tm("recIT", it="Vecchio")]
        plan = plan_translation_writes([_sug(), _sug()], approved_hashes={"t1"}, records=records)
        self.assertEqual(plan[0]["action"], "apply")
        self.assertEqual(plan[1]["action"], "skip")
        self.assertIn("idempotent", plan[1]["reason"])

    def test_dry_run_without_records_defers_resolution(self) -> None:
        plan = plan_translation_writes([_sug()], approved_hashes={"t1"}, records=None)
        self.assertEqual(plan[0]["action"], "apply")
        self.assertEqual(plan[0]["resolution_status"], "deferred")
        self.assertIsNone(plan[0]["record_id"])


class ApplyTests(unittest.TestCase):
    def test_dry_run_plans_without_writing(self) -> None:
        report = apply_translation_suggestions([_sug()], approved_hashes={"t1"})
        self.assertFalse(report["external_write"])
        self.assertEqual(report["summary"]["written"], 0)
        self.assertEqual(report["applied"][0]["status"], "planned")

    def test_write_updates_tm_and_verifies(self) -> None:
        transport = _FakeTm([_tm("recIT", it="Vecchio", en="Old")])
        report = apply_translation_suggestions([_sug()], approved_hashes={"t1"}, transport=transport, write=True)
        self.assertTrue(report["external_write"])
        self.assertEqual(report["summary"]["written"], 1)
        self.assertTrue(report["applied"][0]["verified"])
        self.assertEqual(transport.get(record_id="recIT", field="it"), "Nuovo")

    def test_idempotent_when_already_applied(self) -> None:
        transport = _FakeTm([_tm("recIT", it="Nuovo")])  # already the new value
        report = apply_translation_suggestions([_sug()], approved_hashes={"t1"}, transport=transport, write=True)
        self.assertEqual(report["applied"][0]["status"], "already")
        self.assertEqual(report["summary"]["written"], 0)
        self.assertEqual(transport.writes, [])  # no write performed

    def test_unapproved_is_never_written(self) -> None:
        transport = _FakeTm([_tm("recIT", it="Vecchio")])
        apply_translation_suggestions([_sug()], approved_hashes=set(), transport=transport, write=True)
        self.assertEqual(transport.writes, [])

    def test_one_write_error_does_not_abort_batch(self) -> None:
        class _Raising(_FakeTm):
            def write(self, *, record_id, field, value):
                if record_id == "recBAD":
                    raise RuntimeError("boom")
                super().write(record_id=record_id, field=field, value=value)

        transport = _Raising([_tm("recIT", it="Vecchio"), _tm("recBAD", fr="Vieux")])
        good = _sug(delta_hash="g", lang="it", old="Vecchio", new="Nuovo")
        bad = _sug(delta_hash="b", lang="fr", old="Vieux", new="Neuf")
        report = apply_translation_suggestions(
            [good, bad], approved_hashes={"g", "b"}, transport=transport, write=True
        )
        statuses = {entry["delta_hash"]: entry["status"] for entry in report["applied"]}
        self.assertEqual(statuses["g"], "written")
        self.assertEqual(statuses["b"], "error")
        self.assertEqual(report["summary"]["error"], 1)


if __name__ == "__main__":
    unittest.main()
