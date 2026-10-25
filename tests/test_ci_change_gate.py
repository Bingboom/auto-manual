from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.error import URLError

import yaml

from scripts import ci_change_gate as gate


ROOT = Path(__file__).resolve().parents[1]


class GitInputGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "fixture@example.invalid")
        self.write("README.md", "read me")
        self.write("tools/engine.py", "pass")
        self.commit()
        self.base = self.git("rev-parse", "HEAD").decode().strip()
        self.original_fingerprint = self.fingerprint()

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True,
                              capture_output=True).stdout

    def write(self, name, value):
        dest = self.root / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(value)

    def commit(self):
        self.git("add", ".")
        self.git("commit", "-m", "fixture")

    def required(self):
        return gate.engineering_required(self.git(
            "diff", "--raw", "-z", "--no-renames", "--no-abbrev", self.base, "HEAD", "--"))

    def fingerprint(self):
        return gate.input_fingerprint(self.git("ls-tree", "-r", "-z", "HEAD"))

    def test_editorial_changes_skip_heavy_checks_and_reuse_render_inputs(self):
        self.write("README.md", "changed")
        self.write("user-guide/guide with\nnewline.md", "notes")
        self.write("code-as-doc/architecture/position.md", "notes")
        self.commit()
        self.assertFalse(self.required())
        self.assertEqual(self.original_fingerprint, self.fingerprint())

    def test_unknown_template_policy_and_machine_inputs_are_not_editorial(self):
        for name in ["build.py", "tools/new.py", "data/new.csv", "configs/new.yaml",
                     "docs/templates/page.md", "docs/renderers/contracts/spec.md",
                     "docs/_review/item.md", "AGENTS.md", "user-guide/AGENTS.md",
                     "code-as-doc/spec.json", "requirements.lock", "new-directory/notes.md",
                     ".github/workflows/manual-validation.yml", "scripts/ci_change_gate.py"]:
            with self.subTest(path=name):
                self.assertFalse(gate.editorial(name))
        self.write("data/new.csv", "value")
        self.commit()
        self.assertTrue(self.required())
        self.assertNotEqual(self.original_fingerprint, self.fingerprint())

    def test_rename_from_code_to_markdown_cannot_hide_deletion(self):
        self.git("mv", "tools/engine.py", "user-guide.md")
        self.commit()
        self.assertTrue(self.required())
        self.assertNotEqual(self.original_fingerprint, self.fingerprint())

    def test_editorial_deletion_is_safe_but_executable_or_symlink_is_not(self):
        self.git("rm", "README.md")
        self.commit()
        self.assertFalse(self.required())
        self.write("README.md", "executable")
        (self.root / "README.md").chmod(0o755)
        self.commit()
        self.assertTrue(self.required())
        self.assertNotEqual(self.original_fingerprint, self.fingerprint())
        (self.root / "README.md").unlink()
        (self.root / "README.md").symlink_to("tools/engine.py")
        self.commit()
        self.assertTrue(self.required())

    def test_missing_base_empty_or_malformed_diff_defaults_to_full(self):
        self.assertTrue(self.required())
        self.assertTrue(gate.engineering_required(b"broken"))
        for base in ["", "0" * 40, "f" * 40, "--help"]:
            result = subprocess.run(
                ["python3", str(ROOT / "scripts/ci_change_gate.py"), "manual", "--base=" + base],
                cwd=self.root, capture_output=True, text=True, check=True,
            )
            self.assertIn("engineering=true", result.stdout)

    def test_fingerprint_rejects_incomplete_tree(self):
        for tree in [b"", b"broken", b"100644 blob not-a-sha\tfile\0"]:
            with self.subTest(tree=tree), self.assertRaises(ValueError):
                gate.input_fingerprint(tree)


def run_record(identifier, started, conclusion="success", status="completed"):
    return {"id": identifier, "run_started_at": started, "conclusion": conclusion, "status": status}


