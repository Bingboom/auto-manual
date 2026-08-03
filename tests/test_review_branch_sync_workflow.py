from __future__ import annotations

from pathlib import Path
import unittest

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "review-branch-sync-check.yml"


class ReviewBranchSyncWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
        workflow = yaml.safe_load(self.workflow_text)
        self.job = workflow["jobs"]["review-sync"]
        self.commands = "\n".join(
            str(step.get("run", ""))
            for step in self.job["steps"]
            if isinstance(step, dict)
        )

    def test_schedule_and_manual_dispatch_are_present(self) -> None:
        self.assertIn('cron: "0 2 * * *"', self.workflow_text)
        self.assertIn("workflow_dispatch:", self.workflow_text)
        self.assertIn("contents: read", self.workflow_text)
        self.assertIn("issues: write", self.workflow_text)

    def test_fetch_and_strict_sync_command_are_wired(self) -> None:
        self.assertIn("git fetch --prune --no-tags origin", self.commands)
        self.assertIn("git for-each-ref", self.commands)
        self.assertIn("while IFS= read -r review_ref", self.commands)
        self.assertIn("refs/heads/review/*:refs/remotes/origin/review/*", self.commands)
        self.assertIn("tools/check_review_branch_sync.py", self.commands)
        self.assertIn('--base "${review_ref}"', self.commands)
        self.assertIn("--strict", self.commands)
        self.assertIn('review_sync_out.txt', self.commands)

    def test_drift_issue_is_opened_updated_and_closed(self) -> None:
        self.assertIn("[review-sync-drift]", self.workflow_text)
        self.assertIn("actions/github-script@v7", self.workflow_text)
        self.assertIn("issues.createComment", self.workflow_text)
        self.assertIn("issues.create", self.workflow_text)
        self.assertIn("state: 'closed'", self.workflow_text)
        self.assertIn("Fail when drift is detected", self.workflow_text)


if __name__ == "__main__":
    unittest.main()
