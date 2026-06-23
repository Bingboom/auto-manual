#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CI guard for the live verification orchestrator (tools/backport_live_check.py).

The orchestrator itself is operator-run against the Feishu tenant; these tests
exercise its orchestration logic with the live fetch + sandbox transport mocked,
so the routing/assertion/write-gate behaviour is guaranteed without tenant creds.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.backport_live_check import main, run_live  # noqa: E402
from tools.source_record_index import build_index  # noqa: E402
from tools.token_resolution_map import build_value_index  # noqa: E402


class _FakeTransport:
    def __init__(self, seed: dict[tuple, str]) -> None:
        self.store = dict(seed)

    def get(self, *, table, record_id, field):
        return self.store.get((table, record_id, field))

    def upsert(self, *, table, record_id, field, value) -> None:
        self.store[(table, record_id, field)] = value


_KEY = ("Spec_Master", "rec1", "Value_fr")
_BASELINE = "Sortie USB-A 18 W\n\nL'appareil démarre la charge."
_EDITED = "Sortie USB-A 20 W\n\nL'appareil commence la charge."


class BackportLiveCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        root = Path(cls._tmp.name)
        (root / "Spec_Master.csv").write_text(
            "document_key,Page,Row_key,Slot_key,Source_lang,Value_fr\n"
            "JE-2000F_EU,Specifications,usb_a,front.spec,fr,Sortie USB-A 18 W\n",
            encoding="utf-8",
        )
        cls.value_index = build_value_index(root, "fr")
        cls.sidecar = build_index(
            {"Spec_Master": [({"document_key": "JE-2000F_EU", "Row_key": "usb_a", "Slot_key": "front.spec"}, "rec1")]}
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def _run(self, **kwargs):
        return run_live(
            cloud_doc="https://x.feishu.cn/wiki/live",
            baseline_text=_BASELINE,
            lang="fr",
            value_index=self.value_index,
            sidecar=self.sidecar,
            fetch_fn=lambda _url: _EDITED,
            **kwargs,
        )

    def test_read_only_round_trip_routes_and_asserts(self) -> None:
        result = self._run(expect={"routes": {"source_table_suggestion": 1, "repo_review_text": 1}, "total": 2})
        self.assertTrue(result["passed"], result["mismatches"])
        self.assertEqual(result["routes"], {"source_table_suggestion": 1, "repo_review_text": 1})
        self.assertFalse(result["wrote"])
        self.assertEqual(result["resolved_requests"], 1)

    def test_sandbox_write_applies_and_verifies(self) -> None:
        fake = _FakeTransport({_KEY: "Sortie USB-A 18 W"})
        result = self._run(
            write=True,
            bindings={"Spec_Master": ("baseSANDBOX", "tblSANDBOX")},
            transport_factory=lambda: fake,
        )
        self.assertTrue(result["passed"], result["mismatches"])
        self.assertTrue(result["wrote"])
        self.assertEqual(result["applied"]["written"], 1)
        self.assertEqual(fake.store[_KEY], "Sortie USB-A 20 W")  # the edit landed in the sandbox cell

    def test_sandbox_write_reports_drift_without_clobbering(self) -> None:
        # The sandbox cell drifted from the expected old value -> abstain, flagged.
        fake = _FakeTransport({_KEY: "Sortie USB-A 99 W"})
        result = self._run(
            write=True,
            bindings={"Spec_Master": ("baseSANDBOX", "tblSANDBOX")},
            transport_factory=lambda: fake,
        )
        self.assertFalse(result["passed"])
        self.assertEqual(result["applied"]["drift_abstained"], 1)
        self.assertEqual(fake.store[_KEY], "Sortie USB-A 99 W")  # untouched

    def test_write_without_binding_is_refused(self) -> None:
        with self.assertRaises(RuntimeError):
            self._run(write=True, bindings=None)

    def test_expectation_mismatch_is_reported(self) -> None:
        result = self._run(expect={"total": 99})
        self.assertFalse(result["passed"])
        self.assertTrue(any("total" in m for m in result["mismatches"]))

    def test_cli_refuses_write_without_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            baseline = Path(tmp) / "baseline.md"
            baseline.write_text(_BASELINE, encoding="utf-8")
            code = main(
                [
                    "--cloud-doc", "https://x/wiki/live",
                    "--baseline-md", str(baseline),
                    "--lang", "fr",
                    "--write",
                ]
            )
        self.assertEqual(code, 2)  # refused before any fetch/write


if __name__ == "__main__":
    unittest.main()
