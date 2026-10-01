"""Freeze the public parser and offline failures before command extraction."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from tools import bitable_schema as schema


GOLDEN = Path(__file__).parent / "fixtures" / "bitable_schema_cli_golden.json"
COMMANDS = ("export", "apply", "parity", "seed-export", "seed-import", "promote")


def snapshots():
    cases = {"help": ["--help"], "required-command": []}
    for command in COMMANDS:
        cases[f"{command}-help"] = [command, "--help"]
        cases[f"{command}-required"] = [command]
    cases.update({
        "export-missing-token": ["export", "--out", "unused-report.json"],
        "seed-export-missing-token": ["seed-export", "--table", "fixture", "--out", "unused-seed.csv"],
        "parity-invalid-alias": ["parity", "--source-base", "fixture-source",
                                 "--target-base", "fixture-target", "--table-alias", "invalid"],
    })
    for command in ("apply", "seed-import", "promote"):
        cases[f"{command}-write-required"] = [command, "--write", "--yes"]
    results = {}
    for case, args in cases.items():
        stdout, stderr = io.StringIO(), io.StringIO()
        with (
            patch.object(sys, "argv", ["bitable_schema.py"]),
            patch.dict(os.environ, {"FEISHU_PHASE2_BASE_TOKEN": "", "COLUMNS": "80"}),
            patch.object(schema, "_PROFILE", None), patch.object(schema, "_IDENTITY", "bot"),
            patch.object(schema, "_lark", side_effect=AssertionError("live calls forbidden")) as live,
            redirect_stdout(stdout), redirect_stderr(stderr),
        ):
            try:
                code = schema.main(args)
            except SystemExit as exc:
                code = exc.code
            live.assert_not_called()
        results[case] = {"exit_code": code, "stdout": stdout.getvalue(), "stderr": stderr.getvalue()}
    return results


class BitableSchemaCliTests(unittest.TestCase):
    def test_all_command_help_and_offline_failures_match_frozen_contract(self):
        self.assertEqual(snapshots(), json.loads(GOLDEN.read_text(encoding="utf-8")))


if __name__ == "__main__":
    if sys.argv[1:] == ["--update"]:
        GOLDEN.write_text(json.dumps(snapshots(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        unittest.main()
