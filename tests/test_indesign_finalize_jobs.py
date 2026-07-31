from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.indesign_finalize_jobs import (
    JOBS_SCHEMA_VERSION,
    normalize_jobs,
    run_jobs_manifest,
    scan_incomplete_packages,
    validate_jobs_manifest,
)
from tools.indesign_finalize import main as finalize_main


def _job(job_id: str, *, root: str = "artifacts") -> dict[str, str]:
    prefix = f"{root}/{job_id}"
    return {
        "id": job_id,
        "idml": f"{prefix}.idml",
        "indd": f"{prefix}.indd",
        "pdf": f"{prefix}.pdf",
        "report": f"{prefix}.json",
        "pdf_preset": "[PDF/X-4:2008 (Japan)]",
        "output_intent": "Japan Color 2001 Coated",
        "output_condition": "JC200103",
        "pdfx": "PDF/X-4",
    }


class ManifestValidationTests(unittest.TestCase):
    def test_normalizes_paths_relative_to_manifest_and_keeps_explicit_contract(self) -> None:
        payload = {"schema_version": JOBS_SCHEMA_VERSION, "jobs": [_job("en")]}
        with tempfile.TemporaryDirectory() as tmp:
            jobs = normalize_jobs(payload, base=Path(tmp))
        self.assertEqual(jobs[0]["job_id"], "en")
        self.assertEqual(jobs[0]["input_idml"], str((Path(tmp) / "artifacts/en.idml").resolve()))
        self.assertEqual(jobs[0]["pdf_preset"], "[PDF/X-4:2008 (Japan)]")
        self.assertEqual(jobs[0]["output_intent"], "Japan Color 2001 Coated")

    def test_jobs_mode_requires_explicit_pdf_contract_fields(self) -> None:
        payload = {"schema_version": JOBS_SCHEMA_VERSION, "jobs": [_job("en")]}
        for field in ("pdf_preset", "output_intent", "output_condition", "pdfx"):
            candidate = json.loads(json.dumps(payload))
            del candidate["jobs"][0][field]
            issues = validate_jobs_manifest(candidate)
            self.assertTrue(any(field in issue for issue in issues), field)

    def test_duplicate_ids_and_outputs_are_rejected(self) -> None:
        first = _job("en")
        second = _job("en")
        second["idml"] = "other.idml"
        payload = {"schema_version": JOBS_SCHEMA_VERSION, "jobs": [first, second]}
        issues = validate_jobs_manifest(payload)
        self.assertTrue(any("duplicate job id" in issue for issue in issues))
        second["id"] = "fr"
        second["pdf"] = first["pdf"]
        issues = validate_jobs_manifest(payload)
        self.assertTrue(any("collides" in issue for issue in issues))


class BatchExecutionTests(unittest.TestCase):
    def test_finalize_cli_dispatches_jobs_manifest(self) -> None:
        with patch("tools.indesign_finalize_jobs.run_jobs_manifest", return_value=7) as run:
            with patch("sys.argv", ["indesign_finalize.py", "--jobs", "jobs.json"]):
                self.assertEqual(finalize_main(), 7)
        run.assert_called_once()

    def test_runner_failure_isolated_and_aggregate_is_written(self) -> None:
        payload = {"schema_version": JOBS_SCHEMA_VERSION, "jobs": [_job("ok"), _job("bad")]}
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "jobs.json"
            manifest.write_text(json.dumps(payload), encoding="utf-8")

            def runner(job: dict[str, str], status: str, message: str) -> dict[str, object]:
                if job["job_id"] == "bad":
                    raise RuntimeError("simulated InDesign failure")
                return {"job_id": job["job_id"], "success": True}

            report = Path(tmp) / "aggregate.json"
            exit_code = run_jobs_manifest(
                manifest,
                aggregate_report=report,
                runner=runner,
                version_checker=lambda: ("match", "pinned"),
            )
            aggregate = json.loads(report.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 1)
        self.assertFalse(aggregate["success"])
        self.assertEqual([item["job_id"] for item in aggregate["jobs"]], ["ok", "bad"])
        self.assertTrue(aggregate["jobs"][0]["success"])
        self.assertIn("simulated InDesign failure", aggregate["jobs"][1]["error"])

    def test_version_gate_prevents_runner_and_records_before_scan(self) -> None:
        payload = {"schema_version": JOBS_SCHEMA_VERSION, "jobs": [_job("en")]}
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "jobs.json"
            report = Path(tmp) / "aggregate.json"
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            with patch("tools.indesign_finalize_jobs.scan_incomplete_packages") as scan:
                scan.return_value = {"scanned": 1, "incomplete_count": 0}
                exit_code = run_jobs_manifest(
                    manifest,
                    aggregate_report=report,
                    runner=lambda *_: self.fail("runner must not run"),
                    version_checker=lambda: ("no_indesign", "missing"),
                )
            aggregate = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(exit_code, 2)
        self.assertEqual(aggregate["error"], "missing")
        self.assertEqual(aggregate["package_scan_after"], aggregate["package_scan_before"])

    def test_scan_reports_incomplete_package_batch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            idml_dir = Path(tmp) / "idml"
            idml_dir.mkdir()
            idml = idml_dir / "manual_je1000f_us.idml"
            idml.write_text("idml", encoding="utf-8")
            result = scan_incomplete_packages([{
                "job_id": "en",
                "input_idml": str(idml),
            }])
        self.assertEqual(result["incomplete_count"], 1)
        self.assertEqual(result["batches"][0]["job_ids"], ["en"])
        self.assertIn("indd", result["items"][0]["missing"])


if __name__ == "__main__":
    unittest.main()
