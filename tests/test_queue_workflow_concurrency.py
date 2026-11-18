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
        push_step = next(step for step in steps if step.get("name") == "Push publish candidate branch")
        self.assertIn("HEAD:refs/heads/publish", str(push_step["run"]))
        self.assertNotIn("--force", str(push_step["run"]))

    def test_texlive_smoke_does_not_enter_document_record_domain(self) -> None:
        workflow = _workflow("feishu-build-queue.yml")
        group = str(workflow["jobs"]["process-queue"]["concurrency"]["group"])

        self.assertIn("inputs.texlive_smoke_only", group)
        self.assertIn("feishu-texlive-smoke-", group)
        self.assertIn("github.run_id", group)


    def test_retired_legacy_workflows_have_no_schedule_and_require_opt_in_gate(self) -> None:
        retired = (
            "feishu-start-review.yml",
            "feishu-draft-build-queue.yml",
            "feishu-build-queue.yml",
            "feishu-web-publish-queue.yml",
            "backport-reminder.yml",
            "review-branch-sync-check.yml",
            "nightly-render.yml",
            "feishu-schema-parity.yml",
        )
        for filename in retired:
            with self.subTest(workflow=filename):
                workflow = _workflow(filename)
                triggers = workflow.get(True) or workflow.get("on") or {}
                assert isinstance(triggers, dict)
                self.assertNotIn("schedule", triggers)
                jobs = workflow.get("jobs")
                assert isinstance(jobs, dict) and jobs
                for job_id, job in jobs.items():
                    assert isinstance(job, dict)
                    self.assertIn(
                        "vars.LEGACY_TEMPLATE_QUEUE_ENABLED == 'true'",
                        str(job.get("if", "")),
                        f"{filename}:{job_id} missing legacy opt-in gate",
                    )


class ProductMatrixRefreshWorkflowTests(unittest.TestCase):
    """The product-matrix check is its own job in Workspace Data Refresh (operator 2026-11-18), not a revived
    retired workflow: gated to the private mirror's main, on the daily schedule or when chosen by hand."""

    def test_the_check_is_its_own_gated_job_and_the_other_sources_do_not_take_it(self) -> None:
        workflow = _workflow("workspace-data-refresh.yml")
        triggers = workflow.get(True) or workflow.get("on") or {}
        self.assertIn("product_matrix", triggers["workflow_dispatch"]["inputs"]["source"]["options"])
        jobs = workflow["jobs"]
        self.assertIn("inputs.source != 'product_matrix'", jobs["refresh"]["if"])
        job = jobs["product-matrix"]
        for gate in ("github.repository == 'Bingboom/Hello-Docs'", "github.ref == 'refs/heads/main'",
                     "github.event_name == 'schedule'", "inputs.source == 'product_matrix'"):
            self.assertIn(gate, job["if"])
        self.assertNotIn("LEGACY_TEMPLATE_QUEUE_ENABLED", str(workflow))
        runs = [str(step.get("run", "")) for step in job["steps"]]
        check = next(run for run in runs if "tools.product_matrix_base check" in run)
        self.assertIn("--write --refresh", check)
        self.assertTrue(any("tools.product_matrix_base.publish" in run for run in runs))
        self.assertTrue(any("workspace_refresh_notice --kind product_matrix" in run for run in runs))
        # Only the base token it reads; it is never echoed, and nothing merges the PR.
        self.assertEqual(job["env"]["FEISHU_PUBLISHED_DOCS_BASE_TOKEN"], "${{ secrets.FEISHU_PUBLISHED_DOCS_BASE_TOKEN }}")
        self.assertFalse(any("FEISHU_PUBLISHED_DOCS_BASE_TOKEN" in run or "pr merge" in run for run in runs))


if __name__ == "__main__":
    unittest.main()
