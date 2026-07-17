# -*- coding: utf-8 -*-
"""Fixture tests for tools/bitable_content_backup.py (no live network).

All lark-cli traffic goes through the single ``tools.bitable_schema._lark``
seam, so one fake covers export, restore, and verify.
"""
from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.test_helpers import temp_test_root

from tools import bitable_content_backup as bcb


def _fake_lark_factory(state: dict):
    """A canned lark-cli: one base with table T1 (text/number/checkbox/datetime/
    formula columns, 3 rows) and empty table T2. Records every write call."""

    def fake(args, lark_cli="lark-cli"):
        state.setdefault("calls", []).append(args)
        sub = args[1]
        if sub == "+table-list":
            return {"data": {"items": [
                {"name": "规格参数明细", "table_id": "tblSPEC"},
                {"name": "空表", "table_id": "tblEMPTY"},
            ]}}
        if sub == "+field-list":
            tid = args[args.index("--table-id") + 1]
            if tid == "tblSPEC":
                return {"data": {"items": [
                    {"field_id": "f1", "name": "参数名", "type": "text"},
                    {"field_id": "f2", "name": "数值", "type": "number"},
                    {"field_id": "f3", "name": "启用", "type": "checkbox"},
                    {"field_id": "f4", "name": "更新时刻", "type": "datetime"},
                    {"field_id": "f5", "name": "汇总", "type": "formula"},
                ]}}
            return {"data": {"items": [
                {"field_id": "g1", "name": "参数名", "type": "text"},
                {"field_id": "g2", "name": "数值", "type": "number"},
                {"field_id": "g3", "name": "启用", "type": "checkbox"},
                {"field_id": "g4", "name": "更新时刻", "type": "datetime"},
                {"field_id": "g5", "name": "汇总", "type": "formula"},
            ]}}
        if sub == "+record-list":
            tid = args[args.index("--table-id") + 1]
            if tid == "tblSPEC":
                return {"data": {
                    "fields": ["参数名", "数值", "启用", "更新时刻", "汇总"],
                    "field_id_list": ["f1", "f2", "f3", "f4", "f5"],
                    "data": [
                        ["额定功率", 1000, True, 1752710400000, [{"text": "1000W"}]],
                        ["电池容量", 1002.5, False, 1752710400000, [{"text": "1002.5Wh"}]],
                        ["", None, None, None, None],
                    ],
                    "record_id_list": ["rec1", "rec2", "rec3"],
                    "has_more": False,
                }}
            created = state.get("created_rows", [])
            return {"data": {
                "fields": ["参数名", "数值", "启用", "更新时刻", "汇总"],
                "field_id_list": ["g1", "g2", "g3", "g4", "g5"],
                "data": [[r[0], r[1], r[2], r[3], None] for r in created],
                "record_id_list": [f"new{i}" for i in range(len(created))],
                "has_more": False,
            }}
        if sub == "+record-batch-create":
            payload = json.loads(args[args.index("--json") + 1])
            state.setdefault("batches", []).append(payload)
            state.setdefault("created_rows", []).extend(payload["rows"])
            return {"code": 0, "data": {"records": [{} for _ in payload["rows"]]}}
        raise AssertionError(f"unexpected lark call: {args[:3]}")

    return fake


MANIFEST = {"schema_version": 1, "tables": [{"name": "规格参数明细", "fields": []},
                                            {"name": "不存在的表", "fields": []}]}


class ExportTests(unittest.TestCase):
    def test_export_writes_csv_and_manifest_and_flags_missing(self):
        state: dict = {}
        with temp_test_root() as root, patch.object(bcb.bs, "_lark", _fake_lark_factory(state)):
            report = bcb.export_content(MANIFEST, "basTOK", "business", Path(root), "lark-cli")
            self.assertEqual(report["missing_tables"], ["不存在的表"])
            (entry,) = report["tables"]
            self.assertEqual(entry["rows"], 3)
            csv_path = Path(root) / "business" / entry["csv"]
            with csv_path.open(encoding="utf-8", newline="") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(rows[0]["_record_id"], "rec1")
            self.assertEqual(rows[0]["参数名"], "额定功率")
            self.assertEqual(rows[0]["启用"], "True")
            self.assertEqual(rows[0]["更新时刻"], "1752710400000")
            self.assertEqual(rows[0]["汇总"], "1000W")  # formula VALUE kept for audit
            manifest = json.loads((Path(root) / "business" / bcb.BACKUP_MANIFEST).read_text("utf-8"))
            self.assertEqual(manifest["tables"][0]["sha256"], entry["sha256"])
            self.assertIn("formula", manifest["tables"][0]["field_types"].values())


