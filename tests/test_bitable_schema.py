#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for tools/bitable_schema.py (Bitable schema export/apply for tenant parity)."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import bitable_schema as bs  # noqa: E402


def _fields_response(fields):
    return {"ok": True, "data": {"fields": fields}}


class ExportTests(unittest.TestCase):
    def test_export_is_name_keyed_and_captures_select_options(self):
        def fake(args, lark_cli="lark-cli"):
            if "+table-list" in args:
                return {"ok": True, "data": {"tables": [{"id": "tblA", "name": "T1"}]}}
            if "+field-list" in args:
                return _fields_response([
                    {"name": "Name", "type": "text"},
                    {"name": "N", "type": "number"},
                    {"name": "St", "type": "select", "multiple": False,
                     "options": [{"name": "a"}, {"name": "b"}]},
                ])
            return {"ok": False}

        with mock.patch.object(bs, "_lark", side_effect=fake):
            m = bs.export("base", None, "lark-cli")
        self.assertEqual([t["name"] for t in m["tables"]], ["T1"])
        # no per-tenant IDs leak into the manifest
        self.assertNotIn("id", m["tables"][0])
        st = next(f for f in m["tables"][0]["fields"] if f["name"] == "St")
        self.assertEqual(st["type"], "select")
        self.assertEqual(st["options"], ["a", "b"])
        self.assertFalse(st["multiple"])

    def test_export_table_filter(self):
        def fake(args, lark_cli="lark-cli"):
            if "+table-list" in args:
                return {"ok": True, "data": {"tables": [{"id": "1", "name": "Keep"}, {"id": "2", "name": "Drop"}]}}
            return _fields_response([{"name": "Name", "type": "text"}])

        with mock.patch.object(bs, "_lark", side_effect=fake):
            m = bs.export("base", ["Keep"], "lark-cli")
        self.assertEqual([t["name"] for t in m["tables"]], ["Keep"])


class ApplyTests(unittest.TestCase):
    MANIFEST = {"tables": [{"name": "T1", "fields": [
        {"name": "Name", "type": "text"},
        {"name": "St", "type": "select", "options": ["a"]},
        {"name": "Linked", "type": "link"},      # complex -> manual
    ]}]}

    def test_apply_to_empty_target_plans_create_and_flags_complex(self):
        def fake(args, lark_cli="lark-cli"):
            if "+table-list" in args:
                return {"ok": True, "data": {"tables": []}}   # fresh tenant
            return {"ok": False}

        with mock.patch.object(bs, "_lark", side_effect=fake):
            plan = bs.apply(self.MANIFEST, "prodbase", write=False, lark_cli="lark-cli")
        self.assertEqual(plan["create_tables"], ["T1"])
        self.assertFalse(plan["external_write"])
        self.assertTrue(any(c["field"] == "Linked" for c in plan["manual_complex"]))
        # complex field is never auto-created
        self.assertFalse(any(f["field"] == "Linked" for f in plan["create_fields"]))

    def test_apply_to_uptodate_target_is_idempotent(self):
        def fake(args, lark_cli="lark-cli"):
            if "+table-list" in args:
                return {"ok": True, "data": {"tables": [{"id": "tblA", "name": "T1"}]}}
            if "+field-list" in args:
                return _fields_response([
                    {"name": "Name", "type": "text"},
                    {"name": "St", "type": "select", "multiple": False, "options": [{"name": "a"}]},
                ])
            return {"ok": False}

        with mock.patch.object(bs, "_lark", side_effect=fake):
            plan = bs.apply(self.MANIFEST, "prodbase", write=False, lark_cli="lark-cli")
        self.assertEqual(plan["create_tables"], [])
        self.assertEqual(plan["create_fields"], [])          # both simple fields already exist
        self.assertEqual(plan["drift"], [])                  # and identical -> no drift
        self.assertEqual(len(plan["skip_existing"]), 2)

    def test_apply_adds_only_missing_field(self):
        def fake(args, lark_cli="lark-cli"):
            if "+table-list" in args:
                return {"ok": True, "data": {"tables": [{"id": "tblA", "name": "T1"}]}}
            if "+field-list" in args:
                return _fields_response([{"name": "Name", "type": "text"}])   # missing "St"
            return {"ok": False}

        with mock.patch.object(bs, "_lark", side_effect=fake):
            plan = bs.apply(self.MANIFEST, "prodbase", write=False, lark_cli="lark-cli")
        self.assertEqual([f["field"] for f in plan["create_fields"]], ["St"])

    def test_apply_flags_drift_but_does_not_change(self):
        # existing "St" select has different options than the manifest -> DRIFT, not skip, not changed
        def fake(args, lark_cli="lark-cli"):
            if "+table-list" in args:
                return {"ok": True, "data": {"tables": [{"id": "tblA", "name": "T1"}]}}
            if "+field-list" in args:
                return _fields_response([
                    {"name": "Name", "type": "text"},
                    {"name": "St", "type": "select", "multiple": False, "options": [{"name": "x"}]},
                ])
            return {"ok": False}

        calls = []
        with mock.patch.object(bs, "_lark", side_effect=lambda a, lark_cli="lark-cli": calls.append(a) or fake(a, lark_cli)):
            plan = bs.apply(self.MANIFEST, "prodbase", write=True, lark_cli="lark-cli")
        self.assertEqual([d["field"] for d in plan["drift"]], ["St"])
        self.assertEqual(plan["create_fields"], [])
        # never issued a field-update/create for the drifted field
        self.assertFalse(any("+field-update" in c for c in calls))


