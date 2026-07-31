from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.ci_check_targets import CheckTarget
from tools.nightly_render import (
    CommandResult,
    PilotArtifact,
    build_doctor_command,
    build_pilot_command,
    resolve_pilot_target,
    run_nightly,
)


ROOT = Path(__file__).resolve().parents[1]


class TestNightlyRender(unittest.TestCase):
    def test_commands_keep_target_identity_explicit(self) -> None:
        target = CheckTarget(ROOT / "configs/config.us-en.yaml", "MODEL-X", "US", "en")
        data_root = ROOT / "tests/fixtures/phase2"

        doctor = build_doctor_command(target, repo_root=ROOT, data_root=data_root)
        pilot = build_pilot_command(target, repo_root=ROOT, data_root=data_root)

        self.assertIn("doctor", doctor)
        self.assertIn("--config", doctor)
        self.assertIn("MODEL-X", doctor)
        self.assertIn("--lang", doctor)
        self.assertIn("idml", pilot)
        self.assertIn("production", pilot)
        self.assertIn("runtime", pilot)
        self.assertIn("--skip-root-index", pilot)

    def test_resolve_pilot_target_rejects_config_target_drift(self) -> None:
        target = CheckTarget(ROOT / "configs/config.us-en.yaml", "JE-1000F", "US", "en")

        with self.assertRaisesRegex(RuntimeError, "does not match"):
            resolve_pilot_target(
                [target],
                pilot_config=target.config_path,
                pilot_model="OTHER",
                pilot_region="US",
                pilot_lang="en",
            )

    def test_run_nightly_aggregates_all_doctors_and_pilot(self) -> None:
        passing = CheckTarget(ROOT / "configs/config.us-en.yaml", "JE-1000F", "US", "en")
        failing = CheckTarget(ROOT / "configs/config.eu-en.yaml", "JE-1000F", "EU", "en")
        calls: list[list[str]] = []

        def runner(command: list[str]) -> CommandResult:
            calls.append(command)
            if "doctor" in command and any("config.eu-en.yaml" in part for part in command):
                return CommandResult(7, stderr="doctor drift")
            return CommandResult(0)

        with tempfile.TemporaryDirectory() as td:
            report_path = Path(td) / "nightly.json"
            exit_code, report = run_nightly(
                targets=[passing, failing],
                pilot_target=passing,
                repo_root=ROOT,
                data_root=ROOT / "tests/fixtures/phase2",
                report_path=report_path,
                runner=runner,
                artifact_probe=lambda _target: PilotArtifact(
                    path="docs/_build/pilot.idml",
                    sha256="abc123",
                    issues=(),
                ),
            )

            stored = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(1, exit_code)
        self.assertEqual({"PASS": 1, "FAIL": 1}, report["doctor"]["counts"])
        self.assertEqual("PASS", report["pilot"]["status"])
        self.assertEqual(report, stored)
        self.assertEqual(3, len(calls))

    def test_artifact_issues_fail_a_successful_build(self) -> None:
        target = CheckTarget(ROOT / "configs/config.us-en.yaml", "JE-1000F", "US", "en")

        exit_code, report = run_nightly(
            targets=[target],
            pilot_target=target,
            repo_root=ROOT,
            data_root=ROOT / "tests/fixtures/phase2",
            report_path=None,
            runner=lambda _command: CommandResult(0),
            artifact_probe=lambda _target: PilotArtifact(
                path="docs/_build/missing.idml",
                sha256=None,
                issues=("production IDML artifact is missing",),
            ),
        )

        self.assertEqual(1, exit_code)
        self.assertEqual("FAIL", report["pilot"]["status"])


if __name__ == "__main__":
    unittest.main()