class RestoreTests(unittest.TestCase):
    def _export(self, root, state):
        return bcb.export_content(
            {"schema_version": 1, "tables": [{"name": "规格参数明细", "fields": []}]},
            "basTOK", "business", Path(root), "lark-cli")

    def test_dry_run_plans_without_writing(self):
        state: dict = {}
        with temp_test_root() as root, patch.object(bcb.bs, "_lark", _fake_lark_factory(state)):
            self._export(root, state)
            report = bcb.restore_content(Path(root) / "business", "basSCRATCH",
                                         ["规格参数明细"], write=False, allow_nonempty=True,
                                         lark_cli="lark-cli")
            (plan,) = report["tables"]
            self.assertEqual(plan["planned_rows"], 2)  # empty row skipped
            self.assertEqual(plan["empty_rows_skipped"], 1)
            self.assertEqual(plan["skipped_columns"], ["汇总"])  # _record_id stripped at CSV load
            self.assertNotIn("batches", state)

    def test_write_refuses_nonempty_target_by_default(self):
        state: dict = {}
        with temp_test_root() as root, patch.object(bcb.bs, "_lark", _fake_lark_factory(state)):
            self._export(root, state)
            report = bcb.restore_content(Path(root) / "business", "basSCRATCH",
                                         ["规格参数明细"], write=True, allow_nonempty=False,
                                         lark_cli="lark-cli")
            (plan,) = report["tables"]
            self.assertTrue(any("restore only fills empty" in e for e in plan["errors"]))
            self.assertNotIn("batches", state)

    def test_write_into_empty_table_batches_and_coerces(self):
        state: dict = {}
        with temp_test_root() as root, patch.object(bcb.bs, "_lark", _fake_lark_factory(state)):
            self._export(root, state)
            report = bcb.restore_content(Path(root) / "business", "basSCRATCH",
                                         ["空表"], write=True, allow_nonempty=False,
                                         lark_cli="lark-cli")
            # 空表 is not in this backup — nothing must be written
            self.assertEqual(report["tables"], [])
            self.assertEqual(report["not_in_backup"], ["空表"])

            # restore the real table into the empty one by renaming the entry
            mf = json.loads((Path(root) / "business" / bcb.BACKUP_MANIFEST).read_text("utf-8"))
            mf["tables"][0]["name"] = "空表"
            (Path(root) / "business" / bcb.BACKUP_MANIFEST).write_text(
                json.dumps(mf, ensure_ascii=False), encoding="utf-8")
            report = bcb.restore_content(Path(root) / "business", "basSCRATCH",
                                         ["空表"], write=True, allow_nonempty=False,
                                         lark_cli="lark-cli")
            (plan,) = report["tables"]
            self.assertEqual(plan["errors"], [])
            self.assertEqual(plan["created_rows"], 2)
            self.assertEqual(plan["readback_rows"], 2)
            (batch,) = state["batches"]
            self.assertEqual(batch["fields"], ["参数名", "数值", "启用", "更新时刻"])
            self.assertEqual(batch["rows"][0][0], "额定功率")
            self.assertEqual(batch["rows"][0][1], 1000)          # number, not "1000"
            self.assertIs(batch["rows"][0][2], True)             # checkbox bool
            self.assertEqual(batch["rows"][0][3], 1752710400000)  # datetime ms int, not digit-string
            self.assertEqual(batch["rows"][1][1], 1002.5)

    def test_batch_chunking_respects_200_limit(self):
        state: dict = {}
        with temp_test_root() as root, patch.object(bcb.bs, "_lark", _fake_lark_factory(state)):
            dest = Path(root) / "business"
            dest.mkdir(parents=True)
            cols = ["参数名", "数值", "启用", "更新时刻", "汇总"]
            with (dest / "big.csv").open("w", encoding="utf-8", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["_record_id", *cols])
                for i in range(205):
                    w.writerow([f"rec{i}", f"参数{i}", i, "True", "", ""])
            (dest / bcb.BACKUP_MANIFEST).write_text(json.dumps({
                "generated_at": "t", "tables": [{"name": "空表", "csv": "big.csv", "rows": 205}],
            }, ensure_ascii=False), encoding="utf-8")
            bcb.restore_content(dest, "basSCRATCH", None, write=True,
                                allow_nonempty=False, lark_cli="lark-cli")
            self.assertEqual([len(b["rows"]) for b in state["batches"]], [200, 5])