class FieldWriteFormatTests(unittest.TestCase):
    """select options are stored in the manifest as a name list, but lark-cli's
    create payload needs objects [{"name": ...}]. Bare strings are silently rejected."""

    def test_field_for_write_converts_select_options_to_objects(self):
        out = bs._field_for_write({"name": "St", "type": "select", "multiple": False, "options": ["a", "b"]})
        self.assertEqual(out["options"], [{"name": "a"}, {"name": "b"}])

    def test_field_for_write_leaves_non_select_untouched(self):
        self.assertEqual(bs._field_for_write({"name": "N", "type": "number"}), {"name": "N", "type": "number"})

    def test_apply_create_field_sends_object_options(self):
        manifest = {"tables": [{"name": "T1", "fields": [{"name": "St", "type": "select", "options": ["x", "y"]}]}]}

        def fake(args, lark_cli="lark-cli"):
            if "+table-list" in args:
                return {"ok": True, "data": {"tables": [{"id": "tblA", "name": "T1"}]}}
            if "+field-list" in args:
                return _fields_response([{"name": "Name", "type": "text"}])  # "St" missing -> create it
            return {"ok": True, "data": {}}

        calls = []
        with mock.patch.object(bs, "_lark", side_effect=lambda a, lark_cli="lark-cli": calls.append(a) or fake(a, lark_cli)):
            bs.apply(manifest, "prodbase", write=True, lark_cli="lark-cli")
        fc = next(c for c in calls if "+field-create" in c)
        payload = json.loads(fc[fc.index("--json") + 1])
        self.assertEqual(payload["options"], [{"name": "x"}, {"name": "y"}])

    def test_apply_create_table_sends_object_options(self):
        manifest = {"tables": [{"name": "New", "fields": [{"name": "St", "type": "select", "options": ["p"]}]}]}

        def fake(args, lark_cli="lark-cli"):
            if "+table-list" in args:
                return {"ok": True, "data": {"tables": []}}  # fresh -> create table
            if "+table-create" in args:
                return {"ok": True, "data": {"table_id": "tblNew"}}
            return {"ok": True, "data": {}}

        calls = []
        with mock.patch.object(bs, "_lark", side_effect=lambda a, lark_cli="lark-cli": calls.append(a) or fake(a, lark_cli)):
            bs.apply(manifest, "prodbase", write=True, lark_cli="lark-cli")
        tc = next(c for c in calls if "+table-create" in c)
        fields = json.loads(tc[tc.index("--fields") + 1])
        st = next(f for f in fields if f["name"] == "St")
        self.assertEqual(st["options"], [{"name": "p"}])


