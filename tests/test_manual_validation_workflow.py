from __future__ import annotations

import re
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


class WebIrChecksWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
        self.job = self.workflow["jobs"]["web-ir-checks"]

    def test_job_is_gated_to_auto_manual_and_uses_pinned_python(self) -> None:
        self.assertEqual("${{ github.repository == 'Bingboom/auto-manual' }}", self.job["if"])
        self.assertEqual("ubuntu-latest", self.job["runs-on"])
        self.assertGreaterEqual(int(self.job["timeout-minutes"]), 5)
        steps = self.job["steps"]
        self.assertEqual("actions/checkout", step_action_name(steps[0]))
        self.assertEqual("actions/setup-python", step_action_name(steps[1]))
        self.assertEqual("3.12", steps[1]["with"]["python-version"])
        self.assertIn("pip install -r requirements.lock", str(steps[2]["run"]))

    def test_runs_four_web_and_ir_checks_into_runner_temp(self) -> None:
        run_scripts = [str(step["run"]) for step in self.job["steps"][3:]]
        joined = "\n".join(run_scripts)
        self.assertNotIn("${{", joined)
        self.assertIn(
            'python build.py web-package --package-command inventory --json > "$RUNNER_TEMP/web_package_inventory.json"',
            run_scripts,
        )
        self.assertIn(
            "python build.py web-package --package-command audit-styles --all-packages --respect-baseline",
            run_scripts,
        )
        self.assertIn(
            'python build.py ir-qc --ir-command audit --all-ir --max-warnings 411 --output-path "$RUNNER_TEMP/ir_qc_audit.json"',
            run_scripts,
        )
        self.assertIn(
            'python build.py ir-export --output-corpus "$RUNNER_TEMP/corpus.json" --output-observations "$RUNNER_TEMP/observations.json"',
            run_scripts,
        )


class WorkflowNode24ActionPolicyTests(unittest.TestCase):
    _MIN_NODE24_MAJORS = {
        "actions/checkout": 7,
        "actions/setup-python": 7,
        "actions/setup-node": 7,
        "actions/cache": 6,
        "actions/upload-artifact": 7,
        "actions/download-artifact": 8,
        "actions/github-script": 9,
    }

    def test_all_workflows_and_actions_use_node24_action_majors(self) -> None:
        files = sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml")) + sorted(
            (REPO_ROOT / ".github" / "actions").glob("**/action.yml")
        )
        self.assertTrue(files)
        violations: list[str] = []
        for path in files:
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            steps = (
                [s for job in (doc.get("jobs") or {}).values() for s in (job.get("steps") or [])]
                if "jobs" in doc
                else list((doc.get("runs") or {}).get("steps") or [])
            )
            for step in steps:
                uses = str(step.get("uses") or "")
                match = re.match(r"^(actions/[A-Za-z0-9_-]+)@v(\d+)$", uses)
                if not match:
                    continue
                action, major = match.group(1), int(match.group(2))
                min_major = self._MIN_NODE24_MAJORS.get(action)
                if min_major is not None and major < min_major:
                    violations.append(f"{path.name}: {uses} (< @v{min_major})")
        self.assertEqual([], violations)

    def test_workspace_data_verify_uses_blobless_full_history_checkout(self) -> None:
        wf = yaml.safe_load(
            (REPO_ROOT / ".github" / "workflows" / "workspace-data-verify.yml").read_text(encoding="utf-8")
        )
        checkout = wf["jobs"]["verify"]["steps"][0]
        self.assertEqual(0, checkout["with"]["fetch-depth"])
        self.assertEqual("blob:none", checkout["with"]["filter"])


if __name__ == "__main__":
    unittest.main()
