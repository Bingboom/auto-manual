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
    load_fail_baseline,
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

    def test_shared_family_config_expands_every_target(self) -> None:
        targets = tuple(
            target
            for target in discover_targets(ROOT / "configs")
            if target.config_path.name == "config.kr.yaml"
        )

        self.assertEqual(
            (
                ("JE-1000F", "KR", "ko"),
                ("JE-2000E", "KR", "ko"),
                ("JE-3000C", "KR", "ko"),
            ),
            tuple((target.model, target.region, target.lang) for target in targets),
        )

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

    def test_fail_ratchet_rejects_an_increase(self) -> None:
        results = (
            CheckResult(
                "configs/config.eu-uk.yaml", "JE-1000F", "EU", "uk", "JE-1000F_EU", "FAIL", "boom"
            ),
            CheckResult(
                "configs/config.zh.yaml", "JE-2000E", "CN", None, "JE-2000E_CN", "FAIL", "boom"
            ),
        )

        self.assertTrue(
            build_report(results, baseline_skip_count=0, baseline_fail_count=2)["fail_ratchet"]["passed"]
        )
        self.assertFalse(
            build_report(results, baseline_skip_count=0, baseline_fail_count=1)["fail_ratchet"]["passed"]
        )

    def test_report_omits_the_fail_ratchet_when_the_baseline_does_not_declare_one(self) -> None:
        """An older baseline file keeps loading; it just gets no FAIL ratchet."""
        results = (
            CheckResult(
                "configs/config.zh.yaml", "JE-2000E", "CN", None, "JE-2000E_CN", "FAIL", "boom"
            ),
        )

        self.assertNotIn("fail_ratchet", build_report(results, baseline_skip_count=0))

    def test_observation_lane_fails_when_the_fail_ratchet_is_exceeded(self) -> None:
        """The point of the ratchet: --observation no longer hides a regression.

        The lane runs with --observation so the two known-failing targets do not
        turn CI red. Before this, that also meant a target sliding from PASS to
        FAIL was invisible — only the SKIP ratchet could fail the job.
        """
        for baseline_fail, expected_exit in ((1, 0), (0, 1)):
            with self.subTest(fail_count=baseline_fail):
                with tempfile.TemporaryDirectory() as td:
                    root = Path(td)
                    configs = root / "configs"
                    shutil.copytree(ROOT / "configs", configs)
                    for config_path in configs.glob("config*.yaml"):
                        if config_path.name != "config.us-en.yaml":
                            config_path.unlink()
                    data_root = root / "phase2"
                    data_root.mkdir()
                    shutil.copy2(
                        ROOT / "tests/fixtures/phase2/Spec_Master.csv",
                        data_root / "Spec_Master.csv",
                    )
                    baseline = root / "baseline.json"
                    baseline.write_text(
                        json.dumps({"skip_count": 0, "fail_count": baseline_fail}),
                        encoding="utf-8",
                    )

                    exit_code, report = run_driver(
                        configs_dir=configs,
                        data_root=data_root,
                        repo_root=ROOT,
                        skip_baseline=baseline,
                        fail_on_failures=False,
                        runner=lambda command: CommandResult(7, stdout="observed failure"),
                    )

                    self.assertEqual(expected_exit, exit_code)
                    self.assertEqual(1, report["counts"]["FAIL"])
                    self.assertEqual(baseline_fail, load_fail_baseline(baseline))

    def test_committed_baseline_arms_both_ratchets(self) -> None:
        """Guard the gate itself: dropping fail_count would silently disarm it."""
        baseline = ROOT / ".github" / "ci_check_targets_skip_baseline.json"
        payload = json.loads(baseline.read_text(encoding="utf-8"))

        self.assertIsInstance(payload.get("skip_count"), int)
        self.assertIsInstance(payload.get("fail_count"), int)
        self.assertEqual(payload["skip_count"], load_skip_baseline(baseline))
        self.assertEqual(payload["fail_count"], load_fail_baseline(baseline))
        # Every named config must still exist, or the reason text is fiction.
        for key in ("skipped_configs", "failing_configs"):
            for relative in payload.get(key, []):
                with self.subTest(config=relative):
                    self.assertTrue((ROOT / relative).is_file(), relative)

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

    def test_observation_lane_reports_failures_without_failing(self) -> None:
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

            exit_code, report = run_driver(
                configs_dir=configs,
                data_root=data_root,
                repo_root=ROOT,
                skip_baseline=baseline,
                fail_on_failures=False,
                runner=lambda command: CommandResult(7, stdout="observed failure"),
            )

            self.assertEqual(0, exit_code)
            self.assertEqual(1, report["counts"]["FAIL"])


if __name__ == "__main__":
    unittest.main()
