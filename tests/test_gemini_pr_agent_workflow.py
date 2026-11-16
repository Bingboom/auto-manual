from __future__ import annotations

import json
from pathlib import Path
import unittest

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "gemini-pr-agent.yml"


class GeminiPrAgentWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
        self.job = self.workflow["jobs"]["gemini-developer"]

    def test_workflow_runs_only_on_engineering_repo_and_trusted_associations(self) -> None:
        condition = str(self.job["if"])
        self.assertIn("github.repository == 'Bingboom/auto-manual'", condition)
        self.assertIn("!endsWith(github.actor, '[bot]')", condition)
        for association in ("OWNER", "MEMBER", "COLLABORATOR"):
            self.assertIn(association, condition)

    def test_gemini_step_loads_both_entrypoints_and_disables_public_artifact_upload(self) -> None:
        gemini_step = next(
            step for step in self.job["steps"] if step.get("id") == "gemini_run"
        )
        self.assertTrue(
            str(gemini_step["uses"]).startswith("google-github-actions/run-gemini-cli@")
        )
        with_cfg = gemini_step["with"]
        self.assertEqual("false", str(with_cfg["upload_artifacts"]))
        settings = json.loads(str(with_cfg["settings"]))
        self.assertEqual(
            {"context": {"fileName": ["GEMINI.md", "AGENTS.md"]}},
            settings,
        )


if __name__ == "__main__":
    unittest.main()
