from __future__ import annotations

import unittest
from pathlib import Path

from tools.data_plane_doctor import collect_data_plane_findings
from tools.validate_config import load_yaml


ROOT = Path(__file__).resolve().parents[1]


class TestDataPlaneDoctor(unittest.TestCase):
    def setUp(self) -> None:
        self.cfg_path = ROOT / "configs/config.us-en.yaml"
        self.cfg = load_yaml(self.cfg_path)

    def test_fixture_snapshot_and_target_rows_pass(self) -> None:
        findings = collect_data_plane_findings(
            cfg=self.cfg,
            cfg_path=self.cfg_path,
            repo_root=ROOT,
            model="JE-1000F",
            region="US",
            data_root="tests/fixtures/phase2",
        )

        self.assertEqual(["OK", "OK"], [level for level, _, _ in findings])
        self.assertIn("complete phase2 snapshot", findings[0][2])
        self.assertIn("required source rows", findings[1][2])

    def test_missing_snapshot_fails_before_spec_row_lookup(self) -> None:
        findings = collect_data_plane_findings(
            cfg=self.cfg,
            cfg_path=self.cfg_path,
            repo_root=ROOT,
            model="JE-1000F",
            region="US",
            data_root="tests/fixtures/does-not-exist",
        )

        self.assertEqual("ERROR", findings[0][0])
        self.assertEqual("data_plane.snapshot", findings[0][1])
        self.assertIn("snapshot manifest not found", findings[0][2])

    def test_data_plane_requires_one_target(self) -> None:
        findings = collect_data_plane_findings(
            cfg=self.cfg,
            cfg_path=self.cfg_path,
            repo_root=ROOT,
            model=None,
            region="US",
            data_root="tests/fixtures/phase2",
        )

        self.assertEqual(
            [("ERROR", "data_plane.target", "data-plane preflight requires one explicit model and region")],
            findings,
        )


if __name__ == "__main__":
    unittest.main()
