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
        self.workflow = workflow
        self.job = workflow["jobs"]["review-sync"]
        self.steps = [step for step in self.job["steps"] if isinstance(step, dict)]
        self.steps_by_id = {step["id"]: step for step in self.steps if step.get("id")}
        self.steps_by_name = {step["name"]: step for step in self.steps if step.get("name")}
        self.commands = "\n".join(str(step.get("run", "")) for step in self.steps)

    def test_schedule_and_manual_dispatch_are_present(self) -> None:
        self.assertIn('cron: "30 2 * * *"', self.workflow_text)
        self.assertIn("workflow_dispatch:", self.workflow_text)
        self.assertEqual({"contents": "read", "issues": "write"}, self.workflow["permissions"])

    def test_cron_does_not_collide_with_other_nightly_workflows(self) -> None:
        # PyYAML parses the `on:` key as the boolean True.
        own_cron = self.workflow[True]["schedule"][0]["cron"]
        for path in sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml")):
            if path == WORKFLOW_PATH:
                continue
            triggers = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get(True) or {}
            schedule = triggers.get("schedule") if isinstance(triggers, dict) else None
            for entry in schedule or []:
                self.assertNotEqual(
                    own_cron,
                    entry.get("cron"),
                    f"cron {own_cron} collides with {path.name}",
                )

    def test_fetch_and_strict_sync_command_are_wired(self) -> None:
        self.assertIn("git fetch --prune --no-tags origin", self.commands)
        self.assertIn("git for-each-ref", self.commands)
        self.assertIn("while IFS= read -r review_ref", self.commands)
        self.assertIn("refs/heads/review/*:refs/remotes/origin/review/*", self.commands)
        self.assertIn("tools/check_review_branch_sync.py", self.commands)
        self.assertIn('--base "${review_ref}"', self.commands)
        self.assertIn("--strict", self.commands)
        self.assertIn("review_sync_out.txt", self.commands)

    def test_sync_step_survives_the_checkers_nonzero_drift_exit(self) -> None:
        """GitHub runs `shell: bash` with -eo pipefail; without `set +e` the strict
        checker's drift exit aborts the step before drift=... reaches GITHUB_OUTPUT."""

        sync = self.steps_by_id["sync"]
        self.assertEqual("bash", sync["shell"])
        run = str(sync["run"])
        self.assertIn("set +e", run)
        self.assertLess(
            run.index("set +e"),
            run.index("tools/check_review_branch_sync.py"),
            "set +e must precede the strict checker invocation",
        )
        self.assertIn('echo "drift=${drift}" >> "${GITHUB_OUTPUT}"', run)
        self.assertIn("rc=${PIPESTATUS[0]}", run)

    def test_issue_body_is_bounded_below_the_github_limit(self) -> None:
        digest_run = str(self.steps_by_id["digest"]["run"])
        self.assertIn("cap = 55000", digest_run)
        self.assertIn("review_sync_issue_body.md", digest_run)
        self.assertIn("truncated", digest_run)
        issue_script = str(self.steps_by_id["drift_issue"]["with"]["script"])
        self.assertIn("review_sync_issue_body.md", issue_script)
        self.assertNotIn("review_sync_out.txt", issue_script)

    def test_drift_issue_steps_are_gated_on_the_sync_output(self) -> None:
        self.assertEqual(
            "${{ steps.sync.outputs.drift == 'true' }}",
            self.steps_by_id["drift_issue"]["if"],
        )
        self.assertEqual(
            "${{ steps.sync.outputs.drift == 'false' }}",
            self.steps_by_name["Resolve drift issue"]["if"],
        )
        self.assertEqual(
            "${{ steps.sync.outputs.drift == 'true' && steps.drift_issue.outputs.changed == 'true' }}",
            self.steps_by_name["Fail when the drift set changed"]["if"],
        )

    def test_known_drift_set_stays_quiet_until_the_digest_changes(self) -> None:
        script = str(self.steps_by_id["drift_issue"]["with"]["script"])
        self.assertIn("review-sync-digest", script)
        self.assertIn("core.setOutput('changed', 'false')", script)
        self.assertIn("core.setOutput('changed', 'true')", script)
        self.assertIn("issues.create", script)
        self.assertIn("issues.update", script)

    def test_drift_issue_is_opened_updated_and_closed(self) -> None:
        self.assertIn("[review-sync-drift]", self.workflow_text)
        self.assertIn("actions/github-script@v7", self.workflow_text)
        self.assertIn("issues.createComment", self.workflow_text)
        self.assertIn("state: 'closed'", self.workflow_text)


if __name__ == "__main__":
    unittest.main()
