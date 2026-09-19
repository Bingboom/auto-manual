from __future__ import annotations

from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github/workflows/web-publish-receipt.yml"


class TestWebPublishReceiptWorkflow(unittest.TestCase):
    """REV-07: HTML_link registration happens post-merge, post-deploy-verify."""

    def setUp(self) -> None:
        self.workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
        self.job = self.workflow["jobs"]["receipt"]

    def test_triggers_on_main_publish_pushes_and_manual_retry(self) -> None:
        triggers = self.workflow[True]
        self.assertEqual(["main"], triggers["push"]["branches"])
        self.assertEqual(["docs/publish/**"], triggers["push"]["paths"])
        # Registration failure retries re-run this workflow (scoped by
        # record_ids when needed); they never re-publish the manual.
        self.assertIn("record_ids", triggers["workflow_dispatch"]["inputs"])

    def test_runs_only_on_the_hello_docs_business_plane(self) -> None:
        self.assertIn("Bingboom/Hello-Docs", self.job["if"])
        rendered = "\n".join(str(step) for step in self.job["steps"])
        self.assertIn("Validate execution plane", rendered)

    def test_permissions_are_read_contents_write_issues(self) -> None:
        self.assertEqual("read", self.workflow["permissions"]["contents"])
        self.assertEqual("write", self.workflow["permissions"]["issues"])

    def test_receipt_runs_are_serialized(self) -> None:
        self.assertEqual("web-publish-receipt", self.workflow["concurrency"]["group"])
        self.assertFalse(self.workflow["concurrency"]["cancel-in-progress"])

    def test_registration_verifies_the_merged_tree_before_writing(self) -> None:
        register = next(
            step
            for step in self.job["steps"]
            if step.get("name") == "Verify deployment and register HTML_link"
        )
        run = str(register["run"])
        self.assertIn("tools/write_web_publish_receipt_links.py", run)
        self.assertIn("--publish-root docs/publish", run)
        self.assertIn("AUTO_MANUAL_RTD_BASE_URL", run)
        self.assertIn("--rps", run)
        self.assertIn("--report-json", run)

    def test_only_the_document_link_binding_env_is_granted(self) -> None:
        env = self.job["env"]
        self.assertEqual("bot", env["FEISHU_PHASE2_IDENTITY"])
        self.assertIn("FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID", env)
        # The receipt lane registers links; it must not carry the full
        # phase2 source-table surface of the build workers.
        self.assertNotIn("FEISHU_PHASE2_SPEC_ROWS_SOURCE_TABLE_ID", env)
        self.assertNotIn("FEISHU_TRANSLATION_MEMORY_BASE_TOKEN", env)

    def test_env_preset_is_validated_before_setup(self) -> None:
        names = [str(step.get("name") or "") for step in self.job["steps"]]
        rendered = "\n".join(str(step) for step in self.job["steps"])
        self.assertIn("web-publish-receipt", rendered)
        self.assertIn("validate_required_env.sh", rendered)
        self.assertLess(
            names.index("Validate required secrets"),
            len(names) - 1,
        )

    def test_failure_sentinel_is_the_last_step(self) -> None:
        sentinel = self.job["steps"][-1]
        self.assertTrue(str(sentinel["uses"]).endswith("queue-sentinel-issue"))
        self.assertEqual("always()", sentinel["if"])
        self.assertEqual("queue-failure-web-receipt", sentinel["with"]["label"])


if __name__ == "__main__":
    unittest.main()
