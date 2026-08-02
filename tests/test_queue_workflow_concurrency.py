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

    def test_print_publish_has_no_web_deploy_tail(self) -> None:
        workflow = _workflow("feishu-build-queue.yml")
        jobs = workflow["jobs"]
        self.assertNotIn("deploy-vercel", jobs)
        process_steps = jobs["process-queue"]["steps"]
        self.assertFalse(any("vercel deploy" in str(step.get("run", "")) for step in process_steps))
        self.assertFalse(any("publish HTML" in str(step.get("name", "")) for step in process_steps))
        self.assertTrue(any(step.get("name") == "Write OpenClaw run metadata" for step in process_steps))

    def test_web_publish_serializes_the_shared_publish_branch(self) -> None:
        workflow = _workflow("feishu-web-publish-queue.yml")
        group = str(workflow["concurrency"]["group"])

        self.assertEqual("feishu-web-publish-branch", group)
        self.assertFalse(workflow["concurrency"]["cancel-in-progress"])
        steps = workflow["jobs"]["process-web-publish"]["steps"]
        push_step = next(step for step in steps if step.get("name") == "Commit and push publish branch")
        self.assertIn("HEAD:refs/heads/publish", str(push_step["run"]))
        self.assertNotIn("--force", str(push_step["run"]))

    def test_texlive_smoke_does_not_enter_document_record_domain(self) -> None:
        workflow = _workflow("feishu-build-queue.yml")
        group = str(workflow["jobs"]["process-queue"]["concurrency"]["group"])

        self.assertIn("inputs.texlive_smoke_only", group)
        self.assertIn("feishu-texlive-smoke-", group)
        self.assertIn("github.run_id", group)


if __name__ == "__main__":
    unittest.main()
