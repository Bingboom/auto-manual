#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The guard that would have caught #720's decoupled reference-layout pin."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import check_reference_layout_pins as guard  # noqa: E402


def _repo(tmp: str, *, identity: dict) -> Path:
    root = Path(tmp)
    contracts = root.joinpath(*guard.CONTRACTS_SUBDIR)
    contracts.mkdir(parents=True)
    (contracts / "je1000f_us_v2.json").write_text(
        json.dumps({
            "approval": {"status": "approved"},
            "source_identity": identity,
        }),
        encoding="utf-8",
    )
    return root


class PinDriftTest(unittest.TestCase):
    def setUp(self):
        patches = (
            mock.patch.object(guard, "_layout_pin", lambda repo_root: "layout-actual"),
            mock.patch.object(guard, "_style_pin", lambda repo_root: "style-actual"),
        )
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def test_matching_pins_are_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp, identity={
                "layout_params_sha256": "layout-actual",
                "style_contract_sha256": "style-actual",
            })
            self.assertEqual(guard.collect_pin_drift(root), [])
            self.assertEqual(guard.main(["--repo-root", str(root)]), 0)

    def test_stale_layout_pin_is_reported_and_fails(self):
        """#720's exact shape: the CSV moved, the pin did not."""
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp, identity={
                "layout_params_sha256": "layout-before-the-correction",
                "style_contract_sha256": "style-actual",
            })
            drift = guard.collect_pin_drift(root)
            self.assertEqual(len(drift), 1)
            _contract, name, pinned, actual = drift[0]
            self.assertEqual(name, "layout_params_sha256")
            self.assertEqual(pinned, "layout-before-the-correction")
            self.assertEqual(actual, "layout-actual")
            self.assertEqual(guard.main(["--repo-root", str(root)]), 1)

    def test_stale_style_pin_is_reported_too(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp, identity={"style_contract_sha256": "stale"})
            self.assertEqual(
                [name for _c, name, _p, _a in guard.collect_pin_drift(root)],
                ["style_contract_sha256"],
            )

    def test_snapshot_pins_are_out_of_scope(self):
        """They derive from an untracked snapshot; a checkout cannot verify them."""
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp, identity={
                "manual_content_sha256": "anything",
                "snapshot_sha256": "anything",
                "layout_params_sha256": "layout-actual",
                "style_contract_sha256": "style-actual",
            })
            self.assertEqual(guard.collect_pin_drift(root), [])

    def test_absent_pin_is_skipped_rather_than_failed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp, identity={"style_contract_sha256": "style-actual"})
            self.assertEqual(guard.collect_pin_drift(root), [])

    def test_contract_without_source_identity_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contracts = root.joinpath(*guard.CONTRACTS_SUBDIR)
            contracts.mkdir(parents=True)
            (contracts / "notes.json").write_text('{"pages": []}', encoding="utf-8")
            self.assertEqual(guard.collect_pin_drift(root), [])

    def test_unreadable_contract_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contracts = root.joinpath(*guard.CONTRACTS_SUBDIR)
            contracts.mkdir(parents=True)
            (contracts / "broken.json").write_text("{not json", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                guard.collect_pin_drift(root)

    def test_no_contracts_directory_is_a_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(guard.main(["--repo-root", str(Path(tmp))]), 0)


class RealRepoTest(unittest.TestCase):
    def test_the_committed_contracts_agree_with_the_tracked_files(self):
        """Guards the guard: this repo must stay pin-consistent."""
        self.assertEqual(guard.collect_pin_drift(ROOT), [])


if __name__ == "__main__":
    unittest.main()