class ParityTests(unittest.TestCase):
    """parity = export(source) diffed against target (dev vs prod). Read-only."""

    def _fake(self, prod_tables, prod_fields):
        src_fields = [{"name": "Name", "type": "text"},
                      {"name": "St", "type": "select", "multiple": False, "options": [{"name": "a"}]}]

        def fake(args, lark_cli="lark-cli"):
            bt = args[args.index("--base-token") + 1] if "--base-token" in args else ""
            if "+table-list" in args:
                if bt == "DEV":
                    return {"ok": True, "data": {"tables": [{"id": "d1", "name": "T1"}]}}
                return {"ok": True, "data": {"tables": prod_tables}}
            if "+field-list" in args:
                tid = args[args.index("--table-id") + 1] if "--table-id" in args else ""
                return _fields_response(src_fields if tid == "d1" else prod_fields)
            return {"ok": False}
        return fake

    def test_parity_pass_when_target_matches(self):
        fake = self._fake([{"id": "p1", "name": "T1"}],
                          [{"name": "Name", "type": "text"},
                           {"name": "St", "type": "select", "multiple": False, "options": [{"name": "a"}]}])
        with mock.patch.object(bs, "_lark", side_effect=fake):
            res = bs.parity("DEV", "PROD", None, "lark-cli")
        self.assertTrue(res["in_parity"])
        self.assertEqual(res["missing_tables"], [])
        self.assertEqual(res["drift"], [])

    def test_parity_flags_missing_table(self):
        with mock.patch.object(bs, "_lark", side_effect=self._fake([], [])):
            res = bs.parity("DEV", "PROD", None, "lark-cli")
        self.assertFalse(res["in_parity"])
        self.assertEqual(res["missing_tables"], ["T1"])

    def test_parity_flags_drift(self):
        fake = self._fake([{"id": "p1", "name": "T1"}],
                          [{"name": "Name", "type": "text"},
                           {"name": "St", "type": "select", "multiple": False, "options": [{"name": "DIFFERENT"}]}])
        with mock.patch.object(bs, "_lark", side_effect=fake):
            res = bs.parity("DEV", "PROD", None, "lark-cli")
        self.assertFalse(res["in_parity"])
        self.assertEqual([d["field"] for d in res["drift"]], ["St"])

    def test_parity_ignores_scratch_tables_by_prefix(self):
        # dev carries a scratch table prod correctly lacks -> must not count as a prod lag
        def fake(args, lark_cli="lark-cli"):
            bt = args[args.index("--base-token") + 1] if "--base-token" in args else ""
            if "+table-list" in args:
                if bt == "DEV":
                    return {"ok": True, "data": {"tables": [{"id": "d1", "name": "T1"}, {"id": "d9", "name": "99_scratch"}]}}
                return {"ok": True, "data": {"tables": [{"id": "p1", "name": "T1"}]}}
            if "+field-list" in args:
                return _fields_response([{"name": "Name", "type": "text"}])
            return {"ok": False}

        with mock.patch.object(bs, "_lark", side_effect=fake):
            res_no = bs.parity("DEV", "PROD", None, "lark-cli")
            res_ig = bs.parity("DEV", "PROD", None, "lark-cli", ignore_prefixes=["99_"])
        self.assertIn("99_scratch", res_no["missing_tables"])
        self.assertNotIn("99_scratch", res_ig["missing_tables"])
        self.assertTrue(res_ig["in_parity"])

    def test_main_fail_on_missing_does_not_alert_on_drift_only(self):
        # drift but no missing table/field: 'any' fails (exit 1), 'missing' passes (exit 0)
        fake = self._fake([{"id": "p1", "name": "T1"}],
                          [{"name": "Name", "type": "text"},
                           {"name": "St", "type": "select", "multiple": False, "options": [{"name": "DIFFERENT"}]}])
        with mock.patch.object(bs, "_lark", side_effect=fake):
            rc_any = bs.main(["parity", "--source-base", "DEV", "--target-base", "PROD", "--fail-on", "any"])
            rc_missing = bs.main(["parity", "--source-base", "DEV", "--target-base", "PROD", "--fail-on", "missing"])
        self.assertEqual(rc_any, 1)
        self.assertEqual(rc_missing, 0)


