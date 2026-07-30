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


if __name__ == "__main__":
    unittest.main()
