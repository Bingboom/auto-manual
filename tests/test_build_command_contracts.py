"""Contract tests: every child command build.py assembles must parse in its target.

``build.py`` runs most actions by building an argv list and launching
``tools/<script>.py`` (or a Node adapter) as a subprocess. The two sides only
meet at runtime, so a renamed or dropped flag used to surface as a usage error
in an unattended queue run. Each case below turns a ``build.py`` command line
into the child argv and hands it to the child's own parser.
"""

from __future__ import annotations

import contextlib
import importlib
import io
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

import build
from tools.build_queue import message_control_entry


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ["--config", "configs/config.us.yaml"]
TARGET = [*CONFIG, "--model", "JE-1000F", "--region", "US"]

# builder name -> build.py argv variants that exercise its optional flags.
PYTHON_CASES: dict[str, list[list[str]]] = {
    "build_docs_command": [
        ["html", *TARGET],
        ["rst", *TARGET, "--lang", "en", "--no-clean"],
        ["word", *TARGET, "--source", "review"],
        ["pdf", *TARGET, "--pdf-mode", "word"],
        ["all", *TARGET, "--data-root", "data/phase2", "--draft-placeholders"],
        ["md", *TARGET, "--staging-root", ".tmp/contract-stage"],
        ["html", *TARGET, "--skip-root-index"],
        ["fast", *TARGET],
    ],
    "review_bundle_command": [
        ["review", *TARGET],
        ["review", *TARGET, "--refresh-review", "--lang", "en"],
    ],
    "check_docs_command": [
        ["check", *TARGET],
        ["check", *TARGET, "--lang", "en"],
        ["check", *TARGET, "--staging-root", ".tmp/contract-stage", "--data-root", "data/phase2"],
    ],
    "sync_review_command": [
        ["sync-review", *TARGET],
        ["sync-review", *TARGET, "--sync-scope", "params", "--page-file", "a.rst"],
        ["sync-review", *TARGET, "--data-root", "data/phase2", "--lang", "en"],
    ],
    "sync_data_command": [
        ["sync-data", *CONFIG],
        ["sync-data", *CONFIG, "--table", "spec_master", "--data-root", "data/phase2"],
    ],
    "spec_master_rebuild_command": [
        ["spec-master-rebuild", *CONFIG],
        [
            "spec-master-rebuild", *CONFIG,
            "--spec-rows-table-id", "tbl_rows",
            "--page-placeholders-table-id", "tbl_placeholders",
            "--expect-spec-rows", "5",
            "--expect-placeholder-rows", "3",
            "--write",
        ],
    ],
    "message_control_dry_run_command": [
        ["message-control-dry-run", *CONFIG, "--message", "status?"],
        [
            "message-control-dry-run", *CONFIG, "--message", "publish",
            "--record-id", "rec1", "--document-id", "JE-1000F_US_en_0.3",
            "--document-key", "key", "--lang", "en", "--build-family", "fam",
            "--git-ref", "review/x", "--version", "0.3", "--confirmed",
        ],
    ],
    "process_build_queue_command": [
        ["process-build-queue", *CONFIG],
        ["process-build-queue", *CONFIG, "--record-id", "rec1", "--dry-run"],
        ["process-build-queue", *CONFIG, "--workflow-action", "publish", "--record-ids", "a,b"],
    ],
    "process_review_start_queue_command": [
        ["process-review-start-queue", *CONFIG],
        ["process-review-start-queue", *CONFIG, "--record-id", "rec1", "--dry-run"],
        ["process-review-start-queue", *CONFIG, "--record-ids", "a,b"],
    ],
    "release_manifest_command": [
        ["release-manifest", *TARGET],
        [
            "release-manifest", *TARGET,
            "--data-root", "data/phase2", "--staging-root", ".tmp/contract-stage", "--version", "0.3",
        ],
    ],
    "release_rebuild_command": [
        ["release-rebuild-verify", *CONFIG, "--manifest", "reports/releases/x/manifest.json"],
        [
            "release-rebuild-verify", *CONFIG,
            "--manifest", "reports/releases/x/manifest.json", "--report", "reports/x/rebuild.json",
        ],
    ],
    "listen_build_queue_command": [
        ["listen-build-queue", *CONFIG],
        ["listen-build-queue", *CONFIG, "--dry-run"],
    ],
}

# Scripts whose parser lives outside the script module itself.
CHILD_PARSERS = {
    "message_control_dry_run": message_control_entry.parse_args,
}

NODE_CASES: dict[str, list[list[str]]] = {
    "listen_message_control_command": [["listen-message-control", *CONFIG]],
}

NOT_CHILD_COMMANDS = {"format_command"}


def _child_parser(module_name: str):
    stem = module_name.rpartition(".")[2]
    if stem in CHILD_PARSERS:
        return CHILD_PARSERS[stem]
    return importlib.import_module(module_name).parse_args


class BuildCommandContractTest(unittest.TestCase):
    def test_every_command_builder_has_a_contract_case(self) -> None:
        builders = {
            name
            for name in dir(build)
            if name.endswith("_command") and not name.startswith("_") and callable(getattr(build, name))
        } - NOT_CHILD_COMMANDS
        covered = set(PYTHON_CASES) | set(NODE_CASES)
        self.assertEqual(
            sorted(builders - covered),
            [],
            "add a contract case for each new build.py *_command builder",
        )
        self.assertEqual(sorted(covered - builders), [], "contract case names a builder that no longer exists")

    def test_python_child_commands_parse_in_their_target_script(self) -> None:
        for name, variants in PYTHON_CASES.items():
            for argv in variants:
                with self.subTest(builder=name, argv=argv[1:]):
                    cmd = getattr(build, name)(build.parse_args(argv))
                    self.assertEqual(cmd[0], sys.executable)
                    self.assertEqual(cmd[1], "-m", f"{name} must launch its child with python -m")
                    module_name = cmd[2]
                    self.assertTrue(module_name.startswith("tools."), module_name)
                    self.assertIsNotNone(importlib.util.find_spec(module_name), f"{name} launches a missing module")
                    stderr = io.StringIO()
                    try:
                        with contextlib.redirect_stderr(stderr):
                            _child_parser(module_name)(cmd[3:])
                    except SystemExit:
                        self.fail(f"{module_name} rejected {cmd[3:]}:\n{stderr.getvalue()}")

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_node_child_commands_parse_in_the_listener(self) -> None:
        parser_module = (
            ROOT / "integrations" / "openclaw" / "feishu-im-webhook-adapter" / "lib" / "local-listener-config.mjs"
        )
        for name, variants in NODE_CASES.items():
            for argv in variants:
                with self.subTest(builder=name, argv=argv[1:]):
                    cmd = getattr(build, name)(build.parse_args(argv))
                    self.assertEqual(cmd[0], "node")
                    self.assertTrue(Path(cmd[1]).is_file(), f"{name} launches a missing script: {cmd[1]}")
                    script = (
                        "const { parseLocalListenerArgs } = await import(process.argv[1]);"
                        "console.log(JSON.stringify(parseLocalListenerArgs(JSON.parse(process.argv[2]))));"
                    )
                    proc = subprocess.run(
                        ["node", "--input-type=module", "-e", script, parser_module.as_uri(), json.dumps(cmd[2:])],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertEqual(proc.returncode, 0, proc.stderr)
                    self.assertTrue(json.loads(proc.stdout)["controlConfig"])


if __name__ == "__main__":
    unittest.main()
