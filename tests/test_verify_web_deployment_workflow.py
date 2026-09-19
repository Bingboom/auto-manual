from __future__ import annotations

from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github/workflows/verify-web-deployment.yml"

# The six pre-existing daily crons this schedule must stay offset from.
EXISTING_DAILY_CRONS = {
    "30 0 * * *",  # phase2-content-backup
    "0 1 * * *",  # feishu-schema-parity
    "0 2 * * *",  # backport-reminder
    "30 2 * * *",  # review-branch-sync-check
    "0 7 * * *",  # cred-health-check
    "45 8 * * *",  # nightly-render
}


class TestVerifyWebDeploymentWorkflow(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
        self.job = self.workflow["jobs"]["verify"]

    def test_daily_cron_is_offset_and_dispatchable(self) -> None:
        triggers = self.workflow[True]
        crons = [entry["cron"] for entry in triggers["schedule"]]
        self.assertEqual(1, len(crons))
        self.assertNotIn(crons[0], EXISTING_DAILY_CRONS)
        self.assertRegex(crons[0], r"^\d{1,2} \d{1,2} \* \* \*$")
        self.assertIn("workflow_dispatch", triggers)

    def test_runs_only_on_the_hello_docs_business_plane(self) -> None:
        # docs/publish lives only on Hello-Docs main (sync-hello-docs.yml
        # refuses it in auto-manual), so the checkout-based full verification
        # must run there — same plane split as phase2-content-backup.
        self.assertIn("Bingboom/Hello-Docs", self.job["if"])

    def test_permissions_are_read_contents_write_issues(self) -> None:
        self.assertEqual("read", self.workflow["permissions"]["contents"])
        self.assertEqual("write", self.workflow["permissions"]["issues"])

    def test_verifier_runs_against_the_frozen_publish_root(self) -> None:
        rendered = "\n".join(str(step) for step in self.job["steps"])
        self.assertIn("tools/verify_web_deployment_targets.py", rendered)
        self.assertIn("--publish-root docs/publish", rendered)
        self.assertIn("AUTO_MANUAL_RTD_BASE_URL", rendered)

    def test_failure_sentinel_reuses_the_shared_helper_and_skips_smoke_runs(self) -> None:
        sentinel = next(
            step
            for step in self.job["steps"]
            if str(step.get("uses", "")).endswith("queue-sentinel-issue")
        )
        self.assertEqual("${{ job.status }}", sentinel["with"]["job-status"])
        self.assertIn("limit", sentinel["if"])

    # --- rate-limit wiring (Hello-Docs run 35432328072 regression) ---

    def verify_step(self) -> dict:
        return next(step for step in self.job["steps"] if step.get("id") == "verify")

    def test_the_run_is_paced_and_emits_a_machine_readable_report(self) -> None:
        run = self.verify_step()["run"]
        self.assertIn("--rps", run)
        self.assertIn("AUTO_MANUAL_RTD_VERIFY_RPS", run)
        self.assertIn("--report-json", run)
        # A dispatch override and a repo var both feed the pace, with a default.
        rate = self.job["env"]["AUTO_MANUAL_RTD_VERIFY_RPS"]
        self.assertIn("inputs.rps", rate)
        self.assertIn("vars.AUTO_MANUAL_RTD_VERIFY_RPS", rate)
        self.assertIn("rps", self.workflow[True]["workflow_dispatch"]["inputs"])

    def test_the_nightly_sweep_runs_at_the_bounded_markup_scope(self) -> None:
        self.assertIn("--asset-scope", self.verify_step()["run"])
        self.assertEqual("markup", self.job["env"]["AUTO_MANUAL_RTD_VERIFY_SCOPE"].split("'")[-2])
        scope_input = self.workflow[True]["workflow_dispatch"]["inputs"]["asset-scope"]
        self.assertEqual(["markup", "full"], scope_input["options"])
        self.assertEqual("markup", scope_input["default"])

    def test_the_verifier_exit_status_still_fails_the_job(self) -> None:
        # Classification must not swallow the exit code: fail-closed survives.
        run = self.verify_step()["run"]
        self.assertIn("PIPESTATUS[0]", run)
        self.assertIn('exit "${verify_status}"', run)

    def test_sentinel_separates_undecided_throttling_from_a_real_mismatch(self) -> None:
        sentinel = next(
            step
            for step in self.job["steps"]
            if str(step.get("uses", "")).endswith("queue-sentinel-issue")
        )
        details = sentinel["with"]["details"]
        self.assertIn("steps.verify.outputs.classification", details)
        self.assertIn("steps.verify.outputs.counts", details)
        self.assertIn("steps.verify.outputs.report_status", details)
        self.assertIn("UNDECIDED", details)
        self.assertIn("retry signal", details)


if __name__ == "__main__":
    unittest.main()
