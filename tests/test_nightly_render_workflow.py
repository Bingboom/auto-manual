from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github/workflows/nightly-render.yml"


class TestNightlyRenderWorkflow(unittest.TestCase):
    def test_workflow_is_scheduled_dispatchable_and_runs_driver(self) -> None:
        workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
        triggers = workflow[True]
        self.assertIn("schedule", triggers)
        self.assertIn("workflow_dispatch", triggers)

        job = workflow["jobs"]["render-smoke"]
        steps = job["steps"]
        rendered = "\n".join(str(step) for step in steps)
        self.assertIn("tools/nightly_render.py", rendered)
        self.assertIn("configs/config.us-en.yaml", rendered)
        self.assertIn("JE-1000F", rendered)
        self.assertIn("production", (ROOT / "tools/nightly_render.py").read_text(encoding="utf-8"))

    def test_texlive_cache_precedes_install(self) -> None:
        workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
        steps = workflow["jobs"]["render-smoke"]["steps"]
        names = [str(step.get("name", "")) for step in steps]
        self.assertLess(names.index("Cache XeLaTeX apt archives"), names.index("Install render toolchain"))


if __name__ == "__main__":
    unittest.main()