class SeedImportTests(unittest.TestCase):
    """seed-import = idempotent upsert of reference rows by a business key (Gap C)."""

    def _fake(self, existing_rows, rids):
        def fake(args, lark_cli="lark-cli"):
            if "+table-list" in args:
                return {"ok": True, "data": {"tables": [{"id": "tblR", "name": "Rules"}]}}
            if "+field-list" in args:
                return _fields_response([
                    {"name": "Row_key", "type": "text"},
                    {"name": "取值规则", "type": "text"},
                    {"name": "manual_facing", "type": "checkbox"},
                    {"name": "Slot_key", "type": "lookup"},  # complex -> never written
                ])
            if "+record-list" in args:
                return {"ok": True, "data": {"fields": ["Row_key", "取值规则", "manual_facing"], "data": existing_rows, "record_id_list": rids}}
            return {"ok": True, "data": {}}
        return fake

    def test_create_update_skip(self):
        existing = [["r1", "manual", True], ["r2", "auto", False]]
        seed = [
            {"Row_key": "r1", "取值规则": "manual", "manual_facing": "True"},     # identical -> skip
            {"Row_key": "r2", "取值规则": "CHANGED", "manual_facing": "False"},   # one field -> update
            {"Row_key": "r3", "取值规则": "new", "manual_facing": "True"},        # absent -> create
        ]
        with mock.patch.object(bs, "_lark", side_effect=self._fake(existing, ["rec1", "rec2"])):
            plan = bs.seed_import("PROD", "Rules", seed, "Row_key", write=False, lark_cli="lark-cli")
        self.assertEqual(plan["create"], ["r3"])
        self.assertEqual([u["key"] for u in plan["update"]], ["r2"])
        self.assertEqual(plan["update"][0]["fields"], ["取值规则"])
        self.assertEqual(plan["skip"], ["r1"])
        self.assertEqual(plan["extras"], [])

    def test_idempotent_rerun_is_all_skip(self):
        existing = [["r1", "manual", True]]
        seed = [{"Row_key": "r1", "取值规则": "manual", "manual_facing": "True"}]
        with mock.patch.object(bs, "_lark", side_effect=self._fake(existing, ["rec1"])):
            plan = bs.seed_import("PROD", "Rules", seed, "Row_key", write=False, lark_cli="lark-cli")
        self.assertEqual((plan["create"], plan["update"], plan["skip"]), ([], [], ["r1"]))

    def test_reports_extras_without_prune(self):
        existing = [["r1", "manual", True], ["rX", "stale", False]]
        seed = [{"Row_key": "r1", "取值规则": "manual", "manual_facing": "True"}]
        with mock.patch.object(bs, "_lark", side_effect=self._fake(existing, ["rec1", "recX"])):
            plan = bs.seed_import("PROD", "Rules", seed, "Row_key", write=False, lark_cli="lark-cli")
        self.assertEqual(plan["extras"], ["rX"])
        self.assertEqual(plan["pruned"], [])

    def test_composite_key_distinguishes_same_row_key(self):
        # two rows share Row_key but differ in 规格书字段 -> a composite key keeps them distinct
        def fake(args, lark_cli="lark-cli"):
            if "+table-list" in args:
                return {"ok": True, "data": {"tables": [{"id": "tblR", "name": "Rules"}]}}
            if "+field-list" in args:
                return _fields_response([{"name": "Row_key", "type": "text"}, {"name": "规格书字段", "type": "text"}, {"name": "取值规则", "type": "text"}])
            if "+record-list" in args:
                return {"ok": True, "data": {"fields": ["Row_key", "规格书字段", "取值规则"],
                                             "data": [["x", "A", "keep"], ["x", "B", "keep"]], "record_id_list": ["r1", "r2"]}}
            return {"ok": True, "data": {}}
        seed = [{"Row_key": "x", "规格书字段": "A", "取值规则": "keep"},
                {"Row_key": "x", "规格书字段": "B", "取值规则": "keep"},
                {"Row_key": "x", "规格书字段": "C", "取值规则": "new"}]
        with mock.patch.object(bs, "_lark", side_effect=fake):
            plan = bs.seed_import("PROD", "Rules", seed, ["Row_key", "规格书字段"], write=False, lark_cli="lark-cli")
        self.assertEqual(plan["dup_keys"], [])            # composite key -> no false duplicates
        self.assertEqual(plan["create"], ["x | C"])       # only the genuinely-new (x, C)
        self.assertEqual(sorted(plan["skip"]), ["x | A", "x | B"])

    def test_write_create_uses_record_upsert_without_record_id(self):
        seed = [{"Row_key": "r3", "取值规则": "new", "manual_facing": "True"}]
        calls = []
        with mock.patch.object(bs, "_lark", side_effect=lambda a, lark_cli="lark-cli": calls.append(a) or self._fake([], [])(a, lark_cli)):
            bs.seed_import("PROD", "Rules", seed, "Row_key", write=True, lark_cli="lark-cli")
        upserts = [c for c in calls if "+record-upsert" in c]
        self.assertEqual(len(upserts), 1)
        self.assertNotIn("--record-id", upserts[0])  # create, not update
        payload = json.loads(upserts[0][upserts[0].index("--json") + 1])
        self.assertEqual(payload["manual_facing"], True)  # checkbox coerced to bool
        self.assertNotIn("Slot_key", payload)             # lookup never written


