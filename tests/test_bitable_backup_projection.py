# -*- coding: utf-8 -*-
"""Wide-table export (more than 50 fields) and confidential-error handling for the content backup.

No live network: every lark-cli call goes through the ``tools.bitable_schema._lark`` seam.
"""
from __future__ import annotations

import contextlib
import csv
import io
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.test_helpers import temp_test_root

from tools import bitable_content_backup as bcb
from tools.bitable_backup import projection

WIDE = 120  # one primary column + 119 attribute columns: three 50-field slices
NAMES = ["产品键", *[f"属性{i:03d}" for i in range(1, WIDE)]]
RIDS = ["recA", "recB", "recC"]


def _cell(rid: str, name: str):
    return f"{rid}:{name}"


def _wide_lark(state: dict, *, drop_row_after_first_slice: bool = False, ignore_projection: bool = False,
               fail_record_list: bool = False):
    def fake(args, lark_cli="lark-cli"):
        state.setdefault("calls", []).append(args)
        sub = args[1]
        if sub == "+table-list":
            return {"data": {"items": [{"name": "矩阵", "table_id": "tblWIDE"}]}}
        if sub == "+field-list":
            # without --limit the fake mimics a short default page (first 100 fields)
            limit = int(args[args.index("--limit") + 1]) if "--limit" in args else 100
            items = [{"field_id": f"fld{i}", "name": n, "type": "text"} for i, n in enumerate(NAMES)]
            return {"data": {"items": items[:limit], "has_more": len(items) > limit}}
        if sub == "+record-list":
            if fail_record_list:
                raise RuntimeError("Lark CLI command failed: stdout=MODEL-X/US 项目号 P-SECRET-42")
            projected = [args[i + 1] for i, a in enumerate(args) if a == "--field-id"]
            state.setdefault("projections", []).append(projected)
            if ignore_projection:
                projected = NAMES[:50]
            rids = list(RIDS)
            if drop_row_after_first_slice and len(state["projections"]) > 1:
                rids = rids[:-1]
            return {"data": {
                "fields": projected,
                "field_id_list": [f"fld{NAMES.index(n)}" for n in projected],
                "data": [[_cell(r, n) for n in projected] for r in rids],
                "record_id_list": rids,
                "has_more": False,
            }}
        raise AssertionError(f"unexpected lark call: {args[:3]}")

    return fake


MANIFEST = {"schema_version": "bitable-schema/v1", "tables": [{"name": "矩阵", "fields": []}]}


class WideTableExportTests(unittest.TestCase):
    def test_projection_threshold(self):
        self.assertFalse(projection.needs_projection({f"f{i}": "text" for i in range(50)}))
        self.assertTrue(projection.needs_projection({f"f{i}": "text" for i in range(51)}))

    def test_wide_table_is_read_in_slices_and_merged_by_record(self):
        state: dict = {}
        with temp_test_root() as root, patch.object(bcb.bs, "_lark", _wide_lark(state)):
            report = bcb.export_content(MANIFEST, "basTOK", "product_matrix", Path(root), "lark-cli")
            (entry,) = report["tables"]
            self.assertEqual(entry["rows"], 3)
            # the full field list (120) replaces the short default page (100)
            self.assertEqual(entry["columns"], NAMES)
            self.assertEqual([len(p) for p in state["projections"]], [50, 50, 20])
            self.assertEqual([n for p in state["projections"] for n in p], NAMES)
            with (Path(root) / "product_matrix" / entry["csv"]).open(encoding="utf-8", newline="") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual([r["_record_id"] for r in rows], RIDS)
            self.assertEqual(rows[1][NAMES[0]], _cell("recB", NAMES[0]))
            self.assertEqual(rows[1][NAMES[-1]], _cell("recB", NAMES[-1]))
            self.assertTrue(all(r[n] for r in rows for n in NAMES))

    def test_rows_changing_between_slices_fails_without_cell_values(self):
        state: dict = {}
        with temp_test_root() as root, patch.object(bcb.bs, "_lark", _wide_lark(state, drop_row_after_first_slice=True)):
            with self.assertRaises(projection.ProjectionError) as ctx:
                bcb.export_content(MANIFEST, "basTOK", "product_matrix", Path(root), "lark-cli")
        self.assertIn("rows changed", str(ctx.exception))
        self.assertNotIn("recC", str(ctx.exception))
        self.assertNotIn("属性", str(ctx.exception))

    def test_cli_ignoring_projection_fails_instead_of_dropping_columns(self):
        state: dict = {}
        with temp_test_root() as root, patch.object(bcb.bs, "_lark", _wide_lark(state, ignore_projection=True)):
            with self.assertRaises(projection.ProjectionError):
                bcb.export_content(MANIFEST, "basTOK", "product_matrix", Path(root), "lark-cli")

    def test_truncated_field_list_fails(self):
        def fake(args, lark_cli="lark-cli"):
            return {"data": {"items": [{"field_id": "f", "name": "x", "type": "text"}], "has_more": True}}

        with patch.object(bcb.bs, "_lark", fake):
            with self.assertRaises(projection.ProjectionError):
                projection.list_fields("basTOK", "tblWIDE", "lark-cli")


class WithheldErrorDetailTests(unittest.TestCase):
    def _run(self, extra: list[str]) -> tuple[int, str, str]:
        state: dict = {}
        out, err = io.StringIO(), io.StringIO()
        with temp_test_root() as root, \
                patch.object(bcb.bs, "_lark", _wide_lark(state, fail_record_list=True)), \
                patch.dict(os.environ, {"MATRIX_TOKEN": "basTOK"}), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            manifest = Path(root) / "manifest.json"
            manifest.write_text(json.dumps(MANIFEST, ensure_ascii=False), encoding="utf-8")
            code = bcb.main(["export", "--manifest", str(manifest), "--base-token-env", "MATRIX_TOKEN",
                             "--label", "product_matrix", "--out", str(Path(root) / "out"), *extra])
        return code, out.getvalue(), err.getvalue()

    def test_withheld_failure_prints_only_the_error_type(self):
        code, out, err = self._run(["--withhold-error-detail"])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("RuntimeError", err)
        self.assertNotIn("P-SECRET-42", out + err)
        self.assertNotIn("MODEL-X", out + err)

    def test_without_the_flag_the_error_still_propagates(self):
        with self.assertRaises(RuntimeError):
            self._run([])


if __name__ == "__main__":
    unittest.main()
