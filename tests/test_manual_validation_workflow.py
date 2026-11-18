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


class UnitShardAggregateTests(unittest.TestCase):
    """`unit` is the required check; it must fail whenever any shard did not succeed."""

    def setUp(self) -> None:
        self.jobs = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))["jobs"]

    def test_shards_run_the_parallel_runner_over_the_whole_matrix(self) -> None:
        shard = self.jobs["unit-shard"]
        self.assertFalse(shard["strategy"]["fail-fast"])
        self.assertGreaterEqual(len(shard["strategy"]["matrix"]["shard"]), 2)
        step = shard["steps"][-1]
        # Expression values reach the shell through env:, never expanded inside run:.
        self.assertEqual({"UNIT_SHARD": "${{ matrix.shard }}", "UNIT_SHARD_TOTAL": "${{ strategy.job-total }}"}, step["env"])
        self.assertEqual('python -m tests.run_fast --shard "${UNIT_SHARD}/${UNIT_SHARD_TOTAL}"', step["run"])
        self.assertNotIn("${{", step["run"])

    def test_unit_runs_even_after_a_shard_failure_and_requires_success(self) -> None:
        unit = self.jobs["unit"]
        self.assertEqual("unit-shard", unit["needs"])
        self.assertTrue(str(unit["if"]).startswith("${{ always() && "))
        step = unit["steps"][-1]
        self.assertEqual("${{ needs.unit-shard.result }}", step["env"]["SHARDS_RESULT"])
        self.assertIn('if [ "$SHARDS_RESULT" != "success" ]; then', step["run"])
        self.assertIn("exit 1", step["run"])


if __name__ == "__main__":
    unittest.main()