class PromoteTests(unittest.TestCase):
    """promote = apply (structure) + seed_import (reference data) + env delta, one step (Gap A)."""

    def test_dry_run_composes_structure_and_seed(self):
        manifest = {"tables": [{"name": "T1", "fields": [{"name": "Name", "type": "text"}]}]}
        seeds = [{"table": "Rules", "key": ["k"], "rows": [{"k": "r1", "v": "x"}]}]

        def fake(args, lark_cli="lark-cli"):
            if "+table-list" in args:
                return {"ok": True, "data": {"tables": [{"id": "tblRules", "name": "Rules"}]}}  # T1 absent
            if "+field-list" in args:
                return _fields_response([{"name": "k", "type": "text"}, {"name": "v", "type": "text"}])
            if "+record-list" in args:
                return {"ok": True, "data": {"fields": ["k", "v"], "data": [], "record_id_list": []}}
            return {"ok": True, "data": {}}

        with mock.patch.object(bs, "_lark", side_effect=fake):
            res = bs.promote(manifest, seeds, "PROD", write=False, lark_cli="lark-cli")
        self.assertEqual(res["structure"]["create_tables"], ["T1"])      # structure gap surfaced
        self.assertEqual(res["seeds"][0]["table"], "Rules")
        self.assertEqual(res["seeds"][0]["plan"]["create"], ["r1"])      # reference row to create
        self.assertEqual(res["new_table_ids"], {})                       # dry-run: nothing created
        self.assertEqual(res["post_missing"], {"tables": [], "fields": []})

    def test_write_runs_post_check(self):
        manifest = {"tables": [{"name": "Rules", "fields": [{"name": "k", "type": "text"}]}]}  # already present
        seeds = []

        def fake(args, lark_cli="lark-cli"):
            if "+table-list" in args:
                return {"ok": True, "data": {"tables": [{"id": "tblRules", "name": "Rules"}]}}
            if "+field-list" in args:
                return _fields_response([{"name": "k", "type": "text"}])
            return {"ok": True, "data": {}}

        with mock.patch.object(bs, "_lark", side_effect=fake):
            res = bs.promote(manifest, seeds, "PROD", write=True, lark_cli="lark-cli")
        self.assertTrue(res["write"])
        self.assertEqual(res["post_missing"], {"tables": [], "fields": []})  # nothing missing -> clean


if __name__ == "__main__":
    unittest.main()
