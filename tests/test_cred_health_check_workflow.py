from __future__ import annotations

import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
CRED_WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "cred-health-check.yml"
VALIDATION_WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "manual-validation.yml"


class CredHealthCheckWorkflowTests(unittest.TestCase):
    def test_cred_health_check_runs_only_on_hello_docs_when_unpaused(self) -> None:
        workflow = yaml.safe_load(CRED_WORKFLOW_PATH.read_text(encoding="utf-8"))
        self.assertEqual(["check"], list(workflow["jobs"]))
        self.assertEqual(
            "${{ github.repository == 'Bingboom/Hello-Docs' && vars.FEISHU_BUILD_QUEUE_PAUSED != 'true' }}",
            workflow["jobs"]["check"]["if"],
        )

    def test_doctor_en_declares_job_timeout(self) -> None:
        workflow = yaml.safe_load(VALIDATION_WORKFLOW_PATH.read_text(encoding="utf-8"))
        doctor = workflow["jobs"]["doctor-en"]
        self.assertEqual(15, doctor["timeout-minutes"])


if __name__ == "__main__":
    unittest.main()
