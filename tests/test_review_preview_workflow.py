from __future__ import annotations

import fnmatch
import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "review-preview.yml"


def _workflow_on_section(workflow: dict[object, object]) -> dict[object, object]:
    # PyYAML 5.x parses the YAML 1.1 boolean spelling ``on`` as True.
    return workflow.get("on", workflow.get(True, {}))  # type: ignore[return-value]


class ReviewPreviewWorkflowTests(unittest.TestCase):
    def test_pull_request_paths_cover_every_config_file(self) -> None:
        workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
        paths = _workflow_on_section(workflow)["pull_request"]["paths"]
        config_patterns = [path for path in paths if str(path).startswith("configs/")]
        self.assertEqual(["configs/config*.yaml"], config_patterns)

        config_paths = sorted(
            path.relative_to(REPO_ROOT).as_posix()
            for path in (REPO_ROOT / "configs").glob("config*.yaml")
        )
        self.assertTrue(config_paths)
        self.assertTrue(
            all(
                any(fnmatch.fnmatch(config_path, pattern) for pattern in config_patterns)
                for config_path in config_paths
            ),
            config_paths,
        )

    def test_smoke_package_delegates_target_and_config_resolution_to_preview_tool(self) -> None:
        workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
        steps = workflow["jobs"]["package-review-preview"]["steps"]
        step_names = [step.get("name") for step in steps if isinstance(step, dict)]
        self.assertNotIn("Select preview target", step_names)

        build_step = next(step for step in steps if step.get("name") == "Build review preview smoke package")
        command = str(build_step["run"])
        self.assertNotIn("config.us-en.yaml", command)
        self.assertNotIn("JE-1000F", command)
        self.assertNotIn("--config", command)
        self.assertNotIn("--model", command)
        self.assertNotIn("--region", command)


if __name__ == "__main__":
    unittest.main()
