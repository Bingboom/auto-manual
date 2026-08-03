from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

import yaml

from tests.test_helpers import step_uses_action


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_ROOT = REPO_ROOT / ".github" / "workflows"


def _upload_steps() -> list[tuple[Path, dict[str, object]]]:
    uploads: list[tuple[Path, dict[str, object]]] = []
    for workflow_path in sorted(WORKFLOW_ROOT.glob("*.yml")):
        workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
        for job in workflow.get("jobs", {}).values():
            for step in job.get("steps", []):
                # Match the action, not its version: a version-pinned matcher
                # silently finds nothing after a dependabot bump, and every
                # policy assertion below then collapses.
                if step_uses_action(step, "actions/upload-artifact"):
                    uploads.append((workflow_path, step))
    return uploads


def _path_lines(step: dict[str, object]) -> list[str]:
    raw = str(step["with"]["path"])
    return [line.strip() for line in raw.splitlines() if line.strip()]


class WorkflowArtifactPolicyTests(unittest.TestCase):
    def test_print_release_outputs_are_ignored_but_web_sources_are_trackable(self) -> None:
        generated_print_paths = [
            f"reports/releases/JE-1000F/US/en/versions/2.0/manual.{suffix}"
            for suffix in ("idml", "tex", "pdf", "docx", "zip")
        ]
        publish_leaks = [
            f"docs/publish/web/JE-1000F/US/md/assets/manual.{suffix}"
            for suffix in ("idml", "tex", "pdf", "docx", "zip")
        ]
        for path in generated_print_paths + publish_leaks:
            with self.subTest(path=path):
                ignored = subprocess.run(
                    ["git", "check-ignore", "--no-index", "--quiet", "--", path],
                    cwd=REPO_ROOT,
                    check=False,
                )
                self.assertEqual(0, ignored.returncode)

        web_source = subprocess.run(
            [
                "git",
                "check-ignore",
                "--no-index",
                "--quiet",
                "--",
                "docs/publish/web/JE-1000F/US/md/manual.md",
            ],
            cwd=REPO_ROOT,
            check=False,
        )
        self.assertEqual(1, web_source.returncode)

    def test_every_uploaded_artifact_has_an_explicit_retention_window(self) -> None:
        uploads = _upload_steps()
        self.assertTrue(uploads)
        missing = [path.name for path, step in uploads if "retention-days" not in step["with"]]
        self.assertEqual([], missing)

    def test_queue_artifacts_upload_only_delivery_or_diagnostic_surfaces(self) -> None:
        uploads = {
            step["with"]["name"]: step
            for _, step in _upload_steps()
            if isinstance(step.get("with"), dict)
        }

        draft = uploads["feishu-draft-build-queue-output"]
        self.assertEqual(7, draft["with"]["retention-days"])
        self.assertEqual(
            [
                "docs/_build/**/word/*.docx",
                "docs/_build/**/md/**",
                "data/phase2/snapshot_manifest.json",
                "data/phase2/row_key_mapping.csv",
            ],
            _path_lines(draft),
        )

        review = uploads["feishu-start-review-output"]
        self.assertEqual(7, review["with"]["retention-days"])
        self.assertNotIn("docs/_review", _path_lines(review))
        self.assertIn("docs/_review/**/page/**", _path_lines(review))

        publish = uploads["feishu-build-queue-output"]
        self.assertEqual(14, publish["with"]["retention-days"])
        self.assertEqual(
            [
                "reports/releases/**/versions/**",
                "reports/releases/**/latest/**",
                "reports/releases/**/manifests/*.json",
                "reports/releases/**/manifests/*.csv",
                "data/phase2/snapshot_manifest.json",
                "data/phase2/row_key_mapping.csv",
            ],
            _path_lines(publish),
        )

        web_publish = uploads["feishu-web-publish-queue-output"]
        self.assertEqual(7, web_publish["with"]["retention-days"])
        self.assertEqual(
            [
                "reports/releases/**/versions/**/web/**",
                "reports/releases/**/latest/web/**",
                "${{ runner.temp }}/hello-docs-publish/docs/publish/publish_manifest.json",
                "data/phase2/snapshot_manifest.json",
                "data/phase2/row_key_mapping.csv",
            ],
            _path_lines(web_publish),
        )

        publish_workflow = yaml.safe_load(
            (WORKFLOW_ROOT / "feishu-build-queue.yml").read_text(encoding="utf-8")
        )
        self.assertNotIn("deploy-vercel", publish_workflow["jobs"])
        self.assertNotIn("vercel-publish-candidate", uploads)

    def test_backup_keeps_its_restore_window(self) -> None:
        backup_steps = [
            step
            for path, step in _upload_steps()
            if path.name == "phase2-content-backup.yml"
        ]
        self.assertEqual(1, len(backup_steps))
        self.assertEqual(90, backup_steps[0]["with"]["retention-days"])


class WorkflowStepMatchingTests(unittest.TestCase):
    """Keep workflow guards version-agnostic.

    A dependabot actions bump once turned four of these tests red purely
    because the matcher compared the full ``uses`` string; the workflows were
    correct. Matching must survive any version ref.
    """

    def test_action_matching_ignores_the_version_ref(self) -> None:
        for ref in ("v4", "v7", "v7.0.1", "main", "a1b2c3d4e5f6"):
            with self.subTest(ref=ref):
                step = {"uses": f"actions/upload-artifact@{ref}"}
                self.assertTrue(step_uses_action(step, "actions/upload-artifact"))

    def test_action_matching_does_not_confuse_different_actions(self) -> None:
        self.assertFalse(
            step_uses_action({"uses": "actions/download-artifact@v4"}, "actions/upload-artifact")
        )
        self.assertFalse(step_uses_action({"run": "echo hi"}, "actions/upload-artifact"))

    def test_every_upload_step_in_the_repo_is_discovered(self) -> None:
        # Guards against a matcher that silently finds nothing: the repo does
        # upload artifacts, so an empty result is a matcher bug, not a policy pass.
        discovered = {path.name for path, _ in _upload_steps()}
        self.assertIn("feishu-build-queue.yml", discovered)
        self.assertIn("phase2-content-backup.yml", discovered)


if __name__ == "__main__":
    unittest.main()
