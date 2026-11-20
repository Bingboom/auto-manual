from __future__ import annotations

from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

import yaml

from tests.test_helpers import step_uses_action


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "sync-hello-docs.yml"
SCRIPT_PATH = REPO_ROOT / "scripts" / "sync_mirror.sh"
ALL_CONTENT = "docs/publish docs/knowledge docs/review-drafts"
HELLO_DOCS_KEEP = "docs/publish docs/knowledge"
REVIEW_KEEP = "docs/review-drafts"
HELLO_DOCS_OVERLAY = (
    "manual_sources data/manual_sources reports configs/targets bitable_schema/business"
)


def sync_environ(github_ref: str | None = None) -> dict:
    """os.environ without CI's GITHUB_REF (refs/pull/... on pull requests), optionally set to one."""
    env = {key: value for key, value in os.environ.items() if key != "GITHUB_REF"}
    if github_ref is not None:
        env["GITHUB_REF"] = github_ref
    return env


def sync_step(workflow: dict, job: str, name: str) -> dict:
    step = next(step for step in workflow["jobs"][job]["steps"] if step.get("name") == name)
    # Effective environment: workflow env, then job env, then step env.
    merged = {**workflow.get("env", {}), **workflow["jobs"][job].get("env", {}), **step.get("env", {})}
    return {**step, "env": merged}


class SyncHelloDocsWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
        self.sync_step = sync_step(self.workflow, "sync", "Commit and push mirror update")
        self.review_step = sync_step(self.workflow, "sync-review", "Commit and push review mirror update")
        self.command = SCRIPT_PATH.read_text(encoding="utf-8")

    def test_sync_preserves_the_main_publish_subtree(self) -> None:
        self.assertEqual(self.sync_step["run"], "bash source/scripts/sync_mirror.sh")
        self.assertEqual(self.sync_step["env"]["MIRROR_KEEP_PATHS"], HELLO_DOCS_KEEP)
        self.assertIn('for content_path in ${keep_paths}', self.command)
        self.assertIn('${mirror_parent}:${content_path}', self.command)
        self.assertIn('rm -r -f --cached --quiet --ignore-unmatch -- ":(literal)${content_path}"', self.command)
        self.assertIn('${source_tree}:${content_path}', self.command)
        self.assertIn('--prefix="${content_path}/"', self.command)
        self.assertIn("combined_tree=", self.command)
        self.assertIn('commit-tree "${combined_tree}"', self.command)

    def test_every_mirror_refuses_all_mirror_owned_content_in_the_source(self) -> None:
        # The public Hello-Docs mirror must also refuse review drafts, or a slip would publish them.
        # One copy of the forbidden list, at workflow level; no job or step overrides it.
        self.assertEqual(self.workflow["env"]["SOURCE_FORBIDDEN_PATHS"], ALL_CONTENT)
        for name, job in self.workflow["jobs"].items():
            self.assertNotIn("SOURCE_FORBIDDEN_PATHS", job.get("env", {}), name)
            for step in job["steps"]:
                self.assertNotIn("SOURCE_FORBIDDEN_PATHS", step.get("env", {}), (name, step.get("name")))
        for step in (self.sync_step, self.review_step):
            self.assertEqual(step["env"]["SOURCE_FORBIDDEN_PATHS"], ALL_CONTENT)
        self.assertEqual(self.review_step["env"]["MIRROR_KEEP_PATHS"], REVIEW_KEEP)
        self.assertEqual(self.review_step["run"], "bash source/scripts/sync_mirror.sh")

    def test_keep_and_overlay_lists_relate_as_documented(self) -> None:
        def overlaps(a: str, b: str) -> bool:
            return a == b or a.startswith(b + "/") or b.startswith(a + "/")

        self.assertEqual(self.sync_step["env"]["MIRROR_OVERLAY_PATHS"], HELLO_DOCS_OVERLAY)
        self.assertEqual(self.sync_step["env"]["MIRROR_OVERLAY_PRUNE_EXTERNALIZED"], "1")
        # Hello-Docs-Review has no overlay: it does not read the frozen packages, so upstream
        # deletions must keep reaching it.
        self.assertNotIn("MIRROR_OVERLAY_PATHS", self.review_step["env"])
        self.assertNotIn("MIRROR_OVERLAY_PRUNE_EXTERNALIZED", self.review_step["env"])
        for step in (self.sync_step, self.review_step):
            env = step["env"]
            keep = env["MIRROR_KEEP_PATHS"].split()
            overlay = env.get("MIRROR_OVERLAY_PATHS", "").split()
            forbidden = env["SOURCE_FORBIDDEN_PATHS"].split()
            # Every strict keep path is forbidden upstream, so none is "first write wins".
            for path in keep:
                self.assertIn(path, forbidden)
            for path in overlay:
                for other in keep + forbidden:
                    self.assertFalse(overlaps(path, other), (path, other))
            for path in keep + overlay + forbidden:
                self.assertNotEqual(path, "review_sync_json")
                self.assertFalse(overlaps(path, "site"), path)

    def test_push_credentials_exist_only_on_main(self) -> None:
        # Second guard, independent of MIRROR_DRY_RUN: off main the mirror token is used to read
        # the mirror but is not persisted into mirror/.git/config, so `git push origin` has no
        # credential. The sync step itself never receives a token.
        guard = "${{ github.ref == 'refs/heads/main' }}"
        for job_name in ("sync", "sync-review"):
            checkouts = [step for step in self.workflow["jobs"][job_name]["steps"]
                         if step_uses_action(step, "actions/checkout") and step["with"].get("path") == "mirror"]
            self.assertEqual(len(checkouts), 1, job_name)
            self.assertIn("secrets.", checkouts[0]["with"]["token"])
            self.assertEqual(checkouts[0]["with"]["persist-credentials"], guard)
            for ref, expected in (("refs/heads/main", True), ("refs/heads/docs/x", False)):
                self.assertIs(self._evaluate(guard, ref=ref, event="workflow_dispatch", dry_run=False), expected)
            sync = next(step for step in self.workflow["jobs"][job_name]["steps"]
                        if step.get("run") == "bash source/scripts/sync_mirror.sh")
            self.assertNotIn("secrets.", str(sync.get("env", {})))
        self.assertIn('git -C mirror push origin "${mirror_commit}:${MIRROR_BRANCH}"', self.command)

    def test_pr_guardrail_refuses_the_same_paths_as_the_mirrors(self) -> None:
        # The guardrail fails the PR; the syncs only refuse after the merge.
        from tools.check_maintainability_guardrails import MIRROR_OWNED_PATHS

        self.assertEqual(" ".join(MIRROR_OWNED_PATHS), ALL_CONTENT)

    def test_review_mirror_skips_without_its_token(self) -> None:
        job = self.workflow["jobs"]["sync-review"]
        self.assertEqual(job["env"]["MIRROR_REPOSITORY"], "Bingboom/Hello-Docs-Review")
        self.assertIn("dry_run", self.workflow[True]["workflow_dispatch"]["inputs"])
        check = job["steps"][0]
        self.assertIn("secrets.REVIEW_DOCS_SYNC_TOKEN", check["env"]["REVIEW_DOCS_SYNC_TOKEN"])
        self.assertIn("::notice::", check["run"])
        self.assertNotIn("exit 1", check["run"])
        for step in job["steps"][1:]:
            self.assertEqual(step["if"], "${{ steps.token.outputs.ready == 'true' }}")

    def test_sync_does_not_import_review_branches_into_main(self) -> None:
        self.assertNotIn("docs/_review", self.command)
        self.assertNotIn("review/", self.command)
        self.assertIn('git -C source bundle create "${source_bundle}" refs/sync/snapshot', self.command)
        for job_name in ("sync", "sync-review"):
            checkouts = [
                step for step in self.workflow["jobs"][job_name]["steps"]
                if step_uses_action(step, "actions/checkout")
            ]
            self.assertEqual(len(checkouts), 2, job_name)
            for checkout in checkouts:
                self.assertEqual(checkout["with"]["fetch-depth"], 1, job_name)
                self.assertNotIn("filter", checkout["with"], job_name)

    def test_each_mirror_installs_its_own_readme_from_the_source(self) -> None:
        for step, repository in ((self.sync_step, "Hello-Docs"), (self.review_step, "Hello-Docs-Review")):
            readme = step["env"]["MIRROR_README"]
            self.assertEqual(readme, f"mirrors/{repository}/README.md")
            self.assertTrue((REPO_ROOT / readme).is_file(), readme)
        self.assertIn('${source_tree}:${MIRROR_README}', self.command)
        self.assertIn('--cacheinfo "100644,${readme_blob},README.md"', self.command)

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
                # Keep Git maintenance in the fixture process: an auto-GC child
                # can otherwise recreate .git entries during TemporaryDirectory cleanup.
                git(tree, "config", "gc.autoDetach", "false")
                git(tree, "config", "maintenance.autoDetach", "false")
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
            env = dict(sync_environ(), SOURCE_REPOSITORY="local/source",
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

    # ---- Dry-run gating (YAML only; no Actions run is possible in tests) -------------------

    @staticmethod
    def _evaluate(expression: str, *, ref: str, event: str, dry_run, env: dict | None = None,
                  cancelled: bool = False):
        """Evaluate the small subset of GitHub expression syntax this workflow uses."""
        import re
        body = expression.strip()
        if body.startswith("${{"):
            body = body[3:-2].strip()
        names = {"github.ref": ref, "github.event_name": event, "github.repository": "Bingboom/auto-manual",
                 "inputs.dry_run": dry_run}
        for key, value in (env or {}).items():
            names[f"env.{key}"] = value
        body = re.sub(r"format\('([^']*)', ([\w.]+)\)",
                      lambda m: repr(m.group(1).replace("{0}", str(names[m.group(2)]))), body)
        body = body.replace("!cancelled()", repr(not cancelled))
        for name in sorted(names, key=len, reverse=True):
            body = body.replace(name, f"__n[{name!r}]")
        body = body.replace("!=", " __NE__ ").replace("&&", " and ").replace("||", " or ")
        body = body.replace("__NE__", "!=")
        assert "!" not in body.replace("!=", ""), body
        return eval(body, {"__builtins__": {}}, {"__n": names})  # noqa: S307 - fixed test input

    def _gate(self, ref: str, event: str, dry_run):
        workflow = self.workflow
        dry = self._evaluate(workflow["env"]["MIRROR_DRY_RUN"], ref=ref, event=event, dry_run=dry_run)
        group = self._evaluate(workflow["concurrency"]["group"], ref=ref, event=event, dry_run=dry_run)
        jobs = {name: bool(self._evaluate(job["if"], ref=ref, event=event, dry_run=dry_run))
                for name, job in workflow["jobs"].items()}
        notice = sync_step(workflow, "sync", "Workspace mirror failure notice")
        notice_runs = bool(self._evaluate(notice["if"], ref=ref, event=event, dry_run=dry_run,
                                          env={"MIRROR_DRY_RUN": dry}))
        return dry, group, jobs, notice_runs

    def test_push_on_main_behaves_as_before(self) -> None:
        self.assertEqual(self.workflow[True]["push"]["branches"], ["main"])
        dry, group, jobs, notice = self._gate("refs/heads/main", "push", None)
        self.assertEqual(dry, "0")
        self.assertEqual(group, "sync-hello-docs-main")
        self.assertEqual(jobs, {"sync": True, "sync-review": True})
        self.assertTrue(notice)

    def test_manual_run_on_main_pushes_only_without_the_dry_run_input(self) -> None:
        self.assertEqual(self._gate("refs/heads/main", "workflow_dispatch", False)[0], "0")
        dry, group, jobs, notice = self._gate("refs/heads/main", "workflow_dispatch", True)
        self.assertEqual(dry, "1")
        self.assertEqual(group, "sync-hello-docs-dry-run-refs/heads/main")
        self.assertEqual(jobs, {"sync": True, "sync-review": True})
        self.assertFalse(notice)

    def test_manual_run_off_main_is_always_a_dry_run(self) -> None:
        for dry_run in (False, True, None):
            dry, group, jobs, notice = self._gate("refs/heads/docs/x", "workflow_dispatch", dry_run)
            self.assertEqual(dry, "1", dry_run)
            self.assertEqual(group, "sync-hello-docs-dry-run-refs/heads/docs/x")
            self.assertEqual(jobs, {"sync": True, "sync-review": True})
            self.assertFalse(notice)
        # Pushes to other branches never trigger the workflow; if they did, the jobs would not run.
        self.assertEqual(self._gate("refs/heads/docs/x", "push", None)[2], {"sync": False, "sync-review": False})

    def test_every_side_effect_step_is_skipped_in_a_dry_run(self) -> None:
        for job_name, job in self.workflow["jobs"].items():
            for step in job["steps"]:
                text = str(step.get("uses", "")) + str(step.get("run", "")) + str(step.get("with", ""))
                if "github-script" in text or "gh " in text or "issues." in text:
                    self.assertIn("env.MIRROR_DRY_RUN != '1'", step.get("if", ""), (job_name, step.get("name")))
            sync_steps = [s for s in job["steps"] if s.get("run") == "bash source/scripts/sync_mirror.sh"]
            self.assertEqual(len(sync_steps), 1, job_name)
            self.assertNotIn("MIRROR_DRY_RUN", sync_steps[0].get("env", {}), "a step env must not override the gate")
            self.assertNotIn("MIRROR_DRY_RUN", job.get("env", {}))

    # ---- Overlay (transitional) and strict keep semantics -------------------------------

    @staticmethod
    def _git(where, *args):
        return subprocess.run(["git", "-C", str(where), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def _write(self, repo: Path, files: dict, message: str) -> None:
        for path, content in files.items():
            target = repo / path
            if content is None:
                self._git(repo, "rm", "-r", "-q", "--", path)
                continue
            if target.is_dir():
                self._git(repo, "rm", "-r", "-q", "--", path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            self._git(repo, "add", "--", path)
        self._git(repo, "commit", "-q", "--allow-empty", "-m", message)

    def _fixture(self, root: Path, source_files: dict, mirror_files: dict) -> None:
        self._git(root, "init", "--bare", "-q", "-b", "main", "remote.git")
        for name, files in (("source", source_files), ("mirror", mirror_files)):
            self._git(root, "init", "-q", "-b", "main", name)
            repo = root / name
            self._git(repo, "config", "user.name", "Test")
            self._git(repo, "config", "user.email", "test@example.invalid")
            self._write(repo, {"engine.txt": f"{name}-v1", **files}, "Initial fixture")
        self._git(root / "mirror", "remote", "add", "origin", str(root / "remote.git"))
        self._git(root / "mirror", "push", "-q", "origin", "main")

    def _sync(self, root: Path, **extra):
        env = dict(sync_environ(), SOURCE_REPOSITORY="local/source",
                   SOURCE_SHA=self._git(root / "source", "rev-parse", "HEAD"),
                   SOURCE_RUN_URL="local-test", MIRROR_BRANCH="main",
                   MIRROR_KEEP_PATHS="docs/publish", MIRROR_OVERLAY_PATHS="manual_sources reports",
                   SOURCE_FORBIDDEN_PATHS=ALL_CONTENT)
        env.update(extra)
        return subprocess.run(["bash", str(SCRIPT_PATH)], cwd=root, env=env,
                              capture_output=True, text=True, check=False)

    def _remote(self, root: Path, path: str) -> str:
        return self._git(root / "remote.git", "show", f"main:{path}")

    def _remote_files(self, root: Path, prefix: str) -> set:
        out = self._git(root / "remote.git", "-c", "core.quotePath=false", "ls-tree", "-r",
                        "--name-only", "main", "--", prefix)
        return set(out.splitlines())

    def test_overlay_adds_updates_and_keeps_mirror_only_and_upstream_removed_files(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            shared = {"manual_sources/A/spec.json": "a1", "manual_sources/B/spec.json": "b1",
                      "reports/r.txt": "r1"}
            self._fixture(root, shared, {**shared, "manual_sources/M/only.json": "mirror-only",
                                         "manual_sources/中文/说明.txt": "unicode mirror-only",
                                         "docs/publish/p.txt": "published"})
            result = self._sync(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(self._remote(root, "engine.txt"), "source-v1")
            self.assertEqual(self._remote(root, "manual_sources/M/only.json"), "mirror-only")  # (4)
            self.assertEqual(self._remote(root, "manual_sources/中文/说明.txt"), "unicode mirror-only")
            self.assertIn("overlay manual_sources: mirror_only_kept=2 source_updated=0", result.stdout)
            self.assertIn("::notice::Overlay path manual_sources keeps 2 file(s) that exist only in the mirror",
                          result.stdout)
            self.assertNotIn("::notice::Overlay path reports", result.stdout)

            self._write(root / "source", {"manual_sources/C/new.json": "c1",       # (1) new file
                                          "manual_sources/A/spec.json": "a2",      # (2) edit
                                          "manual_sources/B": None,               # (3) removal
                                          "engine.txt": "source-v2"}, "Stage 2 step")
            result = self._sync(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(self._remote(root, "manual_sources/C/new.json"), "c1")
            self.assertEqual(self._remote(root, "manual_sources/A/spec.json"), "a2")
            self.assertEqual(self._remote(root, "manual_sources/B/spec.json"), "b1")
            self.assertEqual(self._remote(root, "manual_sources/M/only.json"), "mirror-only")
            self.assertEqual(self._remote(root, "docs/publish/p.txt"), "published")
            self.assertIn("overlay manual_sources: mirror_only_kept=3 source_updated=1", result.stdout)
            head = self._git(root / "remote.git", "rev-parse", "main")
            result = self._sync(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Mirror code already matches", result.stdout)
            self.assertEqual(self._git(root / "remote.git", "rev-parse", "main"), head)

    def test_overlay_path_absent_from_mirror_passes_through_then_is_kept(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root, {"manual_sources/A/spec.json": "a1"}, {})
            result = self._sync(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("overlay manual_sources: absent in mirror head", result.stdout)
            self.assertEqual(self._remote(root, "manual_sources/A/spec.json"), "a1")
            self._write(root / "source", {"manual_sources/A": None, "manual_sources/Z/z.json": "z"},
                        "Remove A upstream")
            result = self._sync(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(self._remote_files(root, "manual_sources"),
                             {"manual_sources/A/spec.json", "manual_sources/Z/z.json"})

    def test_overlay_file_directory_conflicts_resolve_to_the_source(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(
                root,
                {"manual_sources/X": "source file", "manual_sources/Y/z.txt": "source dir",
                 "reports": "source file at the overlay path"},
                {"manual_sources/X/y.txt": "mirror dir", "manual_sources/Y": "mirror file",
                 "reports/old.txt": "mirror dir at the overlay path"},
            )
            result = self._sync(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(self._remote(root, "manual_sources/X"), "source file")
            self.assertEqual(self._remote(root, "manual_sources/Y/z.txt"), "source dir")
            self.assertEqual(self._remote(root, "reports"), "source file at the overlay path")
            self.assertIn("overlay manual_sources: mirror_only_kept=0 source_updated=0 "
                          "mirror_lost_to_source_conflict=2", result.stdout)
            self.assertIn("overlay reports: mirror_only_kept=0 source_updated=0 "
                          "mirror_lost_to_source_conflict=1", result.stdout)

    def test_overlay_keeps_a_mirror_only_file_at_the_overlay_path(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root, {}, {"reports": "mirror-only file"})
            result = self._sync(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(self._remote(root, "reports"), "mirror-only file")

    def test_strict_keep_path_still_wins_and_warns_when_the_source_differs(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root,
                          {"keepme/a.txt": "source", "keepme/s.txt": "source only",
                           "docs": "source file where docs/ belongs", "fresh/f.txt": "first write"},
                          {"keepme/a.txt": "mirror", "keepme/m.txt": "mirror only",
                           "docs/publish/p.txt": "published"})
            result = self._sync(root, MIRROR_KEEP_PATHS="docs/publish keepme fresh")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(self._remote_files(root, "keepme"), {"keepme/a.txt", "keepme/m.txt"})
            self.assertEqual(self._remote(root, "keepme/a.txt"), "mirror")
            self.assertEqual(self._remote(root, "docs/publish/p.txt"), "published")
            self.assertIn("::warning::Keep path keepme still exists in local/source with different content",
                          result.stdout)
            self.assertIn("keep keepme: mirror_only_kept=1 source_dropped=2", result.stdout)
            self.assertIn("::warning::Keep path fresh is not in the mirror yet", result.stdout)
            self.assertEqual(self._remote(root, "fresh/f.txt"), "first write")

    def test_keep_path_that_is_a_file_in_the_mirror_fails_clearly(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root, {}, {"keepblob": "a file"})
            before = self._git(root / "remote.git", "rev-parse", "main")
            for dry in ("0", "1"):
                result = self._sync(root, MIRROR_KEEP_PATHS="keepblob", MIRROR_DRY_RUN=dry)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("::error::Keep path keepblob is a blob, not a directory", result.stdout)
            self.assertEqual(self._git(root / "remote.git", "rev-parse", "main"), before)

    def test_overlapping_rules_are_refused(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root, {}, {})
            for extra, message in (
                ({"MIRROR_KEEP_PATHS": "manual_sources/A"}, "MIRROR_OVERLAY_PATHS entry manual_sources overlaps MIRROR_KEEP_PATHS entry manual_sources/A"),
                ({"MIRROR_OVERLAY_PATHS": "docs"}, "MIRROR_OVERLAY_PATHS entry docs overlaps MIRROR_KEEP_PATHS entry docs/publish"),
            ):
                result = self._sync(root, **extra)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(message, result.stdout)

    def test_dry_run_reports_and_matches_the_following_real_sync(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root, {"manual_sources/A/spec.json": "a2", "reports/new.txt": "n"},
                          {"manual_sources/A/spec.json": "a1", "manual_sources/M/m.json": "m",
                           "docs/publish/p.txt": "published"})
            before = self._git(root / "remote.git", "rev-parse", "main")
            dry = self._sync(root, MIRROR_DRY_RUN="1")
            self.assertEqual(dry.returncode, 0, dry.stdout + dry.stderr)
            self.assertEqual(self._git(root / "remote.git", "rev-parse", "main"), before)
            self.assertEqual(self._git(root / "mirror", "rev-parse", "HEAD"), before)
            for text in ("DRY_RUN path summary:",
                         "overlay manual_sources: mirror_only_kept=1 source_updated=1",
                         "overlay reports: absent in mirror head",
                         "keep docs/publish: mirror_only_kept=1 source_dropped=0",
                         "DRY_RUN diff against mirror head",
                         "M engine.txt (1 files)", "M manual_sources/A/ (1 files)",
                         "A reports/new.txt (1 files)", "3 files changed"):
                self.assertIn(text, dry.stdout)
            composed = dry.stdout.split("DRY_RUN composed_tree=")[1].split()[0]
            real = self._sync(root)
            self.assertEqual(real.returncode, 0, real.stdout + real.stderr)
            self.assertEqual(self._git(root / "remote.git", "rev-parse", "main^{tree}"), composed)

    def test_only_main_may_push_when_github_ref_is_set(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root, {"manual_sources/A/spec.json": "a1"}, {})
            remote = root / "remote.git"
            before = self._git(remote, "rev-parse", "main")
            for ref in ("refs/heads/some-branch", "refs/pull/1/merge"):
                result = self._sync(root, GITHUB_REF=ref)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(f"::error::GITHUB_REF is {ref}; only refs/heads/main may push", result.stdout)
                self.assertEqual(self._git(remote, "rev-parse", "main"), before)
                self.assertEqual(self._git(root / "mirror", "rev-parse", "HEAD"), before)
            dry = self._sync(root, GITHUB_REF="refs/heads/some-branch", MIRROR_DRY_RUN="1")
            self.assertEqual(dry.returncode, 0, dry.stdout + dry.stderr)
            self.assertEqual(self._git(remote, "rev-parse", "main"), before)
            result = self._sync(root, GITHUB_REF="refs/heads/main")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(self._remote(root, "manual_sources/A/spec.json"), "a1")

    def test_local_runs_without_github_ref_push_as_before(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root, {"manual_sources/A/spec.json": "a1"}, {})
            self.assertNotIn("GITHUB_REF", sync_environ())
            result = self._sync(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(self._remote(root, "manual_sources/A/spec.json"), "a1")

    def test_dry_run_still_refuses_a_forbidden_source_path(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root, {"docs/knowledge/x.txt": "leak"}, {})
            result = self._sync(root, MIRROR_DRY_RUN="1")
            self.assertEqual(result.returncode, 1)
            self.assertIn("auto-manual must not own docs/knowledge", result.stdout)
            self.assertNotIn("DRY_RUN composed_tree=", result.stdout)

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
            env = dict(sync_environ(), SOURCE_REPOSITORY="local/source",
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

    def _race_fixture(self, root: Path, *, races: int, reject_all: bool = False):
        """A review mirror whose branch gains a draft commit from another writer on each of the
        first ``races`` pushes the sync attempts (a client-side pre-push hook), or whose remote
        rejects every push."""
        def git(where, *args):
            return subprocess.run(["git", "-C", str(where), *args], check=True,
                                  capture_output=True, text=True).stdout.strip()

        remote = root / "remote.git"
        git(root, "init", "--bare", "-b", "main", "remote.git")
        for name in ("source", "mirror"):
            git(root, "init", "-b", "main", name)
            tree = root / name
            git(tree, "config", "user.name", "Test")
            git(tree, "config", "user.email", "test@example.invalid")
            (tree / "engine.txt").write_text(name)
            if name == "mirror":
                draft = tree / "docs" / "review-drafts" / "M" / "JP" / "draft.html"
                draft.parent.mkdir(parents=True)
                draft.write_text("v1")
            git(tree, "add", ".")
            git(tree, "commit", "-m", "Initial fixture")
        mirror, source = root / "mirror", root / "source"
        git(mirror, "remote", "add", "origin", str(remote))
        git(mirror, "push", "origin", "main")
        other = root / "other"
        git(root, "clone", "-q", str(remote), "other")
        git(other, "config", "user.name", "Writer")
        git(other, "config", "user.email", "writer@example.invalid")
        count = root / "races"
        count.write_text("0")
        hook = mirror / ".git" / "hooks" / "pre-push"
        hook.write_text(f"""#!/bin/sh
n=$(cat "{count}")
[ "$n" -ge {races} ] && exit 0
echo $((n + 1)) > "{count}"
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE
cd "{other}" && git pull -q origin main \\
  && echo "race $n" > docs/review-drafts/M/JP/race-$n.html \\
  && git add . && git commit -q -m "draft race $n" && git push -q origin main
""")
        hook.chmod(0o755)
        if reject_all:
            receive = remote / "hooks" / "pre-receive"
            receive.write_text("#!/bin/sh\necho rejected by test >&2\nexit 1\n")
            receive.chmod(0o755)
        env = dict(sync_environ(), SOURCE_REPOSITORY="local/source",
                   SOURCE_SHA=git(source, "rev-parse", "HEAD"), SOURCE_RUN_URL="local-test",
                   MIRROR_BRANCH="main", MIRROR_KEEP_PATHS="docs/review-drafts",
                   SOURCE_FORBIDDEN_PATHS=ALL_CONTENT)
        return git, env

    def test_real_sync_recomposes_when_a_draft_lands_during_the_push(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            git, env = self._race_fixture(root, races=1)
            result = subprocess.run(["bash", str(SCRIPT_PATH)], cwd=root, env=env,
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("recomposing on it (attempt 2 of 3)", result.stdout)
            remote = root / "remote.git"
            self.assertEqual(git(remote, "show", "main:engine.txt"), "source")
            # The racing draft commit is kept: it is the parent of the sync commit and its file survives.
            self.assertEqual(git(remote, "log", "-1", "--format=%s", "main^"), "draft race 0")
            self.assertEqual(git(remote, "show", "main:docs/review-drafts/M/JP/race-0.html"), "race 0")
            self.assertEqual(git(remote, "show", "main:docs/review-drafts/M/JP/draft.html"), "v1")
            self.assertEqual(git(remote, "rev-list", "--count", "main"), "3")

    def test_real_sync_gives_up_after_its_attempts_without_forcing(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            git, env = self._race_fixture(root, races=5)
            result = subprocess.run(["bash", str(SCRIPT_PATH)], cwd=root,
                                    env=dict(env, MIRROR_PUSH_ATTEMPTS="2"),
                                    capture_output=True, text=True, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("still rejected after 2 attempts", result.stdout)
            remote = root / "remote.git"
            self.assertEqual(git(remote, "log", "-1", "--format=%s", "main"), "draft race 1")
            self.assertEqual(git(remote, "show", "main:engine.txt"), "mirror")

    def test_real_sync_does_not_retry_a_rejection_that_is_not_a_race(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            git, env = self._race_fixture(root, races=0, reject_all=True)
            before = git(root / "remote.git", "rev-parse", "main")
            result = subprocess.run(["bash", str(SCRIPT_PATH)], cwd=root, env=env,
                                    capture_output=True, text=True, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("the branch has not moved; not retrying", result.stdout)
            self.assertEqual(git(root / "remote.git", "rev-parse", "main"), before)

    def test_real_sync_installs_the_mirror_readme_kept_in_the_source(self) -> None:
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
                (tree / "README.md").write_text(f"{name} readme")
                if name == "source":
                    own = tree / "mirrors" / "Hello-Docs" / "README.md"
                    own.parent.mkdir(parents=True)
                    own.write_text("business readme")
                git(tree, "add", ".")
                git(tree, "commit", "-m", "Initial fixture")
            mirror, source = root / "mirror", root / "source"
            git(mirror, "remote", "add", "origin", str(root / "remote.git"))
            git(mirror, "push", "origin", "main")
            env = dict(sync_environ(), SOURCE_REPOSITORY="local/source",
                       SOURCE_SHA=git(source, "rev-parse", "HEAD"), SOURCE_RUN_URL="local-test",
                       MIRROR_BRANCH="main", MIRROR_KEEP_PATHS="docs/publish",
                       SOURCE_FORBIDDEN_PATHS=ALL_CONTENT)

            def sync(readme):
                return subprocess.run(["bash", str(SCRIPT_PATH)], cwd=root,
                                      env=dict(env, MIRROR_README=readme),
                                      capture_output=True, text=True, check=False)

            result = sync("")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(git(mirror, "show", "HEAD:README.md"), "source readme")
            result = sync("mirrors/Hello-Docs/README.md")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(git(mirror, "show", "HEAD:README.md"), "business readme")
            self.assertEqual(git(mirror, "show", "HEAD:mirrors/Hello-Docs/README.md"), "business readme")
            synced = git(mirror, "rev-parse", "HEAD")
            result = sync("mirrors/Hello-Docs/README.md")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(git(mirror, "rev-parse", "HEAD"), synced)

            for missing in ("mirrors/Missing/README.md", "mirrors/Hello-Docs"):
                result = sync(missing)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"::error::{missing} is not a file", result.stdout)
                self.assertEqual(git(mirror, "rev-parse", "HEAD"), synced)

    def test_overlay_prune_externalized_removes_superseded_binaries_and_keeps_others(self) -> None:
        from tools.web import external_source_store as store

        def pointer_json(file_name: str, payload: bytes) -> str:
            return json.dumps(
                {
                    "schema_version": store.POINTER_SCHEMA_VERSION,
                    "storage_role": "asset_sources",
                    "file_name": file_name,
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "size_bytes": len(payload),
                    "feishu": {
                        "table_id": store.ASSET_SOURCES_TABLE_ID,
                        "record_id": "recAbcDef123456",
                        "field_name": "source_file",
                        "file_token": "boxcnTokenAbc123456789",
                    },
                },
                indent=2,
            ) + "\n"

        full_pdf_sha = hashlib.sha256(b"part1part2").hexdigest()
        manifest_json = json.dumps(
            {
                "original_source": {
                    "filename": "split.pdf",
                    "sha256": full_pdf_sha,
                    "archive_parts": [
                        {"path": "source/pdf-archive/part-001.bin", "size": 5},
                        {"path": "source/pdf-archive/part-002.bin", "size": 5},
                    ],
                }
            }
        )
        source_files = {
            "manual_sources/A/manual.pdf.source-pointer.json": pointer_json("manual.pdf", b"pdf-a"),
            "manual_sources/A/设计 修正.ai.source-pointer.json": pointer_json("设计 修正.ai", b"ai-a"),
            "manual_sources/A/tracked.pdf": "still-in-upstream",
            "manual_sources/A/tracked.pdf.source-pointer.json": pointer_json("tracked.pdf", b"still-in-upstream"),
            "data/manual_sources/B/manifest.json": manifest_json,
            "data/manual_sources/B/source/pdf-archive/split.pdf.source-pointer.json": pointer_json(
                "split.pdf", b"part1part2"
            ),
        }
        mirror_files = {
            "docs/publish/p.txt": "published",
            "docs/knowledge/k.txt": "knowledge",
            "manual_sources/A/manual.pdf": "old-pdf-a",
            "manual_sources/A/设计 修正.ai": "old-ai-a",
            "manual_sources/A/tracked.pdf": "old-tracked",
            "manual_sources/M/only.json": "downstream-only",
            "data/manual_sources/B/source/pdf-archive/part-001.bin": "part1",
            "data/manual_sources/B/source/pdf-archive/part-002.bin": "part2",
            "data/manual_sources/B/source/pdf-archive/.gitattributes": "*.bin binary\n",
            "reports/downstream.txt": "keep-report",
        }
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root, source_files, mirror_files)
            dry = self._sync(
                root,
                MIRROR_DRY_RUN="1",
                MIRROR_KEEP_PATHS="docs/publish docs/knowledge",
                MIRROR_OVERLAY_PATHS="manual_sources data/manual_sources reports",
                MIRROR_OVERLAY_PRUNE_EXTERNALIZED="1",
                PYTHON=sys.executable,
            )
            self.assertEqual(dry.returncode, 0, dry.stdout + dry.stderr)
            self.assertIn("pruned 2 externalized file(s)", dry.stdout)
            self.assertIn("overlay manual_sources: mirror_only_kept=1 source_updated=1 mirror_lost_to_source_conflict=0 pruned_externalized=2", dry.stdout)
            self.assertIn("overlay data/manual_sources: mirror_only_kept=1 source_updated=0 mirror_lost_to_source_conflict=0 pruned_externalized=2", dry.stdout)
            composed = dry.stdout.split("DRY_RUN composed_tree=")[1].split()[0]

            real = self._sync(
                root,
                MIRROR_KEEP_PATHS="docs/publish docs/knowledge",
                MIRROR_OVERLAY_PATHS="manual_sources data/manual_sources reports",
                MIRROR_OVERLAY_PRUNE_EXTERNALIZED="1",
                PYTHON=sys.executable,
            )
            self.assertEqual(real.returncode, 0, real.stdout + real.stderr)
            self.assertEqual(self._git(root / "remote.git", "rev-parse", "main^{tree}"), composed)
            self.assertEqual(
                self._remote_files(root, "manual_sources"),
                {
                    "manual_sources/A/manual.pdf.source-pointer.json",
                    "manual_sources/A/设计 修正.ai.source-pointer.json",
                    "manual_sources/A/tracked.pdf",
                    "manual_sources/A/tracked.pdf.source-pointer.json",
                    "manual_sources/M/only.json",
                },
            )
            self.assertEqual(self._remote(root, "manual_sources/A/tracked.pdf"), "still-in-upstream")
            self.assertEqual(
                self._remote_files(root, "data/manual_sources"),
                {
                    "data/manual_sources/B/manifest.json",
                    "data/manual_sources/B/source/pdf-archive/split.pdf.source-pointer.json",
                    "data/manual_sources/B/source/pdf-archive/.gitattributes",
                },
            )
            self.assertEqual(self._remote(root, "docs/publish/p.txt"), "published")
            self.assertEqual(self._remote(root, "docs/knowledge/k.txt"), "knowledge")
            self.assertEqual(self._remote(root, "reports/downstream.txt"), "keep-report")

    def test_shallow_depth1_sync_with_snapshot_bundle_and_race_retry(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self._git(root, "init", "--bare", "-q", "-b", "main", "upstream.git")
            self._git(root, "init", "--bare", "-q", "-b", "main", "remote.git")

            up_work = root / "up_work"
            self._git(root, "clone", "-q", str(root / "upstream.git"), str(up_work))
            self._git(up_work, "config", "user.name", "Test")
            self._git(up_work, "config", "user.email", "test@example.invalid")
            self._write(up_work, {"engine.txt": "u1", "old.bin": "deleted-later"}, "Upstream 1")
            self._write(up_work, {"engine.txt": "u2", "old.bin": None}, "Upstream 2")
            self._git(up_work, "push", "-q", "origin", "main")

            mir_work = root / "mir_work"
            self._git(root, "clone", "-q", str(root / "remote.git"), str(mir_work))
            self._git(mir_work, "config", "user.name", "Test")
            self._git(mir_work, "config", "user.email", "test@example.invalid")
            self._write(mir_work, {"docs/publish/p.txt": "m1"}, "Mirror 1")
            self._write(mir_work, {"docs/publish/p2.txt": "m2"}, "Mirror 2")
            self._git(mir_work, "push", "-q", "origin", "main")

            # Clone both at depth=1 (matching fetch-depth: 1 in sync-hello-docs.yml).
            self._git(root, "clone", "--depth=1", "-q", f"file://{root / 'upstream.git'}", "source")
            self._git(root, "clone", "--depth=1", "-q", f"file://{root / 'remote.git'}", "mirror")

            # Advance remote mirror while sync runs so retry loop also triggers on shallow clone.
            self._write(mir_work, {"docs/publish/p3.txt": "race-m3"}, "Mirror race 3")
            self._git(mir_work, "push", "-q", "origin", "main")

            # Simulate mirror push failure on stale mirror_parent by verifying direct shallow push first,
            # then re-testing retry when remote_head moved ahead of local mirror HEAD.
            result = self._sync(root, MIRROR_OVERLAY_PATHS="")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("moved to", result.stdout)
            self.assertEqual(self._remote(root, "engine.txt"), "u2")
            self.assertEqual(self._remote(root, "docs/publish/p3.txt"), "race-m3")
            # Temporary snapshot ref must not remain in source.
            refs = self._git(root / "source", "for-each-ref", "--format=%(refname)", "refs/sync")
            self.assertEqual(refs, "")


if __name__ == "__main__":
    unittest.main()