class NightlyRetryTests(unittest.TestCase):
    def test_first_run_and_failed_cancelled_or_running_predecessor_render(self):
        current = run_record(3, "2026-10-25T08:45:00Z", None, "in_progress")
        self.assertFalse(gate.previous_run_succeeded([current], "3"))
        for conclusion in ["failure", "cancelled", "timed_out", None]:
            previous = run_record(2, "2026-10-24T08:45:00Z", conclusion)
            self.assertFalse(gate.previous_run_succeeded([current, previous], "3"))
        previous = run_record(2, "2026-10-24T08:45:00Z")
        self.assertTrue(gate.previous_run_succeeded([current, previous], "3"))

    def test_old_failed_rerun_is_newer_than_successful_skipped_schedules(self):
        runs = [run_record(10, "2026-10-25T08:45:00Z"),
                run_record(9, "2026-10-24T08:45:00Z"),
                run_record(1, "2026-10-24T10:00:00Z", "failure")]
        self.assertFalse(gate.previous_run_succeeded(runs, "10"))

    def test_weekly_rotation_changes_cache_key_without_input_changes(self):
        from datetime import datetime, timezone
        tree = b"100644 blob " + b"a" * 40 + b"\ttools/engine.py\0"
        keys = []
        for day in [19, 26]:
            with patch.object(gate, "datetime") as clock, patch.object(gate, "git", return_value=tree), \
                    patch.object(gate, "last_run_ok", return_value=True), patch.object(gate, "emit") as emit, \
                    patch("sys.argv", ["ci_change_gate.py", "nightly"]):
                clock.now.return_value = datetime(2026, 10, day, tzinfo=timezone.utc)
                self.assertEqual(0, gate.main())
                keys.append(emit.call_args_list[0].args[1])
        self.assertNotEqual(keys[0], keys[1])
        self.assertEqual(keys[0].rsplit("-", 1)[1], keys[1].rsplit("-", 1)[1])

    def test_history_reads_all_pages_and_network_errors_force_render(self):
        env = {"GITHUB_API_URL": "https://api.github.com", "GITHUB_REPOSITORY": "fixture/repo",
               "GITHUB_REF_NAME": "main", "GITHUB_RUN_ID": "10", "GH_TOKEN": "test"}
        pages = [{"total_count": 3, "workflow_runs": [run_record(10, "3"), run_record(9, "1")]},
                 {"workflow_runs": [run_record(1, "2", "failure")]}]
        from io import BytesIO
        with patch.dict(os.environ, env), patch.object(gate, "urlopen") as request:
            request.side_effect = [BytesIO(json.dumps(page).encode()) for page in pages]
            self.assertFalse(gate.last_run_ok())
            self.assertEqual(2, request.call_count)
            request.side_effect = URLError("offline")
            self.assertFalse(gate.last_run_ok())


class WorkflowGateIntegrationTests(unittest.TestCase):
    def workflow(self, name):
        return yaml.safe_load((ROOT / f".github/workflows/{name}.yml").read_text())

    def test_required_checks_are_emitted_and_classifier_failure_cannot_skip_them(self):
        workflow = self.workflow("manual-validation")
        self.assertNotIn("paths", workflow[True]["push"])
        self.assertIsNone(workflow[True]["pull_request"])
        jobs = workflow["jobs"]
        heavy = {name for name, job in jobs.items() if job.get("needs") == "changes"}
        self.assertEqual(14, len(heavy))
        for name in heavy:
            condition = jobs[name]["if"]
            self.assertIn("!cancelled()", condition)
            self.assertIn("needs.changes.result != 'success'", condition)
            self.assertIn("needs.changes.outputs.engineering != 'false'", condition)
        for name in ["secret-scan", "maintainability-guardrails", "doc-link-integrity", "business-content"]:
            self.assertNotIn("needs", jobs[name])
        classifier = jobs["changes"]["steps"][-1]["run"]
        self.assertIn('git show "$CHANGE_BASE:scripts/ci_change_gate.py"', classifier)
        self.assertIn('echo "engineering=true" >> "$GITHUB_OUTPUT"', classifier)

    def test_nightly_manual_retry_and_cache_miss_run_and_only_success_is_cached(self):
        jobs = self.workflow("nightly-render")["jobs"]
        condition = jobs["render-smoke"]["if"]
        for term in ["github.event_name == 'workflow_dispatch'", "github.run_attempt > 1", "needs.changes.result != 'success'",
                     "needs.changes.outputs.cache_hit != 'true'", "needs.changes.outputs.previous_ok != 'true'"]:
            self.assertIn(term, condition)
        restore = next(s for s in jobs["changes"]["steps"] if s.get("id") == "previous")
        self.assertTrue(restore["with"]["lookup-only"])
        self.assertNotIn("restore-keys", restore["with"])
        save = jobs["render-smoke"]["steps"][-1]
        self.assertEqual("actions/cache/save@v4", save["uses"])
        self.assertIn("success()", save["if"])
        self.assertEqual({"contents": "read", "actions": "read"}, jobs["changes"]["permissions"])


if __name__ == "__main__":
    unittest.main()
