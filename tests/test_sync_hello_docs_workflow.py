from __future__ import annotations

from pathlib import Path
import unittest

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "sync-hello-docs.yml"


class SyncHelloDocsWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
        steps = workflow["jobs"]["sync"]["steps"]
        self.sync_step = next(step for step in steps if step.get("name") == "Commit and push mirror update")
        self.command = str(self.sync_step["run"])

    def test_sync_preserves_the_main_publish_subtree(self) -> None:
        self.assertIn('${mirror_parent}:docs/publish', self.command)
        self.assertIn("publish_tree=", self.command)
        self.assertIn('${source_tree}:docs/publish', self.command)
        self.assertIn("auto-manual must not own docs/publish", self.command)
        self.assertIn("--prefix=docs/publish/", self.command)
        self.assertIn("combined_tree=", self.command)
        self.assertIn('commit-tree "${combined_tree}"', self.command)

    def test_sync_does_not_import_review_branches_into_main(self) -> None:
        self.assertNotIn("docs/_review", self.command)
        self.assertNotIn("review/", self.command)
        self.assertIn('git -C source bundle create "${source_bundle}" HEAD', self.command)


if __name__ == "__main__":
    unittest.main()
