# -*- coding: utf-8 -*-
"""Wide-table / projected export and confidential-error handling for the content backup.

No live network: every lark-cli call goes through the ``tools.bitable_schema._lark`` seam.
Each failure test pins one way a backup could look complete while missing data
(exit 0, green run, sentinel Issue auto-closed); the export must fail instead.
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


def _wide_lark(state: dict, *, names: list[str] | None = None, rids: list[str] | None = None,
               default_field_page: int = 100, explicit_cap: int | None = None, report: str = "has_more",
               explicit_field_list: dict | None = None, drop_row_after_first_slice: bool = False,
               ignore_projection: bool = False, short_rows: bool = False, long_rows: bool = False,
               omit_has_more: bool = False,
               fail_record_list: Exception | None = None):
    """A canned lark-cli with one table 矩阵.

    ``default_field_page``: fields a +field-list WITHOUT --limit returns (CLI default page);
    ``explicit_cap``: server-side cap on --limit; ``report``: how truncation is signalled
    ("has_more", "total" or "none"); ``explicit_field_list``: canned reply to a --limit field list.
    """
    names = names or NAMES
    rids_all = rids or RIDS

    def fake(args, lark_cli="lark-cli"):
        state.setdefault("calls", []).append(list(args))
        sub = args[1]
        if sub == "+table-list":
            return {"data": {"items": [{"name": "矩阵", "table_id": "tblWIDE"}]}}
        if sub == "+field-list":
            explicit = "--limit" in args
            if explicit and explicit_field_list is not None:
                return explicit_field_list
            limit = int(args[args.index("--limit") + 1]) if explicit else default_field_page
            if explicit and explicit_cap is not None:
                limit = min(limit, explicit_cap)
            items = [{"field_id": f"fld{i}", "name": n, "type": "text"} for i, n in enumerate(names)]
            data: dict = {"items": items[:limit]}
            if report == "has_more":
                data["has_more"] = len(items) > limit
            elif report == "total":
                data["total"] = len(items)
            return {"data": data}
        if sub == "+record-list":
            if fail_record_list is not None:
                raise fail_record_list
            projected = [args[i + 1] for i, a in enumerate(args) if a == "--field-id"]
            state.setdefault("projections", []).append(projected)
            cols = names[:50] if ignore_projection else projected
            offset = int(args[args.index("--offset") + 1]) if "--offset" in args else 0
            limit = int(args[args.index("--limit") + 1])
            page_rids = list(rids_all)
            if drop_row_after_first_slice and len({tuple(p) for p in state["projections"]}) > 1:
                page_rids = page_rids[:-1]
            page_rids = page_rids[offset:offset + limit]
            rows = [[_cell(r, n) for n in cols] for r in page_rids]
            if short_rows:  # the CLI omits trailing empty cells: recA's last two cells in every slice
                rows = [row[:-2] if rid == "recA" else row for rid, row in zip(page_rids, rows, strict=True)]
            if long_rows:
                rows = [[*row, "extra"] for row in rows]
            data = {"fields": cols, "field_id_list": [f"fld{names.index(n)}" for n in cols],
                    "data": rows, "record_id_list": page_rids}
            if not omit_has_more:
                data["has_more"] = offset + limit < len(rids_all)
            return {"data": data}
        raise AssertionError(f"unexpected lark call: {args[:3]}")

    return fake


def _manifest(names: list[str] | None = None) -> dict:
    return {"schema_version": "bitable-schema/v1",
            "tables": [{"name": "矩阵", "fields": [{"name": n, "type": "text"} for n in (names or NAMES)]}]}


MANIFEST = _manifest()


def _export(fake, projected_read: bool = False, manifest: dict | None = None):
    with temp_test_root() as root, patch.object(bcb.bs, "_lark", fake):
        report = bcb.export_content(manifest or MANIFEST, "basTOK", "product_matrix", Path(root), "lark-cli",
                                    projected_read=projected_read)
        rows = []
        if report["tables"]:
            with (Path(root) / "product_matrix" / report["tables"][0]["csv"]).open(encoding="utf-8", newline="") as fh:
                rows = list(csv.DictReader(fh))
        return report, rows


class WideTableExportTests(unittest.TestCase):
    def test_projection_threshold(self):
        self.assertFalse(projection.needs_projection({f"f{i}": "text" for i in range(50)}))
        self.assertTrue(projection.needs_projection({f"f{i}": "text" for i in range(51)}))

    def test_wide_table_is_read_in_slices_and_merged_by_record(self):
        state: dict = {}
        report, rows = _export(_wide_lark(state))
        (entry,) = report["tables"]
        self.assertEqual(entry["rows"], 3)
        # the explicit field list (120) replaces the short default page (100)
        self.assertEqual(entry["columns"], NAMES)
        self.assertEqual([len(p) for p in state["projections"]], [50, 50, 20])
        self.assertEqual([n for p in state["projections"] for n in p], NAMES)
        self.assertEqual([r["_record_id"] for r in rows], RIDS)
        self.assertEqual(rows[1][NAMES[-1]], _cell("recB", NAMES[-1]))
        self.assertTrue(all(r[n] for r in rows for n in NAMES))

    def test_projected_read_survives_a_default_field_page_of_50(self):
        # simulation B: without --projected-read a 50-field default page hides the table's width
        state: dict = {}
        report, rows = _export(_wide_lark(state, default_field_page=50), projected_read=True)
        (entry,) = report["tables"]
        self.assertEqual(entry["columns"], NAMES)
        self.assertEqual(report["missing_columns"], {})
        self.assertTrue(all(r[n] for r in rows for n in NAMES))
        self.assertFalse(any(c[1] == "+field-list" and "--limit" not in c for c in state["calls"]))

    def test_projected_read_reports_manifest_fields_missing_from_the_export(self):
        report, _ = _export(_wide_lark({}), projected_read=True, manifest=_manifest([*NAMES, "已删的列"]))
        self.assertEqual(report["missing_columns"], {"矩阵": ["已删的列"]})

    def test_projected_read_reads_narrow_tables_through_projection_too(self):
        state: dict = {}
        narrow = NAMES[:10]
        report, rows = _export(_wide_lark(state, names=narrow), projected_read=True, manifest=_manifest(narrow))
        self.assertEqual(report["tables"][0]["columns"], narrow)
        self.assertEqual(state["projections"], [narrow])

    def test_rows_changing_between_slices_fails_without_cell_values(self):
        with self.assertRaises(projection.ProjectionError) as ctx:
            _export(_wide_lark({}, drop_row_after_first_slice=True))
        self.assertIn("rows changed", str(ctx.exception))
        self.assertNotIn("recC", str(ctx.exception))
        self.assertNotIn("属性", str(ctx.exception))

    def test_cli_ignoring_projection_fails_instead_of_dropping_columns(self):
        with self.assertRaises(projection.ProjectionError):
            _export(_wide_lark({}, ignore_projection=True))

    def test_short_rows_are_padded_at_the_end_and_counted(self):
        # simulation C: lark-cli omits trailing empty cells, as bitable_schema._read_records already accepts
        for projected_read in (False, True):
            with self.subTest(projected_read=projected_read):
                report, rows = _export(_wide_lark({}, short_rows=True), projected_read=projected_read)
                (entry,) = report["tables"]
                self.assertEqual(entry["short_rows"], 1)  # one record, short in all three slices
                rec_a = next(r for r in rows if r["_record_id"] == "recA")
                slice_ends = {NAMES[49], NAMES[48], NAMES[99], NAMES[98], NAMES[119], NAMES[118]}
                for name in NAMES:
                    expected = "" if name in slice_ends else _cell("recA", name)
                    self.assertEqual(rec_a[name], expected, name)
                self.assertTrue(all(r[n] for r in rows if r["_record_id"] != "recA" for n in NAMES))

    def test_long_rows_fail(self):
        for projected_read in (False, True):
            with self.subTest(projected_read=projected_read), self.assertRaises(projection.ProjectionError) as ctx:
                _export(_wide_lark({}, long_rows=True), projected_read=projected_read)
            self.assertIn("cells", str(ctx.exception))
            self.assertNotIn("extra", str(ctx.exception))

    def test_short_row_count_is_absent_on_the_historical_path(self):
        report, _ = _export(_wide_lark({}, names=NAMES[:5]), manifest=_manifest(NAMES[:5]))
        self.assertNotIn("short_rows", report["tables"][0])


class FieldListTests(unittest.TestCase):
    def _fails(self, fake, projected_read: bool = True):
        with self.assertRaises(projection.ProjectionError):
            _export(fake, projected_read=projected_read)

    def test_failed_field_list_fails(self):
        # simulation A: ok:false with exit 0, and non-JSON output wrapped as _raw by bitable_schema._lark
        for reply in ({"ok": False, "error": {"code": 99991400}}, {"ok": False, "_raw": "garbage"}):
            for projected_read in (False, True):
                with self.subTest(reply=reply, projected_read=projected_read):
                    self._fails(_wide_lark({}, explicit_field_list=reply), projected_read)

    def test_empty_field_list_fails(self):
        self._fails(_wide_lark({}, explicit_field_list={"data": {"items": [], "has_more": False}}))

    def test_has_more_fails(self):
        self._fails(_wide_lark({}, explicit_cap=100, report="has_more"))

    def test_total_beyond_returned_fields_fails(self):
        # simulation D: the CLI signals truncation only through total and caps --limit at 100
        for projected_read in (False, True):
            with self.subTest(projected_read=projected_read):
                self._fails(_wide_lark({}, explicit_cap=100, report="total"), projected_read)

    def test_second_read_with_fewer_fields_than_the_first_fails(self):
        # default page shows all 120, the explicit read silently stops at 100 with no signal
        with self.assertRaises(projection.ProjectionError) as ctx:
            _export(_wide_lark({}, default_field_page=200, explicit_cap=100, report="none"))
        self.assertIn("lacks 20 of the 120", str(ctx.exception))


class PaginationTests(unittest.TestCase):
    MANY = [f"rec{i:04d}" for i in range(450)]

    def test_rows_across_pages_are_all_exported(self):
        state: dict = {}
        report, rows = _export(_wide_lark(state, rids=self.MANY))
        self.assertEqual(report["tables"][0]["rows"], 450)
        self.assertEqual([r["_record_id"] for r in rows], self.MANY)
        offsets = [c[c.index("--offset") + 1] if "--offset" in c else "0" for c in state["calls"] if c[1] == "+record-list"]
        self.assertEqual(offsets, ["0", "200", "400"] * 3)

    def test_full_page_without_has_more_fails(self):
        with self.assertRaises(projection.ProjectionError) as ctx:
            _export(_wide_lark({}, rids=self.MANY, omit_has_more=True), projected_read=True)
        self.assertIn("without has_more", str(ctx.exception))

    def test_short_last_page_without_has_more_is_the_end(self):
        report, _ = _export(_wide_lark({}, rids=self.MANY[:150], omit_has_more=True), projected_read=True)
        self.assertEqual(report["tables"][0]["rows"], 150)


class NarrowTableCallSequenceTests(unittest.TestCase):
    def test_default_export_of_a_narrow_table_keeps_its_call_sequence(self):
        """The business / TM exports (all tables <= 50 fields) must issue exactly the historical calls."""
        state: dict = {}
        narrow = NAMES[:5]
        report, _ = _export(_wide_lark(state, names=narrow), manifest=_manifest(narrow))
        self.assertNotIn("missing_columns", report)
        common = ["--base-token", "basTOK"]
        self.assertEqual(state["calls"], [
            ["base", "+table-list", *common, "--format", "json", "--as", "bot"],
            ["base", "+field-list", *common, "--table-id", "tblWIDE", "--format", "json", "--as", "bot"],
            ["base", "+field-list", *common, "--table-id", "tblWIDE", "--format", "json", "--as", "bot"],
            ["base", "+record-list", *common, "--table-id", "tblWIDE", "--limit", "200", "--format", "json",
             "--as", "bot"],
        ])


class WithheldErrorDetailTests(unittest.TestCase):
    def _run(self, extra: list[str], error: Exception) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with temp_test_root() as root, \
                patch.object(bcb.bs, "_lark", _wide_lark({}, fail_record_list=error)), \
                patch.dict(os.environ, {"MATRIX_TOKEN": "basTOK"}), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            manifest = Path(root) / "manifest.json"
            manifest.write_text(json.dumps(MANIFEST, ensure_ascii=False), encoding="utf-8")
            code = bcb.main(["export", "--manifest", str(manifest), "--base-token-env", "MATRIX_TOKEN",
                             "--label", "product_matrix", "--out", str(Path(root) / "out"), *extra])
        return code, out.getvalue(), err.getvalue()

    def test_withheld_failure_prints_only_the_error_type(self):
        secret = "MODEL-X/US 项目号 P-SECRET-42"
        for error in (RuntimeError(f"Lark CLI command failed: stdout={secret}"), AttributeError(secret),
                      ZeroDivisionError(secret)):
            with self.subTest(error=type(error).__name__):
                code, out, err = self._run(["--projected-read", "--withhold-error-detail"], error)
                self.assertEqual(code, 1)
                self.assertEqual(out, "")
                self.assertIn(type(error).__name__, err)
                self.assertNotIn("P-SECRET-42", out + err)
                self.assertNotIn("MODEL-X", out + err)

    def test_without_the_flag_the_error_still_propagates(self):
        with self.assertRaises(RuntimeError):
            self._run([], RuntimeError("boom"))

    def test_missing_declared_columns_fail_the_cli(self):
        out = io.StringIO()
        with temp_test_root() as root, patch.object(bcb.bs, "_lark", _wide_lark({})), \
                patch.dict(os.environ, {"MATRIX_TOKEN": "basTOK"}), contextlib.redirect_stdout(out):
            manifest = Path(root) / "manifest.json"
            manifest.write_text(json.dumps(_manifest([*NAMES, "已删的列"]), ensure_ascii=False), encoding="utf-8")
            code = bcb.main(["export", "--manifest", str(manifest), "--base-token-env", "MATRIX_TOKEN",
                             "--label", "product_matrix", "--out", str(Path(root) / "out"),
                             "--projected-read", "--withhold-error-detail"])
        self.assertEqual(code, 1)
        self.assertIn("MISSING 1 declared column(s) in 矩阵: 已删的列", out.getvalue())
        self.assertIn("矩阵: 3 rows (0 short row(s) padded with trailing empty cells)", out.getvalue())
        self.assertNotIn("rec", out.getvalue())


if __name__ == "__main__":
    unittest.main()
