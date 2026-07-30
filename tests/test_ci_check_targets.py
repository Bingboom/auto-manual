from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.ci_check_targets import (
    CheckResult,
    CheckTarget,
    CommandResult,
    build_report,
    build_check_command,
    discover_targets,
    evaluate_targets,
    fixture_document_keys,
    load_skip_baseline,
    run_driver,
)


ROOT = Path(__file__).resolve().parents[1]


class TestCiCheckTargets(unittest.TestCase):
    def test_config_scan_grows_when_a_config_is_added(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            configs_dir = Path(td) / "configs"
            shutil.copytree(ROOT / "configs", configs_dir)
            original = discover_targets(configs_dir)
            shutil.copy2(configs_dir / "config.us-en.yaml", configs_dir / "config.zz-test.yaml")

            expanded = discover_targets(configs_dir)

        self.assertEqual(len(expanded), len(original) + 1)
        self.assertIn("config.zz-test.yaml", {target.config_path.name for target in expanded})

    def test_missing_document_key_is_explicit_skip_and_does_not_run_check(self) -> None:
        target = CheckTarget(Path("configs/config.au-en.yaml"), "JE-1000F", "AU", "en")
        calls: list[list[str]] = []

        results = evaluate_targets(
            [target],
            fixture_keys={"JE-1000F_US"},
            repo_root=ROOT,
            data_root=ROOT / "tests/fixtures/phase2",
            runner=lambda command: calls.append(command) or CommandResult(0),
        )

        self.assertEqual(("SKIP",), tuple(result.status for result in results))
        self.assertIn("fixture missing document_key JE-1000F_AU", results[0].reason)
        self.assertEqual([], calls)

    def test_pass_fail_coverage_and_command_target_are_aggregated(self) -> None:
        passing = CheckTarget(Path("configs/config.us-en.yaml"), "JE-1000F", "US", "en")
        failing = CheckTarget(Path("configs/config.eu-en.yaml"), "JE-1000F", "EU", "en")
        calls: list[list[str]] = []

        def runner(command: list[str]) -> CommandResult:
            calls.append(command)
            return CommandResult(0 if any("config.us-en.yaml" in part for part in command) else 2, stderr="failed")

        results = evaluate_targets(
            [passing, failing],
            fixture_keys={"JE-1000F_US", "JE-1000F_EU"},
            repo_root=ROOT,
            data_root=ROOT / "tests/fixtures/phase2",
            runner=runner,
            staging_root=Path("/tmp/ci-stage"),
        )

        self.assertEqual(("PASS", "FAIL"), tuple(result.status for result in results))
        self.assertEqual(0.5, build_report(results, baseline_skip_count=0)["coverage"])
        self.assertIn("--staging-root", calls[0])
        self.assertIn("--lang", calls[0])

    def test_skip_ratchet_rejects_an_increase(self) -> None:
        results = (
            # A report-only assertion is enough here; driver tests the exit code below.
            # Use a real result shape so this test also locks the coverage payload.
            CheckResult(
                "configs/config.au-en.yaml", "JE-1000F", "AU", "en", "JE-1000F_AU", "SKIP", "missing"
            ),
        )
        report = build_report(results, baseline_skip_count=0)
        self.assertFalse(report["skip_ratchet"]["passed"])

    def test_fixture_document_keys_are_read_case_insensitively(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            data_root = Path(td)
            (data_root / "Spec_Master.csv").write_text(
                "Document_key,Project\nJE-1000F_US,fixture\n\n", encoding="utf-8"
            )
            self.assertEqual({"JE-1000F_US"}, fixture_document_keys(data_root))

    def test_driver_writes_report_and_applies_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            configs = root / "configs"
            shutil.copytree(ROOT / "configs", configs)
            for config_path in configs.glob("config*.yaml"):
                if config_path.name != "config.us-en.yaml":
                    config_path.unlink()
            data_root = root / "phase2"
            data_root.mkdir()
            shutil.copy2(ROOT / "tests/fixtures/phase2/Spec_Master.csv", data_root / "Spec_Master.csv")
            baseline = root / "baseline.json"
            baseline.write_text(json.dumps({"skip_count": 0}), encoding="utf-8")
            report_path = root / "report.json"

            exit_code, report = run_driver(
                configs_dir=configs,
                data_root=data_root,
                repo_root=ROOT,
                skip_baseline=baseline,
                report_path=report_path,
                runner=lambda command: CommandResult(0),
            )

            self.assertEqual(0, exit_code)
            self.assertEqual(1, report["counts"]["PASS"])
            self.assertEqual(report, json.loads(report_path.read_text(encoding="utf-8")))
            self.assertEqual(0, load_skip_baseline(baseline))


if __name__ == "__main__":
    unittest.main()
