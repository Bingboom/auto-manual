#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for tools/bitable_schema.py (Bitable schema export/apply for tenant parity)."""
from __future__ import annotations

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
                return _fields_response([{"name": "Name"}, {"name": "St"}])
            return {"ok": False}

        with mock.patch.object(bs, "_lark", side_effect=fake):
            plan = bs.apply(self.MANIFEST, "prodbase", write=False, lark_cli="lark-cli")
        self.assertEqual(plan["create_tables"], [])
        self.assertEqual(plan["create_fields"], [])          # both simple fields already exist
        self.assertEqual(len(plan["skip_existing"]), 2)

    def test_apply_adds_only_missing_field(self):
        def fake(args, lark_cli="lark-cli"):
            if "+table-list" in args:
                return {"ok": True, "data": {"tables": [{"id": "tblA", "name": "T1"}]}}
            if "+field-list" in args:
                return _fields_response([{"name": "Name"}])   # missing "St"
            return {"ok": False}

        with mock.patch.object(bs, "_lark", side_effect=fake):
            plan = bs.apply(self.MANIFEST, "prodbase", write=False, lark_cli="lark-cli")
        self.assertEqual([f["field"] for f in plan["create_fields"]], ["St"])


if __name__ == "__main__":
    unittest.main()
