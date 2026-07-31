from __future__ import annotations

import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_ROOT = REPO_ROOT / ".github" / "workflows"


def _workflow(filename: str) -> dict[str, object]:
    return yaml.safe_load((WORKFLOW_ROOT / filename).read_text(encoding="utf-8"))


class QueueWorkflowConcurrencyTests(unittest.TestCase):
    def test_draft_and_publish_share_document_record_concurrency_domain(self) -> None:
        draft = _workflow("feishu-draft-build-queue.yml")
        publish = _workflow("feishu-build-queue.yml")

        draft_group = str(draft["concurrency"]["group"])
        publish_job = publish["jobs"]["process-queue"]
        publish_group = str(publish_job["concurrency"]["group"])

        self.assertIn("feishu-document-queue-", draft_group)
        self.assertIn("feishu-document-queue-", publish_group)
        self.assertIn("inputs.queue_record_id", draft_group)
        self.assertIn("inputs.queue_record_id", publish_group)
        self.assertIn("'batch'", draft_group)
        self.assertIn("'batch'", publish_group)
        self.assertFalse(draft["concurrency"]["cancel-in-progress"])
        self.assertFalse(publish_job["concurrency"]["cancel-in-progress"])

    def test_review_init_uses_its_own_record_id_domain(self) -> None:
        workflow = _workflow("feishu-start-review.yml")
        group = str(workflow["concurrency"]["group"])

        self.assertIn("feishu-review-init-queue-", group)
        self.assertIn("inputs.queue_record_id", group)
        self.assertIn("'batch'", group)
        self.assertFalse(workflow["concurrency"]["cancel-in-progress"])

    def test_publish_deploy_is_a_separate_global_vercel_mutex(self) -> None:
        workflow = _workflow("feishu-build-queue.yml")
        jobs = workflow["jobs"]
        deploy = jobs["deploy-vercel"]

        self.assertEqual("process-queue", deploy["needs"])
        self.assertEqual("${{ always() }}", deploy["if"])
        self.assertEqual("feishu-vercel-production", deploy["concurrency"]["group"])
        self.assertFalse(deploy["concurrency"]["cancel-in-progress"])

        process_steps = jobs["process-queue"]["steps"]
        deploy_steps = deploy["steps"]
        self.assertFalse(any("vercel deploy" in str(step.get("run", "")) for step in process_steps))
        self.assertTrue(any("vercel deploy" in str(step.get("run", "")) for step in deploy_steps))
        self.assertTrue(
            any(step.get("name") == "Upload Vercel publish candidate" for step in process_steps)
        )
        self.assertTrue(
            any(step.get("name") == "Download Vercel publish candidate" for step in deploy_steps)
        )
        self.assertEqual("Vercel deployment failure sentinel", deploy_steps[-1]["name"])
        self.assertEqual("always()", deploy_steps[-1]["if"])
        self.assertEqual("queue-failure-build-deploy", deploy_steps[-1]["with"]["label"])

    def test_texlive_smoke_does_not_enter_document_record_domain(self) -> None:
        workflow = _workflow("feishu-build-queue.yml")
        group = str(workflow["jobs"]["process-queue"]["concurrency"]["group"])

        self.assertIn("inputs.texlive_smoke_only", group)
        self.assertIn("feishu-texlive-smoke-", group)
        self.assertIn("github.run_id", group)


if __name__ == "__main__":
    unittest.main()
