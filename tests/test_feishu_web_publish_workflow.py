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

    def test_web_worker_has_write_permission_and_web_only_queue_filter(self) -> None:
        self.assertEqual("write", self.workflow["permissions"]["contents"])
        process = self._step("Process Feishu Web Publish queue")
        command = str(process["run"])
        self.assertIn("--workflow-action web-publish", command)
        self.assertNotIn("xelatex", WORKFLOW_PATH.read_text(encoding="utf-8"))
        self.assertNotIn("vercel", WORKFLOW_PATH.read_text(encoding="utf-8").casefold())

    def test_publish_branch_is_incremental_and_never_force_pushed(self) -> None:
        prepare = str(self._step("Prepare publish branch worktree")["run"])
        assemble = str(self._step("Assemble frozen Web source under docs/publish")["run"])
        push = str(self._step("Commit and push publish branch")["run"])

        self.assertIn("refs/remotes/origin/publish", prepare)
        self.assertIn("docs/publish", prepare)
        self.assertIn("tools/publish_branch_assembly.py", assemble)
        self.assertIn("--output-dir", assemble)
        self.assertIn("HEAD:refs/heads/publish", push)
        self.assertNotIn("--force", push)

    def test_rtd_link_writeback_happens_after_the_branch_push(self) -> None:
        names = [str(step.get("name") or "") for step in self.steps]
        push_index = names.index("Commit and push publish branch")
        writeback_index = names.index("Write RTD HTML_link back to Document_link")
        self.assertLess(push_index, writeback_index)
        writeback = str(self.steps[writeback_index]["run"])
        self.assertIn("tools/write_web_publish_html_link.py", writeback)
        self.assertIn("AUTO_MANUAL_RTD_BASE_URL", writeback)

    def test_failure_sentinel_is_the_last_step(self) -> None:
        sentinel = self.steps[-1]
        self.assertEqual("Web Publish failure sentinel", sentinel["name"])
        self.assertEqual("always()", sentinel["if"])
        self.assertEqual("queue-failure-web-publish", sentinel["with"]["label"])


if __name__ == "__main__":
    unittest.main()
