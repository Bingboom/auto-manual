from __future__ import annotations

from pathlib import Path
import unittest

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "feishu-web-publish-queue.yml"


class FeishuWebPublishWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
        self.job = self.workflow["jobs"]["process-web-publish"]
        self.steps = self.job["steps"]

    def _step(self, name: str) -> dict[str, object]:
        return next(step for step in self.steps if step.get("name") == name)

    def test_web_worker_has_write_permissions_and_web_only_queue_filter(self) -> None:
        self.assertEqual("write", self.workflow["permissions"]["contents"])
        self.assertEqual("write", self.workflow["permissions"]["pull-requests"])
        process = self._step("Process Feishu Web Publish queue")
        command = str(process["run"])
        self.assertIn("--workflow-action web-publish", command)
        self.assertNotIn("xelatex", WORKFLOW_PATH.read_text(encoding="utf-8"))
        self.assertNotIn("vercel", WORKFLOW_PATH.read_text(encoding="utf-8").casefold())

    def test_publish_branch_is_incremental_and_reconciled_with_main(self) -> None:
        prepare = str(self._step("Prepare publish branch worktree")["run"])
        assemble = str(self._step("Assemble frozen Web source under docs/publish")["run"])
        push = str(self._step("Push publish candidate branch")["run"])

        self.assertIn("refs/remotes/origin/publish", prepare)
        self.assertIn("refs/remotes/origin/${PUBLISH_BASE_BRANCH}", prepare)
        self.assertIn("merge-base --is-ancestor", prepare)
        self.assertIn("merge --no-edit --no-ff -s ours", prepare)
        self.assertIn("read-tree --reset -u", prepare)
        self.assertIn("docs/publish", prepare)
        self.assertIn("tools/publish_branch_assembly.py", assemble)
        self.assertIn("--output-dir", assemble)
        self.assertIn("HEAD:refs/heads/publish", push)
        self.assertNotIn("--force", push)

    def test_publish_pr_scope_is_checked_before_push(self) -> None:
        names = [str(step.get("name") or "") for step in self.steps]
        scope_index = names.index("Validate publish PR scope")
        push_index = names.index("Push publish candidate branch")
        self.assertLess(scope_index, push_index)

        scope = str(self.steps[scope_index]["run"])
        self.assertIn("merge-base --is-ancestor", scope)
        self.assertIn("docs/publish/*", scope)
        self.assertIn("publish PR may change only docs/publish/**", scope)
        self.assertIn("diff --name-only --no-renames -z", scope)

    def test_publish_pr_targets_main_and_precedes_link_writeback(self) -> None:
        names = [str(step.get("name") or "") for step in self.steps]
        push_index = names.index("Push publish candidate branch")
        pr_index = names.index("Open or update publish PR")
        writeback_index = names.index("Write RTD HTML_link back to Document_link")
        self.assertLess(push_index, writeback_index)
        self.assertLess(push_index, pr_index)
        self.assertLess(pr_index, writeback_index)

        pr_step = self.steps[pr_index]
        self.assertEqual("${{ steps.publish-scope.outputs.has_changes == 'true' }}", pr_step["if"])
        pr_command = str(pr_step["run"])
        self.assertIn('--base "${PUBLISH_BASE_BRANCH}"', pr_command)
        self.assertIn("--head publish", pr_command)
        self.assertIn("review/*", pr_command)

        writeback = str(self.steps[writeback_index]["run"])
        self.assertIn("tools/write_web_publish_html_link.py", writeback)
        self.assertIn("AUTO_MANUAL_RTD_BASE_URL", writeback)
        rtd_base_url = str(self.job["env"]["AUTO_MANUAL_RTD_BASE_URL"])
        self.assertIn("https://ht-doc.readthedocs.io", rtd_base_url)
        self.assertNotIn("/en/latest", rtd_base_url)

    def test_failure_sentinel_is_the_last_step(self) -> None:
        sentinel = self.steps[-1]
        self.assertEqual("Web Publish failure sentinel", sentinel["name"])
        self.assertEqual("always()", sentinel["if"])
        self.assertEqual("queue-failure-web-publish", sentinel["with"]["label"])


if __name__ == "__main__":
    unittest.main()
