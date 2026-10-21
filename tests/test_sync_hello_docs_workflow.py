from __future__ import annotations

from pathlib import Path
import os
import subprocess
from tempfile import TemporaryDirectory
import unittest

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "sync-hello-docs.yml"
SCRIPT_PATH = REPO_ROOT / "scripts" / "sync_mirror.sh"
ALL_CONTENT = "docs/publish docs/knowledge docs/review-drafts"


def sync_step(workflow: dict, job: str, name: str) -> dict:
    return next(step for step in workflow["jobs"][job]["steps"] if step.get("name") == name)


class SyncHelloDocsWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
        self.sync_step = sync_step(self.workflow, "sync", "Commit and push mirror update")
        self.review_step = sync_step(self.workflow, "sync-review", "Commit and push review mirror update")
        self.command = SCRIPT_PATH.read_text(encoding="utf-8")

    def test_sync_preserves_the_main_publish_subtree(self) -> None:
        self.assertEqual(self.sync_step["run"], "bash source/scripts/sync_mirror.sh")
        self.assertEqual(self.sync_step["env"]["MIRROR_KEEP_PATHS"], "docs/publish docs/knowledge")
        self.assertIn('for content_path in ${keep_paths}', self.command)
        self.assertIn('${mirror_parent}:${content_path}', self.command)
        self.assertIn('${source_tree}:${content_path}', self.command)
        self.assertIn('--prefix="${content_path}/"', self.command)
        self.assertIn("combined_tree=", self.command)
        self.assertIn('commit-tree "${combined_tree}"', self.command)

    def test_every_mirror_refuses_all_mirror_owned_content_in_the_source(self) -> None:
        # The public Hello-Docs mirror must also refuse review drafts, or a slip would publish them.
        for step in (self.sync_step, self.review_step):
            self.assertEqual(step["env"]["SOURCE_FORBIDDEN_PATHS"], ALL_CONTENT)
        self.assertEqual(self.review_step["env"]["MIRROR_KEEP_PATHS"], "docs/review-drafts")
        self.assertEqual(self.review_step["run"], "bash source/scripts/sync_mirror.sh")

    def test_review_mirror_skips_without_its_token(self) -> None:
        job = self.workflow["jobs"]["sync-review"]
        self.assertEqual(job["env"]["MIRROR_REPOSITORY"], "Bingboom/Hello-Docs-Review")
        check = job["steps"][0]
        self.assertIn("secrets.REVIEW_DOCS_SYNC_TOKEN", check["env"]["REVIEW_DOCS_SYNC_TOKEN"])
        self.assertIn("::notice::", check["run"])
        self.assertNotIn("exit 1", check["run"])
        for step in job["steps"][1:]:
            self.assertEqual(step["if"], "${{ steps.token.outputs.ready == 'true' }}")

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
                       SOURCE_RUN_URL="local-test", MIRROR_BRANCH="main",
                       MIRROR_KEEP_PATHS="docs/publish docs/knowledge",
                       SOURCE_FORBIDDEN_PATHS=ALL_CONTENT)

            def sync():
                return subprocess.run(
                    ["bash", str(SCRIPT_PATH)],
                    cwd=root, env=env, capture_output=True, text=True,
                    check=False,
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

    def test_real_review_sync_keeps_drafts_and_refuses_drafts_in_the_source(self) -> None:
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
                    draft = tree / "docs" / "review-drafts" / "M" / "JP" / "v0.1" / "draft.html"
                    draft.parent.mkdir(parents=True)
                    draft.write_text("draft")
                git(tree, "add", ".")
                git(tree, "commit", "-m", "Initial fixture")
            mirror, source = root / "mirror", root / "source"
            git(mirror, "remote", "add", "origin", str(root / "remote.git"))
            git(mirror, "push", "origin", "main")
            env = dict(os.environ, SOURCE_REPOSITORY="local/source",
                       SOURCE_SHA=git(source, "rev-parse", "HEAD"), SOURCE_RUN_URL="local-test",
                       MIRROR_BRANCH="main", MIRROR_KEEP_PATHS="docs/review-drafts",
                       SOURCE_FORBIDDEN_PATHS=ALL_CONTENT)

            def sync():
                return subprocess.run(["bash", str(SCRIPT_PATH)], cwd=root, env=env,
                                      capture_output=True, text=True, check=False)

            result = sync()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(git(mirror, "show", "HEAD:engine.txt"), "source")
            self.assertEqual(git(mirror, "show", "HEAD:docs/review-drafts/M/JP/v0.1/draft.html"), "draft")
            synced = git(mirror, "rev-parse", "HEAD")
            leak = source / "docs" / "review-drafts" / "leak.html"
            leak.parent.mkdir(parents=True)
            leak.write_text("must never be in the public source")
            git(source, "add", ".")
            git(source, "commit", "-m", "Forbidden review draft")
            result = sync()
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("auto-manual must not own docs/review-drafts", result.stdout)
            self.assertEqual(git(mirror, "rev-parse", "HEAD"), synced)


if __name__ == "__main__":
    unittest.main()
