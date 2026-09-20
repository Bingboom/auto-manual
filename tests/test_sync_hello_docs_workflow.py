from __future__ import annotations

from pathlib import Path
import os
import subprocess
from tempfile import TemporaryDirectory
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
        self.assertIn('for content_path in docs/publish docs/knowledge', self.command)
        self.assertIn('${mirror_parent}:${content_path}', self.command)
        self.assertIn('${source_tree}:${content_path}', self.command)
        self.assertIn('--prefix="${content_path}/"', self.command)
        self.assertIn("combined_tree=", self.command)
        self.assertIn('commit-tree "${combined_tree}"', self.command)

    def test_sync_does_not_import_review_branches_into_main(self) -> None:
        self.assertNotIn("docs/_review", self.command)
        self.assertNotIn("review/", self.command)
        self.assertIn('git -C source bundle create "${source_bundle}" HEAD', self.command)

    def test_real_sync_preserves_business_content_and_rejects_source_ownership(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)

            def git(where, *args):
                return subprocess.run(
                    ["git", "-C", str(where), *args], check=True,
                    capture_output=True, text=True,
                ).stdout.strip()

            git(root, "init", "--bare", "remote.git")
            for name in ("source", "mirror"):
                git(root, "init", "-b", "main", name)
                tree = root / name
                git(tree, "config", "user.name", "Test")
                git(tree, "config", "user.email", "test@example.invalid")
                (tree / "engine.txt").write_text(name)
                if name == "mirror":
                    for folder in ("publish", "knowledge"):
                        path = tree / "docs" / folder / "content.txt"
                        path.parent.mkdir(parents=True)
                        path.write_text(folder)
                git(tree, "add", ".")
                git(tree, "commit", "-m", "Initial fixture")
            mirror = root / "mirror"
            source = root / "source"
            git(mirror, "remote", "add", "origin", str(root / "remote.git"))
            git(mirror, "push", "origin", "main")
            env = dict(os.environ, SOURCE_REPOSITORY="local/source",
                       SOURCE_SHA=git(source, "rev-parse", "HEAD"),
                       SOURCE_RUN_URL="local-test", MIRROR_BRANCH="main")

            def sync():
                return subprocess.run(
                    ["bash", "-e", "-o", "pipefail", "-c", self.command],
                    cwd=root, env=env, capture_output=True, text=True,
                )

            result = sync()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(git(mirror, "show", "HEAD:engine.txt"), "source")
            for folder in ("publish", "knowledge"):
                self.assertEqual(git(mirror, "show", f"HEAD:docs/{folder}/content.txt"), folder)
            preserved_head = git(mirror, "rev-parse", "HEAD")
            result = sync()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(git(mirror, "rev-parse", "HEAD"), preserved_head)

            wrong = source / "docs" / "knowledge" / "wrong.txt"
            wrong.parent.mkdir(parents=True)
            wrong.write_text("must not overwrite business content")
            git(source, "add", ".")
            git(source, "commit", "-m", "Forbidden content ownership")
            result = sync()
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("auto-manual must not own docs/knowledge", result.stdout)
            self.assertEqual(git(mirror, "rev-parse", "HEAD"), preserved_head)


if __name__ == "__main__":
    unittest.main()
