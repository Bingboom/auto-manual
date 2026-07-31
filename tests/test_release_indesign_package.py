#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""InDesign package lineage recorded into the release manifest."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.release_indesign_package import (  # noqa: E402
    collect_indesign_package,
    csv_columns,
)

FINALIZE_PASS = {
    "success": True,
    "page_count": 60,
    "overset_stories": [],
    "missing_fonts": [],
    "bad_links": [],
    "pdf_export_validation": {"pass": True},
    "toolchain": {"indesign_actual": "Adobe InDesign 2026"},
}


def _idml_dir(tmp: str, *, names=("manual_je1000f_us.idml",), reports=None) -> Path:
    idml_dir = Path(tmp) / "idml"
    idml_dir.mkdir(parents=True)
    for name in names:
        (idml_dir / name).write_bytes(name.encode("utf-8"))
    for filename, payload in (reports or {}).items():
        (idml_dir / filename).write_text(json.dumps(payload), encoding="utf-8")
    return idml_dir


class CollectTest(unittest.TestCase):
    def test_records_every_deliverable_with_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = collect_indesign_package(idml_dir=_idml_dir(
                tmp,
                names=(
                    "manual_je1000f_us.idml",
                    "manual_je1000f_us.indd",
                    "manual_je1000f_us_indesign.pdf",
                    "manual_je1000f_us_publish_1.5_handoff.zip",
                ),
                reports={"finalize_report.json": FINALIZE_PASS,
                         "parity_report.json": {"schema_version": "v2", "accepted": True}},
            ))
        self.assertTrue(record["complete"])
        self.assertEqual(record["idml"]["name"], "manual_je1000f_us.idml")
        self.assertEqual(len(record["indd"]["sha256"]), 64)
        self.assertEqual(record["handoff_zip"]["name"],
                         "manual_je1000f_us_publish_1.5_handoff.zip")
        self.assertEqual(record["preflight"], {
            "success": True, "page_count": 60, "overset_stories": 0,
            "missing_fonts": 0, "bad_links": 0, "pdfx_validated": True,
            "indesign": "Adobe InDesign 2026",
        })
        self.assertEqual(record["parity"], {"schema_version": "v2", "accepted": True})

    def test_idml_only_target_is_recorded_as_incomplete(self):
        """Finalize runs on an operator Mac, so CI publishes have IDML alone."""
        with tempfile.TemporaryDirectory() as tmp:
            record = collect_indesign_package(idml_dir=_idml_dir(tmp))
        self.assertFalse(record["complete"])
        self.assertIsNotNone(record["idml"])
        for absent in ("indd", "indesign_pdf", "handoff_zip", "finalize_report"):
            self.assertIsNone(record[absent], absent)
        self.assertIsNone(record["preflight"])

    def test_preflight_failure_is_reported_not_hidden(self):
        failing = dict(FINALIZE_PASS, success=False,
                       overset_stories=[{"index": 3}], missing_fonts=[{"name": "Gilroy"}])
        with tempfile.TemporaryDirectory() as tmp:
            record = collect_indesign_package(idml_dir=_idml_dir(
                tmp, reports={"finalize_report.json": failing}))
        self.assertFalse(record["preflight"]["success"])
        self.assertEqual(record["preflight"]["overset_stories"], 1)
        self.assertEqual(record["preflight"]["missing_fonts"], 1)

    def test_unreadable_report_leaves_the_file_recorded_but_no_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            idml_dir = _idml_dir(tmp)
            (idml_dir / "finalize_report.json").write_text("{not json", encoding="utf-8")
            record = collect_indesign_package(idml_dir=idml_dir)
        self.assertIsNotNone(record["finalize_report"])
        self.assertIsNone(record["preflight"])

    def test_missing_overset_field_remains_unknown(self):
        partial = dict(FINALIZE_PASS)
        partial.pop("overset_stories")
        with tempfile.TemporaryDirectory() as tmp:
            record = collect_indesign_package(idml_dir=_idml_dir(
                tmp, reports={"finalize_report.json": partial}))
        self.assertIsNone(record["preflight"]["overset_stories"])
        self.assertEqual(
            "", csv_columns(record)["indesign_preflight_overset_stories"]
        )

    def test_no_idml_dir_and_no_idml_file_yield_no_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(collect_indesign_package(idml_dir=Path(tmp) / "absent"))
            empty = Path(tmp) / "idml"
            empty.mkdir()
            self.assertIsNone(collect_indesign_package(idml_dir=empty))


class CsvColumnTest(unittest.TestCase):
    def test_columns_carry_verdicts_and_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = collect_indesign_package(idml_dir=_idml_dir(
                tmp,
                names=("manual_je1000f_us.idml", "manual_je1000f_us.indd",
                       "manual_je1000f_us_indesign.pdf", "m_handoff.zip"),
                reports={"finalize_report.json": FINALIZE_PASS,
                         "parity_report.json": {"accepted": False}},
            ))
        columns = csv_columns(record)
        self.assertEqual(columns["indesign_package_complete"], "TRUE")
        self.assertEqual(columns["indesign_preflight_success"], "TRUE")
        self.assertEqual(columns["indesign_preflight_page_count"], "60")
        self.assertEqual(columns["indesign_preflight_overset_stories"], "0")
        self.assertEqual(columns["indesign_parity_accepted"], "FALSE")
        self.assertEqual(len(columns["indesign_idml_sha256"]), 64)

    def test_absent_package_still_yields_every_column_blank(self):
        columns = csv_columns(None)
        self.assertEqual(columns["indesign_package_complete"], "FALSE")
        self.assertEqual(columns["indesign_preflight_success"], "")
        self.assertEqual(columns["indesign_parity_accepted"], "")
        self.assertEqual(sorted(columns), [
            "indesign_handoff_zip_sha256",
            "indesign_idml_sha256",
            "indesign_indd_sha256",
            "indesign_package_complete",
            "indesign_parity_accepted",
            "indesign_preflight_overset_stories",
            "indesign_preflight_page_count",
            "indesign_preflight_success",
        ])


if __name__ == "__main__":
    unittest.main()
