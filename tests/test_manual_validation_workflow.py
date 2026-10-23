from __future__ import annotations

import unittest
from pathlib import Path

import yaml

from tests.test_helpers import step_action_name


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "manual-validation.yml"


def _doctor_en_steps() -> list[dict[str, object]]:
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    return workflow["jobs"]["doctor-en"]["steps"]


def _step_named(name: str) -> tuple[int, dict[str, object]]:
    for index, step in enumerate(_doctor_en_steps()):
        if step.get("name") == name:
            return index, step
    raise AssertionError(f"missing doctor-en step: {name}")


class DoctorEnAptCacheTests(unittest.TestCase):
    def test_apt_cache_is_restored_before_the_install(self) -> None:
        cache_index, cache_step = _step_named("Cache TeX Live apt packages")
        install_index, _ = _step_named("Install system dependencies")
        self.assertLess(cache_index, install_index)
        self.assertEqual("actions/cache", step_action_name(cache_step))
        self.assertEqual("~/apt-cache", cache_step["with"]["path"])

    def test_install_returns_the_cache_to_the_runner_so_it_can_be_saved(self) -> None:
        # apt leaves the archive lock and partial/ owned by root; without the
        # chown the post step's tar fails, the save is only a warning, and every
        # run downloads the whole XeTeX stack again.
        _, install_step = _step_named("Install system dependencies")
        script = str(install_step["run"])
        chown = 'sudo chown -R "$(id -u):$(id -g)" "$HOME/apt-cache"'
        self.assertIn('Dir::Cache::archives="$HOME/apt-cache"', script)
        self.assertIn("APT::Keep-Downloaded-Packages=true", script)
        self.assertIn(chown, script)
        self.assertGreater(script.index(chown), script.index("sudo apt-get install"))


if __name__ == "__main__":
    unittest.main()