class SelectOptionSyncTests(unittest.TestCase):
    """Live-drill regression (2026-07-17): batch-create rejects select values
    that are not existing options; restore must pre-sync them via field-update."""

    def _fake(self, state):
        def fake(args, lark_cli="lark-cli"):
            state.setdefault("calls", []).append(args)
            sub = args[1]
            if sub == "+table-list":
                return {"data": {"items": [{"name": "T", "table_id": "tblT"}]}}
            if sub == "+field-list":
                return {"data": {"items": [
                    {"field_id": "s1", "name": "状态", "type": "select",
                     "options": [{"name": "已通过", "hue": "Green"}]},
                ]}}
            if sub == "+record-list":
                return {"data": {"fields": ["状态"], "field_id_list": ["s1"],
                                 "data": [], "record_id_list": [], "has_more": False}}
            if sub == "+field-update":
                state.setdefault("field_updates", []).append(json.loads(args[args.index("--json") + 1]))
                return {"ok": True, "code": 0}
            if sub == "+record-batch-create":
                payload = json.loads(args[args.index("--json") + 1])
                state.setdefault("batches", []).append(payload)
                return {"code": 0}
            raise AssertionError(f"unexpected: {args[:3]}")
        return fake

    def _backup(self, root):
        dest = Path(root) / "b"
        dest.mkdir(parents=True)
        with (dest / "t.csv").open("w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["_record_id", "状态"])
            w.writerow(["rec1", "已通过"])
            w.writerow(["rec2", "新增选项"])
        (dest / bcb.BACKUP_MANIFEST).write_text(json.dumps({
            "generated_at": "t", "tables": [{"name": "T", "csv": "t.csv", "rows": 2}],
        }, ensure_ascii=False), encoding="utf-8")
        return dest

    def test_dry_run_reports_missing_options_without_updating(self):
        state: dict = {}
        with temp_test_root() as root, patch.object(bcb.bs, "_lark", self._fake(state)):
            report = bcb.restore_content(self._backup(root), "basS", None, write=False,
                                         allow_nonempty=False, lark_cli="lark-cli")
            (plan,) = report["tables"]
            self.assertEqual(plan["select_options_added"], {"状态": ["新增选项"]})
            self.assertNotIn("field_updates", state)

    def test_write_syncs_options_before_batching(self):
        state: dict = {}
        with temp_test_root() as root, patch.object(bcb.bs, "_lark", self._fake(state)):
            report = bcb.restore_content(self._backup(root), "basS", None, write=True,
                                         allow_nonempty=False, lark_cli="lark-cli")
            (plan,) = report["tables"]
            self.assertEqual(plan["errors"], [])
            (upd,) = state["field_updates"]
            self.assertEqual([o["name"] for o in upd["options"]], ["已通过", "新增选项"])
            # field-update happened before the batch that needs the option
            order = [a[1] for a in state["calls"]]
            self.assertLess(order.index("+field-update"), order.index("+record-batch-create"))


class VerifyTests(unittest.TestCase):
    def test_verify_reports_count_match_and_mismatch(self):
        state: dict = {}
        with temp_test_root() as root, patch.object(bcb.bs, "_lark", _fake_lark_factory(state)):
            bcb.export_content({"schema_version": 1, "tables": [{"name": "规格参数明细", "fields": []}]},
                               "basTOK", "business", Path(root), "lark-cli")
            report = bcb.verify_content(Path(root) / "business", "basTOK", None, "lark-cli")
            self.assertTrue(report["in_sync"])
            mf_path = Path(root) / "business" / bcb.BACKUP_MANIFEST
            mf = json.loads(mf_path.read_text("utf-8"))
            mf["tables"][0]["rows"] = 99
            mf_path.write_text(json.dumps(mf, ensure_ascii=False), encoding="utf-8")
            report = bcb.verify_content(Path(root) / "business", "basTOK", None, "lark-cli")
            self.assertFalse(report["in_sync"])


if __name__ == "__main__":
    unittest.main()
