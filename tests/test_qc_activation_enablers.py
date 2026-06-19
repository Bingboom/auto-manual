#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the F6/F8 activation enablers: table-based resolution + lark-cli transports."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.feishu_record_transport import (  # noqa: E402
    QcReportLarkTransport,
    SourceTableLarkTransport,
)
from tools.source_record_index import resolve_by_table  # noqa: E402
from tools.source_table_sync import build_change_requests  # noqa: E402

_SPEC_KEY = "\x1f".join(["JE-1000F_EU", "dc12_port", "main"])


def _spec_master_sidecar(record_id: str | None = "recDC12", ambiguous: bool = False) -> dict:
    table = {
        "key_fields": ["document_key", "Row_key", "Slot_key"],
        "records": {} if (ambiguous or record_id is None) else {_SPEC_KEY: record_id},
        "ambiguous": [_SPEC_KEY] if ambiguous else [],
    }
    return {"schema_version": "source-record-index/v1", "tables": {"Spec_Master": table}}


def _spec_source_ref() -> dict:
    return {
        "table": "Spec_Master",
        "field": "Value_uk",
        "document_key": "JE-1000F_EU",
        "row_key": "dc12_port",
        "slot_key": "main",
    }


class ResolveByTableTests(unittest.TestCase):
    def test_resolves_spec_master_by_keys(self) -> None:
        self.assertEqual(
            resolve_by_table(_spec_master_sidecar(), _spec_source_ref()),
            ("recDC12", "resolved"),
        )

    def test_unknown_table_is_unresolved(self) -> None:
        self.assertEqual(resolve_by_table(_spec_master_sidecar(), {"table": "Nope"}), (None, "unresolved"))

    def test_missing_key_field_is_unresolved(self) -> None:
        ref = {**_spec_source_ref(), "slot_key": ""}
        self.assertEqual(resolve_by_table(_spec_master_sidecar(), ref), (None, "unresolved"))

    def test_ambiguous_key_abstains(self) -> None:
        self.assertEqual(
            resolve_by_table(_spec_master_sidecar(ambiguous=True), _spec_source_ref()),
            (None, "ambiguous"),
        )


class ChangeRequestTableResolutionTests(unittest.TestCase):
    def test_change_request_resolves_via_table(self) -> None:
        diff_report = {
            "deltas": [
                {
                    "route_class": "source_table_suggestion",
                    "delta_hash": "h1",
                    "source_ref": _spec_source_ref(),
                    "old_text": "DC 12 V",
                    "new_text": "DC 12 В",
                }
            ]
        }
        requests = build_change_requests(diff_report, sidecar_index=_spec_master_sidecar())
        self.assertEqual(requests[0]["record_id"], "recDC12")
        self.assertEqual(requests[0]["resolution_status"], "resolved")


class _FakeSource:
    def __init__(self, records: list[dict] | None = None) -> None:
        self.upserts: list[dict] = []
        self._records = records or []

    def upsert_record(self, *, base_token, table_id, record_id, record):
        self.upserts.append({"base_token": base_token, "table_id": table_id, "record_id": record_id, "record": record})
        return {"ok": True}

    def fetch_records_with_ids(self, *, base_token, table_id, view_id):
        return list(self._records)


class SourceTableTransportTests(unittest.TestCase):
    def _transport(self, source):
        return SourceTableLarkTransport(source=source, binding_for=lambda t: ("BASE", f"tbl_{t}"))

    def test_upsert_routes_to_binding(self) -> None:
        source = _FakeSource()
        self._transport(source).upsert(table="Spec_Master", record_id="recX", field="Value_uk", value="DC 12 В")
        self.assertEqual(source.upserts[0]["table_id"], "tbl_Spec_Master")
        self.assertEqual(source.upserts[0]["record"], {"Value_uk": "DC 12 В"})

    def test_get_finds_record_field(self) -> None:
        source = _FakeSource([{"record_id": "recX", "fields": {"Value_uk": "DC 12 В"}}])
        self.assertEqual(self._transport(source).get(table="Spec_Master", record_id="recX", field="Value_uk"), "DC 12 В")

    def test_get_missing_record_returns_none(self) -> None:
        self.assertIsNone(self._transport(_FakeSource()).get(table="Spec_Master", record_id="recX", field="Value_uk"))


class QcReportTransportTests(unittest.TestCase):
    def _transport(self, source):
        return QcReportLarkTransport(source=source, base_token="BASE", table_id="tbl_qc")

    def test_list_finding_hashes(self) -> None:
        source = _FakeSource(
            [{"record_id": "r1", "fields": {"finding_hash": "fh1"}}, {"record_id": "r2", "fields": {"finding_hash": "fh2"}}]
        )
        self.assertEqual(self._transport(source).list_finding_hashes(), {"fh1", "fh2"})

    def test_append_row_is_not_yet_wired(self) -> None:
        with self.assertRaises(NotImplementedError):
            self._transport(_FakeSource()).append_row(row={"finding_hash": "fh1"})


if __name__ == "__main__":
    unittest.main()
